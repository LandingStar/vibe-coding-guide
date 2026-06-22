import assert from 'node:assert/strict';
import test from 'node:test';

import {
  buildSchedulerOperatorWorkflowArgs,
  coerceSchedulerOperatorActionMessage,
  type SchedulerOperatorAction,
} from '../views/schedulerOperatorContracts.js';

function flagCount(args: string[], flag: string): number {
  return args.filter((arg) => arg === flag).length;
}

function assertOnlyExplicitActionFlag(args: string[], expectedFlag: string | null): void {
  for (const flag of ['--admit', '--run-loop', '--refresh-projection']) {
    assert.equal(flagCount(args, flag), flag === expectedFlag ? 1 : 0);
  }
}

function assertSharedWorkflowBase(args: string[]): void {
  assert.deepEqual(args.slice(0, 2), ['scheduler', 'operator-workflow']);
  assert.ok(args.includes('--artifact-store-path'));
  assert.ok(args.includes('.codex/orchestration/exchange-artifacts.json'));
  assert.ok(args.includes('--admission-ledger-path'));
  assert.ok(args.includes('.codex/orchestration/exchange-artifact-admissions.json'));
  assert.ok(args.includes('--snapshot-path'));
  assert.ok(args.includes('.codex/scheduler/scheduler-state.json'));
  assert.ok(args.includes('--event-log-path'));
  assert.ok(args.includes('.codex/scheduler/scheduler-events.jsonl'));
  assert.ok(args.includes('--projection-output-path'));
  assert.ok(args.includes('.codex/progress-graph/scheduler-work-trajectory.json'));
  assert.ok(args.includes('--actor'));
  assert.ok(args.includes('vscode-scheduler-operator'));
}

test('scheduler operator click sequence maps webview messages to shared workflow args', () => {
  const messages = [
    {
      command: 'schedulerOperatorAction',
      action: 'admit',
      artifactId: 'scheduler-operator-dogfood-multilane',
      version: 'v1',
      inspectBindingRefs: true,
      markConsumedOnSuccess: true,
    },
    {
      command: 'schedulerOperatorAction',
      action: 'runLoop',
    },
    {
      command: 'schedulerOperatorAction',
      action: 'project',
    },
  ];
  const actions = messages.map((message) => coerceSchedulerOperatorActionMessage(message));

  assert.deepEqual(actions, [
    {
      kind: 'admit',
      artifactId: 'scheduler-operator-dogfood-multilane',
      version: 'v1',
      inspectBindingRefs: true,
      markConsumedOnSuccess: true,
    },
    { kind: 'runLoop' },
    { kind: 'project' },
  ] satisfies SchedulerOperatorAction[]);

  const admitArgs = buildSchedulerOperatorWorkflowArgs(actions[0]!, { now: () => 123456 });
  assertSharedWorkflowBase(admitArgs);
  assertOnlyExplicitActionFlag(admitArgs, '--admit');
  assert.deepEqual(
    admitArgs.slice(admitArgs.indexOf('--artifact-id'), admitArgs.indexOf('--artifact-id') + 4),
    ['--artifact-id', 'scheduler-operator-dogfood-multilane', '--version', 'v1'],
  );
  assert.ok(admitArgs.includes('--inspect-binding-refs'));
  assert.ok(admitArgs.includes('--mark-consumed-on-success'));

  const loopArgs = buildSchedulerOperatorWorkflowArgs(actions[1]!, {
    evidenceId: 'vscode-operator-smoke',
  });
  assertSharedWorkflowBase(loopArgs);
  assertOnlyExplicitActionFlag(loopArgs, '--run-loop');
  assert.ok(loopArgs.includes('--runtime-provider'));
  assert.ok(loopArgs.includes('fake'));
  assert.ok(loopArgs.includes('--max-ticks'));
  assert.ok(loopArgs.includes('3'));
  assert.ok(loopArgs.includes('--max-runs-per-tick'));
  assert.ok(loopArgs.includes('1'));
  assert.ok(loopArgs.includes('--evidence-id'));
  assert.ok(loopArgs.includes('vscode-operator-smoke'));
  assert.ok(loopArgs.includes('--evidence-path'));
  assert.ok(loopArgs.includes('.codex/scheduler/evidence/vscode-operator-smoke.json'));

  const projectArgs = buildSchedulerOperatorWorkflowArgs(actions[2]!, { now: () => 123456 });
  assertSharedWorkflowBase(projectArgs);
  assertOnlyExplicitActionFlag(projectArgs, '--refresh-projection');
  assert.ok(projectArgs.includes('--guide-context'));
  assert.ok(projectArgs.includes('vscode-scheduler-operator'));
});

