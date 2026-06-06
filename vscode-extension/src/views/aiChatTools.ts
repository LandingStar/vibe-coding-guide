import * as path from 'node:path';
import * as vscode from 'vscode';
import { execFile } from 'node:child_process';
import { accessSync } from 'node:fs';
import { promisify } from 'node:util';
import type { AiChatToolName } from './aiChatActionProtocol';

const execFileAsync = promisify(execFile);
const LOCAL_TRAJECTORY_RESULT_PREFIX = '__DOC_BASED_CODING_LOCAL_TRAJECTORY__=';

interface AiChatToolDefinition {
    readonly name: AiChatToolName;
    readonly description: string;
    readonly args: string;
}

export interface AiChatToolResult {
    readonly ok: boolean;
    readonly tool: AiChatToolName;
    readonly summary: string;
    readonly content: string;
}

const AI_CHAT_TOOL_DEFINITIONS: readonly AiChatToolDefinition[] = [
    {
        name: 'listFiles',
        description: 'List files and directories under a workspace-relative directory.',
        args: '{ path?: string }',
    },
    {
        name: 'readFile',
        description: 'Read a workspace-relative text file. Supports optional line ranges.',
        args: '{ path: string, startLine?: number, endLine?: number }',
    },
    {
        name: 'searchText',
        description: 'Search plain text across the workspace, optionally limited by a glob include pattern.',
        args: '{ query: string, includePattern?: string, maxResults?: number }',
    },
    {
        name: 'getDiagnostics',
        description: 'Read VS Code diagnostics for one file or the whole workspace.',
        args: '{ path?: string }',
    },
    {
        name: 'localTrajectory',
        description: 'Agent-owned Local Work Trajectory mutation. Use start at task start, append for planned/observed events, advance when active event is complete, update to refine current event, block/wait for impediments, resume to continue, and close when the single-line task is done. Use addLane only for the first multi-line expansion step: create another lane with its first event. Use merge to add an explicit target-lane merge event and a merges_into relation from a source lane event. Use relate to record explicit dependency/wait/unblock/handoff/sync/approval metadata between existing events; it does not schedule work or resolve conflicts. After validation or delivery completes, keep advancing until completed milestones are not left pending or in_progress. This is not a user-facing control.',
        args: '{ action: "start"|"append"|"advance"|"update"|"block"|"wait"|"resume"|"close"|"addLane"|"merge"|"relate", laneLabel?: string, firstEventTitle?: string, title?: string, eventKind?: string, relationKind?: "depends_on"|"waits_for"|"unblocks"|"hands_off"|"syncs_from"|"approves_new_line", summary?: string, reason?: string, guideContext?: string, currentEventId?: string, laneId?: string, sourceEventId?: string, sourceLaneId?: string, targetLaneId?: string, targetEventId?: string }',
    },
] as const;

export function describeAiChatTools(): string {
    return AI_CHAT_TOOL_DEFINITIONS
        .map((tool) => `- ${tool.name} ${tool.args}: ${tool.description}`)
        .join('\n');
}

export class AiChatToolExecutor {
    private static readonly _maxListEntries = 200;
    private static readonly _maxReadLines = 220;
    private static readonly _maxSearchResults = 40;
    private static readonly _maxDiagnostics = 60;
    private static readonly _maxToolPayloadChars = 6000;

    getWorkspaceRoot(): string | null {
        return vscode.workspace.workspaceFolders?.[0]?.uri.fsPath ?? null;
    }

