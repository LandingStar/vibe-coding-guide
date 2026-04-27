/**
 * LLM provider interfaces.
 *
 * Abstracts access to language models so the extension can use
 * provider-specific APIs without leaking that dependency into
 * the extension's command and governance layers.
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
    readonly displayName: string;
    readonly isAvailable: boolean;

    classify(input: string, schema: Record<string, unknown>): Promise<ClassificationResult>;
    generate(prompt: string): Promise<string>;
}

/**
 * LLM provider that can be initialized and queried for available model families.
 * Extension commands depend on this richer contract instead of a concrete provider.
 */
export interface ManagedLLMProvider extends LLMProvider {
    readonly currentFamily: string;

    initialize(family?: string): Promise<boolean>;
    listModelFamilies(): Promise<string[]>;
}
