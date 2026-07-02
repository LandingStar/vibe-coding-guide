import React, { useState, useCallback, useMemo } from 'react';
import { createRoot } from 'react-dom/client';
import './monitoringDashboard.css';

// ── Types ──────────────────────────────────────────────────────────

interface MonitoringSnapshot {
    schema_version: string;
    ok: boolean;
    next_action: string;
    paths: Record<string, string>;
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

interface SchedulerSection {
    task_state_counts: Record<string, number>;
    target_task_states: Record<string, string>;
    waiting_task_ids: string[];
    review_required_task_ids: string[];
    completed_task_output_refs: { task_id: string; ref_kind: string; ref_id: string; version: string }[];
}

interface DeliverySection {
    state_counts: Record<string, number>;
    actionable_pending_codex_delivery_count: number;
    latest_records: DeliveryRecord[];
}

interface DeliveryRecord {
    delivery_id: string;
    source_key: string;
    agent_id: string;
    role: string;
    lane_id: string;
    task_id: string;
    delivery_state: string;
    reason: string;
    failure_kind: string;
    failure_detail: string;
    runtime_provider: string;
    delivery_attempt_count: number;
    created_at: string;
    updated_at: string;
    delivered_at: string;
    failed_at: string;
    review_required_at: string;
}

interface RuntimeInvocationsSection {
    counts: Record<string, number>;
    latest_records: RuntimeInvocationRecord[];
    concurrency: ConcurrencySummary;
}

interface RuntimeInvocationRecord {
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
    summary: string;
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

interface ArtifactsSection {
    output_artifact_refs: { ref_kind: string; ref_id: string; version: string }[];
    review_artifact_refs: { ref_kind: string; ref_id: string; version: string; product_type?: string }[];
    worker_patch_artifact_refs: { ref_kind: string; ref_id: string; version: string; product_type?: string }[];
}

// ── VS Code API ────────────────────────────────────────────────────

declare function acquireVsCodeApi(): {
    postMessage(msg: any): void;
    getState(): any;
    setState(state: any): void;
};

let vscodeApi: ReturnType<typeof acquireVsCodeApi> | undefined;
function getVsCodeApi() {
    if (!vscodeApi) {
        try { vscodeApi = acquireVsCodeApi(); } catch { /* test env */ }
    }
    return vscodeApi;
}

function postToHost(msg: any) {
    getVsCodeApi()?.postMessage(msg);
}

// ── Helpers ────────────────────────────────────────────────────────

function severityClass(sev: string): string {
    switch (sev) {
        case 'error': return 'mon-sev-error';
        case 'warning': return 'mon-sev-warn';
        case 'info': return 'mon-sev-info';
        case 'ok': return 'mon-sev-ok';
        default: return '';
    }
}

function stateClass(state: string): string {
    switch (state) {
        case 'succeeded': case 'passed': case 'complete': case 'acknowledged': case 'delivered':
            return 'mon-state-ok';
        case 'failed': case 'error':
            return 'mon-state-error';
        case 'pending': case 'waiting': case 'proposed':
            return 'mon-state-warn';
        case 'review_required':
            return 'mon-state-review';
        case 'unavailable':
            return 'mon-state-unavail';
        default:
            return '';
    }
}

function formatTime(iso: string): string {
    if (!iso) return '—';
    try {
        const d = new Date(iso);
        return d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch { return iso; }
}

function formatDuration(start: string, end: string): string {
    if (!start || !end) return '—';
    try {
        const ms = new Date(end).getTime() - new Date(start).getTime();
        if (ms < 1000) return `${ms}ms`;
        if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
        return `${(ms / 60000).toFixed(1)}m`;
    } catch { return '—'; }
}

// ── Shared Components ──────────────────────────────────────────────

function Badge({ label, className }: { label: string; className?: string }) {
    return <span className={`mon-badge ${className ?? ''}`}>{label}</span>;
}

function CountBadge({ label, count, className }: { label: string; count: number; className?: string }) {
    return (
        <span className={`mon-count-badge ${className ?? ''}`}>
            <span className="mon-count-badge-label">{label}</span>
            <span className="mon-count-badge-value">{count}</span>
        </span>
    );
}

function CopyButton({ text, label }: { text: string; label?: string }) {
    const [copied, setCopied] = useState(false);
    const handleCopy = useCallback(() => {
        postToHost({ command: 'copyToClipboard', text });
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
    }, [text]);
    return (
        <button className="mon-copy-btn" onClick={handleCopy} title={`Copy: ${text}`}>
            {copied ? 'Copied' : (label ?? 'Copy')}
        </button>
    );
}

function DocLink({ path, label }: { path: string; label: string }) {
    return (
        <button className="mon-doc-link" onClick={() => postToHost({ command: 'openDocument', path })}>
            {label}
        </button>
    );
}

function SectionHeader({ title, children }: { title: string; children?: React.ReactNode }) {
    return (
        <div className="mon-section-header">
            <h3 className="mon-section-title">{title}</h3>
            {children}
        </div>
    );
}

function EmptyState({ text }: { text: string }) {
    return <div className="mon-empty">{text}</div>;
}

// ── Toolbar ────────────────────────────────────────────────────────

function Toolbar({ snapshot, autoRefresh, onAutoRefreshToggle }: {
    snapshot: MonitoringSnapshot;
    autoRefresh: boolean;
    onAutoRefreshToggle: (enabled: boolean) => void;
}) {
    const [refreshing, setRefreshing] = useState(false);

    const handleRefresh = useCallback(() => {
        setRefreshing(true);
        postToHost({ command: 'refresh' });
        setTimeout(() => setRefreshing(false), 2000);
    }, []);

    return (
        <div className="mon-toolbar">
            <button className="mon-toolbar-btn" onClick={handleRefresh} disabled={refreshing}>
                <span className={refreshing ? 'mon-spinner' : 'mon-refresh-icon'}>↻</span>
                {refreshing ? 'Refreshing…' : 'Refresh'}
            </button>
            <label className="mon-auto-refresh">
                <input
                    type="checkbox"
                    checked={autoRefresh}
                    onChange={(e) => onAutoRefreshToggle(e.target.checked)}
                />
                Auto-refresh 5s
            </label>
            <Badge label={snapshot.schema_version} className="mon-schema-badge" />
            <span className="mon-toolbar-spacer" />
            <span className="mon-toolbar-time">
                Updated: {new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
            </span>
        </div>
    );
}

// ── Status Strip ───────────────────────────────────────────────────

function StatusStrip({ snapshot }: { snapshot: MonitoringSnapshot }) {
    const integrityIssue = !snapshot.authoritySplit.readModelOnly
        || snapshot.authoritySplit.localWorkTrajectoryMutated;
    const topSignals = snapshot.operatorSignals
        .filter((s) => s.severity !== 'ok')
        .slice(0, 3);

    return (
        <div className="mon-status-strip">
            <div className={`mon-ok-indicator ${snapshot.ok ? 'mon-sev-ok' : 'mon-sev-error'}`}>
                {snapshot.ok ? 'OK' : 'NOT OK'}
            </div>
            <div className="mon-next-action">
                <span className="mon-next-action-label">Next:</span>
                <span className="mon-next-action-text">{snapshot.next_action || '—'}</span>
            </div>
            {integrityIssue && (
                <Badge label="INTEGRITY WARNING" className="mon-sev-error" />
            )}
            {topSignals.length > 0 && (
                <div className="mon-top-signals">
                    {topSignals.map((s, i) => (
                        <Badge key={i} label={s.message} className={severityClass(s.severity)} />
                    ))}
                </div>
            )}
        </div>
    );
}

// ── Scheduler Panel ────────────────────────────────────────────────

function SchedulerPanel({ scheduler }: { scheduler: SchedulerSection }) {
    const entries = Object.entries(scheduler.task_state_counts);
    const targets = Object.entries(scheduler.target_task_states);

    return (
        <div className="mon-panel">
            <SectionHeader title="Scheduler" />
            <div className="mon-badge-row">
                {entries.map(([state, count]) => (
                    <CountBadge key={state} label={state} count={count} className={stateClass(state)} />
                ))}
                {entries.length === 0 && <EmptyState text="No task state data" />}
            </div>
            {scheduler.waiting_task_ids.length > 0 && (
                <div className="mon-subsection">
                    <span className="mon-subsection-label">Waiting:</span>
                    {scheduler.waiting_task_ids.map((id) => (
                        <Badge key={id} label={id} className="mon-state-warn" />
                    ))}
                </div>
            )}
            {scheduler.review_required_task_ids.length > 0 && (
                <div className="mon-subsection">
                    <span className="mon-subsection-label">Review required:</span>
                    {scheduler.review_required_task_ids.map((id) => (
                        <Badge key={id} label={id} className="mon-state-review" />
                    ))}
                </div>
            )}
            {targets.length > 0 && (
                <details className="mon-details">
                    <summary>Target task states ({targets.length})</summary>
                    <table className="mon-table mon-table-compact">
                        <thead><tr><th>Task</th><th>State</th></tr></thead>
                        <tbody>
                            {targets.map(([taskId, state]) => (
                                <tr key={taskId}>
                                    <td className="mon-mono">{taskId}</td>
                                    <td><Badge label={state} className={stateClass(state)} /></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </details>
            )}
        </div>
    );
}

// ── Delivery Panel ─────────────────────────────────────────────────

function DeliveryPanel({ delivery }: { delivery: DeliverySection }) {
    const entries = Object.entries(delivery.state_counts);
    const failedRecords = delivery.latest_records.filter((r) => r.delivery_state === 'failed');
    const reviewRecords = delivery.latest_records.filter((r) => r.delivery_state === 'review_required');

    return (
        <div className="mon-panel">
            <SectionHeader title="Delivery" />
            <div className="mon-badge-row">
                {entries.map(([state, count]) => (
                    <CountBadge key={state} label={state} count={count} className={stateClass(state)} />
                ))}
                {entries.length === 0 && <EmptyState text="No delivery data" />}
            </div>
            {delivery.actionable_pending_codex_delivery_count > 0 && (
                <div className="mon-subsection">
                    <Badge
                        label={`Pending Codex: ${delivery.actionable_pending_codex_delivery_count}`}
                        className="mon-state-warn"
                    />
                </div>
            )}
            {failedRecords.length > 0 && (
                <details className="mon-details" open>
                    <summary>Failed deliveries ({failedRecords.length})</summary>
                    <table className="mon-table">
                        <thead>
                            <tr>
                                <th>ID</th><th>Task</th><th>Agent</th><th>Lane</th>
                                <th>Failure</th><th>Detail</th><th>Time</th>
                            </tr>
                        </thead>
                        <tbody>
                            {failedRecords.map((r) => (
                                <tr key={r.delivery_id}>
                                    <td className="mon-mono">{r.delivery_id}</td>
                                    <td className="mon-mono">{r.task_id}</td>
                                    <td>{r.agent_id}</td>
                                    <td>{r.lane_id}</td>
                                    <td className="mon-state-error">{r.failure_kind || '—'}</td>
                                    <td className="mon-cell-wrap">{r.failure_detail || '—'}</td>
                                    <td>{formatTime(r.failed_at || r.updated_at)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </details>
            )}
            {reviewRecords.length > 0 && (
                <details className="mon-details">
                    <summary>Review required ({reviewRecords.length})</summary>
                    <table className="mon-table">
                        <thead>
                            <tr><th>ID</th><th>Task</th><th>Agent</th><th>Reason</th><th>Time</th></tr>
                        </thead>
                        <tbody>
                            {reviewRecords.map((r) => (
                                <tr key={r.delivery_id}>
                                    <td className="mon-mono">{r.delivery_id}</td>
                                    <td className="mon-mono">{r.task_id}</td>
                                    <td>{r.agent_id}</td>
                                    <td className="mon-cell-wrap">{r.reason || '—'}</td>
                                    <td>{formatTime(r.review_required_at || r.updated_at)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </details>
            )}
        </div>
    );
}

// ── Runtime Panel ──────────────────────────────────────────────────

function RuntimePanel({ runtime }: { runtime: RuntimeInvocationsSection }) {
    const [providerFilter, setProviderFilter] = useState('');
    const [statusFilter, setStatusFilter] = useState('');
    const [laneFilter, setLaneFilter] = useState('');
    const [expandedId, setExpandedId] = useState<string | null>(null);

    const providers = useMemo(() => {
        const set = new Set(runtime.latest_records.map((r) => r.provider));
        return Array.from(set).sort();
    }, [runtime.latest_records]);

    const lanes = useMemo(() => {
        const set = new Set(
            runtime.concurrency.latestRecords.map((r) => r.laneId).filter(Boolean),
        );
        return Array.from(set).sort();
    }, [runtime.concurrency.latestRecords]);

    const filteredRecords = useMemo(() => {
        return runtime.latest_records.filter((r) => {
            if (providerFilter && r.provider !== providerFilter) return false;
            if (statusFilter && r.status !== statusFilter) return false;
            if (laneFilter) {
                const cr = runtime.concurrency.latestRecords.find((c) => c.invocationId === r.invocation_id);
                if (!cr || cr.laneId !== laneFilter) return false;
            }
            return true;
        });
    }, [runtime.latest_records, runtime.concurrency.latestRecords, providerFilter, statusFilter, laneFilter]);

    const hasFilters = providerFilter || statusFilter || laneFilter;
    const clearFilters = useCallback(() => {
        setProviderFilter('');
        setStatusFilter('');
        setLaneFilter('');
    }, []);

    const countEntries = Object.entries(runtime.counts);

    return (
        <div className="mon-panel mon-panel-full">
            <SectionHeader title="Runtime Invocations" />
            <div className="mon-badge-row">
                {countEntries.map(([key, count]) => (
                    <CountBadge key={key} label={key} count={count} className={stateClass(key)} />
                ))}
                {countEntries.length === 0 && <EmptyState text="No runtime invocation data" />}
            </div>
            {runtime.concurrency.liveOverlapProven && (
                <Badge label={`Overlap proven (${runtime.concurrency.overlapPairCount} pairs)`} className="mon-sev-ok" />
            )}
            <div className="mon-filter-bar">
                <label>
                    Provider
                    <select value={providerFilter} onChange={(e) => setProviderFilter(e.target.value)}>
                        <option value="">All</option>
                        {providers.map((p) => <option key={p} value={p}>{p}</option>)}
                    </select>
                </label>
                <label>
                    Status
                    <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
                        <option value="">All</option>
                        <option value="succeeded">succeeded</option>
                        <option value="failed">failed</option>
                    </select>
                </label>
                <label>
                    Lane
                    <select value={laneFilter} onChange={(e) => setLaneFilter(e.target.value)}>
                        <option value="">All</option>
                        {lanes.map((l) => <option key={l} value={l}>{l}</option>)}
                    </select>
                </label>
                {hasFilters && (
                    <button className="mon-filter-clear" onClick={clearFilters}>Clear filters</button>
                )}
                {hasFilters && (
                    <span className="mon-filter-count">{filteredRecords.length} of {runtime.latest_records.length}</span>
                )}
            </div>
            <div className="mon-table-wrap">
                <table className="mon-table">
                    <thead>
                        <tr>
                            <th></th>
                            <th>ID</th>
                            <th>Provider</th>
                            <th>Status</th>
                            <th>Task</th>
                            <th>Agent</th>
                            <th>Attempts</th>
                            <th>Started</th>
                            <th>Duration</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredRecords.map((r) => (
                            <React.Fragment key={r.invocation_id}>
                                <tr
                                    className="mon-expandable-row"
                                    onClick={() => setExpandedId(expandedId === r.invocation_id ? null : r.invocation_id)}
                                >
                                    <td className="mon-expand-icon">
                                        {expandedId === r.invocation_id ? '▼' : '▶'}
                                    </td>
                                    <td className="mon-mono">{r.invocation_id}</td>
                                    <td>{r.provider}</td>
                                    <td><Badge label={r.status} className={stateClass(r.status)} /></td>
                                    <td className="mon-mono">{r.task_id}</td>
                                    <td>{r.agent_id}</td>
                                    <td>{r.attempt_count}</td>
                                    <td>{formatTime(r.started_at)}</td>
                                    <td>{formatDuration(r.started_at, r.ended_at)}</td>
                                </tr>
                                {expandedId === r.invocation_id && (
                                    <tr className="mon-detail-row">
                                        <td colSpan={9}>
                                            <InvocationDetail record={r} />
                                        </td>
                                    </tr>
                                )}
                            </React.Fragment>
                        ))}
                        {filteredRecords.length === 0 && (
                            <tr><td colSpan={9} className="mon-empty">
                                {hasFilters ? 'No records match current filters' : 'No runtime invocation records'}
                            </td></tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

function InvocationDetail({ record }: { record: RuntimeInvocationRecord }) {
    return (
        <div className="mon-invocation-detail">
            <div className="mon-detail-grid">
                <div>
                    <span className="mon-detail-label">Session:</span>
                    <span className="mon-mono">{record.session_id || '—'}</span>
                </div>
                <div>
                    <span className="mon-detail-label">Run:</span>
                    <span className="mon-mono">{record.run_id || '—'}</span>
                </div>
                <div>
                    <span className="mon-detail-label">Surface:</span>
                    <span>{record.runtime_surface || '—'}</span>
                </div>
                <div>
                    <span className="mon-detail-label">Retry policy:</span>
                    <span>max {record.retry_policy?.max_attempts ?? '—'}, backoff {record.retry_policy?.backoff_seconds ?? '—'}s</span>
                </div>
            </div>
            {record.final_summary && (
                <div className="mon-detail-summary">
                    <span className="mon-detail-label">Summary:</span>
                    <span>{record.final_summary}</span>
                </div>
            )}
            {record.final_error_kind && (
                <div className="mon-detail-error">
                    <span className="mon-detail-label">Error:</span>
                    <span className="mon-state-error">{record.final_error_kind}</span>
                </div>
            )}
            {record.attempts.length > 0 && (
                <div className="mon-attempts">
                    <span className="mon-detail-label">Attempts:</span>
                    <table className="mon-table mon-table-compact">
                        <thead>
                            <tr>
                                <th>#</th><th>Status</th><th>Retryable</th>
                                <th>Error</th><th>Duration</th><th>Summary</th>
                            </tr>
                        </thead>
                        <tbody>
                            {record.attempts.map((a) => (
                                <tr key={a.attempt_index}>
                                    <td>{a.attempt_index}</td>
                                    <td><Badge label={a.status} className={stateClass(a.status)} /></td>
                                    <td>{a.retryable ? 'yes' : 'no'}</td>
                                    <td>{a.error_kind || '—'}</td>
                                    <td>{formatDuration(a.started_at, a.ended_at)}</td>
                                    <td className="mon-cell-wrap">{a.summary || '—'}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
            <div className="mon-detail-auth">
                <span className="mon-detail-label">Authority:</span>
                <span>
                    {record.authority_split?.raw_transcript_persisted ? 'raw transcript persisted' : 'no raw transcript'}
                    {record.authority_split?.local_work_trajectory_mutated ? ', trajectory mutated' : ''}
                    {record.authority_split?.scheduler_state_mutated ? ', scheduler mutated' : ''}
                </span>
            </div>
        </div>
    );
}

// ── Live Codex Smoke Panel ─────────────────────────────────────────

function LiveCodexSmokePanel({ smoke }: { smoke: LiveCodexSmokeSection }) {
    const [showOverlapDetail, setShowOverlapDetail] = useState(false);

    if (!smoke.exists) {
        return (
            <div className="mon-panel">
                <SectionHeader title="Live Codex Smoke" />
                <div className="mon-badge-row">
                    <Badge label="unavailable" className="mon-state-unavail" />
                </div>
                <div className="mon-empty">{smoke.diagnostic || 'No smoke report found'}</div>
                {smoke.path && <CopyButton text={smoke.path} label="Copy report path" />}
            </div>
        );
    }

    const countEntries = Object.entries(smoke.counts || {});

    return (
        <div className="mon-panel">
            <SectionHeader title="Live Codex Smoke" />
            <div className="mon-badge-row">
                <Badge label={smoke.verdict} className={stateClass(smoke.verdict)} />
                <Badge label={smoke.ok ? 'ok' : 'not ok'} className={smoke.ok ? 'mon-sev-ok' : 'mon-sev-error'} />
            </div>
            {smoke.diagnostic && (
                <div className="mon-diagnostic">{smoke.diagnostic}</div>
            )}
            {countEntries.length > 0 && (
                <div className="mon-badge-row">
                    {countEntries.map(([key, value]) => (
                        <CountBadge key={key} label={key} count={typeof value === 'number' ? value : 0} />
                    ))}
                </div>
            )}
            {smoke.firstConcurrentBatch?.taskIds?.length > 0 && (
                <div className="mon-subsection">
                    <span className="mon-subsection-label">First concurrent batch:</span>
                    <div className="mon-mono-list">
                        {smoke.firstConcurrentBatch.taskIds.map((id) => (
                            <span key={id} className="mon-mono">{id}</span>
                        ))}
                    </div>
                </div>
            )}
            <div className="mon-subsection">
                <Badge
                    label={smoke.overlap?.proven ? `Overlap proven (${smoke.overlap.pairs?.length ?? 0} pairs)` : 'Overlap not proven'}
                    className={smoke.overlap?.proven ? 'mon-sev-ok' : 'mon-state-unavail'}
                />
            </div>
            {smoke.overlap?.proven && smoke.overlap.pairs?.length > 0 && (
                <details className="mon-details">
                    <summary>Overlap pairs ({smoke.overlap.pairs.length})</summary>
                    <div className="mon-overlap-pairs">
                        {smoke.overlap.pairs.map((pair: any, i: number) => (
                            <div key={i} className="mon-overlap-pair">
                                <pre className="mon-pre">{JSON.stringify(pair, null, 2)}</pre>
                            </div>
                        ))}
                    </div>
                </details>
            )}
            {smoke.errors && smoke.errors.length > 0 && (
                <div className="mon-errors">
                    {smoke.errors.map((e, i) => (
                        <div key={i} className="mon-error-text">{e}</div>
                    ))}
                </div>
            )}
            <CopyButton text={smoke.path} label="Copy report path" />
        </div>
    );
}

// ── Worker Reports Panel ───────────────────────────────────────────

function WorkerReportsPanel({ reports }: { reports: WorkerReportsSection }) {
    return (
        <div className="mon-panel">
            <SectionHeader title="Worker Reports" />
            <div className="mon-worker-info">
                <div className="mon-worker-row">
                    <span className="mon-detail-label">Mode:</span>
                    <Badge label={reports.mode || 'unknown'} />
                </div>
                <div className="mon-worker-row">
                    <span className="mon-detail-label">Direct trajectory mutation:</span>
                    <Badge
                        label={reports.directWorkerTrajectoryMutationAllowed ? 'allowed' : 'not allowed'}
                        className={reports.directWorkerTrajectoryMutationAllowed ? 'mon-sev-warn' : 'mon-sev-ok'}
                    />
                </div>
                {reports.procedureDoc && (
                    <div className="mon-worker-row">
                        <DocLink path={reports.procedureDoc} label="Procedure doc" />
                    </div>
                )}
                {reports.schema && (
                    <div className="mon-worker-row">
                        <DocLink path={reports.schema} label="Report schema" />
                    </div>
                )}
                {reports.consumerCommand && (
                    <div className="mon-worker-row mon-worker-cmd">
                        <code className="mon-mono">{reports.consumerCommand}</code>
                        <CopyButton text={reports.consumerCommand} />
                    </div>
                )}
                {reports.notes?.length > 0 && (
                    <ul className="mon-worker-notes">
                        {reports.notes.map((n, i) => <li key={i}>{n}</li>)}
                    </ul>
                )}
            </div>
            <div className="mon-boundary-note">
                Monitoring does NOT consume worker reports. Report consumption
                is a separate leader-owned operation.
            </div>
        </div>
    );
}

// ── Error Drawer ───────────────────────────────────────────────────

function ErrorDrawer({ errors }: { errors: string[] }) {
    if (errors.length === 0) return null;
    return (
        <details className="mon-error-drawer" open>
            <summary className="mon-error-summary">
                Errors ({errors.length})
            </summary>
            <ul className="mon-error-list">
                {errors.map((e, i) => (
                    <li key={i} className="mon-error-item">{e}</li>
                ))}
            </ul>
        </details>
    );
}

// ── App ────────────────────────────────────────────────────────────

function MonitoringApp({ snapshot: initialSnapshot }: { snapshot: MonitoringSnapshot }) {
    const [snapshot] = useState(initialSnapshot);
    const [autoRefresh, setAutoRefresh] = useState(false);

    const handleAutoRefreshToggle = useCallback((enabled: boolean) => {
        setAutoRefresh(enabled);
        postToHost({ command: 'autoRefresh', enabled });
    }, []);

    return (
        <div className="mon-shell">
            <Toolbar
                snapshot={snapshot}
                autoRefresh={autoRefresh}
                onAutoRefreshToggle={handleAutoRefreshToggle}
            />
            <StatusStrip snapshot={snapshot} />
            <div className="mon-grid">
                <SchedulerPanel scheduler={snapshot.scheduler} />
                <DeliveryPanel delivery={snapshot.delivery} />
            </div>
            <RuntimePanel runtime={snapshot.runtimeInvocations} />
            <div className="mon-grid">
                <LiveCodexSmokePanel smoke={snapshot.liveCodexSmoke} />
                <WorkerReportsPanel reports={snapshot.workerReports} />
            </div>
            <ErrorDrawer errors={snapshot.errors} />
        </div>
    );
}

// ── Mount ──────────────────────────────────────────────────────────

function readPayload(): MonitoringSnapshot | null {
    const el = document.getElementById('monitoringPayload');
    if (!el || !el.textContent) return null;
    try {
        return JSON.parse(el.textContent) as MonitoringSnapshot;
    } catch {
        return null;
    }
}

function main() {
    const root = document.getElementById('monitoring-root');
    if (!root) return;
    const payload = readPayload();
    if (!payload) {
        root.textContent = 'Failed to load monitoring snapshot payload.';
        return;
    }
    createRoot(root).render(<MonitoringApp snapshot={payload} />);
}

main();
