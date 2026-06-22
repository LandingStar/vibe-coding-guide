import type {
  SchedulerAuthorizationReadback,
  SchedulerAuthorizationTaskSummary,
  SchedulerOperatorBindingReference,
  SchedulerOperatorBindingReferenceSummary,
  SchedulerOperatorBindingReferenceTaskSummary,
  SchedulerOperatorExchangeCandidate,
  SchedulerOperatorWorkflowState,
} from './schedulerOperatorWorkflow';

export type ProgressGraphPreviewFreshness = 'missing' | 'fresh' | 'stale' | 'refreshing' | 'failed';

export type ProgressGraphPreviewArtifactState = {
  artifactPath: string;
  artifactModifiedAt: string | null;
  artifactModifiedTimeMs: number | null;
  controlSnapshotPath: string;
  controlSnapshotExists: boolean;
  controlSnapshot: ProgressGraphPreviewControlSnapshot | null;
  controlSnapshotError: string | null;
  historyArtifactPath: string;
  historyArtifactExists: boolean;
  trajectoryArtifactPath: string;
  trajectoryArtifactExists: boolean;
  schedulerTrajectoryArtifactPath: string;
  schedulerTrajectoryArtifactExists: boolean;
  previewExists: boolean;
  previewHtml: string | null;
  localWorkTrajectory: ProgressGraphPreviewLocalWorkTrajectory | null;
  localWorkTrajectoryError: string | null;
  schedulerWorkTrajectory: ProgressGraphPreviewLocalWorkTrajectory | null;
  schedulerWorkTrajectoryError: string | null;
  hostEvidencePresentationResourceUri: string;
  hostEvidencePresentation: ProgressGraphPreviewHostEvidencePresentation | null;
  hostEvidencePresentationError: string | null;
  schedulerOperatorWorkflow: SchedulerOperatorWorkflowState;
  v2GraphPayload: ProgressGraphPreviewV2PoCPayload | null;
  v2GraphPayloadError: string | null;
};

export type ProgressGraphPreviewControlSnapshotSummary = {
  open_work_item_count: number;
  blocked_work_item_count: number;
  waiting_external_resolution_count: number;
  active_group_item_count: number;
  unbound_group_item_count: number;
};

export type ProgressGraphPreviewControlWorkItem = {
  work_item_id: string;
  lifecycle_state: string;
  rollup_surface_kind: string;
  rollup_surface_state: string;
  rollup_blocked_reason: string | null;
  rollup_writeback_disposition: string;
  dominant_group_item_ids: string[];
  open_group_item_count: number;
  source_trace_id: string;
};

export type ProgressGraphPreviewControlGroupItem = {
  group_item_id: string;
  work_item_id: string;
  task_group_id: string | null;
  child_task_ids: string[];
  lifecycle_state: string;
  governance_surface_kind: string;
  governance_surface_state: string;
  current_gate_state: string;
  writeback_disposition: string;
  delivery_surface_kind: string;
  delivery_state: string;
  blocked_reason: string | null;
  open_items: string[];
  authoritative_refs: string[];
  latest_trace_id: string | null;
  latest_envelope_id: string | null;
  actor_label: string | null;
};

export type ProgressGraphPreviewControlBinding = {
  binding_id: string;
  binding_kind: string;
  graph_id: string | null;
  graph_target_id: string | null;
  graph_target_key: string | null;
  work_item_ids: string[];
  group_item_ids: string[];
  binding_reason: string;
};

export type ProgressGraphPreviewControlSnapshot = {
  snapshot_version: string;
  snapshot_kind: string;
  generated_at: string;
  summary: ProgressGraphPreviewControlSnapshotSummary;
  work_items: ProgressGraphPreviewControlWorkItem[];
  group_items: ProgressGraphPreviewControlGroupItem[];
  bindings: ProgressGraphPreviewControlBinding[];
};

export type ProgressGraphPreviewV2PoCNode = {
  id: string;
  label: string;
  kind: string;
  status: string;
  summary: string;
  tags: string[];
  hasRuntimeBinding: boolean;
  hasLocalTrajectory: boolean;
  localTrajectoryId: string | null;
  workItemIds: string[];
  groupItemIds: string[];
};

export type ProgressGraphPreviewV2PoCEdge = {
  id: string;
  source: string;
  target: string;
  kind: string;
  directed: boolean;
};

export type ProgressGraphPreviewV2PoCPayload = {
  graphId: string;
  title: string;
  snapshotId: string | null;
  recordedAt: string | null;
  sourcePath: string | null;
  nodeCount: number;
  edgeCount: number;
  nodes: ProgressGraphPreviewV2PoCNode[];
  edges: ProgressGraphPreviewV2PoCEdge[];
  runtimeSummary: {
    boundNodeCount: number;
    openWorkItemCount: number;
    activeGroupItemCount: number;
    unboundGroupItemCount: number;
  };
};

export type ProgressGraphPreviewTrajectoryLane = {
  id: string;
  label: string;
  status: string;
  summary: string;
  metadata: Record<string, string>;
};

export type ProgressGraphPreviewTrajectoryEvent = {
  id: string;
  laneId: string;
  title: string;
  kind: string;
  status: string;
  order: number;
  summary: string;
  metadata: Record<string, string>;
};

export type ProgressGraphPreviewTrajectoryRelation = {
  sourceEventId: string;
  targetEventId: string;
  kind: string;
  summary: string;
  metadata: Record<string, string>;
};

export type ProgressGraphPreviewLocalWorkTrajectory = {
  trajectoryId: string;
  title: string;
  recordedAt: string | null;
  sourceGraphId: string | null;
  sourceNodeId: string | null;
  guideContext: string | null;
  metadata: Record<string, string>;
  lanes: ProgressGraphPreviewTrajectoryLane[];
  events: ProgressGraphPreviewTrajectoryEvent[];
  relations: ProgressGraphPreviewTrajectoryRelation[];
  childTrajectories: ProgressGraphPreviewLocalWorkTrajectory[];
};

export type ProgressGraphPreviewHostEvidenceFact = {
  label: string;
  value: string;
};

export type ProgressGraphPreviewHostEvidenceRef = {
  label: string;
  target: string;
  refKind: string;
};

export type ProgressGraphPreviewHostEvidenceCard = {
  id: string;
  title: string;
  subtitle: string;
  status: string;
  severity: string;
  timestamp: string;
  runtimeProviders: string[];
  hostSurface: string;
  invocationId: string;
  requestedBy: string;
  stopReason: string;
  stopDetail: string;
  runCount: number;
  outputCount: number;
  permissionReviewCount: number;
  keyFacts: ProgressGraphPreviewHostEvidenceFact[];
  refs: ProgressGraphPreviewHostEvidenceRef[];
  authorityClues: ProgressGraphPreviewHostEvidenceFact[];
  metadata: Record<string, unknown>;
};

export type ProgressGraphPreviewHostEvidenceErrorRow = {
  id: string;
  status: string;
  severity: string;
  evidencePath: string;
  errorKind: string;
  message: string;
};

export type ProgressGraphPreviewHostEvidencePresentation = {
  generatedAt: string | null;
  projectRoot: string;
  evidenceDir: string;
  status: string;
  cardCount: number;
  errorCount: number;
  cards: ProgressGraphPreviewHostEvidenceCard[];
  errorRows: ProgressGraphPreviewHostEvidenceErrorRow[];
  emptyMessage: string;
};

type SchedulerCleanupReceiptCandidate = {
  id: string;
  path: string;
  label: string;
  role: string;
  status: string;
  detail: string;
};

type SchedulerCleanupOutcomeDiffRow = {
  id: string;
  title: string;
  status: string;
  beforeSummary: string;
  afterSummary: string;
  sourcePath: string;
  cleanupPath: string;
  currentPath: string;
  changedAllocationIds: string[];
};

export type ProgressGraphPreviewState = ProgressGraphPreviewArtifactState & {
  freshness: ProgressGraphPreviewFreshness;
  freshnessLabel: string;
  freshnessMessage: string;
  isRefreshRunning: boolean;
  lastLoadedAt: string | null;
  lastRefreshStartedAt: string | null;
  lastRefreshCompletedAt: string | null;
  lastRefreshError: string | null;
  v2GraphScriptUri: string | null;
  v2GraphWorkerUri: string | null;
  v2GraphAutoShake: boolean;
  localWorkTrajectoryScriptUri: string | null;
  localWorkTrajectoryStyleUri: string | null;
};

export function buildProgressGraphPreviewHtml(state: ProgressGraphPreviewState): string {
  if (state.previewHtml) {
    return buildParallelPreviewHtml(state, state.previewHtml);
  }

  const nonce = getNonce();
  const escapedPath = escapeHtml(state.artifactPath);
  const escapedLoadedAt = escapeHtml(formatTimestamp(state.lastLoadedAt));
  const escapedArtifactUpdatedAt = escapeHtml(formatTimestamp(state.artifactModifiedAt));
  const escapedRefreshStartedAt = escapeHtml(formatTimestamp(state.lastRefreshStartedAt));
  const escapedRefreshCompletedAt = escapeHtml(formatTimestamp(state.lastRefreshCompletedAt));
  const escapedRefreshError = escapeHtml(state.lastRefreshError ?? '');
  const escapedFreshnessLabel = escapeHtml(state.freshnessLabel);
  const escapedFreshnessMessage = escapeHtml(state.freshnessMessage);
  const controlOverlay = buildControlOverlay(state);
  const emptyState = !state.previewExists && !state.previewHtml
    ? `<section class="empty-state">
    <h2>Preview Artifact Missing</h2>
    <p>当前宿主工作流已经成立，但 workspace 中还没有可加载的 <code>latest.html</code> artifact。</p>
    <p>请先刷新 progress graph artifacts，然后点击顶部的 <strong>Refresh Preview</strong>。</p>
  </section>`
    : '';
  const freshnessMeta = [
    '<span class="meta-pill">Mode Parallel shell + original HTML</span>',
    `<span class="meta-pill">Loaded ${escapedLoadedAt}</span>`,
    `<span class="meta-pill">Artifact ${escapedArtifactUpdatedAt}</span>`,
    state.lastRefreshStartedAt ? `<span class="meta-pill">Refresh Started ${escapedRefreshStartedAt}</span>` : '',
    state.lastRefreshCompletedAt ? `<span class="meta-pill">Refresh Completed ${escapedRefreshCompletedAt}</span>` : '',
  ].filter(Boolean).join('');
  const refreshError = state.lastRefreshError
    ? `<p class="status-detail">Last error: ${escapedRefreshError}</p>`
    : '';

  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'nonce-${nonce}'; script-src 'nonce-${nonce}';">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Progress Graph</title>
  <style nonce="${nonce}">
    :root {
      color-scheme: light dark;
    }
    * {
      box-sizing: border-box;
    }
    body {
      margin: 0;
      color: var(--vscode-editor-foreground);
      background: var(--vscode-editor-background);
      font-family: var(--vscode-font-family);
      display: flex;
      flex-direction: column;
      min-height: 100vh;
      overflow: hidden;
    }
    .topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 14px 18px;
      border-bottom: 1px solid var(--vscode-panel-border);
      background: color-mix(in srgb, var(--vscode-sideBar-background) 70%, transparent);
    }
    .title-group {
      min-width: 0;
    }
    .title {
      margin: 0;
      font-size: 1.05rem;
      font-weight: 700;
    }
    .status-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      margin-bottom: 8px;
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 0.78rem;
      font-weight: 700;
      letter-spacing: 0.02em;
      border: 1px solid transparent;
    }
    .status-badge.fresh {
      color: var(--vscode-testing-iconPassed);
      background: color-mix(in srgb, var(--vscode-testing-iconPassed) 18%, transparent);
      border-color: color-mix(in srgb, var(--vscode-testing-iconPassed) 35%, transparent);
    }
    .status-badge.stale {
      color: var(--vscode-testing-iconQueued);
      background: color-mix(in srgb, var(--vscode-testing-iconQueued) 18%, transparent);
      border-color: color-mix(in srgb, var(--vscode-testing-iconQueued) 35%, transparent);
    }
    .status-badge.refreshing {
      color: var(--vscode-testing-iconQueued);
      background: color-mix(in srgb, var(--vscode-progressBar-background) 18%, transparent);
      border-color: color-mix(in srgb, var(--vscode-progressBar-background) 35%, transparent);
    }
    .status-badge.failed,
    .status-badge.missing {
      color: var(--vscode-testing-iconFailed);
      background: color-mix(in srgb, var(--vscode-testing-iconFailed) 18%, transparent);
      border-color: color-mix(in srgb, var(--vscode-testing-iconFailed) 35%, transparent);
    }
    .subtitle {
      margin-top: 4px;
      color: var(--vscode-descriptionForeground);
      font-size: 0.86rem;
      line-height: 1.4;
      word-break: break-all;
    }
    .meta-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 10px;
    }
    .meta-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 8px;
      border-radius: 999px;
      font-size: 0.76rem;
      color: var(--vscode-descriptionForeground);
      background: color-mix(in srgb, var(--vscode-sideBar-background) 82%, transparent);
      border: 1px solid var(--vscode-panel-border);
    }
    .actions {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }
    button {
      border: 1px solid var(--vscode-button-border, transparent);
      background: var(--vscode-button-background);
      color: var(--vscode-button-foreground);
      border-radius: 8px;
      padding: 7px 12px;
      cursor: pointer;
      font: inherit;
      font-size: 0.9rem;
    }
    button.secondary {
      background: var(--vscode-button-secondaryBackground);
      color: var(--vscode-button-secondaryForeground);
    }
    button:hover {
      background: var(--vscode-button-hoverBackground);
    }
    button.secondary:hover {
      background: var(--vscode-button-secondaryHoverBackground);
    }
    button:disabled {
      opacity: 0.6;
      cursor: default;
    }
    .status-strip {
      display: grid;
      gap: 6px;
      padding: 12px 18px;
      border-bottom: 1px solid var(--vscode-panel-border);
      background: color-mix(in srgb, var(--vscode-editorWidget-background) 82%, transparent);
    }
    .status-message {
      margin: 0;
      line-height: 1.5;
      color: var(--vscode-editor-foreground);
    }
    .status-detail {
      margin: 0;
      color: var(--vscode-descriptionForeground);
      font-size: 0.82rem;
      line-height: 1.5;
    }
    .body {
      flex: 1;
      min-height: 0;
      padding: 14px 18px 18px;
      overflow: auto;
      background: var(--vscode-editor-background);
    }
    .empty-state {
      max-width: 760px;
      margin: 28px auto 0;
      padding: 22px 24px;
      border-radius: 14px;
      border: 1px solid var(--vscode-panel-border);
      background: var(--vscode-sideBar-background);
      line-height: 1.65;
    }
    .empty-state h2 {
      margin: 0 0 12px;
      font-size: 1.1rem;
    }
    code {
      font-family: var(--vscode-editor-font-family);
      background: var(--vscode-textCodeBlock-background);
      padding: 1px 4px;
      border-radius: 4px;
    }
    @media (max-width: 760px) {
      .topbar {
        grid-auto-flow: row;
        align-items: start;
      }
      .actions {
        width: 100%;
        justify-content: flex-start;
      }
    }
  </style>
</head>
<body>
  <header class="topbar">
    <div class="title-group">
      <div class="status-badge ${state.freshness}">${escapedFreshnessLabel}</div>
      <h1 class="title">Progress Graph</h1>
      <div class="subtitle">artifact: ${escapedPath}</div>
      <div class="meta-row">${freshnessMeta}</div>
    </div>
    <div class="actions">
      <button id="refreshButton" ${state.isRefreshRunning ? 'disabled' : ''}>${state.isRefreshRunning ? 'Refreshing...' : 'Refresh Preview'}</button>
      <button id="revealButton" class="secondary">Reveal Artifact</button>
    </div>
  </header>
  <section class="status-strip">
    <p class="status-message">${escapedFreshnessMessage}</p>
    ${refreshError}
  </section>
  ${controlOverlay}
  <main class="body">
    ${emptyState}
  </main>
  <script nonce="${nonce}">
    const vscode = acquireVsCodeApi();
    const refreshButton = document.getElementById('refreshButton');
    const revealButton = document.getElementById('revealButton');

    refreshButton?.addEventListener('click', () => {
      refreshButton.disabled = true;
      refreshButton.textContent = 'Refreshing...';
      vscode.postMessage({ command: 'refresh' });
    });

    revealButton?.addEventListener('click', () => {
      vscode.postMessage({ command: 'revealArtifact' });
    });

    ${buildControlOverlayEnhancementScript()}
  </script>