test('scheduler operator admission omits binding inspection unless requested', () => {
  const action = coerceSchedulerOperatorActionMessage({
    command: 'schedulerOperatorAction',
    action: 'admit',
    artifactId: 'submission:plain',
    version: 'v1',
  });

  assert.deepEqual(action, {
    kind: 'admit',
    artifactId: 'submission:plain',
    version: 'v1',
    inspectBindingRefs: false,
    markConsumedOnSuccess: false,
  } satisfies SchedulerOperatorAction);

  const args = buildSchedulerOperatorWorkflowArgs(action!);
  assertOnlyExplicitActionFlag(args, '--admit');
  assert.equal(flagCount(args, '--inspect-binding-refs'), 0);
  assert.equal(flagCount(args, '--mark-consumed-on-success'), 0);
});

test('scheduler operator click contract rejects incomplete admission messages', () => {
  assert.equal(
    coerceSchedulerOperatorActionMessage({
      command: 'schedulerOperatorAction',
      action: 'admit',
      artifactId: 'submission:missing-version',
    }),
    null,
  );
  assert.equal(
    coerceSchedulerOperatorActionMessage({
      command: 'schedulerOperatorAction',
      action: 'admit',
      version: 'v1',
    }),
    null,
  );
  assert.equal(
    coerceSchedulerOperatorActionMessage({
      command: 'refresh',
      action: 'runLoop',
    }),
    null,
  );
});

test('scheduler operator run-loop args can derive deterministic evidence path from clock', () => {
  const args = buildSchedulerOperatorWorkflowArgs(
    { kind: 'runLoop' },
    { now: () => 42 },
  );

  assert.ok(args.includes('--evidence-id'));
  assert.ok(args.includes('vscode-operator-42'));
  assert.ok(args.includes('--evidence-path'));
  assert.ok(args.includes('.codex/scheduler/evidence/vscode-operator-42.json'));
});

test('scheduler operator cleanup receipts action requires path and explicit confirmation', () => {
  assert.equal(
    coerceSchedulerOperatorActionMessage({
      command: 'schedulerOperatorAction',
      action: 'cleanupReceipts',
      evidencePath: '.codex/scheduler/evidence/allocation.json',
      confirmed: false,
    }),
    null,
  );
  assert.equal(
    coerceSchedulerOperatorActionMessage({
      command: 'schedulerOperatorAction',
      action: 'cleanupReceipts',
      confirmed: true,
    }),
    null,
  );

  const action = coerceSchedulerOperatorActionMessage({
    command: 'schedulerOperatorAction',
    action: 'cleanupReceipts',
    evidencePath: '  .codex/scheduler/evidence/allocation.json  ',
    confirmed: true,
  });

  assert.deepEqual(action, {
    kind: 'cleanupReceipts',
    evidencePath: '.codex/scheduler/evidence/allocation.json',
    confirmed: true,
  } satisfies SchedulerOperatorAction);
});

test('scheduler operator cleanup receipts action maps to explicit cleanup CLI surface', () => {
  const args = buildSchedulerOperatorWorkflowArgs(
    {
      kind: 'cleanupReceipts',
      evidencePath: '.codex/scheduler/evidence/allocation.json',
      confirmed: true,
    },
    { now: () => 777 },
  );

  assert.deepEqual(args.slice(0, 2), ['scheduler', 'cleanup-receipts']);
  assert.ok(args.includes('--input-evidence-path'));
  assert.ok(args.includes('.codex/scheduler/evidence/allocation.json'));
  assert.ok(args.includes('--output-evidence-id'));
  assert.ok(args.includes('vscode-cleanup-777'));
  assert.ok(args.includes('--output-evidence-path'));
  assert.ok(args.includes('.codex/scheduler/evidence/vscode-cleanup-777.json'));
  assert.equal(flagCount(args, '--admit'), 0);
  assert.equal(flagCount(args, '--run-loop'), 0);
  assert.equal(flagCount(args, '--refresh-projection'), 0);
});

