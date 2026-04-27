/**
 * Chat Participant (P7).
 *
 * Registers a @governance chat participant in the Copilot Chat panel.
 * Users can ask governance questions, classify intents, check constraints,
 * and get pack information directly through chat.
 */

import * as vscode from 'vscode';
import { MCPClient } from '../mcp/client';

const PARTICIPANT_ID = 'docBasedCoding.governance';

const SYSTEM_PROMPT = `You are a governance assistant for a document-driven coding workflow platform.
You help users understand project constraints (C1-C8), pack configurations, and governance decisions.
When asked to check something, you call the MCP governance tools and report results.
Be concise and actionable. Format governance decisions clearly with ALLOW/BLOCK status.`;

interface GovernanceResult extends vscode.ChatResult {
    metadata?: {
        decision?: string;
        intent?: string;
    };
}

export function registerChatParticipant(
    context: vscode.ExtensionContext,
    getMCPClient: () => MCPClient | null,
    outputChannel: vscode.OutputChannel,
): vscode.ChatParticipant {
    const handler: vscode.ChatRequestHandler = async (
        request: vscode.ChatRequest,
        chatContext: vscode.ChatContext,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken,
    ): Promise<GovernanceResult> => {
        const mcpClient = getMCPClient();

        // Handle slash commands
        if (request.command === 'check') {
            return handleCheck(request, stream, mcpClient, outputChannel);
        }
        if (request.command === 'decide') {
            return handleDecide(request, stream, mcpClient, outputChannel);
        }
        if (request.command === 'constraints') {
            return handleConstraints(stream, mcpClient, outputChannel);
        }
        if (request.command === 'packs') {
            return handlePacks(stream, mcpClient, outputChannel);
        }
        if (request.command === 'dogfood') {
            return handleDogfood(request, stream, mcpClient, outputChannel);
        }

        // Default: general governance chat using the model
        return handleGeneral(request, chatContext, stream, token, mcpClient, outputChannel);
    };

    const participant = vscode.chat.createChatParticipant(PARTICIPANT_ID, handler);
    participant.iconPath = new vscode.ThemeIcon('shield');

    participant.followupProvider = {
        provideFollowups(
            _result: GovernanceResult,
            _context: vscode.ChatContext,
            _token: vscode.CancellationToken,
        ): vscode.ProviderResult<vscode.ChatFollowup[]> {
            return [
                { prompt: 'Show current constraints', command: 'constraints', label: 'View Constraints' },
                { prompt: 'Check governance for this action', command: 'decide', label: 'Check Governance' },
                { prompt: 'Run dogfood pipeline', command: 'dogfood', label: 'Dogfood Evidence' },
            ];
        },
    };

    context.subscriptions.push(participant);
    outputChannel.appendLine('[Chat] Governance participant registered.');
    return participant;
}

async function handleCheck(
    request: vscode.ChatRequest,
    stream: vscode.ChatResponseStream,
    mcpClient: MCPClient | null,
    outputChannel: vscode.OutputChannel,
): Promise<GovernanceResult> {
    if (!mcpClient || !mcpClient.isRunning) {
        stream.markdown('⚠️ MCP Server is not running. Start it with the **Start MCP Server** command.');
        return {};
    }

    stream.markdown('Checking constraints...\n\n');

    try {
        const result = await mcpClient.callTool('check_constraints', {}) as Record<string, unknown>;
        const violations = (result.violations as unknown[]) ?? [];
        const phase = result.phase_info as string ?? 'unknown';

        stream.markdown(`**Phase:** ${phase}\n\n`);

        if (violations.length === 0) {
            stream.markdown('✅ All constraints satisfied. No violations detected.');
        } else {
            stream.markdown(`⚠️ **${violations.length} violation(s) detected:**\n\n`);
            for (const v of violations) {
                stream.markdown(`- ${String(v)}\n`);
            }
        }
    } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        stream.markdown(`❌ Error checking constraints: ${msg}`);
        outputChannel.appendLine(`[Chat] check_constraints error: ${msg}`);
    }

    return {};
}

async function handleDecide(
    request: vscode.ChatRequest,
    stream: vscode.ChatResponseStream,
    mcpClient: MCPClient | null,
    outputChannel: vscode.OutputChannel,
): Promise<GovernanceResult> {
    if (!mcpClient || !mcpClient.isRunning) {
        stream.markdown('⚠️ MCP Server is not running. Start it with the **Start MCP Server** command.');
        return {};
    }

    const inputText = request.prompt.trim();
    if (!inputText) {
        stream.markdown('Please provide an action to check. Example: `/decide refactor the payment module`');
        return {};
    }

    stream.markdown(`Checking governance for: *"${inputText}"*\n\n`);

    try {
        const result = await mcpClient.callTool('governance_decide', {
            input_text: inputText,
        }) as Record<string, unknown>;

        const decision = result.decision as string;
        const intent = result.intent as string;
        const gate = result.gate as string;

        const icon = decision === 'ALLOW' ? '✅' : '⛔';
        stream.markdown(`${icon} **${decision}**\n\n`);
        stream.markdown(`| Field | Value |\n|-------|-------|\n`);
        stream.markdown(`| Intent | ${intent} |\n`);
        stream.markdown(`| Gate | ${gate} |\n`);

        if (decision === 'BLOCK') {
            stream.markdown(`\n\n💡 **Suggestion:** Ensure you have an active planning-gate document before proceeding with this action.`);
        }

        return { metadata: { decision, intent } };
    } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        stream.markdown(`❌ Error: ${msg}`);
        outputChannel.appendLine(`[Chat] governance_decide error: ${msg}`);
        return {};
    }
}

