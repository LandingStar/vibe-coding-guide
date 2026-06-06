/// <reference lib="dom" />

import {
  Canvas2DRenderer,
  GraphModel,
  createSimulationClient,
  defaultDisplayOptions,
  defaultRendererTheme,
  normalizeGraph,
} from '@note-web/knowledge-graph-engine';
import type {
  DisplayOptions,
  GraphAppearance,
  KnowledgeGraphLink,
  KnowledgeGraphLinkInput,
  KnowledgeGraphNode,
  MotionControl,
  NormalizedGraph,
  RendererTheme,
  SimulationMetrics,
} from '@note-web/knowledge-graph-engine';
import {
  buildProgressGraphNodeColorMap,
  defaultProgressGraphNodeColor,
} from './progressGraphColorGroups';
import type { ProgressGraphColorGroup } from './progressGraphColorGroups';

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

type V2GraphColorGroup = ProgressGraphColorGroup;

type V2GraphConfigState = {
  appearance: V2GraphAppearanceSettings;
  forces: V2GraphForceSettings;
  colorGroups: V2GraphColorGroup[];
  ui: {
    configCollapsed: boolean;
    sidePanelWidth: number;
  };
};

type EngineGraphModel = InstanceType<typeof GraphModel>;

type EngineRenderer = InstanceType<typeof Canvas2DRenderer>;

type EngineSimulation = ReturnType<typeof createSimulationClient>;

type RendererViewportState = {
  height: number;
  panX: number;
  panY: number;
  scale: number;
  width: number;
};

type RendererWithViewportState = EngineRenderer & {
  state?: RendererViewportState;
};

type EngineForceOptions = {
  centerStrength: number;
  linkStrength: number;
  linkDistance: number;
  repelStrength: number;
};

type ProgressMotionController = {
  onTick(metrics: SimulationMetrics | null): MotionControl | void;
  reset(): void;
};

const viewportScaleLimits = {
  min: 0.01,
  max: 3.6,
};

const forceControlBounds = {
  gravity: { min: 1, max: 24 },
  repulsion: { min: 200, max: 3000 },
  attraction: { min: 10, max: 140 },
  linkLength: { min: 80, max: 280 },
};

const layoutShakeForces: V2GraphForceSettings = {
  gravity: forceControlBounds.gravity.min,
  repulsion: forceControlBounds.repulsion.max,
  attraction: forceControlBounds.attraction.max,
  linkLength: forceControlBounds.linkLength.min,
};

const layoutShakeTiming = {
  autoDelayMs: 140,
  forceHoldMs: 300,
  resetAfterMs: 520,
};

const layoutShakeEvolutionMultiplier = 3;

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
    nodeScale: 1.12,
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

