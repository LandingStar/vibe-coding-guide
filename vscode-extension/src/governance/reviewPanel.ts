/**
 * Review Panel WebView (P5).
 *
 * Shows detailed governance decision information when a BLOCK occurs.
 * Provides approve/reject workflow with override capability.
 */

import * as vscode from 'vscode';
import { GovernanceDecision } from './types';

interface ReviewRequest {
    uri: string;
    decision: GovernanceDecision;
    timestamp: string;
}

export class ReviewPanelProvider implements vscode.Disposable {
    private _panel: vscode.WebviewPanel | undefined;
    private _pendingRequest: ReviewRequest | undefined;
    private _resolveReview: ((approved: boolean) => void) | undefined;
    private readonly _outputChannel: vscode.OutputChannel;
    private readonly _disposables: vscode.Disposable[] = [];

    constructor(outputChannel: vscode.OutputChannel) {
        this._outputChannel = outputChannel;
    }

    /**
     * Show the review panel for a blocked governance decision.
     * Returns true if the user approves (override), false if rejected.
     */
    async requestReview(uri: string, decision: GovernanceDecision): Promise<boolean> {
        this._pendingRequest = {
            uri,
            decision,
            timestamp: new Date().toISOString(),
        };

        this._showPanel();
        this._updateContent();

        return new Promise<boolean>((resolve) => {
            this._resolveReview = resolve;
        });
    }

    private _showPanel(): void {
        if (this._panel) {
            this._panel.reveal(vscode.ViewColumn.Beside);
            return;
        }

        this._panel = vscode.window.createWebviewPanel(
            'docBasedCoding.reviewPanel',
            'Governance Review',
            vscode.ViewColumn.Beside,
            {
                enableScripts: true,
                retainContextWhenHidden: true,
            },
        );

        this._panel.onDidDispose(() => {
            this._panel = undefined;
            // If disposed without decision, treat as reject
            if (this._resolveReview) {
                this._resolveReview(false);
                this._resolveReview = undefined;
            }
        }, null, this._disposables);

        this._panel.webview.onDidReceiveMessage(
            (message: { command: string }) => {
                switch (message.command) {
                    case 'approve':
                        this._outputChannel.appendLine('[Review] User approved override.');
                        if (this._resolveReview) {
                            this._resolveReview(true);
                            this._resolveReview = undefined;
                        }
                        this._panel?.dispose();
                        break;
                    case 'reject':
                        this._outputChannel.appendLine('[Review] User rejected override.');
                        if (this._resolveReview) {
                            this._resolveReview(false);
                            this._resolveReview = undefined;
                        }
                        this._panel?.dispose();
                        break;
                }
            },
            null,
            this._disposables,
        );
    }

    private _updateContent(): void {
        if (!this._panel || !this._pendingRequest) {
            return;
        }

        const { uri, decision, timestamp } = this._pendingRequest;
        const nonce = getNonce();

        this._panel.webview.html = /* html */ `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'nonce-${nonce}'; script-src 'nonce-${nonce}';">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style nonce="${nonce}">
        body {
            font-family: var(--vscode-font-family);
            padding: 20px;
            color: var(--vscode-foreground);
            background: var(--vscode-editor-background);
        }
        h1 {
            color: var(--vscode-errorForeground);
            font-size: 1.4em;
            margin-bottom: 16px;
        }
        .info-row {
            margin: 8px 0;
            padding: 8px 12px;
            background: var(--vscode-editor-inactiveSelectionBackground);
            border-radius: 4px;
        }
        .label {
            font-weight: bold;
            color: var(--vscode-descriptionForeground);
        }
        .message {
            margin: 16px 0;
            padding: 12px;
            background: var(--vscode-inputValidation-warningBackground);
            border: 1px solid var(--vscode-inputValidation-warningBorder);
            border-radius: 4px;
            white-space: pre-wrap;
        }
        .actions {
            margin-top: 24px;
            display: flex;
            gap: 12px;
        }
        button {
            padding: 8px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
        }
        .approve {
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
        }
        .approve:hover {
            background: var(--vscode-button-hoverBackground);
        }
        .reject {
            background: var(--vscode-button-secondaryBackground);
            color: var(--vscode-button-secondaryForeground);
        }
        .reject:hover {
            background: var(--vscode-button-secondaryHoverBackground);
        }
    </style>
</head>
<body>
    <h1>⛔ Governance Block</h1>

    <div class="info-row">
        <span class="label">File:</span> ${escapeHtml(uri)}
    </div>
    <div class="info-row">
        <span class="label">Time:</span> ${escapeHtml(timestamp)}
    </div>
    <div class="info-row">
        <span class="label">Reason:</span> ${escapeHtml(decision.reason ?? 'Unknown')}
    </div>
    ${decision.traceId ? `<div class="info-row"><span class="label">Trace ID:</span> ${escapeHtml(decision.traceId)}</div>` : ''}

    <div class="message">${escapeHtml(decision.denyMessage ?? 'This action was blocked by governance policy.')}</div>

    <div class="actions">
        <button class="approve" onclick="approve()">✓ Override & Save</button>
        <button class="reject" onclick="reject()">✗ Cancel</button>
    </div>

    <script nonce="${nonce}">
        const vscode = acquireVsCodeApi();
        function approve() { vscode.postMessage({ command: 'approve' }); }
        function reject() { vscode.postMessage({ command: 'reject' }); }
    </script>
</body>
</html>`;
    }

    dispose(): void {
        this._panel?.dispose();
        for (const d of this._disposables) {
            d.dispose();
        }
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

function escapeHtml(str: string): string {
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
