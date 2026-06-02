import * as vscode from 'vscode';
import { ClassificationResult, ManagedLLMProvider } from './types';

export const OPENAI_COMPATIBLE_API_KEY_SECRET = 'docBasedCoding.llm.openaiCompatible.apiKey';

type ChatRole = 'system' | 'user' | 'assistant';

interface ChatMessage {
    role: ChatRole;
    content: string;
}

interface OpenAICompatibleConfig {
    baseUrl: string;
    model: string;
}

export class OpenAICompatibleLLMProvider implements ManagedLLMProvider {
    readonly name = 'openai-compatible';
    readonly displayName = 'OpenAI-Compatible API';

    private _apiKey: string | null = null;
    private _currentModel = 'gpt-4o-mini';

    constructor(private readonly _secrets: vscode.SecretStorage) {}

    get isAvailable(): boolean {
        return Boolean(this._apiKey);
    }

    get currentFamily(): string {
        return this._currentModel;
    }

    async initialize(family?: string): Promise<boolean> {
        const config = this._readConfig(family);
        this._currentModel = config.model;
        this._apiKey = await this._secrets.get(OPENAI_COMPATIBLE_API_KEY_SECRET)
            ?? process.env.OPENAI_API_KEY
            ?? null;
        return Boolean(this._apiKey);
    }

    async listModelFamilies(): Promise<string[]> {
        const config = this._readConfig();
        const configuredModel = config.model;

        if (!this._apiKey) {
            await this.initialize(configuredModel);
        }

        if (!this._apiKey) {
            return [configuredModel];
        }

        try {
            const response = await fetch(this._buildUrl(config.baseUrl, '/models'), {
                method: 'GET',
                headers: {
                    Authorization: `Bearer ${this._apiKey}`,
                },
            });

            if (!response.ok) {
                return [configuredModel];
            }

            const payload = await response.json() as { data?: Array<{ id?: string }> };
            const modelIds = payload.data
                ?.map((item) => item.id?.trim())
                .filter((item): item is string => Boolean(item)) ?? [];

            if (!modelIds.length) {
                return [configuredModel];
            }

            if (!modelIds.includes(configuredModel)) {
                modelIds.unshift(configuredModel);
            }

            return Array.from(new Set(modelIds));
        } catch {
            return [configuredModel];
        }
    }

    async classify(input: string, schema: Record<string, unknown>): Promise<ClassificationResult> {
        const text = await this._sendChatCompletion([
            {
                role: 'system',
                content: 'You are an intent classifier. Return only a compact JSON object with keys "label" and "confidence".',
            },
            {
                role: 'user',
                content: `Classify the following input according to this schema: ${JSON.stringify(schema)}\n\nInput: ${input}`,
            },
        ], 0);

        try {
            const parsed = JSON.parse(text);
            return {
                label: typeof parsed.label === 'string' ? parsed.label : 'unknown',
                confidence: typeof parsed.confidence === 'number' ? parsed.confidence : 0,
                raw: text,
            };
        } catch {
            return { label: 'unknown', confidence: 0, raw: text };
        }
    }

    async generate(prompt: string): Promise<string> {
        return this._sendChatCompletion([
            {
                role: 'user',
                content: prompt,
            },
        ]);
    }

    async streamGenerate(prompt: string, onText: (chunk: string) => void): Promise<string> {
        return this._streamChatCompletion([
            {
                role: 'user',
                content: prompt,
            },
        ], 0.2, onText);
    }

    private async _sendChatCompletion(messages: ChatMessage[], temperature = 0.2): Promise<string> {
        const response = await this._sendChatRequest(messages, temperature);
        const responseText = await response.text();
        const completion = this._extractCompletionText(responseText);
        if (completion !== null) {
            return completion;
        }

        throw new Error('External API response did not contain a usable completion.');
    }

    private async _streamChatCompletion(
        messages: ChatMessage[],
        temperature: number,
        onText: (chunk: string) => void,
    ): Promise<string> {
        const response = await this._sendChatRequest(messages, temperature);
        if (!response.body) {
            const responseText = await response.text();
            const completion = this._extractCompletionText(responseText);
            if (completion !== null) {
                if (completion) {
                    onText(completion);
                }
                return completion;
            }
            throw new Error('External API response did not contain a usable completion.');
        }

        return this._consumeStreamingCompletion(response.body, onText);
    }

