/**
 * Config Panel WebviewView.
 *
 * Provides user-global config editing together with a small installed-state
 * runtime/package management surface for the current workspace.
 */

import * as vscode from 'vscode';
import { MCPClient } from '../mcp/client';
import { ManagedLLMProvider } from '../llm/types';
import {
    getRuntimePackageStatus,
    installRuntimePackagesFromWorkspaceRelease,
    uninstallRuntimePackages,
} from '../setup/runtimePackageManager';

interface ConfigPanelProviderOptions {
    outputChannel: vscode.OutputChannel;
    projectRoot: string;
    extensionVersion: string;
    resolvePythonPath: () => Promise<string>;
    startServer: (pythonPath: string) => Promise<void>;
    stopServer: () => void;
    isServerRunning: () => boolean;
}

export class ConfigPanelProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'configPanel';

    private _view: vscode.WebviewView | undefined;
    private _mcpClient: MCPClient | null;
    private _llmProvider: ManagedLLMProvider | null;
    private readonly _outputChannel: vscode.OutputChannel;
    private readonly _projectRoot: string;
    private readonly _extensionVersion: string;
    private readonly _resolvePythonPath: () => Promise<string>;
    private readonly _startServer: (pythonPath: string) => Promise<void>;
    private readonly _stopServer: () => void;
    private readonly _isServerRunning: () => boolean;

    constructor(options: ConfigPanelProviderOptions, mcpClient?: MCPClient, llmProvider?: ManagedLLMProvider) {
        this._outputChannel = options.outputChannel;
        this._projectRoot = options.projectRoot;
        this._extensionVersion = options.extensionVersion;
        this._resolvePythonPath = options.resolvePythonPath;
        this._startServer = options.startServer;
        this._stopServer = options.stopServer;
        this._isServerRunning = options.isServerRunning;
        this._mcpClient = mcpClient ?? null;
        this._llmProvider = llmProvider ?? null;
    }

    updateClient(client: MCPClient): void {
        this._mcpClient = client;
    }

    updateLLMProvider(provider: ManagedLLMProvider): void {
        this._llmProvider = provider;
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

        webviewView.webview.onDidReceiveMessage(async (message: {
            command: string;
            field?: string;
            value?: unknown;
            action?: string;
        }) => {
            switch (message.command) {
                case 'load':
                    await this._sendConfigToWebview();
                    await this._sendPackageStatusToWebview();
                    await this._sendAvailableModels();
                    break;
                case 'save':
                    if (message.field && message.value !== undefined) {
                        await this._saveField(message.field, message.value);
                    }
                    break;
                case 'packageAction':
                    if (message.action) {
                        await this._handlePackageAction(message.action);
                    }
                    break;
            }
        });

        this._updateHtml();
    }

    async refresh(): Promise<void> {
        if (this._view) {
            await this._sendConfigToWebview();
            await this._sendPackageStatusToWebview();
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

    private async _sendPackageStatusToWebview(): Promise<void> {
        if (!this._view) { return; }

        try {
            const config = vscode.workspace.getConfiguration('docBasedCoding');
            const status = await getRuntimePackageStatus({
                projectRoot: this._projectRoot,
                extensionVersion: this._extensionVersion,
                mcpServerRunning: this._isServerRunning(),
                autoStart: config.get<boolean>('autoStart') ?? true,
                serverMode: config.get<string>('serverMode') ?? 'auto',
                outputChannel: this._outputChannel,
            });
            this._view.webview.postMessage({ command: 'packageStatus', data: status, error: null });
        } catch (err) {
            const msg = err instanceof Error ? err.message : String(err);
            this._view.webview.postMessage({ command: 'packageStatus', data: null, error: msg });
        }
    }

    /** Fetch available model families from the active provider and send them to the webview. */
    private async _sendAvailableModels(): Promise<void> {
        if (!this._view) { return; }
        if (!this._llmProvider) {
            this._view.webview.postMessage({ command: 'models', families: [] });
            return;
        }

        try {
            const families = await this._llmProvider.listModelFamilies();
            this._view.webview.postMessage({ command: 'models', families });
        } catch {
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
            vscode.commands.executeCommand('docBasedCoding.refreshConfig');
        } catch (err) {
            const msg = err instanceof Error ? err.message : String(err);
            this._view.webview.postMessage({ command: 'saveResult', ok: false, error: msg });
        }
    }

    private async _handlePackageAction(action: string): Promise<void> {
        if (!this._view) { return; }

        try {
            if (action === 'disable') {
                this._stopServer();
                await vscode.workspace.getConfiguration('docBasedCoding').update(
                    'autoStart',
                    false,
                    vscode.ConfigurationTarget.Workspace,
                );
                this._view.webview.postMessage({
                    command: 'packageActionResult',
                    ok: true,
                    message: 'Stopped the current MCP server and disabled auto-start for this workspace.',
                });
                await vscode.commands.executeCommand('docBasedCoding.refreshConfig');
                await this._sendPackageStatusToWebview();
                return;
            }

            const pythonPath = await this._resolvePythonPath();
            const wasRunning = this._isServerRunning();

            if (action === 'uninstall') {
                const choice = await vscode.window.showWarningMessage(
                    'Uninstall doc-based-coding-runtime and doc-loop-vibe-coding from the selected Python environment?',
                    { modal: true },
                    'Uninstall',
                );
                if (choice !== 'Uninstall') {
                    this._view.webview.postMessage({
                        command: 'packageActionResult',
                        ok: false,
                        message: 'Uninstall cancelled.',
                    });
                    await this._sendPackageStatusToWebview();
                    return;
                }
            }

            if (wasRunning) {
                this._stopServer();
            }

            let result;
            if (action === 'reinstall' || action === 'update') {
                result = await installRuntimePackagesFromWorkspaceRelease(
                    this._projectRoot,
                    pythonPath,
                    this._outputChannel,
                );
                if (result.ok && wasRunning) {
                    try {
                        await this._startServer(pythonPath);
                    } catch (err) {
                        const msg = err instanceof Error ? err.message : String(err);
                        result = {
                            ok: false,
                            message: `Packages updated, but MCP restart failed: ${msg}`,
                            runtimeVersion: result.runtimeVersion,
                            instanceVersion: result.instanceVersion,
                        };
                    }
                }
            } else if (action === 'uninstall') {
                result = await uninstallRuntimePackages(pythonPath, this._outputChannel);
            } else {
                result = {
                    ok: false,
                    message: `Unknown package action: ${action}`,
                    runtimeVersion: null,
                    instanceVersion: null,
                };
            }

            this._view.webview.postMessage({
                command: 'packageActionResult',
                ok: result.ok,
                message: result.message,
            });
        } catch (err) {
            const msg = err instanceof Error ? err.message : String(err);
            this._view.webview.postMessage({
                command: 'packageActionResult',
                ok: false,
                message: msg,
            });
        }

        await vscode.commands.executeCommand('docBasedCoding.refreshConfig');
        await this._sendPackageStatusToWebview();
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
        .package-grid {
            display: grid;
            grid-template-columns: minmax(110px, 132px) 1fr;
            gap: 6px 12px;
            align-items: start;
        }
        .package-label {
            color: var(--vscode-descriptionForeground);
            font-weight: 600;
        }
    </style>
</head>
<body>
    <h3>Runtime & Package Status</h3>

    <div id="packageLoading" class="loading">Loading package status...</div>
    <div id="packageSection" style="display:none;">
        <div class="field-group">
            <div id="packageSummary" style="color:var(--vscode-descriptionForeground); margin-bottom: 10px;"></div>
            <div class="package-grid">
                <div class="package-label">Extension</div><div id="pkgExtensionVersion"></div>
                <div class="package-label">Python</div><div id="pkgPythonVersion"></div>
                <div class="package-label">Python Path</div><div id="pkgPythonPath"></div>
                <div class="package-label">Runtime</div><div id="pkgRuntimeVersion"></div>
                <div class="package-label">Instance Pack</div><div id="pkgInstanceVersion"></div>
                <div class="package-label">Server</div><div id="pkgServerStatus"></div>
                <div class="package-label">Auto Start</div><div id="pkgAutoStart"></div>
                <div class="package-label">Server Mode</div><div id="pkgServerMode"></div>
                <div class="package-label">Workspace Release</div><div id="pkgReleaseArtifacts"></div>
            </div>
            <div class="btn-row" style="margin-top:12px; flex-wrap: wrap;">
                <button class="btn-save" data-package-action="update" onclick="runPackageAction('update')">Update</button>
                <button class="btn-save" data-package-action="reinstall" onclick="runPackageAction('reinstall')">Reinstall</button>
                <button class="btn-reload" data-package-action="disable" onclick="runPackageAction('disable')">Disable</button>
                <button class="btn-reload" data-package-action="uninstall" onclick="runPackageAction('uninstall')">Uninstall</button>
                <button class="btn-reload" onclick="loadPanel()">↻ Refresh Status</button>
            </div>
        </div>
    </div>

    <h3 style="margin-top: 18px;">User-Global Config</h3>

    <div id="configContent" class="loading">Loading...</div>
    <div id="configForm" style="display:none;">
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
                <button class="btn-reload" disabled title="Complex editor - planned for future release">Edit (coming soon)</button>
            </div>
        </div>

        <div class="btn-row" style="margin-top:12px;">
            <button class="btn-reload" onclick="loadPanel()">↻ Reload</button>
        </div>
    </div>

    <div id="status" class="status"></div>

    <script nonce="${nonce}">
        const vscode = acquireVsCodeApi();

        function loadPanel() {
            document.getElementById('packageLoading').style.display = 'block';
            document.getElementById('packageSection').style.display = 'none';
            document.getElementById('configContent').style.display = 'block';
            document.getElementById('configContent').textContent = 'Loading...';
            document.getElementById('configForm').style.display = 'none';
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

        function runPackageAction(action) {
            setPackageButtonsDisabled(true);
            hideStatus();
            vscode.postMessage({ command: 'packageAction', action });
        }

        function setPackageButtonsDisabled(disabled) {
            document.querySelectorAll('[data-package-action]').forEach(button => {
                button.disabled = disabled;
            });
        }

        function setPackageField(id, value) {
            document.getElementById(id).textContent = value;
        }

        function renderPackageStatus(data, error) {
            document.getElementById('packageLoading').style.display = 'none';
            document.getElementById('packageSection').style.display = 'block';
            setPackageButtonsDisabled(false);

            if (error || !data) {
                document.getElementById('packageSummary').textContent = error || 'Failed to load package status.';
                setPackageField('pkgExtensionVersion', '(unknown)');
                setPackageField('pkgPythonVersion', '(unavailable)');
                setPackageField('pkgPythonPath', '(unavailable)');
                setPackageField('pkgRuntimeVersion', '(unavailable)');
                setPackageField('pkgInstanceVersion', '(unavailable)');
                setPackageField('pkgServerStatus', '(unavailable)');
                setPackageField('pkgAutoStart', '(unavailable)');
                setPackageField('pkgServerMode', '(unavailable)');
                setPackageField('pkgReleaseArtifacts', '(unavailable)');
                return;
            }

            document.getElementById('packageSummary').textContent = data.summary || '';
            setPackageField('pkgExtensionVersion', data.extensionVersion || '(unknown)');
            setPackageField('pkgPythonVersion', data.pythonVersion || '(not found)');
            setPackageField('pkgPythonPath', data.pythonPath || '(not found)');
            setPackageField('pkgRuntimeVersion', data.runtimeVersion || '(not installed)');
            setPackageField('pkgInstanceVersion', data.instanceVersion || '(not installed)');
            setPackageField('pkgServerStatus', data.mcpServerRunning ? 'running' : 'stopped');
            setPackageField('pkgAutoStart', data.autoStart ? 'enabled' : 'disabled');
            setPackageField('pkgServerMode', data.serverMode || '(default)');

            const releaseItems = [];
            if ((data.releaseArtifacts.wheelFiles || []).length > 0) {
                releaseItems.push((data.releaseArtifacts.wheelFiles || []).join(', '));
            }
            if (data.releaseArtifacts.zipFile) {
                releaseItems.push(data.releaseArtifacts.zipFile);
            }
            if ((data.releaseArtifacts.vsixFiles || []).length > 0) {
                releaseItems.push((data.releaseArtifacts.vsixFiles || []).join(', '));
            }
            setPackageField('pkgReleaseArtifacts', releaseItems.length > 0 ? releaseItems.join(' | ') : '(none found)');
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
                document.getElementById('configContent').style.display = 'none';
                if (msg.error) {
                    document.getElementById('configContent').style.display = 'block';
                    document.getElementById('configContent').textContent = msg.error;
                    document.getElementById('configForm').style.display = 'none';
                    return;
                }
                const data = msg.data;
                if (!data) {
                    document.getElementById('configContent').style.display = 'block';
                    document.getElementById('configContent').textContent = 'No user config loaded (config.json may not exist).';
                    document.getElementById('configForm').style.display = 'block';
                    return;
                }
                document.getElementById('configForm').style.display = 'block';
                document.getElementById('extraPackDirs').value =
                    (data.extra_pack_dirs || []).join(', ');
                setSelectedModel(data.default_model || '');
                const params = data.default_llm_params || {};
                document.getElementById('llmParamsPreview').textContent =
                    Object.keys(params).length > 0
                        ? JSON.stringify(params, null, 2)
                        : '(empty)';
            } else if (msg.command === 'packageStatus') {
                renderPackageStatus(msg.data, msg.error);
            } else if (msg.command === 'models') {
                populateModelSelect(msg.families || []);
            } else if (msg.command === 'saveResult') {
                if (msg.ok) {
                    showStatus('Saved successfully.', false);
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
            } else if (msg.command === 'packageActionResult') {
                setPackageButtonsDisabled(false);
                showStatus(msg.message || 'Package action completed.', !msg.ok);
                loadPanel();
            }
        });

        let _currentModel = '';

        function populateModelSelect(families) {
            const sel = document.getElementById('defaultModel');
            const prev = sel.value || _currentModel;
            sel.innerHTML = '<option value="">(none)</option>';
            families.forEach(f => {
                const opt = document.createElement('option');
                opt.value = f;
                opt.textContent = f;
                sel.appendChild(opt);
            });
            const otherOpt = document.createElement('option');
            otherOpt.value = '__other__';
            otherOpt.textContent = 'Other... (coming soon)';
            otherOpt.disabled = true;
            sel.appendChild(otherOpt);
            if (prev) {
                sel.value = prev;
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
                _currentModel = model;
            }
        }

        loadPanel();
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
