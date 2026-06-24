import { build } from 'esbuild';
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDir = dirname(fileURLToPath(import.meta.url));
const extensionRoot = resolve(scriptDir, '..');
const repoRoot = resolve(extensionRoot, '..');
const outputDir = resolve(repoRoot, 'output/playwright/host-ux-worker-patch-review-binding');
const entryPath = join(outputDir, 'fixture-entry.ts');
const bundlePath = join(outputDir, 'fixture-entry.cjs');
const htmlPath = join(outputDir, 'worker-patch-review-fixture.html');
const previewModulePath = join(extensionRoot, 'src/views/progressGraphPreviewHtml.ts').replace(/\\/g, '/');

mkdirSync(outputDir, { recursive: true });
writeFileSync(entryPath, `
import { writeFileSync } from 'node:fs';
import { buildProgressGraphPreviewHtml, type ProgressGraphPreviewState } from ${JSON.stringify(previewModulePath)};

const state: ProgressGraphPreviewState = {
  artifactPath: '.codex/progress-graph/latest.html',
  artifactModifiedAt: '2026-06-25T08:00:00.000Z',
  artifactModifiedTimeMs: 1,
  controlSnapshotPath: '.codex/progress-graph/control-snapshot.json',
  controlSnapshotExists: false,
  controlSnapshot: null,
  controlSnapshotError: null,
  historyArtifactPath: '.codex/progress-graph/latest.json',
  historyArtifactExists: false,
  trajectoryArtifactPath: '.codex/progress-graph/local-work-trajectory.json',
  trajectoryArtifactExists: false,
  schedulerTrajectoryArtifactPath: '.codex/progress-graph/scheduler-work-trajectory.json',
  schedulerTrajectoryArtifactExists: false,
  previewExists: false,
  previewHtml: null,
  localWorkTrajectory: null,
  localWorkTrajectoryError: null,
  schedulerWorkTrajectory: null,
  schedulerWorkTrajectoryError: null,
  hostEvidencePresentationResourceUri: 'dbc://host-evidence/presentation',
  hostEvidencePresentation: {
    generatedAt: '2026-06-25T08:00:00.000Z',
    projectRoot: 'E:/workspace/example',
    evidenceDir: 'E:/workspace/example/.codex/scheduler/evidence',
    status: 'empty',
    cardCount: 0,
    errorCount: 0,
    cards: [],
    errorRows: [],
    emptyMessage: 'No host scheduler run evidence has been recorded.',
  },
  hostEvidencePresentationError: null,
  schedulerOperatorWorkflow: {
    exchangeResourceUri: 'dbc://exchange-artifacts/bundle',
    exchange: {
      exists: true,
      storePath: 'E:/workspace/example/.codex/orchestration/exchange-artifacts.json',
      artifactCount: 2,
      versionCount: 2,
      admissionCandidateCount: 0,
      admissionLedgerPath: 'E:/workspace/example/.codex/orchestration/exchange-artifact-admissions.json',
      admissionLedgerExists: false,
      candidates: [],
      errors: [],
    },
    exchangeReadError: null,
    workerPatchReview: {
      resourceUri: 'dbc://agent-exchange/action-candidates',
      exists: true,
      candidateCount: 2,
      candidates: [
        {
          candidateId: 'task-client:patch-review@v1:merge',
          artifactId: 'task-client:patch-review',
          version: 'v1',
          source: 'task-client:patch-review@v1',
          lifecycleState: 'proposed',
          confidence: 'high',
          kind: 'proposal',
          intent: 'request_merge',
          producer: 'agent:client-worker',
          audience: ['agent:guide'],
          taskId: 'task-client',
          laneId: 'lane:client',
          workerAgentId: 'agent:client-worker',
          runtimeProvider: 'codex',
          sandboxProvider: 'git-worktree',
          sandboxAllocationId: 'allocation-client',
          patchState: 'has_patch',
          changedPaths: ['client/app.js', 'client/maze.css'],
          relationTargets: ['scheduler_task:task-client'],
          reasons: ['intent:request_merge', 'relation:merges_into'],
          redactionRequired: false,
        },
        {
          candidateId: 'task-server:patch-review@v1:merge',
          artifactId: 'task-server:patch-review',
          version: 'v1',
          source: 'task-server:patch-review@v1',
          lifecycleState: 'proposed',
          confidence: 'high',
          kind: 'proposal',
          intent: 'request_merge',
          producer: 'agent:server-worker',
          audience: ['agent:guide'],
          taskId: 'task-server',
          laneId: 'lane:server',
          workerAgentId: 'agent:server-worker',
          runtimeProvider: 'codex',
          sandboxProvider: 'git-worktree',
          sandboxAllocationId: 'allocation-server',
          patchState: 'has_patch',
          changedPaths: ['server/app.py'],
          relationTargets: ['scheduler_task:task-server'],
          reasons: ['intent:request_merge', 'relation:merges_into'],
          redactionRequired: false,
        },
      ],
      errors: [],
    },
    workerPatchReviewReadError: null,
    scheduler: {
      snapshotExists: true,
      eventLogExists: true,
      taskCount: 2,
      dependencyCount: 1,
      runRecordCount: 2,
      schedulerEventCount: 8,
      taskStateCounts: { complete: 2 },
      schedulerEventKindCounts: { task_completed: 2 },
    },
    schedulerReadError: null,
    authorizationReadback: null,
    authorizationReadError: null,
    paths: {
      artifactStorePath: 'E:/workspace/example/.codex/orchestration/exchange-artifacts.json',
      admissionLedgerPath: 'E:/workspace/example/.codex/orchestration/exchange-artifact-admissions.json',
      schedulerSnapshotPath: 'E:/workspace/example/.codex/scheduler/scheduler-state.json',
      schedulerEventLogPath: 'E:/workspace/example/.codex/scheduler/scheduler-events.jsonl',
      schedulerProjectionPath: 'E:/workspace/example/.codex/progress-graph/scheduler-work-trajectory.json',
    },
    lastAction: {
      action: 'workerPatchPreflight',
      status: 'succeeded',
      startedAt: '2026-06-25T08:01:00.000Z',
      completedAt: '2026-06-25T08:01:01.000Z',
      summary: 'worker patch composition preflight ok · steps=2 · collisions=0',
      stdout: '{"ok":true}',
      stderr: '',
      payload: { ok: true },
    },
  },
  v2GraphPayload: null,
  v2GraphPayloadError: null,
  v2GraphScriptUri: null,
  v2GraphWorkerUri: null,
  v2GraphAutoShake: true,
  localWorkTrajectoryScriptUri: null,
  localWorkTrajectoryStyleUri: null,
  freshness: 'fresh',
  freshnessLabel: 'Fresh',
  freshnessMessage: 'Worker patch review fixture.',
  isRefreshRunning: false,
  lastLoadedAt: '2026-06-25T08:00:00.000Z',
  lastRefreshStartedAt: null,
  lastRefreshCompletedAt: null,
  lastRefreshError: null,
};

const html = buildProgressGraphPreviewHtml(state).replace(
  ':root {\\n      color-scheme: light dark;',
  ':root {\\n      color-scheme: light dark;\\n      --vscode-editor-foreground: #20252b;\\n      --vscode-editor-background: #f5f7fb;\\n      --vscode-font-family: Inter, Segoe UI, sans-serif;\\n      --vscode-panel-border: rgba(23, 34, 45, 0.14);\\n      --vscode-sideBar-background: #edf2f7;\\n      --vscode-testing-iconPassed: #2f9f73;\\n      --vscode-testing-iconQueued: #a86900;\\n      --vscode-testing-iconFailed: #c84636;\\n      --vscode-button-background: #256f91;\\n      --vscode-button-foreground: #ffffff;\\n      --vscode-button-hoverBackground: #1f5f7c;\\n      --vscode-button-secondaryBackground: #e3e9ef;\\n      --vscode-button-secondaryForeground: #1d2833;\\n      --vscode-button-secondaryHoverBackground: #d5dee8;'
);
writeFileSync(${JSON.stringify(htmlPath)}, html, 'utf8');
`);

await build({
  entryPoints: [entryPath],
  bundle: true,
  outfile: bundlePath,
  platform: 'node',
  format: 'cjs',
  target: 'node20',
  external: ['vscode'],
});

await import(`file:///${bundlePath.replace(/\\/g, '/')}`);
console.log(htmlPath);
