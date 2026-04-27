/**
 * Provider-assisted Pack generation (P4+).
 *
 * Uses the active extension LLM provider to analyze the workspace
 * and generate pack documentation drafts.
 */

import * as vscode from 'vscode';
import { ManagedLLMProvider } from './types';

/**
 * Generate a pack description draft using the active LLM provider.
 * Analyzes open file or workspace context.
 */
export async function generatePackDescription(
    provider: ManagedLLMProvider,
    outputChannel: vscode.OutputChannel,
): Promise<void> {
    if (!provider.isAvailable) {
        const ok = await provider.initialize();
        if (!ok) {
            vscode.window.showErrorMessage(`${provider.displayName} model not available.`);
            return;
        }
    }

    const editor = vscode.window.activeTextEditor;
    const context = editor
        ? `File: ${editor.document.fileName}\nContent (first 500 chars):\n${editor.document.getText().slice(0, 500)}`
        : 'No file is currently open.';

    const prompt = [
        'You are helping create a governance pack for a document-driven coding platform.',
        'A "pack" is a JSON configuration that defines rules, intents, gates, and capabilities for a project scope.',
        '',
        'Based on the following workspace context, suggest a pack description (1-2 sentences)',
        'that follows this quality standard:',
        '- Starts with an action verb',
        '- Mentions the primary capability or scope',
        '- Under 120 characters',
        '',
        `Context:\n${context}`,
        '',
        'Respond with ONLY the description string, no quotes or extra formatting.',
    ].join('\n');

    try {
        outputChannel.appendLine(`[LLM:${provider.name}] Generating pack description...`);
        const description = await provider.generate(prompt);
        const trimmed = description.trim().replace(/^["']|["']$/g, '');

        const action = await vscode.window.showInformationMessage(
            `Suggested description: "${trimmed}"`,
            'Copy to Clipboard',
            'Insert at Cursor',
        );

        if (action === 'Copy to Clipboard') {
            await vscode.env.clipboard.writeText(trimmed);
            vscode.window.showInformationMessage('Copied to clipboard.');
        } else if (action === 'Insert at Cursor' && editor) {
            await editor.edit((edit) => {
                edit.insert(editor.selection.active, trimmed);
            });
        }
    } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        vscode.window.showErrorMessage(`Pack description generation failed: ${msg}`);
    }
}

/**
 * Generate a pack rules draft using the active LLM provider.
 */
export async function generatePackRules(
    provider: ManagedLLMProvider,
    outputChannel: vscode.OutputChannel,
): Promise<void> {
    if (!provider.isAvailable) {
        const ok = await provider.initialize();
        if (!ok) {
            vscode.window.showErrorMessage(`${provider.displayName} model not available.`);
            return;
        }
    }

    const input = await vscode.window.showInputBox({
        prompt: 'Describe the governance rules you want (e.g. "enforce test coverage, require planning docs")',
        placeHolder: 'enforce test coverage before merge, require planning-gate for large changes',
    });
    if (!input) { return; }

    const prompt = [
        'You are helping create governance rules for a document-driven coding platform pack.',
        'Rules are key-value pairs in a JSON "rules" object inside a .pack.json file.',
        'Each rule has a snake_case key and a string value describing the constraint.',
        '',
        `User request: "${input}"`,
        '',
        'Generate 2-5 rules as a JSON object. Keys are snake_case identifiers.',
        'Values are concise rule descriptions (1 sentence each).',
        'Respond with ONLY the JSON object, no markdown fences.',
    ].join('\n');

    try {
        outputChannel.appendLine(`[LLM:${provider.name}] Generating pack rules...`);
        const result = await provider.generate(prompt);
        const cleaned = result.trim().replace(/^```json?\n?|\n?```$/g, '');

        const doc = await vscode.workspace.openTextDocument({
            content: cleaned,
            language: 'json',
        });
        await vscode.window.showTextDocument(doc);
        outputChannel.appendLine(`[LLM:${provider.name}] Pack rules draft opened in editor.`);
    } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        vscode.window.showErrorMessage(`Pack rules generation failed: ${msg}`);
    }
}
