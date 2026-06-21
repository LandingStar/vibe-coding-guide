import assert from 'node:assert/strict';
import test from 'node:test';

import {
  buildProgressGraphPreviewHtml,
  coerceControlSnapshot,
  coerceHostEvidencePresentation,
  type ProgressGraphPreviewState,
  type ProgressGraphPreviewV2PoCPayload,
} from '../views/progressGraphPreviewHtml.js';

function buildBaseState(overrides: Partial<ProgressGraphPreviewState> = {}): ProgressGraphPreviewState {
  return {
    artifactPath: '.codex/progress-graph/latest.html',
    artifactModifiedAt: '2026-05-06T10:00:00.000Z',
    artifactModifiedTimeMs: 1,
    controlSnapshotPath: '.codex/progress-graph/control-snapshot.json',
    controlSnapshotExists: true,
    controlSnapshot: null,
    controlSnapshotError: null,
    historyArtifactPath: '.codex/progress-graph/latest.json',
    historyArtifactExists: true,
    previewExists: true,
    previewHtml: '<!DOCTYPE html><html><head></head><body></body></html>',
    v2GraphPayload: null,
    v2GraphPayloadError: null,
    trajectoryArtifactPath: '.codex/progress-graph/local-work-trajectory.json',
    trajectoryArtifactExists: false,
    schedulerTrajectoryArtifactPath: '.codex/progress-graph/scheduler-work-trajectory.json',
    schedulerTrajectoryArtifactExists: false,
    localWorkTrajectory: null,
    localWorkTrajectoryError: null,
    schedulerWorkTrajectory: null,
    schedulerWorkTrajectoryError: null,
    hostEvidencePresentationResourceUri: 'dbc://host-evidence/presentation',
    hostEvidencePresentation: {
      generatedAt: null,
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
        exists: false,
        storePath: 'E:/workspace/example/.codex/orchestration/exchange-artifacts.json',
        artifactCount: 0,
        versionCount: 0,
        admissionCandidateCount: 0,
        admissionLedgerPath: 'E:/workspace/example/.codex/orchestration/exchange-artifact-admissions.json',
        admissionLedgerExists: false,
        candidates: [],
        errors: [],
      },
      exchangeReadError: null,
      scheduler: null,
      schedulerReadError: 'scheduler snapshot is not available',
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
        action: '',
        status: 'idle',
        startedAt: null,
        completedAt: null,
        summary: '',
        stdout: '',
        stderr: '',
        payload: null,
      },
    },
    v2GraphScriptUri: null,
    v2GraphWorkerUri: null,
    v2GraphAutoShake: true,
    localWorkTrajectoryScriptUri: null,
    localWorkTrajectoryStyleUri: null,
    freshness: 'fresh',
    freshnessLabel: 'Fresh',
    freshnessMessage: '当前面板与最新已知 artifact 一致。',
    isRefreshRunning: false,
    lastLoadedAt: '2026-05-06T10:05:00.000Z',
    lastRefreshStartedAt: null,
    lastRefreshCompletedAt: null,
    lastRefreshError: null,
    ...overrides,
  };
}

test('buildProgressGraphPreviewHtml embeds available control snapshot overlay for bound runtime data', () => {
  const snapshot = coerceControlSnapshot({
    snapshot_version: 'v1alpha1',
    snapshot_kind: 'orchestration-bridge-compact',
    generated_at: '2026-05-06T10:03:00.000Z',
    summary: {
      open_work_item_count: 1,
      blocked_work_item_count: 0,
      waiting_external_resolution_count: 0,
      active_group_item_count: 2,
      unbound_group_item_count: 0,
    },
    work_items: [
      {
        work_item_id: 'doc-loop-work::interactive-control-surface',
        lifecycle_state: 'dispatching',
        rollup_surface_kind: 'planning-gate',
        rollup_surface_state: 'active',
        rollup_writeback_disposition: 'pending',
        dominant_group_item_ids: ['group::todo:024'],
        open_group_item_count: 1,
        source_trace_id: 'trace-001',
      },
    ],
    group_items: [
      {
        group_item_id: 'group::todo:024',
        work_item_id: 'doc-loop-work::interactive-control-surface',
        child_task_ids: [],
        lifecycle_state: 'in_progress',
        governance_surface_kind: 'checkpoint-todo',
        governance_surface_state: 'open',
        current_gate_state: 'active',
        writeback_disposition: 'pending',
        delivery_surface_kind: 'doc-loop',
        delivery_state: 'ready',
        open_items: ['todo:024'],
        authoritative_refs: ['.codex/checkpoints/latest.md'],
      },
    ],
    bindings: [
      {
        binding_id: 'binding::checkpoint-current::todo:024',
        binding_kind: 'graph-target-binding',
        graph_id: 'checkpoint-current',
        graph_target_id: 'todo:024',
        graph_target_key: 'checkpoint-current::todo:024',
        work_item_ids: ['doc-loop-work::interactive-control-surface'],
        group_item_ids: ['group::todo:024'],
        binding_reason: 'checkpoint open todo',
      },
    ],
  });
  const previewHtml = '<!DOCTYPE html><html><head></head><body>'
    + '<section class="graph-section" data-graph-id="checkpoint-current">'
    + '<svg>'
    + '<path class="edge interactive-edge edge-workflow" data-source-id="todo:024" data-target-id="todo:025"></path>'
    + '<g class="interactive-node" data-node-id="todo:024"><rect class="node-shape node-in-progress"></rect></g>'
    + '<g class="interactive-node" data-node-id="todo:025"><rect class="node-shape node-pending"></rect></g>'
    + '</svg>'
    + '<button class="ready-item" data-display-id="todo:024">ready</button>'
    + '<script type="application/json" data-role="graph-payload">'
    + JSON.stringify({
      graphId: 'checkpoint-current',
      nodes: {
        'todo:024': {
          memberIds: ['todo:024'],
        },
      },
    })
    + '</script>'
    + '</section>'
    + '</body></html>';
  const html = buildProgressGraphPreviewHtml(buildBaseState({
    controlSnapshot: snapshot,
    previewHtml,
  }));

  assert.match(html, /data-control-snapshot-status="available"/);
  assert.match(html, /Control Summary Rail/);
  assert.match(html, /Open Work Items/);
  assert.match(html, />1<\/div>/);
  assert.match(html, /pgHostControlSnapshotPayload/);
  assert.match(html, /binding::checkpoint-current::todo:024/);
  assert.match(html, /选择图中的节点或 ready item 后，这里会显示对应的 runtime binding 摘要/);
  assert.match(html, /正在根据 bindings 和当前 graph payload 计算 unbound runtime rows/);
  assert.match(html, /const boundRowsByDisplayKey = new Map\(\)/);
  assert.match(html, /graph-section\[data-pg-graph-mode="obsidianish"\] \.interactive-node \.node-shape/);
  assert.match(html, /section\.dataset\.pgGraphMode = 'obsidianish';/);
  assert.match(html, /group\.classList\.toggle\('pg-runtime-bound', hasRuntimeBinding\);/);
  assert.match(html, /const relatedNodeIds = new Set\(\);/);
  assert.match(html, /edge\.classList\.toggle\('pg-is-selected', touchesSelected\);/);
  assert.match(html, /const ensureHighlightMarkers = \(section\) =>/);
  assert.match(html, /edge\.setAttribute\('marker-end', highlightedId \? 'url\(#' \+ highlightedId \+ '\)' : originalMarkerEnd\);/);
  assert.match(html, /group\.addEventListener\('mouseenter', \(\) => setPreviewTarget\(graphId, displayId\)\);/);
  assert.match(html, /item\.addEventListener\('mouseleave', \(\) => setPreviewTarget\('', ''\)\);/);
  assert.match(html, /renderUnboundPanel\(\);/);
});