async function main(): Promise<void> {
  const container = document.getElementById('pgHostV2GraphCanvas');
  const detail = document.getElementById('pgHostV2GraphDetail');
  if (!(container instanceof HTMLElement) || !(detail instanceof HTMLElement)) {
    return;
  }

  window.__pgHostV2GraphCleanup?.();
  window.__pgHostV2GraphCleanup = undefined;

  const payload = readPayload();
  const workerUri = readWorkerUri(container);
  const autoShakeEnabled = readAutoShakeEnabled(container);
  if (!payload || payload.nodes.length === 0) {
    renderEmpty(container, detail, 'No graph payload is available.');
    return;
  }
  if (!workerUri) {
    renderEmpty(container, detail, 'Graph worker bundle is unavailable.');
    return;
  }

  const configState = loadGraphConfigState();
  const interactionState = {
    selectedNodeId: null as string | null,
    hoveredNodeId: null as string | null,
  };
  const graphData = buildEngineGraph(payload, configState);
  const model = new GraphModel(graphData);
  const canvas = document.createElement('canvas');
  canvas.className = 'pg-host-v2-engine-canvas';
  canvas.style.display = 'block';
  canvas.style.width = '100%';
  canvas.style.height = '100%';
  canvas.style.touchAction = 'none';
  container.replaceChildren(canvas);

  let destroyed = false;
  let fitOnNextTick = true;
  let lastMetrics: SimulationMetrics | null = null;
  let renderer: EngineRenderer | null = null;
  let simulation: EngineSimulation | null = null;
  let workerObjectUrl: string | null = null;
  let layoutShakeTimer: number | null = null;
  let autoShakeTimer: number | null = null;
  let postShakeResetTimer: number | null = null;
  let autoShakePending = autoShakeEnabled;
  const motionController = createProgressMotionController();

  const renderDetailForNode = (nodeId: string | null): void => {
    const node = nodeId ? payload.nodes.find((item) => item.id === nodeId) ?? null : null;
    renderNodeDetail(detail, node, payload.runtimeSummary, interactionState.selectedNodeId);
  };

  const setSelectedNode = (nodeId: string | null): void => {
    interactionState.selectedNodeId = nodeId;
    renderer?.setInteractionState({ selectedNodeId: nodeId }, { render: false });
    renderDetailForNode(nodeId);
    syncClearSelectionButton(nodeId);
    renderer?.render();
  };

  const setHoveredNode = (nodeId: string | null): void => {
    interactionState.hoveredNodeId = nodeId;
    renderer?.setInteractionState({ hoveredNodeId: nodeId }, { render: false });
  };

  renderer = new Canvas2DRenderer({
    canvas,
    model,
    getAppearance: () => buildGraphAppearance(configState),
    getHighlightedNodes: (activeNodeId: string) => getNeighborhoodNodeIds(model, activeNodeId),
    getHighlightedLinks: (activeNodeId: string) => getNeighborhoodLinkIds(model, activeNodeId),
    interaction: {
      selectedNodeId: interactionState.selectedNodeId,
      hoveredNodeId: interactionState.hoveredNodeId,
      selectOnClick: true,
      openOn: 'double-click',
      clearSelectionOnCanvasClick: true,
      hover: true,
      dragNodes: true,
      panCanvas: true,
      zoomCanvas: true,
    },
    events: {
      onNodeDrag: ({ node, point, alpha }) => {
        motionController.reset();
        if (simulation) {
          simulation.pinNode(node.id, point, alpha);
          return;
        }
        node.x = point.x;
        node.y = point.y;
        renderer?.render();
      },
      onNodeRelease: ({ node }) => {
        motionController.reset();
        simulation?.releaseNode(node.id, 0.24);
      },
      onNodeSelect: ({ nodeId }) => {
        setSelectedNode(interactionState.selectedNodeId === nodeId ? null : nodeId);
      },
      onNodeHover: ({ nodeId }) => {
        setHoveredNode(nodeId);
      },
      onNodeOpen: ({ nodeId }) => {
        setSelectedNode(nodeId);
      },
      onStatus: ({ statusText }) => updateStatusText(statusText, lastMetrics),
    },
  });

  const rerender = (): void => {
    if (!destroyed) {
      renderer?.render();
    }
  };

  const restartLayout = (alpha = 0.8): void => {
    if (!destroyed && simulation) {
      simulation.updateForces(buildForceOptions(configState), alpha);
    }
  };

  const syncShakeLayoutButton = (active: boolean): void => {
    const button = document.getElementById('pgHostV2ShakeLayout');
    if (button instanceof HTMLButtonElement) {
      button.disabled = active;
      button.textContent = active ? 'Shaking...' : 'Shake Layout';
    }
  };

  const clearLayoutShakeTimer = (): void => {
    if (layoutShakeTimer !== null) {
      window.clearTimeout(layoutShakeTimer);
      layoutShakeTimer = null;
    }
  };

  const clearAutoShakeTimer = (): void => {
    if (autoShakeTimer !== null) {
      window.clearTimeout(autoShakeTimer);
      autoShakeTimer = null;
    }
  };

  const clearPostShakeResetTimer = (): void => {
    if (postShakeResetTimer !== null) {
      window.clearTimeout(postShakeResetTimer);
      postShakeResetTimer = null;
    }
  };

  const schedulePostShakeReset = (): void => {
    clearPostShakeResetTimer();
    postShakeResetTimer = window.setTimeout(() => {
      postShakeResetTimer = null;
      if (destroyed) {
        return;
      }
      renderer?.resize();
      resetRendererZoom(renderer);
      updateStatusText('Layout shake fitted to viewport', lastMetrics);
    }, layoutShakeTiming.resetAfterMs);
  };

  const runLayoutShake = (reason: 'manual' | 'refresh'): void => {
    if (destroyed || !simulation) {
      return;
    }

    autoShakePending = false;
    clearAutoShakeTimer();
    clearLayoutShakeTimer();
    clearPostShakeResetTimer();
    motionController.reset();
    syncShakeLayoutButton(true);
    updateStatusText(reason === 'manual' ? 'Shaking layout' : 'Untangling refreshed graph', lastMetrics);
    simulation.updateForces(
      buildForceOptionsForSettings(layoutShakeForces),
      layoutShakeEvolutionMultiplier,
    );
    layoutShakeTimer = window.setTimeout(() => {
      layoutShakeTimer = null;
      syncShakeLayoutButton(false);
      if (destroyed || !simulation) {
        return;
      }
      motionController.reset();
      simulation.stop();
      simulation.updateForces(buildForceOptions(configState), 0.95);
      updateStatusText('Layout shake restoring saved forces', lastMetrics);
      if (reason === 'refresh') {
        schedulePostShakeReset();
      }
    }, layoutShakeTiming.forceHoldMs);
  };

  const scheduleAutoLayoutShake = (): void => {
    if (!autoShakeEnabled || !autoShakePending) {
      return;
    }
    autoShakePending = false;
    clearAutoShakeTimer();
    autoShakeTimer = window.setTimeout(() => {
      autoShakeTimer = null;
      runLayoutShake('refresh');
    }, layoutShakeTiming.autoDelayMs);
  };

  initializeConfigPanel(configState, {
    onAppearanceChange: () => {
      persistGraphConfigState(configState);
      applyNodeColors(model, payload, configState.colorGroups);
      rerender();
    },
    onForceChange: () => {
      persistGraphConfigState(configState);
      motionController.reset();
      restartLayout(0.7);
    },
    onColorGroupChange: () => {
      persistGraphConfigState(configState);
      applyNodeColors(model, payload, configState.colorGroups);
      rerender();
    },
  });

  const layoutRoot = document.getElementById('pgHostV2Layout');
  const sideArea = document.getElementById('pgHostV2Side');
  const configCard = document.getElementById('pgHostV2ConfigCard');
  const configToggleButton = document.getElementById('pgHostV2ConfigToggle');
  const collapsedConfigBar = document.getElementById('pgHostV2ConfigCollapsedBar');
  const clearSelectionButton = document.getElementById('pgHostV2ClearSelection');
  const resizeHandle = document.getElementById('pgHostV2ResizeHandle');
  let resizingSidePanel = false;

  const applySplitLayoutState = (): void => {
    if (!(layoutRoot instanceof HTMLElement)) {
      return;
    }
    const maxWidth = Math.min(620, Math.max(320, layoutRoot.clientWidth - 320));
    configState.ui.sidePanelWidth = clampNumber(configState.ui.sidePanelWidth, 280, maxWidth, defaultGraphConfigState.ui.sidePanelWidth);
    layoutRoot.style.setProperty('--pg-host-v2-side-width', `${Math.round(configState.ui.sidePanelWidth)}px`);
  };

  const applyConfigPanelState = (): void => {
    const collapsed = configState.ui.configCollapsed;
    for (const element of [sideArea, configCard, collapsedConfigBar]) {
      if (element instanceof HTMLElement) {
        element.dataset.pgConfigCollapsed = collapsed ? 'true' : 'false';
        element.dataset.pgConfigMorphing = 'false';
      }
    }
    if (configToggleButton instanceof HTMLButtonElement) {
      configToggleButton.textContent = collapsed ? 'Expand' : 'Collapse';
      configToggleButton.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
    }
    if (collapsedConfigBar instanceof HTMLButtonElement) {
      collapsedConfigBar.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
    }
  };

  const setConfigPanelCollapsed = (collapsed: boolean): void => {
    configState.ui.configCollapsed = collapsed;
    applyConfigPanelState();
    persistGraphConfigState(configState);
    requestAnimationFrame(() => {
      renderer?.resize();
      resetRendererZoom(renderer);
    });
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
    persistGraphConfigState(configState);
  };

  const handleSidePanelResize = (event: PointerEvent): void => {
    if (!resizingSidePanel || !(layoutRoot instanceof HTMLElement)) {
      return;
    }
    const rect = layoutRoot.getBoundingClientRect();
    const nextWidth = rect.right - event.clientX - 14;
    configState.ui.sidePanelWidth = clampNumber(nextWidth, 280, 620, defaultGraphConfigState.ui.sidePanelWidth);
    applySplitLayoutState();
    renderer?.resize();
  };

  applySplitLayoutState();
  applyConfigPanelState();
  configToggleButton?.addEventListener('click', () => setConfigPanelCollapsed(!configState.ui.configCollapsed));
  collapsedConfigBar?.addEventListener('click', () => setConfigPanelCollapsed(false));
  clearSelectionButton?.addEventListener('click', () => {
    setSelectedNode(null);
  });
  resizeHandle?.addEventListener('pointerdown', (event) => {
    resizingSidePanel = true;
    if (resizeHandle instanceof HTMLElement) {
      resizeHandle.dataset.pgDragging = 'true';
      resizeHandle.setPointerCapture?.(event.pointerId);
    }
    document.body.style.cursor = 'col-resize';
    event.preventDefault();
  });
  window.addEventListener('pointermove', handleSidePanelResize);
  window.addEventListener('pointerup', stopSidePanelResize);
  window.addEventListener('pointercancel', stopSidePanelResize);
  container.addEventListener('wheel', (event) => {
    if (zoomRendererAtPointer(renderer, canvas, event)) {
      event.preventDefault();
      event.stopPropagation();
    }
  }, { capture: true, passive: false });

  const resetViewportButton = document.getElementById('pgHostV2ResetViewport');
  resetViewportButton?.addEventListener('click', () => {
    resetRendererZoom(renderer);
  });
  const shakeLayoutButton = document.getElementById('pgHostV2ShakeLayout');
  shakeLayoutButton?.addEventListener('click', () => {
    runLayoutShake('manual');
  });

  const resizeObserver = typeof ResizeObserver === 'function'
    ? new ResizeObserver(() => {
      renderer?.resize();
    })
    : null;
  resizeObserver?.observe(container);
  const handleWindowResize = (): void => {
    renderer?.resize();
  };
  window.addEventListener('resize', handleWindowResize);

  renderDetailForNode(null);
  syncClearSelectionButton(null);
  renderer.render();
  requestAnimationFrame(() => {
    renderer?.resize();
    renderer?.render();
  });
  updateStatusText('Static graph ready', null);

  const cleanup = (): void => {
    if (destroyed) {
      return;
    }
    destroyed = true;
    clearLayoutShakeTimer();
    clearAutoShakeTimer();
    clearPostShakeResetTimer();
    resizeObserver?.disconnect();
    window.removeEventListener('resize', handleWindowResize);
    window.removeEventListener('pointermove', handleSidePanelResize);
    window.removeEventListener('pointerup', stopSidePanelResize);
    window.removeEventListener('pointercancel', stopSidePanelResize);
    renderer?.dispose();
    simulation?.dispose();
    if (workerObjectUrl) {
      URL.revokeObjectURL(workerObjectUrl);
      workerObjectUrl = null;
    }
    if (window.__pgHostV2GraphCleanup === cleanup) {
      window.__pgHostV2GraphCleanup = undefined;
    }
  };

  window.__pgHostV2GraphCleanup = cleanup;
  window.addEventListener('beforeunload', cleanup, { once: true });

  void startSimulation();

  async function startSimulation(): Promise<void> {
    try {
      const simulationWorkerUrl = await resolveSimulationWorkerUrl(workerUri);
      if (destroyed) {
        if (simulationWorkerUrl.objectUrl) {
          URL.revokeObjectURL(simulationWorkerUrl.objectUrl);
        }
        return;
      }
      workerObjectUrl = simulationWorkerUrl.objectUrl;
      simulation = createSimulationClient({
        workerUrl: simulationWorkerUrl.url,
        model,
        motionController,
        onTick: (metrics) => {
          if (destroyed) {
            return;
          }
          lastMetrics = metrics;
          if (fitOnNextTick) {
            fitOnNextTick = false;
            scheduleAutoLayoutShake();
          } else {
            renderer?.render();
          }
          updateStatusText('Layout evolving', metrics);
        },
        onSettled: (metrics) => {
          if (destroyed) {
            return;
          }
          lastMetrics = metrics;
          renderer?.render();
          scheduleAutoLayoutShake();
          updateStatusText('Layout settled', metrics);
        },
      });
      simulation.start(buildForceOptions(configState), 1);
      updateStatusText('Layout starting', null);
    } catch (error) {
      if (workerObjectUrl) {
        URL.revokeObjectURL(workerObjectUrl);
        workerObjectUrl = null;
      }
      updateStatusText(`Layout worker unavailable; static graph shown (${formatErrorMessage(error)})`, null);
      renderer?.render();
    }
  }
}

