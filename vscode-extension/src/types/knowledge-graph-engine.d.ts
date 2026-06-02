declare module '@note-web/knowledge-graph-engine' {
  export type KnowledgeGraphNode = {
    id: string;
    label?: string;
    kind?: string;
    status?: string;
    radius?: number;
    color?: string;
    stroke?: string;
    accentColor?: string;
    x?: number;
    y?: number;
    z?: number;
    data?: Record<string, unknown>;
    [key: string]: unknown;
  };

  export type KnowledgeGraphLinkInput =
    | [source: string, target: string, kind?: string, id?: string]
    | {
      id?: string;
      source: string;
      target: string;
      kind?: string;
      directed?: boolean;
      data?: Record<string, unknown>;
      [key: string]: unknown;
    };

  export type KnowledgeGraphLink = {
    id: string;
    source: KnowledgeGraphNode;
    sourceId: string;
    target: KnowledgeGraphNode;
    targetId: string;
    kind: string;
    directed?: boolean;
    data: Record<string, unknown>;
  };

  export type NormalizedGraph = {
    nodes: KnowledgeGraphNode[];
    links: Array<{
      id: string;
      source: string;
      target: string;
      kind: string;
      directed?: boolean;
      data: Record<string, unknown>;
      [key: string]: unknown;
    }>;
  };

  export type DisplayOptions = {
    showArrows: boolean;
    textFade: number;
    nodeSize: number;
    linkThickness: number;
  };

  export type LabelPolicy = {
    mode?: 'density' | 'all' | 'none' | 'active-neighborhood';
    density?: number;
    priority?: 'degree' | 'stable' | ((node: KnowledgeGraphNode, context: { degree: number }) => number);
    textFade?: number;
  };

  export type NodeSizePolicy = {
    mode?: 'metric' | 'fixed';
    priority?: 'degree' | 'none' | ((node: KnowledgeGraphNode, context: { degree: number }) => number);
    minScale?: number;
    maxScale?: number;
    strength?: number;
  };

  export type RendererTheme = {
    canvas?: {
      background?: string;
    };
    node?: {
      fill?: string;
      stroke?: string;
      hoverFill?: string;
      hoverStroke?: string;
      selectedFill?: string;
      selectedStroke?: string;
      dimmedFill?: string;
      dimmedStroke?: string;
      accentRingColor?: string;
      accentRingWidth?: number;
      accentByStatus?: Record<string, string>;
    };
    link?: {
      defaultColor?: string;
      activeColor?: string;
      dimmedColor?: string;
      byKind?: Record<string, string>;
    };
    label?: {
      color?: string;
      dimmedColor?: string;
      font?: string;
      fontFamily?: string;
      fontSize?: number;
      fontStyle?: string;
      fontWeight?: string | number;
      density?: number;
    };
  };

  export type GraphViewportOptions = {
    fitPadding?: number;
    minScale?: number;
    maxScale?: number;
    zoomStep?: number;
  };

  export type GraphHitTestOptions = {
    minRadius?: number;
    padding?: number;
  };

  export type GraphStyleFlags = {
    isSelected?: boolean;
    isHovered?: boolean;
    isMatch?: boolean;
    dimmed?: boolean;
    active?: boolean;
    alpha?: number;
  };

  export type GraphNodeStyle = {
    accentColor?: string;
    accentWidth?: number;
    fill?: string;
    stroke?: string;
    strokeWidth?: number;
  };

  export type GraphLinkStyle = {
    color?: string;
    width?: number;
  };

  export type GraphLabelStyle = {
    color?: string;
    font?: string;
  };

  export type GraphRendererHooks = {
    getNodeStyle?: (context: {
      appearance: GraphAppearance;
      flags: GraphStyleFlags;
      node: KnowledgeGraphNode;
      renderer: Canvas2DRenderer;
      style: GraphNodeStyle;
    }) => GraphNodeStyle | void;
    getLinkStyle?: (context: {
      appearance: GraphAppearance;
      flags: GraphStyleFlags;
      link: KnowledgeGraphLink;
      renderer: Canvas2DRenderer;
      style: GraphLinkStyle;
    }) => GraphLinkStyle | void;
    getLabelStyle?: (context: {
      appearance: GraphAppearance;
      flags: GraphStyleFlags;
      node: KnowledgeGraphNode;
      renderer: Canvas2DRenderer;
      style: GraphLabelStyle;
    }) => GraphLabelStyle | void;
  };

  export type GraphAppearance = {
    display?: Partial<DisplayOptions>;
    hitTest?: GraphHitTestOptions;
    hooks?: GraphRendererHooks;
    labelPolicy?: LabelPolicy;
    nodeSizePolicy?: NodeSizePolicy;
    theme?: RendererTheme;
    viewport?: GraphViewportOptions;
  };

  export type GraphInteractionOptions = {
    selectedNodeId?: string | null;
    hoveredNodeId?: string | null;
    selectOnClick?: boolean;
    openOn?: 'legacy' | 'click' | 'double-click' | 'none';
    clearSelectionOnCanvasClick?: boolean;
    hover?: boolean;
    dragNodes?: boolean;
    panCanvas?: boolean;
    zoomCanvas?: boolean;
  };

  export type ResolvedGraphAppearance = {
    label: {
      density: number;
      font: string;
      fontSize: number;
      mode: string;
      textFade: number;
    };
    viewport: {
      maxScale: number;
      minScale: number;
      scale: number;
    };
  };

  export type GraphRendererEvent = {
    type: string;
    node: KnowledgeGraphNode | null;
    nodeId: string | null;
    model: GraphModel;
    renderer: Canvas2DRenderer;
    sourceEvent: Event | null;
    worldPoint: { x: number; y: number } | null;
    viewport: {
      scale: number;
      panX: number;
      panY: number;
    };
  };

  export type GraphNodeDragEvent = GraphRendererEvent & {
    node: KnowledgeGraphNode;
    nodeId: string;
    point: { x: number; y: number };
    alpha: number;
  };

  export type GraphNodeOpenEvent = GraphRendererEvent & {
    node: KnowledgeGraphNode;
    nodeId: string;
    trigger: 'click' | 'double-click';
  };

  export type GraphRendererStatusEvent = GraphRendererEvent & {
    statusText: string;
    resolvedAppearance?: ResolvedGraphAppearance;
  };

  export type GraphRendererEvents = {
    onNodeClick?: (event: GraphRendererEvent) => void;
    onNodeDoubleClick?: (event: GraphRendererEvent & { node: KnowledgeGraphNode; nodeId: string }) => void;
    onNodeSelect?: (event: GraphRendererEvent) => void;
    onNodeHover?: (event: GraphRendererEvent) => void;
    onNodeDrag?: (event: GraphNodeDragEvent) => void;
    onNodeRelease?: (event: GraphRendererEvent & { node: KnowledgeGraphNode; nodeId: string }) => void;
    onNodeOpen?: (event: GraphNodeOpenEvent) => void;
    onStatus?: (event: GraphRendererStatusEvent) => void;
  };

  export type SimulationMetrics = {
    alpha: number;
    averageMovement: number;
    edgeAngleDelta: number;
    edgeLengthDelta: number;
    energy: number;
    maxEdgeAngleDelta: number;
    maxEdgeLengthDelta: number;
    maxMovement: number;
    stopped: boolean;
  };

  export type MotionControl = {
    damp?: number;
    pin?: Array<{ id: string; x: number; y: number }>;
    stop?: boolean;
  };

  export type GraphColorGroup = {
    id: string;
    query: string;
    color: string;
    label?: string;
    enabled?: boolean;
  };

  export type GraphColorQueryNode = KnowledgeGraphNode & {
    summary?: string;
    tags?: string[];
    color?: string;
  };

  export type GraphColorQueryContext = {
    node: GraphColorQueryNode;
    nodeId?: string;
    path?: string;
    file?: string;
    content?: string;
    properties?: Record<string, unknown>;
  };

  export type GraphColorQueryDiagnostic = {
    severity: 'warning' | 'error';
    message: string;
    offset?: number;
  };

  export type GraphColorQueryExpression = Record<string, unknown>;

  export type GraphColorQueryCompileResult = {
    ok: boolean;
    query: string;
    expression: GraphColorQueryExpression;
    diagnostics: GraphColorQueryDiagnostic[];
  };

  export type GraphColorGroupResult = {
    color: string;
    groupId: string | null;
  };

  export const defaultDisplayOptions: DisplayOptions;
  export const defaultGraphAppearance: Required<GraphAppearance>;
  export const defaultInteractionOptions: Required<GraphInteractionOptions>;
  export const defaultRendererTheme: Required<RendererTheme>;

  export function normalizeGraph(graph?: {
    nodes?: KnowledgeGraphNode[];
    links?: KnowledgeGraphLinkInput[];
  }): NormalizedGraph;

  export class GraphModel {
    constructor(rawGraph: {
      nodes?: KnowledgeGraphNode[];
      links?: KnowledgeGraphLinkInput[];
    });
    nodes: KnowledgeGraphNode[];
    links: KnowledgeGraphLink[];
    linkIds: Array<[string, string, string, string?, boolean?, Record<string, unknown>?]>;
    nodeById: Map<string, KnowledgeGraphNode>;
    linkById: Map<string, KnowledgeGraphLink>;
    resetPositions(): void;
    makeWorkerNodes(): Record<string, [number, number]>;
    applyPositions(ids: string[], coords: Float32Array): void;
    highlightedNodes(query: string): Set<KnowledgeGraphNode>;
  }

  export class SimulationClient {
    constructor(options: {
      workerUrl: string | URL;
      model: GraphModel;
      onTick?: (metrics: SimulationMetrics | null) => void;
      onSettled?: (metrics: SimulationMetrics | null) => void;
      motionController?: {
        onTick?: (metrics: SimulationMetrics | null) => MotionControl | void;
      };
      WorkerClass?: typeof Worker;
    });
    start(forces: Record<string, number>, alpha?: number): void;
    updateForces(forces: Record<string, number>, alpha?: number): void;
    stop(): void;
    pinNode(id: string, point: { x: number; y: number }, alpha?: number): void;
    releaseNode(id: string, alpha?: number): void;
    dispose(): void;
  }

  export function createSimulationClient(options: ConstructorParameters<typeof SimulationClient>[0]): SimulationClient;

  export function resolveCanvasFont(labelTheme?: RendererTheme['label']): string;

  export function compileColorGroupQuery(
    query: string,
    options?: {
      defaultCaseMode?: 'ignore-case' | 'match-case';
    },
  ): GraphColorQueryCompileResult;

  export function evaluateColorGroupQuery(
    compiled: GraphColorQueryCompileResult | GraphColorQueryExpression | string,
    context: GraphColorQueryContext,
    options?: {
      defaultCaseMode?: 'ignore-case' | 'match-case';
    },
  ): boolean;

  export function resolveColorGroupColor(
    context: GraphColorQueryContext,
    colorGroups?: GraphColorGroup[],
    options?: {
      fallbackColor?: string | ((context: GraphColorQueryContext) => string);
      defaultCaseMode?: 'ignore-case' | 'match-case';
    },
  ): GraphColorGroupResult;

  export function applyColorGroupsToGraph<TNode extends GraphColorQueryNode, TGraph extends { nodes?: TNode[] }>(
    graph: TGraph,
    colorGroups?: GraphColorGroup[],
    options?: {
      fallbackColor?: string | ((context: GraphColorQueryContext) => string);
      getContext?: (node: TNode) => GraphColorQueryContext;
    },
  ): TGraph & {
    nodes: Array<TNode & { color: string; colorGroupId: string | null }>;
    matches: Map<string, GraphColorGroupResult>;
  };

  export class Canvas2DRenderer {
    constructor(options: {
      canvas: HTMLCanvasElement;
      model: GraphModel;
      appearance?: GraphAppearance;
      events?: GraphRendererEvents;
      getAppearance?: () => GraphAppearance;
      getQuery?: () => string;
      getDisplayOptions?: () => Partial<DisplayOptions>;
      getHighlightedLinks?: (
        activeNodeId: string,
        context: { model: GraphModel; node: KnowledgeGraphNode },
      ) => Iterable<string | KnowledgeGraphLink> | null | undefined;
      getHighlightedNodes?: (
        activeNodeId: string,
        context: { model: GraphModel; node: KnowledgeGraphNode },
      ) => Iterable<string | KnowledgeGraphNode> | null | undefined;
      getTheme?: () => RendererTheme;
      hoveredNodeId?: string | null;
      interaction?: GraphInteractionOptions;
      selectedNodeId?: string | null;
      theme?: RendererTheme;
      onNodeClick?: (node: KnowledgeGraphNode | null, event: PointerEvent) => void;
      onNodeDoubleClick?: (node: KnowledgeGraphNode, event: MouseEvent) => void;
      onNodeDrag?: (node: KnowledgeGraphNode, point: { x: number; y: number }, alpha: number) => void;
      onNodeHover?: (node: KnowledgeGraphNode | null, event: PointerEvent) => void;
      onNodeOpen?: (node: KnowledgeGraphNode, event: MouseEvent | PointerEvent) => void;
      onNodeRelease?: (node: KnowledgeGraphNode) => void;
      onNodeSelect?: (node: KnowledgeGraphNode | null, event: PointerEvent) => void;
      onStatus?: (text: string) => void;
    });
    render(): void;
    resize(): void;
    getResolvedAppearance(): ResolvedGraphAppearance;
    resetZoom(options?: { padding?: number; minScale?: number; maxScale?: number }): boolean;
    setInteractionState(
      state?: { selectedNodeId?: string | null; hoveredNodeId?: string | null },
      options?: { render?: boolean },
    ): void;
    dispose(): void;
  }
}
