/**
 * Config Explorer TreeView.
 *
 * Displays extension settings, user-global config, and active pack config
 * in a single tree.  Supports inline editing of user-global config fields
 * via the `docBasedCoding.editConfigItem` command.
 */

import * as vscode from 'vscode';
import { MCPClient } from '../mcp/client';

type ConfigTreeItem = ConfigGroupItem | ConfigLeafItem;

/** Top-level group node. */
class ConfigGroupItem extends vscode.TreeItem {
    constructor(
        public readonly groupId: string,
        label: string,
        icon: string,
    ) {
        super(label, vscode.TreeItemCollapsibleState.Collapsed);
        this.iconPath = new vscode.ThemeIcon(icon);
        this.contextValue = 'configGroup';
    }
}

/** Leaf node showing a single key=value pair. */
class ConfigLeafItem extends vscode.TreeItem {
    constructor(
        public readonly fieldKey: string,
        label: string,
        detail: string,
        icon: string,
        public readonly editable: boolean = false,
    ) {
        super(label, vscode.TreeItemCollapsibleState.None);
        this.description = detail;
        this.iconPath = new vscode.ThemeIcon(icon);
        this.contextValue = editable ? 'configEditable' : 'configReadonly';
    }
}

interface UserConfigData {
    extra_pack_dirs: string[];
    default_model: string | null;
    default_llm_params: Record<string, unknown>;
}

export class ConfigExplorerProvider implements vscode.TreeDataProvider<ConfigTreeItem> {
    private _onDidChangeTreeData = new vscode.EventEmitter<ConfigTreeItem | undefined>();
    readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

    private _mcpClient: MCPClient | null;
    private _userConfig: UserConfigData | null = null;
    private _packNames: string[] = [];
    private _error: string | null = null;

    constructor(mcpClient?: MCPClient) {
        this._mcpClient = mcpClient ?? null;
    }

    updateClient(client: MCPClient): void {
        this._mcpClient = client;
    }

    async refresh(): Promise<void> {
        try {
            if (!this._mcpClient || !this._mcpClient.isRunning) {
                this._error = 'MCP server not running';
                this._userConfig = null;
                this._packNames = [];
            } else {
                // Fetch pack info which includes user_config in pipeline info
                const packInfo = (await this._mcpClient.callTool('get_pack_info', {
                    level: 'manifest',
                })) as {
                    packs?: Array<{ name: string }>;
                    user_config?: UserConfigData;
                };
                this._userConfig = packInfo.user_config ?? null;
                this._packNames = (packInfo.packs ?? []).map((p) => p.name);
                this._error = null;
            }
        } catch (err) {
            this._error = err instanceof Error ? err.message : String(err);
            this._userConfig = null;
            this._packNames = [];
        }
        this._onDidChangeTreeData.fire(undefined);
    }

    getTreeItem(element: ConfigTreeItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: ConfigTreeItem): ConfigTreeItem[] {
        if (!element) {
            // Root level — three groups
            if (this._error) {
                return [new ConfigLeafItem('', 'Error', this._error, 'error')];
            }
            return [
                new ConfigGroupItem('extension', 'Extension Settings', 'gear'),
                new ConfigGroupItem('userGlobal', 'User-Global Config', 'home'),
                new ConfigGroupItem('packs', 'Active Packs', 'package'),
            ];
        }

        if (element instanceof ConfigGroupItem) {
            switch (element.groupId) {
                case 'extension':
                    return this._getExtensionSettings();
                case 'userGlobal':
                    return this._getUserGlobalItems();
                case 'packs':
                    return this._getPackItems();
            }
        }

        return [];
    }

    /** Read docBasedCoding.* settings from VS Code configuration. */
    private _getExtensionSettings(): ConfigLeafItem[] {
        const config = vscode.workspace.getConfiguration('docBasedCoding');
        const items: ConfigLeafItem[] = [];

        const keys = [
            'pythonPath',
            'serverMode',
            'autoStart',
            'terminal.killOnBlock',
            'llm.family',
        ];

        for (const key of keys) {
            const val = config.get(key);
            const display = val === '' || val === undefined ? '(default)' : String(val);
            items.push(new ConfigLeafItem(`ext.${key}`, key, display, 'symbol-property'));
        }

        return items;
    }

    /** Show user-global config fields (editable via MCP). */
    private _getUserGlobalItems(): ConfigLeafItem[] {
        if (!this._userConfig) {
            return [new ConfigLeafItem('', 'Not loaded', 'Start MCP server to load', 'info')];
        }

        const cfg = this._userConfig;
        return [
            new ConfigLeafItem(
                'extra_pack_dirs',
                'extra_pack_dirs',
                cfg.extra_pack_dirs.length > 0 ? cfg.extra_pack_dirs.join(', ') : '(none)',
                'folder-library',
                true,
            ),
            new ConfigLeafItem(
                'default_model',
                'default_model',
                cfg.default_model ?? '(none)',
                'symbol-string',
                true,
            ),
            new ConfigLeafItem(
                'default_llm_params',
                'default_llm_params',
                Object.keys(cfg.default_llm_params).length > 0
                    ? JSON.stringify(cfg.default_llm_params)
                    : '(empty)',
                'json',
                true,
            ),
        ];
    }

    /** List active pack names. */
    private _getPackItems(): ConfigLeafItem[] {
        if (this._packNames.length === 0) {
            return [new ConfigLeafItem('', 'No packs loaded', '', 'info')];
        }
        return this._packNames.map(
            (name) => new ConfigLeafItem(`pack.${name}`, name, '', 'package'),
        );
    }

    /**
     * Edit a user-global config field via MCP `update_user_config`.
     * Called by the `docBasedCoding.editConfigItem` command.
     */
    async editField(item: ConfigLeafItem): Promise<void> {
        if (!this._mcpClient || !this._mcpClient.isRunning) {
            vscode.window.showErrorMessage('MCP server not running.');
            return;
        }

        const field = item.fieldKey;
        let newValue: unknown;

        if (field === 'extra_pack_dirs') {
            const current = this._userConfig?.extra_pack_dirs.join(', ') ?? '';
            const input = await vscode.window.showInputBox({
                prompt: 'Enter comma-separated directory paths',
                value: current,
                placeHolder: '/path/to/packs1, /path/to/packs2',
            });
            if (input === undefined) { return; }
            newValue = input.split(',').map((s) => s.trim()).filter(Boolean);
        } else if (field === 'default_model') {
            const current = this._userConfig?.default_model ?? '';
            const input = await vscode.window.showInputBox({
                prompt: 'Enter default LLM model identifier',
                value: current,
                placeHolder: 'gpt-4o',
            });
            if (input === undefined) { return; }
            newValue = input || null;
        } else if (field === 'default_llm_params') {
            const current = JSON.stringify(this._userConfig?.default_llm_params ?? {}, null, 2);
            const input = await vscode.window.showInputBox({
                prompt: 'Enter LLM params as JSON object',
                value: current,
                placeHolder: '{"temperature": 0.7}',
            });
            if (input === undefined) { return; }
            try {
                newValue = JSON.parse(input);
            } catch {
                vscode.window.showErrorMessage('Invalid JSON.');
                return;
            }
        } else {
            return;
        }

        try {
            await this._mcpClient.callTool('update_user_config', { field, value: newValue });
            vscode.window.showInformationMessage(`Updated ${field}.`);
            await this.refresh();
        } catch (err) {
            const msg = err instanceof Error ? err.message : String(err);
            vscode.window.showErrorMessage(`Failed to update ${field}: ${msg}`);
        }
    }
}
