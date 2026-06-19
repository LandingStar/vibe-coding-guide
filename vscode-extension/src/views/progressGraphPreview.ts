import * as vscode from 'vscode';
import { existsSync, readFileSync, statSync } from 'fs';
import {
  buildProgressGraphPreviewHtml,
  coerceControlSnapshot,
  coerceHostEvidencePresentation,
  coerceLocalWorkTrajectory,
  type ProgressGraphPreviewArtifactState,
  type ProgressGraphPreviewControlSnapshot,
  type ProgressGraphPreviewFreshness,
  type ProgressGraphPreviewHostEvidencePresentation,
  type ProgressGraphPreviewLocalWorkTrajectory,
  type ProgressGraphPreviewState,
  type ProgressGraphPreviewV2PoCPayload,
} from './progressGraphPreviewHtml';
import {
  HOST_EVIDENCE_PRESENTATION_RESOURCE_URI,
  readHostEvidencePresentation,
} from './hostEvidencePresentation';
import {
  EXCHANGE_ARTIFACTS_BUNDLE_RESOURCE_URI,
  buildIdleSchedulerOperatorLastAction,
  buildSchedulerOperatorPaths,
  readSchedulerOperatorWorkflowState,
  runSchedulerOperatorAction,
  type SchedulerOperatorLastAction,
  type SchedulerOperatorWorkflowState,
} from './schedulerOperatorWorkflow';
import {
  coerceSchedulerOperatorActionMessage,
  type SchedulerOperatorAction,
} from './schedulerOperatorContracts';
type ProgressGraphPreviewMessage = {
    command:
      | 'refresh'
      | 'revealArtifact'
      | 'schedulerOperatorAction';
    action?: string;
    artifactId?: string;
    version?: string;
};

type ProgressGraphPreviewRefreshLifecycle = {
  status: 'idle' | 'refreshing' | 'failed';
  startedAt: string | null;
  completedAt: string | null;
  errorMessage: string | null;
};

type ProgressGraphArtifactRegenerator = (workspaceFolder: vscode.WorkspaceFolder) => Promise<void>;
type ProgressGraphRuntimeResolver = (workspaceFolder: vscode.WorkspaceFolder) => Promise<{
  workspaceRoot: string;
  pythonPath: string;
  sourceRoot: string | null;
}>;

const DEFAULT_PROGRESS_GRAPH_VIEW_COLUMN = vscode.ViewColumn.One;

export class ProgressGraphPreviewPanel implements vscode.Disposable {
    private _panel: vscode.WebviewPanel | undefined;
    private _workspaceFolder: vscode.WorkspaceFolder | undefined;
  private readonly _extensionUri: vscode.Uri;
    private readonly _extensionDistUri: vscode.Uri;
    private readonly _outputChannel: vscode.OutputChannel;
    private readonly _regenerateArtifacts: ProgressGraphArtifactRegenerator;
    private readonly _resolveRuntime: ProgressGraphRuntimeResolver;
    private readonly _disposables: vscode.Disposable[] = [];
    private _lastLoadedAt: string | null = null;
    private _lastLoadedArtifactModifiedTimeMs: number | null = null;
    private _lastRenderedPreviewHtml: string | null = null;
    private _lastRenderedShellSignature: string | null = null;
    private _lastSchedulerOperatorAction: SchedulerOperatorLastAction = buildIdleSchedulerOperatorLastAction();
    private _refreshLifecycle: ProgressGraphPreviewRefreshLifecycle = {
        status: 'idle',
        startedAt: null,
        completedAt: null,
        errorMessage: null,
    };

    constructor(
      extensionUri: vscode.Uri,
      outputChannel: vscode.OutputChannel,
      regenerateArtifacts: ProgressGraphArtifactRegenerator,
      resolveRuntime: ProgressGraphRuntimeResolver,
    ) {
      this._extensionUri = extensionUri;
      this._extensionDistUri = vscode.Uri.joinPath(extensionUri, 'dist');
        this._outputChannel = outputChannel;
        this._regenerateArtifacts = regenerateArtifacts;
        this._resolveRuntime = resolveRuntime;
    }

    async open(workspaceFolder: vscode.WorkspaceFolder): Promise<void> {
        this._workspaceFolder = workspaceFolder;
        this._ensurePanel();
        await this._reload();
    }

