import * as vscode from 'vscode';
import { existsSync, readFileSync } from 'fs';

type ProgressGraphPreviewMessage = {
    command: 'refresh' | 'revealArtifact';
};

type ProgressGraphPreviewState = {
    artifactPath: string;
    lastLoadedAt: string;
    previewHtml: string | null;
};

type ProgressGraphArtifactRegenerator = (workspaceFolder: vscode.WorkspaceFolder) => Promise<void>;

export class ProgressGraphPreviewPanel implements vscode.Disposable {
    private _panel: vscode.WebviewPanel | undefined;
    private _workspaceFolder: vscode.WorkspaceFolder | undefined;
    private readonly _outputChannel: vscode.OutputChannel;
  private readonly _regenerateArtifacts: ProgressGraphArtifactRegenerator;
    private readonly _disposables: vscode.Disposable[] = [];

  constructor(outputChannel: vscode.OutputChannel, regenerateArtifacts: ProgressGraphArtifactRegenerator) {
        this._outputChannel = outputChannel;
    this._regenerateArtifacts = regenerateArtifacts;
    }

    async open(workspaceFolder: vscode.WorkspaceFolder): Promise<void> {
        this._workspaceFolder = workspaceFolder;
    this._ensurePanel();
    await this._reload();
    }

  async refresh(workspaceFolder?: vscode.WorkspaceFolder): Promise<void> {
    if (workspaceFolder) {
      this._workspaceFolder = workspaceFolder;
    }

    if (!this._workspaceFolder) {
            return;
        }

    this._ensurePanel();

    try {
      await vscode.window.withProgress(
        {
          location: vscode.ProgressLocation.Notification,
          title: 'Refreshing progress graph preview',
        },
        async () => {
          await this._regenerateArtifacts(this._workspaceFolder!);
        },
      );
      await this._reload();
      vscode.window.showInformationMessage('Progress graph artifacts regenerated and preview refreshed.');
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      this._outputChannel.appendLine(`[ProgressGraphPreview] Failed to refresh preview artifacts: ${message}`);
      vscode.window.showErrorMessage(`Failed to refresh progress graph preview: ${message}`);
    }
  }

  async revealArtifact(workspaceFolder?: vscode.WorkspaceFolder): Promise<void> {
    if (workspaceFolder) {
      this._workspaceFolder = workspaceFolder;
    }

    if (!this._workspaceFolder) {
      return;
    }

    const artifactUri = this._previewUri(this._workspaceFolder);
    await vscode.commands.executeCommand('revealInExplorer', artifactUri);
  }

  dispose(): void {
    this._panel?.dispose();
    for (const disposable of this._disposables) {
      disposable.dispose();
    }
  }

  private async _reload(): Promise<void> {
    if (!this._panel || !this._workspaceFolder) {
      return;
    }

    const state = this._loadState(this._workspaceFolder);
    this._panel.title = state.previewHtml ? 'Progress Graph' : 'Progress Graph (Missing Artifact)';
    this._panel.webview.html = this._buildHtml(this._panel.webview, state);

        if (state.previewHtml) {
            this._outputChannel.appendLine(`[ProgressGraphPreview] Refreshed preview artifact: ${state.artifactPath}`);
        } else {
            this._outputChannel.appendLine(`[ProgressGraphPreview] Missing preview artifact: ${state.artifactPath}`);
        }
    }

  private _ensurePanel(): void {
    if (this._panel) {
      this._panel.reveal(this._panel.viewColumn ?? vscode.ViewColumn.Beside);
      return;
        }

    this._panel = vscode.window.createWebviewPanel(
      'docBasedCoding.progressGraphPreview',
      'Progress Graph',
      vscode.ViewColumn.Beside,
      {
        enableScripts: true,
        enableFindWidget: true,
        retainContextWhenHidden: true,
      },
    );

    this._panel.onDidDispose(() => {
      this._panel = undefined;
    }, null, this._disposables);

    this._panel.webview.onDidReceiveMessage(
      async (message: ProgressGraphPreviewMessage) => {
        switch (message.command) {
          case 'refresh':
            await this.refresh();
            break;
          case 'revealArtifact':
            await this.revealArtifact();
            break;
        }
      },
      null,
      this._disposables,
    );
    }

    private _previewUri(workspaceFolder: vscode.WorkspaceFolder): vscode.Uri {
        return vscode.Uri.joinPath(workspaceFolder.uri, '.codex', 'progress-graph', 'latest.html');
    }

    private _loadState(workspaceFolder: vscode.WorkspaceFolder): ProgressGraphPreviewState {
        const previewUri = this._previewUri(workspaceFolder);
        const previewHtml = existsSync(previewUri.fsPath)
            ? readFileSync(previewUri.fsPath, 'utf-8')
            : null;

        return {
            artifactPath: previewUri.fsPath,
            lastLoadedAt: new Date().toISOString(),
            previewHtml,
        };
    }