</body>
</html>`;
}

export function coerceControlSnapshot(value: unknown): ProgressGraphPreviewControlSnapshot {
  if (!isRecord(value)) {
    throw new Error('control snapshot must be an object');
  }

  const summary = isRecord(value.summary) ? value.summary : {};
  return {
    snapshot_version: readString(value.snapshot_version, 'unknown'),
    snapshot_kind: readString(value.snapshot_kind, 'unknown'),
    generated_at: readString(value.generated_at, ''),
    summary: {
      open_work_item_count: readNumber(summary.open_work_item_count),
      blocked_work_item_count: readNumber(summary.blocked_work_item_count),
      waiting_external_resolution_count: readNumber(summary.waiting_external_resolution_count),
      active_group_item_count: readNumber(summary.active_group_item_count),
      unbound_group_item_count: readNumber(summary.unbound_group_item_count),
    },
    work_items: readObjectArray(value.work_items).map((item) => ({
      work_item_id: readString(item.work_item_id, 'unknown-work-item'),
      lifecycle_state: readString(item.lifecycle_state, 'unknown'),
      rollup_surface_kind: readString(item.rollup_surface_kind, 'unknown'),
      rollup_surface_state: readString(item.rollup_surface_state, 'unknown'),
      rollup_blocked_reason: readNullableString(item.rollup_blocked_reason),
      rollup_writeback_disposition: readString(item.rollup_writeback_disposition, 'unknown'),
      dominant_group_item_ids: readStringArray(item.dominant_group_item_ids),
      open_group_item_count: readNumber(item.open_group_item_count),
      source_trace_id: readString(item.source_trace_id, ''),
    })),
    group_items: readObjectArray(value.group_items).map((item) => ({
      group_item_id: readString(item.group_item_id, 'unknown-group-item'),
      work_item_id: readString(item.work_item_id, 'unknown-work-item'),
      task_group_id: readNullableString(item.task_group_id),
      child_task_ids: readStringArray(item.child_task_ids),
      lifecycle_state: readString(item.lifecycle_state, 'unknown'),
      governance_surface_kind: readString(item.governance_surface_kind, 'unknown'),
      governance_surface_state: readString(item.governance_surface_state, 'unknown'),
      current_gate_state: readString(item.current_gate_state, 'unknown'),
      writeback_disposition: readString(item.writeback_disposition, 'unknown'),
      delivery_surface_kind: readString(item.delivery_surface_kind, 'unknown'),
      delivery_state: readString(item.delivery_state, 'unknown'),
      blocked_reason: readNullableString(item.blocked_reason),
      open_items: readStringArray(item.open_items),
      authoritative_refs: readStringArray(item.authoritative_refs),
      latest_trace_id: readNullableString(item.latest_trace_id),
      latest_envelope_id: readNullableString(item.latest_envelope_id),
      actor_label: readNullableString(item.actor_label),
    })),
    bindings: readObjectArray(value.bindings).map((item) => ({
      binding_id: readString(item.binding_id, 'unknown-binding'),
      binding_kind: readString(item.binding_kind, 'unknown'),
      graph_id: readNullableString(item.graph_id),
      graph_target_id: readNullableString(item.graph_target_id),
      graph_target_key: readNullableString(item.graph_target_key),
      work_item_ids: readStringArray(item.work_item_ids),
      group_item_ids: readStringArray(item.group_item_ids),
      binding_reason: readString(item.binding_reason, ''),
    })),
  };
}

export function coerceLocalWorkTrajectory(value: unknown): ProgressGraphPreviewLocalWorkTrajectory {
  if (!isRecord(value)) {
    throw new Error('local work trajectory must be an object');
  }

  const lanes = readObjectCollection(value.lanes).map((item) => ({
    id: readString(item.id, 'unknown-lane'),
    label: readString(item.label, 'untitled lane'),
    status: readString(item.status, 'pending'),
    summary: readString(item.summary, ''),
    metadata: readStringRecord(item.metadata),
  }));
  const events = readObjectCollection(value.events)
    .map((item) => ({
      id: readString(item.id, 'unknown-event'),
      laneId: readString(item.lane_id, readString(item.laneId, 'unknown-lane')),
      title: readString(item.title, 'untitled event'),
      kind: readString(item.kind, 'task'),
      status: readString(item.status, 'pending'),
      order: readNumber(item.order),
      summary: readString(item.summary, ''),
      metadata: readStringRecord(item.metadata),
    }))
    .sort((left, right) => left.order - right.order || left.id.localeCompare(right.id));
  const relations = readObjectArray(value.relations).map((item) => ({
    sourceEventId: readString(
      item.source_event_id,
      readString(item.sourceEventId, 'unknown-source'),
    ),
    targetEventId: readString(
      item.target_event_id,
      readString(item.targetEventId, 'unknown-target'),
    ),
    kind: readString(item.kind, 'sequence'),
    summary: readString(item.summary, ''),
    metadata: readStringRecord(item.metadata),
  }));

  return {
    trajectoryId: readString(value.trajectory_id, readString(value.trajectoryId, 'unknown-trajectory')),
    title: readString(value.title, 'Local Work Trajectory'),
    recordedAt: readNullableString(value.recorded_at) ?? readNullableString(value.recordedAt),
    sourceGraphId: readNullableString(value.source_graph_id) ?? readNullableString(value.sourceGraphId),
    sourceNodeId: readNullableString(value.source_node_id) ?? readNullableString(value.sourceNodeId),
    guideContext: readNullableString(value.guide_context) ?? readNullableString(value.guideContext),
    metadata: readStringRecord(value.metadata),
    lanes,
    events,
    relations,
    childTrajectories: readObjectCollection(value.child_trajectories).map((item) => coerceLocalWorkTrajectory(item)),
  };
}

export function coerceHostEvidencePresentation(value: unknown): ProgressGraphPreviewHostEvidencePresentation {
  if (!isRecord(value)) {
    throw new Error('host evidence presentation must be an object');
  }

  return {
    generatedAt: readNullableString(value.generated_at) ?? readNullableString(value.generatedAt),
    projectRoot: readString(value.project_root, readString(value.projectRoot, '')),
    evidenceDir: readString(value.evidence_dir, readString(value.evidenceDir, '')),
    status: readString(value.status, 'unknown'),
    cardCount: readNumber(value.card_count),
    errorCount: readNumber(value.error_count),
    cards: readObjectArray(value.cards).map((card) => ({
      id: readString(card.id, 'unknown-host-evidence'),
      title: readString(card.title, 'Host evidence'),
      subtitle: readString(card.subtitle, ''),
      status: readString(card.status, 'unknown'),
      severity: readString(card.severity, 'info'),
      timestamp: readString(card.timestamp, ''),
      runtimeProviders: readStringArray(card.runtime_providers),
      hostSurface: readString(card.host_surface, ''),
      invocationId: readString(card.invocation_id, ''),
      requestedBy: readString(card.requested_by, ''),
      stopReason: readString(card.stop_reason, ''),
      stopDetail: readString(card.stop_detail, ''),
      runCount: readNumber(card.run_count),
      outputCount: readNumber(card.output_count),
      permissionReviewCount: readNumber(card.permission_review_count),
      keyFacts: readHostEvidenceFacts(card.key_facts),
      refs: readHostEvidenceRefs(card.refs),
      authorityClues: readHostEvidenceFacts(card.authority_clues),
      metadata: isRecord(card.metadata) ? card.metadata : {},
    })),
    errorRows: readObjectArray(value.error_rows).map((row, index) => ({
      id: readString(row.id, `host-evidence-error:${index + 1}`),
      status: readString(row.status, 'read-error'),
      severity: readString(row.severity, 'error'),
      evidencePath: readString(row.evidence_path, ''),
      errorKind: readString(row.error_kind, 'unknown'),
      message: readString(row.message, ''),
    })),
    emptyMessage: readString(value.empty_message, ''),
  };
}

function buildParallelPreviewHtml(
  state: ProgressGraphPreviewState,
  previewHtml: string,
): string {
  const controlOverlay = buildControlOverlay(state);
  const v2GraphPoC = buildV2GraphPoCSection(state);
  const trajectoryPanel = buildTrajectoryPanelSection(state);
  const previewPanels = buildPreviewTabPanels(v2GraphPoC, trajectoryPanel);
  const localWorkTrajectoryStyle = state.localWorkTrajectoryStyleUri
    ? `<link rel="stylesheet" href="${escapeHtml(state.localWorkTrajectoryStyleUri)}">`
    : '';
  const escapedPath = escapeHtml(state.artifactPath);
  const escapedLoadedAt = escapeHtml(formatTimestamp(state.lastLoadedAt));
  const escapedArtifactUpdatedAt = escapeHtml(formatTimestamp(state.artifactModifiedAt));
  const escapedRefreshStartedAt = escapeHtml(formatTimestamp(state.lastRefreshStartedAt));
  const escapedRefreshCompletedAt = escapeHtml(formatTimestamp(state.lastRefreshCompletedAt));
  const escapedRefreshError = escapeHtml(state.lastRefreshError ?? '');
  const escapedFreshnessLabel = escapeHtml(state.freshnessLabel);
  const escapedFreshnessMessage = escapeHtml(state.freshnessMessage);
  const refreshError = state.lastRefreshError
    ? `<p class="pg-host-status-detail">Last error: ${escapedRefreshError}</p>`
    : '';
  const freshnessMeta = [
    '<span class="pg-host-meta-pill">Mode Parallel shell + original HTML</span>',
    `<span class="pg-host-meta-pill">Loaded ${escapedLoadedAt}</span>`,
    `<span class="pg-host-meta-pill">Artifact ${escapedArtifactUpdatedAt}</span>`,
    state.lastRefreshStartedAt ? `<span class="pg-host-meta-pill">Refresh Started ${escapedRefreshStartedAt}</span>` : '',
    state.lastRefreshCompletedAt ? `<span class="pg-host-meta-pill">Refresh Completed ${escapedRefreshCompletedAt}</span>` : '',
  ].filter(Boolean).join('');
  const hostStyle = `<style>
  .pg-host-chrome-dock {
    position: sticky;
    top: 0;
    z-index: 1000;
    overflow: visible;
  }
  .pg-host-floating-zone {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 1200;
    height: 52px;
    pointer-events: none;
  }
  .pg-host-floating-zone::before {
    content: "";
    position: absolute;
    top: 0;
    left: 50%;
    width: 96px;
    height: 3px;
    border-radius: 0 0 999px 999px;
    background: rgba(248, 244, 239, 0.38);
    transform: translateX(-50%);
    opacity: 0.72;
  }
  .pg-host-floating-bar {
    position: absolute;
    top: 8px;
    left: 50%;
    display: flex;
    align-items: center;
    gap: 8px;
    max-width: calc(100vw - 28px);
    padding: 6px;
    border: 1px solid rgba(255, 255, 255, 0.13);
    border-radius: 999px;
    background: rgba(17, 26, 34, 0.9);
    color: rgba(248, 244, 239, 0.86);
    box-shadow: 0 14px 34px rgba(0, 0, 0, 0.2);
    backdrop-filter: blur(16px);
    opacity: 0;
    visibility: hidden;
    pointer-events: none;
    transform: translate(-50%, -10px);
    transition: opacity 140ms ease, visibility 140ms ease, transform 140ms ease;
  }
  .pg-host-floating-zone[data-pg-floating-visible="true"] .pg-host-floating-bar,
  .pg-host-floating-bar:focus-within {
    opacity: 1;
    visibility: visible;
    pointer-events: auto;
    transform: translate(-50%, 0);
  }
  .pg-host-tab-button,
  .pg-host-floating-action {
    min-height: 28px;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.08);
    color: rgba(248, 244, 239, 0.82);
    padding: 4px 10px;
    font: inherit;
    font-size: 0.76rem;
    font-weight: 700;
    white-space: nowrap;
    cursor: pointer;
  }
  .pg-host-tab-button[aria-selected="true"] {
    background: rgba(95, 164, 220, 0.24);
    border-color: rgba(163, 218, 255, 0.36);
    color: #f8f4ef;
  }
  .pg-host-floating-action:hover,
  .pg-host-tab-button:hover {
    background: rgba(255, 255, 255, 0.15);
  }
  .pg-host-floating-action:disabled {
    cursor: default;
    opacity: 0.62;
  }
  .pg-host-floating-action[data-pg-panel-show="true"][data-pg-visible="false"] {
    display: none;
  }
  .pg-host-chrome-content {
    display: grid;
    overflow-y: auto;
    overscroll-behavior: contain;
    max-height: min(var(--pg-host-chrome-expanded-height, 960px), calc(100vh - 18px));
    opacity: 1;
    transform: translateY(0);
    transform-origin: top center;
    transition: max-height 180ms ease, opacity 180ms ease, transform 180ms ease;
  }
  .pg-host-chrome-dock[data-pg-host-shell="collapsed"] .pg-host-chrome-content {
    max-height: 0;
    opacity: 0;
    transform: translateY(-14px);
    pointer-events: none;
  }
  .pg-host-chrome-peek {
    display: none;
  }
  .pg-host-shell {
    display: grid;
    gap: 10px;
    padding: 14px 18px 16px;
    border-bottom: 1px solid rgba(17, 75, 95, 0.14);
    background: rgba(17, 26, 34, 0.94);
    backdrop-filter: blur(16px);
    box-shadow: 0 14px 32px rgba(0, 0, 0, 0.12);
  }
  .pg-host-topbar {
    display: flex;
    align-items: start;
    justify-content: space-between;
    gap: 16px;
  }
  .pg-host-title-group {
    min-width: 0;
  }
  .pg-host-status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 8px;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.02em;
    border: 1px solid transparent;
  }
  .pg-host-status-badge.fresh {
    color: #5fe0aa;
    background: rgba(95, 224, 170, 0.16);
    border-color: rgba(95, 224, 170, 0.28);
  }
  .pg-host-status-badge.stale,
  .pg-host-status-badge.refreshing {
    color: #ffd98a;
    background: rgba(255, 217, 138, 0.14);
    border-color: rgba(255, 217, 138, 0.28);
  }
  .pg-host-status-badge.failed,
  .pg-host-status-badge.missing {
    color: #ffb2a6;
    background: rgba(255, 178, 166, 0.14);
    border-color: rgba(255, 178, 166, 0.28);
  }
  .pg-host-title {
    margin: 0;
    color: #f8f4ef;
    font-size: 1.05rem;
    font-weight: 700;
  }
  .pg-host-subtitle {
    margin-top: 4px;
    color: rgba(248, 244, 239, 0.76);
    font-size: 0.86rem;
    line-height: 1.4;
    word-break: break-all;
  }
  .pg-host-meta-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 10px;
  }
  .pg-host-meta-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 8px;
    border-radius: 999px;
    font-size: 12px;
    color: rgba(248, 244, 239, 0.76);
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.12);
  }
  .pg-host-actions {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    justify-content: flex-end;
  }
  .pg-host-button {
    border: 1px solid rgba(255, 255, 255, 0.12);
    background: #1f6b83;
    color: #f8f4ef;
    border-radius: 8px;
    padding: 7px 12px;
    cursor: pointer;
    font: inherit;
    font-size: 0.9rem;
  }
  .pg-host-button:hover {
    background: #2a819d;
  }
  .pg-host-button.secondary {
    background: rgba(255, 255, 255, 0.08);
  }
  .pg-host-button.secondary:hover {
    background: rgba(255, 255, 255, 0.14);
  }
  .pg-host-button:disabled {
    opacity: 0.6;
    cursor: default;
  }
  .pg-host-button.collapse {
    background: rgba(255, 255, 255, 0.08);
  }
  .pg-host-button.collapse:hover {
    background: rgba(255, 255, 255, 0.14);
  }
  .pg-host-status-strip {
    display: grid;
    gap: 6px;
  }
  .pg-host-status-message {
    margin: 0;
    color: #f8f4ef;
    line-height: 1.5;
  }
  .pg-host-status-detail {
    margin: 0;
    color: rgba(248, 244, 239, 0.76);
    font-size: 0.82rem;
    line-height: 1.5;
  }
  .pg-host-control-overlay {
    display: grid;
    gap: 12px;
    padding: 14px 18px 18px;
    border-bottom: 1px solid rgba(17, 75, 95, 0.12);
    background: linear-gradient(180deg, rgba(17, 26, 34, 0.92) 0%, rgba(17, 26, 34, 0.86) 100%);
  }
  .pg-host-control-card {
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 14px;
    padding: 14px 16px;
  }
  .pg-host-control-card-title {
    margin: 0 0 6px;
    color: #f8f4ef;
    font-size: 0.94rem;
    font-weight: 700;
  }
  .pg-host-control-card-subtitle {
    margin: 0;
    color: rgba(248, 244, 239, 0.72);
    font-size: 0.82rem;
    line-height: 1.5;
  }
  .pg-host-summary-rail {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(132px, 1fr));
    gap: 10px;
  }
  .pg-host-summary-metric {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 12px 14px;
  }
  .pg-host-summary-label {
    color: rgba(248, 244, 239, 0.68);
    font-size: 0.74rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
  }
  .pg-host-summary-value {
    margin-top: 8px;
    color: #f8f4ef;
    font-size: 1.22rem;
    font-weight: 700;
  }
  .pg-host-control-grid {
    display: grid;
    grid-template-columns: minmax(0, 1.15fr) minmax(280px, 0.85fr);
    gap: 12px;
  }
  .pg-host-preview-tabs {
    --pg-host-preview-panel-height: clamp(640px, calc(100vh - 220px), 920px);
    display: grid;
    gap: 0;
    padding-bottom: 18px;
  }
  .pg-host-tab-panel {
    min-height: calc(var(--pg-host-preview-panel-height) + 36px);
  }
  .pg-host-preview-height-handle {
    position: relative;
    display: grid;
    place-items: center;
    height: 20px;
    margin: -8px 18px 10px;
    border: 0;
    border-radius: 999px;
    background: transparent;
    color: rgba(64, 80, 94, 0.62);
    cursor: row-resize;
  }
  .pg-host-preview-height-handle::before {
    content: "";
    width: min(220px, 42vw);
    height: 4px;
    border-radius: 999px;
    background: rgba(64, 100, 132, 0.2);
    transition: background 120ms ease, transform 120ms ease;
  }
  .pg-host-preview-height-handle:hover::before,
  .pg-host-preview-height-handle:focus-visible::before,
  .pg-host-preview-height-handle[data-pg-dragging="true"]::before {
    background: rgba(64, 100, 132, 0.42);
    transform: scaleX(1.08);
  }
  .pg-host-preview-height-handle:focus-visible {
    outline: 2px solid rgba(86, 144, 191, 0.45);
    outline-offset: 2px;
  }
  .pg-host-v2-poc {
    margin: 18px;
    padding: 18px;
    display: flex;
    flex-direction: column;
    height: var(--pg-host-preview-panel-height);
    min-height: 520px;
    border-radius: 22px;
    border: 1px solid rgba(86, 122, 154, 0.16);
    background:
      radial-gradient(circle at top left, rgba(134, 191, 255, 0.18), transparent 34%),
      radial-gradient(circle at bottom right, rgba(91, 182, 143, 0.1), transparent 28%),
      linear-gradient(180deg, rgba(252, 248, 239, 0.98) 0%, rgba(245, 240, 230, 0.96) 100%);
    box-shadow: 0 24px 46px rgba(38, 49, 60, 0.09), inset 0 1px 0 rgba(255, 255, 255, 0.54);
  }
  .pg-host-v2-poc[data-pg-v2-status="unavailable"] {
    background: rgba(22, 31, 41, 0.9);
    border-color: rgba(255, 255, 255, 0.08);
    box-shadow: 0 18px 34px rgba(0, 0, 0, 0.12);
  }
  .pg-host-trajectory-stack {
    margin: 18px;
    display: grid;
    gap: 16px;
  }
  .pg-host-lwt-mount-section {
    height: var(--pg-host-preview-panel-height);
    min-height: 420px;
    display: grid;
    grid-template-rows: auto auto minmax(0, 1fr);
  }
  .pg-host-tab-panel[hidden] {
    display: none;
  }
  .pg-host-lwt-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 10px;
    padding: 12px 14px;
    border-radius: 12px;
    border: 1px solid rgba(84, 129, 171, 0.14);
    background: rgba(255, 255, 255, 0.72);
  }
  .pg-host-lwt-toolbar-copy {
    min-width: 0;
  }
  .pg-host-lwt-toolbar-title {
    margin: 0;
    color: #22303a;
    font-size: 0.86rem;
    font-weight: 700;
  }
  .pg-host-lwt-toolbar-meta {
    margin: 3px 0 0;
    color: rgba(71, 87, 101, 0.76);
    font-size: 0.75rem;
    line-height: 1.4;
    word-break: break-all;
  }
  .pg-host-lwt-locate-parent {
    flex: 0 0 auto;
    min-height: 30px;
    padding: 6px 11px;
    border: 1px solid rgba(95, 83, 149, 0.24);
    border-radius: 999px;
    background: rgba(246, 243, 255, 0.92);
    color: #5f5395;
    font: inherit;
    font-size: 0.76rem;
    font-weight: 800;
    cursor: pointer;
    white-space: nowrap;
  }
  .pg-host-lwt-locate-parent:hover:not(:disabled),
  .pg-host-lwt-locate-parent:focus-visible:not(:disabled) {
    border-color: rgba(95, 83, 149, 0.42);
    background: #f7f4ff;
    color: #45358f;
  }
  .pg-host-lwt-locate-parent:disabled {
    cursor: default;
    opacity: 0.42;
  }
  .pg-host-lwt-mount {
    min-height: 0;
    height: 100%;
  }
  .pg-host-lwt-mount .pg-lwt-shell {
    height: 100%;
    min-height: 0;
  }
  .pg-host-lwt-history {
    margin: 0 0 10px;
    border: 1px solid rgba(84, 129, 171, 0.14);
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.62);
    overflow: hidden;
  }
  .pg-host-lwt-history-summary {
    cursor: pointer;
    padding: 10px 14px;
    color: #315f7e;
    font-size: 0.78rem;
    font-weight: 800;
  }
  .pg-host-lwt-history-lines {
    display: grid;
    gap: 6px;
    margin: 0;
    padding: 0 14px 12px;
    list-style: none;
  }
  .pg-host-lwt-history-line {
    padding: 7px 9px;
    border-left: 3px solid rgba(72, 111, 146, 0.34);
    border-radius: 6px;
    background: rgba(247, 250, 252, 0.74);
    color: rgba(38, 55, 70, 0.82);
    font-family: ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace;
    font-size: 0.72rem;
    line-height: 1.45;
    overflow-wrap: anywhere;
  }
  .pg-host-lwt-history-more {
    margin: 0;
    padding: 0 14px 12px;
    color: rgba(71, 87, 101, 0.72);
    font-size: 0.74rem;
  }
  .pg-host-v2-head {
    display: flex;
    justify-content: space-between;
    gap: 18px;
    align-items: start;
    margin-bottom: 16px;
  }
  .pg-host-v2-title-wrap {
    min-width: 0;
  }
  .pg-host-v2-head-actions {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 10px;
    min-width: 0;
  }
  .pg-host-v2-eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 999px;
    color: rgba(46, 63, 79, 0.72);
    background: rgba(84, 129, 171, 0.1);
    border: 1px solid rgba(84, 129, 171, 0.14);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }
  .pg-host-v2-poc[data-pg-v2-status="unavailable"] .pg-host-v2-eyebrow {
    color: rgba(248, 244, 239, 0.72);
    background: rgba(255, 255, 255, 0.08);
    border-color: rgba(255, 255, 255, 0.12);
  }
  .pg-host-v2-title {
    margin: 10px 0 4px;
    color: #23303a;
    font-size: 1.08rem;
    font-weight: 700;
  }
  .pg-host-v2-poc[data-pg-v2-status="unavailable"] .pg-host-v2-title {
    color: #f8f4ef;
  }
  .pg-host-v2-subtitle {
    margin: 0;
    color: rgba(64, 80, 94, 0.76);
    font-size: 0.86rem;
    line-height: 1.55;
  }
  .pg-host-v2-poc[data-pg-v2-status="unavailable"] .pg-host-v2-subtitle {
    color: rgba(248, 244, 239, 0.76);
  }
  .pg-host-v2-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: flex-end;
  }
  .pg-host-v2-meta-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 10px;
    border-radius: 999px;
    color: rgba(58, 73, 87, 0.82);
    background: rgba(255, 255, 255, 0.6);
    border: 1px solid rgba(84, 129, 171, 0.12);
    font-size: 12px;
  }
  .pg-host-v2-action-buttons {
    display: flex;
    flex-wrap: wrap;
    justify-content: flex-end;
    gap: 8px;
  }
  .pg-host-v2-reset-button {
    border: 0;
    border-radius: 999px;
    background: linear-gradient(180deg, rgba(93, 134, 174, 0.92), rgba(72, 113, 154, 0.96));
    color: #f8f4ef;
    font-size: 0.76rem;
    font-weight: 700;
    padding: 9px 14px;
    cursor: pointer;
    white-space: nowrap;
    box-shadow: 0 12px 20px rgba(44, 61, 77, 0.12);
  }
  .pg-host-v2-reset-button:hover {
    filter: brightness(1.04);
  }
  .pg-host-v2-reset-button:disabled {
    cursor: default;
    opacity: 0.72;
    filter: none;
  }
  .pg-host-v2-layout {
    --pg-host-v2-side-width: 344px;
    display: grid;
    grid-template-columns: minmax(0, 1fr) 12px minmax(280px, var(--pg-host-v2-side-width));
    gap: 14px;
    flex: 1 1 auto;
    align-items: stretch;
    min-height: 0;
  }
  .pg-host-v2-graph-main {
    position: relative;
    display: grid;
    gap: 12px;
    min-height: 0;
  }
  .pg-host-v2-canvas-shell {
    position: relative;
    height: 100%;
    min-height: 0;
    overflow: hidden;
    border-radius: 18px;
    border: 1px solid rgba(84, 129, 171, 0.14);
    background:
      radial-gradient(circle at 20% 16%, rgba(255, 255, 255, 0.75), transparent 24%),
      radial-gradient(circle at 80% 22%, rgba(174, 211, 255, 0.22), transparent 28%),
      linear-gradient(180deg, rgba(252, 249, 243, 0.98) 0%, rgba(242, 236, 225, 0.96) 100%);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.68);
  }
  .pg-host-v2-graph-canvas {
    position: absolute;
    inset: 0;
  }
  .pg-host-v2-graph-canvas canvas {
    position: absolute;
    inset: 0;
  }
  .pg-host-v2-engine-status {
    position: absolute;
    right: 12px;
    bottom: 12px;
    z-index: 3;
    padding: 6px 10px;
    border-radius: 999px;
    color: rgba(47, 62, 76, 0.72);
    background: rgba(250, 247, 240, 0.78);
    border: 1px solid rgba(84, 129, 171, 0.12);
    font-size: 0.74rem;
    pointer-events: none;
    backdrop-filter: blur(12px);
  }
  .pg-host-v2-empty {
    display: grid;
    place-items: center;
    height: 100%;
    min-height: 420px;
    color: rgba(47, 62, 76, 0.72);
    font-size: 0.9rem;
  }
  .pg-host-v2-metrics-dock {
    position: absolute;
    top: 12px;
    left: 12px;
    z-index: 3;
    display: flex;
    align-items: flex-start;
    width: min(720px, calc(100% - 136px));
    min-height: 52px;
  }
  .pg-host-v2-config-collapsed-bar {
    position: absolute;
    top: 12px;
    right: 12px;
    z-index: 4;
    border: 0;
    border-radius: 999px;
    background: rgba(250, 247, 240, 0.92);
    color: #23303a;
    font-size: 0.76rem;
    font-weight: 700;
    letter-spacing: 0.02em;
    padding: 9px 14px;
    cursor: pointer;
    opacity: 0;
    pointer-events: none;
    transform: translateY(-6px);
    backdrop-filter: blur(14px);
    box-shadow: 0 16px 30px rgba(38, 49, 60, 0.14);
    transition: opacity 140ms ease, transform 140ms ease;
  }
  .pg-host-v2-config-collapsed-label {
    display: inline-block;
    white-space: nowrap;
    opacity: 1;
  }
  .pg-host-v2-config-title-text {
    color: #22303a;
    font-size: 0.86rem;
    font-weight: 700;
    line-height: 1.2;
    letter-spacing: 0.01em;
  }
  .pg-host-v2-config-collapsed-bar[data-pg-config-collapsed="true"] {
    opacity: 1;
    pointer-events: auto;
    transform: translateY(0);
  }
  .pg-host-v2-config-collapsed-bar[data-pg-config-morphing="true"] {
    opacity: 0;
    pointer-events: none;
    transform: translateY(0);
    transition: none;
  }
  .pg-host-v2-config-collapsed-bar[data-pg-config-morphing="true"] .pg-host-v2-config-collapsed-label {
    opacity: 0;
  }
  .pg-host-v2-side {
    position: relative;
    min-height: 0;
    display: grid;
    gap: 12px;
    overflow: auto;
    overflow-x: hidden;
    overscroll-behavior: contain;
    scrollbar-gutter: stable;
  }
  .pg-host-v2-side[data-pg-config-collapsed="false"] .pg-host-v2-config-card {
    opacity: 1;
    pointer-events: auto;
    transform: translateX(0) scale(1);
    box-shadow: 0 18px 34px rgba(38, 49, 60, 0.14);
  }
  .pg-host-v2-side[data-pg-config-collapsed="false"] .pg-host-v2-detail-card {
    opacity: 0.18;
    filter: blur(1.2px);
    transform: translateX(10px) scale(0.985);
    pointer-events: none;
  }
  .pg-host-v2-card {
    padding: 14px 16px;
    border-radius: 16px;
    border: 1px solid rgba(84, 129, 171, 0.12);
    background: rgba(255, 255, 255, 0.52);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.62);
    transition: opacity 180ms ease, transform 220ms cubic-bezier(0.2, 0.8, 0.2, 1), filter 220ms ease, box-shadow 220ms ease;
  }
  .pg-host-v2-card-title {
    margin: 0 0 8px;
    color: #22303a;
    font-size: 0.9rem;
    font-weight: 700;
  }
  .pg-host-v2-card-subtitle {
    margin: 0;
    color: rgba(71, 87, 101, 0.78);
    font-size: 0.8rem;
    line-height: 1.5;
  }
  .pg-host-v2-config-card {
    display: grid;
    gap: 12px;
    position: absolute;
    inset: 0;
    z-index: 2;
    overflow: auto;
    overflow-x: hidden;
    scrollbar-gutter: stable;
    background: rgba(249, 246, 239, 0.94);
    backdrop-filter: blur(16px);
    transform-origin: top right;
    opacity: 1;
    pointer-events: auto;
    transform: translateX(0) scale(1);
    will-change: transform, opacity, border-radius;
  }
  .pg-host-v2-config-card[data-pg-config-collapsed="true"] {
    opacity: 0;
    pointer-events: none;
    transform: none;
    box-shadow: 0 10px 18px rgba(38, 49, 60, 0.04);
  }
  .pg-host-v2-config-card[data-pg-config-morphing="true"],
  .pg-host-v2-detail-card[data-pg-config-morphing="true"] {
    transition: none;
  }
  .pg-host-v2-config-card[data-pg-config-collapsed="true"] .pg-host-v2-config-card-content {
    opacity: 0;
    transform: translateY(10px);
    pointer-events: none;
  }
  .pg-host-v2-config-card[data-pg-config-morphing="true"] .pg-host-v2-config-card-title {
    opacity: 0;
  }
  .pg-host-v2-config-card-head {
    display: flex;
    align-items: start;
    justify-content: space-between;
    gap: 12px;
  }
  .pg-host-v2-config-card-copy {
    min-width: 0;
  }
  .pg-host-v2-config-card-content {
    display: grid;
    gap: 12px;
    min-height: 100%;
    transition: opacity 150ms ease, transform 180ms ease;
  }
  .pg-host-v2-config-card-title {
    opacity: 1;
  }
  .pg-host-v2-config-title-ghost {
    position: fixed;
    top: 0;
    left: 0;
    z-index: 7;
    margin: 0;
    white-space: nowrap;
    pointer-events: none;
    opacity: 0;
  }
  .pg-host-v2-config-morph-proxy {
    position: fixed;
    z-index: 6;
    left: 0;
    top: 0;
    width: 0;
    height: 0;
    pointer-events: none;
    border: 1px solid rgba(84, 129, 171, 0.12);
    border-radius: 16px;
    background: rgba(249, 246, 239, 0.94);
    backdrop-filter: blur(16px);
    box-shadow: 0 18px 34px rgba(38, 49, 60, 0.14);
    transform-origin: top right;
  }
  .pg-host-v2-config-toggle {
    border: 0;
    border-radius: 999px;
    background: rgba(89, 127, 165, 0.14);
    color: #274057;
    font-size: 0.75rem;
    font-weight: 700;
    padding: 8px 12px;
    cursor: pointer;
    white-space: nowrap;
  }
  .pg-host-v2-config-toggle:hover {
    background: rgba(89, 127, 165, 0.22);
  }
  .pg-host-v2-config-section {
    border-radius: 14px;
    border: 1px solid rgba(84, 129, 171, 0.12);
    background: rgba(247, 243, 236, 0.68);
    padding: 12px 14px;
  }
  .pg-host-v2-config-summary {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    cursor: pointer;
    list-style: none;
    color: #22303a;
    font-size: 0.82rem;
    font-weight: 700;
  }
  .pg-host-v2-config-summary::-webkit-details-marker {
    display: none;
  }
  .pg-host-v2-config-summary::after {
    content: '+';
    color: rgba(70, 88, 104, 0.72);
    font-size: 1rem;
    line-height: 1;
    transition: transform 120ms ease;
  }
  .pg-host-v2-config-section[open] .pg-host-v2-config-summary::after {
    transform: rotate(45deg);
  }
  .pg-host-v2-config-body {
    display: grid;
    gap: 12px;
    padding-top: 12px;
  }
  .pg-host-v2-config-row {
    display: grid;
    gap: 6px;
  }
  .pg-host-v2-config-row-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
  }
  .pg-host-v2-config-label {
    color: #23303a;
    font-size: 0.78rem;
    font-weight: 600;
  }
  .pg-host-v2-config-value {
    color: rgba(70, 86, 101, 0.76);
    font-size: 0.72rem;
    font-variant-numeric: tabular-nums;
  }
  .pg-host-v2-config-range {
    width: 100%;
    margin: 0;
    accent-color: #5c84a8;
  }
  .pg-host-v2-config-hint {
    margin: 0;
    color: rgba(71, 87, 101, 0.72);
    font-size: 0.74rem;
    line-height: 1.5;
  }
  .pg-host-v2-config-button {
    justify-self: start;
    border: 0;
    border-radius: 12px;
    background: linear-gradient(180deg, rgba(93, 134, 174, 0.92), rgba(72, 113, 154, 0.96));
    color: #f8f4ef;
    font-size: 0.76rem;
    font-weight: 700;
    padding: 10px 14px;
    cursor: pointer;
    box-shadow: 0 12px 20px rgba(44, 61, 77, 0.12);
  }
  .pg-host-v2-config-button:hover {
    filter: brightness(1.04);
  }
  .pg-host-v2-color-group-list {
    display: grid;
    gap: 10px;
  }
  .pg-host-v2-color-group-row {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto auto;
    gap: 8px;
    align-items: center;
  }
  .pg-host-v2-color-group-actions {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .pg-host-v2-color-group-action {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    border: 1px solid rgba(84, 129, 171, 0.16);
    background: rgba(255, 255, 255, 0.84);
    color: rgba(61, 78, 94, 0.74);
    font-size: 0.88rem;
    cursor: pointer;
  }
  .pg-host-v2-color-group-action:hover {
    border-color: rgba(84, 129, 171, 0.24);
    color: #35516a;
  }
  .pg-host-v2-color-group-input {
    width: 100%;
    min-height: 36px;
    padding: 8px 10px;
    border-radius: 10px;
    border: 1px solid rgba(84, 129, 171, 0.16);
    background: rgba(255, 255, 255, 0.84);
    color: #22303a;
    font-size: 0.78rem;
  }
  .pg-host-v2-color-group-input::placeholder {
    color: rgba(71, 87, 101, 0.46);
  }
  .pg-host-v2-color-group-swatch {
    width: 38px;
    height: 36px;
    border-radius: 10px;
    border: 1px solid rgba(84, 129, 171, 0.16);
    background: rgba(255, 255, 255, 0.84);
    padding: 4px;
    cursor: pointer;
  }
  .pg-host-v2-color-group-remove {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    border: 1px solid rgba(84, 129, 171, 0.16);
    background: rgba(255, 255, 255, 0.84);
    color: rgba(61, 78, 94, 0.74);
    font-size: 1rem;
    cursor: pointer;
  }
  .pg-host-v2-color-group-remove:hover {
    color: #b95f57;
    border-color: rgba(185, 95, 87, 0.22);
  }
  .pg-host-v2-metrics {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }
  .pg-host-v2-metrics-inline {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    width: 100%;
    overflow: hidden;
    max-height: 160px;
    opacity: 1;
    transform: translateY(0);
    transition: max-height 160ms ease, opacity 160ms ease, transform 160ms ease, margin-bottom 160ms ease;
  }
  .pg-host-v2-metrics-inline[data-pg-metrics-collapsed="true"] {
    max-height: 0;
    opacity: 0;
    transform: translateY(-8px);
    pointer-events: none;
    margin-bottom: -12px;
  }
  .pg-host-v2-metrics-inline .pg-host-v2-metric {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 10px;
    padding: 10px 14px;
    border-radius: 999px;
  }
  .pg-host-v2-metrics-inline .pg-host-v2-metric-value {
    margin-top: 0;
    font-size: 0.96rem;
  }
  .pg-host-v2-metrics-side {
    display: none;
  }
  .pg-host-v2-resize-handle {
    position: relative;
    min-height: 100%;
    cursor: col-resize;
    border-radius: 999px;
    user-select: none;
    touch-action: none;
  }
  .pg-host-v2-resize-handle::before {
    content: '';
    position: absolute;
    top: 2px;
    bottom: 2px;
    left: 4px;
    right: 4px;
    border-radius: 999px;
    background: rgba(84, 129, 171, 0.14);
    transition: background 140ms ease;
  }
  .pg-host-v2-resize-handle:hover::before,
  .pg-host-v2-resize-handle[data-pg-dragging="true"]::before {
    background: rgba(84, 129, 171, 0.34);
  }
  .pg-host-v2-metric {
    padding: 12px 13px;
    border-radius: 14px;
    background: rgba(255, 255, 255, 0.54);
    border: 1px solid rgba(84, 129, 171, 0.12);
  }
  .pg-host-v2-metric-label {
    color: rgba(71, 87, 101, 0.74);
    font-size: 0.72rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }
  .pg-host-v2-metric-value {
    margin-top: 8px;
    color: #1d2c36;
    font-size: 1.12rem;
    font-weight: 700;
  }
  .pg-host-v2-detail-body {
    display: grid;
    gap: 10px;
  }
  .pg-host-v2-detail-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    min-width: 0;
  }
  .pg-host-v2-detail-head .pg-host-v2-card-title {
    margin: 0;
    min-width: 0;
  }
  .pg-host-v2-detail-clear {
    border: 1px solid rgba(84, 129, 171, 0.16);
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.68);
    color: rgba(43, 60, 76, 0.82);
    font-size: 0.72rem;
    font-weight: 700;
    padding: 7px 11px;
    cursor: pointer;
    white-space: nowrap;
    transition: opacity 140ms ease, border-color 140ms ease, background 140ms ease, color 140ms ease;
  }
  .pg-host-v2-detail-clear:hover:not(:disabled) {
    border-color: rgba(84, 129, 171, 0.28);
    background: rgba(255, 255, 255, 0.86);
    color: #274057;
  }
  .pg-host-v2-detail-clear:disabled {
    cursor: default;
    opacity: 0.42;
  }
  .pg-host-v2-detail-action {
    justify-self: start;
    min-height: 30px;
    padding: 6px 11px;
    border: 1px solid rgba(95, 83, 149, 0.24);
    border-radius: 999px;
    background: rgba(246, 243, 255, 0.92);
    color: #5f5395;
    font: inherit;
    font-size: 0.76rem;
    font-weight: 800;
    cursor: pointer;
  }
  .pg-host-v2-detail-action:hover,
  .pg-host-v2-detail-action:focus-visible {
    border-color: rgba(95, 83, 149, 0.42);
    background: #f7f4ff;
    color: #45358f;
  }
  .pg-host-v2-detail-empty,
  .pg-host-v2-detail-copy {
    margin: 0;
    color: rgba(71, 87, 101, 0.8);
    font-size: 0.82rem;
    line-height: 1.6;
  }
  .pg-host-v2-detail-chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
  .pg-host-v2-detail-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 999px;
    background: rgba(84, 129, 171, 0.1);
    border: 1px solid rgba(84, 129, 171, 0.12);
    color: rgba(44, 61, 77, 0.82);
    font-size: 11px;
    font-weight: 600;
  }
  .pg-host-v2-unavailable {
    padding: 18px;
    border-radius: 16px;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.08);
  }
  .pg-host-control-list {
    list-style: none;
    padding: 0;
    margin: 10px 0 0;
    display: grid;
    gap: 8px;
  }
  .pg-host-control-item {
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 10px 12px;
    background: rgba(255, 255, 255, 0.04);
  }
  .pg-host-control-item-title {
    color: #f8f4ef;
    font-size: 0.88rem;
    font-weight: 600;
  }
  .pg-host-control-item-meta {
    margin-top: 4px;
    color: rgba(248, 244, 239, 0.68);
    font-size: 0.78rem;
    line-height: 1.45;
  }
  .pg-host-evidence-card {
    display: grid;
    gap: 12px;
  }
  .pg-host-evidence-head {
    display: flex;
    align-items: start;
    justify-content: space-between;
    gap: 12px;
  }
  .pg-host-evidence-title-wrap {
    min-width: 0;
  }
  .pg-host-evidence-badge-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: flex-end;
  }
  .pg-host-evidence-badge {
    display: inline-flex;
    align-items: center;
    min-height: 24px;
    padding: 4px 9px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: rgba(248, 244, 239, 0.76);
    font-size: 0.72rem;
    font-weight: 700;
    white-space: nowrap;
  }
  .pg-host-evidence-badge[data-pg-evidence-status="ok"],
  .pg-host-evidence-badge[data-pg-evidence-status="completed"] {
    color: #87e1b5;
    background: rgba(95, 224, 170, 0.13);
    border-color: rgba(95, 224, 170, 0.22);
  }
  .pg-host-evidence-badge[data-pg-evidence-status="degraded"],
  .pg-host-evidence-badge[data-pg-evidence-status="partial"],
  .pg-host-evidence-badge[data-pg-evidence-status="permission-review"],
  .pg-host-evidence-badge[data-pg-evidence-status="unknown"] {
    color: #ffdc91;
    background: rgba(255, 217, 138, 0.13);
    border-color: rgba(255, 217, 138, 0.24);
  }
  .pg-host-evidence-badge[data-pg-evidence-status="failed"],
  .pg-host-evidence-badge[data-pg-evidence-status="read-error"] {
    color: #ffb5aa;
    background: rgba(255, 178, 166, 0.13);
    border-color: rgba(255, 178, 166, 0.24);
  }
  .pg-host-evidence-list {
    display: grid;
    gap: 10px;
  }
  .pg-host-evidence-run {
    display: grid;
    gap: 10px;
    padding: 12px 0 14px;
    border-top: 1px solid rgba(255, 255, 255, 0.09);
    background: transparent;
  }
  .pg-host-evidence-run[data-pg-evidence-severity="warning"] {
    border-top-color: rgba(255, 217, 138, 0.2);
  }
  .pg-host-evidence-run[data-pg-evidence-severity="error"] {
    border-top-color: rgba(255, 178, 166, 0.2);
  }
  .pg-host-evidence-run-head {
    display: flex;
    align-items: start;
    justify-content: space-between;
    gap: 12px;
  }
  .pg-host-evidence-run-title {
    margin: 0;
    color: #f8f4ef;
    font-size: 0.88rem;
    font-weight: 700;
    line-height: 1.35;
  }
  .pg-host-evidence-run-subtitle {
    margin: 3px 0 0;
    color: rgba(248, 244, 239, 0.66);
    font-size: 0.76rem;
    line-height: 1.45;
    overflow-wrap: anywhere;
  }
  .pg-host-evidence-facts {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(156px, 1fr));
    gap: 8px;
  }
  .pg-host-evidence-fact {
    display: grid;
    gap: 3px;
    min-width: 0;
    padding: 8px 10px;
    border-radius: 10px;
    background: rgba(255, 255, 255, 0.055);
  }
  .pg-host-evidence-label {
    color: rgba(248, 244, 239, 0.58);
    font-size: 0.68rem;
    font-weight: 800;
    letter-spacing: 0.04em;
    text-transform: uppercase;
  }
  .pg-host-evidence-value {
    color: rgba(248, 244, 239, 0.84);
    font-size: 0.76rem;
    line-height: 1.4;
    overflow-wrap: anywhere;
  }
  .pg-host-evidence-group {
    display: grid;
    gap: 6px;
  }
  .pg-host-evidence-group-title {
    margin: 0;
    color: rgba(248, 244, 239, 0.72);
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.03em;
    text-transform: uppercase;
  }
  .pg-host-evidence-chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 7px;
  }
  .pg-host-evidence-chip {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    max-width: 100%;
    padding: 4px 8px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.07);
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: rgba(248, 244, 239, 0.72);
    font-size: 0.72rem;
    overflow-wrap: anywhere;
  }
  .pg-host-evidence-chip span {
    min-width: 0;
    overflow-wrap: anywhere;
  }
  .pg-host-evidence-error-list {
    display: grid;
    gap: 8px;
  }
  .pg-host-evidence-error-row {
    display: grid;
    gap: 4px;
    padding: 9px 0 10px;
    border-top: 1px solid rgba(255, 178, 166, 0.22);
    background: transparent;
  }
  .pg-host-scheduler-operator-card {
    display: grid;
    gap: 12px;
  }
  .pg-host-scheduler-operator-head {
    display: flex;
    align-items: start;
    justify-content: space-between;
    gap: 12px;
  }
  .pg-host-scheduler-operator-actions,
  .pg-host-scheduler-candidate-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: flex-end;
  }
  .pg-host-scheduler-operator-button {
    min-height: 28px;
    border: 1px solid rgba(163, 218, 255, 0.2);
    border-radius: 999px;
    background: rgba(95, 164, 220, 0.18);
    color: #f8f4ef;
    padding: 5px 10px;
    font: inherit;
    font-size: 0.74rem;
    font-weight: 800;
    cursor: pointer;
    white-space: nowrap;
  }
  .pg-host-scheduler-operator-button:hover:not(:disabled) {
    background: rgba(95, 164, 220, 0.28);
    border-color: rgba(163, 218, 255, 0.34);
  }
  .pg-host-scheduler-operator-button:disabled {
    cursor: default;
    opacity: 0.5;
  }
  .pg-host-scheduler-operator-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(156px, 1fr));
    gap: 8px;
  }
  .pg-host-scheduler-cleanup-form {
    display: grid;
    gap: 8px;
    padding: 10px 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.045);
  }
  .pg-host-scheduler-cleanup-row {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 8px;
    align-items: center;
  }
  .pg-host-scheduler-cleanup-input {
    min-width: 0;
    min-height: 30px;
    border: 1px solid rgba(163, 218, 255, 0.18);
    border-radius: 8px;
    background: rgba(0, 0, 0, 0.16);
    color: #f8f4ef;
    padding: 5px 8px;
    font: inherit;
    font-size: 0.74rem;
  }
  .pg-host-scheduler-cleanup-input::placeholder {
    color: rgba(248, 244, 239, 0.42);
  }
  .pg-host-scheduler-select {
    min-width: 0;
    min-height: 30px;
    border: 1px solid rgba(163, 218, 255, 0.18);
    border-radius: 8px;
    background: rgba(0, 0, 0, 0.26);
    color: #f8f4ef;
    padding: 5px 8px;
    font: inherit;
    font-size: 0.74rem;
  }
  .pg-host-scheduler-workflow-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
    gap: 8px;
  }
  .pg-host-scheduler-field {
    display: grid;
    gap: 4px;
    min-width: 0;
  }
  .pg-host-scheduler-field label {
    color: rgba(248, 244, 239, 0.7);
    font-size: 0.68rem;
    font-weight: 800;
    text-transform: uppercase;
  }
  .pg-host-scheduler-field[data-pg-wide-field="true"] {
    grid-column: 1 / -1;
  }
  .pg-host-scheduler-field-hint {
    color: rgba(248, 244, 239, 0.52);
    font-size: 0.68rem;
    line-height: 1.35;
  }
  .pg-host-scheduler-workflow-details {
    display: grid;
    gap: 8px;
  }
  .pg-host-scheduler-workflow-details summary {
    color: rgba(248, 244, 239, 0.76);
    font-size: 0.72rem;
    font-weight: 800;
    cursor: pointer;
  }
  .pg-host-scheduler-workflow-details[open] {
    padding-top: 2px;
  }
  .pg-host-scheduler-cleanup-confirm {
    display: flex;
    gap: 7px;
    align-items: center;
    color: rgba(248, 244, 239, 0.74);
    font-size: 0.72rem;
    line-height: 1.4;
  }
  .pg-host-scheduler-cleanup-confirm input {
    margin: 0;
  }
  .pg-host-scheduler-cleanup-candidates {
    display: grid;
    gap: 7px;
  }
  .pg-host-scheduler-cleanup-candidate-list {
    display: grid;
    gap: 6px;
  }
  .pg-host-scheduler-cleanup-candidate {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 8px;
    align-items: center;
    padding: 7px 8px;
    border: 1px solid rgba(163, 218, 255, 0.14);
    border-radius: 8px;
    background: rgba(0, 0, 0, 0.14);
  }
  .pg-host-scheduler-cleanup-candidate-title {
    margin: 0;
    color: rgba(248, 244, 239, 0.9);
    font-size: 0.76rem;
    font-weight: 800;
  }
  .pg-host-scheduler-cleanup-candidate-meta {
    margin: 2px 0 0;
    color: rgba(248, 244, 239, 0.58);
    font-size: 0.68rem;
    line-height: 1.35;
    overflow-wrap: anywhere;
  }
  .pg-host-scheduler-cleanup-diff {
    display: grid;
    gap: 8px;
    padding: 8px;
    border: 1px solid rgba(163, 218, 255, 0.12);
    border-radius: 8px;
    background: rgba(0, 0, 0, 0.1);
  }
  .pg-host-scheduler-cleanup-diff-row {
    display: grid;
    gap: 7px;
    padding: 8px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.035);
  }
  .pg-host-scheduler-cleanup-diff-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 7px;
  }
  .pg-host-scheduler-cleanup-diff-fact {
    min-width: 0;
    padding: 6px 7px;
    border-radius: 7px;
    background: rgba(0, 0, 0, 0.13);
  }
  .pg-host-scheduler-cleanup-diff-label {
    color: rgba(248, 244, 239, 0.52);
    font-size: 0.64rem;
    font-weight: 800;
    text-transform: uppercase;
  }
  .pg-host-scheduler-cleanup-diff-value {
    margin-top: 2px;
    color: rgba(248, 244, 239, 0.86);
    font-size: 0.7rem;
    line-height: 1.35;
    overflow-wrap: anywhere;
  }
  .pg-host-scheduler-candidates {
    display: grid;
    gap: 9px;
  }
  .pg-host-scheduler-authorization {
    display: grid;
    gap: 10px;
    padding: 10px 12px;
    border: 1px solid rgba(163, 218, 255, 0.16);
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.045);
  }
  .pg-host-scheduler-candidate {
    display: grid;
    gap: 8px;
    padding: 10px 0 11px;
    border-top: 1px solid rgba(255, 255, 255, 0.09);
  }
  .pg-host-scheduler-auth-task {
    display: grid;
    gap: 7px;
    padding: 10px 0 11px;
    border-top: 1px solid rgba(255, 255, 255, 0.09);
  }
  .pg-host-scheduler-candidate-head {
    display: flex;
    align-items: start;
    justify-content: space-between;
    gap: 12px;
  }
  .pg-host-scheduler-candidate-title {
    margin: 0;
    color: #f8f4ef;
    font-size: 0.84rem;
    font-weight: 800;
    line-height: 1.35;
    overflow-wrap: anywhere;
  }
  .pg-host-scheduler-candidate-meta {
    margin: 3px 0 0;
    color: rgba(248, 244, 239, 0.66);
    font-size: 0.74rem;
    line-height: 1.45;
    overflow-wrap: anywhere;
  }
  .pg-host-scheduler-binding-section {
    display: grid;
    gap: 8px;
    padding: 9px 10px;
    border: 1px solid rgba(163, 218, 255, 0.12);
    border-radius: 10px;
    background: rgba(0, 0, 0, 0.12);
  }
  .pg-host-scheduler-binding-section[data-pg-binding-ok="true"] {
    border-color: rgba(95, 224, 170, 0.16);
  }
  .pg-host-scheduler-binding-section[data-pg-binding-ok="false"] {
    border-color: rgba(255, 178, 166, 0.22);
  }
  .pg-host-scheduler-binding-head {
    display: flex;
    align-items: start;
    justify-content: space-between;
    gap: 10px;
  }
  .pg-host-scheduler-binding-title {
    margin: 0;
    color: #f8f4ef;
    font-size: 0.75rem;
    font-weight: 800;
    line-height: 1.35;
  }
  .pg-host-scheduler-binding-meta {
    margin: 2px 0 0;
    color: rgba(248, 244, 239, 0.62);
    font-size: 0.68rem;
    line-height: 1.4;
    overflow-wrap: anywhere;
  }
  .pg-host-scheduler-binding-task-list {
    display: grid;
    gap: 7px;
  }
  .pg-host-scheduler-binding-task {
    display: grid;
    gap: 5px;
    padding-top: 7px;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
  }
  .pg-host-scheduler-binding-task-title {
    margin: 0;
    color: rgba(248, 244, 239, 0.82);
    font-size: 0.7rem;
    font-weight: 800;
    overflow-wrap: anywhere;
  }
  .pg-host-scheduler-binding-ref-row {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
  }
  .pg-host-scheduler-action-result {
    display: grid;
    gap: 7px;
    padding: 10px 12px;
    border-radius: 11px;
    background: rgba(255, 255, 255, 0.055);
    border: 1px solid rgba(255, 255, 255, 0.08);
  }
  .pg-host-scheduler-action-result[data-pg-action-status="succeeded"] {
    border-color: rgba(95, 224, 170, 0.18);
  }
  .pg-host-scheduler-action-result[data-pg-action-status="failed"] {
    border-color: rgba(255, 178, 166, 0.22);
  }
  .pg-host-scheduler-output {
    max-height: 140px;
    margin: 0;
    padding: 8px 10px;
    overflow: auto;
    border-radius: 8px;
    background: rgba(0, 0, 0, 0.18);
    color: rgba(248, 244, 239, 0.78);
    font-family: ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace;
    font-size: 0.7rem;
    line-height: 1.45;
    white-space: pre-wrap;
  }
  .graph-section {
    position: relative;
    border-radius: 18px;
  }
  .graph-section svg {
    overflow: visible;
  }
  .graph-section[data-pg-graph-mode="obsidianish"] {
    border: 1px solid rgba(121, 152, 182, 0.14);
    background:
      radial-gradient(circle at top, rgba(120, 187, 255, 0.11), transparent 40%),
      radial-gradient(circle at bottom right, rgba(104, 255, 203, 0.06), transparent 28%),
      linear-gradient(180deg, rgba(255, 252, 245, 0.96) 0%, rgba(247, 243, 235, 0.94) 100%);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.42), 0 18px 34px rgba(57, 49, 38, 0.08);
  }
  .graph-section[data-pg-graph-mode="obsidianish"] h2 {
    color: #25313b;
  }
  .graph-section[data-pg-graph-mode="obsidianish"] .subtle,
  .graph-section[data-pg-graph-mode="obsidianish"] .filter-summary,
  .graph-section[data-pg-graph-mode="obsidianish"] .zoom-hint,
  .graph-section[data-pg-graph-mode="obsidianish"] .zoom-level {
    color: rgba(88, 102, 118, 0.82);
  }
  .graph-section[data-pg-graph-mode="obsidianish"] .svg-wrap {
    border-color: rgba(121, 152, 182, 0.14);
    background: linear-gradient(180deg, rgba(255, 253, 249, 0.96) 0%, rgba(245, 240, 231, 0.94) 100%);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.54);
  }
  .graph-section[data-pg-graph-mode="obsidianish"] svg {
    background:
      radial-gradient(circle at top, rgba(123, 188, 255, 0.08), transparent 38%),
      linear-gradient(180deg, rgba(255, 253, 249, 1) 0%, rgba(246, 241, 232, 0.98) 100%);
  }
  .graph-section[data-pg-graph-mode="obsidianish"] .interactive-node,
  .graph-section[data-pg-graph-mode="obsidianish"] .ready-item,
  .graph-section[data-pg-graph-mode="obsidianish"] .edge.interactive-edge {
    transition: opacity 180ms ease, filter 180ms ease, transform 180ms ease, stroke 180ms ease, fill 180ms ease;
  }
  .graph-section[data-pg-graph-mode="obsidianish"] .interactive-node {
    cursor: pointer;
    transform-origin: center;
  }
  .graph-section[data-pg-graph-mode="obsidianish"] .interactive-node .node-shape {
    stroke: rgba(54, 73, 91, 0.22);
    stroke-width: 1.3;
    filter: drop-shadow(0 8px 16px rgba(73, 93, 116, 0.08));
  }
  .graph-section[data-pg-graph-mode="obsidianish"] .interactive-node .node-shape.node-pending {
    fill: rgba(191, 157, 84, 0.24);
  }
  .graph-section[data-pg-graph-mode="obsidianish"] .interactive-node .node-shape.node-in-progress {
    fill: rgba(87, 146, 224, 0.32);
  }
  .graph-section[data-pg-graph-mode="obsidianish"] .interactive-node .node-shape.node-blocked {
    fill: rgba(197, 101, 91, 0.26);
  }
  .graph-section[data-pg-graph-mode="obsidianish"] .interactive-node .node-shape.node-completed {
    fill: rgba(90, 160, 118, 0.26);
  }
  .graph-section[data-pg-graph-mode="obsidianish"] .interactive-node .node-shape.node-archived {
    fill: rgba(123, 132, 146, 0.22);
  }
  .graph-section[data-pg-graph-mode="obsidianish"] .interactive-node .node-label {
    fill: rgba(30, 39, 46, 0.9);
    paint-order: stroke fill;
    stroke: rgba(255, 252, 247, 0.66);
    stroke-width: 0.9px;
    stroke-linejoin: round;
  }
  .graph-section[data-pg-graph-mode="obsidianish"] .interactive-node .node-sub {
    fill: rgba(86, 100, 115, 0.78);
    paint-order: stroke fill;
    stroke: rgba(255, 252, 247, 0.58);
    stroke-width: 0.55px;
    stroke-linejoin: round;
  }
  .graph-section[data-pg-graph-mode="obsidianish"] .interactive-node.pg-runtime-bound .node-shape {
    stroke: rgba(77, 134, 175, 0.42);
    filter: drop-shadow(0 10px 18px rgba(93, 151, 194, 0.14));
  }
  .graph-section[data-pg-graph-mode="obsidianish"] .edge.interactive-edge {
    opacity: 0.56;
    stroke-width: 1.7;
    filter: drop-shadow(0 2px 4px rgba(93, 118, 146, 0.08));
  }
  .graph-section[data-pg-graph-mode="obsidianish"] .interactive-node:hover .node-shape,
  .graph-section[data-pg-graph-mode="obsidianish"] .interactive-node:focus-visible .node-shape {
    stroke: rgba(163, 218, 255, 0.62);
    stroke-width: 1.5;
    filter: drop-shadow(0 0 12px rgba(110, 184, 255, 0.22));
  }
  .graph-section[data-pg-graph-mode="obsidianish"] .ready-item {
    background: rgba(109, 141, 170, 0.06);
    border-color: rgba(109, 141, 170, 0.14);
  }
  .graph-section[data-pg-graph-mode="obsidianish"][data-pg-focus-active="true"] .interactive-node:not(.pg-is-selected):not(.pg-is-related),
  .graph-section[data-pg-graph-mode="obsidianish"][data-pg-focus-active="true"] .ready-item:not(.pg-is-selected):not(.pg-is-related) {
    opacity: 0.32;
  }
  .graph-section[data-pg-graph-mode="obsidianish"][data-pg-focus-active="true"] .edge.interactive-edge:not(.pg-is-selected):not(.pg-is-related) {
    opacity: 0.1;
  }
  .graph-section[data-pg-graph-mode="obsidianish"] .interactive-node.pg-is-selected {
    transform: translateY(-1px);
  }
  .graph-section[data-pg-graph-mode="obsidianish"] .interactive-node.pg-is-selected .node-shape {
    stroke: rgba(163, 218, 255, 0.92);
    stroke-width: 1.95;
    filter: drop-shadow(0 0 16px rgba(110, 184, 255, 0.24));
  }
  .graph-section[data-pg-graph-mode="obsidianish"] .interactive-node.pg-is-related .node-shape {
    stroke: rgba(132, 169, 201, 0.58);
    filter: drop-shadow(0 0 10px rgba(110, 184, 255, 0.12));
  }
  .graph-section[data-pg-graph-mode="obsidianish"] .edge.interactive-edge.pg-is-selected,
  .graph-section[data-pg-graph-mode="obsidianish"] .edge.interactive-edge.pg-is-related {
    opacity: 0.94;
    stroke: rgba(86, 144, 191, 0.9);
    filter: drop-shadow(0 0 8px rgba(110, 184, 255, 0.16));
  }
  .graph-section[data-pg-graph-mode="obsidianish"] .ready-item.pg-is-selected,
  .graph-section[data-pg-graph-mode="obsidianish"] .ready-item.pg-is-related {
    border-color: rgba(86, 144, 191, 0.28);
    background: rgba(86, 144, 191, 0.1);
  }
  @media (max-width: 760px) {
    .pg-host-topbar {
      display: grid;
    }
    .pg-host-actions {
      justify-content: flex-start;
    }
    .pg-host-floating-bar {
      left: 10px;
      right: 10px;
      justify-content: flex-start;
      overflow-x: auto;
      transform: translateY(-10px);
    }
    .pg-host-floating-zone[data-pg-floating-visible="true"] .pg-host-floating-bar,
    .pg-host-floating-bar:focus-within {
      transform: translateY(0);
    }
    .pg-host-control-grid {
      grid-template-columns: 1fr;
    }
    .pg-host-v2-head,
    .pg-host-v2-layout {
      display: grid;
      grid-template-columns: 1fr;
    }
    .pg-host-preview-tabs {
      --pg-host-preview-panel-height: clamp(520px, 68vh, 760px);
    }
    .pg-host-tab-panel {
      min-height: calc(var(--pg-host-preview-panel-height) + 30px);
    }
    .pg-host-v2-poc {
      height: var(--pg-host-preview-panel-height);
      min-height: 0;
    }
    .pg-host-v2-head-actions,
    .pg-host-v2-meta {
      align-items: flex-start;
      justify-content: flex-start;
    }
    .pg-host-v2-canvas-shell {
      min-height: 0;
    }
    .pg-host-v2-config-collapsed-bar {
      top: 10px;
      right: 10px;
    }
    .pg-host-v2-metrics-dock {
      top: 10px;
      left: 10px;
      width: calc(100% - 96px);
    }
    .pg-host-v2-resize-handle {
      display: none;
    }
    .pg-host-v2-metrics-inline {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .pg-host-v2-metrics {
      grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    }
  }
</style>`;
  const hostShell = `<section class="pg-host-shell">
  <div class="pg-host-topbar">
    <div class="pg-host-title-group">
      <div class="pg-host-status-badge ${state.freshness}">${escapedFreshnessLabel}</div>
      <h1 class="pg-host-title">Progress Graph</h1>
      <div class="pg-host-subtitle">artifact: ${escapedPath}</div>
      <div class="pg-host-meta-row">${freshnessMeta}</div>
    </div>
  </div>
  <div class="pg-host-status-strip">
    <p class="pg-host-status-message">${escapedFreshnessMessage}</p>
    ${refreshError}
  </div>
</section>`;
  const hostChrome = `<div id="pgHostChromeDock" class="pg-host-chrome-dock" data-pg-host-shell="expanded" data-pg-host-shell-peek="hidden">
  <div id="pgHostFloatingZone" class="pg-host-floating-zone" data-pg-floating-visible="false">
    <nav class="pg-host-floating-bar" aria-label="Progress preview views">
      <button id="pgHostTabChecklist" type="button" class="pg-host-tab-button" role="tab" aria-selected="true" aria-controls="pgHostChecklistPanel" data-pg-tab-target="checklist">Checklist</button>
      <button id="pgHostTabTrajectory" type="button" class="pg-host-tab-button" role="tab" aria-selected="false" aria-controls="pgHostTrajectoryPanel" data-pg-tab-target="trajectory">Trajectory</button>
      <button id="pgHostRefreshButton" type="button" class="pg-host-floating-action" ${state.isRefreshRunning ? 'disabled' : ''}>${state.isRefreshRunning ? 'Refreshing...' : 'Refresh'}</button>
      <button id="pgHostRevealButton" type="button" class="pg-host-floating-action">Reveal</button>
      <button id="pgHostCollapsePanel" type="button" class="pg-host-floating-action" aria-expanded="true">hide panel</button>
      <button id="pgHostChromePeek" type="button" class="pg-host-floating-action" data-pg-panel-show="true" data-pg-visible="true" aria-controls="pgHostChromeContent" aria-expanded="true">show panal</button>
    </nav>
  </div>
  <div id="pgHostChromeContent" class="pg-host-chrome-content">
    ${hostShell}
    ${controlOverlay}
  </div>
</div>`;
  const v2GraphScript = state.v2GraphPayload && state.v2GraphScriptUri
    ? `<script src="${escapeHtml(state.v2GraphScriptUri)}"></script>`
    : '';
  const localWorkTrajectoryScript = state.localWorkTrajectoryScriptUri
    ? `<script src="${escapeHtml(state.localWorkTrajectoryScriptUri)}"></script>`
    : '';
  const hostScript = `<script>
  const vscode = acquireVsCodeApi();
  globalThis.__pgHostVsCodeApi = vscode;
  const clampNumber = (value, min, max) => Math.min(max, Math.max(min, value));
  const hostChromeDock = document.getElementById('pgHostChromeDock');
  const hostChromeContent = document.getElementById('pgHostChromeContent');
  const hostChromePeek = document.getElementById('pgHostChromePeek');
  const hostFloatingZone = document.getElementById('pgHostFloatingZone');
  const collapsePanelButton = document.getElementById('pgHostCollapsePanel');
  document.getElementById('pgHostRefreshButton')?.addEventListener('click', (event) => {
    const button = event.currentTarget;
    if (button instanceof HTMLButtonElement) {
      button.disabled = true;
      button.textContent = 'Refreshing...';
    }
    vscode.postMessage({ command: 'refresh' });
  });
  document.getElementById('pgHostRevealButton')?.addEventListener('click', () => {
    vscode.postMessage({ command: 'revealArtifact' });
  });
  for (const button of document.querySelectorAll('[data-pg-cleanup-evidence-select]')) {
    button.addEventListener('click', (event) => {
      const target = event.currentTarget;
      const evidencePathInput = document.getElementById('pgHostCleanupEvidencePath');
      if (!(target instanceof HTMLButtonElement) || !(evidencePathInput instanceof HTMLInputElement)) {
        return;
      }
      evidencePathInput.value = target.dataset.pgCleanupEvidencePath || '';
      evidencePathInput.dispatchEvent(new Event('input', { bubbles: true }));
      evidencePathInput.focus();
    });
  }
  for (const button of document.querySelectorAll('[data-pg-workflow-evidence-prefill]')) {
    button.addEventListener('click', (event) => {
      const target = event.currentTarget;
      const evidenceIdInput = document.getElementById('pgHostSandboxWorkflowAllocationEvidenceId');
      const evidencePathInput = document.getElementById('pgHostSandboxWorkflowAllocationEvidencePath');
      if (
        !(target instanceof HTMLButtonElement)
        || !(evidenceIdInput instanceof HTMLInputElement)
        || !(evidencePathInput instanceof HTMLInputElement)
      ) {
        return;
      }
      evidenceIdInput.value = target.dataset.pgWorkflowEvidenceId || '';
      evidencePathInput.value = target.dataset.pgWorkflowEvidencePath || '';
      evidenceIdInput.dispatchEvent(new Event('input', { bubbles: true }));
      evidencePathInput.dispatchEvent(new Event('input', { bubbles: true }));
      evidencePathInput.focus();
    });
  }
  const readTextInput = (id) => {
    const input = document.getElementById(id);
    return input instanceof HTMLInputElement ? input.value.trim() : '';
  };
  const readCheckbox = (id) => {
    const input = document.getElementById(id);
    return input instanceof HTMLInputElement ? input.checked : false;
  };
  const readSelectValue = (id) => {
    const select = document.getElementById(id);
    return select instanceof HTMLSelectElement ? select.value : '';
  };
  const isPositiveIntegerText = (value) => /^[1-9]\\d*$/.test(value);
  const focusFirstMissingInput = (ids) => {
    for (const id of ids) {
      const input = document.getElementById(id);
      if (input instanceof HTMLInputElement && !input.value.trim()) {
        input.focus();
        return true;
      }
    }
    return false;
  };
  for (const button of document.querySelectorAll('[data-pg-scheduler-action]')) {
    button.addEventListener('click', (event) => {
      const target = event.currentTarget;
      if (!(target instanceof HTMLButtonElement)) {
        return;
      }
      const action = target.dataset.pgSchedulerAction || '';
      const evidencePathInput = document.getElementById('pgHostCleanupEvidencePath');
      const cleanupConfirmInput = document.getElementById('pgHostCleanupConfirm');
      const evidencePath = evidencePathInput instanceof HTMLInputElement ? evidencePathInput.value.trim() : '';
      const cleanupConfirmed = cleanupConfirmInput instanceof HTMLInputElement ? cleanupConfirmInput.checked : false;
      if (action === 'cleanupReceipts' && (!evidencePath || !cleanupConfirmed)) {
        if (cleanupConfirmInput instanceof HTMLInputElement) {
          cleanupConfirmInput.focus();
        }
        return;
      }
      const workflowCleanup = readCheckbox('pgHostSandboxWorkflowCleanup');
      const workflowMode = readSelectValue('pgHostSandboxWorkflowMode') || 'run-once';
      const workflowPayload = {
        workflowMode,
        workspaceRoot: readTextInput('pgHostSandboxWorkflowWorkspaceRoot'),
        gitWorktreeSandboxRoot: readTextInput('pgHostSandboxWorkflowSandboxRoot'),
        allocationEvidenceId: readTextInput('pgHostSandboxWorkflowAllocationEvidenceId'),
        allocationEvidencePath: readTextInput('pgHostSandboxWorkflowAllocationEvidencePath'),
        maxTicks: workflowMode === 'daemon-loop' ? readTextInput('pgHostSandboxWorkflowMaxTicks') : '',
        maxRunsPerTick: workflowMode === 'daemon-loop' ? readTextInput('pgHostSandboxWorkflowMaxRunsPerTick') : '',
        maxRuntimeFailures: workflowMode === 'daemon-loop' ? readTextInput('pgHostSandboxWorkflowMaxRuntimeFailures') : '',
        cleanup: workflowCleanup,
        cleanupEvidenceId: workflowCleanup ? readTextInput('pgHostSandboxWorkflowCleanupEvidenceId') : '',
        cleanupEvidencePath: workflowCleanup ? readTextInput('pgHostSandboxWorkflowCleanupEvidencePath') : '',
      };
      if (action === 'runSandboxReceiptWorkflow') {
        if (workflowCleanup) {
          const cleanupDetails = document.getElementById('pgHostSandboxWorkflowCleanupDetails');
          if (cleanupDetails instanceof HTMLDetailsElement) {
            cleanupDetails.open = true;
          }
        }
        const missing = [
          'pgHostSandboxWorkflowWorkspaceRoot',
          'pgHostSandboxWorkflowSandboxRoot',
          'pgHostSandboxWorkflowAllocationEvidenceId',
          ...(workflowCleanup ? [
            'pgHostSandboxWorkflowCleanupEvidenceId',
            'pgHostSandboxWorkflowCleanupEvidencePath',
          ] : []),
        ];
        if (focusFirstMissingInput(missing)) {
          return;
        }
        if (workflowMode === 'daemon-loop') {
          const daemonBounds = [
            'pgHostSandboxWorkflowMaxTicks',
            'pgHostSandboxWorkflowMaxRunsPerTick',
            'pgHostSandboxWorkflowMaxRuntimeFailures',
          ];
          if (focusFirstMissingInput(daemonBounds)) {
            return;
          }
          for (const id of daemonBounds) {
            const input = document.getElementById(id);
            if (input instanceof HTMLInputElement && !isPositiveIntegerText(input.value.trim())) {
              input.focus();
              return;
            }
          }
        }
      }
      target.disabled = true;
      target.textContent = action === 'admit'
        ? 'Admitting...'
        : action === 'runLoop'
          ? 'Running...'
          : action === 'cleanupReceipts'
            ? 'Cleaning...'
            : action === 'runSandboxReceiptWorkflow'
              ? 'Running workflow...'
              : 'Refreshing...';
      vscode.postMessage({
        command: 'schedulerOperatorAction',
        action,
        artifactId: target.dataset.pgArtifactId || '',
        version: target.dataset.pgVersion || '',
        inspectBindingRefs: target.dataset.pgInspectBindingRefs === 'true',
        evidencePath,
        confirmed: cleanupConfirmed,
        ...workflowPayload,
      });
    });
  }
  if (hostChromeDock instanceof HTMLDivElement && hostChromeContent instanceof HTMLDivElement && hostChromePeek instanceof HTMLButtonElement) {
    const stateKey = 'pgHostChromeCollapsed';
    let collapsed = Boolean(vscode.getState()?.[stateKey]);

    const syncHostChromeHeight = () => {
      hostChromeDock.style.setProperty('--pg-host-chrome-expanded-height', String(Math.ceil(hostChromeContent.scrollHeight)) + 'px');
    };

    const setPeekVisible = (visible) => {
      hostChromeDock.dataset.pgHostShellPeek = collapsed && visible ? 'visible' : 'hidden';
      hostChromePeek.setAttribute('aria-hidden', collapsed && visible ? 'false' : 'true');
    };

    const setFloatingVisible = (visible) => {
      if (hostFloatingZone instanceof HTMLDivElement) {
        hostFloatingZone.dataset.pgFloatingVisible = visible ? 'true' : 'false';
      }
      setPeekVisible(visible);
    };

    const persistHostChromeState = () => {
      const currentState = vscode.getState?.() ?? {};
      vscode.setState?.({ ...currentState, [stateKey]: collapsed });
    };

    const applyHostChromeState = () => {
      syncHostChromeHeight();
      hostChromeDock.dataset.pgHostShell = collapsed ? 'collapsed' : 'expanded';
      hostChromePeek.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
      collapsePanelButton?.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
      if (collapsePanelButton instanceof HTMLButtonElement) {
        collapsePanelButton.textContent = collapsed ? 'panel hidden' : 'hide panel';
      }
      if (hostChromePeek instanceof HTMLButtonElement) {
        hostChromePeek.dataset.pgVisible = collapsed ? 'true' : 'false';
      }
      setFloatingVisible(false);
    };

    const setHostChromeCollapsed = (nextCollapsed) => {
      collapsed = nextCollapsed;
      applyHostChromeState();
      persistHostChromeState();
    };

    collapsePanelButton?.addEventListener('click', () => {
      setHostChromeCollapsed(true);
    });
    hostChromePeek.addEventListener('click', () => {
      setHostChromeCollapsed(false);
    });
    document.addEventListener('pointermove', (event) => {
      setFloatingVisible(event.clientY <= 56);
    });
    document.addEventListener('pointerleave', () => {
      setFloatingVisible(false);
    });
    window.addEventListener('resize', applyHostChromeState);
    if (typeof ResizeObserver === 'function') {
      const hostChromeObserver = new ResizeObserver(() => {
        syncHostChromeHeight();
      });
      hostChromeObserver.observe(hostChromeContent);
    }
    applyHostChromeState();
  }
  (() => {
    const tabs = Array.from(document.querySelectorAll('[data-pg-tab-target]'));
    const tabsRoot = document.getElementById('pgHostPreviewTabs');
    const heightHandle = document.getElementById('pgHostPreviewHeightHandle');
    const locateTrajectoryParentButton = document.getElementById('pgHostLocateTrajectoryParent');
    const panels = {
      checklist: document.getElementById('pgHostChecklistPanel'),
      trajectory: document.getElementById('pgHostTrajectoryPanel'),
    };
    const stateKey = 'pgHostActivePreviewTab';
    const heightStateKey = 'pgHostPreviewPanelHeight';
    const minPanelHeight = 520;
    const maxPanelHeight = 1200;

    const persistPreviewState = (patch) => {
      const currentState = vscode.getState?.() ?? {};
      vscode.setState?.({ ...currentState, ...patch });
    };

    const panelHeightFromState = () => {
      const rawHeight = Number(vscode.getState?.()?.[heightStateKey]);
      return Number.isFinite(rawHeight) ? clampNumber(rawHeight, minPanelHeight, maxPanelHeight) : null;
    };

    const applyPanelHeight = (height) => {
      if (!(tabsRoot instanceof HTMLElement)) {
        return;
      }
      const nextHeight = clampNumber(Math.round(height), minPanelHeight, maxPanelHeight);
      tabsRoot.style.setProperty('--pg-host-preview-panel-height', String(nextHeight) + 'px');
      if (heightHandle instanceof HTMLElement) {
        heightHandle.setAttribute('aria-valuenow', String(nextHeight));
      }
      requestAnimationFrame(() => {
        window.dispatchEvent(new Event('resize'));
      });
    };

    const readAppliedPanelHeight = () => {
      const handleHeight = Number(heightHandle?.getAttribute('aria-valuenow'));
      if (Number.isFinite(handleHeight)) {
        return clampNumber(handleHeight, minPanelHeight, maxPanelHeight);
      }
      const stateHeight = panelHeightFromState();
      if (stateHeight !== null) {
        return stateHeight;
      }
      if (tabsRoot instanceof HTMLElement) {
        const cssHeight = Number.parseFloat(getComputedStyle(tabsRoot).getPropertyValue('--pg-host-preview-panel-height'));
        if (Number.isFinite(cssHeight)) {
          return clampNumber(cssHeight, minPanelHeight, maxPanelHeight);
        }
        const activePanel = Object.values(panels).find((panel) => panel instanceof HTMLElement && !panel.hidden);
        if (activePanel instanceof HTMLElement) {
          const activeBody = activePanel.querySelector('.pg-host-v2-poc, .pg-host-lwt-mount-section');
          const rectHeight = activeBody instanceof HTMLElement ? activeBody.getBoundingClientRect().height : activePanel.getBoundingClientRect().height;
          if (Number.isFinite(rectHeight) && rectHeight > 0) {
            return clampNumber(rectHeight, minPanelHeight, maxPanelHeight);
          }
        }
      }
      return 760;
    };

    const initialPanelHeight = panelHeightFromState();
    if (initialPanelHeight !== null) {
      applyPanelHeight(initialPanelHeight);
    }

    const setActiveTab = (nextTab) => {
      const activeTab = nextTab === 'trajectory' ? 'trajectory' : 'checklist';
      for (const tab of tabs) {
        const selected = tab.getAttribute('data-pg-tab-target') === activeTab;
        tab.setAttribute('aria-selected', selected ? 'true' : 'false');
      }
      for (const [panelName, panel] of Object.entries(panels)) {
        if (panel instanceof HTMLElement) {
          panel.hidden = panelName !== activeTab;
        }
      }
      persistPreviewState({ [stateKey]: activeTab });
      requestAnimationFrame(() => {
        window.dispatchEvent(new Event('resize'));
      });
    };
    for (const tab of tabs) {
      tab.addEventListener('click', () => {
        setActiveTab(tab.getAttribute('data-pg-tab-target') || 'checklist');
      });
    }
    window.addEventListener('pg-host-open-trajectory', () => {
      setActiveTab('trajectory');
    });
    window.addEventListener('pg-host-locate-trajectory-parent', (event) => {
      const detail = event instanceof CustomEvent && event.detail && typeof event.detail === 'object'
        ? event.detail
        : {};
      const nodeId = typeof detail.nodeId === 'string' ? detail.nodeId : '';
      const graphId = typeof detail.graphId === 'string' ? detail.graphId : '';
      if (!nodeId) {
        return;
      }
      setActiveTab('checklist');
      requestAnimationFrame(() => {
        window.dispatchEvent(new CustomEvent('pg-host-select-graph-node', {
          detail: { graphId, nodeId },
        }));
      });
    });
    locateTrajectoryParentButton?.addEventListener('click', () => {
      if (!(locateTrajectoryParentButton instanceof HTMLElement)) {
        return;
      }
      const graphId = locateTrajectoryParentButton.getAttribute('data-pg-source-graph-id') || '';
      const nodeId = locateTrajectoryParentButton.getAttribute('data-pg-source-node-id') || '';
      if (!nodeId) {
        return;
      }
      window.dispatchEvent(new CustomEvent('pg-host-locate-trajectory-parent', {
        detail: { graphId, nodeId },
      }));
    });
    if (heightHandle instanceof HTMLElement) {
      heightHandle.addEventListener('pointerdown', (event) => {
        event.preventDefault();
        const startY = event.clientY;
        const startHeight = readAppliedPanelHeight();
        heightHandle.dataset.pgDragging = 'true';
        heightHandle.setPointerCapture?.(event.pointerId);
        document.body.style.cursor = 'row-resize';
        document.body.style.userSelect = 'none';

        const handlePointerMove = (moveEvent) => {
          const nextHeight = clampNumber(startHeight + moveEvent.clientY - startY, minPanelHeight, maxPanelHeight);
          applyPanelHeight(nextHeight);
        };

        const stopDragging = () => {
          heightHandle.dataset.pgDragging = 'false';
          document.body.style.cursor = '';
          document.body.style.userSelect = '';
          const currentHeight = Number(heightHandle.getAttribute('aria-valuenow'));
          if (Number.isFinite(currentHeight)) {
            persistPreviewState({ [heightStateKey]: currentHeight });
          }
          window.removeEventListener('pointermove', handlePointerMove);
          window.removeEventListener('pointerup', stopDragging);
          window.removeEventListener('pointercancel', stopDragging);
        };

        window.addEventListener('pointermove', handlePointerMove);
        window.addEventListener('pointerup', stopDragging);
        window.addEventListener('pointercancel', stopDragging);
      });
      heightHandle.addEventListener('keydown', (event) => {
        const currentHeight = readAppliedPanelHeight();
        let nextHeight = currentHeight;
        if (event.key === 'ArrowDown') {
          nextHeight += 20;
        } else if (event.key === 'ArrowUp') {
          nextHeight -= 20;
        } else if (event.key === 'PageDown') {
          nextHeight += 80;
        } else if (event.key === 'PageUp') {
          nextHeight -= 80;
        } else if (event.key === 'Home') {
          nextHeight = minPanelHeight;
        } else if (event.key === 'End') {
          nextHeight = maxPanelHeight;
        } else {
          return;
        }
        event.preventDefault();
        applyPanelHeight(nextHeight);
        const appliedHeight = Number(heightHandle.getAttribute('aria-valuenow'));
        if (Number.isFinite(appliedHeight)) {
          persistPreviewState({ [heightStateKey]: appliedHeight });
        }
      });
    }
    setActiveTab(vscode.getState?.()?.[stateKey] || 'checklist');
  })();
  ${buildControlOverlayEnhancementScript()}
</script>`;

  return injectIntoHtmlDocument(previewHtml, {
    beforeHeadClose: `${hostStyle}\n${localWorkTrajectoryStyle}`,
    afterBodyOpen: `${hostChrome}\n${previewPanels}`,
    beforeBodyClose: `${hostScript}\n${v2GraphScript}\n${localWorkTrajectoryScript}`,
  });
}

function buildPreviewTabPanels(v2GraphPoC: string, trajectoryPanel: string): string {
  return `<main id="pgHostPreviewTabs" class="pg-host-preview-tabs">
  <section id="pgHostChecklistPanel" class="pg-host-tab-panel" role="tabpanel" aria-labelledby="pgHostTabChecklist">
    ${v2GraphPoC}
  </section>
  <section id="pgHostTrajectoryPanel" class="pg-host-tab-panel" role="tabpanel" aria-labelledby="pgHostTabTrajectory" hidden>
    ${trajectoryPanel}
  </section>
  <div id="pgHostPreviewHeightHandle" class="pg-host-preview-height-handle" role="slider" aria-label="Resize Checklist and Trajectory panel height" aria-orientation="vertical" aria-valuemin="520" aria-valuemax="1200" aria-valuenow="760" tabindex="0" data-pg-dragging="false"></div>
</main>`;
}

function buildV2GraphPoCSection(state: ProgressGraphPreviewState): string {
  if (!state.v2GraphPayload || !state.v2GraphScriptUri) {
    return `<section class="pg-host-v2-poc" data-pg-v2-status="unavailable">
  <div class="pg-host-v2-head">
    <div class="pg-host-v2-title-wrap">
      <div class="pg-host-v2-eyebrow">Knowledge Graph Engine</div>
      <h2 class="pg-host-v2-title">V2 Graph View PoC 未就绪</h2>
      <p class="pg-host-v2-subtitle">${escapeHtml(v2GraphUnavailableMessage(state))}</p>
    </div>
  </div>
  <div class="pg-host-v2-unavailable">
    <p class="pg-host-v2-subtitle">history artifact: ${escapeHtml(state.historyArtifactPath)}</p>
  </div>
</section>`;
  }

  const payload = state.v2GraphPayload;
  const runtimeSummary = payload.runtimeSummary;
  const subtitleParts = [
    `graph_id=${escapeHtml(payload.graphId)}`,
    `source=${escapeHtml(payload.sourcePath ?? 'unknown')}`,
    `recorded_at=${escapeHtml(formatTimestamp(payload.recordedAt))}`,
  ];
  const metrics = [
    ['Nodes', String(payload.nodeCount)],
    ['Edges', String(payload.edgeCount)],
    ['Bound Nodes', String(runtimeSummary.boundNodeCount)],
    ['Open Work', String(runtimeSummary.openWorkItemCount)],
  ].map(([label, value]) => `<div class="pg-host-v2-metric"><div class="pg-host-v2-metric-label">${escapeHtml(label)}</div><div class="pg-host-v2-metric-value">${escapeHtml(value)}</div></div>`).join('');
  const meta = [
    '<span class="pg-host-v2-meta-pill">Mode Knowledge Graph Engine</span>',
    `<span class="pg-host-v2-meta-pill">Bound ${escapeHtml(String(runtimeSummary.boundNodeCount))}</span>`,
    `<span class="pg-host-v2-meta-pill">Runtime groups ${escapeHtml(String(runtimeSummary.activeGroupItemCount))}</span>`,
  ].join('');

  return `<section class="pg-host-v2-poc" data-pg-v2-status="available" data-pg-v2-worker-uri="${escapeHtml(state.v2GraphWorkerUri ?? '')}" data-pg-v2-auto-shake="${state.v2GraphAutoShake ? 'true' : 'false'}">
  <div class="pg-host-v2-head">
    <div class="pg-host-v2-title-wrap">
      <div class="pg-host-v2-eyebrow">Knowledge Graph Engine</div>
      <h2 class="pg-host-v2-title">${escapeHtml(payload.title)}</h2>
      <p class="pg-host-v2-subtitle">${subtitleParts.join(' · ')}</p>
    </div>
    <div class="pg-host-v2-head-actions">
      <div class="pg-host-v2-meta">${meta}</div>
      <div class="pg-host-v2-action-buttons">
        <button id="pgHostV2ShakeLayout" type="button" class="pg-host-v2-reset-button">Shake Layout</button>
        <button id="pgHostV2ResetViewport" type="button" class="pg-host-v2-reset-button">Reset Zoom/Pan</button>
      </div>
    </div>
  </div>
  <div id="pgHostV2ConfigTitleGhost" class="pg-host-v2-config-title-ghost pg-host-v2-config-title-text" aria-hidden="true">Graph Config</div>
  <div id="pgHostV2Layout" class="pg-host-v2-layout">
    <div id="pgHostV2GraphMain" class="pg-host-v2-graph-main">
      <div class="pg-host-v2-canvas-shell">
        <div id="pgHostV2MetricsDock" class="pg-host-v2-metrics-dock">
          <section id="pgHostV2MetricsInline" class="pg-host-v2-metrics pg-host-v2-metrics-inline" data-pg-metrics-collapsed="false">${metrics}</section>
        </div>
        <button id="pgHostV2ConfigCollapsedBar" type="button" class="pg-host-v2-config-collapsed-bar" data-pg-config-collapsed="false" aria-controls="pgHostV2ConfigCard" aria-expanded="true"><span id="pgHostV2ConfigCollapsedLabel" class="pg-host-v2-config-collapsed-label pg-host-v2-config-title-text">Graph Config</span></button>
        <div id="pgHostV2GraphCanvas" class="pg-host-v2-graph-canvas"></div>
        <div id="pgHostV2EngineStatus" class="pg-host-v2-engine-status" aria-live="polite"></div>
      </div>
    </div>
    <div id="pgHostV2ResizeHandle" class="pg-host-v2-resize-handle" data-pg-dragging="false" role="separator" aria-orientation="vertical" aria-label="Resize graph and side panel"></div>
    <div id="pgHostV2Side" class="pg-host-v2-side" data-pg-config-collapsed="false">
      ${buildV2GraphConfigCard()}
      <section id="pgHostV2MetricsSide" class="pg-host-v2-metrics pg-host-v2-metrics-side" data-pg-config-collapsed="false">${metrics}</section>
      <section id="pgHostV2NodeDetailCard" class="pg-host-v2-card pg-host-v2-detail-card">
        <div class="pg-host-v2-detail-head">
          <h3 class="pg-host-v2-card-title">Node Detail</h3>
          <button id="pgHostV2ClearSelection" type="button" class="pg-host-v2-detail-clear" disabled>Clear Selection</button>
        </div>
        <div id="pgHostV2GraphDetail" class="pg-host-v2-detail-body">
          <p class="pg-host-v2-detail-empty">悬停或点击节点后，这里会显示 kind、status、summary 与 runtime binding 摘要。</p>
        </div>
      </section>
    </div>
  </div>
  <script type="application/json" id="pgHostV2GraphPayload">${serializeJsonForHtml(payload)}</script>
</section>`;
}

function buildTrajectoryPanelSection(state: ProgressGraphPreviewState): string {
  return `<div class="pg-host-trajectory-stack">
    ${buildLocalWorkTrajectoryMountSection(state)}
    ${buildSchedulerWorkTrajectoryMountSection(state)}
  </div>`;
}

function buildLocalWorkTrajectoryMountSection(state: ProgressGraphPreviewState): string {
  return buildTrajectoryMountSection({
    title: 'Local Work Trajectory',
    authority: 'Agent managed',
    mountId: 'pgHostLocalWorkTrajectoryRoot',
    payloadId: 'pgHostLocalWorkTrajectoryPayload',
    artifactPath: state.trajectoryArtifactPath,
    artifactExists: state.trajectoryArtifactExists,
    trajectory: state.localWorkTrajectory,
    error: state.localWorkTrajectoryError,
    locateParent: true,
  });
}

function buildSchedulerWorkTrajectoryMountSection(state: ProgressGraphPreviewState): string {
  return buildTrajectoryMountSection({
    title: 'Scheduler Trajectory Projection',
    authority: 'Scheduler projection',
    mountId: 'pgHostSchedulerWorkTrajectoryRoot',
    payloadId: 'pgHostSchedulerWorkTrajectoryPayload',
    artifactPath: state.schedulerTrajectoryArtifactPath,
    artifactExists: state.schedulerTrajectoryArtifactExists,
    trajectory: state.schedulerWorkTrajectory,
    error: state.schedulerWorkTrajectoryError,
    locateParent: false,
    showHistoryTimeline: true,
  });
}

function buildTrajectoryMountSection(options: {
  title: string;
  authority: string;
  mountId: string;
  payloadId: string;
  artifactPath: string;
  artifactExists: boolean;
  trajectory: ProgressGraphPreviewLocalWorkTrajectory | null;
  error: string | null;
  locateParent: boolean;
  showHistoryTimeline?: boolean;
}): string {
  const payloadScript = options.trajectory
    ? `<script type="application/json" id="${escapeHtml(options.payloadId)}">${serializeJsonForHtml(options.trajectory)}</script>`
    : '';
  const status = options.error
    ? 'failed'
    : options.trajectory
      ? 'available'
      : 'unavailable';
  const error = options.error
    ?? (!options.trajectory && options.artifactExists
      ? `${options.title} artifact is not usable`
      : '');
  const activeEvent = options.trajectory?.events.find((event) => event.status === 'in_progress') ?? null;
  const toolbarMeta = [
    options.authority,
    `artifact=${options.artifactPath}`,
    options.trajectory ? `lanes=${options.trajectory.lanes.length}` : '',
    options.trajectory ? `events=${options.trajectory.events.length}` : '',
    options.trajectory ? `relations=${options.trajectory.relations.length}` : '',
    activeEvent ? `active=${activeEvent.id}` : '',
  ].filter(Boolean).join(' · ');

  const anchorGraphId = options.trajectory?.sourceGraphId ?? '';
  const anchorNodeId = options.trajectory?.sourceNodeId ?? '';
  const hasAnchor = Boolean(anchorGraphId && anchorNodeId);
  const anchorStateText = hasAnchor
    ? `anchor=${anchorGraphId}/${anchorNodeId}`
    : options.trajectory && options.locateParent
      ? 'anchor=not set'
      : '';
  const locateTitle = hasAnchor
    ? `Locate ${anchorGraphId}/${anchorNodeId} in the global map`
    : 'No global progress-map anchor has been set. Agents should call localTrajectory setAnchor with sourceGraphId and sourceNodeId.';
  const locateParentButton = options.locateParent
    ? `<button
      id="pgHostLocateTrajectoryParent"
      class="pg-host-lwt-locate-parent"
      type="button"
      data-pg-source-graph-id="${escapeHtml(anchorGraphId)}"
      data-pg-source-node-id="${escapeHtml(anchorNodeId)}"
      title="${escapeHtml(locateTitle)}"
      ${hasAnchor ? '' : 'disabled'}
    >Locate parent</button>`
    : '';
  const historyTimeline = options.showHistoryTimeline
    ? buildSchedulerHistoryTimeline(options.trajectory)
    : '';

  return `<section class="pg-host-lwt-mount-section" data-pg-lwt-status="${status}">
  <div class="pg-host-lwt-toolbar">
    <div class="pg-host-lwt-toolbar-copy">
      <p class="pg-host-lwt-toolbar-title">${escapeHtml(options.title)}</p>
      <p class="pg-host-lwt-toolbar-meta">${escapeHtml([toolbarMeta, anchorStateText].filter(Boolean).join(' · '))}</p>
    </div>
    ${locateParentButton}
  </div>
  ${historyTimeline}
  <div
    id="${escapeHtml(options.mountId)}"
    class="pg-host-lwt-mount"
    data-pg-trajectory-path="${escapeHtml(options.artifactPath)}"
    data-pg-trajectory-error="${escapeHtml(error)}"
    data-pg-trajectory-payload-id="${escapeHtml(options.payloadId)}"
  ></div>
  ${payloadScript}
</section>`;
}

function buildSchedulerHistoryTimeline(
  trajectory: ProgressGraphPreviewLocalWorkTrajectory | null,
): string {
  const metadata = trajectory?.metadata ?? {};
  const timeline = readTimelineLines(metadata.scheduler_history_timeline);
  if (timeline.length === 0) {
    return '';
  }
  const count = metadata.scheduler_history_timeline_count || String(timeline.length);
  const limit = metadata.scheduler_history_timeline_limit || String(timeline.length);
  const truncated = metadata.scheduler_history_timeline_truncated === 'true';
  const suffix = truncated
    ? ` · showing ${escapeHtml(String(timeline.length))}/${escapeHtml(count)}`
    : ` · ${escapeHtml(count)} entries`;
  const lines = timeline.map((line) => (
    `<li class="pg-host-lwt-history-line">${escapeHtml(line)}</li>`
  )).join('');
  const more = truncated
    ? `<p class="pg-host-lwt-history-more">Timeline truncated by projection limit ${escapeHtml(limit)}; inspect JSONL history for complete records.</p>`
    : '';
  return `<details class="pg-host-lwt-history">
    <summary class="pg-host-lwt-history-summary">Scheduler history timeline${suffix}</summary>
    <ol class="pg-host-lwt-history-lines">${lines}</ol>
    ${more}
  </details>`;
}

function readTimelineLines(value: string | undefined): string[] {
  return (value ?? '')
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean);
}

function buildV2GraphConfigCard(): string {
  return `<section id="pgHostV2ConfigCard" class="pg-host-v2-card pg-host-v2-config-card" data-pg-config-collapsed="false">
  <div id="pgHostV2ConfigCardContent" class="pg-host-v2-config-card-content">
  <div class="pg-host-v2-config-card-head">
    <div class="pg-host-v2-config-card-copy">
      <h3 id="pgHostV2ConfigCardTitle" class="pg-host-v2-card-title pg-host-v2-config-card-title pg-host-v2-config-title-text">Graph Config</h3>
      <p class="pg-host-v2-card-subtitle">当前图面由外部 knowledge-graph-engine 渲染；宿主只保留 progress graph payload 适配、控制面板和详情面板。</p>
    </div>
    <button id="pgHostV2ConfigToggle" class="pg-host-v2-config-toggle" type="button" aria-expanded="true">Collapse</button>
  </div>
  <details class="pg-host-v2-config-section" open>
    <summary class="pg-host-v2-config-summary">外观</summary>
    <div class="pg-host-v2-config-body">
      <div class="pg-host-v2-config-row">
        <div class="pg-host-v2-config-row-head">
          <label class="pg-host-v2-config-label" for="pgHostV2AppearanceLabelDensity">标签覆盖率</label>
          <output id="pgHostV2AppearanceLabelDensityValue" class="pg-host-v2-config-value">14%</output>
        </div>
        <input id="pgHostV2AppearanceLabelDensity" class="pg-host-v2-config-range" type="range" min="0" max="1" step="0.01" value="0.14">
      </div>
      <div class="pg-host-v2-config-row">
        <div class="pg-host-v2-config-row-head">
          <label class="pg-host-v2-config-label" for="pgHostV2AppearanceLabelSize">标签大小</label>
          <output id="pgHostV2AppearanceLabelSizeValue" class="pg-host-v2-config-value">13px</output>
        </div>
        <input id="pgHostV2AppearanceLabelSize" class="pg-host-v2-config-range" type="range" min="11" max="20" step="1" value="13">
      </div>
      <div class="pg-host-v2-config-row">
          <div class="pg-host-v2-config-row-head">
            <label class="pg-host-v2-config-label" for="pgHostV2AppearanceNodeScale">节点大小</label>
            <output id="pgHostV2AppearanceNodeScaleValue" class="pg-host-v2-config-value">1.12x</output>
          </div>
        <input id="pgHostV2AppearanceNodeScale" class="pg-host-v2-config-range" type="range" min="0.75" max="1.8" step="0.05" value="1.12">
        </div>
      <div class="pg-host-v2-config-row">
        <div class="pg-host-v2-config-row-head">
          <label class="pg-host-v2-config-label" for="pgHostV2AppearanceEdgeScale">连线粗细</label>
          <output id="pgHostV2AppearanceEdgeScaleValue" class="pg-host-v2-config-value">1.00x</output>
        </div>
        <input id="pgHostV2AppearanceEdgeScale" class="pg-host-v2-config-range" type="range" min="0.5" max="2.2" step="0.05" value="1">
      </div>
    </div>
  </details>
  <details class="pg-host-v2-config-section" open>
    <summary class="pg-host-v2-config-summary">力度</summary>
    <div class="pg-host-v2-config-body">
      <div class="pg-host-v2-config-row">
        <div class="pg-host-v2-config-row-head">
          <label class="pg-host-v2-config-label" for="pgHostV2ForceGravity">图谱向心力</label>
          <output id="pgHostV2ForceGravityValue" class="pg-host-v2-config-value">10</output>
        </div>
        <input id="pgHostV2ForceGravity" class="pg-host-v2-config-range" type="range" min="1" max="24" step="1" value="10">
      </div>
      <div class="pg-host-v2-config-row">
        <div class="pg-host-v2-config-row-head">
          <label class="pg-host-v2-config-label" for="pgHostV2ForceRepulsion">节点间的排斥力</label>
          <output id="pgHostV2ForceRepulsionValue" class="pg-host-v2-config-value">1000</output>
        </div>
        <input id="pgHostV2ForceRepulsion" class="pg-host-v2-config-range" type="range" min="200" max="3000" step="50" value="1000">
      </div>
      <div class="pg-host-v2-config-row">
        <div class="pg-host-v2-config-row-head">
          <label class="pg-host-v2-config-label" for="pgHostV2ForceAttraction">相连节点间的吸引力</label>
          <output id="pgHostV2ForceAttractionValue" class="pg-host-v2-config-value">50</output>
        </div>
        <input id="pgHostV2ForceAttraction" class="pg-host-v2-config-range" type="range" min="10" max="140" step="5" value="50">
      </div>
      <div class="pg-host-v2-config-row">
        <div class="pg-host-v2-config-row-head">
          <label class="pg-host-v2-config-label" for="pgHostV2ForceLinkLength">连线长度</label>
          <output id="pgHostV2ForceLinkLengthValue" class="pg-host-v2-config-value">200px</output>
        </div>
        <input id="pgHostV2ForceLinkLength" class="pg-host-v2-config-range" type="range" min="80" max="280" step="5" value="200">
      </div>
    </div>
  </details>
  <details class="pg-host-v2-config-section" open>
    <summary class="pg-host-v2-config-summary">颜色组</summary>
    <div class="pg-host-v2-config-body">
      <p class="pg-host-v2-config-hint">按列表顺序首个命中优先。当前支持 Search 风格核心语法，例如空格 AND、OR、-、括号、引号、regex，以及 file:/path:/content:/tag:/kind:/status:/match-case:/ignore-case:。</p>
      <div id="pgHostV2ColorGroups" class="pg-host-v2-color-group-list"></div>
      <button id="pgHostV2AddColorGroup" class="pg-host-v2-config-button" type="button">添加颜色组</button>
    </div>
  </details>
</div>
</section>`;
}

function buildControlOverlay(state: ProgressGraphPreviewState): string {
  const payloadScript = state.controlSnapshot
    ? `<script type="application/json" id="pgHostControlSnapshotPayload">${serializeJsonForHtml(state.controlSnapshot)}</script>`
    : '';
  const snapshotStatus = state.controlSnapshotError
    ? 'failed'
    : state.controlSnapshot
      ? 'available'
      : 'unavailable';

  return `<section class="pg-host-control-overlay" data-control-snapshot-status="${snapshotStatus}" data-control-snapshot-path="${escapeHtml(state.controlSnapshotPath)}" data-control-snapshot-error="${escapeHtml(state.controlSnapshotError ?? '')}">
  ${buildControlSummaryRail(state)}
  ${buildSchedulerOperatorSection(state)}
  ${buildHostEvidenceSection(state)}
  <div class="pg-host-control-grid">
    ${buildCompanionCard(state)}
    ${buildUnboundRuntimePanel(state)}
  </div>
  ${payloadScript}
</section>`;
}

function buildControlSummaryRail(state: ProgressGraphPreviewState): string {
  const snapshot = state.controlSnapshot;
  if (!snapshot) {
    return `<section class="pg-host-control-card">
  <h2 class="pg-host-control-card-title">Control Summary Rail</h2>
  <p class="pg-host-control-card-subtitle">${escapeHtml(controlSnapshotStatusMessage(state))}</p>
</section>`;
  }

  const summary = snapshot.summary;
  const metrics = [
    ['Open Work Items', String(summary.open_work_item_count)],
    ['Blocked Work Items', String(summary.blocked_work_item_count)],
    ['Waiting External', String(summary.waiting_external_resolution_count)],
    ['Active Group Items', String(summary.active_group_item_count)],
    ['Unbound Group Items', String(summary.unbound_group_item_count)],
  ].map(([label, value]) => `<div class="pg-host-summary-metric"><div class="pg-host-summary-label">${escapeHtml(label)}</div><div class="pg-host-summary-value">${escapeHtml(value)}</div></div>`).join('');

  return `<section class="pg-host-control-card">
  <h2 class="pg-host-control-card-title">Control Summary Rail</h2>
  <p class="pg-host-control-card-subtitle">runtime snapshot generated at ${escapeHtml(formatTimestamp(snapshot.generated_at))}</p>
  <div class="pg-host-summary-rail">${metrics}</div>
</section>`;
}

function buildSchedulerOperatorSection(state: ProgressGraphPreviewState): string {
  const workflow = state.schedulerOperatorWorkflow;
  const exchange = workflow.exchange;
  const lastAction = workflow.lastAction;
  const pathFacts = [
    ['Store', workflow.paths.artifactStorePath],
    ['Ledger', workflow.paths.admissionLedgerPath],
    ['Snapshot', workflow.paths.schedulerSnapshotPath],
    ['Event log', workflow.paths.schedulerEventLogPath],
    ['Projection', workflow.paths.schedulerProjectionPath],
  ].map(([label, value]) => (
    `<div class="pg-host-evidence-fact">
      <div class="pg-host-evidence-label">${escapeHtml(label)}</div>
      <div class="pg-host-evidence-value">${escapeHtml(value)}</div>
    </div>`
  )).join('');
  const exchangeFacts = exchange
    ? [
      ['Store exists', String(exchange.exists)],
      ['Artifacts', String(exchange.artifactCount)],
      ['Versions', String(exchange.versionCount)],
      ['Admission candidates', String(exchange.admissionCandidateCount)],
      ['Ledger exists', String(exchange.admissionLedgerExists)],
    ].map(([label, value]) => (
      `<div class="pg-host-evidence-fact">
        <div class="pg-host-evidence-label">${escapeHtml(label)}</div>
        <div class="pg-host-evidence-value">${escapeHtml(value)}</div>
      </div>`
    )).join('')
    : '';
  const scheduler = workflow.scheduler;
  const schedulerFacts = scheduler
    ? [
      ['Snapshot exists', String(scheduler.snapshotExists)],
      ['Tasks', String(scheduler.taskCount)],
      ['Dependencies', String(scheduler.dependencyCount)],
      ['Run records', String(scheduler.runRecordCount)],
      ['Scheduler events', String(scheduler.schedulerEventCount)],
    ].map(([label, value]) => (
      `<div class="pg-host-evidence-fact">
        <div class="pg-host-evidence-label">${escapeHtml(label)}</div>
        <div class="pg-host-evidence-value">${escapeHtml(value)}</div>
      </div>`
    )).join('')
    : '';
  const candidateList = exchange?.candidates.length
    ? `<div class="pg-host-scheduler-candidates">
      <p class="pg-host-evidence-group-title">Admission candidates</p>
      ${exchange.candidates.map((candidate) => buildSchedulerOperatorCandidate(candidate, lastAction.status === 'running')).join('')}
    </div>`
    : `<p class="pg-host-control-card-subtitle">No scheduler-admission candidates are currently present in the ExchangeArtifact store.</p>`;
  const readError = workflow.exchangeReadError
    ? `<div class="pg-host-scheduler-action-result" data-pg-action-status="failed">
      <span class="pg-host-evidence-badge" data-pg-evidence-status="failed">exchange read failed</span>
      <p class="pg-host-control-card-subtitle">${escapeHtml(workflow.exchangeReadError)}</p>
    </div>`
    : '';
  const schedulerReadError = workflow.schedulerReadError
    ? `<p class="pg-host-control-card-subtitle">Scheduler state readback unavailable: ${escapeHtml(workflow.schedulerReadError)}</p>`
    : '';
  const authorizationReadback = buildSchedulerAuthorizationReadbackSection(
    workflow.authorizationReadback,
    workflow.authorizationReadError,
  );
  const sandboxWorkflowAction = buildSchedulerSandboxReceiptWorkflowAction(lastAction.status === 'running');
  const cleanupAction = buildSchedulerCleanupReceiptAction(
    lastAction.status === 'running',
    state.hostEvidencePresentation,
  );
  const errors = exchange?.errors.length
    ? buildHostEvidenceChipGroup('Exchange read errors', exchange.errors)
    : '';
  const lastActionHtml = lastAction.status === 'idle'
    ? ''
    : `<div class="pg-host-scheduler-action-result" data-pg-action-status="${escapeHtml(lastAction.status)}">
      <div class="pg-host-evidence-chip-row">
        <span class="pg-host-evidence-badge" data-pg-evidence-status="${lastAction.status === 'failed' ? 'failed' : lastAction.status === 'succeeded' ? 'completed' : 'unknown'}">${escapeHtml(lastAction.status)}</span>
        <span class="pg-host-evidence-badge">${escapeHtml(lastAction.action || 'scheduler action')}</span>
      </div>
      <p class="pg-host-control-card-subtitle">${escapeHtml(lastAction.summary || 'action completed')}</p>
      ${lastAction.stderr ? `<pre class="pg-host-scheduler-output">${escapeHtml(lastAction.stderr)}</pre>` : ''}
      ${lastAction.stdout ? `<pre class="pg-host-scheduler-output">${escapeHtml(lastAction.stdout)}</pre>` : ''}
    </div>`;

  return `<section id="pgHostSchedulerOperatorPanel" class="pg-host-control-card pg-host-scheduler-operator-card">
  <div class="pg-host-scheduler-operator-head">
    <div class="pg-host-evidence-title-wrap">
      <h2 class="pg-host-control-card-title">Scheduler Operator</h2>
      <p class="pg-host-control-card-subtitle">resource=${escapeHtml(workflow.exchangeResourceUri)} · explicit admit / bounded run / projection refresh</p>
    </div>
    <div class="pg-host-scheduler-operator-actions">
      <button class="pg-host-scheduler-operator-button" type="button" data-pg-scheduler-action="runLoop" ${lastAction.status === 'running' ? 'disabled' : ''}>Run bounded loop</button>
      <button class="pg-host-scheduler-operator-button" type="button" data-pg-scheduler-action="project" ${lastAction.status === 'running' ? 'disabled' : ''}>Refresh projection</button>
    </div>
  </div>
  <div class="pg-host-scheduler-operator-grid">${exchangeFacts || pathFacts}${schedulerFacts}</div>
  ${schedulerReadError}
  ${authorizationReadback}
  ${sandboxWorkflowAction}
  ${cleanupAction}
  ${readError}
  ${candidateList}
  ${errors}
  ${lastActionHtml}
</section>`;
}

function buildSchedulerSandboxReceiptWorkflowAction(actionRunning: boolean): string {
  return `<section id="pgHostSandboxReceiptWorkflow" class="pg-host-scheduler-cleanup-form">
  <div class="pg-host-evidence-title-wrap">
    <h3 class="pg-host-scheduler-candidate-title">Sandbox Receipt Workflow</h3>
    <p class="pg-host-control-card-subtitle">run-once or bounded daemon-loop allocate/readback with optional explicit cleanup/readback · scheduler sandbox-receipt-workflow</p>
  </div>
  <div class="pg-host-scheduler-workflow-grid">
    <div class="pg-host-scheduler-field">
      <label for="pgHostSandboxWorkflowMode">workflow mode</label>
      <select
        id="pgHostSandboxWorkflowMode"
        class="pg-host-scheduler-select"
        ${actionRunning ? 'disabled' : ''}
      >
        <option value="run-once" selected>run-once</option>
        <option value="daemon-loop">daemon-loop</option>
      </select>
      <span class="pg-host-scheduler-field-hint">daemon-loop uses bounded fake runtime settings below.</span>
    </div>
    <div class="pg-host-scheduler-field">
      <label for="pgHostSandboxWorkflowMaxTicks">max ticks</label>
      <input
        id="pgHostSandboxWorkflowMaxTicks"
        class="pg-host-scheduler-cleanup-input"
        type="number"
        min="1"
        step="1"
        inputmode="numeric"
        autocomplete="off"
        spellcheck="false"
        value="1"
        ${actionRunning ? 'disabled' : ''}
      >
    </div>
    <div class="pg-host-scheduler-field">
      <label for="pgHostSandboxWorkflowMaxRunsPerTick">max runs / tick</label>
      <input
        id="pgHostSandboxWorkflowMaxRunsPerTick"
        class="pg-host-scheduler-cleanup-input"
        type="number"
        min="1"
        step="1"
        inputmode="numeric"
        autocomplete="off"
        spellcheck="false"
        value="1"
        ${actionRunning ? 'disabled' : ''}
      >
    </div>
    <div class="pg-host-scheduler-field">
      <label for="pgHostSandboxWorkflowMaxRuntimeFailures">max runtime failures</label>
      <input
        id="pgHostSandboxWorkflowMaxRuntimeFailures"
        class="pg-host-scheduler-cleanup-input"
        type="number"
        min="1"
        step="1"
        inputmode="numeric"
        autocomplete="off"
        spellcheck="false"
        value="1"
        ${actionRunning ? 'disabled' : ''}
      >
    </div>
    <div class="pg-host-scheduler-field" data-pg-wide-field="true">
      <label for="pgHostSandboxWorkflowWorkspaceRoot">workspace root</label>
      <input
        id="pgHostSandboxWorkflowWorkspaceRoot"
        class="pg-host-scheduler-cleanup-input"
        type="text"
        autocomplete="off"
        spellcheck="false"
        placeholder="source git repository root"
        ${actionRunning ? 'disabled' : ''}
      >
    </div>
    <div class="pg-host-scheduler-field" data-pg-wide-field="true">
      <label for="pgHostSandboxWorkflowSandboxRoot">git-worktree sandbox root</label>
      <input
        id="pgHostSandboxWorkflowSandboxRoot"
        class="pg-host-scheduler-cleanup-input"
        type="text"
        autocomplete="off"
        spellcheck="false"
        placeholder=".codex/scheduler/sandboxes"
        ${actionRunning ? 'disabled' : ''}
      >
    </div>
    <div class="pg-host-scheduler-field">
      <label for="pgHostSandboxWorkflowAllocationEvidenceId">allocation evidence id</label>
      <input
        id="pgHostSandboxWorkflowAllocationEvidenceId"
        class="pg-host-scheduler-cleanup-input"
        type="text"
        autocomplete="off"
        spellcheck="false"
        placeholder="vscode-workflow-allocation"
        ${actionRunning ? 'disabled' : ''}
      >
    </div>
    <div class="pg-host-scheduler-field">
      <label for="pgHostSandboxWorkflowAllocationEvidencePath">allocation evidence path</label>
      <input
        id="pgHostSandboxWorkflowAllocationEvidencePath"
        class="pg-host-scheduler-cleanup-input"
        type="text"
        autocomplete="off"
        spellcheck="false"
        placeholder=".codex/scheduler/evidence/vscode-workflow-allocation.json"
        ${actionRunning ? 'disabled' : ''}
      >
    </div>
  </div>
  <label class="pg-host-scheduler-cleanup-confirm" for="pgHostSandboxWorkflowCleanup">
    <input id="pgHostSandboxWorkflowCleanup" type="checkbox" ${actionRunning ? 'disabled' : ''}>
    <span>Also run explicit cleanup and post-cleanup readback in this workflow.</span>
  </label>
  <details id="pgHostSandboxWorkflowCleanupDetails" class="pg-host-scheduler-workflow-details">
    <summary>Cleanup evidence output settings</summary>
    <div class="pg-host-scheduler-workflow-grid">
      <div class="pg-host-scheduler-field">
        <label for="pgHostSandboxWorkflowCleanupEvidenceId">cleanup evidence id</label>
        <input
          id="pgHostSandboxWorkflowCleanupEvidenceId"
          class="pg-host-scheduler-cleanup-input"
          type="text"
          autocomplete="off"
          spellcheck="false"
          placeholder="vscode-workflow-cleanup"
          ${actionRunning ? 'disabled' : ''}
        >
      </div>
      <div class="pg-host-scheduler-field">
        <label for="pgHostSandboxWorkflowCleanupEvidencePath">cleanup evidence path</label>
        <input
          id="pgHostSandboxWorkflowCleanupEvidencePath"
          class="pg-host-scheduler-cleanup-input"
          type="text"
          autocomplete="off"
          spellcheck="false"
          placeholder=".codex/scheduler/evidence/vscode-workflow-cleanup.json"
          ${actionRunning ? 'disabled' : ''}
        >
      </div>
    </div>
  </details>
  <div class="pg-host-scheduler-candidate-actions">
    <button
      class="pg-host-scheduler-operator-button"
      type="button"
      data-pg-scheduler-action="runSandboxReceiptWorkflow"
      ${actionRunning ? 'disabled' : ''}
    >Run receipt workflow</button>
  </div>
</section>`;
}

function buildSchedulerCleanupReceiptAction(
  actionRunning: boolean,
  presentation: ProgressGraphPreviewHostEvidencePresentation | null,
): string {
  const candidates = buildSchedulerCleanupReceiptCandidates(presentation);
  const outcomeDiff = buildSchedulerCleanupOutcomeDiff(presentation);
  const candidateList = candidates.length
    ? `<div class="pg-host-scheduler-cleanup-candidates">
      <p class="pg-host-evidence-group-title">Receipt evidence candidates</p>
      <div class="pg-host-scheduler-cleanup-candidate-list">
        ${candidates.map((candidate) => buildSchedulerCleanupReceiptCandidate(candidate, actionRunning)).join('')}
      </div>
    </div>`
    : `<p class="pg-host-control-card-subtitle">No sandbox receipt evidence candidates are currently visible in Host Evidence.</p>`;
  return `<section id="pgHostSchedulerCleanupReceipts" class="pg-host-scheduler-cleanup-form">
  <div class="pg-host-evidence-title-wrap">
    <h3 class="pg-host-scheduler-candidate-title">Sandbox Receipt Cleanup</h3>
    <p class="pg-host-control-card-subtitle">select visible sandbox_allocation_receipt_evidence or enter a manual path · explicit scheduler cleanup-receipts invocation</p>
  </div>
  ${candidateList}
  ${outcomeDiff}
  <div class="pg-host-scheduler-cleanup-row">
    <input
      id="pgHostCleanupEvidencePath"
      class="pg-host-scheduler-cleanup-input"
      type="text"
      autocomplete="off"
      spellcheck="false"
      placeholder=".codex/scheduler/evidence/allocation-receipts.json"
      ${actionRunning ? 'disabled' : ''}
    >
    <button class="pg-host-scheduler-operator-button" type="button" data-pg-scheduler-action="cleanupReceipts" ${actionRunning ? 'disabled' : ''}>Clean receipts</button>
  </div>
  <label class="pg-host-scheduler-cleanup-confirm" for="pgHostCleanupConfirm">
    <input id="pgHostCleanupConfirm" type="checkbox" ${actionRunning ? 'disabled' : ''}>
    <span>I confirm this explicitly runs cleanup for receipt-marked git-worktree sandboxes and writes updated evidence.</span>
  </label>
</section>`;
}

function buildSchedulerCleanupReceiptCandidate(
  candidate: SchedulerCleanupReceiptCandidate,
  actionRunning: boolean,
): string {
  const workflowEvidenceId = schedulerEvidenceIdFromPath(candidate.path);
  return `<article class="pg-host-scheduler-cleanup-candidate" data-pg-cleanup-evidence-candidate="${escapeHtml(candidate.id)}">
    <div>
      <p class="pg-host-scheduler-cleanup-candidate-title">${escapeHtml(candidate.label)}</p>
      <p class="pg-host-scheduler-cleanup-candidate-meta">${escapeHtml(candidate.role)} · ${escapeHtml(candidate.status)} · ${escapeHtml(candidate.path)}</p>
      <p class="pg-host-scheduler-cleanup-candidate-meta">${escapeHtml(candidate.detail)}</p>
    </div>
    <div class="pg-host-scheduler-candidate-actions">
      <button
        class="pg-host-scheduler-operator-button"
        type="button"
        data-pg-cleanup-evidence-select="true"
        data-pg-cleanup-evidence-path="${escapeHtml(candidate.path)}"
        ${actionRunning ? 'disabled' : ''}
      >Select</button>
      <button
        class="pg-host-scheduler-operator-button"
        type="button"
        data-pg-workflow-evidence-prefill="true"
        data-pg-workflow-evidence-id="${escapeHtml(workflowEvidenceId)}"
        data-pg-workflow-evidence-path="${escapeHtml(candidate.path)}"
        ${actionRunning ? 'disabled' : ''}
      >Use for workflow</button>
    </div>
  </article>`;
}

function schedulerEvidenceIdFromPath(path: string): string {
  const normalized = path.replace(/\\/g, '/').split('/').filter(Boolean).pop() || path;
  return normalized.replace(/\.json$/i, '').trim();
}

function buildSchedulerCleanupReceiptCandidates(
  presentation: ProgressGraphPreviewHostEvidencePresentation | null,
): SchedulerCleanupReceiptCandidate[] {
  if (!presentation) {
    return [];
  }

  const candidates: SchedulerCleanupReceiptCandidate[] = [];
  const seen = new Set<string>();
  for (const card of presentation.cards) {
    if (!isSandboxAllocationReceiptEvidenceCard(card)) {
      continue;
    }
    const cleanupSummary = summarizeCleanupState(card);
    for (const ref of card.refs) {
      if (!isReceiptEvidencePathRef(ref)) {
        continue;
      }
      const role = cleanupReceiptRefRole(ref.label);
      const key = `${role}\u0000${ref.target}`;
      if (seen.has(key)) {
        continue;
      }
      seen.add(key);
      candidates.push({
        id: `${card.id}:${candidates.length + 1}`,
        path: ref.target,
        label: `${card.title} · ${ref.label}`,
        role,
        status: cleanupSummary.status || card.status || 'unknown',
        detail: cleanupSummary.detail || card.stopDetail || 'sandbox allocation receipt evidence',
      });
    }
  }
  return candidates;
}

function buildSchedulerCleanupOutcomeDiff(
  presentation: ProgressGraphPreviewHostEvidencePresentation | null,
): string {
  const rows = buildSchedulerCleanupOutcomeDiffRows(presentation);
  const rowHtml = rows.length
    ? rows.map(buildSchedulerCleanupOutcomeDiffRow).join('')
    : `<p class="pg-host-control-card-subtitle">No visible source/cleanup sandbox receipt pair is available for diff.</p>`;
  return `<div id="pgHostSchedulerCleanupOutcomeDiff" class="pg-host-scheduler-cleanup-diff" data-pg-cleanup-outcome-diff-count="${rows.length}">
    <div class="pg-host-evidence-title-wrap">
      <p class="pg-host-evidence-group-title">Cleanup outcome diff</p>
      <p class="pg-host-control-card-subtitle">read-only comparison from visible Host Evidence receipt refs</p>
    </div>
    ${rowHtml}
  </div>`;
}

function buildSchedulerCleanupOutcomeDiffRows(
  presentation: ProgressGraphPreviewHostEvidencePresentation | null,
): SchedulerCleanupOutcomeDiffRow[] {
  if (!presentation) {
    return [];
  }
  return presentation.cards
    .filter(isSandboxAllocationReceiptEvidenceCard)
    .map((card) => {
      const sourcePath = findReceiptRefPath(card, 'source receipt');
      const cleanupPath = findReceiptRefPath(card, 'cleanup receipt')
        || (isCleanupOutcomeCard(card) ? findReceiptRefPath(card, 'current receipt') : '');
      if (!sourcePath || !cleanupPath) {
        return null;
      }
      const currentPath = findReceiptRefPath(card, 'current receipt');
      const stateCounts = readCleanupStateCounts(card);
      const requiredIds = readUnknownStringArray(card.metadata.cleanup_required_allocation_ids);
      const failedIds = readUnknownStringArray(card.metadata.cleanup_failed_allocation_ids);
      const completedIds = readUnknownStringArray(card.metadata.cleanup_completed_allocation_ids);
      return {
        id: card.id,
        title: card.title || card.id,
        status: summarizeCleanupState(card).status || card.status || 'unknown',
        beforeSummary: `required before: ${readFactValue(card, 'Cleanup required before', readFactValue(card, 'Source cleanup required', 'unknown'))}`,
        afterSummary: [
          `required=${stateCounts.required}`,
          `completed=${stateCounts.completed}`,
          `failed=${stateCounts.failed}`,
        ].join(' · '),
        sourcePath,
        cleanupPath,
        currentPath,
        changedAllocationIds: Array.from(new Set([
          ...completedIds,
          ...failedIds,
          ...requiredIds,
        ].filter(Boolean))),
      } satisfies SchedulerCleanupOutcomeDiffRow;
    })
    .filter((row): row is SchedulerCleanupOutcomeDiffRow => row !== null);
}

function buildSchedulerCleanupOutcomeDiffRow(row: SchedulerCleanupOutcomeDiffRow): string {
  const changed = row.changedAllocationIds.length ? row.changedAllocationIds.join(', ') : 'not listed';
  const facts = [
    ['Before', row.beforeSummary],
    ['After', row.afterSummary],
    ['Changed allocations', changed],
    ['Source receipt', row.sourcePath],
    ['Cleanup receipt', row.cleanupPath],
    ...(row.currentPath && row.currentPath !== row.cleanupPath ? [['Current receipt', row.currentPath]] : []),
  ].map(([label, value]) => `<div class="pg-host-scheduler-cleanup-diff-fact">
      <div class="pg-host-scheduler-cleanup-diff-label">${escapeHtml(label)}</div>
      <div class="pg-host-scheduler-cleanup-diff-value">${escapeHtml(value)}</div>
    </div>`).join('');
  return `<article class="pg-host-scheduler-cleanup-diff-row" data-pg-cleanup-outcome-diff-row="${escapeHtml(row.id)}">
    <div class="pg-host-evidence-chip-row">
      <span class="pg-host-evidence-badge" data-pg-evidence-status="${escapeHtml(row.status.includes('failed') ? 'failed' : row.status.includes('required') ? 'warning' : 'completed')}">${escapeHtml(row.status)}</span>
      <span class="pg-host-evidence-badge">${escapeHtml(row.title)}</span>
    </div>
    <div class="pg-host-scheduler-cleanup-diff-grid">${facts}</div>
  </article>`;
}

function isSandboxAllocationReceiptEvidenceCard(card: ProgressGraphPreviewHostEvidenceCard): boolean {
  if (card.metadata.evidence_product_type === 'sandbox_allocation_receipt_evidence') {
    return true;
  }
  return card.keyFacts.some((fact) => (
    fact.label.toLowerCase() === 'evidence product'
    && fact.value === 'sandbox_allocation_receipt_evidence'
  ));
}

function isReceiptEvidencePathRef(ref: ProgressGraphPreviewHostEvidenceRef): boolean {
  if (ref.refKind !== 'path' || !ref.target.trim()) {
    return false;
  }
  const label = ref.label.toLowerCase();
  const target = ref.target.replace(/\\/g, '/').toLowerCase();
  return label.includes('evidence')
    && target.includes('.codex/scheduler/evidence/')
    && target.endsWith('.json');
}

function cleanupReceiptRefRole(label: string): string {
  const normalized = label.toLowerCase();
  if (normalized.includes('source')) {
    return 'source receipt';
  }
  if (normalized.includes('cleanup')) {
    return 'cleanup receipt';
  }
  return 'current receipt';
}

function findReceiptRefPath(card: ProgressGraphPreviewHostEvidenceCard, role: string): string {
  const ref = card.refs.find((candidate) => (
    isReceiptEvidencePathRef(candidate)
    && cleanupReceiptRefRole(candidate.label) === role
  ));
  return ref?.target ?? '';
}

function isCleanupOutcomeCard(card: ProgressGraphPreviewHostEvidenceCard): boolean {
  const executed = readFactValue(card, 'Cleanup executed', '').toLowerCase() === 'true'
    || card.authorityClues.some((fact) => (
      fact.label.toLowerCase() === 'cleanup executed'
      && fact.value.toLowerCase() === 'true'
    ));
  return executed
    || card.hostSurface.toLowerCase().includes('cleanup')
    || card.stopReason.toLowerCase().includes('cleanup_settled');
}

function readCleanupStateCounts(card: ProgressGraphPreviewHostEvidenceCard): {
  required: string;
  completed: string;
  failed: string;
} {
  const stateCounts = isRecord(card.metadata.cleanup_state_counts)
    ? card.metadata.cleanup_state_counts
    : {};
  return {
    required: readStateCountOrFact(card, stateCounts, 'required', 'Cleanup required'),
    completed: readStateCountOrFact(card, stateCounts, 'completed', 'Cleanup completed'),
    failed: readStateCountOrFact(card, stateCounts, 'failed', 'Cleanup failed'),
  };
}

function readStateCountOrFact(
  card: ProgressGraphPreviewHostEvidenceCard,
  stateCounts: Record<string, unknown>,
  key: string,
  factLabel: string,
): string {
  const value = stateCounts[key];
  if (typeof value === 'number' || typeof value === 'string') {
    return String(value);
  }
  return readFactValue(card, factLabel, '0');
}

function readFactValue(
  card: ProgressGraphPreviewHostEvidenceCard,
  label: string,
  fallback: string,
): string {
  const normalized = label.toLowerCase();
  const fact = [...card.keyFacts, ...card.authorityClues].find((candidate) => (
    candidate.label.toLowerCase() === normalized
  ));
  return fact?.value ?? fallback;
}

function summarizeCleanupState(card: ProgressGraphPreviewHostEvidenceCard): { status: string; detail: string } {
  const stateCounts = card.metadata.cleanup_state_counts;
  const cleanupStateParts = isRecord(stateCounts)
    ? Object.entries(stateCounts)
      .filter(([, value]) => typeof value === 'number' || typeof value === 'string')
      .map(([label, value]) => `${label}: ${String(value)}`)
    : [];
  const requiredIds = readUnknownStringArray(card.metadata.cleanup_required_allocation_ids);
  const failedIds = readUnknownStringArray(card.metadata.cleanup_failed_allocation_ids);
  const completedIds = readUnknownStringArray(card.metadata.cleanup_completed_allocation_ids);
  const status = failedIds.length
    ? 'cleanup failed'
    : requiredIds.length
      ? 'cleanup required'
      : completedIds.length
        ? 'cleanup settled'
        : card.stopReason || card.status;
  const detailParts = [
    cleanupStateParts.length ? `states ${cleanupStateParts.join(', ')}` : '',
    requiredIds.length ? `required ${requiredIds.join(', ')}` : '',
    failedIds.length ? `failed ${failedIds.join(', ')}` : '',
    completedIds.length ? `completed ${completedIds.join(', ')}` : '',
  ].filter(Boolean);
  return {
    status,
    detail: detailParts.join(' · '),
  };
}

function buildSchedulerAuthorizationReadbackSection(
  readback: SchedulerAuthorizationReadback | null,
  readError: string | null,
): string {
  if (readError) {
    return `<section id="pgHostSchedulerAuthorizationReadback" class="pg-host-scheduler-authorization" data-pg-authorization-readback-status="failed">
  <div class="pg-host-evidence-chip-row">
    <span class="pg-host-evidence-badge" data-pg-evidence-status="failed">authorization read failed</span>
  </div>
  <p class="pg-host-control-card-subtitle">${escapeHtml(readError)}</p>
</section>`;
  }

  if (!readback) {
    return `<section id="pgHostSchedulerAuthorizationReadback" class="pg-host-scheduler-authorization" data-pg-authorization-readback-status="unavailable">
  <div class="pg-host-evidence-chip-row">
    <span class="pg-host-evidence-badge" data-pg-evidence-status="unknown">authorization unavailable</span>
  </div>
  <p class="pg-host-control-card-subtitle">Scheduler authorization readback has not been loaded.</p>
</section>`;
  }

  if (!readback.ok) {
    return `<section id="pgHostSchedulerAuthorizationReadback" class="pg-host-scheduler-authorization" data-pg-authorization-readback-status="failed">
  <div class="pg-host-evidence-chip-row">
    <span class="pg-host-evidence-badge" data-pg-evidence-status="failed">authorization unavailable</span>
    <span class="pg-host-evidence-badge">${escapeHtml(readback.snapshotPath || 'snapshot unknown')}</span>
  </div>
  <p class="pg-host-control-card-subtitle">${escapeHtml(readback.error || 'schedulerAuthorizationReadback returned ok=false')}</p>
</section>`;
  }

  const facts = [
    ['Tasks', String(readback.taskCount)],
    ['Edit lease tasks', String(readback.editLeaseTaskCount)],
    ['Lifecycle records', String(readback.lifecycleRecordCount)],
    ['Orphan lifecycle records', String(readback.orphanLifecycleRecordCount)],
    ['Recovered from event log', String(readback.recoveredFromEventLog)],
  ].map(([label, value]) => (
    `<div class="pg-host-evidence-fact">
      <div class="pg-host-evidence-label">${escapeHtml(label)}</div>
      <div class="pg-host-evidence-value">${escapeHtml(value)}</div>
    </div>`
  )).join('');
  const lifecycleCounts = buildRecordChipGroup('Lifecycle states', readback.lifecycleStateCounts);
  const sandboxCounts = buildRecordChipGroup('Sandbox authorization states', readback.sandboxAuthorizationStateCounts);
  const taskRows = readback.tasks.length
    ? `<div class="pg-host-evidence-list">${readback.tasks.map(buildSchedulerAuthorizationTaskRow).join('')}</div>`
    : '<p class="pg-host-control-card-subtitle">No scheduler tasks are present in the authorization readback.</p>';

  return `<section id="pgHostSchedulerAuthorizationReadback" class="pg-host-scheduler-authorization" data-pg-authorization-readback-status="ok">
  <div class="pg-host-evidence-head">
    <div class="pg-host-evidence-title-wrap">
      <h3 class="pg-host-scheduler-candidate-title">Authorization Readback</h3>
      <p class="pg-host-control-card-subtitle">read-only schedulerAuthorizationReadback · ${escapeHtml(readback.productType || 'scheduler_authorization_readback')}</p>
    </div>
    <div class="pg-host-evidence-badge-row">
      <span class="pg-host-evidence-badge" data-pg-evidence-status="ok">read-only</span>
      <span class="pg-host-evidence-badge">schema ${escapeHtml(readback.schemaVersion || 'unknown')}</span>
    </div>
  </div>
  <div class="pg-host-scheduler-operator-grid">${facts}</div>
  ${lifecycleCounts}
  ${sandboxCounts}
  ${taskRows}
</section>`;
}

function buildSchedulerAuthorizationTaskRow(task: SchedulerAuthorizationTaskSummary): string {
  const lifecycleState = task.lifecycle?.state ?? (task.lifecycleMissing ? 'missing' : 'not_required');
  const sandboxState = task.sandboxAuthorization?.leaseAuthorizationState
    ?? task.sandboxAuthorization?.allocationState
    ?? 'unknown';
  const leaseLabel = task.hasEditLease
    ? `${task.leaseId || 'lease unknown'} · ${task.leaseMode || 'mode unknown'}`
    : 'no edit lease';
  const artifacts = task.allowedArtifacts.length
    ? task.allowedArtifacts.join(', ')
    : 'none';
  const reason = [
    task.lifecycle?.reason || '',
    task.sandboxAuthorization?.leaseAuthorizationReason || task.sandboxAuthorization?.allocationReason || '',
  ].filter(Boolean).join(' · ');
  return `<article class="pg-host-scheduler-auth-task" data-pg-authorization-task-id="${escapeHtml(task.taskId)}">
  <div class="pg-host-scheduler-candidate-head">
    <div>
      <h4 class="pg-host-scheduler-candidate-title">${escapeHtml(task.taskId || 'unknown task')}</h4>
      <p class="pg-host-scheduler-candidate-meta">${escapeHtml(task.title || 'untitled task')} · ${escapeHtml(task.state || 'unknown')} · ${escapeHtml(task.runtimeProvider || 'unknown provider')}</p>
      <p class="pg-host-scheduler-candidate-meta">lease=${escapeHtml(leaseLabel)} · allowed=${escapeHtml(artifacts)}</p>
    </div>
    <div class="pg-host-evidence-badge-row">
      <span class="pg-host-evidence-badge" data-pg-evidence-status="${escapeHtml(statusToEvidenceBadge(lifecycleState))}">lifecycle ${escapeHtml(lifecycleState)}</span>
      <span class="pg-host-evidence-badge" data-pg-evidence-status="${escapeHtml(statusToEvidenceBadge(sandboxState))}">sandbox ${escapeHtml(sandboxState)}</span>
    </div>
  </div>
  ${reason ? `<p class="pg-host-control-card-subtitle">${escapeHtml(reason)}</p>` : ''}
</article>`;
}

function buildRecordChipGroup(title: string, record: Record<string, number>): string {
  const values = Object.entries(record)
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([key, value]) => `${key}: ${value}`);
  return buildHostEvidenceChipGroup(title, values);
}

function statusToEvidenceBadge(status: string): string {
  if (['acquired', 'authorized', 'allocated', 'ok', 'completed'].includes(status)) {
    return 'ok';
  }
  if (['waiting', 'review_required', 'not_required', 'missing'].includes(status)) {
    return 'unknown';
  }
  if (['released', 'revoked', 'expired', 'rejected', 'blocked', 'failed'].includes(status)) {
    return 'failed';
  }
  return 'unknown';
}

function buildSchedulerOperatorCandidate(
  candidate: SchedulerOperatorExchangeCandidate,
  actionRunning: boolean,
): string {
  const taskLabel = candidate.taskIds.length
    ? candidate.taskIds.join(', ')
    : `${candidate.taskCount} task(s)`;
  const alreadyAdmitted = candidate.admissionStatus === 'admitted';
  const statusLabel = [
    `admission=${candidate.admissionStatus || 'unknown'}`,
    candidate.latestAdmissionStatus ? `latest=${candidate.latestAdmissionStatus}` : '',
    candidate.batchId ? `batch=${candidate.batchId}` : '',
  ].filter(Boolean).join(' · ');
  const bindingVisibility = buildSchedulerOperatorCandidateBindingVisibility(candidate);
  const inspectBindingRefs = candidate.bindingReferenceReadiness ? 'true' : 'false';
  return `<article class="pg-host-scheduler-candidate">
    <div class="pg-host-scheduler-candidate-head">
      <div>
        <h3 class="pg-host-scheduler-candidate-title">${escapeHtml(candidate.artifactId)}@${escapeHtml(candidate.version)}</h3>
        <p class="pg-host-scheduler-candidate-meta">${escapeHtml(candidate.productType)} · ${escapeHtml(taskLabel)}</p>
        <p class="pg-host-scheduler-candidate-meta">${escapeHtml(statusLabel)}</p>
      </div>
      <div class="pg-host-scheduler-candidate-actions">
        <button
          class="pg-host-scheduler-operator-button"
          type="button"
          data-pg-scheduler-action="admit"
          data-pg-artifact-id="${escapeHtml(candidate.artifactId)}"
          data-pg-version="${escapeHtml(candidate.version)}"
          data-pg-inspect-binding-refs="${inspectBindingRefs}"
          ${actionRunning || alreadyAdmitted ? 'disabled' : ''}
        >${alreadyAdmitted ? 'Admitted' : 'Admit'}</button>
      </div>
    </div>
    ${bindingVisibility}
  </article>`;
}

function buildSchedulerOperatorCandidateBindingVisibility(
  candidate: SchedulerOperatorExchangeCandidate,
): string {
  const sections = [
    buildSchedulerBindingReferenceSummarySection(
      'Binding readiness',
      candidate.bindingReferenceReadiness,
      'current exact-version preflight',
    ),
    buildSchedulerBindingReferenceSummarySection(
      'Latest binding admission',
      candidate.latestBindingReferenceSummary,
      'latest ledger compact summary',
    ),
  ].filter(Boolean).join('');
  return sections
    ? `<div class="pg-host-scheduler-binding-visibility">${sections}</div>`
    : '';
}

function buildSchedulerBindingReferenceSummarySection(
  title: string,
  summary: SchedulerOperatorBindingReferenceSummary | null,
  subtitle: string,
): string {
  if (!summary) {
    return '';
  }
  const badgeStatus = summary.ok ? 'ok' : 'failed';
  const statusLabel = summary.status || (summary.ok ? 'ok' : 'not ok');
  const meta = [
    subtitle,
    `${summary.bindingRefCount} binding ref(s)`,
    `${summary.checkedRefCount} checked`,
    summary.errorCount ? `${summary.errorCount} error(s)` : '',
    summary.ledgerId ? `ledger=${summary.ledgerId}` : '',
    summary.actor ? `actor=${summary.actor}` : '',
    summary.rawEvidenceJsonRead ? 'raw evidence read=true' : 'raw evidence read=false',
  ].filter(Boolean).join(' · ');
  const taskRows = summary.tasks.length
    ? `<div class="pg-host-scheduler-binding-task-list">${summary.tasks.map(buildSchedulerBindingReferenceTaskRow).join('')}</div>`
    : '';
  const errors = summary.errors.length || summary.errorSummary
    ? buildHostEvidenceChipGroup('Binding errors', [
      ...summary.errors,
      summary.errorSummary,
    ].filter(Boolean))
    : '';
  return `<section class="pg-host-scheduler-binding-section" data-pg-binding-section="${escapeHtml(title)}" data-pg-binding-ok="${summary.ok ? 'true' : 'false'}">
    <div class="pg-host-scheduler-binding-head">
      <div>
        <h4 class="pg-host-scheduler-binding-title">${escapeHtml(title)}</h4>
        <p class="pg-host-scheduler-binding-meta">${escapeHtml(meta)}</p>
      </div>
      <span class="pg-host-evidence-badge" data-pg-evidence-status="${escapeHtml(badgeStatus)}">${escapeHtml(statusLabel)}</span>
    </div>
    ${taskRows}
    ${errors}
  </section>`;
}

function buildSchedulerBindingReferenceTaskRow(
  task: SchedulerOperatorBindingReferenceTaskSummary,
): string {
  const refs = task.bindingRefs.length
    ? task.bindingRefs.map((ref) => buildSchedulerBindingReferenceChip('input', ref)).join('')
    : '<span class="pg-host-evidence-chip"><span>input refs: none</span></span>';
  const checked = task.checkedRefs.length
    ? task.checkedRefs.map((ref) => buildSchedulerBindingReferenceChip('checked', ref)).join('')
    : '<span class="pg-host-evidence-chip"><span>checked refs: none</span></span>';
  const errors = task.errors.length
    ? buildHostEvidenceChipGroup('Task binding errors', task.errors)
    : '';
  const taskMeta = [
    `${task.bindingRefCount} input`,
    `${task.checkedRefCount} checked`,
    task.errorCount ? `${task.errorCount} error(s)` : '',
  ].filter(Boolean).join(' · ');
  return `<article class="pg-host-scheduler-binding-task" data-pg-binding-task-id="${escapeHtml(task.taskId)}">
    <p class="pg-host-scheduler-binding-task-title">${escapeHtml(task.taskId || 'unknown task')}${task.title ? ` · ${escapeHtml(task.title)}` : ''}</p>
    <p class="pg-host-scheduler-binding-meta">${escapeHtml(taskMeta)}</p>
    <div class="pg-host-scheduler-binding-ref-row">${refs}</div>
    <div class="pg-host-scheduler-binding-ref-row">${checked}</div>
    ${errors}
  </article>`;
}

function buildSchedulerBindingReferenceChip(
  prefix: string,
  ref: SchedulerOperatorBindingReference,
): string {
  const version = ref.version ? `@${ref.version}` : '';
  const path = ref.path ? ` · ${ref.path}` : '';
  const label = [
    `${prefix}: ${ref.refKind || 'ref'}`,
    `${ref.refId || 'unknown'}${version}`,
    ref.label,
  ].filter(Boolean).join(' · ');
  return `<span class="pg-host-evidence-chip"><span>${escapeHtml(`${label}${path}`)}</span></span>`;
}

function buildCompanionCard(state: ProgressGraphPreviewState): string {
  return `<section class="pg-host-control-card">
  <h2 class="pg-host-control-card-title">Bound Target Detail Companion</h2>
  <p class="pg-host-control-card-subtitle">当前由宿主负责把 raw target binding 解析到 display target，并在这里显示最小 runtime 摘要。</p>
  <p class="pg-host-control-card-subtitle" id="pgHostCompanionSummary">select a node</p>
  <div id="pgHostCompanionBody"><p class="pg-host-control-card-subtitle">${escapeHtml(
    state.controlSnapshot
      ? '选择图中的节点或 ready item 后，这里会显示对应的 runtime binding 摘要。'
      : controlSnapshotStatusMessage(state),
  )}</p></div>
</section>`;
}

function buildUnboundRuntimePanel(state: ProgressGraphPreviewState): string {
  return `<section class="pg-host-control-card">
  <h2 class="pg-host-control-card-title">Unbound Runtime Panel</h2>
  <p class="pg-host-control-card-subtitle">显式保留当前仍没有稳定 graph target 的 runtime rows，避免错误绑定。</p>
  <div id="pgHostUnboundBody"><p class="pg-host-control-card-subtitle">${escapeHtml(
    state.controlSnapshot
      ? '正在根据 bindings 和当前 graph payload 计算 unbound runtime rows。'
      : controlSnapshotStatusMessage(state),
  )}</p></div>
</section>`;
}

function buildHostEvidenceSection(state: ProgressGraphPreviewState): string {
  const presentation = state.hostEvidencePresentation;
  if (state.hostEvidencePresentationError) {
    return `<section id="pgHostEvidencePanel" class="pg-host-control-card pg-host-evidence-card" data-pg-host-evidence-status="failed">
  <div class="pg-host-evidence-head">
    <div class="pg-host-evidence-title-wrap">
      <h2 class="pg-host-control-card-title">Host Evidence</h2>
      <p class="pg-host-control-card-subtitle">resource=${escapeHtml(state.hostEvidencePresentationResourceUri)}</p>
    </div>
    <div class="pg-host-evidence-badge-row">
      <span class="pg-host-evidence-badge" data-pg-evidence-status="failed">read failed</span>
    </div>
  </div>
  <p class="pg-host-control-card-subtitle">${escapeHtml(state.hostEvidencePresentationError)}</p>
</section>`;
  }

  if (!presentation) {
    return `<section id="pgHostEvidencePanel" class="pg-host-control-card pg-host-evidence-card" data-pg-host-evidence-status="unavailable">
  <div class="pg-host-evidence-head">
    <div class="pg-host-evidence-title-wrap">
      <h2 class="pg-host-control-card-title">Host Evidence</h2>
      <p class="pg-host-control-card-subtitle">resource=${escapeHtml(state.hostEvidencePresentationResourceUri)}</p>
    </div>
    <div class="pg-host-evidence-badge-row">
      <span class="pg-host-evidence-badge" data-pg-evidence-status="unknown">unavailable</span>
    </div>
  </div>
  <p class="pg-host-control-card-subtitle">host evidence presentation resource has not been loaded.</p>
</section>`;
  }

  const statusBadge = `<span class="pg-host-evidence-badge" data-pg-evidence-status="${escapeHtml(presentation.status)}">${escapeHtml(presentation.status)}</span>`;
  const countBadges = [
    `<span class="pg-host-evidence-badge">cards ${escapeHtml(String(presentation.cardCount))}</span>`,
    `<span class="pg-host-evidence-badge">errors ${escapeHtml(String(presentation.errorCount))}</span>`,
  ].join('');
  const emptyMessage = !presentation.cards.length && !presentation.errorRows.length
    ? `<p class="pg-host-control-card-subtitle">${escapeHtml(presentation.emptyMessage || 'No host scheduler run evidence has been recorded.')}</p>`
    : '';
  const cards = presentation.cards.length
    ? `<div class="pg-host-evidence-list">${presentation.cards.map((card) => buildHostEvidenceCard(card)).join('')}</div>`
    : '';
  const errorRows = presentation.errorRows.length
    ? `<div class="pg-host-evidence-error-list">
      <p class="pg-host-evidence-group-title">Malformed evidence rows</p>
      ${presentation.errorRows.map((row) => buildHostEvidenceErrorRow(row)).join('')}
    </div>`
    : '';

  return `<section id="pgHostEvidencePanel" class="pg-host-control-card pg-host-evidence-card" data-pg-host-evidence-status="${escapeHtml(presentation.status)}">
  <div class="pg-host-evidence-head">
    <div class="pg-host-evidence-title-wrap">
      <h2 class="pg-host-control-card-title">Host Evidence</h2>
      <p class="pg-host-control-card-subtitle">resource=${escapeHtml(state.hostEvidencePresentationResourceUri)} · evidence_dir=${escapeHtml(presentation.evidenceDir || 'unknown')}</p>
    </div>
    <div class="pg-host-evidence-badge-row">${statusBadge}${countBadges}</div>
  </div>
  ${emptyMessage}
  ${cards}
  ${errorRows}
</section>`;
}

function buildHostEvidenceCard(card: ProgressGraphPreviewHostEvidenceCard): string {
  const facts = [
    ['Runtime providers', card.runtimeProviders.join(', ') || 'unknown'],
    ['Host surface', card.hostSurface || 'unknown'],
    ['Invocation', card.invocationId || 'unknown'],
    ['Stop reason', card.stopReason || 'unknown'],
    ['Runs', String(card.runCount)],
    ['Outputs', String(card.outputCount)],
    ['Permission reviews', String(card.permissionReviewCount)],
    ...card.keyFacts.map((fact) => [fact.label, fact.value] as [string, string]),
  ];
  const dedupedFacts = dedupeHostEvidenceFacts(facts);
  const factHtml = dedupedFacts.map(([label, value]) => (
    `<div class="pg-host-evidence-fact">
      <div class="pg-host-evidence-label">${escapeHtml(label)}</div>
      <div class="pg-host-evidence-value">${escapeHtml(value || 'unknown')}</div>
    </div>`
  )).join('');
  const refs = card.refs.length
    ? buildHostEvidenceChipGroup('Refs', card.refs.map((ref) => `${ref.label}: ${ref.target}`))
    : '';
  const authorityClues = card.authorityClues.length
    ? buildHostEvidenceChipGroup('Authority clues', card.authorityClues.map((fact) => `${fact.label}: ${fact.value}`))
    : '';
  const stopDetail = card.stopDetail
    ? buildHostEvidenceChipGroup('Stop detail', [card.stopDetail])
    : '';

  return `<article class="pg-host-evidence-run" data-pg-evidence-severity="${escapeHtml(card.severity)}">
    <div class="pg-host-evidence-run-head">
      <div>
        <h3 class="pg-host-evidence-run-title">${escapeHtml(card.title)}</h3>
        <p class="pg-host-evidence-run-subtitle">${escapeHtml([card.subtitle, formatTimestamp(card.timestamp)].filter(Boolean).join(' · '))}</p>
      </div>
      <span class="pg-host-evidence-badge" data-pg-evidence-status="${escapeHtml(card.status)}">${escapeHtml(card.status)}</span>
    </div>
    <div class="pg-host-evidence-facts">${factHtml}</div>
    ${stopDetail}
    ${refs}
    ${authorityClues}
  </article>`;
}

function buildHostEvidenceChipGroup(title: string, values: string[]): string {
  const chips = values
    .filter((value) => value.trim().length > 0)
    .map((value) => `<span class="pg-host-evidence-chip"><span>${escapeHtml(value)}</span></span>`)
    .join('');
  if (!chips) {
    return '';
  }
  return `<div class="pg-host-evidence-group">
    <p class="pg-host-evidence-group-title">${escapeHtml(title)}</p>
    <div class="pg-host-evidence-chip-row">${chips}</div>
  </div>`;
}

function buildHostEvidenceErrorRow(row: ProgressGraphPreviewHostEvidenceErrorRow): string {
  return `<div class="pg-host-evidence-error-row">
    <div class="pg-host-evidence-chip-row">
      <span class="pg-host-evidence-badge" data-pg-evidence-status="${escapeHtml(row.status)}">${escapeHtml(row.status)}</span>
      <span class="pg-host-evidence-badge" data-pg-evidence-status="${escapeHtml(row.severity)}">${escapeHtml(row.errorKind)}</span>
    </div>
    <div class="pg-host-evidence-value">${escapeHtml(row.evidencePath || row.id)}</div>
    <div class="pg-host-evidence-value">${escapeHtml(row.message)}</div>
  </div>`;
}

function dedupeHostEvidenceFacts(facts: [string, string][]): [string, string][] {
  const seen = new Set<string>();
  const result: [string, string][] = [];
  for (const [label, value] of facts) {
    const key = `${label}\u0000${value}`;
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);
    result.push([label, value]);
  }
  return result;
}

function controlSnapshotStatusMessage(state: ProgressGraphPreviewState): string {
  if (state.controlSnapshotError) {
    return `runtime snapshot 加载失败：${state.controlSnapshotError}`;
  }
  if (state.controlSnapshotExists) {
    return `runtime snapshot 当前不可用：${state.controlSnapshotPath}`;
  }
  return `runtime snapshot unavailable；等待 ${state.controlSnapshotPath} 出现后再接入 summary/binding surface。`;
}

function v2GraphUnavailableMessage(state: ProgressGraphPreviewState): string {
  if (state.v2GraphPayloadError) {
    return `V2 graph payload 加载失败：${state.v2GraphPayloadError}`;
  }
  if (!state.historyArtifactExists) {
    return `等待 ${state.historyArtifactPath} 出现后再构建 V2 graph payload。`;
  }
  if (!state.v2GraphScriptUri) {
    return '浏览器 bundle 尚未可用，当前无法挂载 Knowledge Graph Engine 图面。';
  }
  if (!state.v2GraphWorkerUri) {
    return 'force worker bundle 尚未可用，当前无法启动 Knowledge Graph Engine 布局。';
  }
  return '当前没有可用的 V2 graph payload。';
}

function getNonce(): string {
  let text = '';
  const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  for (let i = 0; i < 32; i++) {
    text += possible.charAt(Math.floor(Math.random() * possible.length));
  }
  return text;
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function formatTimestamp(value: string | null): string {
  if (!value) {
    return 'unknown';
  }

  const parsed = new Date(value);
  return Number.isNaN(parsed.valueOf())
    ? value
    : parsed.toLocaleString('zh-CN', { hour12: false });
}

function serializeJsonForHtml(value: unknown): string {
  return JSON.stringify(value).replace(/<\//g, '<\\/');
}

function buildControlOverlayEnhancementScript(): string {
  return `
  (() => {
    const overlay = document.querySelector('.pg-host-control-overlay');
    const companionSummary = document.getElementById('pgHostCompanionSummary');
    const companionBody = document.getElementById('pgHostCompanionBody');
    const unboundBody = document.getElementById('pgHostUnboundBody');
    const payloadEl = document.getElementById('pgHostControlSnapshotPayload');
    const graphPayloadCount = document.querySelectorAll('[data-role="graph-payload"]').length;
    const escapeHtml = (value) => String(value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/\"/g, '&quot;')
      .replace(/'/g, '&#39;');
    const toArray = (value) => Array.isArray(value) ? value : [];

    if (!(overlay instanceof HTMLElement) || !(companionBody instanceof HTMLElement) || !(unboundBody instanceof HTMLElement)) {
      return;
    }

    if (companionSummary instanceof HTMLElement) {
      companionSummary.textContent = graphPayloadCount > 0 ? 'select a node' : 'graph payload unavailable';
    }

    let snapshot = null;
    if (payloadEl?.textContent) {
      try {
        snapshot = JSON.parse(payloadEl.textContent);
      } catch {
        snapshot = null;
      }
    }

    const renderUnavailable = (message) => {
      if (companionSummary instanceof HTMLElement) {
        companionSummary.textContent = 'runtime snapshot unavailable';
      }
      companionBody.innerHTML = '<p class="pg-host-control-card-subtitle">' + escapeHtml(message) + '</p>';
      unboundBody.innerHTML = '<p class="pg-host-control-card-subtitle">' + escapeHtml(message) + '</p>';
    };

    if (!snapshot) {
      const status = overlay.dataset.controlSnapshotStatus || 'unavailable';
      const snapshotPath = overlay.dataset.controlSnapshotPath || 'unknown';
      const snapshotError = overlay.dataset.controlSnapshotError || 'unknown error';
      const message = status === 'failed'
        ? 'runtime snapshot 读取失败：' + snapshotError
        : '当前还没有可消费的 runtime snapshot。预留路径：' + snapshotPath;
      renderUnavailable(message);
      return;
    }

    const workItemsById = new Map(toArray(snapshot.work_items).map((item) => [String(item.work_item_id || ''), item]));
    const groupItemsById = new Map(toArray(snapshot.group_items).map((item) => [String(item.group_item_id || ''), item]));
    const rawToDisplayByGraph = new Map();
    const graphPayloadByGraph = new Map();

    for (const section of document.querySelectorAll('.graph-section[data-graph-id]')) {
      const graphId = section.getAttribute('data-graph-id') || '';
      const graphPayloadEl = section.querySelector('[data-role="graph-payload"]');
      if (!graphId || !graphPayloadEl?.textContent) {
        continue;
      }

      try {
        const graphPayload = JSON.parse(graphPayloadEl.textContent);
        graphPayloadByGraph.set(graphId, graphPayload);
        const rawToDisplay = new Map();
        for (const [displayId, node] of Object.entries(graphPayload.nodes || {})) {
          rawToDisplay.set(displayId, displayId);
          for (const rawId of toArray(node.memberIds)) {
            rawToDisplay.set(String(rawId), displayId);
          }
        }
        rawToDisplayByGraph.set(graphId, rawToDisplay);
      } catch {
        continue;
      }
    }

    const renderBindingRow = (row) => {
      const workDetails = toArray(row.work_item_ids).map((value) => {
        const workItemId = String(value);
        const workItem = workItemsById.get(workItemId);
        return workItem
          ? 'work ' + escapeHtml(workItemId) + ': ' + escapeHtml(String(workItem.lifecycle_state || 'unknown')) + ' · ' + escapeHtml(String(workItem.rollup_surface_kind || 'unknown')) + '/' + escapeHtml(String(workItem.rollup_surface_state || 'unknown'))
          : 'work ' + escapeHtml(workItemId);
      }).join('<br>');
      const groupDetails = toArray(row.group_item_ids).map((value) => {
        const groupItemId = String(value);
        const groupItem = groupItemsById.get(groupItemId);
        if (!groupItem) {
          return 'group ' + escapeHtml(groupItemId);
        }
        const blockedReason = groupItem.blocked_reason ? ' · blocked=' + escapeHtml(String(groupItem.blocked_reason)) : '';
        return 'group ' + escapeHtml(groupItemId) + ': ' + escapeHtml(String(groupItem.lifecycle_state || 'unknown')) + ' · ' + escapeHtml(String(groupItem.governance_surface_kind || 'unknown')) + '/' + escapeHtml(String(groupItem.governance_surface_state || 'unknown')) + ' · ' + escapeHtml(String(groupItem.delivery_surface_kind || 'unknown')) + '/' + escapeHtml(String(groupItem.delivery_state || 'unknown')) + blockedReason;
      }).join('<br>');
      const detailBlock = [workDetails, groupDetails].filter(Boolean).join('<br>');
      return '<li class="pg-host-control-item">'
        + '<div class="pg-host-control-item-title">' + escapeHtml(String(row.binding_id || 'unknown-binding')) + '</div>'
        + '<div class="pg-host-control-item-meta">kind=' + escapeHtml(String(row.binding_kind || 'unknown')) + ' · reason=' + escapeHtml(String(row.binding_reason || 'unknown')) + '</div>'
        + (detailBlock ? '<div class="pg-host-control-item-meta">' + detailBlock + '</div>' : '')
        + '</li>';
    };

    const boundRowsByDisplayKey = new Map();
    const unboundRows = [];
    for (const row of toArray(snapshot.bindings)) {
      if (String(row.binding_kind || '') === 'unbound-runtime-panel') {
        unboundRows.push(row);
        continue;
      }
      const graphId = String(row.graph_id || '');
      const rawTargetId = String(row.graph_target_id || '');
      const graphPayload = graphPayloadByGraph.get(graphId);
      const rawToDisplay = rawToDisplayByGraph.get(graphId);
      const displayId = rawToDisplay?.get(rawTargetId) || rawTargetId;
      if (!graphPayload || !displayId || !(graphPayload.nodes || {})[displayId]) {
        unboundRows.push(row);
        continue;
      }
      const displayKey = graphId + '::' + displayId;
      const rows = boundRowsByDisplayKey.get(displayKey) || [];
      rows.push(row);
      boundRowsByDisplayKey.set(displayKey, rows);
    }

    let stickySelection = null;
    let previewSelection = null;

    const effectiveSelection = () => previewSelection || stickySelection || { graphId: '', displayId: '' };

    const ensureHighlightMarkers = (section) => {
      const markerMap = new Map();
      const svg = section.querySelector('svg');
      const defs = svg?.querySelector('defs');
      if (!(svg instanceof SVGElement) || !(defs instanceof SVGElement)) {
        return markerMap;
      }

      for (const marker of defs.querySelectorAll('marker[id]')) {
        const markerId = marker.getAttribute('id') || '';
        if (!markerId) {
          continue;
        }
        const highlightedId = markerId + '-pg-active';
        let highlightedMarker = defs.querySelector('marker[id="' + highlightedId + '"]');
        if (!(highlightedMarker instanceof SVGElement)) {
          highlightedMarker = marker.cloneNode(true);
          highlightedMarker.setAttribute('id', highlightedId);
          for (const path of highlightedMarker.querySelectorAll('path')) {
            path.setAttribute('fill', 'rgba(86, 144, 191, 0.92)');
          }
          defs.appendChild(highlightedMarker);
        }
        markerMap.set(markerId, highlightedId);
      }

      return markerMap;
    };

    const applyGraphDecorations = () => {
      const { graphId: selectedGraphId, displayId: selectedDisplayId } = effectiveSelection();
      for (const section of document.querySelectorAll('.graph-section[data-graph-id]')) {
        const graphId = section.getAttribute('data-graph-id') || '';
        if (!graphId) {
          continue;
        }

        section.dataset.pgGraphMode = 'obsidianish';
        const hasSelection = graphId === selectedGraphId && !!selectedDisplayId;
        section.dataset.pgFocusActive = hasSelection ? 'true' : 'false';
        const highlightMarkers = ensureHighlightMarkers(section);

        const relatedNodeIds = new Set();
        if (hasSelection) {
          for (const edge of section.querySelectorAll('.edge.interactive-edge[data-source-id][data-target-id]')) {
            const sourceId = edge.getAttribute('data-source-id') || '';
            const targetId = edge.getAttribute('data-target-id') || '';
            if (sourceId === selectedDisplayId && targetId) {
              relatedNodeIds.add(targetId);
            }
            if (targetId === selectedDisplayId && sourceId) {
              relatedNodeIds.add(sourceId);
            }
          }
        }

        for (const group of section.querySelectorAll('g[data-node-id]')) {
          const displayId = group.getAttribute('data-node-id') || '';
          if (!displayId) {
            continue;
          }
          const displayKey = graphId + '::' + displayId;
          const hasRuntimeBinding = (boundRowsByDisplayKey.get(displayKey) || []).length > 0;
          const isSelected = hasSelection && displayId === selectedDisplayId;
          const isRelated = hasSelection && relatedNodeIds.has(displayId);
          group.dataset.pgRuntimeBound = hasRuntimeBinding ? 'true' : 'false';
          group.classList.toggle('pg-runtime-bound', hasRuntimeBinding);
          group.classList.toggle('pg-is-selected', isSelected);
          group.classList.toggle('pg-is-related', isRelated);
        }

        for (const item of section.querySelectorAll('.ready-item[data-display-id]')) {
          const displayId = item.getAttribute('data-display-id') || '';
          if (!displayId) {
            continue;
          }
          const isSelected = hasSelection && displayId === selectedDisplayId;
          const isRelated = hasSelection && relatedNodeIds.has(displayId);
          item.classList.toggle('pg-is-selected', isSelected);
          item.classList.toggle('pg-is-related', isRelated);
        }

        for (const edge of section.querySelectorAll('.edge.interactive-edge[data-source-id][data-target-id]')) {
          const sourceId = edge.getAttribute('data-source-id') || '';
          const targetId = edge.getAttribute('data-target-id') || '';
          const touchesSelected = hasSelection
            && (sourceId === selectedDisplayId || targetId === selectedDisplayId);
          const touchesRelated = hasSelection
            && !touchesSelected
            && (relatedNodeIds.has(sourceId) || relatedNodeIds.has(targetId));
          edge.classList.toggle('pg-is-selected', touchesSelected);
          edge.classList.toggle('pg-is-related', touchesRelated);

          const originalMarkerEnd = edge.dataset.pgOriginalMarkerEnd || edge.getAttribute('marker-end') || '';
          if (originalMarkerEnd && !edge.dataset.pgOriginalMarkerEnd) {
            edge.dataset.pgOriginalMarkerEnd = originalMarkerEnd;
          }
          if (originalMarkerEnd.startsWith('url(#') && (touchesSelected || touchesRelated)) {
            const markerId = originalMarkerEnd.slice(5, -1);
            const highlightedId = highlightMarkers.get(markerId);
            edge.setAttribute('marker-end', highlightedId ? 'url(#' + highlightedId + ')' : originalMarkerEnd);
          } else if (edge.dataset.pgOriginalMarkerEnd) {
            edge.setAttribute('marker-end', edge.dataset.pgOriginalMarkerEnd);
          }
        }
      }
    };

    const renderUnboundPanel = () => {
      if (!unboundRows.length) {
        unboundBody.innerHTML = '<p class="pg-host-control-card-subtitle">当前没有 unbound runtime rows。</p>';
        return;
      }
      unboundBody.innerHTML = '<ul class="pg-host-control-list">' + unboundRows.map((row) => renderBindingRow(row)).join('') + '</ul>';
    };

    const renderCompanion = (graphId, displayId) => {
      const displayKey = graphId + '::' + displayId;
      const rows = boundRowsByDisplayKey.get(displayKey) || [];
      if (companionSummary instanceof HTMLElement) {
        companionSummary.textContent = rows.length
          ? graphId + ' / ' + displayId
          : graphId + ' / ' + displayId + ' · no runtime binding';
      }
      if (!rows.length) {
        companionBody.innerHTML = '<p class="pg-host-control-card-subtitle">当前节点还没有稳定的 runtime binding；若相关 item 存在，它会落到 unbound runtime panel。</p>';
        return;
      }
      companionBody.innerHTML = '<ul class="pg-host-control-list">' + rows.map((row) => renderBindingRow(row)).join('') + '</ul>';
    };

    const setPreviewTarget = (graphId, displayId) => {
      previewSelection = graphId && displayId ? { graphId, displayId } : null;
      applyGraphDecorations();
    };

    const selectDisplayTarget = (graphId, displayId) => {
      stickySelection = { graphId, displayId };
      previewSelection = null;
      renderCompanion(graphId, displayId);
      applyGraphDecorations();
    };

    for (const section of document.querySelectorAll('.graph-section[data-graph-id]')) {
      const graphId = section.getAttribute('data-graph-id') || '';
      if (!graphId) {
        continue;
      }
      for (const group of section.querySelectorAll('g[data-node-id]')) {
        const displayId = group.getAttribute('data-node-id') || '';
        if (!displayId) {
          continue;
        }
        group.addEventListener('mouseenter', () => setPreviewTarget(graphId, displayId));
        group.addEventListener('mouseleave', () => setPreviewTarget('', ''));
        group.addEventListener('focus', () => setPreviewTarget(graphId, displayId));
        group.addEventListener('blur', () => setPreviewTarget('', ''));
        group.addEventListener('click', () => selectDisplayTarget(graphId, displayId));
        group.addEventListener('keydown', (event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            selectDisplayTarget(graphId, displayId);
          }
        });
      }
      for (const item of section.querySelectorAll('.ready-item[data-display-id]')) {
        const displayId = item.getAttribute('data-display-id') || '';
        if (!displayId) {
          continue;
        }
        item.addEventListener('mouseenter', () => setPreviewTarget(graphId, displayId));
        item.addEventListener('mouseleave', () => setPreviewTarget('', ''));
        item.addEventListener('focus', () => setPreviewTarget(graphId, displayId));
        item.addEventListener('blur', () => setPreviewTarget('', ''));
        item.addEventListener('click', () => selectDisplayTarget(graphId, displayId));
      }
    }

    applyGraphDecorations();
    renderUnboundPanel();
  })();`;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function readObjectArray(value: unknown): Record<string, unknown>[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter(isRecord);
}

function readObjectCollection(value: unknown): Record<string, unknown>[] {
  if (Array.isArray(value)) {
    return value.filter(isRecord);
  }
  if (isRecord(value)) {
    return Object.values(value).filter(isRecord);
  }
  return [];
}

function readString(value: unknown, fallback: string): string {
  return typeof value === 'string' ? value : fallback;
}

function readNullableString(value: unknown): string | null {
  return typeof value === 'string' ? value : null;
}

function readNumber(value: unknown): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : 0;
}

function readStringRecord(value: unknown): Record<string, string> {
  if (!isRecord(value)) {
    return {};
  }
  return Object.fromEntries(
    Object.entries(value)
      .filter((entry): entry is [string, string] => typeof entry[1] === 'string'),
  );
}

function readHostEvidenceFacts(value: unknown): ProgressGraphPreviewHostEvidenceFact[] {
  return readObjectArray(value).map((item) => ({
    label: readString(item.label, 'unknown'),
    value: readString(item.value, ''),
  }));
}

function readHostEvidenceRefs(value: unknown): ProgressGraphPreviewHostEvidenceRef[] {
  return readObjectArray(value).map((item) => ({
    label: readString(item.label, 'unknown'),
    target: readString(item.target, ''),
    refKind: readString(item.ref_kind, readString(item.refKind, 'path')),
  }));
}

function readStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is string => typeof item === 'string');
}

function readUnknownStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .filter((item) => typeof item === 'string' || typeof item === 'number')
    .map((item) => String(item));
}

function injectIntoHtmlDocument(
  html: string,
  injections: {
    beforeHeadClose?: string;
    afterBodyOpen?: string;
    beforeBodyClose?: string;
  },
): string {
  let result = html;

  if (injections.beforeHeadClose) {
    result = result.match(/<\/head>/i)
      ? result.replace(/<\/head>/i, `${injections.beforeHeadClose}\n</head>`)
      : `${injections.beforeHeadClose}\n${result}`;
  }

  if (injections.afterBodyOpen) {
    result = result.match(/<body[^>]*>/i)
      ? result.replace(/<body([^>]*)>/i, `<body$1>\n${injections.afterBodyOpen}`)
      : `${injections.afterBodyOpen}\n${result}`;
  }

  if (injections.beforeBodyClose) {
    result = result.match(/<\/body>/i)
      ? result.replace(/<\/body>/i, `${injections.beforeBodyClose}\n</body>`)
      : `${result}\n${injections.beforeBodyClose}`;
  }

  return result;
}
