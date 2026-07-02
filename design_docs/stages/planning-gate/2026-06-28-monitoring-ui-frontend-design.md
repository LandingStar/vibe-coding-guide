# Monitoring UI Frontend Design

> Date: 2026-06-28
> Status: DESIGN DRAFT — pending user review before implementation
> Backend API: `docs/monitoring-ui-backend-api.md` (COMPLETED)
> Frontend expectations: `design_docs/monitoring-ui-frontend-expectations.md`

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  VS Code Extension Host (Node.js)                               │
│                                                                 │
│  MonitoringPanel (WebviewPanel manager)                         │
│    ├─ spawn CLI: python -m src scheduler                        │
│    │   inspect-monitoring-snapshot --snapshot-path ...           │
│    ├─ parse JSON stdout → MonitoringSnapshot payload            │
│    ├─ serialize into <script type="application/json">           │
│    └─ handle postMessage from webview:                          │
│        ├─ { command: 'refresh' }       → re-run CLI            │
│        ├─ { command: 'autoRefresh',    → start/stop timer      │
│        │   enabled: boolean }                                   │
│        └─ { command: 'copyToClipboard', → vscode.clipboard     │
│             text: string }                                      │
│                                                                 │
│  on webview.html assignment → injects:                          │
│    ├─ <link> monitoringDashboard.css (bundled)                  │
│    ├─ <script type="application/json" id="monitoringPayload">   │
│    └─ <script> monitoringDashboard.js (bundled IIFE)            │
└─────────────────────────────────────────────────────────────────┘
         │  webview.html
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  React Webview (Browser iframe)                                 │
│                                                                 │
│  main() → readPayload() → <MonitoringApp />                    │
│    ├─ <StatusStrip />                                           │
│    ├─ <SchedulerPanel />                                        │
│    ├─ <DeliveryPanel />                                         │
│    ├─ <RuntimePanel />                                          │
│    ├─ <LiveCodexSmokePanel />                                   │
│    ├─ <WorkerReportsPanel />                                    │
│    └─ <Toolbar /> (refresh, auto-refresh toggle, interval)      │
│                                                                 │
│  postMessage → host for refresh/autoRefresh/copyToClipboard     │
└─────────────────────────────────────────────────────────────────┘
```

### Key Difference From Local Work Trajectory

The LWT component is read-only (no postMessage back to host). The monitoring UI
needs bidirectional communication because:

1. User triggers refresh → host re-runs CLI → re-injects payload
2. User toggles auto-refresh → host manages timer, pushes new payloads
3. User copies path → host uses `vscode.env.clipboard`

### Data Refresh Strategy

- **Initial load**: payload injected via `<script type="application/json">`
- **Refresh / auto-refresh**: host updates `webview.html` entirely (same as ProgressGraphPreviewPanel's approach)
  - Alternative considered: postMessage-based incremental update → rejected because it adds state sync complexity for a polling dashboard
- **Shell signature**: like ProgressGraphPreviewPanel, skip re-render if the payload fingerprint hasn't changed

---

## 2. File Structure

### New Files

| File | Purpose |
|------|---------|
| `vscode-extension/src/webviews/monitoringDashboard.tsx` | React app — all panels and components |
| `vscode-extension/src/webviews/monitoringDashboard.css` | CSS — compact operational theme |
| `vscode-extension/src/views/monitoringPanel.ts` | WebviewPanel manager — CLI invocation, message handling |

### Modified Files

| File | Change |
|------|--------|
| `vscode-extension/src/extension.ts` | Register `MonitoringPanel` instance + commands |
| `vscode-extension/package.json` | Add commands + view contribution (optional) |
| `vscode-extension/esbuild.config.mjs` | Add `monitoringDashboard` to webview entryPoints |

### Built Output

| File | Source |
|------|--------|
| `dist/webviews/monitoringDashboard.js` | IIFE bundle of React app |
| `dist/webviews/monitoringDashboard.css` | Extracted CSS |

---

## 3. Component Hierarchy

```
MonitoringApp
├── Toolbar
│   ├── RefreshButton
│   ├── AutoRefreshToggle (checkbox + interval display)
│   ├── SchemaBadge (schema_version)
│   └── LastUpdatedTimestamp
├── StatusStrip
│   ├── OkBadge (ok: true/false)
│   ├── NextAction (next_action text)
│   ├── AuthorityIntegrityCheck (authoritySplit validation)
│   └── TopOperatorSignals (highest severity signals, max 3)
├── PanelGrid (2-column responsive grid)
│   ├── SchedulerPanel
│   │   ├── StateCountBadges (task_state_counts)
│   │   ├── TargetTaskTable (target_task_states)
│   │   ├── WaitingTaskList (waiting_task_ids)
│   │   └── ReviewRequiredList (review_required_task_ids)
│   ├── DeliveryPanel
│   │   ├── StateCountBadges (state_counts)
│   │   ├── PendingCodexCount (actionable_pending_codex_delivery_count)
│   │   ├── FailedDeliveryTable (filtered latest_records where delivery_state=failed)
│   │   └── ReviewRequiredTable (filtered latest_records where delivery_state=review_required)
│   ├── RuntimePanel (spans full width)
│   │   ├── InvocationCountBadges (counts)
│   │   ├── ConcurrencySummary (concurrency.latestProviderCounts, liveOverlapProven)
│   │   ├── FilterBar (provider / status / lane dropdowns)
│   │   ├── InvocationTable (latest_records, sortable columns)
│   │   └── InvocationDetailDrawer (expandable row detail)
│   ├── LiveCodexSmokePanel
│   │   ├── AvailabilityBadge (exists + verdict)
│   │   ├── VerdictBadge (passed/failed/unavailable)
│   │   ├── WorkerCounts (counts)
│   │   ├── FirstConcurrentBatch (taskIds, invocationIds)
│   │   ├── OverlapPairSummary (proven, pairs count)
│   │   └── OverlapPairDetail (expandable)
│   └── WorkerReportsPanel
│       ├── ModeNote (mode: leader-owned-consumer)
│       ├── ProcedureLink (procedureDoc → open in editor)
│       ├── SchemaLink (schema → open in editor)
│       ├── ConsumerCommand (copyable command string)
│       └── BoundaryNote ("monitoring does not consume reports")
└── ErrorDrawer (collapsible, shows errors[] if non-empty)
```

---

## 4. Data Model (TypeScript Types)

```typescript
// monitoring-types.ts (inline in monitoringDashboard.tsx)

