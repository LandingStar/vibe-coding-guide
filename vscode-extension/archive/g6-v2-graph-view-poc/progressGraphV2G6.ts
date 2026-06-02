/// <reference lib="dom" />

import { Graph } from '@antv/g6';
import {
  createDefaultMotionController,
  type MotionControlControllerFactory,
  type MotionControlNode,
} from './progressGraphMotionControl';

type ProgressGraphPreviewV2PoCNode = {
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

type ProgressGraphPreviewV2PoCEdge = {
  id: string;
  source: string;
  target: string;
  kind: string;
  directed: boolean;
};

type ProgressGraphPreviewV2PoCPayload = {
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

type ProgressGraphPreviewVsCodeApi = {
  getState(): unknown;
  setState(state: unknown): void;
  postMessage(message: unknown): void;
};

type V2GraphAppearanceSettings = {
  labelDensity: number;
  labelSize: number;
  nodeScale: number;
  edgeScale: number;
};

type V2GraphForceSettings = {
  gravity: number;
  repulsion: number;
  attraction: number;
  linkLength: number;
};

type V2GraphColorGroup = {
  id: string;
  query: string;
  color: string;
};

type V2GraphConfigState = {
  appearance: V2GraphAppearanceSettings;
  forces: V2GraphForceSettings;
  colorGroups: V2GraphColorGroup[];
  ui: {
    configCollapsed: boolean;
    sidePanelWidth: number;
  };
};

type GraphInteractionState = {
  hoveredNode: string | null;
  selectedNode: string | null;
};

type NodePosition = {
  x: number;
  y: number;
};

type G6ForceMonitorParams = {
  energy?: number;
  iterations?: number;
  nodes?: MotionControlNode[];
};

const createGraphMotionController: MotionControlControllerFactory = createDefaultMotionController;

type GraphNodeRenderData = ProgressGraphPreviewV2PoCNode & {
  visualColor: string;
};

type ColorQueryWordToken = {
  type: 'word';
  value: string;
};

type ColorQueryPhraseToken = {
  type: 'phrase';
  value: string;
};

type ColorQueryRegexToken = {
  type: 'regex';
  pattern: string;
  flags: string;
};

type ColorQueryBracketToken = {
  type: 'bracket';
  value: string;
};

type ColorQueryToken =
  | { type: 'lparen' }
  | { type: 'rparen' }
  | { type: 'or' }
  | { type: 'negate' }
  | ColorQueryWordToken
  | ColorQueryPhraseToken
  | ColorQueryRegexToken
  | ColorQueryBracketToken;

type ColorQueryTerm = ColorQueryWordToken | ColorQueryPhraseToken | ColorQueryRegexToken;

type ColorQueryScope =
  | 'file'
  | 'path'
  | 'content'
  | 'tag'
  | 'line'
  | 'block'
  | 'section'
  | 'task'
  | 'task-todo'
  | 'task-done'
  | 'kind'
  | 'status'
  | 'label'
  | 'summary'
  | 'bound'
  | 'match-case'
  | 'ignore-case';

type ColorQuerySearchScope = 'default' | 'file' | 'path' | 'content' | 'tag' | 'kind' | 'status' | 'label' | 'summary' | 'bound';
type ColorQueryCaseMode = 'default' | 'match-case' | 'ignore-case';

type ColorQueryExpression =
  | { kind: 'and'; expressions: ColorQueryExpression[] }
  | { kind: 'or'; expressions: ColorQueryExpression[] }
  | { kind: 'not'; expression: ColorQueryExpression }
  | { kind: 'case'; mode: ColorQueryCaseMode; expression: ColorQueryExpression }
  | { kind: 'scope'; scope: ColorQueryScope; expression: ColorQueryExpression }
  | { kind: 'property'; property: string; expression: ColorQueryExpression | null }
  | { kind: 'term'; term: ColorQueryTerm };

type CompiledColorGroup = V2GraphColorGroup & {
  compiledQuery: ColorQueryExpression;
};

type ColorQueryContext = {
  nodeId: string;
  node: ProgressGraphPreviewV2PoCNode;
};

declare global {
  interface Window {
    __pgHostVsCodeApi?: ProgressGraphPreviewVsCodeApi;
    __pgHostV2GraphCleanup?: () => void;
  }
}

const colorGroupPalette = ['#e55d5d', '#4d95d8', '#59a57b', '#d3a04e', '#8d6ad8', '#4ea8a0'];

const defaultGraphConfigState: V2GraphConfigState = {
  appearance: {
    labelDensity: 0.14,
    labelSize: 13,
    nodeScale: 1,
    edgeScale: 1,
  },
  forces: {
    gravity: 10,
    repulsion: 1000,
    attraction: 50,
    linkLength: 200,
  },
  colorGroups: [{ id: 'color-group-seed', query: '', color: colorGroupPalette[0] }],
  ui: {
    configCollapsed: false,
    sidePanelWidth: 344,
  },
};

const statusColors: Record<string, string> = {
  pending: '#b3904a',
  in_progress: '#3f84b7',
  blocked: '#b95f57',
  completed: '#5f9e72',
  archived: '#8a949f',
};

const edgeColors: Record<string, string> = {
  workflow: '#5a89bd',
  dependency: '#d29a46',
  reference: '#7b8491',
};

async function main(): Promise<void> {
  const container = document.getElementById('pgHostV2GraphCanvas');
  const detail = document.getElementById('pgHostV2GraphDetail');
  if (!(container instanceof HTMLElement) || !(detail instanceof HTMLElement)) {
    return;
  }
  const canvasShell = container.parentElement instanceof HTMLElement ? container.parentElement : container;

  // Single-owner guard: if this script is executed again in the same webview,
  // dispose the previous graph instance first to avoid stacked canvases.
  window.__pgHostV2GraphCleanup?.();
  window.__pgHostV2GraphCleanup = undefined;

  const payload = readPayload();
  if (!payload || payload.nodes.length === 0) {
    renderEmpty(container, detail, '当前没有可渲染的 G6 graph payload。');
    return;
  }

  const configState = loadGraphConfigState();
  const interactionState: GraphInteractionState = {
    hoveredNode: null,
    selectedNode: null,
  };
  const nodesById = new Map(payload.nodes.map((node) => [node.id, node]));
  const degrees = buildDegrees(payload);
  const neighborsByNode = buildNeighborsIndex(payload.edges);
  const connectedEdgesByNode = buildConnectedEdgesIndex(payload.edges);
  const persistConfigState = createDebouncedCallback(() => {
    persistGraphConfigState(configState);
  }, 120);
  const scheduleForceLayoutRefresh = createDebouncedCallback(() => {
    scheduleVisualRefresh({ rerunLayout: true });
  }, 160);

  let destroyed = false;
  let refreshScheduled = false;
  let refreshInFlight = false;
  let refreshQueued = false;
  let layoutRefreshPending = false;
  let activeForceLayoutRunId = 0;
  let draggingNodeId: string | null = null;
  let hoverResumeTimer: number | null = null;
  let hoverSuppressedUntil = 0;
  let suppressNextNodeClick = false;
  let suppressNodeClickTimer: number | null = null;
  let observedWidth = canvasShell.clientWidth;
  let observedHeight = canvasShell.clientHeight;
  let fitViewFrameId: number | null = null;
  let fitViewSettledFrameId: number | null = null;
  let canvasResizeObserver: ResizeObserver | null = null;
  let metricsCollapsed = false;
  let resizingSidePanel = false;
  let configCardMorphAnimation: Animation | null = null;
  let detailCardMorphAnimation: Animation | null = null;
  let configPanelTitleAnimation: Animation | null = null;
  let configTitleGhostAnimation: Animation | null = null;
  let configCollapsedBarAnimation: Animation | null = null;
  const configCard = document.getElementById('pgHostV2ConfigCard');
  const configCardContent = document.getElementById('pgHostV2ConfigCardContent');
  const configCardTitle = document.getElementById('pgHostV2ConfigCardTitle');
  const configTitleGhost = document.getElementById('pgHostV2ConfigTitleGhost');
  const configToggleButton = document.getElementById('pgHostV2ConfigToggle');
  const collapsedConfigBar = document.getElementById('pgHostV2ConfigCollapsedBar');
  const metricsDock = document.getElementById('pgHostV2MetricsDock');
  const inlineMetrics = document.getElementById('pgHostV2MetricsInline');
  const sideMetrics = document.getElementById('pgHostV2MetricsSide');
  const layoutRoot = document.getElementById('pgHostV2Layout');
  const sideArea = document.getElementById('pgHostV2Side');
  const detailCard = document.getElementById('pgHostV2NodeDetailCard');
  const clearSelectionButton = document.getElementById('pgHostV2ClearSelection');
  const resizeHandle = document.getElementById('pgHostV2ResizeHandle');

  const graph = new Graph({
    container,
    autoFit: false,
    zoomRange: [0.04, 8],
    node: {
      state: {
        selected: {
          halo: false,
          // Neutralize G6 base theme selected lineWidth=4 override.
          // Keep it aligned with the normal node stroke width policy.
          lineWidth: (datum: { data?: { hasRuntimeBinding?: boolean } }) => datum.data?.hasRuntimeBinding ? 1.8 : 1.3,
          labelFontSize: 12,
          labelFontWeight: 400,
        },
        'pg-hover': {
          fill: (datum: { data?: GraphNodeRenderData }) => hexToRgba(resolveNodeVisualColor(datum.data), 0.78),
          stroke: (datum: { data?: GraphNodeRenderData }) => resolveNodeVisualColor(datum.data),
          strokeOpacity: 0.98,
          lineWidth: (datum: { data?: { hasRuntimeBinding?: boolean } }) => datum.data?.hasRuntimeBinding ? 1.8 : 1.3,
          shadowBlur: 10,
          shadowColor: (datum: { data?: GraphNodeRenderData }) => hexToRgba(resolveNodeVisualColor(datum.data), 0.24),
          labelOpacity: 0.92,
          labelFill: 'rgba(22, 31, 39, 0.96)',
        },
        'pg-selected': {
          fill: (datum: { data?: GraphNodeRenderData }) => hexToRgba(resolveNodeVisualColor(datum.data), 0.9),
          stroke: (datum: { data?: GraphNodeRenderData }) => resolveNodeVisualColor(datum.data),
          strokeOpacity: 1,
          lineWidth: (datum: { data?: { hasRuntimeBinding?: boolean } }) => datum.data?.hasRuntimeBinding ? 1.8 : 1.3,
          halo: true,
          haloLineWidth: 18,
          haloStroke: (datum: { data?: GraphNodeRenderData }) => resolveNodeVisualColor(datum.data),
          haloStrokeOpacity: 0.24,
          shadowBlur: 22,
          shadowColor: (datum: { data?: GraphNodeRenderData }) => hexToRgba(resolveNodeVisualColor(datum.data), 0.42),
          labelOpacity: 1,
          labelFontWeight: 700,
          labelFill: 'rgba(15, 21, 28, 0.98)',
        },
        'pg-related': {
          fill: (datum: { data?: GraphNodeRenderData }) => hexToRgba(resolveNodeVisualColor(datum.data), 0.5),
          stroke: (datum: { data?: GraphNodeRenderData }) => resolveNodeVisualColor(datum.data),
          strokeOpacity: 0.78,
          lineWidth: (datum: { data?: { hasRuntimeBinding?: boolean } }) => datum.data?.hasRuntimeBinding ? 1.8 : 1.3,
          shadowBlur: 6,
          shadowColor: (datum: { data?: GraphNodeRenderData }) => hexToRgba(resolveNodeVisualColor(datum.data), 0.14),
          labelOpacity: 0.9,
          labelFill: 'rgba(24, 34, 43, 0.94)',
        },
        'pg-dimmed': {
          fill: (datum: { data?: GraphNodeRenderData }) => hexToRgba(blendHexColors(resolveNodeVisualColor(datum.data), '#a6afb8', 0.68), 0.16),
          stroke: (datum: { data?: GraphNodeRenderData }) => blendHexColors(resolveNodeVisualColor(datum.data), '#a6afb8', 0.68),
          strokeOpacity: 0.32,
          lineWidth: (datum: { data?: { hasRuntimeBinding?: boolean } }) => datum.data?.hasRuntimeBinding ? 1.8 : 1.3,
          labelOpacity: 0.3,
          labelFill: 'rgba(77, 88, 99, 0.56)',
          shadowBlur: 0,
          shadowColor: 'transparent',
        },
      },
    },
    edge: {
      state: {
        'pg-related': {
          stroke: (datum: { data?: ProgressGraphPreviewV2PoCEdge }) => edgeColors[datum.data?.kind ?? ''] ?? '#7b8491',
          strokeOpacity: 0.72,
          lineWidth: 1.75,
          endArrowOpacity: 0.72,
        },
        'pg-dimmed': {
          stroke: (datum: { data?: ProgressGraphPreviewV2PoCEdge }) => blendHexColors(edgeColors[datum.data?.kind ?? ''] ?? '#7b8491', '#a6afb8', 0.72),
          strokeOpacity: 0.14,
          lineWidth: 1.05,
          endArrowOpacity: 0.18,
        },
      },
    },
    behaviors: [
      'drag-canvas',
      { type: 'zoom-canvas', sensitivity: 0.9 },
      'drag-element',
    ],
    layout: buildLayoutConfig(canvasShell, configState, payload),
    data: buildGraphData(payload, configState, interactionState, degrees, neighborsByNode, connectedEdgesByNode),
  });

  const renderCurrentDetail = (): void => {
    if (clearSelectionButton instanceof HTMLButtonElement) {
      clearSelectionButton.disabled = !interactionState.selectedNode;
    }
    renderNodeDetail(
      detail,
      interactionState.selectedNode
        ? nodesById.get(interactionState.selectedNode) ?? null
        : interactionState.hoveredNode
          ? nodesById.get(interactionState.hoveredNode) ?? null
          : null,
      payload.runtimeSummary,
      interactionState.selectedNode,
    );
  };

  const scheduleVisualRefresh = (options: { rerunLayout?: boolean } = {}): void => {
    if (destroyed) {
      return;
    }

    if (options.rerunLayout) {
      layoutRefreshPending = true;
    }

    renderCurrentDetail();

    refreshQueued = true;
    if (refreshScheduled || refreshInFlight) {
      return;
    }

    refreshScheduled = true;
    requestAnimationFrame(() => {
      refreshScheduled = false;
      refreshInFlight = true;
      refreshQueued = false;
      void applyVisualState().finally(() => {
        refreshInFlight = false;
        if (destroyed) {
          return;
        }
        if (refreshQueued || layoutRefreshPending) {
          scheduleVisualRefresh();
        }
      });
    });
  };

  const resetViewport = async (): Promise<void> => {
    if (destroyed) {
      return;
    }
    await graph.fitView({ direction: 'both', when: 'always' });
  };

  const applySplitLayoutState = (): void => {
    if (!(layoutRoot instanceof HTMLElement)) {
      return;
    }
    const maxWidth = Math.min(620, Math.max(320, layoutRoot.clientWidth - 320));
    configState.ui.sidePanelWidth = clampNumber(configState.ui.sidePanelWidth, 280, maxWidth, defaultGraphConfigState.ui.sidePanelWidth);
    layoutRoot.style.setProperty('--pg-host-v2-side-width', `${Math.round(configState.ui.sidePanelWidth)}px`);
  };

  const applyInlineMetricsState = (): void => {
    if (inlineMetrics instanceof HTMLElement) {
      inlineMetrics.dataset.pgMetricsCollapsed = metricsCollapsed ? 'true' : 'false';
    }
  };

  const clearConfigPanelMorphState = (): void => {
    if (configCard instanceof HTMLElement) {
      configCard.dataset.pgConfigMorphing = 'false';
      configCard.dataset.pgConfigMorphDirection = 'idle';
    }
    if (collapsedConfigBar instanceof HTMLButtonElement) {
      collapsedConfigBar.dataset.pgConfigMorphing = 'false';
      collapsedConfigBar.dataset.pgConfigMorphDirection = 'idle';
    }
    if (detailCard instanceof HTMLElement) {
      detailCard.dataset.pgConfigMorphing = 'false';
    }
    if (configTitleGhost instanceof HTMLElement) {
      configTitleGhost.style.opacity = '0';
      configTitleGhost.style.left = '';
      configTitleGhost.style.top = '';
      configTitleGhost.style.fontSize = '';
      configTitleGhost.style.fontWeight = '';
      configTitleGhost.style.lineHeight = '';
      configTitleGhost.style.letterSpacing = '';
      configTitleGhost.style.fontFamily = '';
      configTitleGhost.style.color = '';
    }
    if (collapsedConfigBar instanceof HTMLButtonElement) {
      collapsedConfigBar.style.opacity = '';
      collapsedConfigBar.style.transform = '';
      collapsedConfigBar.style.zIndex = '';
    }
    if (configCard instanceof HTMLElement) {
      configCard.style.opacity = '';
      configCard.style.pointerEvents = '';
      configCard.style.position = '';
      configCard.style.left = '';
      configCard.style.top = '';
      configCard.style.width = '';
      configCard.style.height = '';
      configCard.style.inset = '';
      configCard.style.margin = '';
      configCard.style.zIndex = '';
      configCard.style.overflow = '';
    }
    if (configCardContent instanceof HTMLElement) {
      configCardContent.style.opacity = '';
      configCardContent.style.transform = '';
      configCardContent.style.pointerEvents = '';
      configCardContent.style.transitionDelay = '';
    }
  };

  const setConfigCardFloatingBounds = (rect: DOMRect): void => {
    if (!(configCard instanceof HTMLElement)) {
      return;
    }
    configCard.style.position = 'fixed';
    configCard.style.left = `${rect.left}px`;
    configCard.style.top = `${rect.top}px`;
    configCard.style.width = `${rect.width}px`;
    configCard.style.height = `${rect.height}px`;
    configCard.style.inset = 'auto';
    configCard.style.margin = '0';
    configCard.style.zIndex = '6';
    configCard.style.overflow = 'hidden';
  };

  const prepareConfigCardContentForMorph = (mode: 'expand' | 'collapse'): void => {
    if (!(configCardContent instanceof HTMLElement)) {
      return;
    }

    configCardContent.style.pointerEvents = 'none';
    configCardContent.style.transitionDelay = '0ms';

    if (mode === 'collapse') {
      configCardContent.style.opacity = '0';
      configCardContent.style.transform = 'translateY(10px)';
      return;
    }

    configCardContent.style.opacity = '0';
    configCardContent.style.transform = 'translateY(12px)';
    void configCardContent.getBoundingClientRect();
    configCardContent.style.transitionDelay = '90ms';
    configCardContent.style.opacity = '1';
    configCardContent.style.transform = 'translateY(0px)';
  };

  const releaseMorphAnimation = (animation: Animation | null): void => {
    if (!animation) {
      return;
    }
    animation.onfinish = null;
    animation.oncancel = null;
    animation.cancel();
  };

  const cancelConfigPanelMorphAnimations = (): void => {
    releaseMorphAnimation(configCardMorphAnimation);
    configCardMorphAnimation = null;
    releaseMorphAnimation(detailCardMorphAnimation);
    detailCardMorphAnimation = null;
    releaseMorphAnimation(configPanelTitleAnimation);
    configPanelTitleAnimation = null;
    releaseMorphAnimation(configTitleGhostAnimation);
    configTitleGhostAnimation = null;
    releaseMorphAnimation(configCollapsedBarAnimation);
    configCollapsedBarAnimation = null;
    clearConfigPanelMorphState();
  };

  const buildPanelBoundsKeyframes = (fromRect: DOMRect, toRect: DOMRect): Keyframe[] => {
    return [
      {
        left: `${fromRect.left}px`,
        top: `${fromRect.top}px`,
        width: `${fromRect.width}px`,
        height: `${fromRect.height}px`,
        borderRadius: '999px',
        background: 'rgba(250, 247, 240, 0.92)',
        boxShadow: '0 16px 30px rgba(38, 49, 60, 0.14)',
        opacity: 1,
      },
      {
        left: `${toRect.left}px`,
        top: `${toRect.top}px`,
        width: `${toRect.width}px`,
        height: `${toRect.height}px`,
        borderRadius: '16px',
        background: 'rgba(249, 246, 239, 0.94)',
        boxShadow: '0 18px 34px rgba(38, 49, 60, 0.14)',
        opacity: 1,
      },
    ];
  };

  const applyConfigTitleGhostSnapshot = (anchorElement: HTMLElement, rect: DOMRect): void => {
    if (!(configTitleGhost instanceof HTMLElement)) {
      return;
    }

    const anchorStyles = window.getComputedStyle(anchorElement);
    configTitleGhost.style.left = `${rect.left}px`;
    configTitleGhost.style.top = `${rect.top}px`;
    configTitleGhost.style.fontSize = anchorStyles.fontSize;
    configTitleGhost.style.fontWeight = anchorStyles.fontWeight;
    configTitleGhost.style.lineHeight = anchorStyles.lineHeight;
    configTitleGhost.style.letterSpacing = anchorStyles.letterSpacing;
    configTitleGhost.style.fontFamily = anchorStyles.fontFamily;
    configTitleGhost.style.color = anchorStyles.color;
  };

  const runConfigTitleFade = (
    collapsed: boolean,
    sourceRect: DOMRect,
    targetRect: DOMRect,
    timing: KeyframeAnimationOptions,
  ): void => {
    if (!(collapsedConfigBar instanceof HTMLButtonElement) || !(configCardTitle instanceof HTMLElement)) {
      return;
    }

    if (!collapsed) {
      configPanelTitleAnimation = configCardTitle.animate([{ opacity: 0 }, { opacity: 1 }], timing);
      configPanelTitleAnimation.onfinish = () => {
        const completedAnimation = configPanelTitleAnimation;
        configPanelTitleAnimation = null;
        releaseMorphAnimation(completedAnimation);
      };
      configPanelTitleAnimation.oncancel = () => {
        configPanelTitleAnimation = null;
      };

      collapsedConfigBar.style.transform = 'translateY(0px)';
      configCollapsedBarAnimation = collapsedConfigBar.animate([
        { opacity: 1, transform: 'translateY(0px)' },
        { opacity: 0, transform: 'translateY(0px)' },
      ], timing);
      configCollapsedBarAnimation.onfinish = () => {
        const completedAnimation = configCollapsedBarAnimation;
        configCollapsedBarAnimation = null;
        releaseMorphAnimation(completedAnimation);
      };
      configCollapsedBarAnimation.oncancel = () => {
        configCollapsedBarAnimation = null;
      };
      return;
    }

    collapsedConfigBar.style.transform = 'translateY(0px)';
    collapsedConfigBar.style.zIndex = '7';
    configCollapsedBarAnimation = collapsedConfigBar.animate([
      { opacity: 0, transform: 'translateY(0px)' },
      { opacity: 1, transform: 'translateY(0px)' },
    ], timing);
    configCollapsedBarAnimation.onfinish = () => {
      const completedAnimation = configCollapsedBarAnimation;
      configCollapsedBarAnimation = null;
      releaseMorphAnimation(completedAnimation);
    };
    configCollapsedBarAnimation.oncancel = () => {
      configCollapsedBarAnimation = null;
    };
  };

  const runConfigPanelMorph = (collapsed: boolean): boolean => {
    if (!(configCard instanceof HTMLElement)
      || !(collapsedConfigBar instanceof HTMLButtonElement)
      || !(sideArea instanceof HTMLElement)
      || !(configCardTitle instanceof HTMLElement)) {
      return false;
    }

    const collapsedBarRect = collapsedConfigBar.getBoundingClientRect();
    const sideRect = sideArea.getBoundingClientRect();
    const configTitleRect = configCardTitle.getBoundingClientRect();
    if (collapsedBarRect.width < 1 || collapsedBarRect.height < 1 || sideRect.width < 1 || sideRect.height < 1 || configTitleRect.width < 1 || configTitleRect.height < 1) {
      return false;
    }

    cancelConfigPanelMorphAnimations();
    const animationTiming: KeyframeAnimationOptions = {
      duration: 260,
      easing: 'cubic-bezier(0.2, 0.8, 0.2, 1)',
      fill: 'both',
    };

    if (!collapsed) {
      configState.ui.configCollapsed = false;
      applyConfigPanelChromeState();
      configCard.dataset.pgConfigMorphing = 'true';
      configCard.dataset.pgConfigMorphDirection = 'expanding';
      collapsedConfigBar.dataset.pgConfigMorphing = 'true';
      collapsedConfigBar.dataset.pgConfigMorphDirection = 'expanding';
      prepareConfigCardContentForMorph('expand');
      configCard.style.opacity = '0';
      configCard.style.pointerEvents = 'none';
      setConfigCardFloatingBounds(collapsedBarRect);

      configCardMorphAnimation = configCard.animate(buildPanelBoundsKeyframes(collapsedBarRect, sideRect), animationTiming);
      runConfigTitleFade(false, collapsedBarRect, configTitleRect, animationTiming);
      configCardMorphAnimation.onfinish = () => {
        const completedAnimation = configCardMorphAnimation;
        configCardMorphAnimation = null;
        clearConfigPanelMorphState();
        persistConfigState();
        releaseMorphAnimation(completedAnimation);
      };
      configCardMorphAnimation.oncancel = () => {
        configCardMorphAnimation = null;
        clearConfigPanelMorphState();
      };
      return true;
    }

    configCard.dataset.pgConfigMorphing = 'true';
    configCard.dataset.pgConfigMorphDirection = 'collapsing';
    collapsedConfigBar.dataset.pgConfigMorphing = 'true';
    collapsedConfigBar.dataset.pgConfigMorphDirection = 'collapsing';
    prepareConfigCardContentForMorph('collapse');
    configCard.style.opacity = '0';
    configCard.style.pointerEvents = 'none';
    setConfigCardFloatingBounds(sideRect);
    if (detailCard instanceof HTMLElement) {
      detailCard.dataset.pgConfigMorphing = 'true';
      detailCardMorphAnimation = detailCard.animate([
        { opacity: 0.18, filter: 'blur(1.2px)', transform: 'translateX(10px) scale(0.985)' },
        { opacity: 1, filter: 'blur(0px)', transform: 'translateX(0px) scale(1)' },
      ], animationTiming);
      detailCardMorphAnimation.onfinish = () => {
        const completedAnimation = detailCardMorphAnimation;
        detailCardMorphAnimation = null;
        releaseMorphAnimation(completedAnimation);
      };
      detailCardMorphAnimation.oncancel = () => {
        detailCardMorphAnimation = null;
      };
    }

    configCardMorphAnimation = configCard.animate(buildPanelBoundsKeyframes(sideRect, collapsedBarRect), animationTiming);
    runConfigTitleFade(true, configTitleRect, collapsedBarRect, animationTiming);
    configCardMorphAnimation.onfinish = () => {
      const completedAnimation = configCardMorphAnimation;
      configCardMorphAnimation = null;
      configState.ui.configCollapsed = true;
      applyConfigPanelChromeState();
      clearConfigPanelMorphState();
      persistConfigState();
      releaseMorphAnimation(completedAnimation);
    };
    configCardMorphAnimation.oncancel = () => {
      configCardMorphAnimation = null;
      clearConfigPanelMorphState();
    };
    return true;
  };

  const applyConfigPanelChromeState = (): void => {
    const collapsed = configState.ui.configCollapsed;
    if (configCard instanceof HTMLElement) {
      configCard.dataset.pgConfigCollapsed = collapsed ? 'true' : 'false';
      configCard.setAttribute('aria-hidden', collapsed ? 'true' : 'false');
      configCard.toggleAttribute('inert', collapsed);
    }
    if (collapsedConfigBar instanceof HTMLButtonElement) {
      collapsedConfigBar.dataset.pgConfigCollapsed = collapsed ? 'true' : 'false';
      collapsedConfigBar.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
    }
    if (configToggleButton instanceof HTMLButtonElement) {
      configToggleButton.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
      configToggleButton.textContent = collapsed ? 'Expand' : 'Collapse';
    }
    if (inlineMetrics instanceof HTMLElement) {
      inlineMetrics.dataset.pgConfigCollapsed = collapsed ? 'true' : 'false';
    }
    if (sideMetrics instanceof HTMLElement) {
      sideMetrics.dataset.pgConfigCollapsed = collapsed ? 'true' : 'false';
    }
    if (sideArea instanceof HTMLElement) {
      sideArea.dataset.pgConfigCollapsed = collapsed ? 'true' : 'false';
    }
    if (detailCard instanceof HTMLElement) {
      detailCard.dataset.pgConfigCollapsed = collapsed ? 'true' : 'false';
    }
  };

  const setConfigPanelCollapsed = (collapsed: boolean): void => {
    if (configState.ui.configCollapsed === collapsed) {
      return;
    }

    if (runConfigPanelMorph(collapsed)) {
      return;
    }

    configState.ui.configCollapsed = collapsed;
    applyConfigPanelChromeState();
    persistConfigState();
  };

  const setInlineMetricsCollapsed = (collapsed: boolean): void => {
    if (metricsCollapsed === collapsed) {
      return;
    }
    metricsCollapsed = collapsed;
    applyInlineMetricsState();
  };

  const stopSidePanelResize = (): void => {
    if (!resizingSidePanel) {
      return;
    }
    resizingSidePanel = false;
    if (resizeHandle instanceof HTMLElement) {
      resizeHandle.dataset.pgDragging = 'false';
    }
    document.body.style.cursor = '';
    persistConfigState();
  };

  const handleSidePanelResize = (event: PointerEvent): void => {
    if (!resizingSidePanel || !(layoutRoot instanceof HTMLElement)) {
      return;
    }
    const layoutBounds = layoutRoot.getBoundingClientRect();
    const maxWidth = Math.min(620, Math.max(320, layoutBounds.width - 320));
    const nextWidth = clampNumber(layoutBounds.right - event.clientX, 280, maxWidth, configState.ui.sidePanelWidth);
    configState.ui.sidePanelWidth = nextWidth;
    applySplitLayoutState();
    syncGraphViewportToShell();
  };

  const scheduleFitView = (): void => {
    if (destroyed || fitViewFrameId !== null) {
      return;
    }

    fitViewFrameId = window.requestAnimationFrame(() => {
      fitViewFrameId = null;
      if (destroyed) {
        return;
      }
      if (fitViewSettledFrameId !== null) {
        window.cancelAnimationFrame(fitViewSettledFrameId);
      }
      fitViewSettledFrameId = window.requestAnimationFrame(() => {
        fitViewSettledFrameId = null;
        if (destroyed) {
          return;
        }
        void resetViewport();
      });
    });
  };

  const syncGraphViewportToShell = (): void => {
    const nextWidth = canvasShell.clientWidth;
    const nextHeight = canvasShell.clientHeight;
    if (Math.abs(nextWidth - observedWidth) < 2 && Math.abs(nextHeight - observedHeight) < 2) {
      return;
    }
    observedWidth = nextWidth;
    observedHeight = nextHeight;
    graph.resize(nextWidth, nextHeight);
    if (!getActiveNodeId(interactionState)) {
      scheduleFitView();
    }
  };

  const isHoverSuppressed = (): boolean => {
    return Boolean(draggingNodeId) || Date.now() < hoverSuppressedUntil;
  };

  const clearHover = (): void => {
    if (isHoverSuppressed()) {
      return;
    }
    if (!interactionState.hoveredNode) {
      return;
    }
    interactionState.hoveredNode = null;
    if (interactionState.selectedNode) {
      renderCurrentDetail();
      return;
    }
    renderCurrentDetail();
    void applyInteractionState();
  };

  const clearActiveNode = (): void => {
    if (!interactionState.selectedNode && !interactionState.hoveredNode) {
      return;
    }

    interactionState.selectedNode = null;
    interactionState.hoveredNode = null;
    renderCurrentDetail();
    void applyInteractionState();
  };

  const applyInteractionState = async (): Promise<void> => {
    if (destroyed) {
      return;
    }

    const activeNodeId = getActiveNodeId(interactionState);
    const states: Record<string, string[]> = {};

    if (!activeNodeId) {
      for (const node of payload.nodes) {
        states[node.id] = [];
      }
      for (const edge of payload.edges) {
        states[edge.id] = [];
      }
      await graph.setElementState(states, false);
      return;
    }

    const highlightedNodeIds = buildHighlightedNodeIds(interactionState, neighborsByNode);
    const highlightedEdgeIds = buildHighlightedEdgeIds(interactionState, connectedEdgesByNode);

    for (const node of payload.nodes) {
      if (node.id === activeNodeId) {
        states[node.id] = [interactionState.selectedNode ? 'pg-selected' : 'pg-hover'];
      } else if (highlightedNodeIds.has(node.id)) {
        states[node.id] = ['pg-related'];
      } else {
        states[node.id] = ['pg-dimmed'];
      }
    }

    for (const edge of payload.edges) {
      states[edge.id] = highlightedEdgeIds.has(edge.id) ? ['pg-related'] : ['pg-dimmed'];
    }

    await graph.setElementState(states, false);
  };

  const applyVisualState = async (): Promise<void> => {
    if (destroyed) {
      return;
    }

    graph.updateData(buildGraphUpdates(
      payload,
      configState,
      interactionState,
      degrees,
      neighborsByNode,
      connectedEdgesByNode,
    ));
    if (layoutRefreshPending) {
      layoutRefreshPending = false;
      // Re-run force layout in-place, but only through the single-flight
      // scheduler above. Keep the long-tail force animation non-blocking so
      // new slider input can immediately stop/restart the current evolution.
      graph.stopLayout();
      const layoutRunId = activeForceLayoutRunId + 1;
      activeForceLayoutRunId = layoutRunId;
      void graph.layout(buildLayoutConfig(canvasShell, configState, payload)).then(() => {
        if (destroyed || layoutRunId !== activeForceLayoutRunId) {
          return;
        }
        if (getActiveNodeId(interactionState)) {
          void applyInteractionState();
        }
      }).catch(() => {
        // A stopped force layout can leave the previous promise unresolved in
        // G6; this catch only prevents unexpected rejected layouts from leaking.
      });
    } else {
      await graph.draw();
    }

    if (getActiveNodeId(interactionState)) {
      await applyInteractionState();
    }
  };

  graph.on('node:pointerenter', (event: { target?: { id?: string }; originalTarget?: GraphEventTargetShape }) => {
    if (isHoverSuppressed()) {
      return;
    }
    const nodeId = getEventTargetId(event, { keyShapeOnly: true });
    if (!nodeId) {
      return;
    }
    if (interactionState.selectedNode) {
      return;
    }
    interactionState.hoveredNode = nodeId;
    renderCurrentDetail();
    void applyInteractionState();
  });

  graph.on('node:pointerleave', (event: { target?: { id?: string }; originalTarget?: GraphEventTargetShape }) => {
    if (isHoverSuppressed()) {
      return;
    }
    const nodeId = getEventTargetId(event, { keyShapeOnly: true });
    if (!nodeId || interactionState.hoveredNode !== nodeId) {
      return;
    }
    clearHover();
  });

  graph.on('node:pointerout', (event: { target?: { id?: string }; originalTarget?: GraphEventTargetShape }) => {
    if (isHoverSuppressed()) {
      return;
    }
    const nodeId = getEventTargetId(event, { keyShapeOnly: true });
    if (!nodeId || interactionState.hoveredNode !== nodeId) {
      return;
    }
    clearHover();
  });

  graph.on('node:dragstart', (event: { target?: { id?: string }; originalTarget?: GraphEventTargetShape }) => {
    const nodeId = getEventTargetId(event);
    draggingNodeId = nodeId;
    hoverSuppressedUntil = Date.now() + 120;
    suppressNextNodeClick = Boolean(nodeId);
    if (hoverResumeTimer !== null) {
      window.clearTimeout(hoverResumeTimer);
      hoverResumeTimer = null;
    }
    if (suppressNodeClickTimer !== null) {
      window.clearTimeout(suppressNodeClickTimer);
      suppressNodeClickTimer = null;
    }
    if (!nodeId || interactionState.selectedNode) {
      return;
    }
    interactionState.hoveredNode = nodeId;
    renderCurrentDetail();
    void applyInteractionState();
  });

  graph.on('node:dragend', () => {
    draggingNodeId = null;
    hoverSuppressedUntil = Date.now() + 120;
    hoverResumeTimer = window.setTimeout(() => {
      hoverResumeTimer = null;
      if (!destroyed && !interactionState.selectedNode) {
        void applyInteractionState();
      }
    }, 120);
    suppressNodeClickTimer = window.setTimeout(() => {
      suppressNextNodeClick = false;
      suppressNodeClickTimer = null;
    }, 80);
  });

  graph.on('node:click', (event: { target?: { id?: string }; originalTarget?: GraphEventTargetShape }) => {
    if (suppressNextNodeClick) {
      suppressNextNodeClick = false;
      return;
    }
    const nodeId = getEventTargetId(event, { keyShapeOnly: true });
    if (!nodeId) {
      return;
    }

    interactionState.selectedNode = interactionState.selectedNode === nodeId ? null : nodeId;
    interactionState.hoveredNode = interactionState.selectedNode ? nodeId : null;
    renderCurrentDetail();
    void applyInteractionState();
  });

  graph.on('canvas:click', () => {
    clearActiveNode();
  });

  graph.on('canvas:pointermove', () => {
    if (isHoverSuppressed() || interactionState.selectedNode) {
      return;
    }
    clearHover();
  });

  graph.on('canvas:pointerleave', () => {
    if (isHoverSuppressed() || interactionState.selectedNode) {
      return;
    }
    clearHover();
  });

  initializeConfigPanel(configState, {
    onAppearanceChange: (rerunLayout) => {
      persistConfigState();
      scheduleVisualRefresh({ rerunLayout });
    },
    onForceChange: () => {
      persistConfigState();
      scheduleForceLayoutRefresh();
    },
    onColorGroupChange: () => {
      persistConfigState();
      scheduleVisualRefresh();
    },
  });

  applySplitLayoutState();
  applyConfigPanelChromeState();
  applyInlineMetricsState();
  if (configToggleButton instanceof HTMLButtonElement) {
    configToggleButton.onclick = () => {
      setConfigPanelCollapsed(!configState.ui.configCollapsed);
    };
  }
  if (collapsedConfigBar instanceof HTMLButtonElement) {
    collapsedConfigBar.onclick = () => {
      setConfigPanelCollapsed(false);
    };
  }
  if (metricsDock instanceof HTMLElement) {
    metricsDock.addEventListener('pointerenter', () => {
      setInlineMetricsCollapsed(false);
    });
    metricsDock.addEventListener('pointerleave', () => {
      setInlineMetricsCollapsed(true);
    });
  }
  if (clearSelectionButton instanceof HTMLButtonElement) {
    clearSelectionButton.addEventListener('click', () => {
      clearActiveNode();
    });
  }
  if (resizeHandle instanceof HTMLElement) {
    resizeHandle.addEventListener('pointerdown', (event) => {
      resizingSidePanel = true;
      resizeHandle.dataset.pgDragging = 'true';
      document.body.style.cursor = 'col-resize';
      resizeHandle.setPointerCapture?.(event.pointerId);
      event.preventDefault();
    });
  }
  window.addEventListener('pointermove', handleSidePanelResize);
  window.addEventListener('pointerup', stopSidePanelResize);
  window.addEventListener('pointercancel', stopSidePanelResize);

  const resetViewportButton = document.getElementById('pgHostV2ResetViewport');
  if (resetViewportButton instanceof HTMLButtonElement) {
    resetViewportButton.onclick = () => {
      void resetViewport();
    };
  }

  renderCurrentDetail();
  await graph.render();
  await resetViewport();
  await applyInteractionState();

  const handleWindowResize = (): void => {
    if (destroyed) {
      return;
    }
    syncGraphViewportToShell();
  };
  window.addEventListener('resize', handleWindowResize);
  if (typeof ResizeObserver === 'function') {
    canvasResizeObserver = new ResizeObserver(() => {
      syncGraphViewportToShell();
    });
    canvasResizeObserver.observe(canvasShell);
  }

  const cleanup = () => {
    if (destroyed) {
      return;
    }
    destroyed = true;
    window.removeEventListener('resize', handleWindowResize);
    window.removeEventListener('pointermove', handleSidePanelResize);
    window.removeEventListener('pointerup', stopSidePanelResize);
    window.removeEventListener('pointercancel', stopSidePanelResize);
    if (fitViewFrameId !== null) {
      window.cancelAnimationFrame(fitViewFrameId);
      fitViewFrameId = null;
    }
    if (fitViewSettledFrameId !== null) {
      window.cancelAnimationFrame(fitViewSettledFrameId);
      fitViewSettledFrameId = null;
    }
    canvasResizeObserver?.disconnect();
    canvasResizeObserver = null;
    activeForceLayoutRunId += 1;
    graph.stopLayout();
    if (hoverResumeTimer !== null) {
      window.clearTimeout(hoverResumeTimer);
      hoverResumeTimer = null;
    }
    if (suppressNodeClickTimer !== null) {
      window.clearTimeout(suppressNodeClickTimer);
      suppressNodeClickTimer = null;
    }
    cancelConfigPanelMorphAnimations();
    graph.destroy();
    if (window.__pgHostV2GraphCleanup === cleanup) {
      window.__pgHostV2GraphCleanup = undefined;
    }
  };

  window.__pgHostV2GraphCleanup = cleanup;

  window.addEventListener('beforeunload', cleanup, { once: true });
}

function buildGraphData(
  payload: ProgressGraphPreviewV2PoCPayload,
  configState: V2GraphConfigState,
  interactionState: GraphInteractionState,
  degrees: Map<string, number>,
  neighborsByNode: Map<string, string[]>,
  connectedEdgesByNode: Map<string, string[]>,
): { nodes: Array<Record<string, unknown>>; edges: Array<Record<string, unknown>> } {
  const labelIds = computeVisibleLabelIds(payload, configState.appearance, interactionState, degrees, neighborsByNode);
  const highlightedNodeIds = buildHighlightedNodeIds(interactionState, neighborsByNode);
  const highlightedEdgeIds = buildHighlightedEdgeIds(interactionState, connectedEdgesByNode);
  const resolvedNodeColors = buildNodeColorMap(payload.nodes, configState.colorGroups);

  return {
    nodes: payload.nodes.map((node, index) => ({
      id: node.id,
      data: { ...node, visualColor: resolvedNodeColors.get(node.id) ?? defaultNodeColor(node) },
      style: buildNodeStyle(node, resolvedNodeColors.get(node.id) ?? defaultNodeColor(node), configState.appearance, labelIds, highlightedNodeIds, interactionState, index, payload.nodes.length, undefined),
    })),
    edges: payload.edges.map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      data: edge,
      style: buildEdgeStyle(edge, configState.appearance, highlightedEdgeIds, interactionState),
    })),
  };
}