    async refresh(workspaceFolder?: vscode.WorkspaceFolder): Promise<void> {
        if (workspaceFolder) {
            this._workspaceFolder = workspaceFolder;
        }

        if (!this._workspaceFolder) {
            return;
        }

        this._ensurePanel();
        const refreshStartedAt = new Date().toISOString();
        this._refreshLifecycle = {
            status: 'refreshing',
            startedAt: refreshStartedAt,
            completedAt: null,
            errorMessage: null,
        };

        try {
            await vscode.window.withProgress(
                {
                    location: vscode.ProgressLocation.Notification,
                    title: 'Refreshing progress graph preview',
                },
                async () => {
                    await this._regenerateArtifacts(this._workspaceFolder!);
                },
            );
            this._refreshLifecycle = {
                status: 'idle',
                startedAt: refreshStartedAt,
                completedAt: new Date().toISOString(),
                errorMessage: null,
            };
            await this._reload();
            vscode.window.showInformationMessage('Progress graph artifacts regenerated and preview refreshed.');
        } catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            this._refreshLifecycle = {
                status: 'failed',
                startedAt: refreshStartedAt,
                completedAt: new Date().toISOString(),
                errorMessage: message,
            };
            this._renderShellState({ preserveCurrentPreview: true });
            this._outputChannel.appendLine(`[ProgressGraphPreview] Failed to refresh preview artifacts: ${message}`);
            vscode.window.showErrorMessage(`Failed to refresh progress graph preview: ${message}`);
        }
    }

    async revealArtifact(workspaceFolder?: vscode.WorkspaceFolder): Promise<void> {
        if (workspaceFolder) {
            this._workspaceFolder = workspaceFolder;
        }

        if (!this._workspaceFolder) {
            return;
        }

        const artifactUri = this._previewUri(this._workspaceFolder);
        await vscode.commands.executeCommand('revealInExplorer', artifactUri);
    }

    async reloadFromDiskIfOpen(workspaceFolder?: vscode.WorkspaceFolder): Promise<void> {
      if (workspaceFolder) {
        this._workspaceFolder = workspaceFolder;
      }
      if (!this._panel || !this._workspaceFolder) {
        return;
      }
      await this._reload();
    }

  dispose(): void {
    this._panel?.dispose();
    for (const disposable of this._disposables) {
      disposable.dispose();
    }
  }

  private async _reload(): Promise<void> {
    if (!this._panel || !this._workspaceFolder) {
      return;
    }

    const artifactState = await this._readArtifactState(this._workspaceFolder);
    this._lastRenderedPreviewHtml = artifactState.previewHtml;
    this._lastLoadedAt = new Date().toISOString();
    this._lastLoadedArtifactModifiedTimeMs = artifactState.artifactModifiedTimeMs;
    const state = this._buildState(artifactState, artifactState.previewHtml);
    this._panel.title = this._buildPanelTitle(state);
    this._panel.webview.html = this._buildHtml(state);
    this._lastRenderedShellSignature = this._shellSignature(state);

    if (state.previewExists) {
            this._outputChannel.appendLine(`[ProgressGraphPreview] Refreshed preview artifact: ${state.artifactPath}`);
        } else {
            this._outputChannel.appendLine(`[ProgressGraphPreview] Missing preview artifact: ${state.artifactPath}`);
        }
    }

  private _ensurePanel(): void {
    if (this._panel) {
      this._panel.reveal(DEFAULT_PROGRESS_GRAPH_VIEW_COLUMN);
      return;
        }

    this._panel = vscode.window.createWebviewPanel(
      'docBasedCoding.progressGraphPreview',
      'Progress Graph',
      DEFAULT_PROGRESS_GRAPH_VIEW_COLUMN,
      {
        enableScripts: true,
        enableFindWidget: true,
        retainContextWhenHidden: true,
        localResourceRoots: this._workspaceFolder
          ? [this._workspaceFolder.uri, this._extensionDistUri]
          : [this._extensionDistUri],
      },
    );

    this._panel.onDidDispose(() => {
      this._panel = undefined;
    }, null, this._disposables);

    this._panel.onDidChangeViewState((event) => {
      if (!event.webviewPanel.visible || !this._workspaceFolder) {
        return;
      }
      this._renderShellState({ preserveCurrentPreview: true });
    }, null, this._disposables);

    this._panel.webview.onDidReceiveMessage(
      async (message: ProgressGraphPreviewMessage) => {
        switch (message.command) {
          case 'refresh':
            await this.refresh();
            break;
          case 'revealArtifact':
            await this.revealArtifact();
            break;
          case 'schedulerOperatorAction':
            await this._runSchedulerOperatorAction(message);
            break;
        }
      },
      null,
      this._disposables,
    );
    }

  private async _runSchedulerOperatorAction(message: ProgressGraphPreviewMessage): Promise<void> {
    if (!this._workspaceFolder) {
      return;
    }
    const action = this._coerceSchedulerOperatorAction(message);
    if (!action) {
      vscode.window.showWarningMessage('Scheduler operator action is missing required input.');
      return;
    }

    const startedAt = new Date().toISOString();
    this._lastSchedulerOperatorAction = {
      action: action.kind,
      status: 'running',
      startedAt,
      completedAt: null,
      summary: 'running scheduler operator action',
      stdout: '',
      stderr: '',
      payload: null,
    };
    this._renderShellState({ preserveCurrentPreview: true });

    try {
      const runtime = await this._resolveRuntime(this._workspaceFolder);
      const result = await vscode.window.withProgress(
        {
          location: vscode.ProgressLocation.Notification,
          title: `Scheduler operator: ${action.kind}`,
        },
        async () => runSchedulerOperatorAction({
          projectRoot: runtime.workspaceRoot,
          sourceRoot: runtime.sourceRoot,
          pythonPath: runtime.pythonPath,
          outputChannel: this._outputChannel,
          action,
        }),
      );
      this._lastSchedulerOperatorAction = result;
      if (result.status === 'succeeded') {
        vscode.window.showInformationMessage(`Scheduler operator action completed: ${result.summary}`);
      } else {
        vscode.window.showErrorMessage(`Scheduler operator action failed: ${result.summary}`);
      }
    } catch (error) {
      const messageText = error instanceof Error ? error.message : String(error);
      this._lastSchedulerOperatorAction = {
        action: action.kind,
        status: 'failed',
        startedAt,
        completedAt: new Date().toISOString(),
        summary: messageText,
        stdout: '',
        stderr: '',
        payload: null,
      };
      vscode.window.showErrorMessage(`Scheduler operator action failed: ${messageText}`);
    }

    await this._reload();
  }

  private _coerceSchedulerOperatorAction(message: ProgressGraphPreviewMessage): SchedulerOperatorAction | null {
    return coerceSchedulerOperatorActionMessage(message);
  }

    private _previewUri(workspaceFolder: vscode.WorkspaceFolder): vscode.Uri {
        return vscode.Uri.joinPath(workspaceFolder.uri, '.codex', 'progress-graph', 'latest.html');
    }

  private _controlSnapshotUri(workspaceFolder: vscode.WorkspaceFolder): vscode.Uri {
    return vscode.Uri.joinPath(workspaceFolder.uri, '.codex', 'progress-graph', 'control-snapshot.json');
  }

  private _historyArtifactUri(workspaceFolder: vscode.WorkspaceFolder): vscode.Uri {
    return vscode.Uri.joinPath(workspaceFolder.uri, '.codex', 'progress-graph', 'latest.json');
  }

  private _trajectoryArtifactUri(workspaceFolder: vscode.WorkspaceFolder): vscode.Uri {
    return vscode.Uri.joinPath(workspaceFolder.uri, '.codex', 'progress-graph', 'local-work-trajectory.json');
  }

  private _schedulerTrajectoryArtifactUri(workspaceFolder: vscode.WorkspaceFolder): vscode.Uri {
    return vscode.Uri.joinPath(workspaceFolder.uri, '.codex', 'progress-graph', 'scheduler-work-trajectory.json');
  }

  private async _readArtifactState(workspaceFolder: vscode.WorkspaceFolder): Promise<ProgressGraphPreviewArtifactState> {
        const previewUri = this._previewUri(workspaceFolder);
        const controlSnapshotUri = this._controlSnapshotUri(workspaceFolder);
        const historyArtifactUri = this._historyArtifactUri(workspaceFolder);
        const trajectoryArtifactUri = this._trajectoryArtifactUri(workspaceFolder);
        const schedulerTrajectoryArtifactUri = this._schedulerTrajectoryArtifactUri(workspaceFolder);
        const previewExists = existsSync(previewUri.fsPath);
    const controlSnapshotExists = existsSync(controlSnapshotUri.fsPath);
    const historyArtifactExists = existsSync(historyArtifactUri.fsPath);
    const trajectoryArtifactExists = existsSync(trajectoryArtifactUri.fsPath);
    const schedulerTrajectoryArtifactExists = existsSync(schedulerTrajectoryArtifactUri.fsPath);
    const previewStat = previewExists ? statSync(previewUri.fsPath) : null;
        const previewHtml = previewExists ? readFileSync(previewUri.fsPath, 'utf-8') : null;
    let controlSnapshot: ProgressGraphPreviewControlSnapshot | null = null;
    let controlSnapshotError: string | null = null;
    let localWorkTrajectory: ProgressGraphPreviewLocalWorkTrajectory | null = null;
    let localWorkTrajectoryError: string | null = null;
    let schedulerWorkTrajectory: ProgressGraphPreviewLocalWorkTrajectory | null = null;
    let schedulerWorkTrajectoryError: string | null = null;
    let hostEvidencePresentation: ProgressGraphPreviewHostEvidencePresentation | null = null;
    let hostEvidencePresentationError: string | null = null;
    let schedulerOperatorWorkflow: SchedulerOperatorWorkflowState | null = null;
    let v2GraphPayload: ProgressGraphPreviewV2PoCPayload | null = null;
    let v2GraphPayloadError: string | null = null;

    if (controlSnapshotExists) {
      try {
        controlSnapshot = coerceControlSnapshot(
          JSON.parse(readFileSync(controlSnapshotUri.fsPath, 'utf-8')),
        );
      } catch (error) {
        controlSnapshotError = error instanceof Error ? error.message : String(error);
      }
    }

    if (trajectoryArtifactExists) {
      try {
        localWorkTrajectory = coerceLocalWorkTrajectory(
          JSON.parse(readFileSync(trajectoryArtifactUri.fsPath, 'utf-8')),
        );
      } catch (error) {
        localWorkTrajectoryError = error instanceof Error ? error.message : String(error);
      }
    }

    if (schedulerTrajectoryArtifactExists) {
      try {
        schedulerWorkTrajectory = coerceLocalWorkTrajectory(
          JSON.parse(readFileSync(schedulerTrajectoryArtifactUri.fsPath, 'utf-8')),
        );
      } catch (error) {
        schedulerWorkTrajectoryError = error instanceof Error ? error.message : String(error);
      }
    }

    if (historyArtifactExists) {
      try {
        v2GraphPayload = buildProgressGraphV2PoCPayload(
          JSON.parse(readFileSync(historyArtifactUri.fsPath, 'utf-8')),
          controlSnapshot,
          localWorkTrajectory,
        );
      } catch (error) {
        v2GraphPayloadError = error instanceof Error ? error.message : String(error);
      }
    }

    try {
      const runtime = await this._resolveRuntime(workspaceFolder);
      try {
      hostEvidencePresentation = await readHostEvidencePresentation({
        projectRoot: runtime.workspaceRoot,
        sourceRoot: runtime.sourceRoot,
        pythonPath: runtime.pythonPath,
        outputChannel: this._outputChannel,
      });
      } catch (error) {
        hostEvidencePresentationError = error instanceof Error ? error.message : String(error);
        hostEvidencePresentation = coerceHostEvidencePresentation({
          generated_at: null,
          project_root: workspaceFolder.uri.fsPath,
          evidence_dir: vscode.Uri.joinPath(workspaceFolder.uri, '.codex', 'scheduler', 'evidence').fsPath,
          status: 'failed',
          card_count: 0,
          error_count: 0,
          cards: [],
          error_rows: [],
          empty_message: '',
        });
      }
      schedulerOperatorWorkflow = await readSchedulerOperatorWorkflowState({
        projectRoot: runtime.workspaceRoot,
        sourceRoot: runtime.sourceRoot,
        pythonPath: runtime.pythonPath,
        outputChannel: this._outputChannel,
        lastAction: this._lastSchedulerOperatorAction,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      hostEvidencePresentationError = hostEvidencePresentationError ?? message;
      hostEvidencePresentation = hostEvidencePresentation ?? coerceHostEvidencePresentation({
        generated_at: null,
        project_root: workspaceFolder.uri.fsPath,
        evidence_dir: vscode.Uri.joinPath(workspaceFolder.uri, '.codex', 'scheduler', 'evidence').fsPath,
        status: 'failed',
        card_count: 0,
        error_count: 0,
        cards: [],
        error_rows: [],
        empty_message: '',
      });
      schedulerOperatorWorkflow = await readSchedulerOperatorWorkflowState({
        projectRoot: workspaceFolder.uri.fsPath,
        sourceRoot: null,
        pythonPath: 'python',
        outputChannel: this._outputChannel,
        lastAction: this._lastSchedulerOperatorAction,
      });
    }

        return {
            artifactPath: previewUri.fsPath,
      artifactModifiedAt: previewStat ? previewStat.mtime.toISOString() : null,
      artifactModifiedTimeMs: previewStat ? previewStat.mtimeMs : null,
            controlSnapshotPath: controlSnapshotUri.fsPath,
            controlSnapshotExists,
            controlSnapshot,
            controlSnapshotError,
            historyArtifactPath: historyArtifactUri.fsPath,
            historyArtifactExists,
            trajectoryArtifactPath: trajectoryArtifactUri.fsPath,
            trajectoryArtifactExists,
            schedulerTrajectoryArtifactPath: schedulerTrajectoryArtifactUri.fsPath,
            schedulerTrajectoryArtifactExists,
            previewExists,
            previewHtml,
            localWorkTrajectory,
            localWorkTrajectoryError,
            schedulerWorkTrajectory,
            schedulerWorkTrajectoryError,
            hostEvidencePresentationResourceUri: HOST_EVIDENCE_PRESENTATION_RESOURCE_URI,
            hostEvidencePresentation,
            hostEvidencePresentationError,
            schedulerOperatorWorkflow: schedulerOperatorWorkflow ?? {
              exchangeResourceUri: EXCHANGE_ARTIFACTS_BUNDLE_RESOURCE_URI,
              exchange: null,
              exchangeReadError: 'scheduler operator workflow state was not loaded',
              scheduler: null,
              schedulerReadError: 'scheduler operator workflow state was not loaded',
              paths: buildSchedulerOperatorPaths(workspaceFolder.uri.fsPath),
              lastAction: this._lastSchedulerOperatorAction,
            },
            v2GraphPayload,
            v2GraphPayloadError,
        };
    }

  private _renderShellState(options: { preserveCurrentPreview: boolean }): void {
    if (!this._panel || !this._workspaceFolder) {
      return;
    }

    void this._renderShellStateAsync(options).catch((error) => {
      const message = error instanceof Error ? error.message : String(error);
      this._outputChannel.appendLine(`[ProgressGraphPreview] Failed to render shell state: ${message}`);
    });
  }

  private async _renderShellStateAsync(options: { preserveCurrentPreview: boolean }): Promise<void> {
    if (!this._panel || !this._workspaceFolder) {
      return;
    }

    const artifactState = await this._readArtifactState(this._workspaceFolder);
    const previewHtml = options.preserveCurrentPreview
      ? (this._lastRenderedPreviewHtml ?? artifactState.previewHtml)
      : artifactState.previewHtml;
    const state = this._buildState(artifactState, previewHtml);
    const shellSignature = this._shellSignature(state);
    if (shellSignature === this._lastRenderedShellSignature) {
      return;
    }
    this._panel.title = this._buildPanelTitle(state);
    this._panel.webview.html = this._buildHtml(state);
    this._lastRenderedShellSignature = shellSignature;
  }

  private _buildState(
    artifactState: ProgressGraphPreviewArtifactState,
    previewHtml: string | null,
  ): ProgressGraphPreviewState {
    const freshness = this._determineFreshness(artifactState, previewHtml);
    return {
      ...artifactState,
      previewHtml,
      freshness,
      freshnessLabel: this._freshnessLabel(freshness),
      freshnessMessage: this._freshnessMessage(freshness, artifactState, previewHtml),
      isRefreshRunning: freshness === 'refreshing',
      lastLoadedAt: this._lastLoadedAt,
      lastRefreshStartedAt: this._refreshLifecycle.startedAt,
      lastRefreshCompletedAt: this._refreshLifecycle.completedAt,
      lastRefreshError: this._refreshLifecycle.errorMessage,
      v2GraphScriptUri: this._panel
        ? this._panel.webview.asWebviewUri(
            vscode.Uri.joinPath(this._extensionUri, 'dist', 'webviews', 'progressGraphV2Engine.js'),
        ).toString()
        : null,
      v2GraphWorkerUri: this._panel
        ? this._panel.webview.asWebviewUri(
            vscode.Uri.joinPath(this._extensionUri, 'dist', 'webviews', 'knowledgeGraphForceWorker.js'),
        ).toString()
        : null,
      v2GraphAutoShake: freshness !== 'refreshing',
      localWorkTrajectoryScriptUri: this._panel
        ? this._panel.webview.asWebviewUri(
            vscode.Uri.joinPath(this._extensionUri, 'dist', 'webviews', 'localWorkTrajectory.js'),
        ).toString()
        : null,
      localWorkTrajectoryStyleUri: this._panel
        ? this._panel.webview.asWebviewUri(
            vscode.Uri.joinPath(this._extensionUri, 'dist', 'webviews', 'localWorkTrajectory.css'),
        ).toString()
        : null,
    };
  }

  private _determineFreshness(
    artifactState: ProgressGraphPreviewArtifactState,
    previewHtml: string | null,
  ): ProgressGraphPreviewFreshness {
    if (this._refreshLifecycle.status === 'refreshing') {
      return 'refreshing';
    }
    if (this._refreshLifecycle.status === 'failed') {
      return 'failed';
    }
    if (!artifactState.previewExists) {
      return 'missing';
    }
    if (
      artifactState.artifactModifiedTimeMs !== null
      && this._lastLoadedArtifactModifiedTimeMs !== null
      && artifactState.artifactModifiedTimeMs > this._lastLoadedArtifactModifiedTimeMs + 1
    ) {
      return 'stale';
    }
    return previewHtml ? 'fresh' : 'missing';
  }

  private _freshnessLabel(freshness: ProgressGraphPreviewFreshness): string {
    switch (freshness) {
      case 'fresh':
        return 'Fresh';
      case 'stale':
        return 'Stale';
      case 'refreshing':
        return 'Refreshing';
      case 'failed':
        return 'Refresh Failed';
      case 'missing':
      default:
        return 'Missing Artifact';
    }
  }

  private _freshnessMessage(
    freshness: ProgressGraphPreviewFreshness,
    artifactState: ProgressGraphPreviewArtifactState,
    previewHtml: string | null,
  ): string {
    switch (freshness) {
      case 'fresh':
        return '当前面板与最新已知 artifact 一致。';
      case 'stale':
        return '磁盘上的 artifact 比当前面板更新；当前仍显示上一次已加载的预览。点击 Refresh Preview 可加载最新结果。';
      case 'refreshing':
        return '正在重新生成 progress graph artifacts；当前暂时保留已加载的预览。';
      case 'failed':
        return previewHtml
          ? `刷新失败；当前保留上一次已加载的预览。修复问题后可再次点击 Refresh Preview。${this._refreshLifecycle.errorMessage ?? ''}`.trim()
          : `刷新失败，且当前没有可展示的预览。修复问题后可再次点击 Refresh Preview。${this._refreshLifecycle.errorMessage ?? ''}`.trim();
      case 'missing':
      default:
        return previewHtml && !artifactState.previewExists
          ? '当前磁盘上已找不到 latest.html，但面板仍保留上一次已加载的预览。点击 Refresh Preview 可尝试重建 artifact。'
          : '当前 workspace 中还没有可加载的 latest.html artifact。请先点击 Refresh Preview。';
    }
  }

  private _buildPanelTitle(state: ProgressGraphPreviewState): string {
    switch (state.freshness) {
      case 'refreshing':
        return 'Progress Graph (Refreshing)';
      case 'stale':
        return 'Progress Graph (Stale)';
      case 'failed':
        return 'Progress Graph (Refresh Failed)';
      case 'missing':
        return 'Progress Graph (Missing Artifact)';
      case 'fresh':
      default:
        return 'Progress Graph';
    }
  }

  private _shellSignature(state: ProgressGraphPreviewState): string {
    return JSON.stringify({
      freshness: state.freshness,
      artifactModifiedAt: state.artifactModifiedAt,
      previewExists: state.previewExists,
      controlSnapshotExists: state.controlSnapshotExists,
      controlSnapshotGeneratedAt: state.controlSnapshot?.generated_at ?? null,
      controlSnapshotError: state.controlSnapshotError,
      historyArtifactExists: state.historyArtifactExists,
      trajectoryArtifactExists: state.trajectoryArtifactExists,
      trajectoryId: state.localWorkTrajectory?.trajectoryId ?? null,
      trajectoryError: state.localWorkTrajectoryError,
      schedulerTrajectoryArtifactExists: state.schedulerTrajectoryArtifactExists,
      schedulerTrajectoryId: state.schedulerWorkTrajectory?.trajectoryId ?? null,
      schedulerTrajectoryError: state.schedulerWorkTrajectoryError,
      hostEvidencePresentationStatus: state.hostEvidencePresentation?.status ?? null,
      hostEvidencePresentationCardCount: state.hostEvidencePresentation?.cardCount ?? null,
      hostEvidencePresentationErrorCount: state.hostEvidencePresentation?.errorCount ?? null,
      hostEvidencePresentationCardIds: state.hostEvidencePresentation?.cards.map((card) => card.id) ?? [],
      hostEvidencePresentationErrorIds: state.hostEvidencePresentation?.errorRows.map((row) => row.id) ?? [],
      hostEvidencePresentationError: state.hostEvidencePresentationError,
      schedulerOperatorExchangeCandidateCount: state.schedulerOperatorWorkflow.exchange?.admissionCandidateCount ?? null,
      schedulerOperatorCandidateKeys: state.schedulerOperatorWorkflow.exchange?.candidates.map(
        (candidate) => `${candidate.artifactId}@${candidate.version}:${candidate.admissionStatus}`,
      ) ?? [],
      schedulerOperatorExchangeReadError: state.schedulerOperatorWorkflow.exchangeReadError,
      schedulerOperatorLastAction: state.schedulerOperatorWorkflow.lastAction,
      v2GraphId: state.v2GraphPayload?.graphId ?? null,
      v2GraphPayloadError: state.v2GraphPayloadError,
      v2GraphScriptUri: state.v2GraphScriptUri,
      v2GraphWorkerUri: state.v2GraphWorkerUri,
      v2GraphAutoShake: state.v2GraphAutoShake,
      localWorkTrajectoryScriptUri: state.localWorkTrajectoryScriptUri,
      localWorkTrajectoryStyleUri: state.localWorkTrajectoryStyleUri,
      lastLoadedAt: state.lastLoadedAt,
      lastRefreshStartedAt: state.lastRefreshStartedAt,
      lastRefreshCompletedAt: state.lastRefreshCompletedAt,
      lastRefreshError: state.lastRefreshError,
    });
  }

    private _buildHtml(state: ProgressGraphPreviewState): string {
        return buildProgressGraphPreviewHtml(state);
    }

}

type RawSnapshotNode = {
  id: string;
  title: string;
  kind: string;
  status: string;
  summary: string;
  tags: string[];
};

type RawSnapshotEdge = {
  source: string;
  target: string;
  kind: string;
  directed: boolean;
};

type RawSnapshotGraph = {
  graphId: string;
  title: string;
  snapshotId: string | null;
  recordedAt: string | null;
  sourcePath: string | null;
  nodes: RawSnapshotNode[];
  edges: RawSnapshotEdge[];
};

function buildProgressGraphV2PoCPayload(
  rawHistory: unknown,
  controlSnapshot: ProgressGraphPreviewControlSnapshot | null,
  localWorkTrajectory: ProgressGraphPreviewLocalWorkTrajectory | null,
): ProgressGraphPreviewV2PoCPayload {
  const history = asRecord(rawHistory, 'history artifact');
  const snapshots = asRecord(history.snapshots, 'history.snapshots');
  const candidateGraphs = Object.values(snapshots)
    .flatMap((snapshot) => {
      try {
        return [coerceSnapshotGraph(snapshot)];
      } catch {
        return [];
      }
    })
    .filter((graph) => graph.nodes.length > 0);

  const selectedGraph = selectV2Graph(candidateGraphs, localWorkTrajectory);
  if (!selectedGraph) {
    throw new Error('latest.json does not contain a usable graph snapshot for the V2 PoC.');
  }

  const runtimeBindingIndex = buildRuntimeBindingIndex(controlSnapshot, selectedGraph.graphId);
  const trajectoryAnchorMatchesGraph = localWorkTrajectory?.sourceGraphId === selectedGraph.graphId;
  const nodes = selectedGraph.nodes.map((node) => {
    const binding = runtimeBindingIndex.get(node.id);
    const hasLocalTrajectory = Boolean(
      trajectoryAnchorMatchesGraph
      && localWorkTrajectory?.sourceNodeId
      && localWorkTrajectory.sourceNodeId === node.id,
    );
    return {
      id: node.id,
      label: node.title,
      kind: node.kind,
      status: node.status,
      summary: node.summary,
      tags: node.tags,
      hasRuntimeBinding: Boolean(binding),
      hasLocalTrajectory,
      localTrajectoryId: hasLocalTrajectory ? localWorkTrajectory?.trajectoryId ?? null : null,
      workItemIds: binding ? [...binding.workItemIds] : [],
      groupItemIds: binding ? [...binding.groupItemIds] : [],
    };
  });

  return {
    graphId: selectedGraph.graphId,
    title: selectedGraph.title,
    snapshotId: selectedGraph.snapshotId,
    recordedAt: selectedGraph.recordedAt,
    sourcePath: selectedGraph.sourcePath,
    nodeCount: nodes.length,
    edgeCount: selectedGraph.edges.length,
    nodes,
    edges: selectedGraph.edges.map((edge, index) => ({
      id: `${edge.source}=>${edge.target}#${index}`,
      source: edge.source,
      target: edge.target,
      kind: edge.kind,
      directed: edge.directed,
    })),
    runtimeSummary: {
      boundNodeCount: nodes.filter((node) => node.hasRuntimeBinding).length,
      openWorkItemCount: controlSnapshot?.summary.open_work_item_count ?? 0,
      activeGroupItemCount: controlSnapshot?.summary.active_group_item_count ?? 0,
      unboundGroupItemCount: controlSnapshot?.summary.unbound_group_item_count ?? 0,
    },
  };
}

function selectV2Graph(
  graphs: RawSnapshotGraph[],
  localWorkTrajectory: ProgressGraphPreviewLocalWorkTrajectory | null = null,
): RawSnapshotGraph | null {
  if (graphs.length === 0) {
    return null;
  }

  const anchoredGraphId = localWorkTrajectory?.sourceGraphId;
  const anchoredNodeId = localWorkTrajectory?.sourceNodeId;
  if (anchoredGraphId && anchoredNodeId) {
    const anchoredGraph = graphs.find(
      (graph) => graph.graphId === anchoredGraphId
        && graph.nodes.some((node) => node.id === anchoredNodeId),
    );
    if (anchoredGraph) {
      return anchoredGraph;
    }
  }

  const preferredOrder = ['project-checklist-current', 'planning-gates-index', 'checkpoint-current'];
  const preferenceIndex = new Map(preferredOrder.map((graphId, index) => [graphId, preferredOrder.length - index]));
  const edgefulGraphs = graphs.filter((graph) => graph.edges.length > 0);
  const selectionPool = edgefulGraphs.length > 0 ? edgefulGraphs : graphs;

  return [...selectionPool].sort((left, right) => {
    const leftPriority = preferenceIndex.get(left.graphId) ?? 0;
    const rightPriority = preferenceIndex.get(right.graphId) ?? 0;
    if (leftPriority !== rightPriority) {
      return rightPriority - leftPriority;
    }
    const leftRecordedAt = Number.isNaN(Date.parse(left.recordedAt ?? '')) ? 0 : Date.parse(left.recordedAt ?? '');
    const rightRecordedAt = Number.isNaN(Date.parse(right.recordedAt ?? '')) ? 0 : Date.parse(right.recordedAt ?? '');
    if (leftRecordedAt !== rightRecordedAt) {
      return rightRecordedAt - leftRecordedAt;
    }
    if (left.edges.length !== right.edges.length) {
      return right.edges.length - left.edges.length;
    }
    return right.nodes.length - left.nodes.length;
  })[0] ?? null;
}

function buildRuntimeBindingIndex(
  controlSnapshot: ProgressGraphPreviewControlSnapshot | null,
  graphId: string,
): Map<string, { workItemIds: Set<string>; groupItemIds: Set<string> }> {
  const index = new Map<string, { workItemIds: Set<string>; groupItemIds: Set<string> }>();

  for (const binding of controlSnapshot?.bindings ?? []) {
    if (binding.graph_id !== graphId || !binding.graph_target_id) {
      continue;
    }

    const existing = index.get(binding.graph_target_id) ?? {
      workItemIds: new Set<string>(),
      groupItemIds: new Set<string>(),
    };

    for (const workItemId of binding.work_item_ids) {
      existing.workItemIds.add(workItemId);
    }
    for (const groupItemId of binding.group_item_ids) {
      existing.groupItemIds.add(groupItemId);
    }

    index.set(binding.graph_target_id, existing);
  }

  return index;
}

function coerceSnapshotGraph(value: unknown): RawSnapshotGraph {
  const snapshot = asRecord(value, 'snapshot');
  const graphId = readString(snapshot.graph_id, 'snapshot.graph_id');
  const title = readOptionalString(snapshot.title) ?? graphId;
  const recordedAt = readOptionalString(snapshot.recorded_at);
  const snapshotId = readOptionalString(snapshot.snapshot_id);
  const metadata = asOptionalRecord(snapshot.metadata);
  const nodesRecord = asRecord(snapshot.nodes, 'snapshot.nodes');
  const nodes = Object.entries(nodesRecord).map(([fallbackId, rawNode]) => {
    const node = asRecord(rawNode, `snapshot.nodes.${fallbackId}`);
    return {
      id: readOptionalString(node.id) ?? fallbackId,
      title: readOptionalString(node.title) ?? fallbackId,
      kind: readOptionalString(node.kind) ?? 'task',
      status: readOptionalString(node.status) ?? 'pending',
      summary: readOptionalString(node.summary) ?? '',
      tags: readStringArray(node.tags),
    };
  });
  const nodeIds = new Set(nodes.map((node) => node.id));
  const edges = readArray(snapshot.edges).flatMap((rawEdge) => {
    const edge = asOptionalRecord(rawEdge);
    const source = readOptionalString(edge?.source);
    const target = readOptionalString(edge?.target);
    if (!source || !target || !nodeIds.has(source) || !nodeIds.has(target)) {
      return [];
    }

    return [{
      source,
      target,
      kind: readOptionalString(edge?.kind) ?? 'workflow',
      directed: readOptionalBoolean(edge?.is_directed) ?? true,
    }];
  });

  return {
    graphId,
    title,
    snapshotId,
    recordedAt,
    sourcePath: readOptionalString(metadata?.source_path),
    nodes,
    edges,
  };
}

function asRecord(value: unknown, label: string): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error(`Expected ${label} to be an object.`);
  }
  return value as Record<string, unknown>;
}

function asOptionalRecord(value: unknown): Record<string, unknown> | null {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return null;
  }
  return value as Record<string, unknown>;
}

function readArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function readString(value: unknown, label: string): string {
  if (typeof value !== 'string' || !value.trim()) {
    throw new Error(`Expected ${label} to be a non-empty string.`);
  }
  return value;
}

function readOptionalString(value: unknown): string | null {
  return typeof value === 'string' && value.trim() ? value : null;
}

function readOptionalBoolean(value: unknown): boolean | null {
  return typeof value === 'boolean' ? value : null;
}

function readStringArray(value: unknown): string[] {
  return readArray(value)
    .filter((entry): entry is string => typeof entry === 'string' && entry.trim().length > 0);
}
