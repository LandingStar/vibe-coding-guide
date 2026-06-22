import * as vscode from 'vscode';
import { execFile } from 'child_process';
import { promisify } from 'util';
import {
  buildSchedulerOperatorWorkflowArgs,
  type SchedulerOperatorAction,
} from './schedulerOperatorContracts';

const execFileAsync = promisify(execFile);

export const EXCHANGE_ARTIFACTS_BUNDLE_RESOURCE_URI = 'dbc://exchange-artifacts/bundle';

export type SchedulerOperatorRuntimeOptions = {
  projectRoot: string;
  sourceRoot: string | null;
  pythonPath: string;
  outputChannel: vscode.OutputChannel;
};

export type SchedulerOperatorExchangeCandidate = {
  artifactId: string;
  version: string;
  lifecycleState: string;
  productType: string;
  taskIds: string[];
  taskCount: number;
  batchId: string;
  admissionStatus: string;
  latestAdmissionStatus: string;
  bindingReferenceReadiness: SchedulerOperatorBindingReferenceSummary | null;
  latestBindingReferenceSummary: SchedulerOperatorBindingReferenceSummary | null;
};

export type SchedulerOperatorBindingReference = {
  refKind: string;
  refId: string;
  version: string;
  path: string;
  label: string;
};

export type SchedulerOperatorBindingReferenceTaskSummary = {
  taskId: string;
  title: string;
  ok: boolean;
  bindingRefCount: number;
  checkedRefCount: number;
  errorCount: number;
  bindingRefs: SchedulerOperatorBindingReference[];
  checkedRefs: SchedulerOperatorBindingReference[];
  errors: string[];
};

export type SchedulerOperatorBindingReferenceSummary = {
  enabled: boolean;
  ok: boolean;
  sourceArtifactId: string;
  sourceArtifactVersion: string;
  submissionProductType: string;
  taskCount: number;
  bindingRefCount: number;
  checkedRefCount: number;
  errorCount: number;
  errors: string[];
  tasks: SchedulerOperatorBindingReferenceTaskSummary[];
  rawEvidenceJsonRead: boolean;
  ledgerId: string;
  status: string;
  timestamp: string;
  actor: string;
  surface: string;
  errorSummary: string;
};

export type SchedulerOperatorExchangeSummary = {
  exists: boolean;
  storePath: string;
  artifactCount: number;
  versionCount: number;
  admissionCandidateCount: number;
  admissionLedgerPath: string;
  admissionLedgerExists: boolean;
  candidates: SchedulerOperatorExchangeCandidate[];
  errors: string[];
};

export type SchedulerOperatorSchedulerSummary = {
  snapshotExists: boolean;
  eventLogExists: boolean;
  taskCount: number;
  dependencyCount: number;
  runRecordCount: number;
  schedulerEventCount: number;
  taskStateCounts: Record<string, number>;
  schedulerEventKindCounts: Record<string, number>;
};

export type SchedulerOperatorPaths = {
  artifactStorePath: string;
  admissionLedgerPath: string;
  schedulerSnapshotPath: string;
  schedulerEventLogPath: string;
  schedulerProjectionPath: string;
};

export type SchedulerOperatorLastAction = {
  action: string;
  status: 'idle' | 'running' | 'succeeded' | 'failed';
  startedAt: string | null;
  completedAt: string | null;
  summary: string;
  stdout: string;
  stderr: string;
  payload: Record<string, unknown> | null;
};

export type SchedulerAuthorizationLifecycleSummary = {
  leaseId: string;
  taskId: string;
  state: string;
  mode: string;
  allowedArtifacts: string[];
  deniedArtifacts: string[];
  conflictPolicy: string;
  acquiredAt: string;
  expiresAt: string;
  releasedAt: string;
  reason: string;
  conflictState: string;
  conflictClassification: string;
};

export type SchedulerAuthorizationSandboxSummary = {
  profileId: string;
  profileKind: string;
  mountPolicy: string;
  allocationState: string;
  allocationReason: string;
  visibleMounts: string[];
  leaseAuthorizationState: string;
  leaseAuthorizationReason: string;
};