    private async _sendChatRequest(messages: ChatMessage[], temperature = 0.2): Promise<Response> {
        if (!this._apiKey) {
            const ok = await this.initialize();
            if (!ok || !this._apiKey) {
                throw new Error('External API key is not configured. Run "Doc-Based Coding: Configure External API Key" first.');
            }
        }

        const config = this._readConfig();
        const response = await fetch(this._buildUrl(config.baseUrl, '/chat/completions'), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${this._apiKey}`,
            },
            body: JSON.stringify({
                model: config.model,
                messages,
                temperature,
            }),
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`External API request failed (${response.status}): ${errorText}`);
        }

        return response;
    }

    private async _consumeStreamingCompletion(
        body: ReadableStream<Uint8Array>,
        onText: (chunk: string) => void,
    ): Promise<string> {
        const reader = body.getReader();
        const decoder = new TextDecoder();
        let pending = '';
        let raw = '';
        let output = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) {
                break;
            }

            const decoded = decoder.decode(value, { stream: true });
            raw += decoded;
            pending += decoded;

            const drained = this._drainSseText(pending);
            pending = drained.pending;
            if (drained.text) {
                output += drained.text;
                onText(drained.text);
            }
        }

        const tail = decoder.decode();
        if (tail) {
            raw += tail;
            pending += tail;
        }

        const finalDrain = this._drainSseText(`${pending}\n`);
        if (finalDrain.text) {
            output += finalDrain.text;
            onText(finalDrain.text);
        }

        if (output) {
            return output.trim();
        }

        const completion = this._extractCompletionText(raw);
        if (completion !== null) {
            return completion;
        }

        throw new Error('External API response did not contain a usable completion.');
    }

    private _extractCompletionText(responseText: string): string | null {
        const trimmed = responseText.trim();
        if (!trimmed) {
            return null;
        }

        const payload = this._tryParseJson(trimmed);
        if (payload) {
            const directCompletion = this._extractCompletionTextFromPayload(payload);
            if (directCompletion !== null) {
                return directCompletion;
            }
        }

        return this._extractCompletionTextFromSse(trimmed);
    }

    private _extractCompletionTextFromSse(responseText: string): string | null {
        const chunks: string[] = [];

        for (const rawLine of responseText.split(/\r?\n/)) {
            const line = rawLine.trim();
            if (!line.startsWith('data:')) {
                continue;
            }

            const data = line.slice(5).trim();
            if (!data || data === '[DONE]') {
                continue;
            }

            const payload = this._tryParseJson(data);
            if (!payload) {
                continue;
            }

            const chunk = this._extractCompletionTextFromPayload(payload, false);
            if (chunk !== null) {
                chunks.push(chunk);
            }
        }

        const combined = chunks.join('').trim();
        return combined || null;
    }

    private _drainSseText(buffer: string): { text: string; pending: string } {
        let pending = buffer;
        const chunks: string[] = [];

        while (true) {
            const newlineIndex = pending.indexOf('\n');
            if (newlineIndex === -1) {
                break;
            }

            const rawLine = pending.slice(0, newlineIndex);
            pending = pending.slice(newlineIndex + 1);

            const line = rawLine.trim();
            if (!line.startsWith('data:')) {
                continue;
            }

            const data = line.slice(5).trim();
            if (!data || data === '[DONE]') {
                continue;
            }

            const payload = this._tryParseJson(data);
            if (!payload) {
                continue;
            }

            const chunk = this._extractCompletionTextFromPayload(payload, false);
            if (chunk !== null) {
                chunks.push(chunk);
            }
        }

        return {
            text: chunks.join(''),
            pending,
        };
    }

    private _extractCompletionTextFromPayload(payload: unknown, trim = true): string | null {
        if (!payload || typeof payload !== 'object') {
            return null;
        }

        const choices = (payload as {
            choices?: Array<{
                delta?: { content?: string };
                message?: {
                    content?: string | Array<{ type?: string; text?: string }>;
                };
            }>;
        }).choices;

        if (!Array.isArray(choices) || !choices.length) {
            return null;
        }

        const parts: string[] = [];
        for (const choice of choices) {
            if (typeof choice.delta?.content === 'string') {
                parts.push(choice.delta.content);
            }

            const messageContent = choice.message?.content;
            if (typeof messageContent === 'string') {
                parts.push(messageContent);
            } else if (Array.isArray(messageContent)) {
                parts.push(
                    messageContent
                        .map((part) => typeof part.text === 'string' ? part.text : '')
                        .join(''),
                );
            }
        }

        const combined = parts.join('');
        const normalized = trim ? combined.trim() : combined;
        return normalized ? normalized : null;
    }

    private _tryParseJson(value: string): unknown | null {
        try {
            return JSON.parse(value);
        } catch {
            return null;
        }
    }

    private _readConfig(explicitModel?: string): OpenAICompatibleConfig {
        const config = vscode.workspace.getConfiguration('docBasedCoding');
        const baseUrl = String(config.get<string>('llm.openaiCompatible.baseUrl') ?? 'https://api.openai.com/v1').trim().replace(/\/+$/, '');
        const configuredModel = String(config.get<string>('llm.openaiCompatible.model') ?? 'gpt-4o-mini').trim();
        const model = (explicitModel ?? configuredModel) || 'gpt-4o-mini';
        this._currentModel = model;
        return { baseUrl, model };
    }

    private _buildUrl(baseUrl: string, pathname: string): string {
        return `${baseUrl}${pathname.startsWith('/') ? pathname : `/${pathname}`}`;
    }
}