function buildEngineGraph(
  payload: ProgressGraphPreviewV2PoCPayload,
  configState: V2GraphConfigState,
): NormalizedGraph {
  const colors = buildNodeColorMap(payload.nodes, configState.colorGroups);
  const nodeCount = Math.max(1, payload.nodes.length);
  const nodes: KnowledgeGraphNode[] = payload.nodes.map((node, index) => {
    const seed = computeSeedPosition(index, nodeCount);
    return {
      ...node,
      kind: node.kind || 'node',
      status: node.status || '',
      radius: computeBaseNodeSize(node),
      color: colors.get(node.id) ?? defaultNodeColor(node),
      x: seed.x,
      y: seed.y,
      data: {
        progressNode: node,
      },
    };
  });
  const nodeIds = new Set(nodes.map((node) => node.id));
  const links: KnowledgeGraphLinkInput[] = payload.edges
    .filter((edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target))
    .map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      kind: edge.kind,
      directed: edge.directed,
      data: {
        progressEdge: edge,
      },
    }));
  return normalizeGraph({ nodes, links });
}

function zoomRendererAtPointer(
  renderer: EngineRenderer | null,
  canvas: HTMLCanvasElement,
  event: WheelEvent,
): boolean {
  const state = (renderer as RendererWithViewportState | null)?.state;
  if (!renderer || !state) {
    return false;
  }

  const rect = canvas.getBoundingClientRect();
  if (rect.width <= 0 || rect.height <= 0) {
    return false;
  }

  const localX = event.clientX - rect.left;
  const localY = event.clientY - rect.top;
  if (localX < 0 || localY < 0 || localX > rect.width || localY > rect.height) {
    return false;
  }

  const beforeX = (localX - state.width / 2 - state.panX) / state.scale;
  const beforeY = (localY - state.height / 2 - state.panY) / state.scale;
  const factor = Math.pow(1.2, -event.deltaY / 120);
  const nextScale = clampNumber(state.scale * factor, viewportScaleLimits.min, viewportScaleLimits.max, state.scale);
  if (nextScale === state.scale) {
    return true;
  }

  state.scale = nextScale;
  const afterX = state.width / 2 + state.panX + beforeX * state.scale;
  const afterY = state.height / 2 + state.panY + beforeY * state.scale;
  state.panX += localX - afterX;
  state.panY += localY - afterY;
  renderer.render();
  return true;
}