export type SchedulerAuthorizationTaskSummary = {
  taskId: string;
  title: string;
  state: string;
  agentId: string;
  runtimeProvider: string;
  hasEditLease: boolean;
  leaseId: string;
  leaseMode: string;
  allowedArtifacts: string[];
  deniedArtifacts: string[];
  conflictPolicy: string;
  leaseExpiresAt: string;
  lifecycleMissing: boolean;
  lifecycle: SchedulerAuthorizationLifecycleSummary | null;
  sandboxAuthorization: SchedulerAuthorizationSandboxSummary | null;
};

export type SchedulerAuthorizationReadback = {
  ok: boolean;
  productType: string;
  schemaVersion: string;
  snapshotPath: string;
  schedulerEventLogPath: string;
  recoveredFromEventLog: boolean;
  strictReplay: boolean;
  taskCount: number;
  editLeaseTaskCount: number;
  lifecycleRecordCount: number;
  lifecycleStateCounts: Record<string, number>;
  sandboxAuthorizationStateCounts: Record<string, number>;
  orphanLifecycleRecordCount: number;
  tasks: SchedulerAuthorizationTaskSummary[];
  error: string;
};

export type SchedulerOperatorWorkflowState = {
  exchangeResourceUri: string;
  exchange: SchedulerOperatorExchangeSummary | null;
  exchangeReadError: string | null;
  scheduler: SchedulerOperatorSchedulerSummary | null;
  schedulerReadError: string | null;
  authorizationReadback: SchedulerAuthorizationReadback | null;
  authorizationReadError: string | null;
  paths: SchedulerOperatorPaths;
  lastAction: SchedulerOperatorLastAction;
};

export function buildIdleSchedulerOperatorLastAction(): SchedulerOperatorLastAction {
  return {
    action: '',
    status: 'idle',
    startedAt: null,
    completedAt: null,
    summary: '',
    stdout: '',
    stderr: '',
    payload: null,
  };
}

export function buildSchedulerOperatorPaths(projectRoot: string): SchedulerOperatorPaths {
  return {
    artifactStorePath: `${projectRoot}/.codex/orchestration/exchange-artifacts.json`,
    admissionLedgerPath: `${projectRoot}/.codex/orchestration/exchange-artifact-admissions.json`,
    schedulerSnapshotPath: `${projectRoot}/.codex/scheduler/scheduler-state.json`,
    schedulerEventLogPath: `${projectRoot}/.codex/scheduler/scheduler-events.jsonl`,
    schedulerProjectionPath: `${projectRoot}/.codex/progress-graph/scheduler-work-trajectory.json`,
  };
}

export async function readSchedulerOperatorWorkflowState(
  options: SchedulerOperatorRuntimeOptions & {
    lastAction: SchedulerOperatorLastAction;
  },
): Promise<SchedulerOperatorWorkflowState> {
  const paths = buildSchedulerOperatorPaths(options.projectRoot);
  const schedulerReadback = await readSchedulerSummary(options);
  const authorizationReadback = await readSchedulerAuthorizationReadback(options, paths);
  try {
    const raw = await readResourceJson(options, EXCHANGE_ARTIFACTS_BUNDLE_RESOURCE_URI);
    return {
      exchangeResourceUri: EXCHANGE_ARTIFACTS_BUNDLE_RESOURCE_URI,
      exchange: coerceExchangeSummary(raw),
      exchangeReadError: null,
      scheduler: schedulerReadback.scheduler,
      schedulerReadError: schedulerReadback.schedulerReadError,
      authorizationReadback: authorizationReadback.readback,
      authorizationReadError: authorizationReadback.readError,
      paths,
      lastAction: options.lastAction,
    };
  } catch (error) {
    return {
      exchangeResourceUri: EXCHANGE_ARTIFACTS_BUNDLE_RESOURCE_URI,
      exchange: null,
      exchangeReadError: error instanceof Error ? error.message : String(error),
      scheduler: schedulerReadback.scheduler,
      schedulerReadError: schedulerReadback.schedulerReadError,
      authorizationReadback: authorizationReadback.readback,
      authorizationReadError: authorizationReadback.readError,
      paths,
      lastAction: options.lastAction,
    };
  }
}