    async execute(tool: AiChatToolName, args: Record<string, unknown>): Promise<AiChatToolResult> {
        try {
            switch (tool) {
                case 'listFiles':
                    return await this._listFiles(args);
                case 'readFile':
                    return await this._readFile(args);
                case 'searchText':
                    return await this._searchText(args);
                case 'getDiagnostics':
                    return this._getDiagnostics(args);
                case 'localTrajectory':
                    return await this._localTrajectory(args);
                default:
                    return this._error(tool, `Unsupported tool: ${tool}`);
            }
        } catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            return this._error(tool, message);
        }
    }

    private async _listFiles(args: Record<string, unknown>): Promise<AiChatToolResult> {
        const directoryUri = await this._resolveExistingUri(this._readOptionalPath(args.path), 'directory');
        const entries = await vscode.workspace.fs.readDirectory(directoryUri);
        const sortedEntries = entries
            .slice()
            .sort((left, right) => {
                const leftIsDirectory = (left[1] & vscode.FileType.Directory) !== 0;
                const rightIsDirectory = (right[1] & vscode.FileType.Directory) !== 0;
                if (leftIsDirectory !== rightIsDirectory) {
                    return leftIsDirectory ? -1 : 1;
                }
                return left[0].localeCompare(right[0], 'en');
            });
        const relativePath = this._toRelativePath(directoryUri);
        const visibleEntries = sortedEntries.slice(0, AiChatToolExecutor._maxListEntries);
        const lines = visibleEntries.map(([name, fileType]) => {
            const suffix = (fileType & vscode.FileType.Directory) !== 0 ? '/' : '';
            return `${name}${suffix}`;
        });

        if (sortedEntries.length > visibleEntries.length) {
            lines.push(`... truncated ${sortedEntries.length - visibleEntries.length} more entries`);
        }

        return {
            ok: true,
            tool: 'listFiles',
            summary: `Listed ${sortedEntries.length} entries under ${relativePath}.`,
            content: this._truncate(lines.join('\n')),
        };
    }

    private async _readFile(args: Record<string, unknown>): Promise<AiChatToolResult> {
        const filePath = this._readRequiredPath(args.path, 'readFile requires a path.');
        const fileUri = await this._resolveExistingUri(filePath, 'file');
        const bytes = await vscode.workspace.fs.readFile(fileUri);
        const text = new TextDecoder().decode(bytes);
        const allLines = text.split(/\r?\n/);
        const requestedStartLine = this._clampPositiveInteger(args.startLine, 1);
        const defaultEndLine = Math.min(allLines.length, requestedStartLine + AiChatToolExecutor._maxReadLines - 1);
        const requestedEndLine = this._clampPositiveInteger(args.endLine, defaultEndLine);
        const endLine = Math.min(allLines.length, Math.max(requestedStartLine, requestedEndLine));
        const maxEndLine = Math.min(allLines.length, requestedStartLine + AiChatToolExecutor._maxReadLines - 1);
        const effectiveEndLine = Math.min(endLine, maxEndLine);
        const visibleLines = allLines
            .slice(requestedStartLine - 1, effectiveEndLine)
            .map((line, index) => `${requestedStartLine + index}: ${line}`);

        if (effectiveEndLine < allLines.length && effectiveEndLine < endLine) {
            visibleLines.push(`... truncated after line ${effectiveEndLine}`);
        }

        return {
            ok: true,
            tool: 'readFile',
            summary: `Read ${this._toRelativePath(fileUri)} lines ${requestedStartLine}-${effectiveEndLine} of ${allLines.length}.`,
            content: this._truncate(visibleLines.join('\n')),
        };
    }

    private async _searchText(args: Record<string, unknown>): Promise<AiChatToolResult> {
        const query = typeof args.query === 'string' ? args.query.trim() : '';
        if (!query) {
            return this._error('searchText', 'searchText requires a non-empty query.');
        }

        const includePattern = typeof args.includePattern === 'string' && args.includePattern.trim()
            ? args.includePattern.trim()
            : undefined;
        const maxResults = Math.min(
            this._clampPositiveInteger(args.maxResults, AiChatToolExecutor._maxSearchResults),
            AiChatToolExecutor._maxSearchResults,
        );

        const matches: string[] = [];
        let totalMatches = 0;
        await vscode.workspace.findTextInFiles(
            { pattern: query, isRegExp: false, isCaseSensitive: false },
            { include: includePattern },
            (result) => {
                const ranges = this._toArray(result.ranges);
                const firstRange = ranges[0];
                const previewText = result.preview.text.replace(/\s+/g, ' ').trim();
                totalMatches += ranges.length;
                if (matches.length >= maxResults || !firstRange) {
                    return;
                }
                matches.push(`${this._toRelativePath(result.uri)}:${firstRange.start.line + 1}: ${previewText}`);
            },
        );

        if (matches.length === 0) {
            return {
                ok: true,
                tool: 'searchText',
                summary: `No matches found for "${query}"${includePattern ? ` in ${includePattern}` : ''}.`,
                content: 'No matches found.',
            };
        }

        if (totalMatches > matches.length) {
            matches.push(`... truncated ${totalMatches - matches.length} more matches`);
        }

        return {
            ok: true,
            tool: 'searchText',
            summary: `Found ${totalMatches} match(es) for "${query}"${includePattern ? ` in ${includePattern}` : ''}.`,
            content: this._truncate(matches.join('\n')),
        };
    }

    private _getDiagnostics(args: Record<string, unknown>): AiChatToolResult {
        const pathArg = this._readOptionalPath(args.path);
        const entries = pathArg
            ? this._collectFileDiagnostics(pathArg)
            : vscode.languages.getDiagnostics();

        const formatted: string[] = [];
        let totalDiagnostics = 0;

        for (const [uri, diagnostics] of entries) {
            if (!this._isWorkspaceUri(uri) || diagnostics.length === 0) {
                continue;
            }

            for (const diagnostic of diagnostics) {
                totalDiagnostics += 1;
                if (formatted.length >= AiChatToolExecutor._maxDiagnostics) {
                    continue;
                }
                const severity = this._formatSeverity(diagnostic.severity);
                const code = diagnostic.code ? ` ${String(diagnostic.code)}` : '';
                formatted.push(
                    `${this._toRelativePath(uri)}:${diagnostic.range.start.line + 1}:${diagnostic.range.start.character + 1}`
                    + ` [${severity}${code}] ${diagnostic.message}`,
                );
            }
        }

        if (formatted.length === 0) {
            return {
                ok: true,
                tool: 'getDiagnostics',
                summary: pathArg
                    ? `No diagnostics found for ${pathArg}.`
                    : 'No diagnostics found in the workspace.',
                content: 'No diagnostics found.',
            };
        }

        if (totalDiagnostics > formatted.length) {
            formatted.push(`... truncated ${totalDiagnostics - formatted.length} more diagnostics`);
        }

        return {
            ok: true,
            tool: 'getDiagnostics',
            summary: pathArg
                ? `Collected ${totalDiagnostics} diagnostic(s) for ${pathArg}.`
                : `Collected ${totalDiagnostics} diagnostic(s) in the workspace.`,
            content: this._truncate(formatted.join('\n')),
        };
    }

    private async _localTrajectory(args: Record<string, unknown>): Promise<AiChatToolResult> {
        const action = this._readRequiredString(args.action, 'localTrajectory requires action.');
        if (!['start', 'append', 'advance', 'update', 'block', 'wait', 'resume', 'close', 'addLane', 'merge', 'relate'].includes(action)) {
            return this._error('localTrajectory', 'localTrajectory action must be start, append, advance, update, block, wait, resume, close, addLane, merge, or relate.');
        }

        const workspaceRoot = this.getWorkspaceRoot();
        if (!workspaceRoot) {
            return this._error('localTrajectory', 'No workspace folder is open.');
        }

        const sourceRoot = this._resolveProgressGraphSourceRoot(workspaceRoot);
        const pythonPath = await this._resolvePythonPath(workspaceRoot);
        const payload = {
            kind: action,
            title: this._readOptionalString(args.title) ?? 'Local Work Trajectory',
            laneLabel: this._readOptionalString(args.laneLabel) ?? 'current work',
            firstEventTitle: this._readOptionalString(args.firstEventTitle) ?? this._readOptionalString(args.title) ?? 'start current work',
            firstEventKind: this._readOptionalString(args.eventKind) ?? 'start',
            eventKind: this._readOptionalString(args.eventKind) ?? 'task',
            summary: this._readOptionalString(args.summary) ?? '',
            reason: this._readOptionalString(args.reason) ?? '',
            guideContext: this._readOptionalString(args.guideContext) ?? 'ai-chat-agent',
            currentEventId: this._readOptionalString(args.currentEventId) ?? '',
            laneId: this._readOptionalString(args.laneId) ?? '',
            sourceEventId: this._readOptionalString(args.sourceEventId) ?? '',
            sourceLaneId: this._readOptionalString(args.sourceLaneId) ?? '',
            targetLaneId: this._readOptionalString(args.targetLaneId) ?? '',
            targetEventId: this._readOptionalString(args.targetEventId) ?? '',
            relationKind: this._readOptionalString(args.relationKind) ?? '',
        };
        const script = [
            'import json',
            'import sys',
            'from pathlib import Path',
            `sys.path.insert(0, ${JSON.stringify(sourceRoot)})`,
            'from tools.progress_graph import add_local_work_lane, add_local_work_relation, advance_single_line_event, append_single_line_event, block_single_line_event, close_single_line_trajectory, load_local_work_trajectory, merge_local_work_lane, resume_single_line_event, start_single_line_trajectory, update_single_line_event',
            '',
            'root = Path.cwd()',
            `action = json.loads(${JSON.stringify(JSON.stringify(payload))})`,
            'kind = action.get("kind")',
            'if kind == "start":',
            '    path = start_single_line_trajectory(',
            '        root,',
            '        title=action.get("title") or "Local Work Trajectory",',
            '        lane_label=action.get("laneLabel") or "current work",',
            '        first_event_title=action.get("firstEventTitle") or "start current work",',
            '        first_event_kind=action.get("firstEventKind") or "start",',
            '        guide_context=action.get("guideContext") or "ai-chat-agent",',
            '    )',
            'elif kind == "append":',
            '    path = append_single_line_event(',
            '        root,',
            '        title=action.get("title") or "next milestone",',
            '        kind=action.get("eventKind") or "task",',
            '        summary=action.get("summary") or "",',
            '        lane_id=action.get("laneId") or "",',
            '    )',
            'elif kind == "advance":',
            '    path = advance_single_line_event(root, current_event_id=action.get("currentEventId") or None)',
            'elif kind == "update":',
            '    path = update_single_line_event(',
            '        root,',
            '        current_event_id=action.get("currentEventId") or None,',
            '        title=action.get("title") or "",',
            '        summary=action.get("summary") or "",',
            '    )',
            'elif kind in {"block", "wait"}:',
            '    path = block_single_line_event(',
            '        root,',
            '        current_event_id=action.get("currentEventId") or None,',
            '        reason=action.get("reason") or action.get("summary") or "",',
            '        waiting=kind == "wait",',
            '    )',
            'elif kind == "resume":',
            '    path = resume_single_line_event(',
            '        root,',
            '        current_event_id=action.get("currentEventId") or None,',
            '        summary=action.get("summary") or "",',
            '    )',
            'elif kind == "close":',
            '    path = close_single_line_trajectory(',
            '        root,',
            '        current_event_id=action.get("currentEventId") or None,',
            '        summary=action.get("summary") or "",',
            '    )',
            'elif kind == "addLane":',
            '    path = add_local_work_lane(',
            '        root,',
            '        lane_label=action.get("laneLabel") or "new lane",',
            '        first_event_title=action.get("firstEventTitle") or action.get("title") or "start new lane",',
            '        first_event_kind=action.get("eventKind") or "task",',
            '        first_event_summary=action.get("summary") or "",',
            '        source_event_id=action.get("sourceEventId") or action.get("currentEventId") or None,',
            '        lane_id=action.get("laneId") or "",',
            '    )',
            'elif kind == "merge":',
            '    path = merge_local_work_lane(',
            '        root,',
            '        source_lane_id=action.get("sourceLaneId") or action.get("laneId") or "",',
            '        target_lane_id=action.get("targetLaneId") or "lane:main",',
            '        title=action.get("title") or "merge",',
            '        summary=action.get("summary") or "",',
            '        source_event_id=action.get("sourceEventId") or action.get("currentEventId") or None,',
            '        target_event_id=action.get("targetEventId") or None,',
            '    )',
            'elif kind == "relate":',
            '    path = add_local_work_relation(',
            '        root,',
            '        source_event_id=action.get("sourceEventId") or "",',
            '        target_event_id=action.get("targetEventId") or "",',
            '        relation_kind=action.get("relationKind") or "",',
            '        summary=action.get("summary") or "",',
            '    )',
            'else:',
            '    raise ValueError(f"unknown local trajectory action: {kind}")',
            'trajectory = load_local_work_trajectory(root)',
            'active_event_id = None',
            'active_event_ids = []',
            'for event_id, event in sorted(trajectory.events.items(), key=lambda item: (item[1].order, item[0])):',
            '    if event.status == "in_progress":',
            '        active_event_ids.append(event_id)',
            '        if active_event_id is None:',
            '            active_event_id = event_id',
            `print(${JSON.stringify(LOCAL_TRAJECTORY_RESULT_PREFIX)} + json.dumps({`,
            '    "trajectory_path": str(path),',
            '    "trajectory_id": trajectory.trajectory_id,',
            '    "lane_count": len(trajectory.lanes),',
            '    "event_count": len(trajectory.events),',
            '    "relation_count": len(trajectory.relations),',
            '    "active_event_id": active_event_id,',
            '    "active_event_ids": active_event_ids,',
            '}, ensure_ascii=False))',
        ].join('\n');

        const { stdout, stderr } = await execFileAsync(
            pythonPath,
            ['-c', script],
            {
                cwd: workspaceRoot,
                maxBuffer: 1024 * 1024,
            },
        );
        const resultLine = stdout
            .split(/\r?\n/)
            .map((line) => line.trim())
            .find((line) => line.startsWith(LOCAL_TRAJECTORY_RESULT_PREFIX));
        if (!resultLine) {
            throw new Error(`localTrajectory did not return a result.${stderr ? ` stderr: ${stderr}` : ''}`);
        }
        const result = JSON.parse(resultLine.slice(LOCAL_TRAJECTORY_RESULT_PREFIX.length)) as Record<string, unknown>;
        return {
            ok: true,
            tool: 'localTrajectory',
            summary: `Local trajectory ${action} wrote ${String(result.trajectory_path)}.`,
            content: this._truncate(JSON.stringify(result, null, 2)),
        };
    }

    private _collectFileDiagnostics(filePath: string): readonly [vscode.Uri, readonly vscode.Diagnostic[]][] {
        const fileUri = this._resolveWorkspaceUriSync(filePath);
        return [[fileUri, vscode.languages.getDiagnostics(fileUri)]];
    }

    private async _resolveExistingUri(requestedPath: string | undefined, expectedType: 'file' | 'directory'): Promise<vscode.Uri> {
        const uri = this._resolveWorkspaceUriSync(requestedPath ?? '.');
        const stat = await vscode.workspace.fs.stat(uri);
        const isDirectory = (stat.type & vscode.FileType.Directory) !== 0;
        if (expectedType === 'directory' && !isDirectory) {
            throw new Error(`${this._toRelativePath(uri)} is not a directory.`);
        }
        if (expectedType === 'file' && isDirectory) {
            throw new Error(`${this._toRelativePath(uri)} is not a file.`);
        }
        return uri;
    }

    private _resolveWorkspaceUriSync(requestedPath: string): vscode.Uri {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            throw new Error('No workspace folder is open.');
        }

        const rootPath = workspaceFolder.uri.fsPath;
        const normalizedInput = requestedPath.trim().replace(/\//g, path.sep);
        const candidatePath = path.resolve(rootPath, normalizedInput || '.');
        if (!this._isWithinWorkspace(rootPath, candidatePath)) {
            throw new Error(`Path ${requestedPath} is outside the workspace root.`);
        }

        return vscode.Uri.file(candidatePath);
    }

    private _isWithinWorkspace(rootPath: string, candidatePath: string): boolean {
        const normalizedRoot = path.resolve(rootPath).toLowerCase();
        const normalizedCandidate = path.resolve(candidatePath).toLowerCase();
        return normalizedCandidate === normalizedRoot || normalizedCandidate.startsWith(`${normalizedRoot}${path.sep}`);
    }

    private _isWorkspaceUri(uri: vscode.Uri): boolean {
        const workspaceRoot = this.getWorkspaceRoot();
        return workspaceRoot ? this._isWithinWorkspace(workspaceRoot, uri.fsPath) : false;
    }

    private _toRelativePath(uri: vscode.Uri): string {
        const workspaceRoot = this.getWorkspaceRoot();
        if (!workspaceRoot) {
            return uri.fsPath;
        }
        const relative = path.relative(workspaceRoot, uri.fsPath).replace(/\\/g, '/');
        return relative || '.';
    }

    private _readOptionalPath(value: unknown): string | undefined {
        return typeof value === 'string' && value.trim() ? value.trim() : undefined;
    }

    private _readOptionalString(value: unknown): string | undefined {
        return typeof value === 'string' && value.trim() ? value.trim() : undefined;
    }

    private _readRequiredString(value: unknown, errorMessage: string): string {
        const text = this._readOptionalString(value);
        if (!text) {
            throw new Error(errorMessage);
        }
        return text;
    }

    private _readRequiredPath(value: unknown, errorMessage: string): string {
        const pathValue = this._readOptionalPath(value);
        if (!pathValue) {
            throw new Error(errorMessage);
        }
        return pathValue;
    }

    private _clampPositiveInteger(value: unknown, fallback: number): number {
        if (typeof value !== 'number' || !Number.isFinite(value)) {
            return fallback;
        }
        return Math.max(1, Math.floor(value));
    }

    private _formatSeverity(severity: vscode.DiagnosticSeverity): string {
        switch (severity) {
            case vscode.DiagnosticSeverity.Error:
                return 'Error';
            case vscode.DiagnosticSeverity.Warning:
                return 'Warning';
            case vscode.DiagnosticSeverity.Information:
                return 'Info';
            case vscode.DiagnosticSeverity.Hint:
                return 'Hint';
            default:
                return 'Unknown';
        }
    }

    private _toArray<T>(value: T | readonly T[]): readonly T[] {
        return Array.isArray(value) ? value : [value];
    }

    private _truncate(content: string): string {
        if (content.length <= AiChatToolExecutor._maxToolPayloadChars) {
            return content;
        }
        return `${content.slice(0, AiChatToolExecutor._maxToolPayloadChars)}\n... truncated`;
    }

    private _error(tool: AiChatToolName, message: string): AiChatToolResult {
        return {
            ok: false,
            tool,
            summary: `${tool} failed.`,
            content: message,
        };
    }

    private async _resolvePythonPath(workspaceRoot: string): Promise<string> {
        const config = vscode.workspace.getConfiguration('docBasedCoding');
        const configuredPythonPath = config.get<string>('pythonPath');
        if (configuredPythonPath) {
            return configuredPythonPath;
        }
        const candidates = [
            path.join(workspaceRoot, '.venv', 'Scripts', 'python.exe'),
            path.join(workspaceRoot, '.venv', 'bin', 'python'),
            path.join(workspaceRoot, '.venv-release-test', 'Scripts', 'python.exe'),
            path.join(workspaceRoot, '.venv-release-test', 'bin', 'python'),
            path.join(workspaceRoot, 'venv', 'Scripts', 'python.exe'),
            path.join(workspaceRoot, 'venv', 'bin', 'python'),
        ];
        for (const candidate of candidates) {
            try {
                await vscode.workspace.fs.stat(vscode.Uri.file(candidate));
                return candidate;
            } catch {
                // Continue with the next candidate.
            }
        }
        return 'python';
    }

    private _resolveProgressGraphSourceRoot(workspaceRoot: string): string {
        const config = vscode.workspace.getConfiguration('docBasedCoding');
        const configuredSourceRoot = config.get<string>('sourceRoot');
        const candidates = [
            configuredSourceRoot ? path.resolve(configuredSourceRoot) : '',
            path.resolve(workspaceRoot),
        ].filter(Boolean);
        for (const candidate of candidates) {
            try {
                const marker = path.join(candidate, 'tools', 'progress_graph', '__init__.py');
                // Synchronous path check keeps the generated Python command small and deterministic.
                accessSync(marker);
                return candidate;
            } catch {
                // Continue with the next candidate.
            }
        }
        return path.resolve(workspaceRoot);
    }
}