interface MonitoringSnapshot {
  schema_version: string;
  ok: boolean;
  next_action: string;
  paths: MonitoringPaths;
  scheduler: SchedulerSection;
  delivery: DeliverySection;
  runtimeInvocations: RuntimeInvocationsSection;
  artifacts: ArtifactsSection;
  liveCodexSmoke: LiveCodexSmokeSection;
  workerReports: WorkerReportsSection;
  operatorSignals: OperatorSignal[];
  errors: string[];
  authoritySplit: AuthoritySplitSection;
}

interface MonitoringPaths {
  scheduler_snapshot_path: string;
  scheduler_event_log_path: string;
  delivery_state_path?: string;
  runtime_invocation_log_path?: string;
  artifact_store_path?: string;
  live_codex_smoke_report_path?: string;
}

interface SchedulerSection {
  task_state_counts: Record<string, number>;
  target_task_states: Record<string, string>;
  waiting_task_ids: string[];
  review_required_task_ids: string[];
  completed_task_output_refs: CompletedTaskOutputRef[];
}

interface CompletedTaskOutputRef {
  task_id: string;
  ref_kind: string;
  ref_id: string;
  version: string;
}

interface DeliverySection {
  state_counts: Record<string, number>;
  actionable_pending_codex_delivery_count: number;
  latest_records: DeliveryRecord[];
}

interface DeliveryRecord {
  delivery_id: string;
  source_key: string;
  decision_id: string;
  tick_id: string;
  dispatcher_id: string;
  event_kind: string;
  agent_id: string;
  role: string;
  next_action: string;
  lane_id: string;
  task_id: string;
  source: string;
  reason: string;
  delivery_state: string;
  created_at: string;
  updated_at: string;
  delivered_at: string;
  review_required_at: string;
  acknowledged_at: string;
  failed_at: string;
  host_id: string;
  runtime_provider: string;
  runtime_session_id: string;
  runtime_run_id: string;
  invocation_id: string;
  delivery_attempt_count: number;
  failure_kind: string;
  failure_detail: string;
  metadata: Record<string, any>;
}

interface RuntimeInvocationsSection {
  counts: Record<string, number>;
  latest_records: RuntimeInvocationRecord[];
  concurrency: ConcurrencySummary;
}