function buildGraphUpdates(
  payload: ProgressGraphPreviewV2PoCPayload,
  configState: V2GraphConfigState,
  interactionState: GraphInteractionState,
  degrees: Map<string, number>,
  neighborsByNode: Map<string, string[]>,
  connectedEdgesByNode: Map<string, string[]>,
): { nodes: Array<Record<string, unknown>>; edges: Array<Record<string, unknown>> } {
  const labelIds = computeVisibleLabelIds(payload, configState.appearance, interactionState, degrees, neighborsByNode);
  const highlightedNodeIds = buildHighlightedNodeIds(interactionState, neighborsByNode);
  const highlightedEdgeIds = buildHighlightedEdgeIds(interactionState, connectedEdgesByNode);
  const resolvedNodeColors = buildNodeColorMap(payload.nodes, configState.colorGroups);

  return {
    nodes: payload.nodes.map((node, index) => {
      // Do not include x/y: the force simulation owns positions.
      // Writing back stale model coordinates would cause visible jumps.
      const { x: _x, y: _y, ...styleUpdate } = buildNodeStyle(
        node,
        resolvedNodeColors.get(node.id) ?? defaultNodeColor(node),
        configState.appearance,
        labelIds,
        highlightedNodeIds,
        interactionState,
        index,
        payload.nodes.length,
        undefined,
      );
      void _x; void _y;
      return {
        id: node.id,
        data: { ...node, visualColor: resolvedNodeColors.get(node.id) ?? defaultNodeColor(node) },
        style: styleUpdate,
      };
    }),
    edges: payload.edges.map((edge) => ({
      id: edge.id,
      style: buildEdgeStyle(edge, configState.appearance, highlightedEdgeIds, interactionState),
    })),
  };
}