export async function runSchedulerOperatorAction(
  options: SchedulerOperatorRuntimeOptions & {
    action: SchedulerOperatorAction;
  },
): Promise<SchedulerOperatorLastAction> {
  const startedAt = new Date().toISOString();
  const args = buildSchedulerOperatorWorkflowArgs(options.action);
  options.outputChannel.appendLine(
    `[SchedulerOperator] Running ${options.action.kind}: ${options.pythonPath} doc-based-coding ${args.join(' ')}`,
  );

  try {
    const { stdout, stderr } = await execFileAsync(
      options.pythonPath,
      buildCliScriptInvocation(options, args),
      {
        cwd: options.projectRoot,
        maxBuffer: 2 * 1024 * 1024,
      },
    );
    const payload = parseJsonObject(stdout);
    return {
      action: options.action.kind,
      status: 'succeeded',
      startedAt,
      completedAt: new Date().toISOString(),
      summary: summarizeActionPayload(options.action.kind, payload),
      stdout: stdout.trim(),
      stderr: stderr.trim(),
      payload,
    };
  } catch (error: unknown) {
    const execError = error as {
      stdout?: string;
      stderr?: string;
      message?: string;
    };
    const stdout = typeof execError.stdout === 'string' ? execError.stdout.trim() : '';
    const stderr = typeof execError.stderr === 'string' ? execError.stderr.trim() : '';
    return {
      action: options.action.kind,
      status: 'failed',
      startedAt,
      completedAt: new Date().toISOString(),
      summary: stderr || execError.message || String(error),
      stdout,
      stderr,
      payload: parseJsonObjectOrNull(stdout),
    };
  }
}

async function readResourceJson(
  options: SchedulerOperatorRuntimeOptions,
  resourceUri: string,
): Promise<Record<string, unknown>> {
  const readResourceScript = [
    'import importlib.metadata',
    'import json',
    'import sys',
    ...(options.sourceRoot ? [`sys.path.append(${JSON.stringify(options.sourceRoot)})`] : []),
    'try:',
    '    runtime_root = importlib.metadata.distribution("doc-based-coding-runtime").locate_file("")',
    '    sys.path.insert(0, str(runtime_root))',
    'except importlib.metadata.PackageNotFoundError:',
    '    pass',
    'from src.mcp.tools import GovernanceTools',
    `tools = GovernanceTools(${JSON.stringify(options.projectRoot)}, dry_run=True)`,
    `content = tools.read_resource(${JSON.stringify(resourceUri)})`,
    'if content is None:',
    `    raise RuntimeError("resource not found: ${resourceUri}")`,
    'if isinstance(content, dict):',
    '    print(json.dumps(content, ensure_ascii=False))',
    'else:',
    '    print(content)',
  ].join('\n');

  options.outputChannel.appendLine(
    `[SchedulerOperator] Reading ${resourceUri} with Python: ${options.pythonPath}`,
  );
  const { stdout, stderr } = await execFileAsync(
    options.pythonPath,
    ['-c', readResourceScript],
    {
      cwd: options.projectRoot,
      maxBuffer: 1024 * 1024,
    },
  );
  const stderrText = stderr.trim();
  if (stderrText) {
    options.outputChannel.appendLine(`[SchedulerOperator resource stderr] ${stderrText}`);
  }
  return parseJsonObject(stdout);
}

async function readSchedulerSummary(
  options: SchedulerOperatorRuntimeOptions,
): Promise<{
  scheduler: SchedulerOperatorSchedulerSummary | null;
  schedulerReadError: string | null;
}> {
  try {
    const { stdout } = await execFileAsync(
      options.pythonPath,
      buildCliScriptInvocation(options, [
        'scheduler',
        'inspect-state',
        '--snapshot-path',
        '.codex/scheduler/scheduler-state.json',
        '--event-log-path',
        '.codex/scheduler/scheduler-events.jsonl',
      ]),
      {
        cwd: options.projectRoot,
        maxBuffer: 1024 * 1024,
      },
    );
    const payload = parseJsonObject(stdout);
    return {
      scheduler: {
        snapshotExists: readBoolean(payload.snapshot_exists),
        eventLogExists: readBoolean(payload.scheduler_event_log_exists),
        taskCount: readNumber(payload.task_count),
        dependencyCount: readNumber(payload.dependency_count),
        runRecordCount: readNumber(payload.run_record_count),
        schedulerEventCount: readNumber(payload.scheduler_event_count),
        taskStateCounts: readNumberRecord(payload.task_state_counts),
        schedulerEventKindCounts: readNumberRecord(payload.scheduler_event_kind_counts),
      },
      schedulerReadError: null,
    };
  } catch (error: unknown) {
    const execError = error as { stderr?: string; message?: string };
    return {
      scheduler: null,
      schedulerReadError: execError.stderr?.trim() || execError.message || String(error),
    };
  }
}

