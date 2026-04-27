/**
 * MCP-backed Governance Interceptor (P3).
 *
 * Calls the MCP `governance_decide` tool to enforce constraints
 * before file writes and terminal commands.
 */

import * as vscode from 'vscode';
import { MCPClient } from '../mcp/client';
import { GovernanceDecideResult } from '../mcp/types';
import { LLMProvider } from '../llm/types';
import {
    GovernanceInterceptor,
    GovernanceDecision,
    AgentAction,
} from './types';
import { ReviewPanelProvider } from './reviewPanel';

export class MCPGovernanceInterceptor implements GovernanceInterceptor {
    private _mcpClient: MCPClient | null;
    private _llmProvider: LLMProvider | null;
    private readonly _outputChannel: vscode.OutputChannel;

    constructor(mcpClient: MCPClient | null, outputChannel: vscode.OutputChannel, llmProvider?: LLMProvider) {
        this._mcpClient = mcpClient;
        this._llmProvider = llmProvider ?? null;
        this._outputChannel = outputChannel;
    }

    updateClient(client: MCPClient): void {
        this._mcpClient = client;
    }

    updateLLMProvider(provider: LLMProvider): void {
        this._llmProvider = provider;
    }

    updateCopilot(copilot: LLMProvider): void {
        this.updateLLMProvider(copilot);
    }

    async beforeFileWrite(uri: string, _content: string): Promise<GovernanceDecision> {
        return this._decide(`file-write: ${uri}`);
    }

    async beforeTerminalCommand(command: string): Promise<GovernanceDecision> {
        return this._decide(`terminal-command: ${command}`);
    }

    async beforeAgentAction(action: AgentAction): Promise<GovernanceDecision> {
        return this._decide(`${action.type}: ${action.description}`);
    }

    private async _decide(inputText: string): Promise<GovernanceDecision> {
        if (!this._mcpClient || !this._mcpClient.isRunning) {
            // If MCP server is not available, allow by default with warning
            this._outputChannel.appendLine(
                `[Governance] MCP unavailable, allowing: ${inputText.slice(0, 80)}`
            );
            return { allow: true, reason: 'mcp-unavailable' };
        }

        try {
            const result = await this._mcpClient.callTool('governance_decide', {
                input_text: inputText,
            }) as GovernanceDecideResult;

            const allow = result.decision === 'ALLOW';

            this._outputChannel.appendLine(
                `[Governance] ${result.decision} | intent=${result.intent} gate=${result.gate} | ${inputText.slice(0, 60)}`
            );

            let denyMessage: string | undefined;
            if (!allow) {
                denyMessage = `Governance BLOCK: ${result.intent} (gate: ${result.gate})`;
                // Enrich with Copilot explanation if available
                const explanation = await this._explainBlock(inputText, result);
                if (explanation) {
                    denyMessage += `\n\n${explanation}`;
                }
            }

            return {
                allow,
                reason: `${result.decision}: intent=${result.intent}, gate=${result.gate}`,
                denyMessage,
                traceId: (result.envelope as Record<string, unknown>)?.trace_id as string | undefined,
            };
        } catch (err) {
            const msg = err instanceof Error ? err.message : String(err);
            this._outputChannel.appendLine(`[Governance] Error during decide: ${msg}`);
            // On error, allow to avoid blocking user work
            return { allow: true, reason: `error: ${msg}` };
        }
    }

    /**
     * Use the active LLM provider to explain why a governance decision blocked and suggest fixes.
     * Returns null if the provider is unavailable or fails.
     */
    private async _explainBlock(inputText: string, result: GovernanceDecideResult): Promise<string | null> {
        if (!this._llmProvider || !this._llmProvider.isAvailable) {
            return null;
        }

        try {
            const prompt = [
                'A document-driven governance system blocked an action.',
                `Action: ${inputText.slice(0, 200)}`,
                `Decision: ${result.decision}`,
                `Intent classified as: ${result.intent}`,
                `Gate: ${result.gate}`,
                '',
                'In 1-2 sentences, explain why this was blocked and what the user should do to proceed.',
                'Be concise and actionable.',
            ].join('\n');

            const explanation = await this._llmProvider.generate(prompt);
            return explanation.trim().slice(0, 300);
        } catch {
            return null;
        }
    }
}

/**
 * Register file-save governance listener.
 * Shows a Review Panel when governance blocks a file save.
 */
export function registerGovernanceListeners(
    context: vscode.ExtensionContext,
    interceptor: MCPGovernanceInterceptor,
    outputChannel: vscode.OutputChannel,
    reviewPanel: ReviewPanelProvider,
): void {
    // Listen to document save events
    const saveDisposable = vscode.workspace.onWillSaveTextDocument((event) => {
        const uri = event.document.uri.fsPath;

        // Only intercept workspace files (skip untitled, output, etc.)
        if (event.document.uri.scheme !== 'file') {
            return;
        }

        event.waitUntil(
            (async () => {
                const decision = await interceptor.beforeFileWrite(uri, '');

                if (!decision.allow) {
                    // Open Review Panel for user to approve/reject
                    const approved = await reviewPanel.requestReview(uri, decision);

                    if (!approved) {
                        throw new Error('Save cancelled by governance policy.');
                    }

                    outputChannel.appendLine(
                        `[Governance] User override via Review Panel: saving ${uri} despite BLOCK`
                    );
                }

                // Return empty edits (don't modify content)
                return [] as vscode.TextEdit[];
            })(),
        );
    });

    context.subscriptions.push(saveDisposable);
}
