/**
 * Pack Explorer TreeView (P2).
 *
 * Displays loaded packs from the MCP server's get_pack_info tool.
 * Shows pack name, kind, scope, provides, and description.
 */

import * as vscode from 'vscode';
import { MCPClient } from '../mcp/client';
import { PackInfo } from '../mcp/types';

type PackTreeItem = PackGroupItem | PackDetailItem;

/** Top-level item representing a single pack. */
class PackGroupItem extends vscode.TreeItem {
    constructor(
        public readonly packName: string,
        public readonly packKind: string,
        public readonly packDescription: string | undefined,
        public readonly provides: string[],
        public readonly scope: string,
    ) {
        super(packName, vscode.TreeItemCollapsibleState.Collapsed);
        this.description = packKind;
        this.tooltip = packDescription ?? `${packName} (${packKind})`;
        this.iconPath = new vscode.ThemeIcon('package');
        this.contextValue = 'pack';
    }
}

/** Child item showing a property of a pack. */
class PackDetailItem extends vscode.TreeItem {
    constructor(label: string, detail: string, icon: string) {
        super(label, vscode.TreeItemCollapsibleState.None);
        this.description = detail;
        this.iconPath = new vscode.ThemeIcon(icon);
    }
}

export class PackExplorerProvider implements vscode.TreeDataProvider<PackTreeItem> {
    private _onDidChangeTreeData = new vscode.EventEmitter<PackTreeItem | undefined>();
    readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

    private _packInfo: PackInfo | null = null;
    private _error: string | null = null;
    private _mcpClient: MCPClient | null;

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
                this._packInfo = null;
            } else {
                const result = await this._mcpClient.callTool('get_pack_info', { level: 'manifest' });
                this._packInfo = result as PackInfo;
                this._error = null;
            }
        } catch (err) {
            this._error = err instanceof Error ? err.message : String(err);
            this._packInfo = null;
        }
        this._onDidChangeTreeData.fire(undefined);
    }

    getTreeItem(element: PackTreeItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: PackTreeItem): PackTreeItem[] {
        if (element && element instanceof PackGroupItem) {
            const items: PackDetailItem[] = [];
            items.push(new PackDetailItem('scope', element.scope, 'symbol-namespace'));
            if (element.provides.length > 0) {
                items.push(new PackDetailItem('provides', element.provides.join(', '), 'extensions'));
            }
            if (element.packDescription) {
                items.push(new PackDetailItem('description', element.packDescription, 'info'));
            }
            return items;
        }

        // Root level
        if (this._error) {
            const item = new PackDetailItem('Error', this._error, 'error');
            return [item];
        }

        if (!this._packInfo) {
            return [new PackDetailItem('', 'Click refresh to load packs', 'info')];
        }

        const packs = this._packInfo.packs ?? [];
        if (packs.length === 0) {
            return [new PackDetailItem('', 'No packs loaded', 'info')];
        }

        return packs.map(
            (p) => new PackGroupItem(p.name, p.kind, p.description, p.provides ?? [], p.scope ?? ''),
        );
    }
}
