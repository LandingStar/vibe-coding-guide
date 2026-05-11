import assert from 'node:assert/strict';
import test from 'node:test';

import {
  buildProgressGraphPreviewHtml,
  coerceControlSnapshot,
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
    v2GraphScriptUri: null,
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

test('buildProgressGraphPreviewHtml exposes failed control snapshot status when snapshot parsing failed', () => {
  const html = buildProgressGraphPreviewHtml(buildBaseState({
    controlSnapshotExists: true,
    controlSnapshotError: 'unexpected token',
  }));

  assert.match(html, /data-control-snapshot-status="failed"/);
  assert.match(html, /runtime snapshot 加载失败：unexpected token/);
});

test('buildProgressGraphPreviewHtml injects G6 graph PoC shell when V2 payload is available', () => {
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
    v2GraphScriptUri: 'vscode-webview-resource://test/progressGraphV2G6.js',
  }));

  assert.match(html, /G6 Graph View PoC/);
  assert.match(html, /Planning Gates Index/);
  assert.match(html, /graph_id=planning-gates-index/);
  assert.match(html, /id="pgHostChromeDock"/);
  assert.match(html, /id="pgHostChromePeek"/);
  assert.match(html, /id="pgHostCollapsePanel"/);
  assert.match(html, /Show Progress Graph Panel/);
  assert.match(html, /Collapse Panel/);
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
  assert.match(html, /id="pgHostV2NodeDetailCard"/);
  assert.match(html, /id="pgHostV2MetricsDock"/);
  assert.match(html, /id="pgHostV2MetricsInline"/);
  assert.match(html, /id="pgHostV2MetricsSide"/);
  assert.match(html, /id="pgHostV2ResetViewport"/);
  assert.match(html, /Reset Zoom\/Pan/);
  assert.match(html, /id="pgHostV2AppearanceLabelDensity"/);
  assert.match(html, /id="pgHostV2ForceGravity"/);
  assert.match(html, /id="pgHostV2ColorGroups"/);
  assert.match(html, /id="pgHostV2AddColorGroup"/);
  assert.match(html, /Search 风格的查询语义/);
  assert.match(html, /globalThis\.__pgHostVsCodeApi = vscode/);
  assert.match(html, /progressGraphV2G6\.js/);
});