async function readSchedulerAuthorizationReadback(
  options: SchedulerOperatorRuntimeOptions,
  paths: SchedulerOperatorPaths,
): Promise<{
  readback: SchedulerAuthorizationReadback | null;
  readError: string | null;
}> {
  const readbackScript = [
    'import importlib.metadata',
    'import json',
    'import sys',
    ...(options.sourceRoot ? [`sys.path.append(${JSON.stringify(options.sourceRoot)})`] : []),
    'try:',
    '    runtime_root = importlib.metadata.distribution("doc-based-coding-runtime").locate_file("")',
    '    sys.path.insert(0, str(runtime_root))',
    'except importlib.metadata.PackageNotFoundError:',
    '    pass',
    'from src.mcp.tools import GovernanceTools',
    `tools = GovernanceTools(${JSON.stringify(options.projectRoot)}, dry_run=True)`,
    'payload = tools.scheduler_authorization_readback(',
    `    snapshot_path=${JSON.stringify(paths.schedulerSnapshotPath)},`,
    `    scheduler_event_log_path=${JSON.stringify(paths.schedulerEventLogPath)},`,
    '    strict=True,',
    `    workspace_root=${JSON.stringify(options.projectRoot)},`,
    '    scratch_root=".codex/scratch",',
    ')',
    'print(json.dumps(payload, ensure_ascii=False))',
  ].join('\n');

  options.outputChannel.appendLine(
    `[SchedulerOperator] Reading scheduler authorization readback with Python: ${options.pythonPath}`,
  );

  try {
    const { stdout, stderr } = await execFileAsync(
      options.pythonPath,
      ['-c', readbackScript],
      {
        cwd: options.projectRoot,
        maxBuffer: 1024 * 1024,
      },
    );
    const stderrText = stderr.trim();
    if (stderrText) {
      options.outputChannel.appendLine(`[SchedulerOperator authorization stderr] ${stderrText}`);
    }
    return {
      readback: coerceSchedulerAuthorizationReadback(parseJsonObject(stdout)),
      readError: null,
    };
  } catch (error: unknown) {
    const execError = error as { stderr?: string; message?: string };
    return {
      readback: null,
      readError: execError.stderr?.trim() || execError.message || String(error),
    };
  }
}

function buildCliScriptInvocation(
  options: SchedulerOperatorRuntimeOptions,
  args: string[],
): string[] {
  const script = [
    'import importlib.metadata',
    'import sys',
    ...(options.sourceRoot ? [`sys.path.append(${JSON.stringify(options.sourceRoot)})`] : []),
    'try:',
    '    runtime_root = importlib.metadata.distribution("doc-based-coding-runtime").locate_file("")',
    '    sys.path.insert(0, str(runtime_root))',
    'except importlib.metadata.PackageNotFoundError:',
    '    pass',
    'from src.__main__ import main',
    `sys.argv = ["doc-based-coding", *${JSON.stringify(args)}]`,
    'raise SystemExit(main())',
  ].join('\n');
  return ['-c', script];
}

