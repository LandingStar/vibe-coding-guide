import * as vscode from 'vscode';
import { CopilotLLMProvider } from './copilot';
import { OpenAICompatibleLLMProvider } from './openaiCompatible';
import { ManagedLLMProvider } from './types';

/**
 * Create the default extension-side LLM provider.
 *
 * Keeping creation behind a factory lets us preserve current Copilot behavior
 * while preventing the rest of the extension from depending on a concrete class.
 */
export function createDefaultLLMProvider(context: vscode.ExtensionContext): ManagedLLMProvider {
    const providerKind = vscode.workspace.getConfiguration('docBasedCoding').get<string>('llm.provider') ?? 'copilot';
    if (providerKind === 'openai-compatible') {
        return new OpenAICompatibleLLMProvider(context.secrets);
    }
    return new CopilotLLMProvider();
}
