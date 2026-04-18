/**
 * Governance interceptor interfaces.
 *
 * These interfaces define the enforcement layer that sits between
 * agent actions and the governance runtime. MVP uses PassthroughInterceptor;
 * future versions will implement real interception.
 *
 * Design note: these interfaces support multi-agent scenarios where
 * each agent session has its own interceptor context, and recursive
 * governance flows where a sub-agent's actions are governed by
 * nested interceptor chains.
 */

/** Result of a governance decision at the interceptor level. */
export interface GovernanceDecision {
    allow: boolean;
    reason?: string;
    /** If not allowed, a user-facing message explaining why. */
    denyMessage?: string;
    /** Trace ID linking back to the PDP decision. */
    traceId?: string;
    /** If the action needs human review before proceeding. */
    requiresReview?: boolean;
}

/** Describes an agent action for governance evaluation. */
export interface AgentAction {
    type: 'file-write' | 'terminal-command' | 'tool-call' | 'delegation' | string;
    description: string;
    /** The agent session ID (for multi-agent tracking). */
    agentId?: string;
    /** Parent agent ID if this is a sub-agent action (for recursive governance). */
    parentAgentId?: string;
    metadata?: Record<string, unknown>;
}

/** Result of a human review request. */
export interface ReviewResult {
    approved: boolean;
    reviewer?: string;
    comments?: string;
    timestamp?: string;
}

/**
 * Intercepts agent actions before they execute.
 * Implementations can query the governance runtime (via MCP)
 * to enforce constraints.
 */
export interface GovernanceInterceptor {
    beforeFileWrite(uri: string, content: string): Promise<GovernanceDecision>;
    beforeTerminalCommand(command: string): Promise<GovernanceDecision>;
    beforeAgentAction(action: AgentAction): Promise<GovernanceDecision>;
}

/**
 * Human review panel for governance decisions that require approval.
 */
export interface ReviewPanel {
    requestReview(decision: GovernanceDecision, action: AgentAction): Promise<ReviewResult>;
}

/**
 * Multi-agent session context.
 * Tracks agent hierarchy for recursive governance visualization.
 */
export interface AgentSession {
    agentId: string;
    parentAgentId?: string;
    label: string;
    /** Current governance state for this agent. */
    constraintState?: Record<string, unknown>;
    /** Child agent sessions (for recursive display). */
    children: AgentSession[];
}