test('buildProgressGraphPreviewHtml renders empty host evidence presentation state', () => {
  const html = buildProgressGraphPreviewHtml(buildBaseState());

  assert.match(html, /id="pgHostSchedulerOperatorPanel"/);
  assert.match(html, /Scheduler Operator/);
  assert.match(html, /dbc:\/\/exchange-artifacts\/bundle/);
  assert.match(html, /id="pgHostSchedulerAuthorizationReadback"/);
  assert.match(html, /authorization unavailable/);
  assert.match(html, /id="pgHostSandboxReceiptWorkflow"/);
  assert.match(html, /Sandbox Receipt Workflow/);
  assert.match(html, /scheduler sandbox-receipt-workflow/);
  assert.match(html, /id="pgHostSandboxWorkflowMode"/);
  assert.match(html, /value="run-once" selected/);
  assert.match(html, /value="daemon-loop"/);
  assert.match(html, /id="pgHostSandboxWorkflowMaxTicks"/);
  assert.match(html, /id="pgHostSandboxWorkflowMaxRunsPerTick"/);
  assert.match(html, /id="pgHostSandboxWorkflowMaxRuntimeFailures"/);
  assert.match(html, /daemon-loop uses bounded fake runtime settings below/);
  assert.match(html, /id="pgHostSandboxWorkflowWorkspaceRoot"/);
  assert.match(html, /id="pgHostSandboxWorkflowSandboxRoot"/);
  assert.match(html, /id="pgHostSandboxWorkflowAllocationEvidenceId"/);
  assert.match(html, /id="pgHostSandboxWorkflowAllocationEvidencePath"/);
  assert.match(html, /id="pgHostSandboxWorkflowCleanup"/);
  assert.match(html, /id="pgHostSandboxWorkflowCleanupDetails"/);
  assert.match(html, /data-pg-scheduler-action="runSandboxReceiptWorkflow"/);
  assert.match(html, /id="pgHostSchedulerCleanupReceipts"/);
  assert.match(html, /Sandbox Receipt Cleanup/);
  assert.match(html, /id="pgHostCleanupEvidencePath"/);
  assert.match(html, /placeholder="\.codex\/scheduler\/evidence\/allocation-receipts\.json"/);
  assert.match(html, /id="pgHostCleanupConfirm"/);
  assert.match(html, /data-pg-scheduler-action="cleanupReceipts"/);
  assert.match(html, /scheduler cleanup-receipts/);
  assert.match(html, /No sandbox receipt evidence candidates are currently visible in Host Evidence/);
  assert.match(html, /No scheduler-admission candidates are currently present/);
  assert.match(html, /id="pgHostEvidencePanel"/);
  assert.match(html, /Host Evidence/);
  assert.match(html, /dbc:\/\/host-evidence\/presentation/);
  assert.match(html, /data-pg-host-evidence-status="empty"/);
  assert.match(html, /cards 0/);
  assert.match(html, /errors 0/);
  assert.match(html, /No host scheduler run evidence has been recorded/);
});

