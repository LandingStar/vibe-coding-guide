/**
 * Decision Log Viewer TreeView (P2).
 *
 * Displays recent governance decisions from the MCP server's
 * query_decision_logs tool response.
 */

import * as vscode from 'vscode';
import { MCPClient } from '../mcp/client';
import { DecisionLogEntry } from '../mcp/types';

/** Tree item representing a single decision log entry. */
class DecisionLogItem extends vscode.TreeItem {
    constructor(public readonly entry: DecisionLogEntry) {
        super(
            `${entry.intent}`,
            vscode.TreeItemCollapsibleState.None,
        );

        const time = entry.timestamp?.replace('T', ' ').slice(0, 19) ?? '';
        this.description = `${entry.decision} • ${time}`;
        this.tooltip = [
            `Decision: ${entry.decision}`,
            `Intent: ${entry.intent}`,
            `Gate: ${entry.gate}`,
            `Trace: ${entry.trace_id}`,
            `Time: ${entry.timestamp}`,
            `Input: ${entry.input_summary ?? ''}`,
        ].join('\n');

        if (entry.decision === 'ALLOW') {
            this.iconPath = new vscode.ThemeIcon('pass', new vscode.ThemeColor('testing.iconPassed'));
        } else {
            this.iconPath = new vscode.ThemeIcon('error', new vscode.ThemeColor('testing.iconFailed'));
        }
    }
}

export class DecisionLogViewerProvider implements vscode.TreeDataProvider<DecisionLogItem> {
    private _onDidChangeTreeData = new vscode.EventEmitter<DecisionLogItem | undefined>();
    readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

    private _entries: DecisionLogEntry[] = [];
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
                this._entries = [];
            } else {
                const result = await this._mcpClient.callTool('query_decision_logs', { limit: 50 });
                const data = result as { entries?: DecisionLogEntry[] };
                this._entries = data.entries ?? [];
                this._error = null;
            }
        } catch (err) {
            this._error = err instanceof Error ? err.message : String(err);
            this._entries = [];
        }
        this._onDidChangeTreeData.fire(undefined);
    }

    getTreeItem(element: DecisionLogItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: DecisionLogItem): DecisionLogItem[] {
        if (element) {
            return [];
        }

        if (this._error) {
            const item = new DecisionLogItem({
                log_id: '',
                decision_id: '',
                trace_id: '',
                timestamp: '',
                input_summary: this._error,
                decision: 'BLOCK',
                intent: `Error: ${this._error}`,
                gate: '',
            });
            return [item];
        }

        if (this._entries.length === 0) {
            const item = new DecisionLogItem({
                log_id: '',
                decision_id: '',
                trace_id: '',
                timestamp: '',
                input_summary: 'No decision logs found',
                decision: 'ALLOW',
                intent: 'No entries — click refresh',
                gate: '',
            });
            return [item];
        }

        return this._entries.map((e) => new DecisionLogItem(e));
    }
}
