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
  previewExists: boolean;
  previewHtml: string | null;
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

function buildParallelPreviewHtml(
  state: ProgressGraphPreviewState,
  previewHtml: string,
): string {
  const controlOverlay = buildControlOverlay(state);
  const v2GraphPoC = buildV2GraphPoCSection(state);
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
  .pg-host-chrome-content {
    display: grid;
    overflow: hidden;
    max-height: var(--pg-host-chrome-expanded-height, 960px);
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
    position: absolute;
    top: 8px;
    left: 50%;
    transform: translate(-50%, -10px);
    visibility: hidden;
    opacity: 0;
    pointer-events: none;
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 999px;
    background: rgba(17, 26, 34, 0.92);
    color: rgba(248, 244, 239, 0.82);
    padding: 6px 12px;
    font: inherit;
    font-size: 0.76rem;
    font-weight: 700;
    letter-spacing: 0.02em;
    cursor: pointer;
    backdrop-filter: blur(16px);
    box-shadow: 0 10px 22px rgba(0, 0, 0, 0.18);
    transition: opacity 140ms ease, transform 140ms ease, visibility 140ms ease;
  }
  .pg-host-chrome-dock[data-pg-host-shell="collapsed"][data-pg-host-shell-peek="visible"] .pg-host-chrome-peek,
  .pg-host-chrome-peek:focus-visible {
    visibility: visible;
    opacity: 1;
    pointer-events: auto;
    transform: translate(-50%, 0);
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
  .pg-host-v2-poc {
    margin: 18px;
    padding: 18px;
    display: flex;
    flex-direction: column;
    min-height: max(620px, calc(100vh - 220px));
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
    min-height: max(560px, 100%);
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
    overflow: visible;
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
    .pg-host-chrome-peek {
      left: 16px;
      transform: translateY(-10px);
    }
    .pg-host-chrome-dock[data-pg-host-shell="collapsed"][data-pg-host-shell-peek="visible"] .pg-host-chrome-peek,
    .pg-host-chrome-peek:focus-visible {
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
    .pg-host-v2-poc {
      min-height: auto;
    }
    .pg-host-v2-head-actions,
    .pg-host-v2-meta {
      align-items: flex-start;
      justify-content: flex-start;
    }
    .pg-host-v2-canvas-shell {
      min-height: clamp(420px, 56vh, 760px);
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
    <div class="pg-host-actions">
      <button id="pgHostRefreshButton" class="pg-host-button" ${state.isRefreshRunning ? 'disabled' : ''}>${state.isRefreshRunning ? 'Refreshing...' : 'Refresh Preview'}</button>
      <button id="pgHostRevealButton" class="pg-host-button secondary">Reveal Artifact</button>
      <button id="pgHostCollapsePanel" type="button" class="pg-host-button collapse">Collapse Panel</button>
    </div>
  </div>
  <div class="pg-host-status-strip">
    <p class="pg-host-status-message">${escapedFreshnessMessage}</p>
    ${refreshError}
  </div>
</section>`;
  const hostChrome = `<div id="pgHostChromeDock" class="pg-host-chrome-dock" data-pg-host-shell="expanded" data-pg-host-shell-peek="hidden">
  <button id="pgHostChromePeek" type="button" class="pg-host-chrome-peek" aria-controls="pgHostChromeContent" aria-expanded="true">Show Progress Graph Panel</button>
  <div id="pgHostChromeContent" class="pg-host-chrome-content">
    ${hostShell}
    ${controlOverlay}
  </div>
</div>`;
  const v2GraphScript = state.v2GraphPayload && state.v2GraphScriptUri
    ? `<script src="${escapeHtml(state.v2GraphScriptUri)}"></script>`
    : '';
  const hostScript = `<script>
  const vscode = acquireVsCodeApi();
  globalThis.__pgHostVsCodeApi = vscode;
  const hostChromeDock = document.getElementById('pgHostChromeDock');
  const hostChromeContent = document.getElementById('pgHostChromeContent');
  const hostChromePeek = document.getElementById('pgHostChromePeek');
  const collapsePanelButton = document.getElementById('pgHostCollapsePanel');
  document.getElementById('pgHostRefreshButton')?.addEventListener('click', () => {
    vscode.postMessage({ command: 'refresh' });
  });
  document.getElementById('pgHostRevealButton')?.addEventListener('click', () => {
    vscode.postMessage({ command: 'revealArtifact' });
  });
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

    const persistHostChromeState = () => {
      const currentState = vscode.getState?.() ?? {};
      vscode.setState?.({ ...currentState, [stateKey]: collapsed });
    };

    const applyHostChromeState = () => {
      syncHostChromeHeight();
      hostChromeDock.dataset.pgHostShell = collapsed ? 'collapsed' : 'expanded';
      hostChromePeek.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
      collapsePanelButton?.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
      setPeekVisible(false);
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
      if (!collapsed) {
        return;
      }
      setPeekVisible(event.clientY <= 42);
    });
    document.addEventListener('pointerleave', () => {
      if (!collapsed) {
        return;
      }
      setPeekVisible(false);
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
  ${buildControlOverlayEnhancementScript()}
</script>`;

  return injectIntoHtmlDocument(previewHtml, {
    beforeHeadClose: hostStyle,
    afterBodyOpen: `${hostChrome}\n${v2GraphPoC}`,
    beforeBodyClose: `${hostScript}\n${v2GraphScript}`,
  });
}

function buildV2GraphPoCSection(state: ProgressGraphPreviewState): string {
  if (!state.v2GraphPayload || !state.v2GraphScriptUri) {
    return `<section class="pg-host-v2-poc" data-pg-v2-status="unavailable">
  <div class="pg-host-v2-head">
    <div class="pg-host-v2-title-wrap">
      <div class="pg-host-v2-eyebrow">G6 Graph View PoC</div>
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
    '<span class="pg-host-v2-meta-pill">Mode G6 graph-view PoC</span>',
    `<span class="pg-host-v2-meta-pill">Bound ${escapeHtml(String(runtimeSummary.boundNodeCount))}</span>`,
    `<span class="pg-host-v2-meta-pill">Runtime groups ${escapeHtml(String(runtimeSummary.activeGroupItemCount))}</span>`,
  ].join('');

  return `<section class="pg-host-v2-poc" data-pg-v2-status="available">
  <div class="pg-host-v2-head">
    <div class="pg-host-v2-title-wrap">
      <div class="pg-host-v2-eyebrow">G6 Graph View PoC</div>
      <h2 class="pg-host-v2-title">${escapeHtml(payload.title)}</h2>
      <p class="pg-host-v2-subtitle">${subtitleParts.join(' · ')}</p>
    </div>
    <div class="pg-host-v2-head-actions">
      <div class="pg-host-v2-meta">${meta}</div>
      <button id="pgHostV2ResetViewport" type="button" class="pg-host-v2-reset-button">Reset Zoom/Pan</button>
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
      </div>
    </div>
    <div id="pgHostV2ResizeHandle" class="pg-host-v2-resize-handle" data-pg-dragging="false" role="separator" aria-orientation="vertical" aria-label="Resize graph and side panel"></div>
    <div id="pgHostV2Side" class="pg-host-v2-side" data-pg-config-collapsed="false">
      ${buildV2GraphConfigCard()}
      <section id="pgHostV2MetricsSide" class="pg-host-v2-metrics pg-host-v2-metrics-side" data-pg-config-collapsed="false">${metrics}</section>
      <section id="pgHostV2NodeDetailCard" class="pg-host-v2-card pg-host-v2-detail-card">
        <h3 class="pg-host-v2-card-title">Node Detail</h3>
        <div id="pgHostV2GraphDetail" class="pg-host-v2-detail-body">
          <p class="pg-host-v2-detail-empty">悬停或点击节点后，这里会显示 kind、status、summary 与 runtime binding 摘要。</p>
        </div>
      </section>
    </div>
  </div>
  <script type="application/json" id="pgHostV2GraphPayload">${serializeJsonForHtml(payload)}</script>
</section>`;
}

function buildV2GraphConfigCard(): string {
  return `<section id="pgHostV2ConfigCard" class="pg-host-v2-card pg-host-v2-config-card" data-pg-config-collapsed="false">
  <div id="pgHostV2ConfigCardContent" class="pg-host-v2-config-card-content">
  <div class="pg-host-v2-config-card-head">
    <div class="pg-host-v2-config-card-copy">
      <h3 id="pgHostV2ConfigCardTitle" class="pg-host-v2-card-title pg-host-v2-config-card-title pg-host-v2-config-title-text">Graph Config</h3>
      <p class="pg-host-v2-card-subtitle">当前 G6 图面已稳定到可继续增量收口；颜色组现已回到当前切片，并继续沿用 Search 风格的查询语义。</p>
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
        <input id="pgHostV2AppearanceLabelDensity" class="pg-host-v2-config-range" type="range" min="0.06" max="0.3" step="0.01" value="0.14">
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
          <output id="pgHostV2AppearanceNodeScaleValue" class="pg-host-v2-config-value">1.00x</output>
        </div>
        <input id="pgHostV2AppearanceNodeScale" class="pg-host-v2-config-range" type="range" min="0.75" max="1.6" step="0.05" value="1">
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
    return '浏览器 bundle 尚未可用，当前无法挂载 G6 graph-view PoC。';
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

function readString(value: unknown, fallback: string): string {
  return typeof value === 'string' ? value : fallback;
}

function readNullableString(value: unknown): string | null {
  return typeof value === 'string' ? value : null;
}

function readNumber(value: unknown): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : 0;
}

function readStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is string => typeof item === 'string');
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