test('scheduler operator run-once sandbox receipt workflow requires explicit inputs', () => {
  assert.equal(
    coerceSchedulerOperatorActionMessage({
      command: 'schedulerOperatorAction',
      action: 'runSandboxReceiptWorkflow',
      workflowMode: 'daemon-loop',
      workspaceRoot: 'repo',
      gitWorktreeSandboxRoot: 'sandboxes',
      allocationEvidenceId: 'allocation',
    }),
    null,
  );
  assert.equal(
    coerceSchedulerOperatorActionMessage({
      command: 'schedulerOperatorAction',
      action: 'runSandboxReceiptWorkflow',
      workflowMode: 'run-once',
      workspaceRoot: '',
      gitWorktreeSandboxRoot: 'sandboxes',
      allocationEvidenceId: 'allocation',
    }),
    null,
  );
  assert.equal(
    coerceSchedulerOperatorActionMessage({
      command: 'schedulerOperatorAction',
      action: 'runSandboxReceiptWorkflow',
      workflowMode: 'run-once',
      workspaceRoot: 'repo',
      gitWorktreeSandboxRoot: 'sandboxes',
      allocationEvidenceId: 'allocation',
      cleanup: true,
      cleanupEvidenceId: 'cleanup',
    }),
    null,
  );

  const action = coerceSchedulerOperatorActionMessage({
    command: 'schedulerOperatorAction',
    action: 'runSandboxReceiptWorkflow',
    workflowMode: 'run-once',
    workspaceRoot: ' repo ',
    gitWorktreeSandboxRoot: ' sandboxes ',
    allocationEvidenceId: ' allocation ',
    allocationEvidencePath: ' .codex/scheduler/evidence/allocation.json ',
    cleanup: true,
    cleanupEvidenceId: ' cleanup ',
    cleanupEvidencePath: ' .codex/scheduler/evidence/cleanup.json ',
  });

  assert.deepEqual(action, {
    kind: 'runSandboxReceiptWorkflow',
    mode: 'run-once',
    workspaceRoot: 'repo',
    gitWorktreeSandboxRoot: 'sandboxes',
    allocationEvidenceId: 'allocation',
    allocationEvidencePath: '.codex/scheduler/evidence/allocation.json',
    maxTicks: '',
    maxRunsPerTick: '',
    maxRuntimeFailures: '',
    cleanup: true,
    cleanupEvidenceId: 'cleanup',
    cleanupEvidencePath: '.codex/scheduler/evidence/cleanup.json',
  } satisfies SchedulerOperatorAction);
});

test('scheduler operator run-once sandbox receipt workflow maps to explicit workflow CLI surface', () => {
  const args = buildSchedulerOperatorWorkflowArgs({
    kind: 'runSandboxReceiptWorkflow',
    mode: 'run-once',
    workspaceRoot: 'repo',
    gitWorktreeSandboxRoot: 'sandboxes',
    allocationEvidenceId: 'workflow-allocation',
    allocationEvidencePath: '.codex/scheduler/evidence/workflow-allocation.json',
    maxTicks: '',
    maxRunsPerTick: '',
    maxRuntimeFailures: '',
    cleanup: false,
    cleanupEvidenceId: '',
    cleanupEvidencePath: '',
  });

  assert.deepEqual(args.slice(0, 2), ['scheduler', 'sandbox-receipt-workflow']);
  assert.deepEqual(args.slice(args.indexOf('--mode'), args.indexOf('--mode') + 2), ['--mode', 'run-once']);
  assert.ok(args.includes('--snapshot-path'));
  assert.ok(args.includes('.codex/scheduler/scheduler-state.json'));
  assert.ok(args.includes('--event-log-path'));
  assert.ok(args.includes('.codex/scheduler/scheduler-events.jsonl'));
  assert.ok(args.includes('--workspace-root'));
  assert.ok(args.includes('repo'));
  assert.ok(args.includes('--git-worktree-sandbox-root'));
  assert.ok(args.includes('sandboxes'));
  assert.ok(args.includes('--allocation-evidence-id'));
  assert.ok(args.includes('workflow-allocation'));
  assert.ok(args.includes('--allocation-evidence-path'));
  assert.ok(args.includes('.codex/scheduler/evidence/workflow-allocation.json'));
  assert.ok(args.includes('--runtime-provider'));
  assert.ok(args.includes('fake'));
  assert.ok(args.includes('--max-runs'));
  assert.ok(args.includes('1'));
  assertOnlyExplicitActionFlag(args, null);
  assert.equal(flagCount(args, '--cleanup'), 0);
  assert.equal(flagCount(args, '--cleanup-evidence-id'), 0);
  assert.equal(flagCount(args, '--cleanup-evidence-path'), 0);
});