function buildNodeStyle(
  node: ProgressGraphPreviewV2PoCNode,
  resolvedColor: string,
  appearance: V2GraphAppearanceSettings,
  labelIds: Set<string>,
  highlightedNodeIds: Set<string>,
  interactionState: GraphInteractionState,
  index: number,
  nodeCount: number,
  currentPosition?: NodePosition,
): Record<string, unknown> {
  const color = statusColors[node.status] ?? '#6f8192';
  const baseSize = computeBaseNodeSize(node);
  const size = Math.round(baseSize * appearance.nodeScale);
  const labelVisible = labelIds.has(node.id);
  const seed = currentPosition ?? computeSeedPosition(index, Math.max(1, nodeCount));
  const stableLineWidth = node.hasRuntimeBinding ? 1.8 : 1.3;

  return {
    x: seed.x,
    y: seed.y,
    size,
    fill: hexToRgba(resolvedColor, node.hasRuntimeBinding ? 0.54 : 0.38),
    stroke: resolvedColor,
    strokeOpacity: 0.9,
    lineWidth: stableLineWidth,
    label: labelVisible,
    labelText: labelVisible ? node.label : '',
    labelFill: 'rgba(24, 34, 43, 0.94)',
    labelFontSize: appearance.labelSize,
    labelPlacement: 'bottom',
    labelOffsetY: 10,
    labelOpacity: 0.86,
    cursor: 'pointer',
    shadowBlur: 0,
    shadowColor: 'transparent',
  };
}

