/**
 * File Lifecycle Governance (P6+).
 *
 * Intercepts file creation, deletion, and rename events.
 * Calls MCP governance_decide before each operation.
 * On BLOCK, shows a warning and aborts the operation.
 */

import * as vscode from 'vscode';
import { MCPGovernanceInterceptor } from './interceptor';

export function registerFileLifecycleListeners(
    context: vscode.ExtensionContext,
    interceptor: MCPGovernanceInterceptor,
    outputChannel: vscode.OutputChannel,
): void {
    // Intercept file creation
    const createListener = vscode.workspace.onWillCreateFiles((event) => {
        const uris = event.files.map((f) => f.fsPath).join(', ');

        event.waitUntil(
            (async () => {
                const decision = await interceptor.beforeAgentAction({
                    type: 'file-write',
                    description: `create: ${uris}`,
                });

                if (!decision.allow) {
                    outputChannel.appendLine(
                        `[Governance] BLOCKED file creation: ${uris.slice(0, 100)}`
                    );
                    vscode.window.showWarningMessage(
                        decision.denyMessage ?? `Governance blocked file creation: ${uris.slice(0, 80)}`
                    );
                    throw new Error('File creation blocked by governance.');
                }

                return undefined as unknown as vscode.WorkspaceEdit;
            })(),
        );
    });

    // Intercept file deletion
    const deleteListener = vscode.workspace.onWillDeleteFiles((event) => {
        const uris = event.files.map((f) => f.fsPath).join(', ');

        event.waitUntil(
            (async () => {
                const decision = await interceptor.beforeAgentAction({
                    type: 'file-write',
                    description: `delete: ${uris}`,
                });

                if (!decision.allow) {
                    outputChannel.appendLine(
                        `[Governance] BLOCKED file deletion: ${uris.slice(0, 100)}`
                    );
                    vscode.window.showWarningMessage(
                        decision.denyMessage ?? `Governance blocked file deletion: ${uris.slice(0, 80)}`
                    );
                    throw new Error('File deletion blocked by governance.');
                }

                return undefined as unknown as vscode.WorkspaceEdit;
            })(),
        );
    });

    // Intercept file rename
    const renameListener = vscode.workspace.onWillRenameFiles((event) => {
        const desc = event.files
            .map((f) => `${f.oldUri.fsPath} → ${f.newUri.fsPath}`)
            .join(', ');

        event.waitUntil(
            (async () => {
                const decision = await interceptor.beforeAgentAction({
                    type: 'file-write',
                    description: `rename: ${desc}`,
                });

                if (!decision.allow) {
                    outputChannel.appendLine(
                        `[Governance] BLOCKED file rename: ${desc.slice(0, 100)}`
                    );
                    vscode.window.showWarningMessage(
                        decision.denyMessage ?? `Governance blocked file rename: ${desc.slice(0, 80)}`
                    );
                    throw new Error('File rename blocked by governance.');
                }

                return undefined as unknown as vscode.WorkspaceEdit;
            })(),
        );
    });

    context.subscriptions.push(createListener, deleteListener, renameListener);
    outputChannel.appendLine('[Governance] File lifecycle listeners registered (create/delete/rename).');
}