interface RuntimeInvocationRecord {
  schema_version: string;
  invocation_id: string;
  provider: string;
  status: string;
  started_at: string;
  ended_at: string;
  task_id: string;
  session_id: string;
  run_id: string;
  agent_id: string;
  runtime_surface: string;
  attempt_count: number;
  retry_policy: { max_attempts: number; backoff_seconds: number };
  attempts: AttemptRecord[];
  final_error_kind: string;
  final_summary: string;
  metadata: Record<string, any>;
  authority_split: {
    runtime_invocation_authority: string;
    raw_transcript_persisted: boolean;
    scheduler_state_mutated: boolean;
    exchange_store_mutated: boolean;
    local_work_trajectory_mutated: boolean;
  };
}

interface AttemptRecord {
  attempt_index: number;
  started_at: string;
  ended_at: string;
  status: string;
  retryable: boolean;
  error_kind: string;
  raw_error_type: string;
  summary: string;
  metadata: Record<string, any>;
  stdout_bytes?: number;
  stderr_bytes?: number;
}

interface ConcurrencySummary {
  latestProviderCounts: Record<string, number>;
  failedTaskIds: string[];
  latestRecords: ConcurrencyRecord[];
  liveOverlapProven: boolean;
  overlapPairCount: number;
}

interface ConcurrencyRecord {
  invocationId: string;
  provider: string;
  status: string;
  taskId: string;
  agentId: string;
  laneId: string;
  startedAt: string;
  endedAt: string;
}

interface LiveCodexSmokeSection {
  exists: boolean;
  ok: boolean;
  verdict: string;
  diagnostic: string;
  path: string;
  counts: Record<string, any>;
  firstConcurrentBatch: { taskIds: string[]; invocationIds: string[] };
  overlap: { proven: boolean; pairs: any[]; timingParseErrors?: string[] };
  residualGaps?: any[];
  errors?: string[];
}

interface WorkerReportsSection {
  mode: string;
  directWorkerTrajectoryMutationAllowed: boolean;
  consumerCommand: string;
  procedureDoc: string;
  schema: string;
  notes: string[];
}

interface OperatorSignal {
  severity: 'error' | 'warning' | 'info' | 'ok';
  kind: string;
  message: string;
  suggestedAction: string;
}

interface AuthoritySplitSection {
  readModelOnly: boolean;
  providerExecuted: boolean;
  schedulerStateMutated: boolean;
  schedulerEventLogMutated: boolean;
  dispatcherStateMutated: boolean;
  deliveryStateMutated: boolean;
  deliveryLogMutated: boolean;
  exchangeStoreMutated: boolean;
  runtimeInvocationLogMutated: boolean;
  localWorkTrajectoryMutated: boolean;
  rawTranscriptExposed: boolean;
}
```

---

## 5. Extension Host: MonitoringPanel

```typescript
// vscode-extension/src/views/monitoringPanel.ts

export class MonitoringPanel implements vscode.Disposable {
  private _panel: vscode.WebviewPanel | undefined;
  private _autoRefreshTimer: NodeJS.Timer | undefined;
  private _autoRefreshInterval = 5000; // ms
  private _lastPayload: MonitoringSnapshot | undefined;
  private _disposables: vscode.Disposable[] = [];

  constructor(
    private readonly _extensionUri: vscode.Uri,
    private readonly _outputChannel: vscode.OutputChannel,
  ) {}

  async open(workspace: vscode.WorkspaceFolder): Promise<void> {
    if (!this._panel) {
      this._panel = vscode.window.createWebviewPanel(
        'docBasedCoding.monitoringDashboard',
        'Monitoring Dashboard',
        vscode.ViewColumn.Two,
        {
          enableScripts: true,
          enableFindWidget: true,
          retainContextWhenHidden: true,
          localResourceRoots: [
            workspace.uri,
            vscode.Uri.joinPath(this._extensionUri, 'dist'),
          ],
        },
      );
      this._panel.onDidDispose(() => { this._panel = undefined; }, null, this._disposables);
      this._panel.webview.onDidReceiveMessage(msg => this._handleMessage(msg, workspace), null, this._disposables);
    }
    this._panel.reveal();
    await this._refreshSnapshot(workspace);
  }