function resetRendererZoom(renderer: EngineRenderer | null): void {
  renderer?.resetZoom({
    padding: 64,
    minScale: viewportScaleLimits.min,
    maxScale: viewportScaleLimits.max,
  });
}

function applyNodeColors(
  model: EngineGraphModel,
  payload: ProgressGraphPreviewV2PoCPayload,
  colorGroups: V2GraphColorGroup[],
): void {
  const colors = buildNodeColorMap(payload.nodes, colorGroups);
  for (const node of model.nodes) {
    const payloadNode = payload.nodes.find((item) => item.id === node.id);
    if (payloadNode) {
      node.color = colors.get(node.id) ?? defaultNodeColor(payloadNode);
    }
  }
}

function buildDisplayOptions(configState: V2GraphConfigState): DisplayOptions {
  return {
    ...defaultDisplayOptions,
    showArrows: true,
    // Large graphs may auto-fit far below the engine's default text-fade threshold.
    // Keep label visibility governed by the coverage slider instead of viewport scale.
    textFade: viewportScaleLimits.min,
    nodeSize: configState.appearance.nodeScale,
    linkThickness: configState.appearance.edgeScale,
  };
}

function buildGraphAppearance(configState: V2GraphConfigState): GraphAppearance {
  return {
    display: buildDisplayOptions(configState),
    hitTest: {
      minRadius: 9,
      padding: 4,
    },
    labelPolicy: {
      mode: 'density',
      priority: 'degree',
      density: clampNumber(
        configState.appearance.labelDensity,
        0,
        1,
        defaultGraphConfigState.appearance.labelDensity,
      ),
      textFade: viewportScaleLimits.min,
    },
    nodeSizePolicy: {
      mode: 'metric',
      priority: 'degree',
      minScale: 1,
      maxScale: 1.85,
      strength: 0.3,
    },
    theme: buildRendererTheme(configState),
    viewport: {
      fitPadding: 64,
      minScale: viewportScaleLimits.min,
      maxScale: viewportScaleLimits.max,
      zoomStep: 1.2,
    },
  };
}

