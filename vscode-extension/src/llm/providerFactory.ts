import { CopilotLLMProvider } from './copilot';
import { ManagedLLMProvider } from './types';

/**
 * Create the default extension-side LLM provider.
 *
 * Keeping creation behind a factory lets us preserve current Copilot behavior
 * while preventing the rest of the extension from depending on a concrete class.
 */
export function createDefaultLLMProvider(): ManagedLLMProvider {
    return new CopilotLLMProvider();
}