  private async _handleMessage(msg: any, workspace: vscode.WorkspaceFolder): Promise<void> {
    switch (msg.command) {
      case 'refresh':
        await this._refreshSnapshot(workspace);
        break;
      case 'autoRefresh':
        this._setAutoRefresh(msg.enabled, workspace);
        break;
      case 'copyToClipboard':
        await vscode.env.clipboard.writeText(msg.text);
        break;
      case 'openDocument':
        // Open a workspace-relative doc in the editor
        const docPath = vscode.Uri.joinPath(workspace.uri, msg.path);
        await vscode.window.showTextDocument(await vscode.workspace.openTextDocument(docPath));
        break;
    }
  }

  private async _refreshSnapshot(workspace: vscode.WorkspaceFolder): Promise<void> {
    try {
      const payload = await runMonitoringSnapshotCLI(workspace.uri.fsPath);
      this._lastPayload = payload;
      this._render(payload);
    } catch (err) {
      this._outputChannel.appendLine(`[monitoring] snapshot error: ${err}`);
      this._renderError(String(err));
    }
  }

  private _setAutoRefresh(enabled: boolean, workspace: vscode.WorkspaceFolder): void {
    if (this._autoRefreshTimer) {
      clearInterval(this._autoRefreshTimer);
      this._autoRefreshTimer = undefined;
    }
    if (enabled) {
      this._autoRefreshTimer = setInterval(
        () => this._refreshSnapshot(workspace),
        this._autoRefreshInterval,
      );
    }
  }

  private _render(payload: MonitoringSnapshot): void {
    if (!this._panel) return;
    this._panel.webview.html = buildMonitoringHtml(
      this._panel.webview,
      this._extensionUri,
      payload,
    );
  }

  dispose(): void {
    if (this._autoRefreshTimer) clearInterval(this._autoRefreshTimer);
    this._panel?.dispose();
    this._disposables.forEach(d => d.dispose());
  }
}
```

### CLI Invocation

```typescript
async function runMonitoringSnapshotCLI(workspaceRoot: string): Promise<MonitoringSnapshot> {
  const { execFile } = await import('child_process');
  const { promisify } = await import('util');
  const exec = promisify(execFile);

  const pythonPath = await resolvePythonPath(workspaceRoot);
  const codexDir = path.join(workspaceRoot, '.codex');

  const args = [
    '-m', 'src', 'scheduler', 'inspect-monitoring-snapshot',
    '--snapshot-path', path.join(codexDir, 'scheduler', 'state.json'),
    '--event-log-path', path.join(codexDir, 'scheduler', 'events.jsonl'),
    '--delivery-state-path', path.join(codexDir, 'scheduler', 'delivery-state.json'),
    '--runtime-invocation-log-path', path.join(codexDir, 'runtime', 'invocations.jsonl'),
    '--artifact-store-path', path.join(codexDir, 'orchestration', 'exchange-artifacts.json'),
    '--live-codex-smoke-report-path', path.join(codexDir, 'scheduler', 'smoke-report.json'),
  ];

  const { stdout } = await exec(pythonPath, args, {
    cwd: workspaceRoot,
    timeout: 15000,
  });

  return JSON.parse(stdout) as MonitoringSnapshot;
}
```

Note: the actual file paths need to be resolved from the project configuration
or discovered dynamically. The above shows the pattern.

---

## 6. HTML Builder

```typescript
// Inline in monitoringPanel.ts or separate monitoringPanelHtml.ts

