/**
 * Constraint Dashboard TreeView (P1).
 *
 * Displays C1-C8 constraint status from the MCP server's
 * check_constraints tool response.
 */

import * as vscode from 'vscode';
import { MCPClient } from '../mcp/client';
import { CheckConstraintsResult, ConstraintViolation } from '../mcp/types';

/** Tree item representing a single constraint or a summary node. */
class ConstraintItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly violation?: ConstraintViolation,
    ) {
        super(label, collapsibleState);

        if (violation) {
            this.description = violation.severity;
            this.tooltip = violation.details ?? violation.description;

            switch (violation.severity) {
                case 'error':
                    this.iconPath = new vscode.ThemeIcon('error', new vscode.ThemeColor('testing.iconFailed'));
                    break;
                case 'warning':
                    this.iconPath = new vscode.ThemeIcon('warning', new vscode.ThemeColor('list.warningForeground'));
                    break;
                case 'info':
                    this.iconPath = new vscode.ThemeIcon('info', new vscode.ThemeColor('charts.blue'));
                    break;
            }
        } else {
            // Summary / status node
            this.iconPath = new vscode.ThemeIcon('pass', new vscode.ThemeColor('testing.iconPassed'));
        }
    }
}

export class ConstraintDashboardProvider implements vscode.TreeDataProvider<ConstraintItem> {
    private _onDidChangeTreeData = new vscode.EventEmitter<ConstraintItem | undefined>();
    readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

    private _lastResult: CheckConstraintsResult | null = null;
    private _error: string | null = null;
    private _mcpClient: MCPClient | null;

    constructor(mcpClient?: MCPClient) {
        this._mcpClient = mcpClient ?? null;
    }

    /** Update the MCP client reference (e.g. after setup wizard completes). */
    updateClient(client: MCPClient): void {
        this._mcpClient = client;
    }

    /** Refresh constraint data from MCP server. */
    async refresh(): Promise<void> {
        try {
            if (!this._mcpClient || !this._mcpClient.isRunning) {
                this._error = 'MCP server not running';
                this._lastResult = null;
            } else {
                const result = await this._mcpClient.callTool('check_constraints');
                this._lastResult = result as CheckConstraintsResult;
                this._error = null;
            }
        } catch (err) {
            this._error = err instanceof Error ? err.message : String(err);
            this._lastResult = null;
        }
        this._onDidChangeTreeData.fire(undefined);
    }

    getTreeItem(element: ConstraintItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: ConstraintItem): ConstraintItem[] {
        if (element) {
            // No children for leaf items
            return [];
        }

        // Root level
        if (this._error) {
            const item = new ConstraintItem(
                `Error: ${this._error}`,
                vscode.TreeItemCollapsibleState.None,
            );
            item.iconPath = new vscode.ThemeIcon('error');
            return [item];
        }

        if (!this._lastResult) {
            const item = new ConstraintItem(
                'Click refresh to load constraints',
                vscode.TreeItemCollapsibleState.None,
            );
            item.iconPath = new vscode.ThemeIcon('info');
            return [item];
        }

        const violations = this._lastResult.violations ?? [];

        if (violations.length === 0) {
            return [
                new ConstraintItem(
                    'All constraints satisfied',
                    vscode.TreeItemCollapsibleState.None,
                ),
            ];
        }

        return violations.map(
            (v) =>
                new ConstraintItem(
                    `${v.constraint_id}: ${v.description}`,
                    vscode.TreeItemCollapsibleState.None,
                    v,
                ),
        );
    }
}