async function handleConstraints(
    stream: vscode.ChatResponseStream,
    mcpClient: MCPClient | null,
    outputChannel: vscode.OutputChannel,
): Promise<GovernanceResult> {
    if (!mcpClient || !mcpClient.isRunning) {
        stream.markdown('⚠️ MCP Server is not running. Start it with the **Start MCP Server** command.');
        return {};
    }

    try {
        const result = await mcpClient.callTool('check_constraints', {}) as Record<string, unknown>;
        const violations = (result.violations as unknown[]) ?? [];
        const filesNeeded = (result.files_to_reread as string[]) ?? [];

        stream.markdown('## Constraint Status (C1-C8)\n\n');

        if (violations.length === 0) {
            stream.markdown('✅ All constraints are satisfied.\n');
        } else {
            stream.markdown(`⚠️ ${violations.length} violation(s):\n\n`);
            for (const v of violations) {
                stream.markdown(`- ${String(v)}\n`);
            }
        }

        if (filesNeeded.length > 0) {
            stream.markdown(`\n**Files to re-read for context recovery:**\n`);
            for (const f of filesNeeded) {
                stream.markdown(`- \`${f}\`\n`);
            }
        }
    } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        stream.markdown(`❌ Error: ${msg}`);
        outputChannel.appendLine(`[Chat] check_constraints error: ${msg}`);
    }

    return {};
}

async function handlePacks(
    stream: vscode.ChatResponseStream,
    mcpClient: MCPClient | null,
    outputChannel: vscode.OutputChannel,
): Promise<GovernanceResult> {
    if (!mcpClient || !mcpClient.isRunning) {
        stream.markdown('⚠️ MCP Server is not running. Start it with the **Start MCP Server** command.');
        return {};
    }

    try {
        const result = await mcpClient.callTool('get_pack_info', { level: 'metadata' }) as Record<string, unknown>;
        const packs = (result.packs as Array<Record<string, unknown>>) ?? [];

        stream.markdown('## Loaded Packs\n\n');

        if (packs.length === 0) {
            stream.markdown('No packs loaded.');
        } else {
            stream.markdown(`| Name | Kind | Description |\n|------|------|-------------|\n`);
            for (const p of packs) {
                const name = p.name ?? 'unnamed';
                const kind = p.kind ?? '-';
                const desc = (p.description as string ?? '').slice(0, 60);
                stream.markdown(`| ${name} | ${kind} | ${desc} |\n`);
            }
        }
    } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        stream.markdown(`❌ Error: ${msg}`);
        outputChannel.appendLine(`[Chat] get_pack_info error: ${msg}`);
    }

    return {};
}

