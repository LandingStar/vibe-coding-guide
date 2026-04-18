/**
 * Copilot LLM provider using vscode.lm API.
 *
 * NOTE: vscode.lm constraints (from official docs):
 * - No system messages; only User and Assistant
 * - GPT-4o has 64K token limit
 * - Requires user consent on first use (auth dialog)
 * - Rate limited per extension
 * - Nondeterministic responses
 * - selectChatModels should be called from user-initiated actions
 */

import * as vscode from 'vscode';
import { LLMProvider, ClassificationResult } from './types';

export class CopilotLLMProvider implements LLMProvider {
    readonly name = 'copilot';
    private _model: vscode.LanguageModelChat | null = null;

    get isAvailable(): boolean {
        return this._model !== null;
    }

    /** Try to select a Copilot model. Call from a user-initiated action. */
    async initialize(family: string = 'gpt-4o'): Promise<boolean> {
        try {
            const models = await vscode.lm.selectChatModels({
                vendor: 'copilot',
                family,
            });
            if (models.length > 0) {
                this._model = models[0];
                return true;
            }
        } catch (err) {
            if (err instanceof vscode.LanguageModelError) {
                console.warn(`[CopilotLLM] Model selection failed: ${err.message}`);
            }
        }
        return false;
    }

    async classify(
        input: string,
        schema: Record<string, unknown>
    ): Promise<ClassificationResult> {
        if (!this._model) {
            throw new Error('Copilot model not initialized. Call initialize() first.');
        }

        const messages = [
            vscode.LanguageModelChatMessage.User(
                `You are an intent classifier. Given the following input, classify it according to this schema: ${JSON.stringify(schema)}\n\nRespond with a JSON object containing "label" and "confidence" (0-1).\n\nInput: "${input}"`
            ),
        ];

        const response = await this._model.sendRequest(
            messages,
            {},
            new vscode.CancellationTokenSource().token
        );

        let text = '';
        for await (const fragment of response.text) {
            text += fragment;
        }

        try {
            const parsed = JSON.parse(text);
            return {
                label: parsed.label ?? 'unknown',
                confidence: parsed.confidence ?? 0,
                raw: text,
            };
        } catch {
            return { label: 'unknown', confidence: 0, raw: text };
        }
    }

    async generate(prompt: string): Promise<string> {
        if (!this._model) {
            throw new Error('Copilot model not initialized. Call initialize() first.');
        }

        const messages = [
            vscode.LanguageModelChatMessage.User(prompt),
        ];

        const response = await this._model.sendRequest(
            messages,
            {},
            new vscode.CancellationTokenSource().token
        );

        let text = '';
        for await (const fragment of response.text) {
            text += fragment;
        }

        return text;
    }
}
