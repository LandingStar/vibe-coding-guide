export type SchedulerOperatorAction =
  | { kind: 'admit'; artifactId: string; version: string }
  | { kind: 'runLoop' }
  | { kind: 'project' }
  | { kind: 'cleanupReceipts'; evidencePath: string; confirmed: boolean };

export type SchedulerOperatorWebviewMessage = {
  command?: unknown;
  action?: unknown;
  artifactId?: unknown;
  version?: unknown;
  evidencePath?: unknown;
  confirmed?: unknown;
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
  return [
    ...baseArgs,
    '--refresh-projection',
    '--guide-context',
    'vscode-scheduler-operator',
  ];
}
