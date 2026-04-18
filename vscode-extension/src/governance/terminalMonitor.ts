/**
 * Terminal Governance Monitor (P6).
 *
 * Hooks into VS Code Shell Integration to monitor terminal commands.
 * Calls MCP governance_decide for each command; on BLOCK shows a warning
 * and optionally kills the running command.
 */

import * as vscode from 'vscode';
import { MCPGovernanceInterceptor } from './interceptor';
import { checkGitRemoteGuard } from './gitRemoteGuard';

export class TerminalGovernanceMonitor implements vscode.Disposable {
    private readonly _disposables: vscode.Disposable[] = [];
    private readonly _outputChannel: vscode.OutputChannel;
    private _interceptor: MCPGovernanceInterceptor;
    private _killOnBlock: boolean;

    constructor(
        interceptor: MCPGovernanceInterceptor,
        outputChannel: vscode.OutputChannel,
        killOnBlock = false,
    ) {
        this._interceptor = interceptor;
        this._outputChannel = outputChannel;
        this._killOnBlock = killOnBlock;
    }

    /**
     * Start monitoring terminal shell executions.
     * Requires VS Code 1.93+ with shell integration active in terminal.
     */
    activate(context: vscode.ExtensionContext): void {
        const startListener = vscode.window.onDidStartTerminalShellExecution(
            async (event) => {
                const commandLine = event.execution.commandLine.value;
                if (!commandLine.trim()) {
                    return;
                }

                this._outputChannel.appendLine(
                    `[Terminal] Command started: ${commandLine.slice(0, 100)}`
                );

                // ── Hard guard: remote git operations (not overridable) ──
                const gitGuard = checkGitRemoteGuard(commandLine);
                if (gitGuard.blocked) {
                    this._outputChannel.appendLine(
                        `[Terminal] HARD BLOCK (git ${gitGuard.matchedSubcommand}): ${commandLine.slice(0, 80)}`
                    );
                    // Immediately kill the command
                    event.terminal.sendText('\x03', false); // Ctrl+C
                    vscode.window.showErrorMessage(
                        gitGuard.message!,
                        { modal: true },
                    );
                    return; // Do not continue to governance interceptor
                }

                const decision = await this._interceptor.beforeTerminalCommand(commandLine);

                if (!decision.allow) {
                    this._outputChannel.appendLine(
                        `[Terminal] BLOCKED: ${commandLine.slice(0, 80)}`
                    );

                    const message = decision.denyMessage
                        ?? `Governance blocked terminal command: ${commandLine.slice(0, 60)}`;

                    if (this._killOnBlock) {
                        // Send SIGINT to the terminal to kill the running command
                        event.terminal.sendText('\x03', false); // Ctrl+C
                        vscode.window.showWarningMessage(
                            `${message}\n\nThe command was terminated.`,
                            'OK',
                        );
                    } else {
                        const choice = await vscode.window.showWarningMessage(
                            message,
                            'Kill Command',
                            'Dismiss',
                        );
                        if (choice === 'Kill Command') {
                            event.terminal.sendText('\x03', false); // Ctrl+C
                            this._outputChannel.appendLine(
                                `[Terminal] User killed blocked command.`
                            );
                        }
                    }
                }
            },
        );

        this._disposables.push(startListener);
        context.subscriptions.push(startListener);

        // Log command completions
        const endListener = vscode.window.onDidEndTerminalShellExecution(
            (event) => {
                const commandLine = event.execution.commandLine.value;
                const exitCode = event.exitCode;
                this._outputChannel.appendLine(
                    `[Terminal] Command ended (exit=${exitCode}): ${commandLine.slice(0, 80)}`
                );
            },
        );

        this._disposables.push(endListener);
        context.subscriptions.push(endListener);

        this._outputChannel.appendLine('[Terminal] Governance monitor activated.');
    }

    /** Update kill-on-block behavior. */
    setKillOnBlock(enabled: boolean): void {
        this._killOnBlock = enabled;
    }

    dispose(): void {
        for (const d of this._disposables) {
            d.dispose();
        }
    }
}