function coerceExchangeSummary(value: Record<string, unknown>): SchedulerOperatorExchangeSummary {
  const summaries = readObjectArray(value.summaries);
  const candidates = summaries.flatMap((summary) => {
    const artifactId = readString(summary.artifact_id, '');
    const version = readString(summary.version, '');
    const admissionState = readRecord(summary.admission_state);
    return readObjectArray(summary.admission_candidates).map((candidate) => ({
      artifactId,
      version,
      lifecycleState: readString(summary.lifecycle_state, 'unknown'),
      productType: readString(candidate.product_type, 'unknown'),
      taskIds: readStringArray(candidate.task_ids),
      taskCount: readNumber(candidate.task_count),
      batchId: readString(candidate.batch_id, ''),
      admissionStatus: readString(admissionState.status, 'unknown'),
      latestAdmissionStatus: readString(admissionState.latest_status, ''),
      bindingReferenceReadiness: coerceBindingReferenceSummary(
        readRecord(candidate.binding_reference_readiness),
      ),
      latestBindingReferenceSummary: coerceBindingReferenceSummary(
        readRecord(candidate.latest_binding_reference_summary),
      ),
    }));
  });

  return {
    exists: readBoolean(value.exists),
    storePath: readString(value.store_path, ''),
    artifactCount: readNumber(value.artifact_count),
    versionCount: readNumber(value.version_count),
    admissionCandidateCount: readNumber(value.admission_candidate_count),
    admissionLedgerPath: readString(value.admission_ledger_path, ''),
    admissionLedgerExists: readBoolean(value.admission_ledger_exists),
    candidates,
    errors: readStringArray(value.errors),
  };
}

function coerceBindingReferenceSummary(
  value: Record<string, unknown>,
): SchedulerOperatorBindingReferenceSummary | null {
  if (Object.keys(value).length === 0) {
    return null;
  }
  return {
    enabled: readBoolean(value.enabled),
    ok: readBoolean(value.ok),
    sourceArtifactId: readString(value.source_artifact_id, ''),
    sourceArtifactVersion: readString(value.source_artifact_version, ''),
    submissionProductType: readString(value.submission_product_type, ''),
    taskCount: readNumber(value.task_count),
    bindingRefCount: readNumber(value.binding_ref_count),
    checkedRefCount: readNumber(value.checked_ref_count),
    errorCount: readNumber(value.error_count),
    errors: readStringArray(value.errors),
    tasks: readObjectArray(value.tasks).map(coerceBindingReferenceTaskSummary),
    rawEvidenceJsonRead: readBoolean(value.raw_evidence_json_read),
    ledgerId: readString(value.ledger_id, ''),
    status: readString(value.status, ''),
    timestamp: readString(value.timestamp, ''),
    actor: readString(value.actor, ''),
    surface: readString(value.surface, ''),
    errorSummary: readString(value.error_summary, ''),
  };
}

function coerceBindingReferenceTaskSummary(
  value: Record<string, unknown>,
): SchedulerOperatorBindingReferenceTaskSummary {
  return {
    taskId: readString(value.task_id, ''),
    title: readString(value.title, ''),
    ok: readBoolean(value.ok),
    bindingRefCount: readNumber(value.binding_ref_count),
    checkedRefCount: readNumber(value.checked_ref_count),
    errorCount: readNumber(value.error_count),
    bindingRefs: readObjectArray(value.binding_refs).map(coerceBindingReference),
    checkedRefs: readObjectArray(value.checked_refs).map(coerceBindingReference),
    errors: readStringArray(value.errors),
  };
}

function coerceBindingReference(
  value: Record<string, unknown>,
): SchedulerOperatorBindingReference {
  return {
    refKind: readString(value.ref_kind, ''),
    refId: readString(value.ref_id, ''),
    version: readString(value.version, ''),
    path: readString(value.path, ''),
    label: readString(value.label, ''),
  };
}

function coerceSchedulerAuthorizationReadback(
  value: Record<string, unknown>,
): SchedulerAuthorizationReadback {
  return {
    ok: readBoolean(value.ok),
    productType: readString(value.product_type, ''),
    schemaVersion: readString(value.schema_version, ''),
    snapshotPath: readString(value.snapshot_path, ''),
    schedulerEventLogPath: readString(value.scheduler_event_log_path, ''),
    recoveredFromEventLog: readBoolean(value.recovered_from_event_log),
    strictReplay: readBoolean(value.strict_replay),
    taskCount: readNumber(value.task_count),
    editLeaseTaskCount: readNumber(value.edit_lease_task_count),
    lifecycleRecordCount: readNumber(value.lifecycle_record_count),
    lifecycleStateCounts: readNumberRecord(value.lifecycle_state_counts),
    sandboxAuthorizationStateCounts: readNumberRecord(value.sandbox_authorization_state_counts),
    orphanLifecycleRecordCount: readNumber(value.orphan_lifecycle_record_count),
    tasks: readObjectArray(value.tasks).map(coerceSchedulerAuthorizationTaskSummary),
    error: readString(value.error, ''),
  };
}