test('scheduler operator run-once sandbox receipt workflow only sends cleanup output when requested', () => {
  const args = buildSchedulerOperatorWorkflowArgs({
    kind: 'runSandboxReceiptWorkflow',
    mode: 'run-once',
    workspaceRoot: 'repo',
    gitWorktreeSandboxRoot: 'sandboxes',
    allocationEvidenceId: 'workflow-allocation',
    allocationEvidencePath: '',
    maxTicks: '',
    maxRunsPerTick: '',
    maxRuntimeFailures: '',
    cleanup: true,
    cleanupEvidenceId: 'workflow-cleanup',
    cleanupEvidencePath: '.codex/scheduler/evidence/workflow-cleanup.json',
  });

  assert.deepEqual(args.slice(0, 2), ['scheduler', 'sandbox-receipt-workflow']);
  assert.ok(args.includes('--cleanup'));
  assert.ok(args.includes('--cleanup-evidence-id'));
  assert.ok(args.includes('workflow-cleanup'));
  assert.ok(args.includes('--cleanup-evidence-path'));
  assert.ok(args.includes('.codex/scheduler/evidence/workflow-cleanup.json'));
  assert.equal(flagCount(args, '--allocation-evidence-path'), 0);
});

test('scheduler operator daemon-loop sandbox receipt workflow requires bounded positive integers', () => {
  for (const badValue of ['', '0', '-1', '1.5', 'abc']) {
    assert.equal(
      coerceSchedulerOperatorActionMessage({
        command: 'schedulerOperatorAction',
        action: 'runSandboxReceiptWorkflow',
        workflowMode: 'daemon-loop',
        workspaceRoot: 'repo',
        gitWorktreeSandboxRoot: 'sandboxes',
        allocationEvidenceId: 'allocation',
        maxTicks: badValue,
        maxRunsPerTick: '1',
        maxRuntimeFailures: '1',
      }),
      null,
    );
  }

  const action = coerceSchedulerOperatorActionMessage({
    command: 'schedulerOperatorAction',
    action: 'runSandboxReceiptWorkflow',
    workflowMode: 'daemon-loop',
    workspaceRoot: ' repo ',
    gitWorktreeSandboxRoot: ' sandboxes ',
    allocationEvidenceId: ' allocation ',
    allocationEvidencePath: ' ',
    maxTicks: ' 4 ',
    maxRunsPerTick: ' 2 ',
    maxRuntimeFailures: ' 3 ',
    cleanup: false,
  });

  assert.deepEqual(action, {
    kind: 'runSandboxReceiptWorkflow',
    mode: 'daemon-loop',
    workspaceRoot: 'repo',
    gitWorktreeSandboxRoot: 'sandboxes',
    allocationEvidenceId: 'allocation',
    allocationEvidencePath: '',
    maxTicks: '4',
    maxRunsPerTick: '2',
    maxRuntimeFailures: '3',
    cleanup: false,
    cleanupEvidenceId: '',
    cleanupEvidencePath: '',
  } satisfies SchedulerOperatorAction);
});

test('scheduler operator daemon-loop sandbox receipt workflow maps bounded flags', () => {
  const args = buildSchedulerOperatorWorkflowArgs({
    kind: 'runSandboxReceiptWorkflow',
    mode: 'daemon-loop',
    workspaceRoot: 'repo',
    gitWorktreeSandboxRoot: 'sandboxes',
    allocationEvidenceId: 'workflow-allocation',
    allocationEvidencePath: '',
    maxTicks: '4',
    maxRunsPerTick: '2',
    maxRuntimeFailures: '3',
    cleanup: false,
    cleanupEvidenceId: '',
    cleanupEvidencePath: '',
  });

  assert.deepEqual(args.slice(0, 2), ['scheduler', 'sandbox-receipt-workflow']);
  assert.deepEqual(args.slice(args.indexOf('--mode'), args.indexOf('--mode') + 2), ['--mode', 'daemon-loop']);
  assert.deepEqual(
    args.slice(args.indexOf('--max-ticks'), args.indexOf('--max-ticks') + 2),
    ['--max-ticks', '4'],
  );
  assert.deepEqual(
    args.slice(args.indexOf('--max-runs-per-tick'), args.indexOf('--max-runs-per-tick') + 2),
    ['--max-runs-per-tick', '2'],
  );
  assert.deepEqual(
    args.slice(args.indexOf('--max-runtime-failures'), args.indexOf('--max-runtime-failures') + 2),
    ['--max-runtime-failures', '3'],
  );
  assert.equal(flagCount(args, '--max-runs'), 0);
  assertOnlyExplicitActionFlag(args, null);
});