function buildEdgeStyle(
  edge: ProgressGraphPreviewV2PoCEdge,
  appearance: V2GraphAppearanceSettings,
  highlightedEdgeIds: Set<string>,
  interactionState: GraphInteractionState,
): Record<string, unknown> {
  const color = edgeColors[edge.kind] ?? '#7b8491';
  const lineWidth = 1.05 * appearance.edgeScale;

  return {
    stroke: hexToRgba(color, 0.28),
    lineWidth,
    endArrow: edge.directed,
    endArrowOpacity: 0.32,
    cursor: 'pointer',
  };
}

function buildLayoutConfig(
  container: HTMLElement,
  configState: V2GraphConfigState,
  payload: ProgressGraphPreviewV2PoCPayload,
): Record<string, unknown> {
  const width = Math.max(container.clientWidth, 720);
  const height = Math.max(container.clientHeight, 520);
  const nodeCount = payload.nodes.length;
  const collisionSize = Math.max(22, Math.round(28 * configState.appearance.nodeScale));
  const largeGraphFactor = Math.min(1, Math.max(0, (Math.max(1, nodeCount) - 48) / 120));
  const nodeSpacing = Math.max(6, Math.round(collisionSize * (0.24 + largeGraphFactor * 0.1)));
  const gravity = configState.forces.gravity * (1 - largeGraphFactor * 0.38);
  const nodeStrength = configState.forces.repulsion * (1 + largeGraphFactor * 0.08);
  const edgeStrength = configState.forces.attraction * (1 - largeGraphFactor * 0.16);
  const linkDistance = configState.forces.linkLength * (1 + largeGraphFactor * 0.22);
  const maxIteration = Math.round(1200 - largeGraphFactor * 420);
  const maxSpeed = Math.round(72 - largeGraphFactor * 34);
  const minMovement = 0;
  const motionController = createGraphMotionController({
    edges: payload.edges.map((edge) => ({ source: edge.source, target: edge.target })),
    largeGraphFactor,
    nodeCount,
    nodeSpacing,
  });

  return {
    type: 'force',
    animation: true,
    iterations: maxIteration,
    width,
    height,
    preventOverlap: true,
    nodeSize: collisionSize,
    nodeSpacing,
    gravity,
    nodeStrength,
    edgeStrength,
    linkDistance,
    damping: 0.91,
    maxIteration,
    minMovement,
    maxSpeed,
    interval: 0.034,
    distanceThresholdMode: 'max',
    collideStrength: 0.82,
    monitor: (params: G6ForceMonitorParams): void => {
      motionController.onTick({
        energy: params.energy,
        iteration: params.iterations,
        nodes: params.nodes ?? [],
      });
    },
  };
}