function coerceSchedulerAuthorizationTaskSummary(
  value: Record<string, unknown>,
): SchedulerAuthorizationTaskSummary {
  return {
    taskId: readString(value.task_id, ''),
    title: readString(value.title, ''),
    state: readString(value.state, 'unknown'),
    agentId: readString(value.agent_id, ''),
    runtimeProvider: readString(value.runtime_provider, ''),
    hasEditLease: readBoolean(value.has_edit_lease),
    leaseId: readString(value.lease_id, ''),
    leaseMode: readString(value.lease_mode, ''),
    allowedArtifacts: readStringArray(value.allowed_artifacts),
    deniedArtifacts: readStringArray(value.denied_artifacts),
    conflictPolicy: readString(value.conflict_policy, ''),
    leaseExpiresAt: readString(value.lease_expires_at, ''),
    lifecycleMissing: readBoolean(value.lifecycle_missing),
    lifecycle: coerceSchedulerAuthorizationLifecycleSummary(readRecord(value.lifecycle)),
    sandboxAuthorization: coerceSchedulerAuthorizationSandboxSummary(readRecord(value.sandbox_authorization)),
  };
}

function coerceSchedulerAuthorizationLifecycleSummary(
  value: Record<string, unknown>,
): SchedulerAuthorizationLifecycleSummary | null {
  if (Object.keys(value).length === 0) {
    return null;
  }
  return {
    leaseId: readString(value.lease_id, ''),
    taskId: readString(value.task_id, ''),
    state: readString(value.state, 'unknown'),
    mode: readString(value.mode, ''),
    allowedArtifacts: readStringArray(value.allowed_artifacts),
    deniedArtifacts: readStringArray(value.denied_artifacts),
    conflictPolicy: readString(value.conflict_policy, ''),
    acquiredAt: readString(value.acquired_at, ''),
    expiresAt: readString(value.expires_at, ''),
    releasedAt: readString(value.released_at, ''),
    reason: readString(value.reason, ''),
    conflictState: readString(value.conflict_state, ''),
    conflictClassification: readString(value.conflict_classification, ''),
  };
}

function coerceSchedulerAuthorizationSandboxSummary(
  value: Record<string, unknown>,
): SchedulerAuthorizationSandboxSummary | null {
  if (Object.keys(value).length === 0) {
    return null;
  }
  return {
    profileId: readString(value.profile_id, ''),
    profileKind: readString(value.profile_kind, ''),
    mountPolicy: readString(value.mount_policy, ''),
    allocationState: readString(value.allocation_state, 'unknown'),
    allocationReason: readString(value.allocation_reason, ''),
    visibleMounts: readStringArray(value.visible_mounts),
    leaseAuthorizationState: readString(value.lease_authorization_state, 'unknown'),
    leaseAuthorizationReason: readString(value.lease_authorization_reason, ''),
  };
}

