/**
 * Config Panel WebviewView (Slice B).
 *
 * Provides a form-based UI for editing user-global config fields
 * (~/.doc-based-coding/config.json).  Embedded in the Activity Bar
 * sidebar via WebviewViewProvider.
 */

import * as vscode from 'vscode';
import { MCPClient } from '../mcp/client';

export class ConfigPanelProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'configPanel';

    private _view: vscode.WebviewView | undefined;
    private _mcpClient: MCPClient | null;
    private readonly _outputChannel: vscode.OutputChannel;

    constructor(outputChannel: vscode.OutputChannel, mcpClient?: MCPClient) {
        this._outputChannel = outputChannel;
        this._mcpClient = mcpClient ?? null;
    }

    updateClient(client: MCPClient): void {
        this._mcpClient = client;
    }

    resolveWebviewView(
        webviewView: vscode.WebviewView,
        _context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ): void {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
        };

        webviewView.webview.onDidReceiveMessage(async (message: { command: string; field?: string; value?: unknown }) => {
            switch (message.command) {
                case 'load':
                    await this._sendConfigToWebview();
                    await this._sendAvailableModels();
                    break;
                case 'save':
                    if (message.field && message.value !== undefined) {
                        await this._saveField(message.field, message.value);
                    }
                    break;
            }
        });

        this._updateHtml();
    }

    async refresh(): Promise<void> {
        if (this._view) {
            await this._sendConfigToWebview();
        }
    }

    private async _sendConfigToWebview(): Promise<void> {
        if (!this._view) { return; }

        if (!this._mcpClient || !this._mcpClient.isRunning) {
            this._view.webview.postMessage({ command: 'config', data: null, error: 'MCP server not running' });
            return;
        }

        try {
            const info = (await this._mcpClient.callTool('get_pack_info', { level: 'manifest' })) as {
                user_config?: {
                    extra_pack_dirs: string[];
                    default_model: string | null;
                    default_llm_params: Record<string, unknown>;
                };
            };
            this._view.webview.postMessage({ command: 'config', data: info.user_config ?? null, error: null });
        } catch (err) {
            const msg = err instanceof Error ? err.message : String(err);
            this._view.webview.postMessage({ command: 'config', data: null, error: msg });
        }
    }

    /** Fetch available Copilot model families and send to webview. */
    private async _sendAvailableModels(): Promise<void> {
        if (!this._view) { return; }

        try {
            const allModels = await vscode.lm.selectChatModels({ vendor: 'copilot' });
            const seen = new Set<string>();
            const families: string[] = [];
            for (const m of allModels) {
                if (!seen.has(m.family)) {
                    seen.add(m.family);
                    families.push(m.family);
                }
            }
            this._view.webview.postMessage({ command: 'models', families });
        } catch {
            // Copilot not available — send empty list, user can still type manually
            this._view.webview.postMessage({ command: 'models', families: [] });
        }
    }

    private async _saveField(field: string, value: unknown): Promise<void> {
        if (!this._view) { return; }

        if (!this._mcpClient || !this._mcpClient.isRunning) {
            this._view.webview.postMessage({ command: 'saveResult', ok: false, error: 'MCP server not running' });
            return;
        }

        try {
            const result = await this._mcpClient.callTool('update_user_config', { field, value });
            this._view.webview.postMessage({ command: 'saveResult', ok: true, data: result });
            this._outputChannel.appendLine(`[ConfigPanel] Updated field '${field}'.`);
            // Also fire a refresh event so the TreeView stays in sync
            vscode.commands.executeCommand('docBasedCoding.refreshConfig');
        } catch (err) {
            const msg = err instanceof Error ? err.message : String(err);
            this._view.webview.postMessage({ command: 'saveResult', ok: false, error: msg });
        }
    }

    private _updateHtml(): void {
        if (!this._view) { return; }

        const nonce = getNonce();

        this._view.webview.html = /* html */ `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Security-Policy"
          content="default-src 'none'; style-src 'nonce-${nonce}'; script-src 'nonce-${nonce}';">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style nonce="${nonce}">
        body {
            font-family: var(--vscode-font-family);
            font-size: var(--vscode-font-size);
            padding: 12px;
            color: var(--vscode-foreground);
            background: var(--vscode-sideBar-background);
        }
        h3 {
            margin: 0 0 12px 0;
            font-size: 1.1em;
            color: var(--vscode-foreground);
        }
        .field-group {
            margin-bottom: 14px;
        }
        label {
            display: block;
            margin-bottom: 4px;
            font-weight: 600;
            color: var(--vscode-descriptionForeground);
            font-size: 0.9em;
        }
        input, textarea, select {
            width: 100%;
            box-sizing: border-box;
            padding: 6px 8px;
            border: 1px solid var(--vscode-input-border);
            background: var(--vscode-input-background);
            color: var(--vscode-input-foreground);
            border-radius: 3px;
            font-family: var(--vscode-editor-font-family);
            font-size: var(--vscode-editor-font-size);
        }
        textarea {
            min-height: 60px;
            resize: vertical;
        }
        input:focus, textarea:focus, select:focus {
            outline: none;
            border-color: var(--vscode-focusBorder);
        }
        .btn-row {
            display: flex;
            gap: 8px;
            margin-top: 4px;
        }
        button {
            padding: 5px 14px;
            border: none;
            border-radius: 3px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 500;
        }
        .btn-save {
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
        }
        .btn-save:hover {
            background: var(--vscode-button-hoverBackground);
        }
        .btn-reload {
            background: var(--vscode-button-secondaryBackground);
            color: var(--vscode-button-secondaryForeground);
        }
        .btn-reload:hover {
            background: var(--vscode-button-secondaryHoverBackground);
        }
        .status {
            margin-top: 8px;
            padding: 6px 8px;
            border-radius: 3px;
            font-size: 0.85em;
            display: none;
        }
        .status.success {
            display: block;
            background: var(--vscode-inputValidation-infoBackground);
            border: 1px solid var(--vscode-inputValidation-infoBorder);
        }
        .status.error {
            display: block;
            background: var(--vscode-inputValidation-errorBackground);
            border: 1px solid var(--vscode-inputValidation-errorBorder);
        }
        .loading {
            color: var(--vscode-descriptionForeground);
            font-style: italic;
        }
    </style>
</head>
<body>
    <h3>User-Global Config</h3>

    <div id="content" class="loading">Loading...</div>
    <div id="form" style="display:none;">
        <div class="field-group">
            <label for="extraPackDirs">extra_pack_dirs</label>
            <input type="text" id="extraPackDirs" placeholder="/path/to/packs1, /path/to/packs2">
            <div class="btn-row">
                <button class="btn-save" onclick="saveField('extra_pack_dirs')">Save</button>
            </div>
        </div>

        <div class="field-group">
            <label for="defaultModel">default_model</label>
            <select id="defaultModel">
                <option value="">(none)</option>
            </select>
            <div class="btn-row">
                <button class="btn-save" onclick="saveField('default_model')">Save</button>
            </div>
        </div>

        <div class="field-group">
            <label>default_llm_params</label>
            <div id="llmParamsPreview" style="padding:4px 0;color:var(--vscode-descriptionForeground);font-size:0.9em;">(empty)</div>
            <div class="btn-row">
                <button class="btn-reload" disabled title="Complex editor — planned for future release">Edit (coming soon)</button>
            </div>
        </div>

        <div class="btn-row" style="margin-top:12px;">
            <button class="btn-reload" onclick="loadConfig()">↻ Reload</button>
        </div>
    </div>

    <div id="status" class="status"></div>

    <script nonce="${nonce}">
        const vscode = acquireVsCodeApi();

        function loadConfig() {
            document.getElementById('content').style.display = 'block';
            document.getElementById('content').textContent = 'Loading...';
            document.getElementById('form').style.display = 'none';
            hideStatus();
            vscode.postMessage({ command: 'load' });
        }

        function saveField(field) {
            let value;
            if (field === 'extra_pack_dirs') {
                const raw = document.getElementById('extraPackDirs').value;
                value = raw.split(',').map(s => s.trim()).filter(Boolean);
            } else if (field === 'default_model') {
                const raw = document.getElementById('defaultModel').value;
                value = raw || null;
            }
            vscode.postMessage({ command: 'save', field, value });
        }

        function showStatus(msg, isError) {
            const el = document.getElementById('status');
            el.textContent = msg;
            el.className = 'status ' + (isError ? 'error' : 'success');
        }

        function hideStatus() {
            const el = document.getElementById('status');
            el.className = 'status';
        }

        window.addEventListener('message', event => {
            const msg = event.data;
            if (msg.command === 'config') {
                document.getElementById('content').style.display = 'none';
                if (msg.error) {
                    document.getElementById('content').style.display = 'block';
                    document.getElementById('content').textContent = msg.error;
                    document.getElementById('form').style.display = 'none';
                    return;
                }
                const data = msg.data;
                if (!data) {
                    document.getElementById('content').style.display = 'block';
                    document.getElementById('content').textContent = 'No user config loaded (config.json may not exist).';
                    document.getElementById('form').style.display = 'block';
                    return;
                }
                document.getElementById('form').style.display = 'block';
                document.getElementById('extraPackDirs').value =
                    (data.extra_pack_dirs || []).join(', ');
                // Set model select — the option may not exist yet if models haven't loaded
                setSelectedModel(data.default_model || '');
                // Show llm params preview
                const params = data.default_llm_params || {};
                document.getElementById('llmParamsPreview').textContent =
                    Object.keys(params).length > 0
                        ? JSON.stringify(params, null, 2)
                        : '(empty)';
            } else if (msg.command === 'models') {
                populateModelSelect(msg.families || []);
            } else if (msg.command === 'saveResult') {
                if (msg.ok) {
                    showStatus('Saved successfully.', false);
                    // Reload data to reflect actual state
                    if (msg.data) {
                        document.getElementById('extraPackDirs').value =
                            (msg.data.extra_pack_dirs || []).join(', ');
                        setSelectedModel(msg.data.default_model || '');
                        const params = msg.data.default_llm_params || {};
                        document.getElementById('llmParamsPreview').textContent =
                            Object.keys(params).length > 0
                                ? JSON.stringify(params, null, 2)
                                : '(empty)';
                    }
                } else {
                    showStatus('Save failed: ' + (msg.error || 'Unknown error'), true);
                }
            }
        });

        let _currentModel = '';

        function populateModelSelect(families) {
            const sel = document.getElementById('defaultModel');
            // Preserve current selection
            const prev = sel.value || _currentModel;
            sel.innerHTML = '<option value="">(none)</option>';
            families.forEach(f => {
                const opt = document.createElement('option');
                opt.value = f;
                opt.textContent = f;
                sel.appendChild(opt);
            });
            // Add "Other..." option for future custom model entry
            const otherOpt = document.createElement('option');
            otherOpt.value = '__other__';
            otherOpt.textContent = 'Other... (coming soon)';
            otherOpt.disabled = true;
            sel.appendChild(otherOpt);
            // Restore selection
            if (prev) {
                sel.value = prev;
                // If prev model isn't in the list, add it as a custom option
                if (sel.value !== prev) {
                    const custom = document.createElement('option');
                    custom.value = prev;
                    custom.textContent = prev + ' (custom)';
                    sel.insertBefore(custom, otherOpt);
                    sel.value = prev;
                }
            }
        }

        function setSelectedModel(model) {
            _currentModel = model;
            const sel = document.getElementById('defaultModel');
            sel.value = model;
            if (sel.value !== model && model) {
                // Model not yet in list — will be set when models load
                _currentModel = model;
            }
        }

        // Auto-load on panel open
        loadConfig();
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
