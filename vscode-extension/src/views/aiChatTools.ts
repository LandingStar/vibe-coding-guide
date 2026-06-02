import * as path from 'node:path';
import * as vscode from 'vscode';
import type { AiChatToolName } from './aiChatActionProtocol';

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
}