function buildMonitoringHtml(
  webview: vscode.Webview,
  extensionUri: vscode.Uri,
  payload: MonitoringSnapshot,
): string {
  const scriptUri = webview.asWebviewUri(
    vscode.Uri.joinPath(extensionUri, 'dist', 'webviews', 'monitoringDashboard.js'),
  );
  const styleUri = webview.asWebviewUri(
    vscode.Uri.joinPath(extensionUri, 'dist', 'webviews', 'monitoringDashboard.css'),
  );
  const nonce = generateNonce();

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="Content-Security-Policy"
        content="default-src 'none'; style-src ${webview.cspSource}; script-src 'nonce-${nonce}';">
  <link rel="stylesheet" href="${styleUri}">
  <title>Monitoring Dashboard</title>
</head>
<body>
  <div id="monitoring-root"></div>
  <script type="application/json" id="monitoringPayload">${
    JSON.stringify(payload).replace(/</g, '\\u003c')
  }</script>
  <script nonce="${nonce}" src="${scriptUri}"></script>
</body>
</html>`;
}
```

---

## 7. Visual Layout

### 7.1 Overall Structure

```
┌──────────────────────────────────────────────────────────────────────┐
│ Toolbar: [↻ Refresh] [☐ Auto-refresh 5s] Schema: v1 Updated: 14:32  │
├──────────────────────────────────────────────────────────────────────┤
│ StatusStrip                                                          │
│ ┌──────┐ ┌──────────────────────────────┐ ┌───────────────────────┐ │
│ │ OK ✓ │ │ Next: review failed delivery │ │ ⚠ 2 signals           │ │
│ └──────┘ └──────────────────────────────┘ └───────────────────────┘ │
├──────────────────────────────────────────────────────────────────────┤
│ Scheduler              │ Delivery                                    │
│ ┌────────────────────┐ │ ┌────────────────────────────────────────┐  │
│ │ complete: 5        │ │ │ pending: 2   delivered: 3  failed: 1   │  │
│ │ ready: 2           │ │ │                                        │  │
│ │ waiting: 1         │ │ │ Pending Codex: 2                       │  │
│ │ review_required: 1 │ │ │                                        │  │
│ │                    │ │ │ Failed Deliveries:                     │  │
│ │ Waiting: [T-007]   │ │ │  #D-004 agent-x failed_at 14:30       │  │
│ │ Review:  [T-003]   │ │ │  reason: timeout                       │  │
│ └────────────────────┘ │ └────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────────────────┤
│ Runtime Invocations (full width)                                     │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │ Total: 12  Succeeded: 10  Failed: 2                             │ │
│ │ Providers: codex:8  opencode:4   Overlap proven: ✓              │ │
│ │                                                                  │ │
│ │ Filter: [Provider ▼] [Status ▼] [Lane ▼]                        │ │
│ │                                                                  │ │
│ │ ┌──────────────────────────────────────────────────────────────┐ │ │
│ │ │ ID     │ Provider │ Status    │ Lane  │ Task  │ Started      │ │ │
│ │ ├────────┼──────────┼───────────┼───────┼───────┼──────────────┤ │ │
│ │ │ inv-12 │ codex    │ succeeded │ main  │ T-005 │ 14:28:00     │ │ │
│ │ │ inv-11 │ codex    │ failed    │ feat  │ T-004 │ 14:27:30     │ │ │
│ │ │ inv-10 │ codex    │ succeeded │ main  │ T-003 │ 14:27:00     │ │ │
│ │ └──────────────────────────────────────────────────────────────┘ │ │
│ │ ▶ inv-11 detail: attempts, error_kind, final_summary             │ │
│ └──────────────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────────────┤
│ Live Codex Smoke         │ Worker Reports                            │
│ ┌──────────────────────┐ │ ┌──────────────────────────────────────┐ │
│ │ Exists: ✓            │ │ │ Mode: leader-owned-consumer          │ │
│ │ Verdict: passed      │ │ │                                      │ │
│ │ Workers: 3           │ │ │ 📄 Procedure: worker-trajectory-...  │ │
│ │ Batch: T-001,T-002   │ │ │ 📄 Schema: subagent-report.schema   │ │
│ │ Overlap: proven (2)  │ │ │                                      │ │
│ │ ▶ overlap details    │ │ │ $ doc-based-coding scheduler         │ │
│ └──────────────────────┘ │ │   consume-worker-trajectory-report   │ │
│                          │ │                                      │ │
│                          │ │ ⚠ Monitoring does NOT consume reports│ │
│                          │ └──────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

### 7.2 Status Color Semantics

| Status | Text Label | Color Cue | Use |
|--------|-----------|-----------|-----|
| ok / passed / succeeded | "passed" / "succeeded" | green accent | healthy states |
| warning / pending | "warning" / "pending" | amber accent | needs attention |
| error / failed | "failed" / "error" | red accent | action required |
| unavailable | "unavailable" | grey accent | data missing |
| review_required | "review required" | blue accent | operator decision needed |
| running | "running" | cyan accent | in-progress |

All status indicators have **both** text and color. Color is never the sole signal.

### 7.3 Responsive Behavior

- **Wide (>900px)**: 2-column grid (scheduler | delivery), full-width runtime
- **Narrow (<900px)**: single column stack, all panels full-width
- **Very narrow (<500px)**: tables switch to card layout, badges wrap
- Tables use `overflow-x: auto` with a scroll hint, never clip silently

### 7.4 Typography and Density

- Font: `var(--vscode-font-family)`, `var(--vscode-font-size)`
- Panel headers: 12px uppercase, letter-spacing 0.5px, muted color
- Table cells: monospace for IDs/timestamps, normal for descriptions
- Padding: 8px panel internal, 4px table cell, 12px between panels
- Line-height: 1.4 for body text, 1.2 for table cells

---

## 8. Interaction Details

### 8.1 Refresh

- Button in toolbar, icon + text
- Calls `postMessage({ command: 'refresh' })`
- Shows spinner/loading state during CLI execution
- On error, shows error banner with retry suggestion

### 8.2 Auto-Refresh

- Toggle checkbox with interval display: "Auto-refresh: 5s"
- Interval is configurable in extension settings (default 5000ms)
- When enabled, host starts `setInterval` timer
- Each tick re-runs CLI and re-renders HTML
- Visual indicator shows countdown or pulsing dot when active
- Automatically pauses when panel is not visible (VS Code `onDidChangeViewState`)

### 8.3 Runtime Invocation Filter

- Three dropdown selects: provider, status, lane
- Filter state is local to the React component (not persisted)
- Filter resets on full re-render (payload refresh) — acceptable for v1
- "Clear filters" link when any filter is active

### 8.4 Expandable Rows

- Runtime invocation rows: click to expand → shows attempts, error details, authority_split
- Live Codex Smoke overlap pairs: click to expand → shows pair timing details
- Expansion state is local React state, resets on re-render

### 8.5 Copy to Clipboard

- Available for: artifact paths, consumer command, invocation IDs
- Uses `postMessage({ command: 'copyToClipboard', text: '...' })`
- Shows brief "Copied!" tooltip after copy

### 8.6 Document Links

- Worker report procedure doc and schema: opens in VS Code editor
- Uses `postMessage({ command: 'openDocument', path: 'docs/...' })`

---

## 9. CSS Theme Strategy

Use VS Code CSS variables for host integration, with operational-specific status colors:

```css
:root {
  /* Layout */
  --mon-panel-gap: 12px;
  --mon-cell-pad: 4px 8px;
  --mon-panel-pad: 8px;

  /* Status accents (always paired with text) */
  --mon-ok: var(--vscode-testing-iconPassed, #73c991);
  --mon-warn: var(--vscode-editorWarning-foreground, #cca700);
  --mon-error: var(--vscode-editorError-foreground, #f14c4c);
  --mon-info: var(--vscode-editorInfo-foreground, #3794ff);
  --mon-unavail: var(--vscode-disabledForeground, #888);
  --mon-review: var(--vscode-charts-blue, #3794ff);
  --mon-running: var(--vscode-charts-green, #89d185);

  /* Surfaces */
  --mon-surface: var(--vscode-editor-background);
  --mon-surface-raised: var(--vscode-sideBar-background);
  --mon-border: var(--vscode-panel-border, rgba(128,128,128,0.35));
  --mon-text: var(--vscode-editor-foreground);
  --mon-text-muted: var(--vscode-descriptionForeground);
  --mon-font: var(--vscode-font-family);
  --mon-font-mono: var(--vscode-editor-font-family, monospace);
}
```

CSS class prefix: `mon-` (e.g., `.mon-panel`, `.mon-status-strip`, `.mon-badge`).

---

## 10. Fixture Strategy for Validation

Since no static fixture JSON files exist, we need to create them for screenshot validation.

### Fixture Files

Create in: `vscode-extension/src/test/fixtures/monitoring/`

| File | Scenario | Description |
|------|----------|-------------|
| `healthy-c9-passed.json` | Happy path | All green: ok=true, C9 passed, overlap proven, no errors, several completed tasks |
| `missing-live-smoke.json` | Missing report | liveCodexSmoke.exists=false, verdict=unavailable, operatorSignal for missing smoke |
| `failed-delivery.json` | Delivery failure | 2 failed deliveries with failure_kind/failure_detail, pending count > 0 |
| `authority-integrity-warning.json` | Integrity issue | authoritySplit.readModelOnly=false (simulated), triggers integrity warning |

### Fixture Approach

Two options:

**Option A: Static JSON fixtures** (recommended for v1)
- Store `.json` files in the fixtures directory
- A test HTML builder reads fixture + renders the monitoring HTML
- Playwright captures screenshots of the generated HTML pages

**Option B: Programmatic fixture generation**
- Python test creates snapshot payloads via `MonitoringSnapshot` constructor
- Writes to temp files
- Less maintainable, couples frontend testing to backend internals

### Screenshot Validation Workflow

1. Build the React bundle: `npm run build`
2. For each fixture:
   a. Generate a standalone HTML page (inject fixture JSON as payload)
   b. Open in Playwright browser
   c. Capture full-page screenshot at 1200px width
   d. Capture narrow-viewport screenshot at 480px width
3. Verify in screenshots:
   - Text is readable (no overlap, no truncation)
   - Panel boundaries are clear
   - Status colors + text are both visible
   - Tables don't overflow
   - Scheduler/delivery/runtime/live-smoke panels are distinct

---

## 11. Command Registration (package.json)

```jsonc
{
  "contributes": {
    "commands": [
      {
        "command": "docBasedCoding.openMonitoringDashboard",
        "title": "Doc-Based Coding: Open Monitoring Dashboard"
      },
      {
        "command": "docBasedCoding.refreshMonitoringDashboard",
        "title": "Doc-Based Coding: Refresh Monitoring Dashboard"
      }
    ]
  }
}
```

Extension host registration in `extension.ts`:

```typescript
const monitoringPanel = new MonitoringPanel(context.extensionUri, outputChannel);
context.subscriptions.push(monitoringPanel);

context.subscriptions.push(
  vscode.commands.registerCommand('docBasedCoding.openMonitoringDashboard', async () => {
    const workspace = vscode.workspace.workspaceFolders?.[0];
    if (workspace) await monitoringPanel.open(workspace);
  }),
);
```

---

## 12. esbuild Configuration Update

Add `monitoringDashboard` entry to the webviews build group in `esbuild.config.mjs`:

```javascript
entryPoints: {
  progressGraphV2Engine: 'src/webviews/progressGraphV2Engine.ts',
  localWorkTrajectory: 'src/webviews/localWorkTrajectory.tsx',
  monitoringDashboard: 'src/webviews/monitoringDashboard.tsx',  // NEW
  knowledgeGraphForceWorker: 'node_modules/@note-web/knowledge-graph-engine/src/layout/force-worker.js',
}
```

---

## 13. Non-Goals (Reiterated)

This first visual slice does NOT implement:

1. Mutation buttons (no "run supervisor", "consume report", "retry delivery")
2. Local Work Trajectory mutation
3. Worker report consumption
4. Raw transcript viewing
5. WebSocket/streaming behavior
6. Distributed worker lease controls

---

## 14. Implementation Phases

### Phase 1: Shell + Data Pipeline
- `monitoringPanel.ts` — WebviewPanel manager
- CLI invocation helper
- HTML builder with payload injection
- Command registration
- **Validate**: CLI runs, JSON appears in webview `<script>` tag

### Phase 2: React Component — Static Panels
- `monitoringDashboard.tsx` — MonitoringApp + StatusStrip + all 6 panels (no interaction)
- `monitoringDashboard.css` — Full theme
- **Validate**: Static render of fixture data in browser

### Phase 3: Interactions
- Refresh button + auto-refresh toggle
- Runtime invocation filter + expandable rows
- Copy to clipboard
- Document link opening
- **Validate**: Interactive dashboard with live CLI calls

### Phase 4: Fixtures + Screenshot Validation
- Create fixture JSON files
- Standalone HTML generator for each fixture
- Playwright screenshots at 1200px and 480px
- **Validate**: Screenshots confirm readability, layout, status clarity

---

## 15. Open Questions

1. **File path resolution**: The CLI needs `--snapshot-path` etc. Should these be
   hardcoded (like `.codex/scheduler/state.json`) or read from extension settings?
   → Recommend: start with conventional paths, add configuration later.

2. **Auto-refresh during re-render**: Full HTML replacement causes a visual flash.
   Acceptable for v1, or should we implement incremental DOM update?
   → Recommend: full re-render is acceptable for v1 (same pattern as ProgressGraphPreview).

3. **Filter persistence across refreshes**: Filters reset when payload refreshes.
   → Recommend: acceptable for v1; document as known limitation.

4. **Panel placement**: Open in ViewColumn.Two (split) or ViewColumn.Active?
   → Recommend: ViewColumn.Two so operator can see code + dashboard side by side.