function summarizeActionPayload(action: string, payload: Record<string, unknown>): string {
  if (action === 'admit') {
    const admissionResult = readNestedWorkflowResult(payload, 'admission_result');
    const taskIds = readStringArray(admissionResult.submitted_task_ids);
    const ledgerId = readString(
      admissionResult.admission_ledger_record_id,
      readString(admissionResult.ledger_record_id, ''),
    );
    return `admitted ${taskIds.length} task(s)${ledgerId ? ` · ledger=${ledgerId}` : ''}`;
  }
  if (action === 'runLoop') {
    const loopResult = readNestedWorkflowResult(payload, 'loop_result');
    const ticks = readNumber(loopResult.tick_count);
    const runs = readNumber(loopResult.total_run_count);
    const stopReason = readString(loopResult.stop_reason, 'unknown');
    return `loop ticks=${ticks} · runs=${runs} · stop=${stopReason}`;
  }
  if (action === 'project') {
    const projectionResult = readNestedWorkflowResult(payload, 'projection_result');
    const eventCount = readNumber(projectionResult.event_count);
    const laneCount = readNumber(projectionResult.lane_count);
    return `projection refreshed · events=${eventCount} · lanes=${laneCount}`;
  }
  if (action === 'cleanupReceipts') {
    const cleanedCount = readStringArray(payload.cleaned_allocation_ids).length;
    const failedCount = readStringArray(payload.failed_allocation_ids).length;
    const skippedCount = readStringArray(payload.skipped_allocation_ids).length;
    const evidenceId = readString(payload.output_evidence_id, '');
    return `cleanup receipts · cleaned=${cleanedCount} · failed=${failedCount} · skipped=${skippedCount}${evidenceId ? ` · evidence=${evidenceId}` : ''}`;
  }
  if (action === 'runSandboxReceiptWorkflow') {
    const mode = readString(payload.workflow_mode, 'unknown');
    const steps = readObjectArray(payload.steps);
    const completed = steps.filter((step) => readString(step.status, '') === 'completed').length;
    const failed = steps.filter((step) => readString(step.status, '') === 'failed').length;
    const paths = readRecord(payload.paths);
    const allocationPath = readString(paths.allocation_evidence_path, '');
    const cleanupPath = readString(paths.cleanup_evidence_path, '');
    return [
      `sandbox receipt workflow · mode=${mode}`,
      `steps=${completed}/${steps.length}`,
      failed ? `failed=${failed}` : '',
      allocationPath ? `allocation=${allocationPath}` : '',
      cleanupPath ? `cleanup=${cleanupPath}` : '',
    ].filter(Boolean).join(' · ');
  }
  if (action === 'operatorDogfoodClosure') {
    const closureSummary = readRecord(payload.closure_summary);
    const authoritySplit = readRecord(payload.authority_split);
    const ok = readBoolean(payload.ok);
    const fixture = readString(closureSummary.fixture, 'unknown');
    const lifecycle = readString(closureSummary.lifecycle_state, 'unknown');
    const evidenceId = readString(closureSummary.loop_evidence_id, '');
    const hostCards = readNumber(closureSummary.host_evidence_card_count);
    const projectionEvents = readNumber(closureSummary.scheduler_projection_event_count);
    const agentTrajectoryMutation = readBoolean(authoritySplit.local_work_trajectory_mutated);
    return [
      `dogfood closure ${ok ? 'ok' : 'not ok'}`,
      `fixture=${fixture}`,
      `lifecycle=${lifecycle}`,
      evidenceId ? `evidence=${evidenceId}` : '',
      `host cards=${hostCards}`,
      `projection events=${projectionEvents}`,
      `local trajectory mutated=${agentTrajectoryMutation}`,
    ].filter(Boolean).join(' · ');
  }
  return 'action completed';
}

function readNestedWorkflowResult(
  payload: Record<string, unknown>,
  key: string,
): Record<string, unknown> {
  const nested = readRecord(payload[key]);
  return Object.keys(nested).length > 0 ? nested : payload;
}

function parseJsonObject(stdout: string): Record<string, unknown> {
  const payload = JSON.parse(stdout);
  if (!isRecord(payload)) {
    throw new Error('Expected command output to be a JSON object.');
  }
  return payload;
}

function parseJsonObjectOrNull(stdout: string): Record<string, unknown> | null {
  if (!stdout.trim()) {
    return null;
  }
  try {
    return parseJsonObject(stdout);
  } catch {
    return null;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function readRecord(value: unknown): Record<string, unknown> {
  return isRecord(value) ? value : {};
}

function readObjectArray(value: unknown): Record<string, unknown>[] {
  return Array.isArray(value) ? value.filter(isRecord) : [];
}

function readString(value: unknown, fallback: string): string {
  return typeof value === 'string' ? value : fallback;
}

function readStringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : [];
}

function readNumber(value: unknown): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : 0;
}

function readBoolean(value: unknown): boolean {
  return typeof value === 'boolean' ? value : false;
}

function readNumberRecord(value: unknown): Record<string, number> {
  if (!isRecord(value)) {
    return {};
  }
  return Object.fromEntries(
    Object.entries(value).filter((entry): entry is [string, number] => (
      typeof entry[1] === 'number' && Number.isFinite(entry[1])
    )),
  );
}