function buildRendererTheme(configState: V2GraphConfigState): RendererTheme {
  return {
    ...defaultRendererTheme,
    canvas: {
      ...defaultRendererTheme.canvas,
      background: '#f7f3eb',
    },
    node: {
      ...defaultRendererTheme.node,
      fill: '#526a7f',
      stroke: 'rgba(39, 57, 72, 0.34)',
      hoverFill: '#eef6ff',
      hoverStroke: '#6aa7df',
      selectedFill: '#f8fbff',
      selectedStroke: '#2f87c5',
      dimmedFill: 'rgba(95, 116, 136, 0.62)',
      dimmedStroke: 'rgba(39, 57, 72, 0.16)',
      accentRingColor: 'transparent',
      accentRingWidth: 0,
      accentByStatus: {
        pending: 'transparent',
        in_progress: 'transparent',
        blocked: 'transparent',
        completed: 'transparent',
        archived: 'transparent',
      },
    },
    link: {
      ...defaultRendererTheme.link,
      defaultColor: 'rgba(93, 118, 146, 0.28)',
      activeColor: 'rgba(47, 135, 197, 0.92)',
      dimmedColor: 'rgba(93, 118, 146, 0.28)',
      byKind: {
        workflow: 'rgba(70, 128, 178, 0.36)',
        reference: 'rgba(122, 139, 160, 0.26)',
        dependency: 'rgba(139, 108, 176, 0.34)',
      },
    },
    label: {
      ...defaultRendererTheme.label,
      color: 'rgba(30, 39, 46, 0.92)',
      dimmedColor: 'rgba(30, 39, 46, 0.72)',
      fontSize: configState.appearance.labelSize,
      density: clampNumber(
        configState.appearance.labelDensity,
        0.01,
        1,
        defaultGraphConfigState.appearance.labelDensity,
      ),
    },
  };
}

function buildForceOptions(configState: V2GraphConfigState): EngineForceOptions {
  return buildForceOptionsForSettings(configState.forces);
}

function buildForceOptionsForSettings(forces: V2GraphForceSettings): EngineForceOptions {
  return {
    centerStrength: clampNumber(forces.gravity / 150, 0.01, 0.24, 0.08),
    linkStrength: clampNumber(forces.attraction / 50, 0.2, 3.2, 1),
    linkDistance: clampNumber(forces.linkLength, 60, 340, 180),
    repelStrength: clampNumber(forces.repulsion, 120, 4200, 1000),
  };
}

function getNeighborhoodNodeIds(model: EngineGraphModel, activeNodeId: string): string[] {
  const ids = new Set<string>([activeNodeId]);
  for (const link of model.links) {
    if (link.sourceId === activeNodeId) {
      ids.add(link.targetId);
    }
    if (link.targetId === activeNodeId) {
      ids.add(link.sourceId);
    }
  }
  return [...ids];
}

function getNeighborhoodLinkIds(model: EngineGraphModel, activeNodeId: string): string[] {
  return model.links
    .filter((link) => link.sourceId === activeNodeId || link.targetId === activeNodeId)
    .map((link: KnowledgeGraphLink) => link.id);
}

function createProgressMotionController(): ProgressMotionController {
  let quietTicks = 0;
  let brakingTicks = 0;

  const reset = (): void => {
    quietTicks = 0;
    brakingTicks = 0;
  };

  const onTick = (metrics: SimulationMetrics | null): MotionControl | void => {
    if (!metrics) {
      return undefined;
    }

    const relationDelta = computeRelationDelta(metrics);
    if (relationDelta > 0.1 || metrics.averageMovement > 1.8) {
      reset();
      return undefined;
    }

    if (relationDelta < 0.006 && metrics.averageMovement < 0.12 && metrics.alpha < 0.05) {
      quietTicks += 1;
      brakingTicks += 1;
    } else if (relationDelta < 0.018 && metrics.averageMovement < 0.34) {
      quietTicks = Math.max(0, quietTicks - 1);
      brakingTicks += 1;
    } else {
      quietTicks = 0;
      brakingTicks = Math.max(0, brakingTicks - 1);
    }

    if (quietTicks >= 18) {
      return { damp: 0.92, stop: true };
    }

    if (brakingTicks > 0) {
      const damp = clampNumber(0.08 + brakingTicks * 0.045, 0.12, 0.68, 0.22);
      return { damp };
    }

    return undefined;
  };

  return { onTick, reset };
}