    private _buildHtml(webview: vscode.Webview, state: ProgressGraphPreviewState): string {
        const nonce = getNonce();
        const previewPayload = JSON.stringify(state.previewHtml ?? '');
        const escapedPath = escapeHtml(state.artifactPath);
        const escapedLoadedAt = escapeHtml(state.lastLoadedAt);
        const emptyState = !state.previewHtml
            ? `<section class="empty-state">
    <h2>Preview Artifact Missing</h2>
    <p>当前宿主工作流已经成立，但 workspace 中还没有可加载的 <code>latest.html</code> artifact。</p>
    <p>请先刷新 progress graph artifacts，然后点击顶部的 <strong>Refresh Preview</strong>。</p>
  </section>`
            : `<div class="frame-wrap"><iframe id="previewFrame" title="Progress Graph Preview" sandbox="allow-same-origin"></iframe></div>`;

        return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'nonce-${nonce}'; script-src 'nonce-${nonce}'; frame-src 'self';">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Progress Graph</title>
  <style nonce="${nonce}">
    :root {
      color-scheme: light dark;
    }
    * {
      box-sizing: border-box;
    }
    body {
      margin: 0;
      color: var(--vscode-editor-foreground);
      background: var(--vscode-editor-background);
      font-family: var(--vscode-font-family);
      display: grid;
      grid-template-rows: auto 1fr;
      height: 100vh;
      overflow: hidden;
    }
    .topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 14px 18px;
      border-bottom: 1px solid var(--vscode-panel-border);
      background: color-mix(in srgb, var(--vscode-sideBar-background) 70%, transparent);
    }
    .title-group {
      min-width: 0;
    }
    .title {
      margin: 0;
      font-size: 1.05rem;
      font-weight: 700;
    }
    .subtitle {
      margin-top: 4px;
      color: var(--vscode-descriptionForeground);
      font-size: 0.86rem;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .actions {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }
    button {
      border: 1px solid var(--vscode-button-border, transparent);
      background: var(--vscode-button-background);
      color: var(--vscode-button-foreground);
      border-radius: 8px;
      padding: 7px 12px;
      cursor: pointer;
      font: inherit;
      font-size: 0.9rem;
    }
    button.secondary {
      background: var(--vscode-button-secondaryBackground);
      color: var(--vscode-button-secondaryForeground);
    }
    button:hover {
      background: var(--vscode-button-hoverBackground);
    }
    button.secondary:hover {
      background: var(--vscode-button-secondaryHoverBackground);
    }
    .body {
      min-height: 0;
      padding: 0;
      background: var(--vscode-editor-background);
    }
    .frame-wrap {
      height: 100%;
    }
    iframe {
      width: 100%;
      height: 100%;
      border: 0;
      background: white;
    }
    .empty-state {
      max-width: 760px;
      margin: 28px auto;
      padding: 22px 24px;
      border-radius: 14px;
      border: 1px solid var(--vscode-panel-border);
      background: var(--vscode-sideBar-background);
      line-height: 1.65;
    }
    .empty-state h2 {
      margin: 0 0 12px;
      font-size: 1.1rem;
    }
    code {
      font-family: var(--vscode-editor-font-family);
      background: var(--vscode-textCodeBlock-background);
      padding: 1px 4px;
      border-radius: 4px;
    }
    @media (max-width: 760px) {
      .topbar {
        grid-auto-flow: row;
        align-items: start;
      }
      .actions {
        width: 100%;
        justify-content: flex-start;
      }
    }
  </style>
</head>
<body>
  <header class="topbar">
    <div class="title-group">
      <h1 class="title">Progress Graph</h1>
      <div class="subtitle">artifact: ${escapedPath} · loaded: ${escapedLoadedAt}</div>
    </div>
    <div class="actions">
      <button id="refreshButton">Refresh Preview</button>
      <button id="revealButton" class="secondary">Reveal Artifact</button>
    </div>
  </header>
  <main class="body">
    ${emptyState}
  </main>
  <script nonce="${nonce}">
    const vscode = acquireVsCodeApi();
    const previewHtml = ${previewPayload};
    const refreshButton = document.getElementById('refreshButton');
    const revealButton = document.getElementById('revealButton');

    refreshButton?.addEventListener('click', () => {
      vscode.postMessage({ command: 'refresh' });
    });

    revealButton?.addEventListener('click', () => {
      vscode.postMessage({ command: 'revealArtifact' });
    });

    const frame = document.getElementById('previewFrame');
    if (frame && previewHtml) {
      frame.srcdoc = previewHtml;
    }
  </script>
</body>
</html>`;
    }
}

function getNonce(): string {
    let text = '';
    const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    for (let i = 0; i < 32; i++) {
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return text;
}

function escapeHtml(value: string): string {
    return value
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}