function initializeConfigPanel(
  configState: V2GraphConfigState,
  handlers: {
    onAppearanceChange: (rerunLayout: boolean) => void;
    onForceChange: () => void;
    onColorGroupChange: () => void;
  },
): void {
  bindRangeControl('pgHostV2AppearanceLabelDensity', 'pgHostV2AppearanceLabelDensityValue', {
    value: configState.appearance.labelDensity,
    formatValue: (value) => `${Math.round(value * 100)}%`,
    onInput: (value) => {
      configState.appearance.labelDensity = value;
        handlers.onAppearanceChange(true);
    },
  });

  bindRangeControl('pgHostV2AppearanceLabelSize', 'pgHostV2AppearanceLabelSizeValue', {
    value: configState.appearance.labelSize,
    formatValue: (value) => `${Math.round(value)}px`,
    onInput: (value) => {
      configState.appearance.labelSize = value;
        handlers.onAppearanceChange(true);
    },
  });

  bindRangeControl('pgHostV2AppearanceNodeScale', 'pgHostV2AppearanceNodeScaleValue', {
    value: configState.appearance.nodeScale,
    formatValue: (value) => `${value.toFixed(2)}x`,
    onInput: (value) => {
      configState.appearance.nodeScale = value;
        handlers.onAppearanceChange(true);
    },
  });

  bindRangeControl('pgHostV2AppearanceEdgeScale', 'pgHostV2AppearanceEdgeScaleValue', {
    value: configState.appearance.edgeScale,
    formatValue: (value) => `${value.toFixed(2)}x`,
    onInput: (value) => {
      configState.appearance.edgeScale = value;
        handlers.onAppearanceChange(true);
    },
  });

  bindRangeControl('pgHostV2ForceGravity', 'pgHostV2ForceGravityValue', {
    value: configState.forces.gravity,
    formatValue: (value) => `${Math.round(value)}`,
    onInput: (value) => {
      configState.forces.gravity = value;
      handlers.onForceChange();
    },
  });

  bindRangeControl('pgHostV2ForceRepulsion', 'pgHostV2ForceRepulsionValue', {
    value: configState.forces.repulsion,
    formatValue: (value) => `${Math.round(value)}`,
    onInput: (value) => {
      configState.forces.repulsion = value;
      handlers.onForceChange();
    },
  });

  bindRangeControl('pgHostV2ForceAttraction', 'pgHostV2ForceAttractionValue', {
    value: configState.forces.attraction,
    formatValue: (value) => `${Math.round(value)}`,
    onInput: (value) => {
      configState.forces.attraction = value;
      handlers.onForceChange();
    },
  });

  bindRangeControl('pgHostV2ForceLinkLength', 'pgHostV2ForceLinkLengthValue', {
    value: configState.forces.linkLength,
    formatValue: (value) => `${Math.round(value)}px`,
    onInput: (value) => {
      configState.forces.linkLength = value;
      handlers.onForceChange();
    },
  });

  bindColorGroupControls(configState.colorGroups, handlers.onColorGroupChange);
}

function bindRangeControl(
  inputId: string,
  outputId: string,
  options: {
    value: number;
    formatValue: (value: number) => string;
    onInput: (value: number) => void;
    onChange?: (value: number) => void;
  },
): void {
  const input = document.getElementById(inputId);
  const output = document.getElementById(outputId);
  if (!(input instanceof HTMLInputElement) || !(output instanceof HTMLOutputElement)) {
    return;
  }

  const sync = (value: number) => {
    output.value = options.formatValue(value);
    output.textContent = options.formatValue(value);
  };

  input.value = String(options.value);
  sync(options.value);
  input.addEventListener('input', () => {
    const value = Number.parseFloat(input.value);
    if (!Number.isFinite(value)) {
      return;
    }
    sync(value);
    options.onInput(value);
  });

  input.addEventListener('change', () => {
    if (!options.onChange) {
      return;
    }
    const value = Number.parseFloat(input.value);
    if (!Number.isFinite(value)) {
      return;
    }
    options.onChange(value);
  });
}

function bindColorGroupControls(
  colorGroups: V2GraphColorGroup[],
  onChange: () => void,
): void {
  const list = document.getElementById('pgHostV2ColorGroups');
  const addButton = document.getElementById('pgHostV2AddColorGroup');
  if (!(list instanceof HTMLElement) || !(addButton instanceof HTMLButtonElement)) {
    return;
  }

  const render = (): void => {
    renderColorGroupRows(list, colorGroups, render, onChange);
  };

  addButton.addEventListener('click', () => {
    colorGroups.push(createColorGroup('', pickColorGroupPaletteColor(colorGroups.length)));
    render();
    onChange();
  });

  render();
}

function renderColorGroupRows(
  list: HTMLElement,
  colorGroups: V2GraphColorGroup[],
  rerender: () => void,
  onChange: () => void,
): void {
  list.replaceChildren();

  for (const colorGroup of colorGroups) {
    const row = document.createElement('div');
    row.className = 'pg-host-v2-color-group-row';

    const queryInput = document.createElement('input');
    queryInput.className = 'pg-host-v2-color-group-input';
    queryInput.type = 'text';
    queryInput.value = colorGroup.query;
    queryInput.placeholder = 'tag:active / status:blocked / path:"design_docs"';
    queryInput.addEventListener('input', () => {
      colorGroup.query = queryInput.value;
      onChange();
    });

    const colorInput = document.createElement('input');
    colorInput.className = 'pg-host-v2-color-group-swatch';
    colorInput.type = 'color';
    colorInput.value = normalizeColorGroupHex(colorGroup.color, pickColorGroupPaletteColor(0));
    colorInput.addEventListener('input', () => {
      colorGroup.color = colorInput.value;
      onChange();
    });

    const actions = document.createElement('div');
    actions.className = 'pg-host-v2-color-group-actions';

    const moveUpButton = document.createElement('button');
    moveUpButton.className = 'pg-host-v2-color-group-action';
    moveUpButton.type = 'button';
    moveUpButton.textContent = '↑';
    moveUpButton.title = '上移颜色组';
    moveUpButton.disabled = colorGroups[0]?.id === colorGroup.id;
    moveUpButton.addEventListener('click', () => {
      moveColorGroup(colorGroups, colorGroup.id, -1);
      rerender();
      onChange();
    });

    const moveDownButton = document.createElement('button');
    moveDownButton.className = 'pg-host-v2-color-group-action';
    moveDownButton.type = 'button';
    moveDownButton.textContent = '↓';
    moveDownButton.title = '下移颜色组';
    moveDownButton.disabled = colorGroups.at(-1)?.id === colorGroup.id;
    moveDownButton.addEventListener('click', () => {
      moveColorGroup(colorGroups, colorGroup.id, 1);
      rerender();
      onChange();
    });

    const removeButton = document.createElement('button');
    removeButton.className = 'pg-host-v2-color-group-action pg-host-v2-color-group-remove';
    removeButton.type = 'button';
    removeButton.textContent = '×';
    removeButton.title = '删除颜色组';
    removeButton.addEventListener('click', () => {
      const index = colorGroups.findIndex((entry) => entry.id === colorGroup.id);
      if (index === -1) {
        return;
      }
      colorGroups.splice(index, 1);
      rerender();
      onChange();
    });

    actions.append(moveUpButton, moveDownButton, removeButton);
    row.append(queryInput, colorInput, actions);
    list.appendChild(row);
  }
}

