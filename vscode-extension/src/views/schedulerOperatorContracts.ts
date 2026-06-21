export type SchedulerOperatorAction =
  | { kind: 'admit'; artifactId: string; version: string }
  | { kind: 'runLoop' }
  | { kind: 'project' }
  | { kind: 'cleanupReceipts'; evidencePath: string; confirmed: boolean }
  | {
      kind: 'runSandboxReceiptWorkflow';
      mode: 'run-once';
      workspaceRoot: string;
      gitWorktreeSandboxRoot: string;
      allocationEvidenceId: string;
      allocationEvidencePath: string;
      cleanup: boolean;
      cleanupEvidenceId: string;
      cleanupEvidencePath: string;
    };

export type SchedulerOperatorWebviewMessage = {
  command?: unknown;
  action?: unknown;
  artifactId?: unknown;
  version?: unknown;
  evidencePath?: unknown;
  confirmed?: unknown;
  workflowMode?: unknown;
  workspaceRoot?: unknown;
  gitWorktreeSandboxRoot?: unknown;
  allocationEvidenceId?: unknown;
  allocationEvidencePath?: unknown;
  cleanup?: unknown;
  cleanupEvidenceId?: unknown;
  cleanupEvidencePath?: unknown;
};

export type SchedulerOperatorWorkflowArgsOptions = {
  actor?: string;
  evidenceId?: string;
  now?: () => number;
};

const DEFAULT_OPERATOR_ACTOR = 'vscode-scheduler-operator';

export function coerceSchedulerOperatorActionMessage(
  message: SchedulerOperatorWebviewMessage,
): SchedulerOperatorAction | null {
  if (message.command !== 'schedulerOperatorAction') {
    return null;
  }
  if (message.action === 'admit') {
    if (typeof message.artifactId !== 'string' || !message.artifactId.trim()) {
      return null;
    }
    if (typeof message.version !== 'string' || !message.version.trim()) {
      return null;
    }
    return {
      kind: 'admit',
      artifactId: message.artifactId,
      version: message.version,
    };
  }
  if (message.action === 'runLoop') {
    return { kind: 'runLoop' };
  }
  if (message.action === 'project') {
    return { kind: 'project' };
  }
  if (message.action === 'cleanupReceipts') {
    if (typeof message.evidencePath !== 'string' || !message.evidencePath.trim()) {
      return null;
    }
    if (message.confirmed !== true) {
      return null;
    }
    return {
      kind: 'cleanupReceipts',
      evidencePath: message.evidencePath.trim(),
      confirmed: true,
    };
  }
  if (message.action === 'runSandboxReceiptWorkflow') {
    if (message.workflowMode !== 'run-once') {
      return null;
    }
    if (typeof message.workspaceRoot !== 'string' || !message.workspaceRoot.trim()) {
      return null;
    }
    if (
      typeof message.gitWorktreeSandboxRoot !== 'string'
      || !message.gitWorktreeSandboxRoot.trim()
    ) {
      return null;
    }
    if (
      typeof message.allocationEvidenceId !== 'string'
      || !message.allocationEvidenceId.trim()
    ) {
      return null;
    }
    const cleanup = message.cleanup === true;
    if (cleanup) {
      if (
        typeof message.cleanupEvidenceId !== 'string'
        || !message.cleanupEvidenceId.trim()
      ) {
        return null;
      }
      if (
        typeof message.cleanupEvidencePath !== 'string'
        || !message.cleanupEvidencePath.trim()
      ) {
        return null;
      }
    }
    return {
      kind: 'runSandboxReceiptWorkflow',
      mode: 'run-once',
      workspaceRoot: message.workspaceRoot.trim(),
      gitWorktreeSandboxRoot: message.gitWorktreeSandboxRoot.trim(),
      allocationEvidenceId: message.allocationEvidenceId.trim(),
      allocationEvidencePath: typeof message.allocationEvidencePath === 'string'
        ? message.allocationEvidencePath.trim()
        : '',
      cleanup,
      cleanupEvidenceId: cleanup && typeof message.cleanupEvidenceId === 'string'
        ? message.cleanupEvidenceId.trim()
        : '',
      cleanupEvidencePath: cleanup && typeof message.cleanupEvidencePath === 'string'
        ? message.cleanupEvidencePath.trim()
        : '',
    };
  }
  return null;
}

export function buildSchedulerOperatorWorkflowArgs(
  action: SchedulerOperatorAction,
  options: SchedulerOperatorWorkflowArgsOptions = {},
): string[] {
  const baseArgs = [
    'scheduler',
    'operator-workflow',
    '--artifact-store-path',
    '.codex/orchestration/exchange-artifacts.json',
    '--admission-ledger-path',
    '.codex/orchestration/exchange-artifact-admissions.json',
    '--snapshot-path',
    '.codex/scheduler/scheduler-state.json',
    '--event-log-path',
    '.codex/scheduler/scheduler-events.jsonl',
    '--projection-output-path',
    '.codex/progress-graph/scheduler-work-trajectory.json',
    '--actor',
    options.actor ?? DEFAULT_OPERATOR_ACTOR,
  ];
  if (action.kind === 'admit') {
    return [
      ...baseArgs,
      '--artifact-id',
      action.artifactId,
      '--version',
      action.version,
      '--admit',
    ];
  }
  if (action.kind === 'runLoop') {
    const evidenceId = options.evidenceId ?? `vscode-operator-${(options.now ?? Date.now)()}`;
    return [
      ...baseArgs,
      '--run-loop',
      '--runtime-provider',
      'fake',
      '--max-ticks',
      '3',
      '--max-runs-per-tick',
      '1',
      '--evidence-id',
      evidenceId,
      '--evidence-path',
      `.codex/scheduler/evidence/${evidenceId}.json`,
    ];
  }
  if (action.kind === 'cleanupReceipts') {
    const evidenceId = options.evidenceId ?? `vscode-cleanup-${(options.now ?? Date.now)()}`;
    return [
      'scheduler',
      'cleanup-receipts',
      '--input-evidence-path',
      action.evidencePath,
      '--output-evidence-id',
      evidenceId,
      '--output-evidence-path',
      `.codex/scheduler/evidence/${evidenceId}.json`,
    ];
  }
  if (action.kind === 'runSandboxReceiptWorkflow') {
    const args = [
      'scheduler',
      'sandbox-receipt-workflow',
      '--mode',
      action.mode,
      '--snapshot-path',
      '.codex/scheduler/scheduler-state.json',
      '--event-log-path',
      '.codex/scheduler/scheduler-events.jsonl',
      '--workspace-root',
      action.workspaceRoot,
      '--git-worktree-sandbox-root',
      action.gitWorktreeSandboxRoot,
      '--allocation-evidence-id',
      action.allocationEvidenceId,
      '--runtime-provider',
      'fake',
      '--max-runs',
      '1',
    ];
    if (action.allocationEvidencePath) {
      args.push('--allocation-evidence-path', action.allocationEvidencePath);
    }
    if (action.cleanup) {
      args.push(
        '--cleanup',
        '--cleanup-evidence-id',
        action.cleanupEvidenceId,
        '--cleanup-evidence-path',
        action.cleanupEvidencePath,
      );
    }
    return args;
  }
  return [
    ...baseArgs,
    '--refresh-projection',
    '--guide-context',
    'vscode-scheduler-operator',
  ];
}
