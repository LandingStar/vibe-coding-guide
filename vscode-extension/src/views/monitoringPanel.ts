import * as vscode from 'vscode';
import * as path from 'path';
import { existsSync } from 'fs';
import { execFile } from 'child_process';
import { promisify } from 'util';

const exec = promisify(execFile);

export class MonitoringPanel implements vscode.Disposable {
    private _panel: vscode.WebviewPanel | undefined;
    private _autoRefreshTimer: ReturnType<typeof setInterval> | undefined;
    private _autoRefreshEnabled = false;
    private _lastSignature = '';
    private _disposables: vscode.Disposable[] = [];

    constructor(
        private readonly _extensionUri: vscode.Uri,
        private readonly _outputChannel: vscode.OutputChannel,
    ) {}

    async open(workspace: vscode.WorkspaceFolder): Promise<void> {
        if (this._panel) {
            this._panel.reveal();
            await this._refreshSnapshot(workspace);
            return;
        }

        this._panel = vscode.window.createWebviewPanel(
            'docBasedCoding.monitoringDashboard',
            'Monitoring Dashboard',
            vscode.ViewColumn.Two,
            {
                enableScripts: true,
                enableFindWidget: true,
                retainContextWhenHidden: true,
                localResourceRoots: [
                    workspace.uri,
                    vscode.Uri.joinPath(this._extensionUri, 'dist'),
                ],
            },
        );

        this._panel.onDidDispose(() => {
            this._stopAutoRefresh();
            this._panel = undefined;
        }, null, this._disposables);

        this._panel.onDidChangeViewState((e) => {
            if (!e.webviewPanel.visible) {
                this._stopAutoRefresh();
            } else if (this._autoRefreshEnabled) {
                this._startAutoRefresh(workspace);
            }
        }, null, this._disposables);

        this._panel.webview.onDidReceiveMessage(
            (msg) => this._handleMessage(msg, workspace),
            null,
            this._disposables,
        );

        await this._refreshSnapshot(workspace);
    }

    async refresh(workspace: vscode.WorkspaceFolder): Promise<void> {
        await this._refreshSnapshot(workspace);
    }

    private async _handleMessage(msg: any, workspace: vscode.WorkspaceFolder): Promise<void> {
        switch (msg.command) {
            case 'refresh':
                await this._refreshSnapshot(workspace);
                break;
            case 'autoRefresh':
                this._autoRefreshEnabled = msg.enabled;
                if (msg.enabled) {
                    this._startAutoRefresh(workspace);
                } else {
                    this._stopAutoRefresh();
                }
                break;
            case 'copyToClipboard':
                await vscode.env.clipboard.writeText(msg.text);
                break;
            case 'openDocument': {
                const docPath = vscode.Uri.joinPath(workspace.uri, msg.path);
                try {
                    const doc = await vscode.workspace.openTextDocument(docPath);
                    await vscode.window.showTextDocument(doc, vscode.ViewColumn.One);
                } catch {
                    this._outputChannel.appendLine(`[monitoring] could not open: ${msg.path}`);
                }
                break;
            }
        }
    }

    private _startAutoRefresh(workspace: vscode.WorkspaceFolder): void {
        this._stopAutoRefresh();
        const interval = vscode.workspace
            .getConfiguration('docBasedCoding')
            .get<number>('monitoring.autoRefreshIntervalMs', 5000);
        this._autoRefreshTimer = setInterval(
            () => this._refreshSnapshot(workspace),
            interval,
        );
    }

    private _stopAutoRefresh(): void {
        if (this._autoRefreshTimer) {
            clearInterval(this._autoRefreshTimer);
            this._autoRefreshTimer = undefined;
        }
    }

    private async _refreshSnapshot(workspace: vscode.WorkspaceFolder): Promise<void> {
        try {
            const payload = await this._runCli(workspace.uri.fsPath);
            const signature = JSON.stringify(payload);
            if (signature === this._lastSignature) { return; }
            this._lastSignature = signature;
            this._render(payload);
        } catch (err) {
            const msg = err instanceof Error ? err.message : String(err);
            this._outputChannel.appendLine(`[monitoring] snapshot error: ${msg}`);
            this._renderError(msg);
        }
    }

    private async _runCli(workspaceRoot: string): Promise<any> {
        const config = vscode.workspace.getConfiguration(
            'docBasedCoding',
            vscode.Uri.file(workspaceRoot),
        );
        const pythonPath = config.get<string>('pythonPath')
            || this._resolvePythonPath(workspaceRoot);
        const sourceRoot = this._resolveSourceRoot(workspaceRoot, pythonPath);
        const codexDir = path.join(workspaceRoot, '.codex');

        const snapshotPath = path.join(codexDir, 'scheduler', 'state.json');
        const eventLogPath = path.join(codexDir, 'scheduler', 'events.jsonl');

        const args = [
            '-m', 'src', 'scheduler', 'inspect-monitoring-snapshot',
            '--snapshot-path', snapshotPath,
            '--event-log-path', eventLogPath,
        ];

        const optionalPaths: [string, string][] = [
            ['--delivery-state-path', path.join(codexDir, 'scheduler', 'leader-worker-delivery-state.json')],
            ['--runtime-invocation-log-path', path.join(codexDir, 'runtime', 'invocations.jsonl')],
            ['--artifact-store-path', path.join(codexDir, 'orchestration', 'exchange-artifacts.json')],
            ['--live-codex-smoke-report-path', path.join(codexDir, 'scheduler', 'live-codex-concurrent-worker-smoke-report.json')],
        ];

        for (const [flag, filePath] of optionalPaths) {
            if (existsSync(filePath)) {
                args.push(flag, filePath);
            }
        }

        let stdout: string;
        try {
            const result = await exec(pythonPath, args, {
                cwd: sourceRoot,
                timeout: 15000,
                maxBuffer: 10 * 1024 * 1024,
            });
            stdout = result.stdout;
        } catch (err: any) {
            if (err.stdout && err.stdout.trim().startsWith('{')) {
                stdout = err.stdout;
            } else {
                throw err;
            }
        }

        return JSON.parse(stdout);
    }

