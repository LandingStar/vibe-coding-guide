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
    readonly onToolResult?: (tool: AiChatToolAction['tool'], ok: boolean) => void | Promise<void>;
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
        await options.onToolResult?.(action.tool, result.ok);
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
        'You are currently in the read-only vibe-coding slice for workspace content. You may inspect files, but you cannot edit source files, apply patches, or run terminal commands.',
        'The localTrajectory tool is the explicit exception: you must use it to update Local Work Trajectory metadata for tracked tasks.',
        'Reply with exactly one JSON object and nothing else.',
        'If you need more project context, request exactly one tool call.',
        'If you can answer, return a final response in Chinese.',
        'For task-like user requests, you own Local Work Trajectory updates: call localTrajectory start when beginning a new task, append planned or observed milestones, update when current milestone details change, block/wait for impediments, resume when continuing, advance when the current milestone is complete, and close when the tracked task is done.',
        'For the current multi-line expansion, use localTrajectory addLane when a clearly separate work context must begin, and localTrajectory merge when that separate lane is ready to rejoin a target lane.',
        'Use localTrajectory relate to record explicit depends_on, waits_for, unblocks, hands_off, syncs_from, or approves_new_line metadata between existing events when that relation matters for reading the work map.',
        'Treat merge and relate as visible trajectory metadata only: do not invent dependency scheduling, conflict resolution, or review-barrier semantics around them.',
        'After validation or delivery is complete, keep calling localTrajectory advance as needed until no completed milestone remains pending or in_progress; your final answer should not leave a completed validation/delivery node unadvanced.',
        'Do not ask the user to manually press Local Work Trajectory buttons.',
        'Allowed JSON shapes:',
        '{"type":"tool","tool":"listFiles","args":{"path":"."},"reason":"why this tool is needed"}',
        '{"type":"tool","tool":"localTrajectory","args":{"action":"start","laneLabel":"short lane label","firstEventTitle":"first milestone"},"reason":"start tracking the task"}',
        '{"type":"tool","tool":"localTrajectory","args":{"action":"addLane","laneLabel":"short lane label","firstEventTitle":"first milestone"},"reason":"start a separate work context"}',
        '{"type":"tool","tool":"localTrajectory","args":{"action":"merge","sourceLaneId":"lane:002","targetLaneId":"lane:main","title":"merge milestone"},"reason":"merge a completed separate lane back into the main lane"}',
        '{"type":"tool","tool":"localTrajectory","args":{"action":"relate","sourceEventId":"event:002","targetEventId":"event:004","relationKind":"depends_on","summary":"target needs source result"},"reason":"record a cross-lane dependency"}',
        '{"type":"tool","tool":"localTrajectory","args":{"action":"close","summary":"done"},"reason":"close the single-line trajectory"}',
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
