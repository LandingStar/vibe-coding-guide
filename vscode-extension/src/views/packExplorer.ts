/**
 * Pack Explorer TreeView (P2 placeholder).
 *
 * Provides a minimal TreeDataProvider so the view container
 * doesn't show an error. Full implementation is P2 scope.
 */

import * as vscode from 'vscode';

class PackItem extends vscode.TreeItem {
    constructor(label: string) {
        super(label, vscode.TreeItemCollapsibleState.None);
        this.iconPath = new vscode.ThemeIcon('package');
    }
}

export class PackExplorerProvider implements vscode.TreeDataProvider<PackItem> {
    private _onDidChangeTreeData = new vscode.EventEmitter<PackItem | undefined>();
    readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

    getTreeItem(element: PackItem): vscode.TreeItem {
        return element;
    }

    getChildren(): PackItem[] {
        return [
            new PackItem('Start MCP server to view packs'),
        ];
    }

    refresh(): void {
        this._onDidChangeTreeData.fire(undefined);
    }
}