    private _resolveSourceRoot(workspaceRoot: string, pythonPath: string): string {
        const config = vscode.workspace.getConfiguration(
            'docBasedCoding',
            vscode.Uri.file(workspaceRoot),
        );
        const configured = config.get<string>('sourceRoot') || '';
        const candidates: string[] = [];
        if (configured) { candidates.push(path.resolve(configured)); }
        candidates.push(path.resolve(workspaceRoot));
        if (path.isAbsolute(pythonPath)) {
            candidates.push(path.resolve(path.dirname(pythonPath), '..', '..'));
        }
        for (const candidate of candidates) {
            try {
                if (existsSync(path.join(candidate, 'src', '__main__.py'))) {
                    return candidate;
                }
            } catch { /* skip */ }
        }
        return workspaceRoot;
    }

    private _resolvePythonPath(projectRoot: string): string {
        const candidates = [
            path.join(projectRoot, '.venv', 'Scripts', 'python.exe'),
            path.join(projectRoot, '.venv', 'bin', 'python'),
            path.join(projectRoot, '.venv-mcp', 'Scripts', 'python.exe'),
            path.join(projectRoot, '.venv-mcp', 'bin', 'python'),
            path.join(projectRoot, 'venv', 'Scripts', 'python.exe'),
            path.join(projectRoot, 'venv', 'bin', 'python'),
        ];
        for (const candidate of candidates) {
            if (existsSync(candidate)) { return candidate; }
        }
        return 'python';
    }

    private _render(payload: any): void {
        if (!this._panel) { return; }
        this._panel.webview.html = buildMonitoringHtml(
            this._panel.webview,
            this._extensionUri,
            payload,
        );
    }

    private _renderError(errorMsg: string): void {
        if (!this._panel) { return; }
        const errorPayload = {
            schema_version: 'monitoring-snapshot.v1',
            ok: false,
            next_action: 'investigate snapshot error',
            paths: {},
            scheduler: { task_state_counts: {}, target_task_states: {}, waiting_task_ids: [], review_required_task_ids: [], completed_task_output_refs: [] },
            delivery: { state_counts: {}, actionable_pending_codex_delivery_count: 0, latest_records: [] },
            runtimeInvocations: { counts: {}, latest_records: [], concurrency: { latestProviderCounts: {}, failedTaskIds: [], latestRecords: [], liveOverlapProven: false, overlapPairCount: 0 } },
            artifacts: { output_artifact_refs: [], review_artifact_refs: [], worker_patch_artifact_refs: [] },
            liveCodexSmoke: { exists: false, ok: false, verdict: 'unavailable', diagnostic: 'snapshot error', path: '', counts: {}, firstConcurrentBatch: { taskIds: [], invocationIds: [] }, overlap: { proven: false, pairs: [] } },
            workerReports: { mode: 'leader-owned-consumer', directWorkerTrajectoryMutationAllowed: false, consumerCommand: '', procedureDoc: '', schema: '', notes: [] },
            operatorSignals: [{ severity: 'error', kind: 'snapshot_error', message: errorMsg, suggestedAction: 'check output channel and CLI paths' }],
            errors: [errorMsg],
            authoritySplit: { readModelOnly: true, providerExecuted: false, schedulerStateMutated: false, schedulerEventLogMutated: false, dispatcherStateMutated: false, deliveryStateMutated: false, deliveryLogMutated: false, exchangeStoreMutated: false, runtimeInvocationLogMutated: false, localWorkTrajectoryMutated: false, rawTranscriptExposed: false },
        };
        this._panel.webview.html = buildMonitoringHtml(
            this._panel.webview,
            this._extensionUri,
            errorPayload,
        );
    }

    dispose(): void {
        this._stopAutoRefresh();
        this._panel?.dispose();
        this._disposables.forEach((d) => d.dispose());
    }
}

function generateNonce(): string {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < 32; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
}

function buildMonitoringHtml(
    webview: vscode.Webview,
    extensionUri: vscode.Uri,
    payload: any,
): string {
    const scriptUri = webview.asWebviewUri(
        vscode.Uri.joinPath(extensionUri, 'dist', 'webviews', 'monitoringDashboard.js'),
    );
    const styleUri = webview.asWebviewUri(
        vscode.Uri.joinPath(extensionUri, 'dist', 'webviews', 'monitoringDashboard.css'),
    );
    const nonce = generateNonce();
    const escapedPayload = JSON.stringify(payload).replace(/</g, '\\u003c');

    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="Content-Security-Policy"
        content="default-src 'none'; style-src ${webview.cspSource}; script-src 'nonce-${nonce}';">
  <link rel="stylesheet" href="${styleUri}">
  <title>Monitoring Dashboard</title>
</head>
<body>
  <div id="monitoring-root"></div>
  <script type="application/json" id="monitoringPayload">${escapedPayload}</script>
  <script nonce="${nonce}" src="${scriptUri}"></script>
</body>
</html>`;
}