function computeRelationDelta(metrics: SimulationMetrics): number {
  const lengthDelta = metrics.edgeLengthDelta / 120;
  const maxLengthDelta = metrics.maxEdgeLengthDelta / 260;
  const angleDelta = metrics.edgeAngleDelta / Math.PI;
  const maxAngleDelta = metrics.maxEdgeAngleDelta / Math.PI;
  return Math.max(lengthDelta, maxLengthDelta * 0.45, angleDelta, maxAngleDelta * 0.35);
}

function initializeConfigPanel(
  configState: V2GraphConfigState,
  handlers: {
    onAppearanceChange: () => void;
    onForceChange: () => void;
    onColorGroupChange: () => void;
  },
): void {
  bindRangeControl('pgHostV2AppearanceLabelDensity', 'pgHostV2AppearanceLabelDensityValue', {
    value: configState.appearance.labelDensity,
    formatValue: (value) => `${Math.round(value * 100)}%`,
    onInput: (value) => {
      configState.appearance.labelDensity = value;
      handlers.onAppearanceChange();
    },
  });
  bindRangeControl('pgHostV2AppearanceLabelSize', 'pgHostV2AppearanceLabelSizeValue', {
    value: configState.appearance.labelSize,
    formatValue: (value) => `${Math.round(value)}px`,
    onInput: (value) => {
      configState.appearance.labelSize = value;
      handlers.onAppearanceChange();
    },
  });
  bindRangeControl('pgHostV2AppearanceNodeScale', 'pgHostV2AppearanceNodeScaleValue', {
    value: configState.appearance.nodeScale,
    formatValue: (value) => `${value.toFixed(2)}x`,
    onInput: (value) => {
      configState.appearance.nodeScale = value;
      handlers.onAppearanceChange();
    },
  });
  bindRangeControl('pgHostV2AppearanceEdgeScale', 'pgHostV2AppearanceEdgeScaleValue', {
    value: configState.appearance.edgeScale,
    formatValue: (value) => `${value.toFixed(2)}x`,
    onInput: (value) => {
      configState.appearance.edgeScale = value;
      handlers.onAppearanceChange();
    },
  });
  bindRangeControl('pgHostV2ForceGravity', 'pgHostV2ForceGravityValue', {
    value: configState.forces.gravity,
    formatValue: (value) => String(Math.round(value)),
    onInput: (value) => {
      configState.forces.gravity = value;
      handlers.onForceChange();
    },
  });
  bindRangeControl('pgHostV2ForceRepulsion', 'pgHostV2ForceRepulsionValue', {
    value: configState.forces.repulsion,
    formatValue: (value) => String(Math.round(value)),
    onInput: (value) => {
      configState.forces.repulsion = value;
      handlers.onForceChange();
    },
  });
  bindRangeControl('pgHostV2ForceAttraction', 'pgHostV2ForceAttractionValue', {
    value: configState.forces.attraction,
    formatValue: (value) => String(Math.round(value)),
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
  valueId: string,
  options: {
    value: number;
    formatValue: (value: number) => string;
    onInput: (value: number) => void;
  },
): void {
  const input = document.getElementById(inputId);
  const output = document.getElementById(valueId);
  if (!(input instanceof HTMLInputElement)) {
    return;
  }
  const syncValue = (value: number): void => {
    input.value = String(value);
    if (output instanceof HTMLOutputElement) {
      output.value = options.formatValue(value);
    }
  };
  syncValue(options.value);
  input.addEventListener('input', () => {
    const value = Number(input.value);
    if (!Number.isFinite(value)) {
      return;
    }
    if (output instanceof HTMLOutputElement) {
      output.value = options.formatValue(value);
    }
    options.onInput(value);
  });
}

function bindColorGroupControls(colorGroups: V2GraphColorGroup[], onChange: () => void): void {
  const list = document.getElementById('pgHostV2ColorGroups');
  const addButton = document.getElementById('pgHostV2AddColorGroup');
  if (!(list instanceof HTMLElement)) {
    return;
  }
  const render = (): void => {
    renderColorGroupRows(list, colorGroups, render, onChange);
  };
  addButton?.addEventListener('click', () => {
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
  list.innerHTML = '';
  colorGroups.forEach((colorGroup, index) => {
    const row = document.createElement('div');
    row.className = 'pg-host-v2-color-group-row';

    const colorInput = document.createElement('input');
    colorInput.type = 'color';
    colorInput.className = 'pg-host-v2-color-group-swatch';
    colorInput.value = normalizeColorGroupHex(colorGroup.color, pickColorGroupPaletteColor(index));
    colorInput.title = 'Color';
    colorInput.addEventListener('input', () => {
      colorGroup.color = colorInput.value;
      onChange();
    });

    const queryInput = document.createElement('input');
    queryInput.type = 'text';
    queryInput.className = 'pg-host-v2-color-group-input';
    queryInput.value = colorGroup.query;
    queryInput.placeholder = 'label, tag, kind, status';
    queryInput.addEventListener('input', () => {
      colorGroup.query = queryInput.value;
      onChange();
    });

    const removeButton = document.createElement('button');
    removeButton.type = 'button';
    removeButton.className = 'pg-host-v2-color-group-remove';
    removeButton.textContent = 'x';
    removeButton.disabled = colorGroups.length <= 1;
    removeButton.addEventListener('click', () => {
      colorGroups.splice(index, 1);
      rerender();
      onChange();
    });

    row.append(queryInput, colorInput, removeButton);
    list.append(row);
  });
}

function renderNodeDetail(
  detail: HTMLElement,
  node: ProgressGraphPreviewV2PoCNode | null,
  runtimeSummary: ProgressGraphPreviewV2PoCPayload['runtimeSummary'],
  selectedNodeId: string | null,
): void {
  if (!node) {
    detail.innerHTML = `<div class="pg-host-v2-detail-stack">
  <p class="pg-host-v2-detail-kicker">Knowledge Graph Engine</p>
  <h4 class="pg-host-v2-detail-title">Select a node</h4>
  <p class="pg-host-v2-detail-meta">runtime bound nodes=${escapeHtml(String(runtimeSummary.boundNodeCount))} · open work=${escapeHtml(String(runtimeSummary.openWorkItemCount))}</p>
  <p class="pg-host-v2-detail-copy">Click a node to keep its detail here. Drag nodes directly on the canvas to adjust local layout.</p>
</div>`;
    return;
  }
  detail.innerHTML = `<div class="pg-host-v2-detail-stack">
  <p class="pg-host-v2-detail-kicker">${selectedNodeId === node.id ? 'Selected node' : 'Node'}</p>
  <h4 class="pg-host-v2-detail-title">${escapeHtml(node.label)}</h4>
  <p class="pg-host-v2-detail-meta">kind=${escapeHtml(node.kind)} · status=${escapeHtml(node.status || 'unknown')}</p>
  <p class="pg-host-v2-detail-copy">${escapeHtml(node.summary || 'No summary available.')}</p>
  <div class="pg-host-v2-detail-grid">
    <div><strong>Runtime binding</strong><br>${node.hasRuntimeBinding ? 'Yes' : 'No'}</div>
    <div><strong>Work items</strong><br>${escapeHtml(String(node.workItemIds.length))}</div>
    <div><strong>Group items</strong><br>${escapeHtml(String(node.groupItemIds.length))}</div>
    <div><strong>Tags</strong><br>${escapeHtml(node.tags.length ? node.tags.join(', ') : 'none')}</div>
  </div>
</div>`;
}

function renderEmpty(container: HTMLElement, detail: HTMLElement, message: string): void {
  container.innerHTML = `<div class="pg-host-v2-empty">${escapeHtml(message)}</div>`;
  detail.innerHTML = `<p class="pg-host-v2-detail-empty">${escapeHtml(message)}</p>`;
}

function syncClearSelectionButton(selectedNodeId: string | null): void {
  const button = document.getElementById('pgHostV2ClearSelection');
  if (button instanceof HTMLButtonElement) {
    button.disabled = !selectedNodeId;
  }
}

function updateStatusText(text: string, metrics: SimulationMetrics | null = null): void {
  const target = document.getElementById('pgHostV2EngineStatus');
  if (target instanceof HTMLElement) {
    target.textContent = metrics
      ? `${text} | relation ${formatMetric(computeRelationDelta(metrics))} | move ${formatMetric(metrics.averageMovement)} | alpha ${formatMetric(metrics.alpha)}`
      : text;
  }
}

function formatMetric(value: number): string {
  if (!Number.isFinite(value)) {
    return 'n/a';
  }
  if (Math.abs(value) >= 10) {
    return value.toFixed(1);
  }
  if (Math.abs(value) >= 1) {
    return value.toFixed(2);
  }
  return value.toFixed(3);
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

function readWorkerUri(container: HTMLElement): string {
  const section = container.closest('.pg-host-v2-poc');
  return section instanceof HTMLElement ? section.dataset.pgV2WorkerUri ?? '' : '';
}

function readAutoShakeEnabled(container: HTMLElement): boolean {
  const section = container.closest('.pg-host-v2-poc');
  return !(section instanceof HTMLElement) || section.dataset.pgV2AutoShake !== 'false';
}

async function resolveSimulationWorkerUrl(workerUri: string): Promise<{ url: string; objectUrl: string | null }> {
  if (/^(blob|data):/i.test(workerUri)) {
    return { url: workerUri, objectUrl: null };
  }

  const response = await fetch(workerUri);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  const workerSource = await response.text();
  const blob = new Blob([workerSource], { type: 'text/javascript' });
  const objectUrl = URL.createObjectURL(blob);
  return { url: objectUrl, objectUrl };
}

function formatErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

function loadGraphConfigState(): V2GraphConfigState {
  const vscode = window.__pgHostVsCodeApi;
  const raw = vscode?.getState() as {
    progressGraphV2EngineConfig?: Partial<V2GraphConfigState>;
  } | undefined;
  const persisted = raw?.progressGraphV2EngineConfig;

  return {
    appearance: {
      labelDensity: clampNumber(persisted?.appearance?.labelDensity, 0, 1, defaultGraphConfigState.appearance.labelDensity),
      labelSize: clampNumber(persisted?.appearance?.labelSize, 11, 20, defaultGraphConfigState.appearance.labelSize),
      nodeScale: clampNumber(persisted?.appearance?.nodeScale, 0.75, 1.8, defaultGraphConfigState.appearance.nodeScale),
      edgeScale: clampNumber(persisted?.appearance?.edgeScale, 0.5, 2.2, defaultGraphConfigState.appearance.edgeScale),
    },
    forces: {
      gravity: clampNumber(persisted?.forces?.gravity, forceControlBounds.gravity.min, forceControlBounds.gravity.max, defaultGraphConfigState.forces.gravity),
      repulsion: clampNumber(persisted?.forces?.repulsion, forceControlBounds.repulsion.min, forceControlBounds.repulsion.max, defaultGraphConfigState.forces.repulsion),
      attraction: clampNumber(persisted?.forces?.attraction, forceControlBounds.attraction.min, forceControlBounds.attraction.max, defaultGraphConfigState.forces.attraction),
      linkLength: clampNumber(persisted?.forces?.linkLength, forceControlBounds.linkLength.min, forceControlBounds.linkLength.max, defaultGraphConfigState.forces.linkLength),
    },
    colorGroups: normalizeColorGroups(persisted?.colorGroups),
    ui: {
      configCollapsed: Boolean(persisted?.ui?.configCollapsed ?? defaultGraphConfigState.ui.configCollapsed),
      sidePanelWidth: clampNumber(persisted?.ui?.sidePanelWidth, 280, 620, defaultGraphConfigState.ui.sidePanelWidth),
    },
  };
}

function persistGraphConfigState(configState: V2GraphConfigState): void {
  const vscode = window.__pgHostVsCodeApi;
  if (!vscode) {
    return;
  }
  const current = (vscode.getState() as Record<string, unknown> | undefined) ?? {};
  delete current.v2GraphConfig;
  vscode.setState({
    ...current,
    progressGraphV2EngineConfig: configState,
  });
}

function normalizeColorGroups(value: unknown): V2GraphColorGroup[] {
  if (!Array.isArray(value) || value.length === 0) {
    return defaultGraphConfigState.colorGroups.map((colorGroup) => ({ ...colorGroup }));
  }
  const normalized = value.flatMap((entry, index): V2GraphColorGroup[] => {
    if (!isRecord(entry)) {
      return [];
    }
    return [{
      id: typeof entry.id === 'string' && entry.id ? entry.id : `color-group-${index}`,
      query: typeof entry.query === 'string' ? entry.query : '',
      color: normalizeColorGroupHex(entry.color, pickColorGroupPaletteColor(index)),
      label: typeof entry.label === 'string' ? entry.label : undefined,
      enabled: typeof entry.enabled === 'boolean' ? entry.enabled : undefined,
    }];
  });
  return normalized.length > 0 ? normalized : defaultGraphConfigState.colorGroups.map((colorGroup) => ({ ...colorGroup }));
}

function buildNodeColorMap(
  nodes: ProgressGraphPreviewV2PoCNode[],
  colorGroups: V2GraphColorGroup[],
): Map<string, string> {
  return buildProgressGraphNodeColorMap(nodes, colorGroups);
}

function computeBaseNodeSize(node: ProgressGraphPreviewV2PoCNode): number {
  const statusBoost = node.status === 'in_progress' ? 2 : node.status === 'blocked' ? 1.5 : 0;
  const runtimeBoost = node.hasRuntimeBinding ? 1.5 : 0;
  return Math.round(8 + statusBoost + runtimeBoost);
}

function computeSeedPosition(index: number, total: number): { x: number; y: number } {
  const angle = (index / Math.max(total, 1)) * Math.PI * 2;
  const ring = Math.floor(index / 18);
  const radius = 120 + ring * 90 + (index % 6) * 8;
  return {
    x: Math.cos(angle) * radius,
    y: Math.sin(angle) * radius,
  };
}

function defaultNodeColor(node: ProgressGraphPreviewV2PoCNode): string {
  return defaultProgressGraphNodeColor(node);
}

function createColorGroup(query: string, color: string): V2GraphColorGroup {
  return {
    id: `color-group-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`,
    query,
    color,
  };
}

function normalizeColorGroupHex(value: unknown, fallback: string): string {
  return typeof value === 'string' && /^#[0-9a-f]{6}$/i.test(value) ? value : fallback;
}

function pickColorGroupPaletteColor(index: number): string {
  return colorGroupPalette[index % colorGroupPalette.length];
}

function clampNumber(value: unknown, min: number, max: number, fallback: number): number {
  const candidate = typeof value === 'number' && Number.isFinite(value) ? value : Number(value);
  return Number.isFinite(candidate) ? Math.min(max, Math.max(min, candidate)) : fallback;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
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