async function handleDogfood(
    request: vscode.ChatRequest,
    stream: vscode.ChatResponseStream,
    mcpClient: MCPClient | null,
    outputChannel: vscode.OutputChannel,
): Promise<GovernanceResult> {
    if (!mcpClient || !mcpClient.isRunning) {
        stream.markdown('⚠️ MCP Server is not running. Start it with the **Start MCP Server** command.');
        return {};
    }

    const input = request.prompt.trim();
    if (!input) {
        stream.markdown(
            'Provide symptoms to evaluate. Example:\n\n' +
            '`/dogfood MCP query_decision_logs returns empty merge_conflicts for entries that should have them`\n\n' +
            'You can also pass structured JSON: `/dogfood [{"symptom_id":"S1","symptom_summary":"..."}]`',
        );
        return {};
    }

    stream.markdown('Running dogfood evidence pipeline...\n\n');

    try {
        // Parse symptoms: either JSON array or plain text as single symptom
        let symptoms: Array<Record<string, unknown>>;
        try {
            const parsed = JSON.parse(input);
            symptoms = Array.isArray(parsed) ? parsed : [parsed];
        } catch {
            // Plain text → wrap as single symptom
            symptoms = [{
                symptom_id: `chat-${Date.now()}`,
                symptom_summary: input,
            }];
        }

        const result = await mcpClient.callTool('promote_dogfood_evidence', {
            symptoms,
            confidence: 'medium',
        }) as Record<string, unknown>;

        if (result.error) {
            stream.markdown(`❌ Pipeline error: ${result.error}`);
            return {};
        }

        // Promotion decisions
        const decisions = (result.promotion_decisions as Array<Record<string, unknown>>) ?? [];
        if (decisions.length > 0) {
            stream.markdown('## Promotion Decisions\n\n');
            stream.markdown('| Symptom | Verdict | Triggers |\n|---------|---------|----------|\n');
            for (const d of decisions) {
                const id = d.symptom_id ?? '-';
                const verdict = d.verdict ?? '-';
                const triggers = Array.isArray(d.triggered) ? (d.triggered as string[]).join(', ') : '-';
                stream.markdown(`| ${id} | ${verdict} | ${triggers} |\n`);
            }
            stream.markdown('\n');
        }

        // Issue candidates
        const issues = (result.issue_candidates as Array<Record<string, unknown>>) ?? [];
        if (issues.length > 0) {
            stream.markdown(`## Promoted Issues (${issues.length})\n\n`);
            for (const issue of issues) {
                stream.markdown(`**${issue.title ?? 'Untitled'}** — ${issue.category ?? ''}\n`);
                if (issue.symptom_summary) {
                    stream.markdown(`> ${issue.symptom_summary}\n`);
                }
                stream.markdown('\n');
            }
        }

        // Feedback packet summary
        const packet = result.packet as Record<string, unknown> | undefined;
        if (packet) {
            stream.markdown('## Feedback Packet\n\n');
            stream.markdown(`- **Packet ID:** ${packet.packet_id ?? '-'}\n`);
            stream.markdown(`- **Confidence:** ${packet.confidence ?? '-'}\n`);
            stream.markdown(`- **Issues:** ${(packet.source_issues as unknown[])?.length ?? 0}\n`);
            if (packet.judgment) {
                stream.markdown(`- **Judgment:** ${packet.judgment}\n`);
            }
        }

        // Consumer payloads summary
        const payloads = (result.consumer_payloads as Array<Record<string, unknown>>) ?? [];
        if (payloads.length > 0) {
            stream.markdown(`\n## Consumer Payloads (${payloads.length})\n\n`);
            for (const p of payloads) {
                stream.markdown(`- **${p.consumer ?? 'unknown'}** → ${p.target_doc ?? '-'}\n`);
            }
            stream.markdown('\n💡 Use `auto_writeback: true` to write payloads to target documents.');
        }

        if (decisions.length === 0 && issues.length === 0) {
            stream.markdown('No symptoms were promoted. All were suppressed or did not meet threshold criteria.');
        }
    } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        stream.markdown(`❌ Error: ${msg}`);
        outputChannel.appendLine(`[Chat] promote_dogfood_evidence error: ${msg}`);
    }

    return {};
}

async function handleGeneral(
    request: vscode.ChatRequest,
    chatContext: vscode.ChatContext,
    stream: vscode.ChatResponseStream,
    token: vscode.CancellationToken,
    mcpClient: MCPClient | null,
    outputChannel: vscode.OutputChannel,
): Promise<GovernanceResult> {
    // Build messages with system context
    const messages: vscode.LanguageModelChatMessage[] = [
        vscode.LanguageModelChatMessage.User(SYSTEM_PROMPT),
    ];

    // Add governance context if MCP is available
    if (mcpClient?.isRunning) {
        try {
            const constraints = await mcpClient.callTool('check_constraints', {}) as Record<string, unknown>;
            const violations = (constraints.violations as unknown[]) ?? [];
            const contextMsg = violations.length === 0
                ? 'Current status: All constraints satisfied.'
                : `Current status: ${violations.length} constraint violation(s): ${violations.map(String).join('; ')}`;
            messages.push(vscode.LanguageModelChatMessage.User(`[Context] ${contextMsg}`));
        } catch {
            // Ignore - proceed without context
        }
    }

    // Add chat history
    for (const turn of chatContext.history) {
        if (turn instanceof vscode.ChatResponseTurn) {
            let text = '';
            for (const part of turn.response) {
                if (part instanceof vscode.ChatResponseMarkdownPart) {
                    text += part.value.value;
                }
            }
            if (text) {
                messages.push(vscode.LanguageModelChatMessage.Assistant(text));
            }
        } else if (turn instanceof vscode.ChatRequestTurn) {
            messages.push(vscode.LanguageModelChatMessage.User(turn.prompt));
        }
    }

    // Add current user message
    messages.push(vscode.LanguageModelChatMessage.User(request.prompt));

    // Send to model
    try {
        const chatResponse = await request.model.sendRequest(messages, {}, token);
        for await (const fragment of chatResponse.text) {
            stream.markdown(fragment);
        }
    } catch (err) {
        if (err instanceof vscode.LanguageModelError) {
            stream.markdown(`⚠️ Language model error: ${err.message}`);
        } else {
            throw err;
        }
    }

    return {};
}
