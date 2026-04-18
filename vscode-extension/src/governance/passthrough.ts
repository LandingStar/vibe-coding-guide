/**
 * Pass-through interceptor for MVP.
 * All actions are allowed. Replace with real enforcement later.
 */

import {
    GovernanceInterceptor,
    GovernanceDecision,
    AgentAction,
    ReviewPanel,
    ReviewResult,
} from './types';

export class PassthroughInterceptor implements GovernanceInterceptor {
    async beforeFileWrite(_uri: string, _content: string): Promise<GovernanceDecision> {
        return { allow: true, reason: 'passthrough' };
    }

    async beforeTerminalCommand(_command: string): Promise<GovernanceDecision> {
        return { allow: true, reason: 'passthrough' };
    }

    async beforeAgentAction(_action: AgentAction): Promise<GovernanceDecision> {
        return { allow: true, reason: 'passthrough' };
    }
}

export class PassthroughReviewPanel implements ReviewPanel {
    async requestReview(
        _decision: GovernanceDecision,
        _action: AgentAction
    ): Promise<ReviewResult> {
        return { approved: true, reviewer: 'auto-passthrough' };
    }
}
