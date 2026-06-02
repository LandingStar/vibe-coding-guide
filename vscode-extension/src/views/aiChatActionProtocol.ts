export type AiChatToolName = 'listFiles' | 'readFile' | 'searchText' | 'getDiagnostics';

export interface AiChatToolAction {
    readonly type: 'tool';
    readonly tool: AiChatToolName;
    readonly args: Record<string, unknown>;
    readonly reason?: string;
}

export interface AiChatFinalAction {
    readonly type: 'final';
    readonly content: string;
}

export type AiChatAssistantAction = AiChatToolAction | AiChatFinalAction;

const TOOL_NAMES: readonly AiChatToolName[] = ['listFiles', 'readFile', 'searchText', 'getDiagnostics'] as const;

export function parseAssistantAction(rawResponse: string): AiChatAssistantAction | null {
    const jsonSource = extractJsonObject(rawResponse);
    if (!jsonSource) {
        return null;
    }

    try {
        const parsed = JSON.parse(jsonSource) as Record<string, unknown>;
        if (parsed.type === 'final' && typeof parsed.content === 'string') {
            return {
                type: 'final',
                content: parsed.content,
            };
        }

        if (
            parsed.type === 'tool'
            && typeof parsed.tool === 'string'
            && TOOL_NAMES.includes(parsed.tool as AiChatToolName)
            && parsed.args
            && typeof parsed.args === 'object'
            && !Array.isArray(parsed.args)
        ) {
            return {
                type: 'tool',
                tool: parsed.tool as AiChatToolName,
                args: parsed.args as Record<string, unknown>,
                reason: typeof parsed.reason === 'string' ? parsed.reason : undefined,
            };
        }
    } catch {
        return null;
    }

    return null;
}

function extractJsonObject(rawResponse: string): string | null {
    const fencedMatch = rawResponse.match(/```(?:json)?\s*([\s\S]*?)```/i);
    if (fencedMatch?.[1]) {
        const fenced = fencedMatch[1].trim();
        if (fenced.startsWith('{') && fenced.endsWith('}')) {
            return fenced;
        }
    }

    const startIndex = rawResponse.indexOf('{');
    if (startIndex === -1) {
        return null;
    }

    let depth = 0;
    let inString = false;
    let escaping = false;
    for (let index = startIndex; index < rawResponse.length; index += 1) {
        const char = rawResponse[index];
        if (escaping) {
            escaping = false;
            continue;
        }
        if (char === '\\') {
            escaping = true;
            continue;
        }
        if (char === '"') {
            inString = !inString;
            continue;
        }
        if (inString) {
            continue;
        }
        if (char === '{') {
            depth += 1;
            continue;
        }
        if (char === '}') {
            depth -= 1;
            if (depth === 0) {
                return rawResponse.slice(startIndex, index + 1);
            }
        }
    }

    return null;
}