function moveColorGroup(colorGroups: V2GraphColorGroup[], id: string, delta: number): void {
  const index = colorGroups.findIndex((entry) => entry.id === id);
  if (index === -1) {
    return;
  }

  const nextIndex = index + delta;
  if (nextIndex < 0 || nextIndex >= colorGroups.length) {
    return;
  }

  [colorGroups[index], colorGroups[nextIndex]] = [colorGroups[nextIndex], colorGroups[index]];
}

function createColorGroup(query: string, color: string): V2GraphColorGroup {
  return {
    id: `color-group-${Date.now()}-${Math.random().toString(16).slice(2, 7)}`,
    query,
    color,
  };
}

function buildNodeColorMap(
  nodes: ProgressGraphPreviewV2PoCNode[],
  colorGroups: V2GraphColorGroup[],
): Map<string, string> {
  const compiledGroups = colorGroups
    .filter((colorGroup) => colorGroup.query.trim().length > 0)
    .map((colorGroup) => ({
      ...colorGroup,
      compiledQuery: compileColorGroupQuery(colorGroup.query),
    }));

  return new Map(nodes.map((node) => [node.id, resolveColorGroupNodeColor(node, compiledGroups)]));
}

function resolveColorGroupNodeColor(
  node: ProgressGraphPreviewV2PoCNode,
  colorGroups: CompiledColorGroup[],
): string {
  const context: ColorQueryContext = { nodeId: node.id, node };
  for (const colorGroup of colorGroups) {
    if (evaluateColorGroupQuery(colorGroup.compiledQuery, context)) {
      return colorGroup.color;
    }
  }
  return defaultNodeColor(node);
}

function computeVisibleLabelIds(
  payload: ProgressGraphPreviewV2PoCPayload,
  appearance: V2GraphAppearanceSettings,
  interactionState: GraphInteractionState,
  degrees: Map<string, number>,
  neighborsByNode: Map<string, string[]>,
): Set<string> {
  const rankedNodes = [...payload.nodes]
    .map((node) => ({
      id: node.id,
      score: (degrees.get(node.id) ?? 0) * 3
        + (node.hasRuntimeBinding ? 4 : 0)
        + node.workItemIds.length
        + node.groupItemIds.length
        + node.tags.length * 0.4,
    }))
    .sort((left, right) => right.score - left.score || left.id.localeCompare(right.id));
  const minimum = Math.min(payload.nodes.length, Math.max(6, Math.ceil(Math.sqrt(payload.nodes.length))));
  const visibleCount = Math.min(
    payload.nodes.length,
    Math.max(minimum, Math.round(payload.nodes.length * appearance.labelDensity)),
  );
  const visible = new Set(rankedNodes.slice(0, visibleCount).map((entry) => entry.id));
  const activeNodeId = getActiveNodeId(interactionState);
  if (activeNodeId) {
    visible.add(activeNodeId);
    for (const neighborId of neighborsByNode.get(activeNodeId) ?? []) {
      visible.add(neighborId);
    }
  }
  return visible;
}

function buildDegrees(payload: ProgressGraphPreviewV2PoCPayload): Map<string, number> {
  const degrees = new Map<string, number>();
  for (const node of payload.nodes) {
    degrees.set(node.id, 0);
  }
  for (const edge of payload.edges) {
    degrees.set(edge.source, (degrees.get(edge.source) ?? 0) + 1);
    degrees.set(edge.target, (degrees.get(edge.target) ?? 0) + 1);
  }
  return degrees;
}

function buildNeighborsIndex(edges: ProgressGraphPreviewV2PoCEdge[]): Map<string, string[]> {
  const map = new Map<string, Set<string>>();
  for (const edge of edges) {
    if (!map.has(edge.source)) {
      map.set(edge.source, new Set());
    }
    if (!map.has(edge.target)) {
      map.set(edge.target, new Set());
    }
    map.get(edge.source)?.add(edge.target);
    map.get(edge.target)?.add(edge.source);
  }
  return new Map(Array.from(map.entries(), ([nodeId, values]) => [nodeId, [...values]]));
}

function buildConnectedEdgesIndex(edges: ProgressGraphPreviewV2PoCEdge[]): Map<string, string[]> {
  const map = new Map<string, string[]>();
  for (const edge of edges) {
    const source = map.get(edge.source) ?? [];
    source.push(edge.id);
    map.set(edge.source, source);
    const target = map.get(edge.target) ?? [];
    target.push(edge.id);
    map.set(edge.target, target);
  }
  return map;
}

function buildHighlightedNodeIds(
  interactionState: GraphInteractionState,
  neighborsByNode: Map<string, string[]>,
): Set<string> {
  const activeNodeId = getActiveNodeId(interactionState);
  if (!activeNodeId) {
    return new Set();
  }
  return new Set([activeNodeId, ...(neighborsByNode.get(activeNodeId) ?? [])]);
}

function buildHighlightedEdgeIds(
  interactionState: GraphInteractionState,
  connectedEdgesByNode: Map<string, string[]>,
): Set<string> {
  const activeNodeId = getActiveNodeId(interactionState);
  return new Set(activeNodeId ? connectedEdgesByNode.get(activeNodeId) ?? [] : []);
}

function getActiveNodeId(interactionState: GraphInteractionState): string | null {
  return interactionState.selectedNode ?? interactionState.hoveredNode;
}

function computeSeedPosition(index: number, count: number): NodePosition {
  const normalizedCount = Math.max(1, count);
  if (normalizedCount === 1) {
    return { x: 0, y: 0 };
  }

  const normalizedIndex = index + 0.5;
  const goldenAngle = Math.PI * (3 - Math.sqrt(5));
  const radialRatio = normalizedIndex / normalizedCount;
  const radius = (64 + Math.sqrt(normalizedCount) * 20) * Math.pow(radialRatio, 0.82);
  const angle = normalizedIndex * goldenAngle;
  const jitter = Math.min(18, 6 + Math.sqrt(normalizedCount) * 0.8) * (0.35 + radialRatio * 0.65);

  return {
    x: Math.cos(angle) * radius + Math.cos(index * 2.17) * jitter,
    y: Math.sin(angle) * radius + Math.sin(index * 2.63) * jitter,
  };
}

function computeBaseNodeSize(node: ProgressGraphPreviewV2PoCNode): number {
  return 18
    + Math.min(node.workItemIds.length, 3) * 3
    + Math.min(node.groupItemIds.length, 3) * 2
    + (node.hasRuntimeBinding ? 4 : 0);
}

function renderEmpty(container: HTMLElement, detail: HTMLElement, message: string): void {
  container.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--vscode-descriptionForeground);font-size:0.92rem;">${escapeHtml(message)}</div>`;
  detail.innerHTML = `<p class="pg-host-v2-detail-empty">${escapeHtml(message)}</p>`;
}

function renderNodeDetail(
  detail: HTMLElement,
  node: ProgressGraphPreviewV2PoCNode | null,
  runtimeSummary: ProgressGraphPreviewV2PoCPayload['runtimeSummary'],
  selectedNodeId: string | null,
): void {
  if (!node) {
    detail.innerHTML = `<div class="pg-host-v2-detail-stack">
  <p class="pg-host-v2-detail-empty">悬停或点击节点后，这里会显示 kind、status、summary 与 runtime binding 摘要。</p>
  <div class="pg-host-v2-detail-grid">
    <div><strong>Bound nodes</strong><br>${escapeHtml(String(runtimeSummary.boundNodeCount))}</div>
    <div><strong>Open work</strong><br>${escapeHtml(String(runtimeSummary.openWorkItemCount))}</div>
    <div><strong>Active groups</strong><br>${escapeHtml(String(runtimeSummary.activeGroupItemCount))}</div>
    <div><strong>Unbound groups</strong><br>${escapeHtml(String(runtimeSummary.unboundGroupItemCount))}</div>
  </div>
</div>`;
    return;
  }

  detail.innerHTML = `<div class="pg-host-v2-detail-stack">
  <p class="pg-host-v2-detail-kicker">${selectedNodeId === node.id ? 'Selected node' : 'Hovered node'}</p>
  <h4 class="pg-host-v2-detail-title">${escapeHtml(node.label)}</h4>
  <p class="pg-host-v2-detail-meta">kind=${escapeHtml(node.kind)} · status=${escapeHtml(node.status || 'unknown')}</p>
  <p class="pg-host-v2-detail-copy">${escapeHtml(node.summary || '当前节点没有 summary。')}</p>
  <div class="pg-host-v2-detail-grid">
    <div><strong>Runtime binding</strong><br>${node.hasRuntimeBinding ? 'Yes' : 'No'}</div>
    <div><strong>Work items</strong><br>${escapeHtml(String(node.workItemIds.length))}</div>
    <div><strong>Group items</strong><br>${escapeHtml(String(node.groupItemIds.length))}</div>
    <div><strong>Tags</strong><br>${escapeHtml(node.tags.length ? node.tags.join(', ') : 'none')}</div>
  </div>
</div>`;
}

function readPayload(): ProgressGraphPreviewV2PoCPayload | null {
  const payloadElement = document.getElementById('pgHostV2GraphPayload');
  if (!payloadElement?.textContent) {
    return null;
  }

  try {
    return JSON.parse(payloadElement.textContent) as ProgressGraphPreviewV2PoCPayload;
  } catch {
    return null;
  }
}

