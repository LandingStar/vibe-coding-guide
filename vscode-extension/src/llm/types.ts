/**
 * LLM provider interfaces.
 *
 * Abstracts access to language models so the extension can use
 * Copilot's vscode.lm API or fall back to the Python MCP worker.
 */

/** Result of an intent/schema classification. */
export interface ClassificationResult {
    label: string;
    confidence: number;
    raw?: string;
}

/**
 * Abstract LLM provider.
 * Two planned implementations:
 * - CopilotLLMProvider (vscode.lm API)
 * - MCPWorkerProvider (delegates to Python LLM worker via MCP)
 */
export interface LLMProvider {
    readonly name: string;
    readonly isAvailable: boolean;

    classify(input: string, schema: Record<string, unknown>): Promise<ClassificationResult>;
    generate(prompt: string): Promise<string>;
}
