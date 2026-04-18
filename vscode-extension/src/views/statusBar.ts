/**
 * Governance Status Bar Item (P2).
 *
 * Shows constraint violation count in the VS Code status bar.
 * Clicking navigates to the Constraint Dashboard view.
 */

import * as vscode from 'vscode';

export class GovernanceStatusBar implements vscode.Disposable {
    private readonly _item: vscode.StatusBarItem;

    constructor() {
        this._item = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Left,
            50,
        );
        this._item.command = 'constraintDashboard.focus';
        this._item.tooltip = 'Doc-Based Coding — Constraint Status';
        this._update(null);
        this._item.show();
    }

    /** Update the status bar with the current violation count. */
    update(violationCount: number | null): void {
        this._update(violationCount);
    }

    private _update(violationCount: number | null): void {
        if (violationCount === null) {
            this._item.text = '$(shield) DBC: —';
            this._item.backgroundColor = undefined;
        } else if (violationCount === 0) {
            this._item.text = '$(shield) DBC: OK';
            this._item.backgroundColor = undefined;
        } else {
            this._item.text = `$(shield) DBC: ${violationCount} violation${violationCount > 1 ? 's' : ''}`;
            this._item.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
        }
    }

    dispose(): void {
        this._item.dispose();
    }
}