function loadGraphConfigState(): V2GraphConfigState {
  const vscode = window.__pgHostVsCodeApi;
  const raw = vscode?.getState() as {
    progressGraphV2G6Config?: Partial<V2GraphConfigState>;
    v2GraphConfig?: Partial<V2GraphConfigState>;
  } | undefined;
  const persisted = raw?.progressGraphV2G6Config;
  const legacy = raw?.v2GraphConfig;

  return {
    appearance: {
      labelDensity: clampNumber(persisted?.appearance?.labelDensity ?? legacy?.appearance?.labelDensity, 0.06, 0.3, defaultGraphConfigState.appearance.labelDensity),
      labelSize: clampNumber(persisted?.appearance?.labelSize ?? legacy?.appearance?.labelSize, 11, 20, defaultGraphConfigState.appearance.labelSize),
      nodeScale: clampNumber(persisted?.appearance?.nodeScale ?? legacy?.appearance?.nodeScale, 0.75, 1.6, defaultGraphConfigState.appearance.nodeScale),
      edgeScale: clampNumber(persisted?.appearance?.edgeScale ?? legacy?.appearance?.edgeScale, 0.5, 2.2, defaultGraphConfigState.appearance.edgeScale),
    },
    forces: {
      gravity: clampNumber(persisted?.forces?.gravity ?? legacy?.forces?.gravity, 1, 24, defaultGraphConfigState.forces.gravity),
      repulsion: clampNumber(persisted?.forces?.repulsion ?? legacy?.forces?.repulsion, 200, 3000, defaultGraphConfigState.forces.repulsion),
      attraction: clampNumber(persisted?.forces?.attraction ?? legacy?.forces?.attraction, 10, 140, defaultGraphConfigState.forces.attraction),
      linkLength: clampNumber(persisted?.forces?.linkLength ?? legacy?.forces?.linkLength, 80, 280, defaultGraphConfigState.forces.linkLength),
    },
    colorGroups: normalizeColorGroups(persisted?.colorGroups ?? legacy?.colorGroups),
    ui: {
      configCollapsed: Boolean(persisted?.ui?.configCollapsed ?? legacy?.ui?.configCollapsed ?? defaultGraphConfigState.ui.configCollapsed),
      sidePanelWidth: clampNumber(persisted?.ui?.sidePanelWidth ?? legacy?.ui?.sidePanelWidth, 280, 620, defaultGraphConfigState.ui.sidePanelWidth),
    },
  };
}

function persistGraphConfigState(configState: V2GraphConfigState): void {
  const vscode = window.__pgHostVsCodeApi;
  if (!vscode) {
    return;
  }

  const current = (vscode.getState() as Record<string, unknown> | undefined) ?? {};
  vscode.setState({
    ...current,
    progressGraphV2G6Config: configState,
    v2GraphConfig: configState,
  });
}

function normalizeColorGroups(value: unknown): V2GraphColorGroup[] {
  if (!Array.isArray(value) || value.length === 0) {
    return defaultGraphConfigState.colorGroups.map((colorGroup) => ({ ...colorGroup }));
  }

  const normalized = value.flatMap((entry, index) => {
    if (!isRecord(entry)) {
      return [];
    }
    return [{
      id: typeof entry.id === 'string' ? entry.id : `color-group-${index + 1}`,
      query: typeof entry.query === 'string' ? entry.query : '',
      color: normalizeColorGroupHex(entry.color, pickColorGroupPaletteColor(index)),
    }];
  });

  return normalized.length > 0
    ? normalized
    : defaultGraphConfigState.colorGroups.map((colorGroup) => ({ ...colorGroup }));
}

function compileColorGroupQuery(query: string): ColorQueryExpression {
  const trimmed = query.trim();
  if (!trimmed) {
    return { kind: 'term', term: { type: 'word', value: '' } };
  }

  try {
    return parseColorGroupTokens(tokenizeColorGroupQuery(trimmed));
  } catch {
    return { kind: 'term', term: { type: 'word', value: trimmed } };
  }
}

function tokenizeColorGroupQuery(query: string): ColorQueryToken[] {
  const tokens: ColorQueryToken[] = [];
  let index = 0;

  while (index < query.length) {
    const current = query[index];
    if (/\s/.test(current)) {
      index += 1;
      continue;
    }

    if (current === '(') {
      tokens.push({ type: 'lparen' });
      index += 1;
      continue;
    }

    if (current === ')') {
      tokens.push({ type: 'rparen' });
      index += 1;
      continue;
    }

    if (current === '-') {
      tokens.push({ type: 'negate' });
      index += 1;
      continue;
    }

    if (current === '"') {
      const phrase = readQuotedColorGroupToken(query, index);
      tokens.push({ type: 'phrase', value: phrase.value });
      index = phrase.nextIndex;
      continue;
    }

    if (current === '/') {
      const regex = readRegexColorGroupToken(query, index);
      if (regex) {
        tokens.push({ type: 'regex', pattern: regex.pattern, flags: regex.flags });
        index = regex.nextIndex;
        continue;
      }
    }

    if (current === '[') {
      const bracket = readBracketColorGroupToken(query, index);
      tokens.push({ type: 'bracket', value: bracket.value });
      index = bracket.nextIndex;
      continue;
    }

    const start = index;
    while (
      index < query.length
      && !/\s/.test(query[index])
      && query[index] !== '('
      && query[index] !== ')'
      && query[index] !== '"'
      && query[index] !== '['
    ) {
      index += 1;
    }

    const value = query.slice(start, index);
    tokens.push(/^OR$/i.test(value) ? { type: 'or' } : { type: 'word', value });
  }

  return tokens;
}

function readQuotedColorGroupToken(query: string, startIndex: number): { value: string; nextIndex: number } {
  let index = startIndex + 1;
  let value = '';
  while (index < query.length) {
    const current = query[index];
    if (current === '\\' && index + 1 < query.length) {
      value += query[index + 1];
      index += 2;
      continue;
    }

    if (current === '"') {
      return { value, nextIndex: index + 1 };
    }

    value += current;
    index += 1;
  }

  return { value, nextIndex: query.length };
}

function readRegexColorGroupToken(query: string, startIndex: number): { pattern: string; flags: string; nextIndex: number } | null {
  let index = startIndex + 1;
  let pattern = '';

  while (index < query.length) {
    const current = query[index];
    if (current === '\\' && index + 1 < query.length) {
      pattern += `${current}${query[index + 1]}`;
      index += 2;
      continue;
    }

    if (current === '/') {
      index += 1;
      const flagsStart = index;
      while (index < query.length && /[a-z]/i.test(query[index])) {
        index += 1;
      }
      return {
        pattern,
        flags: query.slice(flagsStart, index),
        nextIndex: index,
      };
    }

    pattern += current;
    index += 1;
  }

  return null;
}

function readBracketColorGroupToken(query: string, startIndex: number): { value: string; nextIndex: number } {
  let index = startIndex + 1;
  let value = '';

  while (index < query.length) {
    if (query[index] === ']') {
      return { value, nextIndex: index + 1 };
    }
    value += query[index];
    index += 1;
  }

  return { value, nextIndex: query.length };
}

function parseColorGroupTokens(tokens: ColorQueryToken[]): ColorQueryExpression {
  let index = 0;

  const parseExpression = (): ColorQueryExpression => {
    const expressions = [parseAnd()];
    while (tokens[index]?.type === 'or') {
      index += 1;
      expressions.push(parseAnd());
    }
    return expressions.length === 1 ? expressions[0] : { kind: 'or', expressions };
  };

  const parseAnd = (): ColorQueryExpression => {
    const expressions: ColorQueryExpression[] = [];
    while (index < tokens.length && tokens[index]?.type !== 'rparen' && tokens[index]?.type !== 'or') {
      expressions.push(parseUnary());
    }
    if (expressions.length === 0) {
      return { kind: 'term', term: { type: 'word', value: '' } };
    }
    return expressions.length === 1 ? expressions[0] : { kind: 'and', expressions };
  };

  const parseUnary = (): ColorQueryExpression => {
    if (tokens[index]?.type === 'negate') {
      index += 1;
      return { kind: 'not', expression: parseUnary() };
    }
    return parsePrimary();
  };

  const parsePrimary = (): ColorQueryExpression => {
    const token = tokens[index];
    if (!token) {
      return { kind: 'term', term: { type: 'word', value: '' } };
    }

    if (token.type === 'lparen') {
      index += 1;
      const expression = parseExpression();
      if (tokens[index]?.type === 'rparen') {
        index += 1;
      }
      return expression;
    }

    if (token.type === 'phrase' || token.type === 'regex') {
      index += 1;
      return { kind: 'term', term: token };
    }

    if (token.type === 'bracket') {
      index += 1;
      return parseColorGroupPropertyExpression(token.value);
    }

    if (token.type === 'word') {
      const scoped = parseScopedColorGroupWord(token.value);
      index += 1;
      if (scoped) {
        const expression = scoped.rest.length > 0 ? parseColorGroupTokens(tokenizeColorGroupQuery(scoped.rest)) : parseUnary();
        return scoped.scope === 'match-case' || scoped.scope === 'ignore-case'
          ? { kind: 'case', mode: scoped.scope, expression }
          : { kind: 'scope', scope: scoped.scope, expression };
      }
      return { kind: 'term', term: token };
    }

    index += 1;
    return { kind: 'term', term: { type: 'word', value: '' } };
  };

  return parseExpression();
}

function parseScopedColorGroupWord(value: string): { scope: ColorQueryScope; rest: string } | null {
  const separatorIndex = value.indexOf(':');
  if (separatorIndex <= 0) {
    return null;
  }

  const scope = value.slice(0, separatorIndex).toLowerCase() as ColorQueryScope;
  const rest = value.slice(separatorIndex + 1);
  switch (scope) {
    case 'file':
    case 'path':
    case 'content':
    case 'tag':
    case 'line':
    case 'block':
    case 'section':
    case 'task':
    case 'task-todo':
    case 'task-done':
    case 'kind':
    case 'status':
    case 'label':
    case 'summary':
    case 'bound':
    case 'match-case':
    case 'ignore-case':
      return { scope, rest };
    default:
      return null;
  }
}

function parseColorGroupPropertyExpression(value: string): ColorQueryExpression {
  const separatorIndex = value.indexOf(':');
  if (separatorIndex === -1) {
    return { kind: 'property', property: value.trim(), expression: null };
  }

  return {
    kind: 'property',
    property: value.slice(0, separatorIndex).trim(),
    expression: parseColorGroupTokens(tokenizeColorGroupQuery(value.slice(separatorIndex + 1).trim())),
  };
}

function evaluateColorGroupQuery(
  expression: ColorQueryExpression,
  context: ColorQueryContext,
  caseMode: ColorQueryCaseMode = 'default',
  scope: ColorQuerySearchScope = 'default',
): boolean {
  switch (expression.kind) {
    case 'and':
      return expression.expressions.every((item) => evaluateColorGroupQuery(item, context, caseMode, scope));
    case 'or':
      return expression.expressions.some((item) => evaluateColorGroupQuery(item, context, caseMode, scope));
    case 'not':
      return !evaluateColorGroupQuery(expression.expression, context, caseMode, scope);
    case 'case':
      return evaluateColorGroupQuery(expression.expression, context, expression.mode, scope);
    case 'scope':
      return evaluateColorGroupScope(expression.scope, expression.expression, context, caseMode);
    case 'property':
      return evaluateColorGroupProperty(expression, context, caseMode);
    case 'term':
      return evaluateColorGroupTerm(expression.term, context, caseMode, scope);
    default:
      return false;
  }
}

