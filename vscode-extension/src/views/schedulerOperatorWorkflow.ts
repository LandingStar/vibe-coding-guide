import * as vscode from 'vscode';
import { execFile } from 'child_process';
import { promisify } from 'util';

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
  productType: string;
  taskIds: string[];
  taskCount: number;
  batchId: string;
  admissionStatus: string;
  latestAdmissionStatus: string;
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

export type SchedulerOperatorWorkflowState = {
  exchangeResourceUri: string;
  exchange: SchedulerOperatorExchangeSummary | null;
  exchangeReadError: string | null;
  scheduler: SchedulerOperatorSchedulerSummary | null;
  schedulerReadError: string | null;
  paths: SchedulerOperatorPaths;
  lastAction: SchedulerOperatorLastAction;
};

export type SchedulerOperatorAction =
  | { kind: 'admit'; artifactId: string; version: string }
  | { kind: 'runLoop' }
  | { kind: 'project' };

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
  try {
    const raw = await readResourceJson(options, EXCHANGE_ARTIFACTS_BUNDLE_RESOURCE_URI);
    return {
      exchangeResourceUri: EXCHANGE_ARTIFACTS_BUNDLE_RESOURCE_URI,
      exchange: coerceExchangeSummary(raw),
      exchangeReadError: null,
      scheduler: schedulerReadback.scheduler,
      schedulerReadError: schedulerReadback.schedulerReadError,
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
  const args = schedulerActionArgs(options.action);
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

function schedulerActionArgs(action: SchedulerOperatorAction): string[] {
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
    'vscode-scheduler-operator',
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
    const evidenceId = `vscode-operator-${Date.now()}`;
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
  return [
    ...baseArgs,
    '--refresh-projection',
    '--guide-context',
    'vscode-scheduler-operator',
  ];
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
      productType: readString(candidate.product_type, 'unknown'),
      taskIds: readStringArray(candidate.task_ids),
      taskCount: readNumber(candidate.task_count),
      batchId: readString(candidate.batch_id, ''),
      admissionStatus: readString(admissionState.status, 'unknown'),
      latestAdmissionStatus: readString(admissionState.latest_status, ''),
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
