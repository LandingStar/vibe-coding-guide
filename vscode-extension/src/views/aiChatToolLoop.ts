import { ManagedLLMProvider } from '../llm/types';
import {
    parseAssistantAction,
    type AiChatToolAction,
} from './aiChatActionProtocol';
import { AiChatToolExecutor, describeAiChatTools } from './aiChatTools';

export type AiChatMessageRole = 'user' | 'assistant' | 'tool';

export interface AiChatConversationMessage {
    readonly role: AiChatMessageRole;
    readonly content: string;
}

interface RunAiChatToolLoopOptions {
    readonly provider: ManagedLLMProvider;
    readonly history: readonly AiChatConversationMessage[];
    readonly currentPrompt: string;
    readonly executor: AiChatToolExecutor;
    readonly onToolMessage: (message: string) => void;
    readonly maxSteps?: number;
}

export async function runAiChatToolLoop(options: RunAiChatToolLoopOptions): Promise<string> {
    const maxSteps = Math.max(1, options.maxSteps ?? 5);
    const transcript: AiChatConversationMessage[] = [
        ...options.history.slice(-8),
        { role: 'user', content: options.currentPrompt },
    ];

    for (let step = 0; step < maxSteps; step += 1) {
        const rawResponse = await options.provider.generate(
            buildDecisionPrompt(transcript, options.executor.getWorkspaceRoot()),
        );
        const action = parseAssistantAction(rawResponse);

        if (!action) {
            return rawResponse.trim() || '没有拿到可用回复。';
        }

        if (action.type === 'final') {
            return action.content.trim() || '没有拿到可用回复。';
        }

        const result = await options.executor.execute(action.tool, action.args);
        const toolMessage = formatToolMessage(action, result.summary, result.content, result.ok);
        options.onToolMessage(toolMessage);
        transcript.push({ role: 'tool', content: toolMessage });
    }

    return (await options.provider.generate(buildForcedFinalPrompt(transcript))).trim() || '没有拿到可用回复。';
}

function buildDecisionPrompt(
    transcript: readonly AiChatConversationMessage[],
    workspaceRoot: string | null,
): string {
    return [
        'You are Doc-Based Coding assistant inside a VS Code extension custom chat panel.',
        'You are currently in the read-only vibe-coding slice. You may inspect the workspace but you cannot edit files, apply patches, or run terminal commands.',
        'Reply with exactly one JSON object and nothing else.',
        'If you need more project context, request exactly one tool call.',
        'If you can answer, return a final response in Chinese.',
        'Allowed JSON shapes:',
        '{"type":"tool","tool":"listFiles","args":{"path":"."},"reason":"why this tool is needed"}',
        '{"type":"final","content":"your final Chinese answer"}',
        'Tool rules:',
        '- Prefer the smallest useful read.',
        '- Paths must be workspace-relative.',
        '- Do not invent file contents, search results, or diagnostics.',
        '- If a tool fails, either fix the tool arguments or explain the limitation in the final answer.',
        'Available tools:',
        describeAiChatTools(),
        `Workspace root: ${workspaceRoot ?? '(no workspace root)'}`,
        `Conversation transcript:\n${formatTranscript(transcript)}`,
    ].join('\n\n');
}

function buildForcedFinalPrompt(transcript: readonly AiChatConversationMessage[]): string {
    return [
        'You have reached the maximum number of tool steps for this turn.',
        'Based only on the validated tool observations below, answer the user in Chinese.',
        'Do not ask for more tools. Do not output JSON.',
        `Conversation transcript:\n${formatTranscript(transcript)}`,
    ].join('\n\n');
}

function formatTranscript(transcript: readonly AiChatConversationMessage[]): string {
    return transcript
        .map((message) => `${capitalizeRole(message.role)}: ${message.content}`)
        .join('\n\n');
}

function capitalizeRole(role: AiChatMessageRole): string {
    if (role === 'user') {
        return 'User';
    }
    if (role === 'assistant') {
        return 'Assistant';
    }
    return 'Tool';
}

function formatToolMessage(
    action: AiChatToolAction,
    summary: string,
    content: string,
    ok: boolean,
): string {
    return [
        `工具 ${action.tool}${ok ? '' : ' 失败'}`,
        action.reason ? `原因：${action.reason}` : '',
        summary,
        content,
    ].filter(Boolean).join('\n');
}