function evaluateColorGroupScope(
  scope: ColorQueryScope,
  expression: ColorQueryExpression,
  context: ColorQueryContext,
  caseMode: ColorQueryCaseMode,
): boolean {
  switch (scope) {
    case 'task':
      return context.node.kind === 'task' && evaluateColorGroupQuery(expression, context, caseMode, 'default');
    case 'task-todo':
      return context.node.kind === 'task' && context.node.status !== 'completed' && evaluateColorGroupQuery(expression, context, caseMode, 'default');
    case 'task-done':
      return context.node.kind === 'task' && context.node.status === 'completed' && evaluateColorGroupQuery(expression, context, caseMode, 'default');
    case 'line':
    case 'block':
    case 'section':
      return evaluateColorGroupQuery(expression, context, caseMode, 'content');
    case 'file':
    case 'path':
    case 'content':
    case 'tag':
    case 'kind':
    case 'status':
    case 'label':
    case 'summary':
    case 'bound':
      return evaluateColorGroupQuery(expression, context, caseMode, scope);
    default:
      return evaluateColorGroupQuery(expression, context, caseMode, 'default');
  }
}

function evaluateColorGroupProperty(
  expression: Extract<ColorQueryExpression, { kind: 'property' }>,
  context: ColorQueryContext,
  caseMode: ColorQueryCaseMode,
): boolean {
  const propertyScope = normalizeColorGroupPropertyScope(expression.property);
  if (!propertyScope) {
    return false;
  }
  return expression.expression
    ? evaluateColorGroupScope(propertyScope, expression.expression, context, caseMode)
    : hasColorGroupPropertyValue(propertyScope, context);
}

function normalizeColorGroupPropertyScope(property: string): ColorQuerySearchScope | 'tag' {
  switch (property.toLowerCase()) {
    case 'file':
    case 'path':
    case 'content':
    case 'tag':
    case 'tags':
    case 'kind':
    case 'status':
    case 'label':
    case 'summary':
    case 'bound':
      return property.toLowerCase() === 'tags' ? 'tag' : property.toLowerCase() as ColorQuerySearchScope | 'tag';
    default:
      return null as never;
  }
}

function hasColorGroupPropertyValue(
  property: ColorQuerySearchScope | 'tag',
  context: ColorQueryContext,
): boolean {
  switch (property) {
    case 'tag':
      return context.node.tags.length > 0;
    case 'summary':
      return context.node.summary.trim().length > 0;
    case 'bound':
      return true;
    case 'path':
      return context.nodeId.trim().length > 0;
    case 'file':
    case 'content':
    case 'label':
      return context.node.label.trim().length > 0;
    case 'kind':
      return context.node.kind.trim().length > 0;
    case 'status':
      return context.node.status.trim().length > 0;
    default:
      return false;
  }
}

function evaluateColorGroupTerm(
  term: ColorQueryTerm,
  context: ColorQueryContext,
  caseMode: ColorQueryCaseMode,
  scope: ColorQuerySearchScope,
): boolean {
  switch (scope) {
    case 'file':
      return matchesColorGroupTexts(term, getColorGroupFileTexts(context), caseMode);
    case 'path':
      return matchesColorGroupTexts(term, getColorGroupPathTexts(context), caseMode);
    case 'content':
      return matchesColorGroupTexts(term, getColorGroupContentTexts(context), caseMode);
    case 'tag':
      return matchesColorGroupTags(term, context.node.tags, caseMode);
    case 'kind':
      return matchesColorGroupTexts(term, [context.node.kind], caseMode);
    case 'status':
      return matchesColorGroupTexts(term, [context.node.status], caseMode);
    case 'label':
      return matchesColorGroupTexts(term, [context.node.label], caseMode);
    case 'summary':
      return matchesColorGroupTexts(term, [context.node.summary], caseMode);
    case 'bound':
      return matchesColorGroupBound(term, context.node.hasRuntimeBinding, caseMode);
    default:
      return matchesColorGroupTexts(term, getDefaultColorGroupTexts(context), caseMode);
  }
}

function getDefaultColorGroupTexts(context: ColorQueryContext): string[] {
  return [context.node.label, context.node.summary, ...context.node.tags.map((tag) => `#${tag}`)].filter(Boolean);
}

function getColorGroupFileTexts(context: ColorQueryContext): string[] {
  const candidates = [context.node.label, context.nodeId]
    .filter(Boolean)
    .flatMap((value) => [value, value.replace(/\\/g, '/').split('/').at(-1) ?? value]);
  return Array.from(new Set(candidates));
}

function getColorGroupPathTexts(context: ColorQueryContext): string[] {
  return Array.from(new Set([context.nodeId, context.node.label].filter(Boolean)));
}

function getColorGroupContentTexts(context: ColorQueryContext): string[] {
  return [context.node.label, context.node.summary, ...context.node.tags.map((tag) => `#${tag}`)].filter(Boolean);
}

function matchesColorGroupTexts(
  term: ColorQueryTerm,
  candidates: string[],
  caseMode: ColorQueryCaseMode,
): boolean {
  if (term.type === 'regex') {
    const regex = buildColorGroupRegex(term.pattern, term.flags, caseMode);
    return regex ? candidates.some((candidate) => regex.test(candidate)) : false;
  }

  const needle = normalizeColorQueryText(term.value, caseMode);
  return candidates.some((candidate) => normalizeColorQueryText(candidate, caseMode).includes(needle));
}

function matchesColorGroupTags(
  term: ColorQueryTerm,
  tags: string[],
  caseMode: ColorQueryCaseMode,
): boolean {
  const normalizedTags = tags.map((tag) => normalizeColorQueryTag(tag));
  if (term.type === 'regex') {
    const regex = buildColorGroupRegex(term.pattern, term.flags, caseMode);
    return regex ? normalizedTags.some((tag) => regex.test(tag) || regex.test(`#${tag}`)) : false;
  }

  const needle = normalizeColorQueryText(normalizeColorQueryTag(term.value), caseMode);
  return normalizedTags.some((tag) => normalizeColorQueryText(tag, caseMode) === needle);
}

function matchesColorGroupBound(
  term: ColorQueryTerm,
  hasRuntimeBinding: boolean,
  caseMode: ColorQueryCaseMode,
): boolean {
  return matchesColorGroupTexts(
    term.type === 'word' || term.type === 'phrase' ? { type: term.type, value: term.value } : term,
    hasRuntimeBinding ? ['true', 'yes', '1', 'bound', 'runtime'] : ['false', 'no', '0', 'unbound', 'display'],
    caseMode,
  );
}

function buildColorGroupRegex(
  pattern: string,
  flags: string,
  caseMode: ColorQueryCaseMode,
): RegExp | null {
  try {
    const normalizedFlags = Array.from(new Set(flags.replace(/[gy]/g, '').split(''))).join('');
    const effectiveFlags = caseMode === 'match-case' || normalizedFlags.includes('i') ? normalizedFlags : `${normalizedFlags}i`;
    return new RegExp(pattern, effectiveFlags);
  } catch {
    return null;
  }
}

function normalizeColorQueryText(value: string, caseMode: ColorQueryCaseMode): string {
  return caseMode === 'match-case' ? value : value.toLowerCase();
}

function normalizeColorQueryTag(value: string): string {
  return value.replace(/^#/, '').trim();
}

function normalizeColorGroupHex(value: unknown, fallback: string): string {
  return typeof value === 'string' && /^#[0-9a-f]{6}$/i.test(value) ? value : fallback;
}

function pickColorGroupPaletteColor(index: number): string {
  return colorGroupPalette[index % colorGroupPalette.length];
}

function defaultNodeColor(node: ProgressGraphPreviewV2PoCNode): string {
  return statusColors[node.status] ?? '#6f8192';
}

function resolveNodeVisualColor(node: Partial<GraphNodeRenderData> | undefined): string {
  if (typeof node?.visualColor === 'string' && node.visualColor.length > 0) {
    return node.visualColor;
  }
  return typeof node?.status === 'string' ? (statusColors[node.status] ?? '#6f8192') : '#6f8192';
}

function createDebouncedCallback(callback: () => void, delayMs: number): () => void {
  let timeoutId: number | null = null;
  return () => {
    if (timeoutId !== null) {
      window.clearTimeout(timeoutId);
    }
    timeoutId = window.setTimeout(() => {
      timeoutId = null;
      callback();
    }, delayMs);
  };
}

type GraphEventTargetShape = {
  id?: string;
  className?: string;
  parentElement?: GraphEventTargetShape | null;
  parentNode?: GraphEventTargetShape | null;
};

function getEventTargetId(
  event: { target?: { id?: string }; originalTarget?: GraphEventTargetShape },
  options?: { keyShapeOnly?: boolean },
): string | null {
  if (options?.keyShapeOnly && resolveEventSubShapeClassName(event.originalTarget) !== 'key') {
    return null;
  }
  const nodeId = event.target?.id;
  return typeof nodeId === 'string' && nodeId.length > 0 ? nodeId : null;
}

function resolveEventSubShapeClassName(target?: GraphEventTargetShape): string | null {
  let current = target;
  while (current) {
    if (current.className === 'key' || current.className === 'label') {
      return current.className;
    }
    current = current.parentElement ?? current.parentNode ?? null;
  }
  return null;
}

function hexToRgba(hex: string, alpha: number): string {
  const normalized = hex.replace('#', '');
  if (normalized.length !== 6) {
    return hex;
  }

  const red = Number.parseInt(normalized.slice(0, 2), 16);
  const green = Number.parseInt(normalized.slice(2, 4), 16);
  const blue = Number.parseInt(normalized.slice(4, 6), 16);
  return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
}

function blendHexColors(fromHex: string, toHex: string, ratio: number): string {
  const from = fromHex.replace('#', '');
  const to = toHex.replace('#', '');
  if (from.length !== 6 || to.length !== 6) {
    return fromHex;
  }

  const clampedRatio = Math.min(1, Math.max(0, ratio));
  const fromRed = Number.parseInt(from.slice(0, 2), 16);
  const fromGreen = Number.parseInt(from.slice(2, 4), 16);
  const fromBlue = Number.parseInt(from.slice(4, 6), 16);
  const toRed = Number.parseInt(to.slice(0, 2), 16);
  const toGreen = Number.parseInt(to.slice(2, 4), 16);
  const toBlue = Number.parseInt(to.slice(4, 6), 16);

  const red = Math.round(fromRed * (1 - clampedRatio) + toRed * clampedRatio);
  const green = Math.round(fromGreen * (1 - clampedRatio) + toGreen * clampedRatio);
  const blue = Math.round(fromBlue * (1 - clampedRatio) + toBlue * clampedRatio);

  return `#${[red, green, blue].map((value) => value.toString(16).padStart(2, '0')).join('')}`;
}

function coerceNumber(value: unknown, fallback: number): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback;
}

function clampNumber(value: unknown, min: number, max: number, fallback: number): number {
  const candidate = coerceNumber(value, fallback);
  return Math.min(max, Math.max(min, candidate));
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    void main();
  }, { once: true });
} else {
  void main();
}
