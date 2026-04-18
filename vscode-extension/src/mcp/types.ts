/**
 * MCP tool input/output TypeScript types.
 * Mirrors the Python GovernanceTools interface.
 */

// ── Check Constraints ──────────────────────────────────────────────

export interface ConstraintViolation {
    constraint_id: string;
    description: string;
    severity: 'error' | 'warning' | 'info';
    details?: string;
}

export interface CheckConstraintsResult {
    violations: ConstraintViolation[];
    files_to_reread?: string[];
    phase_info?: Record<string, unknown>;
}

// ── Get Pack Info ──────────────────────────────────────────────────

export interface PackInfo {
    packs: Array<{
        name: string;
        version: string;
        kind: string;
        scope: string;
        provides: string[];
        description?: string;
    }>;
    merged_intents: string[];
    merged_gates: string[];
    merged_document_types: string[];
    pack_tree: Record<string, unknown>;
    [key: string]: unknown;
}

// ── Governance Decide ──────────────────────────────────────────────

export interface GovernanceDecideResult {
    decision: 'ALLOW' | 'BLOCK';
    intent: string;
    gate: string;
    envelope: Record<string, unknown>;
    execution: Record<string, unknown>;
}

// ── Analyze Changes ────────────────────────────────────────────────

export interface AnalyzeChangesResult {
    impact: {
        direct: string[];
        transitive: string[];
        error?: string;
    };
    coupling: {
        alerts: Array<{
            annotation_id: string;
            trigger_type: string;
            message: string;
        }>;
    };
}

// ── Get Next Action ────────────────────────────────────────────────

export interface NextActionResult {
    action: string;
    pending_gates: string[];
    instruction: string;
    files_to_update: string[];
}

// ── Query Decision Logs ────────────────────────────────────────────

export interface DecisionLogEntry {
    log_id: string;
    decision_id: string;
    trace_id: string;
    timestamp: string;
    input_summary: string;
    decision: 'ALLOW' | 'BLOCK';
    intent: string;
    gate: string;
}

// ── MCP Tool Call ──────────────────────────────────────────────────

export interface MCPToolCall {
    name: string;
    arguments: Record<string, unknown>;
}

export interface MCPToolResult {
    content: Array<{
        type: 'text';
        text: string;
    }>;
    isError?: boolean;
}