test('buildProgressGraphPreviewHtml renders scheduler operator candidates and explicit action buttons', () => {
  const html = buildProgressGraphPreviewHtml(buildBaseState({
    schedulerOperatorWorkflow: {
      ...buildBaseState().schedulerOperatorWorkflow,
      exchange: {
        exists: true,
        storePath: 'E:/workspace/example/.codex/orchestration/exchange-artifacts.json',
        artifactCount: 1,
        versionCount: 1,
        admissionCandidateCount: 1,
        admissionLedgerPath: 'E:/workspace/example/.codex/orchestration/exchange-artifact-admissions.json',
        admissionLedgerExists: true,
        candidates: [
          {
            artifactId: 'submission:maze',
            version: 'v1',
            productType: 'scheduler_task_batch_submission',
            taskIds: ['task-server', 'task-client'],
            taskCount: 2,
            batchId: 'batch-maze',
            admissionStatus: 'not_admitted',
            latestAdmissionStatus: '',
          },
        ],
        errors: [],
      },
      scheduler: {
        snapshotExists: true,
        eventLogExists: true,
        taskCount: 2,
        dependencyCount: 1,
        runRecordCount: 2,
        schedulerEventCount: 9,
        taskStateCounts: { complete: 2 },
        schedulerEventKindCounts: { task_completed: 2 },
      },
      schedulerReadError: null,
      lastAction: {
        action: 'runLoop',
        status: 'succeeded',
        startedAt: '2026-06-19T10:00:00.000Z',
        completedAt: '2026-06-19T10:00:01.000Z',
        summary: 'loop ticks=2 · runs=2 · stop=no_ready_tasks',
        stdout: '{"ok":true}',
        stderr: '',
        payload: { ok: true },
      },
    },
  }));

  assert.match(html, /Admission candidates/);
  assert.match(html, /submission:maze@v1/);
  assert.match(html, /scheduler_task_batch_submission/);
  assert.match(html, /task-server, task-client/);
  assert.match(html, /data-pg-scheduler-action="admit"/);
  assert.match(html, /data-pg-artifact-id="submission:maze"/);
  assert.match(html, /data-pg-version="v1"/);
  assert.match(html, /data-pg-scheduler-action="runLoop"/);
  assert.match(html, /data-pg-scheduler-action="project"/);
  assert.match(html, /data-pg-scheduler-action="cleanupReceipts"/);
  assert.match(html, /data-pg-scheduler-action="runSandboxReceiptWorkflow"/);
  assert.match(html, /const workflowPayload = \{/);
  assert.match(html, /const workflowMode = readSelectValue\('pgHostSandboxWorkflowMode'\) \|\| 'run-once'/);
  assert.match(html, /workflowMode,/);
  assert.match(html, /workspaceRoot: readTextInput\('pgHostSandboxWorkflowWorkspaceRoot'\)/);
  assert.match(html, /gitWorktreeSandboxRoot: readTextInput\('pgHostSandboxWorkflowSandboxRoot'\)/);
  assert.match(html, /allocationEvidenceId: readTextInput\('pgHostSandboxWorkflowAllocationEvidenceId'\)/);
  assert.match(html, /maxTicks: workflowMode === 'daemon-loop' \? readTextInput\('pgHostSandboxWorkflowMaxTicks'\) : ''/);
  assert.match(html, /maxRunsPerTick: workflowMode === 'daemon-loop' \? readTextInput\('pgHostSandboxWorkflowMaxRunsPerTick'\) : ''/);
  assert.match(html, /maxRuntimeFailures: workflowMode === 'daemon-loop' \? readTextInput\('pgHostSandboxWorkflowMaxRuntimeFailures'\) : ''/);
  assert.match(html, /cleanupEvidencePath: workflowCleanup \? readTextInput\('pgHostSandboxWorkflowCleanupEvidencePath'\) : ''/);
  assert.match(html, /action === 'runSandboxReceiptWorkflow'/);
  assert.match(html, /cleanupDetails instanceof HTMLDetailsElement/);
  assert.match(html, /cleanupDetails\.open = true/);
  assert.match(html, /workflowMode === 'daemon-loop'/);
  assert.match(html, /isPositiveIntegerText\(input\.value\.trim\(\)\)/);
  assert.match(html, /focusFirstMissingInput\(missing\)/);
  assert.match(html, /querySelectorAll\('\[data-pg-cleanup-evidence-select\]'\)/);
  assert.match(html, /target\.dataset\.pgCleanupEvidencePath \|\| ''/);
  assert.match(html, /evidencePathInput\.dispatchEvent\(new Event\('input', \{ bubbles: true \}\)\)/);
  assert.match(html, /const evidencePath = evidencePathInput instanceof HTMLInputElement \? evidencePathInput\.value\.trim\(\) : ''/);
  assert.match(html, /const cleanupConfirmed = cleanupConfirmInput instanceof HTMLInputElement \? cleanupConfirmInput\.checked : false/);
  assert.match(html, /action === 'cleanupReceipts' && \(!evidencePath \|\| !cleanupConfirmed\)/);
  assert.match(html, /evidencePath,/);
  assert.match(html, /confirmed: cleanupConfirmed/);
  assert.match(html, /loop ticks=2/);
  assert.match(html, /Scheduler events/);
  assert.match(html, />9<\/div>/);
  assert.match(html, /vscode\.postMessage\(\{[\s\S]*command: 'schedulerOperatorAction'/);
});

test('buildProgressGraphPreviewHtml renders scheduler authorization readback task diagnostics', () => {
  const html = buildProgressGraphPreviewHtml(buildBaseState({
    schedulerOperatorWorkflow: {
      ...buildBaseState().schedulerOperatorWorkflow,
      scheduler: {
        snapshotExists: true,
        eventLogExists: true,
        taskCount: 1,
        dependencyCount: 0,
        runRecordCount: 0,
        schedulerEventCount: 3,
        taskStateCounts: { queued: 1 },
        schedulerEventKindCounts: { task_submitted: 1 },
      },
      schedulerReadError: null,
      authorizationReadback: {
        ok: true,
        productType: 'scheduler_authorization_readback',
        schemaVersion: '1',
        snapshotPath: 'E:/workspace/example/.codex/scheduler/scheduler-state.json',
        schedulerEventLogPath: 'E:/workspace/example/.codex/scheduler/scheduler-events.jsonl',
        recoveredFromEventLog: true,
        strictReplay: true,
        taskCount: 1,
        editLeaseTaskCount: 1,
        lifecycleRecordCount: 1,
        lifecycleStateCounts: { acquired: 1 },
        sandboxAuthorizationStateCounts: { allocated: 1 },
        orphanLifecycleRecordCount: 0,
        error: '',
        tasks: [
          {
            taskId: 'task-api',
            title: 'Implement API',
            state: 'queued',
            agentId: 'agent-api',
            runtimeProvider: 'fake',
            hasEditLease: true,
            leaseId: 'lease-api',
            leaseMode: 'exclusive',
            allowedArtifacts: ['src/api.py'],
            deniedArtifacts: [],
            conflictPolicy: 'block',
            leaseExpiresAt: '',
            lifecycleMissing: false,
            lifecycle: {
              leaseId: 'lease-api',
              taskId: 'task-api',
              state: 'acquired',
              mode: 'exclusive',
              allowedArtifacts: ['src/api.py'],
              deniedArtifacts: [],
              conflictPolicy: 'block',
              acquiredAt: '2026-06-21T01:00:00.000Z',
              expiresAt: '',
              releasedAt: '',
              reason: '',
              conflictState: 'compatible',
              conflictClassification: 'no_conflict',
            },
            sandboxAuthorization: {
              profileId: 'shared-process',
              profileKind: 'shared-process',
              mountPolicy: 'workspace',
              allocationState: 'allocated',
              allocationReason: '',
              visibleMounts: ['src/api.py'],
              leaseAuthorizationState: 'authorized',
              leaseAuthorizationReason: 'acquired lifecycle authorizes visible mounts',
            },
          },
        ],
      },
      authorizationReadError: null,
    },
  }));

  assert.match(html, /data-pg-authorization-readback-status="ok"/);
  assert.match(html, /Authorization Readback/);
  assert.match(html, /read-only schedulerAuthorizationReadback/);
  assert.match(html, /Edit lease tasks/);
  assert.match(html, />1<\/div>/);
  assert.match(html, /Lifecycle states/);
  assert.match(html, /acquired: 1/);
  assert.match(html, /Sandbox authorization states/);
  assert.match(html, /allocated: 1/);
  assert.match(html, /data-pg-authorization-task-id="task-api"/);
  assert.match(html, /Implement API/);
  assert.match(html, /lease=lease-api · exclusive/);
  assert.match(html, /allowed=src\/api\.py/);
  assert.match(html, /lifecycle acquired/);
  assert.match(html, /sandbox authorized/);
});

test('buildProgressGraphPreviewHtml renders scheduler authorization readback errors without mutation controls', () => {
  const html = buildProgressGraphPreviewHtml(buildBaseState({
    schedulerOperatorWorkflow: {
      ...buildBaseState().schedulerOperatorWorkflow,
      authorizationReadback: {
        ok: false,
        productType: '',
        schemaVersion: '',
        snapshotPath: 'E:/workspace/example/.codex/scheduler/scheduler-state.json',
        schedulerEventLogPath: '',
        recoveredFromEventLog: false,
        strictReplay: true,
        taskCount: 0,
        editLeaseTaskCount: 0,
        lifecycleRecordCount: 0,
        lifecycleStateCounts: {},
        sandboxAuthorizationStateCounts: {},
        orphanLifecycleRecordCount: 0,
        tasks: [],
        error: 'scheduler state snapshot does not exist',
      },
      authorizationReadError: null,
    },
  }));

  assert.match(html, /data-pg-authorization-readback-status="failed"/);
  assert.match(html, /authorization unavailable/);
  assert.match(html, /scheduler state snapshot does not exist/);
  assert.doesNotMatch(html, /data-pg-scheduler-action="authorize"/);
  assert.doesNotMatch(html, /data-pg-scheduler-action="acquireLease"/);
});

test('buildProgressGraphPreviewHtml renders host evidence cards from presentation payload', () => {
  const presentation = coerceHostEvidencePresentation({
    generated_at: '2026-06-19T09:00:00.000Z',
    project_root: 'E:/workspace/example',
    evidence_dir: 'E:/workspace/example/.codex/scheduler/evidence',
    status: 'ok',
    card_count: 1,
    error_count: 0,
    empty_message: '',
    cards: [
      {
        id: 'host-loop-projection-workflow',
        title: 'Scheduler loop evidence host-loop-projection-workflow',
        subtitle: 'host-loop-projection-workflow · no_ready_tasks · 3 run(s)',
        status: 'completed',
        severity: 'info',
        timestamp: '2026-06-19T09:00:00.000Z',
        runtime_providers: ['fake'],
        host_surface: 'host-loop-projection-workflow',
        invocation_id: 'invocation-001',
        requested_by: 'operator-or-host',
        stop_reason: 'no_ready_tasks',
        stop_detail: 'queue drained',
        run_count: 3,
        output_count: 0,
        permission_review_count: 0,
        key_facts: [
          { label: 'Scheduler projection path', value: '.codex/progress-graph/scheduler-work-trajectory.json' },
          { label: 'Scheduler projection role', value: 'read-only-view' },
        ],
        refs: [
          { label: 'Evidence', target: '.codex/scheduler/evidence/host-loop-projection-workflow.json', ref_kind: 'path' },
          { label: 'Scheduler projection', target: '.codex/progress-graph/scheduler-work-trajectory.json', ref_kind: 'path' },
        ],
        authority_clues: [
          { label: 'Scheduler projection refreshed', value: 'true' },
          { label: 'Local trajectory mutated', value: 'false' },
        ],
        metadata: {
          evidence_product_type: 'scheduler_loop_evidence',
        },
      },
    ],
    error_rows: [],
  });

  const html = buildProgressGraphPreviewHtml(buildBaseState({
    hostEvidencePresentation: presentation,
  }));

  assert.match(html, /data-pg-host-evidence-status="ok"/);
  assert.match(html, /cards 1/);
  assert.match(html, /Scheduler loop evidence host-loop-projection-workflow/);
  assert.match(html, /host-loop-projection-workflow/);
  assert.match(html, /Runtime providers/);
  assert.match(html, /fake/);
  assert.match(html, /Host surface/);
  assert.match(html, /invocation-001/);
  assert.match(html, /no_ready_tasks/);
  assert.match(html, /queue drained/);
  assert.match(html, /Scheduler projection path/);
  assert.match(html, /scheduler-work-trajectory\.json/);
  assert.match(html, /Authority clues/);
  assert.match(html, /Scheduler projection refreshed: true/);
  assert.match(html, /Local trajectory mutated: false/);
});

test('buildProgressGraphPreviewHtml renders cleanup receipt evidence cards', () => {
  const presentation = coerceHostEvidencePresentation({
    generated_at: '2026-06-21T07:15:00.000Z',
    project_root: 'E:/workspace/example',
    evidence_dir: 'E:/workspace/example/.codex/scheduler/evidence',
    status: 'ok',
    card_count: 1,
    error_count: 0,
    empty_message: '',
    cards: [
      {
        id: 'cleanup',
        title: 'Sandbox cleanup evidence cleanup',
        subtitle: 'mcp:schedulerCleanupReceipts · 1 allocation(s) · cleanup settled',
        status: 'completed',
        severity: 'info',
        timestamp: '2026-06-21T07:10:00+08:00',
        runtime_providers: ['git-worktree'],
        host_surface: 'mcp:schedulerCleanupReceipts',
        invocation_id: 'cleanup',
        requested_by: 'operator-or-host',
        stop_reason: 'cleanup_settled',
        stop_detail: '1 git-worktree allocation cleanup receipt(s) are completed.',
        run_count: 0,
        output_count: 0,
        permission_review_count: 0,
        key_facts: [
          { label: 'Evidence product', value: 'sandbox_allocation_receipt_evidence' },
          { label: 'Allocations', value: '1' },
          { label: 'Git worktrees', value: '1' },
          { label: 'Cleanup required', value: '0' },
          { label: 'Cleanup completed', value: '1' },
          { label: 'Cleanup executed', value: 'true' },
          { label: 'Source evidence id', value: 'allocation' },
        ],
        refs: [
          { label: 'Evidence', target: '.codex/scheduler/evidence/cleanup.json', ref_kind: 'path' },
          { label: 'Source evidence', target: '.codex/scheduler/evidence/allocation.json', ref_kind: 'path' },
          { label: 'Worktree task-1', target: 'E:/workspace/sandboxes/task-1-worktree', ref_kind: 'path' },
        ],
        authority_clues: [
          { label: 'Cleanup executed', value: 'true' },
          { label: 'Local trajectory mutated', value: 'false' },
        ],
        metadata: {
          evidence_product_type: 'sandbox_allocation_receipt_evidence',
          cleanup_state_counts: { completed: 1 },
        },
      },
    ],
    error_rows: [],
  });

  const html = buildProgressGraphPreviewHtml(buildBaseState({
    hostEvidencePresentation: presentation,
  }));

  assert.match(html, /Sandbox cleanup evidence cleanup/);
  assert.match(html, /git-worktree/);
  assert.match(html, /mcp:schedulerCleanupReceipts/);
  assert.match(html, /sandbox_allocation_receipt_evidence/);
  assert.match(html, /Cleanup completed/);
  assert.match(html, /cleanup_settled/);
  assert.match(html, /Source evidence: \.codex\/scheduler\/evidence\/allocation\.json/);
  assert.match(html, /Worktree task-1: E:\/workspace\/sandboxes\/task-1-worktree/);
  assert.match(html, /Cleanup executed: true/);
  assert.match(html, /Local trajectory mutated: false/);
});

test('buildProgressGraphPreviewHtml renders selectable cleanup receipt evidence candidates', () => {
  const presentation = coerceHostEvidencePresentation({
    generated_at: '2026-06-21T07:15:00.000Z',
    project_root: 'E:/workspace/example',
    evidence_dir: 'E:/workspace/example/.codex/scheduler/evidence',
    status: 'ok',
    card_count: 1,
    error_count: 0,
    empty_message: '',
    cards: [
      {
        id: 'allocation-receipts',
        title: 'Sandbox cleanup evidence allocation-receipts',
        subtitle: 'host-run · 2 allocation(s) · cleanup required',
        status: 'warning',
        severity: 'warning',
        timestamp: '2026-06-21T07:10:00+08:00',
        runtime_providers: ['git-worktree'],
        host_surface: 'host-run',
        invocation_id: 'allocation-receipts',
        requested_by: 'operator-or-host',
        stop_reason: 'cleanup_required',
        stop_detail: '2 git-worktree allocation cleanup receipt(s) still require cleanup.',
        run_count: 0,
        output_count: 0,
        permission_review_count: 0,
        key_facts: [
          { label: 'Evidence product', value: 'sandbox_allocation_receipt_evidence' },
          { label: 'Cleanup required', value: '2' },
        ],
        refs: [
          { label: 'Evidence', target: '.codex/scheduler/evidence/allocation-receipts.json', ref_kind: 'path' },
          { label: 'Source evidence', target: 'E:/workspace/example/.codex/scheduler/evidence/source-allocation.json', ref_kind: 'path' },
          { label: 'Worktree task-1', target: 'E:/workspace/sandboxes/task-1-worktree', ref_kind: 'path' },
        ],
        authority_clues: [
          { label: 'Cleanup executed', value: 'false' },
          { label: 'Local trajectory mutated', value: 'false' },
        ],
        metadata: {
          evidence_product_type: 'sandbox_allocation_receipt_evidence',
          cleanup_state_counts: { required: 2 },
          cleanup_required_allocation_ids: ['allocation-1', 'allocation-2'],
        },
      },
    ],
    error_rows: [],
  });

  const html = buildProgressGraphPreviewHtml(buildBaseState({
    hostEvidencePresentation: presentation,
  }));

  assert.match(html, /Receipt evidence candidates/);
  assert.match(html, /data-pg-cleanup-evidence-candidate="allocation-receipts:1"/);
  assert.match(html, /data-pg-cleanup-evidence-select="true"/);
  assert.match(html, /data-pg-cleanup-evidence-path="\.codex\/scheduler\/evidence\/allocation-receipts\.json"/);
  assert.match(html, /data-pg-cleanup-evidence-path="E:\/workspace\/example\/\.codex\/scheduler\/evidence\/source-allocation\.json"/);
  assert.match(html, /current receipt · cleanup required · \.codex\/scheduler\/evidence\/allocation-receipts\.json/);
  assert.match(html, /source receipt · cleanup required · E:\/workspace\/example\/\.codex\/scheduler\/evidence\/source-allocation\.json/);
  assert.match(html, /required allocation-1, allocation-2/);
  assert.match(html, /id="pgHostSchedulerCleanupOutcomeDiff"/);
  assert.match(html, /data-pg-cleanup-outcome-diff-count="0"/);
  assert.match(html, /No visible source\/cleanup sandbox receipt pair is available for diff/);
  assert.doesNotMatch(html, /data-pg-cleanup-evidence-path="E:\/workspace\/sandboxes\/task-1-worktree"/);
});

test('buildProgressGraphPreviewHtml renders cleanup outcome diff from visible receipt pair', () => {
  const presentation = coerceHostEvidencePresentation({
    generated_at: '2026-06-21T07:25:00.000Z',
    project_root: 'E:/workspace/example',
    evidence_dir: 'E:/workspace/example/.codex/scheduler/evidence',
    status: 'ok',
    card_count: 1,
    error_count: 0,
    empty_message: '',
    cards: [
      {
        id: 'workflow-cleanup',
        title: 'Sandbox cleanup evidence workflow-cleanup',
        subtitle: 'host-sandbox-receipt-workflow · cleanup settled',
        status: 'completed',
        severity: 'info',
        timestamp: '2026-06-21T07:20:00+08:00',
        runtime_providers: ['git-worktree'],
        host_surface: 'host-sandbox-receipt-workflow',
        invocation_id: 'workflow-cleanup',
        requested_by: 'operator-or-host',
        stop_reason: 'cleanup_settled',
        stop_detail: 'cleanup completed for one allocation',
        run_count: 0,
        output_count: 0,
        permission_review_count: 0,
        key_facts: [
          { label: 'Evidence product', value: 'sandbox_allocation_receipt_evidence' },
          { label: 'Cleanup required before', value: '1' },
          { label: 'Cleanup required', value: '0' },
          { label: 'Cleanup completed', value: '1' },
          { label: 'Cleanup failed', value: '0' },
        ],
        refs: [
          { label: 'Cleanup evidence', target: '.codex/scheduler/evidence/workflow-cleanup.json', ref_kind: 'path' },
          { label: 'Source evidence', target: '.codex/scheduler/evidence/workflow-allocation.json', ref_kind: 'path' },
          { label: 'Worktree task-1', target: 'E:/workspace/sandboxes/task-1-worktree', ref_kind: 'path' },
        ],
        authority_clues: [
          { label: 'Cleanup executed', value: 'true' },
          { label: 'Local trajectory mutated', value: 'false' },
        ],
        metadata: {
          evidence_product_type: 'sandbox_allocation_receipt_evidence',
          cleanup_state_counts: { required: 0, completed: 1, failed: 0 },
          cleanup_completed_allocation_ids: ['allocation-1'],
        },
      },
    ],
    error_rows: [],
  });

  const html = buildProgressGraphPreviewHtml(buildBaseState({
    hostEvidencePresentation: presentation,
  }));

  assert.match(html, /Cleanup outcome diff/);
  assert.match(html, /data-pg-cleanup-outcome-diff-count="1"/);
  assert.match(html, /data-pg-cleanup-outcome-diff-row="workflow-cleanup"/);
  assert.match(html, /Before/);
  assert.match(html, /required before: 1/);
  assert.match(html, /After/);
  assert.match(html, /required=0 · completed=1 · failed=0/);
  assert.match(html, /Changed allocations/);
  assert.match(html, /allocation-1/);
  assert.match(html, /Source receipt/);
  assert.match(html, /\.codex\/scheduler\/evidence\/workflow-allocation\.json/);
  assert.match(html, /Cleanup receipt/);
  assert.match(html, /\.codex\/scheduler\/evidence\/workflow-cleanup\.json/);
  assert.doesNotMatch(html, /data-pg-cleanup-outcome-diff-row="E:\/workspace\/sandboxes\/task-1-worktree"/);
});

test('buildProgressGraphPreviewHtml renders isolated malformed host evidence rows', () => {
  const presentation = coerceHostEvidencePresentation({
    generated_at: '2026-06-19T09:00:00.000Z',
    project_root: 'E:/workspace/example',
    evidence_dir: 'E:/workspace/example/.codex/scheduler/evidence',
    status: 'degraded',
    card_count: 0,
    error_count: 1,
    empty_message: '',
    cards: [],
    error_rows: [
      {
        id: 'host-evidence-error:1',
        status: 'read-error',
        severity: 'error',
        evidence_path: 'E:/workspace/example/.codex/scheduler/evidence/malformed.json',
        error_kind: 'invalid_evidence',
        message: 'host scheduler evidence artifact is not valid JSON',
      },
    ],
  });

  const html = buildProgressGraphPreviewHtml(buildBaseState({
    hostEvidencePresentation: presentation,
  }));

  assert.match(html, /data-pg-host-evidence-status="degraded"/);
  assert.match(html, /errors 1/);
  assert.match(html, /Malformed evidence rows/);
  assert.match(html, /invalid_evidence/);
  assert.match(html, /malformed\.json/);
  assert.match(html, /host scheduler evidence artifact is not valid JSON/);
});

test('buildProgressGraphPreviewHtml renders host evidence backend read errors', () => {
  const html = buildProgressGraphPreviewHtml(buildBaseState({
    hostEvidencePresentation: null,
    hostEvidencePresentationError: 'MCP resource read failed',
  }));

  assert.match(html, /data-pg-host-evidence-status="failed"/);
  assert.match(html, /read failed/);
  assert.match(html, /MCP resource read failed/);
});

test('buildProgressGraphPreviewHtml exposes failed control snapshot status when snapshot parsing failed', () => {
  const html = buildProgressGraphPreviewHtml(buildBaseState({
    controlSnapshotExists: true,
    controlSnapshotError: 'unexpected token',
  }));

  assert.match(html, /data-control-snapshot-status="failed"/);
  assert.match(html, /runtime snapshot 加载失败：unexpected token/);
});

test('buildProgressGraphPreviewHtml injects Knowledge Graph Engine shell when V2 payload is available', () => {
  const v2Payload: ProgressGraphPreviewV2PoCPayload = {
    graphId: 'planning-gates-index',
    title: 'Planning Gates Index',
    snapshotId: 'snapshot-001',
    recordedAt: '2026-05-07T06:00:00.000Z',
    sourcePath: 'design_docs/stages/planning-gate',
    nodeCount: 2,
    edgeCount: 1,
    nodes: [
      {
        id: 'gate:1',
        label: 'Gate 1',
        kind: 'task',
        status: 'in_progress',
        summary: 'First gate',
        tags: ['active'],
        hasRuntimeBinding: true,
        hasLocalTrajectory: false,
        localTrajectoryId: null,
        workItemIds: ['work:1'],
        groupItemIds: ['group:1'],
      },
      {
        id: 'gate:2',
        label: 'Gate 2',
        kind: 'reference',
        status: 'pending',
        summary: '',
        tags: [],
        hasRuntimeBinding: false,
        hasLocalTrajectory: false,
        localTrajectoryId: null,
        workItemIds: [],
        groupItemIds: [],
      },
    ],
    edges: [
      {
        id: 'gate:1=>gate:2#0',
        source: 'gate:1',
        target: 'gate:2',
        kind: 'workflow',
        directed: true,
      },
    ],
    runtimeSummary: {
      boundNodeCount: 1,
      openWorkItemCount: 1,
      activeGroupItemCount: 2,
      unboundGroupItemCount: 0,
    },
  };

  const html = buildProgressGraphPreviewHtml(buildBaseState({
    v2GraphPayload: v2Payload,
    v2GraphScriptUri: 'vscode-webview-resource://test/progressGraphV2Engine.js',
    v2GraphWorkerUri: 'vscode-webview-resource://test/knowledgeGraphForceWorker.js',
    localWorkTrajectoryScriptUri: 'vscode-webview-resource://test/localWorkTrajectory.js',
    localWorkTrajectoryStyleUri: 'vscode-webview-resource://test/localWorkTrajectory.css',
  }));

  assert.match(html, /Knowledge Graph Engine/);
  assert.match(html, /Planning Gates Index/);
  assert.match(html, /graph_id=planning-gates-index/);
  assert.match(html, /id="pgHostChromeDock"/);
  assert.match(html, /id="pgHostFloatingZone"/);
  assert.match(html, /class="pg-host-floating-bar"/);
  assert.match(html, /id="pgHostTabChecklist"/);
  assert.match(html, /id="pgHostTabTrajectory"/);
  assert.match(html, /id="pgHostPreviewTabs"/);
  assert.match(html, /id="pgHostChecklistPanel"/);
  assert.match(html, /id="pgHostTrajectoryPanel"/);
  assert.match(html, /id="pgHostPreviewHeightHandle"/);
  assert.match(html, /class="pg-host-preview-height-handle"/);
  assert.match(html, /role="slider"/);
  assert.match(html, /aria-label="Resize Checklist and Trajectory panel height"/);
  assert.match(html, /aria-orientation="vertical"/);
  assert.match(html, /aria-valuemin="520"/);
  assert.match(html, /aria-valuemax="1200"/);
  assert.match(html, /id="pgHostChromePeek"/);
  assert.match(html, /id="pgHostCollapsePanel"/);
  assert.match(html, /Checklist/);
  assert.match(html, /Trajectory/);
  assert.match(html, /show panal/);
  assert.match(html, /hide panel/);
  assert.match(html, /data-pg-tab-target="checklist"/);
  assert.match(html, /data-pg-tab-target="trajectory"/);
  assert.match(html, /pgHostActivePreviewTab/);
  assert.match(html, /pgHostPreviewPanelHeight/);
  assert.match(html, /--pg-host-preview-panel-height/);
  assert.match(html, /readAppliedPanelHeight/);
  assert.match(html, /heightHandle\.addEventListener\('pointerdown'/);
  assert.match(html, /heightHandle\.addEventListener\('keydown'/);
  assert.match(html, /setPointerCapture/);
  assert.match(html, /row-resize/);
  assert.match(html, /ArrowDown/);
  assert.match(html, /PageDown/);
  assert.match(html, /tabsRoot\.style\.setProperty\('--pg-host-preview-panel-height'/);
  assert.match(html, /window\.dispatchEvent\(new Event\('resize'\)\)/);
  assert.doesNotMatch(html, /Show Progress Graph Panel/);
  assert.doesNotMatch(html, /Collapse Panel/);
  assert.match(html, /id="pgHostV2GraphCanvas"/);
  assert.match(html, /id="pgHostV2GraphPayload"/);
  assert.match(html, /Graph Config/);
  assert.match(html, /id="pgHostV2ConfigCard"/);
  assert.match(html, /id="pgHostV2ConfigToggle"/);
  assert.match(html, /id="pgHostV2ConfigCollapsedBar"/);
  assert.match(html, /id="pgHostV2ConfigCollapsedLabel"/);
  assert.match(html, /id="pgHostV2ConfigCardContent"/);
  assert.match(html, /id="pgHostV2ConfigCardTitle"/);
  assert.match(html, /id="pgHostV2ConfigTitleGhost"/);
  assert.match(html, /id="pgHostV2Layout"/);
  assert.match(html, /id="pgHostV2GraphMain"/);
  assert.match(html, /id="pgHostV2ResizeHandle"/);
  assert.match(html, /id="pgHostV2Side"/);
  assert.match(html, /id="pgHostV2EngineStatus"/);
  assert.match(html, /data-pg-v2-worker-uri="vscode-webview-resource:\/\/test\/knowledgeGraphForceWorker\.js"/);
  assert.match(html, /data-pg-v2-auto-shake="true"/);
  assert.match(html, /id="pgHostV2NodeDetailCard"/);
  assert.match(html, /id="pgHostV2ClearSelection"/);
  assert.match(html, /Clear Selection/);
  assert.match(html, /id="pgHostV2MetricsDock"/);
  assert.match(html, /id="pgHostV2MetricsInline"/);
  assert.match(html, /id="pgHostV2MetricsSide"/);
  assert.match(html, /id="pgHostV2ShakeLayout"/);
  assert.match(html, /Shake Layout/);
  assert.match(html, /id="pgHostV2ResetViewport"/);
  assert.match(html, /Reset Zoom\/Pan/);
  assert.match(html, /id="pgHostV2AppearanceLabelDensity"/);
  assert.match(html, /id="pgHostV2AppearanceLabelDensity"[^>]*min="0"[^>]*max="1"/);
  assert.match(html, /id="pgHostV2ForceGravity"/);
  assert.match(html, /id="pgHostV2ColorGroups"/);
  assert.match(html, /id="pgHostV2AddColorGroup"/);
  assert.match(html, /外部 knowledge-graph-engine 渲染/);
  assert.match(html, /globalThis\.__pgHostVsCodeApi = vscode/);
  assert.match(html, /progressGraphV2Engine\.js/);
  assert.match(html, /id="pgHostLocalWorkTrajectoryRoot"/);
  assert.match(html, /localWorkTrajectory\.js/);
  assert.match(html, /localWorkTrajectory\.css/);
});

test('buildProgressGraphPreviewHtml disables V2 auto shake during refreshing shell preservation', () => {
  const v2Payload: ProgressGraphPreviewV2PoCPayload = {
    graphId: 'project-checklist-current',
    title: 'Project Checklist',
    snapshotId: 'snapshot-refreshing',
    recordedAt: '2026-06-04T06:00:00.000Z',
    sourcePath: 'design_docs/Project Master Checklist.md',
    nodeCount: 1,
    edgeCount: 0,
    nodes: [
      {
        id: 'node:1',
        label: 'Node 1',
        kind: 'task',
        status: 'pending',
        summary: '',
        tags: [],
        hasRuntimeBinding: false,
        hasLocalTrajectory: false,
        localTrajectoryId: null,
        workItemIds: [],
        groupItemIds: [],
      },
    ],
    edges: [],
    runtimeSummary: {
      boundNodeCount: 0,
      openWorkItemCount: 0,
      activeGroupItemCount: 0,
      unboundGroupItemCount: 0,
    },
  };

  const html = buildProgressGraphPreviewHtml(buildBaseState({
    freshness: 'refreshing',
    freshnessLabel: 'Refreshing',
    isRefreshRunning: true,
    v2GraphPayload: v2Payload,
    v2GraphScriptUri: 'vscode-webview-resource://test/progressGraphV2Engine.js',
    v2GraphWorkerUri: 'vscode-webview-resource://test/knowledgeGraphForceWorker.js',
    v2GraphAutoShake: false,
  }));

  assert.match(html, /data-pg-v2-auto-shake="false"/);
});

test('buildProgressGraphPreviewHtml injects local work trajectory payload for React Flow mount', () => {
  const html = buildProgressGraphPreviewHtml(buildBaseState({
    localWorkTrajectoryScriptUri: 'vscode-webview-resource://test/localWorkTrajectory.js',
    localWorkTrajectoryStyleUri: 'vscode-webview-resource://test/localWorkTrajectory.css',
    localWorkTrajectory: {
      trajectoryId: 'local-work:checkpoint-current',
      title: 'Checkpoint Local Work Trajectory',
      recordedAt: '2026-06-04T00:00:00.000Z',
      sourceGraphId: 'checkpoint-current',
      sourceNodeId: 'milestone:current-phase',
      guideContext: 'design_docs/stages/planning-gate/current.md',
      metadata: {},
      lanes: [
        {
          id: 'lane:main',
          label: '当前工作',
          status: 'active',
          summary: '',
          metadata: {},
        },
      ],
      events: [
        {
          id: 'event:001',
          laneId: 'lane:main',
          title: '实现单线轨迹',
          kind: 'task',
          status: 'in_progress',
          order: 1,
          summary: '',
          metadata: {},
        },
      ],
      relations: [],
    },
  }));

  assert.match(html, /id="pgHostLocalWorkTrajectoryRoot"/);
  assert.match(html, /id="pgHostLocateTrajectoryParent"/);
  assert.match(html, /data-pg-source-graph-id="checkpoint-current"/);
  assert.match(html, /data-pg-source-node-id="milestone:current-phase"/);
  assert.match(html, /pg-host-locate-trajectory-parent/);
  assert.match(html, /pg-host-select-graph-node/);
  assert.match(html, /pg-host-open-trajectory/);
  assert.match(html, /Agent managed/);
  assert.doesNotMatch(html, /id="pgHostLwtStart"/);
  assert.doesNotMatch(html, /id="pgHostLwtAppend"/);
  assert.doesNotMatch(html, /id="pgHostLwtAdvance"/);
  assert.doesNotMatch(html, /startLocalWorkTrajectory/);
  assert.doesNotMatch(html, /appendLocalWorkTrajectoryEvent/);
  assert.doesNotMatch(html, /advanceLocalWorkTrajectoryEvent/);
  assert.match(html, /id="pgHostLocalWorkTrajectoryPayload"/);
  assert.match(html, /Checkpoint Local Work Trajectory/);
  assert.match(html, /localWorkTrajectory\.js/);
  assert.match(html, /localWorkTrajectory\.css/);
});

test('buildProgressGraphPreviewHtml injects scheduler trajectory payload separately', () => {
  const html = buildProgressGraphPreviewHtml(buildBaseState({
    localWorkTrajectoryScriptUri: 'vscode-webview-resource://test/localWorkTrajectory.js',
    localWorkTrajectoryStyleUri: 'vscode-webview-resource://test/localWorkTrajectory.css',
    schedulerTrajectoryArtifactExists: true,
    schedulerWorkTrajectory: {
      trajectoryId: 'local-work:scheduler-projection',
      title: 'Scheduler Local Work Trajectory',
      recordedAt: '2026-06-17T00:00:00.000Z',
      sourceGraphId: null,
      sourceNodeId: null,
      guideContext: 'schedulerProjection',
      metadata: {
        authority: 'scheduler',
        scheduler_history_timeline: [
          'timestamp=2026-06-17T01:40:01+08:00 | kind=task_running | id=scheduler-event-1 | task=api-task',
          'timestamp=2026-06-17T01:40:02+08:00 | kind=task_completed | id=scheduler-event-2 | task=api-task',
        ].join('\n'),
        scheduler_history_timeline_count: '2',
        scheduler_history_timeline_limit: '40',
        scheduler_history_timeline_truncated: 'false',
      },
      lanes: [
        {
          id: 'lane:api',
          label: 'api',
          status: 'done',
          summary: '',
          metadata: {},
        },
        {
          id: 'lane:data',
          label: 'data',
          status: 'done',
          summary: '',
          metadata: {},
        },
        {
          id: 'lane:client',
          label: 'client',
          status: 'done',
          summary: '',
          metadata: {},
        },
        {
          id: 'lane:qa',
          label: 'qa',
          status: 'done',
          summary: '',
          metadata: {},
        },
      ],
      events: [
        {
          id: 'scheduler-task:api-task',
          laneId: 'lane:api',
          title: 'api/task',
          kind: 'task',
          status: 'completed',
          order: 1,
          summary: '',
          metadata: {},
        },
        {
          id: 'scheduler-task:data-task',
          laneId: 'lane:data',
          title: 'data/task',
          kind: 'task',
          status: 'completed',
          order: 2,
          summary: '',
          metadata: {},
        },
        {
          id: 'scheduler-task:client-task',
          laneId: 'lane:client',
          title: 'client/task',
          kind: 'task',
          status: 'completed',
          order: 3,
          summary: '',
          metadata: {},
        },
        {
          id: 'scheduler-merge:client-ready',
          laneId: 'lane:client',
          title: 'client ready',
          kind: 'merge',
          status: 'completed',
          order: 4,
          summary: '',
          metadata: {},
        },
        {
          id: 'scheduler-task:integration-task',
          laneId: 'lane:qa',
          title: 'integration/task',
          kind: 'task',
          status: 'completed',
          order: 5,
          summary: '',
          metadata: {},
        },
        {
          id: 'scheduler-merge:integration-done',
          laneId: 'lane:qa',
          title: 'integration done',
          kind: 'merge',
          status: 'completed',
          order: 6,
          summary: '',
          metadata: {},
        },
      ],
      relations: [
        {
          sourceEventId: 'scheduler-task:api-task',
          targetEventId: 'scheduler-task:client-task',
          kind: 'depends_on',
          summary: '',
          metadata: {},
        },
        {
          sourceEventId: 'scheduler-task:data-task',
          targetEventId: 'scheduler-task:client-task',
          kind: 'depends_on',
          summary: '',
          metadata: {},
        },
        {
          sourceEventId: 'scheduler-task:client-task',
          targetEventId: 'scheduler-merge:client-ready',
          kind: 'sequence',
          summary: '',
          metadata: {},
        },
        {
          sourceEventId: 'scheduler-task:api-task',
          targetEventId: 'scheduler-merge:client-ready',
          kind: 'syncs_from',
          summary: '',
          metadata: {},
        },
        {
          sourceEventId: 'scheduler-task:data-task',
          targetEventId: 'scheduler-merge:client-ready',
          kind: 'syncs_from',
          summary: '',
          metadata: {},
        },
        {
          sourceEventId: 'scheduler-merge:client-ready',
          targetEventId: 'scheduler-task:integration-task',
          kind: 'depends_on',
          summary: '',
          metadata: {},
        },
        {
          sourceEventId: 'scheduler-task:data-task',
          targetEventId: 'scheduler-task:integration-task',
          kind: 'depends_on',
          summary: '',
          metadata: {},
        },
        {
          sourceEventId: 'scheduler-task:integration-task',
          targetEventId: 'scheduler-merge:integration-done',
          kind: 'sequence',
          summary: '',
          metadata: {},
        },
        {
          sourceEventId: 'scheduler-task:api-task',
          targetEventId: 'scheduler-merge:integration-done',
          kind: 'syncs_from',
          summary: '',
          metadata: {},
        },
        {
          sourceEventId: 'scheduler-task:data-task',
          targetEventId: 'scheduler-merge:integration-done',
          kind: 'syncs_from',
          summary: '',
          metadata: {},
        },
        {
          sourceEventId: 'scheduler-task:client-task',
          targetEventId: 'scheduler-merge:integration-done',
          kind: 'syncs_from',
          summary: '',
          metadata: {},
        },
        {
          sourceEventId: 'scheduler-merge:client-ready',
          targetEventId: 'scheduler-merge:integration-done',
          kind: 'syncs_from',
          summary: '',
          metadata: {},
        },
      ],
    },
  }));

  assert.match(html, /id="pgHostSchedulerWorkTrajectoryRoot"/);
  assert.match(html, /id="pgHostSchedulerWorkTrajectoryPayload"/);
  assert.match(html, /data-pg-trajectory-payload-id="pgHostSchedulerWorkTrajectoryPayload"/);
  assert.match(html, /Scheduler Trajectory Projection/);
  assert.match(html, /Scheduler projection/);
  assert.match(html, /scheduler-work-trajectory\.json/);
  assert.match(html, /lanes=4/);
  assert.match(html, /events=6/);
  assert.match(html, /relations=12/);
  assert.match(html, /Scheduler Local Work Trajectory/);
  assert.match(html, /Scheduler history timeline/);
  assert.match(html, /2 entries/);
  assert.match(html, /scheduler-event-1/);
  assert.match(html, /scheduler-event-2/);
  assert.doesNotMatch(html, /Timeline truncated by projection limit/);
  assert.match(html, /localWorkTrajectory\.js/);
});

test('buildProgressGraphPreviewHtml marks truncated scheduler history timeline', () => {
  const html = buildProgressGraphPreviewHtml(buildBaseState({
    schedulerTrajectoryArtifactExists: true,
    schedulerWorkTrajectory: {
      trajectoryId: 'local-work:scheduler-projection',
      title: 'Scheduler Local Work Trajectory',
      recordedAt: '2026-06-17T00:00:00.000Z',
      sourceGraphId: null,
      sourceNodeId: null,
      guideContext: 'schedulerProjection',
      metadata: {
        scheduler_history_timeline: 'timestamp=2026-06-17T01:40:01+08:00 | kind=task_running | id=scheduler-event-1 | task=api-task',
        scheduler_history_timeline_count: '45',
        scheduler_history_timeline_limit: '40',
        scheduler_history_timeline_truncated: 'true',
      },
      lanes: [
        {
          id: 'lane:scheduler',
          label: 'scheduler',
          status: 'done',
          summary: '',
          metadata: {},
        },
      ],
      events: [
        {
          id: 'scheduler-task:api-task',
          laneId: 'lane:scheduler',
          title: 'api/task',
          kind: 'task',
          status: 'completed',
          order: 1,
          summary: '',
          metadata: {},
        },
      ],
      relations: [],
    },
  }));

  assert.match(html, /Scheduler history timeline/);
  assert.match(html, /showing 1\/45/);
  assert.match(html, /Timeline truncated by projection limit 40/);
});

test('buildProgressGraphPreviewHtml explains missing local trajectory anchor', () => {
  const html = buildProgressGraphPreviewHtml(buildBaseState({
    localWorkTrajectory: {
      trajectoryId: 'local-work:single-line-current',
      title: 'Unanchored Local Work Trajectory',
      recordedAt: '2026-06-13T00:00:00.000Z',
      sourceGraphId: null,
      sourceNodeId: null,
      guideContext: 'codex-mcp-agent',
      metadata: {},
      lanes: [],
      events: [],
      relations: [],
    },
  }));

  assert.match(html, /anchor=not set/);
  assert.match(html, /No global progress-map anchor has been set/);
  assert.match(html, /localTrajectory setAnchor/);
  assert.match(html, /id="pgHostLocateTrajectoryParent"[\s\S]*disabled/);
});
