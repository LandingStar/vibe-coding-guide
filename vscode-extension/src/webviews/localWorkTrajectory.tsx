/// <reference lib="dom" />

import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Background,
  Controls,
  Handle,
  MarkerType,
  MiniMap,
  Position,
  ReactFlow,
  ReactFlowProvider,
  useReactFlow,
  type Edge,
  type Node,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import './localWorkTrajectory.css';

type TrajectoryLane = {
  id: string;
  label: string;
  status: string;
  summary: string;
  metadata: Record<string, string>;
};

type TrajectoryEvent = {
  id: string;
  laneId: string;
  title: string;
  kind: string;
  status: string;
  order: number;
  summary: string;
  metadata: Record<string, string>;
};

type TrajectoryRelation = {
  sourceEventId: string;
  targetEventId: string;
  kind: string;
  summary: string;
  metadata: Record<string, string>;
};

type LocalWorkTrajectory = {
  trajectoryId: string;
  title: string;
  recordedAt: string | null;
  sourceGraphId: string | null;
  sourceNodeId: string | null;
  guideContext: string | null;
  metadata: Record<string, string>;
  lanes: TrajectoryLane[];
  events: TrajectoryEvent[];
  relations: TrajectoryRelation[];
  childTrajectories?: LocalWorkTrajectory[];
};

type LayoutState = {
  nodes: Node[];
  edges: Edge[];
  mode: 'pending' | 'lanes' | 'fallback';
  message: string;
  activeEventId: string | null;
  focusEventId: string | null;
  fitMode: 'all' | 'focus';
};

type LaneOrderControls = {
  onMoveLaneUp: (laneId: string) => void;
  onMoveLaneDown: (laneId: string) => void;
  canMoveLaneUp: (laneId: string) => boolean;
  canMoveLaneDown: (laneId: string) => boolean;
};

type PreparedFlowElements = {
  nodes: Node[];
  edges: Edge[];
  activeEventId: string | null;
  focusEventId: string | null;
};

type LaneEventMap = Map<string, TrajectoryEvent[]>;

type RelationBadge = {
  label: string;
  title: string;
  external?: boolean;
  tone?: 'source' | 'target' | 'external';
};

type TrajectoryDetail = {
  event: TrajectoryEvent | null;
  lane: TrajectoryLane | null;
  childTrajectory: LocalWorkTrajectory | null;
  externalRelianceIndicators: ExternalRelianceIndicator[];
  dependencyProxy: DependencyProxy | null;
  relation: TrajectoryRelation | null;
  relationSourceEvent: TrajectoryEvent | null;
  relationTargetEvent: TrajectoryEvent | null;
  relationSourceEndpointChild: LocalWorkTrajectory | null;
  relationTargetEndpointChild: LocalWorkTrajectory | null;
};

type EndpointTarget = {
  trajectory: LocalWorkTrajectory;
  eventId: string;
};

type RelationTarget = {
  trajectory: LocalWorkTrajectory;
  relationId: string;
};

type PendingEndpointSelection = {
  trajectoryId: string;
  eventId: string;
};

type PendingRelationSelection = {
  trajectoryId: string;
  relationId: string;
};

type ExternalRelianceIndicator = {
  relation: TrajectoryRelation;
  relationId: string;
  ownerTrajectory: LocalWorkTrajectory;
  endpointRole: 'source' | 'target';
  endpointEventId: string;
};

type DependencyProxy = {
  id: string;
  relation: TrajectoryRelation;
  relationId: string;
  ownerTrajectory: LocalWorkTrajectory;
  dependentEventId: string;
  dependentEvent: TrajectoryEvent;
  sourceEndpointTrajectoryId: string;
  sourceEndpointEventId: string;
  sourceEndpointParentEventId: string;
  sourceEndpointCompoundPath: string;
  sourceEndpointTrajectory: LocalWorkTrajectory | null;
  sourceEndpointEvent: TrajectoryEvent | null;
  origin: 'local-relation' | 'external-reliance';
};

type DependencyProxyPlacement = {
  proxy: DependencyProxy;
  side: 'top' | 'bottom';
  stackIndex: number;
  laneIndex: number;
  eventColumn: number;
};

type LaneOpeningFanout = {
  sourceEventId: string;
  relations: TrajectoryRelation[];
  sourceColumn: number;
  targetColumns: number[];
  sourceLaneIndex: number;
  targetLaneIndexes: number[];
};

type NavigationSnapshot = {
  trajectoryStack: LocalWorkTrajectory[];
  selectedEventId: string | null;
  selectedRelationId: string | null;
  selectedProxyId: string | null;
};

const nodeWidth = 190;
const nodeHeight = 82;
const dependencyProxyWidth = 164;
const dependencyProxyHeight = 58;
const dependencyProxyGap = 14;
const dependencyProxyOffset = 38;
const laneOpeningJunctionSize = 18;
const laneLabelWidth = 170;
const laneLabelHeight = 54;
const laneStartX = 0;
const laneStartY = 0;
const laneStrideY = 188;
const eventStartX = laneLabelWidth + 96;
const eventStrideX = nodeWidth + 70;
const fullFitNodeLimit = 12;
const fullFitTargetWidth = 540;
const fullFitTargetHeight = 430;
const maxVisibleBadges = 4;
const maxColumnConstraintPasses = 80;
const alignmentRelationKinds = new Set([
  'merges_into',
  'proposes_new_line',
  'approves_new_line',
]);
const laneOpeningRelationKinds = new Set([
  'proposes_new_line',
  'approves_new_line',
]);
const auxiliaryRelationKinds = new Set([
  'depends_on',
  'waits_for',
  'unblocks',
  'hands_off',
  'syncs_from',
  'proposes_new_line',
  'approves_new_line',
]);
const relianceRelationKinds = new Set([
  'depends_on',
  'waits_for',
  'syncs_from',
]);
const relationWeightedLaneOrderKinds = new Set([
  'depends_on',
  'waits_for',
  'unblocks',
  'hands_off',
  'syncs_from',
  'merges_into',
  'proposes_new_line',
  'approves_new_line',
]);
const relianceTopSourceHandle = 'reliance-top-source';
const relianceTopTargetHandle = 'reliance-top-target';
const relianceBottomSourceHandle = 'reliance-bottom-source';
const relianceBottomTargetHandle = 'reliance-bottom-target';
const dependencyProxyTopSourceHandle = 'dependency-proxy-top-source';
const dependencyProxyBottomSourceHandle = 'dependency-proxy-bottom-source';
const mainFlowSourceHandle = 'main-flow-source';
const mainFlowTargetHandle = 'main-flow-target';
const fanoutTopSourceHandle = 'fanout-top-source';
const fanoutTopTargetHandle = 'fanout-top-target';
const fanoutBottomSourceHandle = 'fanout-bottom-source';
const fanoutBottomTargetHandle = 'fanout-bottom-target';
const relationEdgeIdPrefix = 'relation:';
type TrajectoryVisualLayerKind = 'node' | 'edge';
type TrajectoryNodeVisualLayerId =
  | 'lane'
  | 'event'
  | 'laneOpeningJunction'
  | 'compound'
  | 'compoundProxy'
  | 'dependencyProxy'
  | 'statusAttention'
  | 'active'
  | 'selected';
type TrajectoryEdgeVisualLayerId =
  | 'sequence'
  | 'laneOpening'
  | 'merge'
  | 'relianceOverlay'
  | 'dependencyProxy'
  | 'relation';
type TrajectoryVisualLayerIdByKind = {
  node: TrajectoryNodeVisualLayerId;
  edge: TrajectoryEdgeVisualLayerId;
};
type TrajectoryVisualLayerDescriptor<Kind extends TrajectoryVisualLayerKind = TrajectoryVisualLayerKind> = {
  kind: Kind;
  id: string;
  className: string;
  zIndex: number;
};
type TrajectoryVisualLayerRegistration<Kind extends TrajectoryVisualLayerKind = TrajectoryVisualLayerKind> = {
  kind: Kind;
  id: string;
  zIndex: number;
  className?: string;
};
type TrajectoryLayerStyle = React.CSSProperties & {
  '--pg-lwt-layer-z'?: number;
};
type TrajectoryVisualLayerView = {
  className: string;
  style: TrajectoryLayerStyle;
};
type TrajectoryVisualLayerRegistry = {
  node: Map<string, TrajectoryVisualLayerDescriptor<'node'>>;
  edge: Map<string, TrajectoryVisualLayerDescriptor<'edge'>>;
};

const trajectoryVisualLayers = createDefaultTrajectoryVisualLayerRegistry();

function main(): void {
  const mounts = document.querySelectorAll<HTMLElement>('[data-pg-trajectory-payload-id]');
  if (mounts.length > 0) {
    for (const mount of mounts) {
      mountTrajectory(mount);
    }
    return;
  }
  const mount = document.getElementById('pgHostLocalWorkTrajectoryRoot');
  if (!(mount instanceof HTMLElement)) {
    return;
  }
  mountTrajectory(mount);
}

function mountTrajectory(mount: HTMLElement): void {
  const payload = readPayload(mount.dataset.pgTrajectoryPayloadId || 'pgHostLocalWorkTrajectoryPayload');
  const error = mount.dataset.pgTrajectoryError || '';
  createRoot(mount).render(
    <React.StrictMode>
      <TrajectoryApp trajectory={payload} error={error} />
    </React.StrictMode>,
  );
}

function readPayload(payloadElementId: string): LocalWorkTrajectory | null {
  const element = document.getElementById(payloadElementId);
  if (!element?.textContent) {
    return null;
  }
  try {
    return JSON.parse(element.textContent) as LocalWorkTrajectory;
  } catch {
    return null;
  }
}

function createDefaultTrajectoryVisualLayerRegistry(): TrajectoryVisualLayerRegistry {
  return createTrajectoryVisualLayerRegistry([
    { kind: 'node', id: 'lane', zIndex: 2 },
    { kind: 'node', id: 'event', zIndex: 4 },
    { kind: 'node', id: 'laneOpeningJunction', zIndex: 5 },
    { kind: 'node', id: 'compoundProxy', zIndex: 5 },
    { kind: 'node', id: 'compound', zIndex: 6 },
    { kind: 'node', id: 'dependencyProxy', zIndex: 7 },
    { kind: 'node', id: 'statusAttention', zIndex: 7 },
    { kind: 'node', id: 'active', zIndex: 8 },
    { kind: 'node', id: 'selected', zIndex: 9 },
    { kind: 'edge', id: 'sequence', zIndex: 2 },
    { kind: 'edge', id: 'relianceOverlay', zIndex: 4 },
    { kind: 'edge', id: 'dependencyProxy', zIndex: 5 },
    { kind: 'edge', id: 'laneOpening', zIndex: 5 },
    { kind: 'edge', id: 'merge', zIndex: 6 },
    { kind: 'edge', id: 'relation', zIndex: 5 },
  ]);
}

function createTrajectoryVisualLayerRegistry(
  registrations: readonly TrajectoryVisualLayerRegistration[] = [],
): TrajectoryVisualLayerRegistry {
  const registry: TrajectoryVisualLayerRegistry = {
    node: new Map(),
    edge: new Map(),
  };
  for (const registration of registrations) {
    registerTrajectoryVisualLayer(registry, registration);
  }
  return registry;
}

function registerTrajectoryVisualLayer<Kind extends TrajectoryVisualLayerKind>(
  registry: TrajectoryVisualLayerRegistry,
  registration: TrajectoryVisualLayerRegistration<Kind>,
): TrajectoryVisualLayerDescriptor<Kind> {
  const descriptor: TrajectoryVisualLayerDescriptor<Kind> = {
    kind: registration.kind,
    id: registration.id,
    className: registration.className ?? `pg-lwt-layer-${registration.kind}-${normalizeVisualLayerClassId(registration.id)}`,
    zIndex: registration.zIndex,
  };
  registry[registration.kind].set(registration.id, descriptor as TrajectoryVisualLayerDescriptor<'node'> & TrajectoryVisualLayerDescriptor<'edge'>);
  return descriptor;
}

function resolveTrajectoryVisualLayer<Kind extends TrajectoryVisualLayerKind>(
  registry: TrajectoryVisualLayerRegistry,
  kind: Kind,
  id: string,
  owner: string,
): TrajectoryVisualLayerView {
  const layers = registry[kind] as Map<string, TrajectoryVisualLayerDescriptor<Kind>>;
  const layer = layers.get(id);
  if (!layer) {
    const knownLayerIds = Array.from(layers.keys()).join(', ') || '(none)';
    throw new Error(
      [
        `Unknown Local Work Trajectory ${kind} visual layer "${id}" requested by ${owner}.`,
        `Known ${kind} layers: ${knownLayerIds}.`,
        'Register the missing layer in createDefaultTrajectoryVisualLayerRegistry() before using it in a node or edge builder.',
      ].join(' '),
    );
  }
  return {
    className: layer.className,
    style: {
      '--pg-lwt-layer-z': layer.zIndex,
    },
  };
}

function nodeVisualLayer(
  id: TrajectoryNodeVisualLayerId | string,
  owner: string,
): TrajectoryVisualLayerView {
  return resolveTrajectoryVisualLayer(trajectoryVisualLayers, 'node', id, owner);
}

function edgeVisualLayer(
  id: TrajectoryEdgeVisualLayerId | string,
  owner: string,
): TrajectoryVisualLayerView {
  return resolveTrajectoryVisualLayer(trajectoryVisualLayers, 'edge', id, owner);
}

function normalizeVisualLayerClassId(id: string): string {
  return normalizeStatus(id.replace(/([a-z0-9])([A-Z])/g, '$1-$2'));
}

function mergedLayerStyle(
  layer: TrajectoryVisualLayerView,
  style: React.CSSProperties,
): TrajectoryLayerStyle {
  return {
    ...style,
    ...layer.style,
  };
}

function layeredNodeClassNames(
  layer: TrajectoryVisualLayerView,
  classNames: string[],
): string {
  return [
    layer.className,
    ...classNames,
  ].filter(Boolean).join(' ');
}

function layeredEdgeClassNames(
  layer: TrajectoryVisualLayerView,
  classNames: string[],
): string {
  return [
    layer.className,
    ...classNames,
  ].filter(Boolean).join(' ');
}

function TrajectoryApp({
  trajectory,
  error,
}: {
  trajectory: LocalWorkTrajectory | null;
  error: string;
}): React.ReactElement {
  const [trajectoryStack, setTrajectoryStack] = useState<LocalWorkTrajectory[]>([]);
  const currentTrajectory = trajectoryStack.at(-1) ?? trajectory;
  const childTrajectoryById = useMemo(
    () => buildChildTrajectoryIndex(trajectory),
    [trajectory],
  );
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [selectedRelationId, setSelectedRelationId] = useState<string | null>(null);
  const [selectedProxyId, setSelectedProxyId] = useState<string | null>(null);
  const [navigationHistory, setNavigationHistory] = useState<NavigationSnapshot[]>([]);
  const [laneOrderOverride, setLaneOrderOverride] = useState<string[] | null>(null);
  const [pendingSelectedEventId, setPendingSelectedEventId] = useState<PendingEndpointSelection | null>(null);
  const [pendingSelectedRelationId, setPendingSelectedRelationId] = useState<PendingRelationSelection | null>(null);
  useEffect(() => {
    setTrajectoryStack([]);
    setSelectedEventId(null);
    setSelectedRelationId(null);
    setSelectedProxyId(null);
    setNavigationHistory([]);
    setLaneOrderOverride(null);
    setPendingSelectedEventId(null);
    setPendingSelectedRelationId(null);
  }, [trajectory]);
  const [layout, setLayout] = useState<LayoutState>(emptyLayout('pending', 'Building trajectory layout...'));
  const lanes = currentTrajectory?.lanes ?? [];
  const events = currentTrajectory?.events ?? [];
  const relations = currentTrajectory?.relations ?? [];
  const externalRelianceByEventId = useMemo(
    () => buildExternalRelianceByEventId(trajectory, currentTrajectory),
    [currentTrajectory, trajectory],
  );
  const dependencyProxies = useMemo(
    () => buildDependencyProxies(trajectory, currentTrajectory, relations, events, childTrajectoryById),
    [childTrajectoryById, currentTrajectory, events, relations, trajectory],
  );
  const hasLane = lanes.length > 0;
  const isEmptyLifecycle = Boolean(
    currentTrajectory
    && !hasLane
    && currentTrajectory.metadata?.projection === 'single-lane-lifecycle'
    && currentTrajectory.metadata?.lifecycle_state === 'empty',
  );
  const selectedDetail = useMemo(
    () => buildSelectedDetail(
      selectedEventId,
      selectedRelationId,
      selectedProxyId,
      trajectory,
      currentTrajectory,
      lanes,
      events,
      relations,
      childTrajectoryById,
      externalRelianceByEventId,
      dependencyProxies,
    ),
    [
      childTrajectoryById,
      currentTrajectory,
      events,
      externalRelianceByEventId,
      dependencyProxies,
      lanes,
      relations,
      selectedEventId,
      selectedProxyId,
      selectedRelationId,
      trajectory,
    ],
  );

  useEffect(() => {
    if (!pendingSelectedEventId) {
      return;
    }
    if (currentTrajectory?.trajectoryId === pendingSelectedEventId.trajectoryId) {
      setSelectedEventId(pendingSelectedEventId.eventId);
      setSelectedRelationId(null);
      setSelectedProxyId(null);
      setPendingSelectedEventId(null);
    }
  }, [currentTrajectory?.trajectoryId, pendingSelectedEventId]);

  useEffect(() => {
    if (!pendingSelectedRelationId) {
      return;
    }
    if (currentTrajectory?.trajectoryId === pendingSelectedRelationId.trajectoryId) {
      setSelectedEventId(null);
      setSelectedRelationId(pendingSelectedRelationId.relationId);
      setSelectedProxyId(null);
      setPendingSelectedRelationId(null);
    }
  }, [currentTrajectory?.trajectoryId, pendingSelectedRelationId]);

  useEffect(() => {
    setLaneOrderOverride(null);
  }, [currentTrajectory?.trajectoryId]);

  const manualLaneOrder = useMemo(
    () => (laneOrderOverride ? applyLaneOrderOverride(lanes, laneOrderOverride) : null),
    [laneOrderOverride, lanes],
  );
  const orderedLaneIdsForControls = useMemo(
    () => (manualLaneOrder ?? orderLanes(currentTrajectory, lanes, events, relations)).map((lane) => lane.id),
    [currentTrajectory, events, lanes, manualLaneOrder, relations],
  );
  const laneOrderControls = useMemo<LaneOrderControls>(() => ({
    onMoveLaneUp: (laneId: string) => {
      setLaneOrderOverride((current) => moveLaneInOrder(
        applyLaneOrderOverride(lanes, current ?? orderedLaneIdsForControls),
        laneId,
        -1,
      ));
    },
    onMoveLaneDown: (laneId: string) => {
      setLaneOrderOverride((current) => moveLaneInOrder(
        applyLaneOrderOverride(lanes, current ?? orderedLaneIdsForControls),
        laneId,
        1,
      ));
    },
    canMoveLaneUp: (laneId: string) => orderedLaneIdsForControls.indexOf(laneId) > 0,
    canMoveLaneDown: (laneId: string) => {
      const index = orderedLaneIdsForControls.indexOf(laneId);
      return index >= 0 && index < orderedLaneIdsForControls.length - 1;
    },
  }), [lanes, orderedLaneIdsForControls]);

  useEffect(() => {
    if (!currentTrajectory || !hasLane) {
      setLayout(emptyLayout('pending', 'No trajectory payload is available.'));
      return;
    }
    try {
      setLayout(buildLayout(
        lanes,
        events,
        relations,
        externalRelianceByEventId,
        dependencyProxies,
        currentTrajectory,
        manualLaneOrder,
        laneOrderOverride ? 'manual' : 'weighted',
        laneOrderControls,
      ));
    } catch (layoutError) {
      setLayout(buildFallbackLayout(
        lanes,
        events,
        relations,
        externalRelianceByEventId,
        dependencyProxies,
        formatErrorMessage(layoutError),
        currentTrajectory,
        manualLaneOrder,
        laneOrderOverride ? 'manual' : 'weighted',
        laneOrderControls,
      ));
    }
  }, [
    currentTrajectory,
    dependencyProxies,
    externalRelianceByEventId,
    hasLane,
    lanes,
    events,
    relations,
    manualLaneOrder,
    laneOrderControls,
    laneOrderOverride,
  ]);

  const metrics = useMemo(() => {
    return {
      lanes: lanes.length,
      events: events.length,
      relations: relations.length,
      childTrajectories: currentTrajectory?.childTrajectories?.length ?? 0,
    };
  }, [lanes.length, events.length, relations.length, currentTrajectory?.childTrajectories?.length]);

  const breadcrumbItems = useMemo(() => {
    if (!trajectory) {
      return [];
    }
    return [trajectory, ...trajectoryStack];
  }, [trajectory, trajectoryStack]);

  const currentNavigationSnapshot = (): NavigationSnapshot => ({
    trajectoryStack,
    selectedEventId,
    selectedRelationId,
    selectedProxyId,
  });

  const pushNavigationHistory = (): void => {
    setNavigationHistory((current) => [...current, currentNavigationSnapshot()]);
  };

  const clearSelection = (): void => {
    setSelectedEventId(null);
    setSelectedRelationId(null);
    setSelectedProxyId(null);
    setPendingSelectedEventId(null);
    setPendingSelectedRelationId(null);
  };

  const handleEnterChild = (childTrajectory: LocalWorkTrajectory): void => {
    pushNavigationHistory();
    clearSelection();
    setTrajectoryStack((current) => [...current, childTrajectory]);
  };

  const handleJumpToEndpoint = (target: EndpointTarget): void => {
    pushNavigationHistory();
    if (currentTrajectory?.trajectoryId === target.trajectory.trajectoryId) {
      setSelectedRelationId(null);
      setSelectedProxyId(null);
      setSelectedEventId(target.eventId);
      return;
    }
    setPendingSelectedEventId({
      trajectoryId: target.trajectory.trajectoryId,
      eventId: target.eventId,
    });
    setTrajectoryStack((current) => {
      if (!trajectory) {
        return current;
      }
      const path = findTrajectoryPath(trajectory, target.trajectory.trajectoryId);
      return path.length > 1 ? path.slice(1) : [];
    });
    setSelectedRelationId(null);
    setSelectedProxyId(null);
    setSelectedEventId(null);
  };

  const handleOpenRelation = (target: RelationTarget): void => {
    pushNavigationHistory();
    if (currentTrajectory?.trajectoryId !== target.trajectory.trajectoryId) {
      setPendingSelectedRelationId({
        trajectoryId: target.trajectory.trajectoryId,
        relationId: target.relationId,
      });
      setTrajectoryStack((current) => {
        if (!trajectory) {
          return current;
        }
        const path = findTrajectoryPath(trajectory, target.trajectory.trajectoryId);
        return path.length > 1 ? path.slice(1) : [];
      });
      setPendingSelectedEventId(null);
      setSelectedEventId(null);
      setSelectedProxyId(null);
      setSelectedRelationId(null);
      return;
    }
    setPendingSelectedEventId(null);
    setPendingSelectedRelationId(null);
    setSelectedEventId(null);
    setSelectedProxyId(null);
    setSelectedRelationId(target.relationId);
  };

  const handleBreadcrumbNavigate = (index: number): void => {
    pushNavigationHistory();
    if (index <= 0) {
      setTrajectoryStack([]);
      setSelectedEventId(null);
      setSelectedRelationId(null);
      setSelectedProxyId(null);
      setPendingSelectedEventId(null);
      setPendingSelectedRelationId(null);
      return;
    }
    setTrajectoryStack((current) => current.slice(0, index));
    setSelectedEventId(null);
    setSelectedRelationId(null);
    setSelectedProxyId(null);
    setPendingSelectedEventId(null);
    setPendingSelectedRelationId(null);
  };

  const handleBack = (): void => {
    setNavigationHistory((current) => {
      const previous = current.at(-1);
      if (!previous) {
        return current;
      }
      setTrajectoryStack(previous.trajectoryStack);
      setSelectedEventId(previous.selectedEventId);
      setSelectedRelationId(previous.selectedRelationId);
      setSelectedProxyId(previous.selectedProxyId);
      setPendingSelectedEventId(null);
      setPendingSelectedRelationId(null);
      return current.slice(0, -1);
    });
  };

  if (error) {
    return (
      <Shell status="failed" title="局部工作轨迹加载失败" subtitle={error}>
        <p className="pg-lwt-empty">修复 local-work-trajectory artifact 后刷新预览。</p>
      </Shell>
    );
  }

  if (isEmptyLifecycle) {
    return (
      <Shell status="empty" title={currentTrajectory?.title ?? 'Local Work Trajectory'} subtitle="No local trajectory has been started in this workspace.">
        <p className="pg-lwt-empty">The agent will create the first lane and active event when it starts a tracked task.</p>
      </Shell>
    );
  }

  if (!currentTrajectory || !hasLane) {
    return (
      <Shell status="unavailable" title="局部工作轨迹未就绪" subtitle="等待 local-work-trajectory artifact 生成。">
        <p className="pg-lwt-empty">刷新 progress graph 后会先生成单线轨迹 artifact。</p>
      </Shell>
    );
  }

  return (
    <Shell
      status="available"
      title={currentTrajectory.title}
      subtitle={`trajectory_id=${currentTrajectory.trajectoryId} · guide=${currentTrajectory.guideContext ?? 'unknown'} · recorded_at=${formatTimestamp(currentTrajectory.recordedAt)}`}
      metrics={[
        ['Mode', 'React Flow lanes'],
        ['Layout', layout.mode],
        ['Lanes', String(metrics.lanes)],
        ['Events', String(metrics.events)],
        ['Relations', String(metrics.relations)],
        ['Compounds', String(metrics.childTrajectories)],
      ]}
    >
      <TrajectoryBreadcrumb
        items={breadcrumbItems}
        canGoBack={navigationHistory.length > 0}
        canGoUp={breadcrumbItems.length > 1}
        onBack={handleBack}
        onGoUp={() => {
          if (trajectoryStack.length === 0) {
            return;
          }
          pushNavigationHistory();
          clearSelection();
          setTrajectoryStack((current) => current.slice(0, -1));
        }}
        onNavigate={handleBreadcrumbNavigate}
      />
      <div className="pg-lwt-workspace">
        <div className="pg-lwt-flow" aria-label="Local work trajectory graph">
          <ReactFlowProvider>
            <TrajectoryFlow
              layout={layout}
              selectedEventId={selectedEventId}
              selectedRelationId={selectedRelationId}
              selectedProxyId={selectedProxyId}
              onSelectEvent={(eventId) => {
                setSelectedEventId(eventId);
                setSelectedRelationId(null);
                setSelectedProxyId(null);
              }}
              onSelectRelation={(relationId) => {
                setSelectedRelationId(relationId);
                setSelectedEventId(null);
                setSelectedProxyId(null);
              }}
              onSelectProxy={(proxyId) => {
                setSelectedProxyId(proxyId);
                setSelectedEventId(null);
                setSelectedRelationId(null);
              }}
            />
          </ReactFlowProvider>
        </div>
        <TrajectoryDetailPanel
          detail={selectedDetail}
          onEnterChild={handleEnterChild}
          onJumpToEndpoint={handleJumpToEndpoint}
          onOpenRelation={handleOpenRelation}
        />
      </div>
    </Shell>
  );
}

function TrajectoryFlow({
  layout,
  selectedEventId,
  selectedRelationId,
  selectedProxyId,
  onSelectEvent,
  onSelectRelation,
  onSelectProxy,
}: {
  layout: LayoutState;
  selectedEventId: string | null;
  selectedRelationId: string | null;
  selectedProxyId: string | null;
  onSelectEvent: (eventId: string | null) => void;
  onSelectRelation: (relationId: string | null) => void;
  onSelectProxy: (proxyId: string | null) => void;
}): React.ReactElement {
  const { setViewport } = useReactFlow();
  const shouldFitEntireGraph = (
    layout.fitMode === 'all'
    || (layout.mode === 'lanes' && layout.nodes.length <= fullFitNodeLimit)
  );
  const activeNode = layout.activeEventId
    ? layout.nodes.find((node) => node.id === layout.activeEventId)
    : layout.focusEventId
      ? layout.nodes.find((node) => node.id === layout.focusEventId)
    : undefined;
  const initialViewport = shouldFitEntireGraph
    ? buildTopAlignedViewport(layout.nodes, activeNode)
    : buildFocusedViewport(activeNode);
  const [isMiniMapCollapsed, setIsMiniMapCollapsed] = useState(false);

  useEffect(() => {
    if (layout.nodes.length === 0) {
      return;
    }
    const frame = window.requestAnimationFrame(() => {
      if (shouldFitEntireGraph) {
        setViewport(buildTopAlignedViewport(layout.nodes, activeNode), { duration: 0 });
        return;
      }
      setViewport(buildFocusedViewport(activeNode), { duration: 180 });
    });
    return () => {
      window.cancelAnimationFrame(frame);
    };
  }, [activeNode, layout.activeEventId, layout.edges.length, layout.nodes, layout.nodes.length, setViewport, shouldFitEntireGraph]);

  return (
    <>
      <ReactFlow
        nodes={layout.nodes.map((node) => ({
          ...node,
          selected: node.id === selectedEventId || node.id === selectedProxyId,
          className: trajectoryNodeClassNameForSelection(node, selectedEventId, selectedProxyId, layout.nodes),
          style: trajectoryNodeStyleForSelection(node, selectedEventId, selectedProxyId),
        }))}
        edges={layout.edges.map((edge) => ({
          ...edge,
          selected: isRelationEdge(edge)
            ? relationIdFromEdgeId(edge.id) === selectedRelationId
            : edge.id === selectedRelationId,
        }))}
        fitView={false}
        defaultViewport={initialViewport}
        minZoom={0.01}
        maxZoom={1.8}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable
        proOptions={{ hideAttribution: true }}
        onNodeClick={(_, node) => {
          if (isDependencyProxyNode(node)) {
            onSelectProxy(node.id);
            return;
          }
          onSelectEvent(isEventNode(node) ? node.id : null);
        }}
        onEdgeClick={(_, edge) => {
          onSelectRelation(isRelationEdge(edge) ? relationIdFromEdgeId(edge.id) : null);
        }}
        onPaneClick={() => {
          onSelectEvent(null);
          onSelectRelation(null);
          onSelectProxy(null);
        }}
      >
        <Background color="rgba(70, 95, 116, 0.16)" gap={22} />
        {isMiniMapCollapsed ? null : (
          <MiniMap
            pannable
            zoomable
            width={190}
            height={128}
            bgColor="rgba(255, 250, 240, 0.96)"
            nodeBorderRadius={4}
            nodeStrokeWidth={1}
            nodeStrokeColor={(node) => (node.id.startsWith('lane:') ? '#254b65' : '#51677a')}
            nodeColor={(node) => {
              if (node.id === layout.activeEventId) {
                return '#4d95d8';
              }
              const status = typeof node.data?.status === 'string' ? node.data.status : '';
              if (status === 'blocked') {
                return '#c75f5f';
              }
              if (status === 'waiting') {
                return '#b88a2e';
              }
              if (status === 'done' || status === 'completed') {
                return '#4f936f';
              }
              if (status === 'archived') {
                return '#9aa6b2';
              }
              return node.id.startsWith('lane:') ? '#315f7e' : '#9eb7ca';
            }}
            maskColor="rgba(247, 243, 235, 0.72)"
            maskStrokeColor="rgba(49, 95, 126, 0.46)"
            maskStrokeWidth={1}
          />
        )}
        <Controls showInteractive={false} />
      </ReactFlow>
      <button
        type="button"
        className="pg-lwt-minimap-toggle"
        aria-expanded={!isMiniMapCollapsed}
        data-pg-minimap-collapsed={isMiniMapCollapsed ? 'true' : 'false'}
        onClick={() => {
          setIsMiniMapCollapsed((current) => !current);
        }}
      >
        {isMiniMapCollapsed ? 'Show map' : 'Hide map'}
      </button>
      {layout.message ? (
        <div className="pg-lwt-layout-note" data-pg-lwt-layout-mode={layout.mode}>{layout.message}</div>
      ) : null}
    </>
  );
}

function TrajectoryBreadcrumb({
  items,
  canGoBack,
  canGoUp,
  onBack,
  onGoUp,
  onNavigate,
}: {
  items: LocalWorkTrajectory[];
  canGoBack: boolean;
  canGoUp: boolean;
  onBack: () => void;
  onGoUp: () => void;
  onNavigate: (index: number) => void;
}): React.ReactElement | null {
  if (items.length === 0 && !canGoBack && !canGoUp) {
    return null;
  }
  return (
    <nav className="pg-lwt-breadcrumb" aria-label="Trajectory breadcrumb">
      <button
        type="button"
        className="pg-lwt-breadcrumb-back"
        disabled={!canGoBack}
        onClick={onBack}
        title="Back to previous path"
      >
        Back
      </button>
      <button
        type="button"
        className="pg-lwt-breadcrumb-up"
        disabled={!canGoUp}
        onClick={onGoUp}
        title="Go to parent path"
        aria-label="Go to parent path"
      >
        Up
      </button>
      {items.map((item, index) => {
        const isCurrent = index === items.length - 1;
        return (
          <React.Fragment key={`${item.trajectoryId}:${index}`}>
            {index > 0 ? <span className="pg-lwt-breadcrumb-separator">/</span> : null}
            <button
              type="button"
              className="pg-lwt-breadcrumb-item"
              disabled={isCurrent}
              onClick={() => {
                onNavigate(index);
              }}
              title={item.trajectoryId}
            >
              {item.title || item.trajectoryId}
            </button>
          </React.Fragment>
        );
      })}
    </nav>
  );
}

function TrajectoryDetailPanel({
  detail,
  onEnterChild,
  onJumpToEndpoint,
  onOpenRelation,
}: {
  detail: TrajectoryDetail;
  onEnterChild: (childTrajectory: LocalWorkTrajectory) => void;
  onJumpToEndpoint: (target: EndpointTarget) => void;
  onOpenRelation: (target: RelationTarget) => void;
}): React.ReactElement {
  const {
    event,
    lane,
    childTrajectory,
    externalRelianceIndicators,
    dependencyProxy,
    relation,
    relationSourceEvent,
    relationTargetEvent,
    relationSourceEndpointChild,
    relationTargetEndpointChild,
  } = detail;
  if (dependencyProxy) {
    return (
      <aside className="pg-lwt-detail" aria-label="Dependency proxy detail">
        <div className="pg-lwt-detail-kicker">dependency proxy</div>
        <h3>{dependencyProxy.sourceEndpointEvent?.title ?? dependencyProxy.sourceEndpointEventId}</h3>
        <dl className="pg-lwt-detail-list">
          <div>
            <dt>Represents</dt>
            <dd>{formatEventReference(dependencyProxy.sourceEndpointEvent, dependencyProxy.sourceEndpointEventId)}</dd>
          </div>
          <div>
            <dt>Dependent</dt>
            <dd>{formatEventReference(dependencyProxy.dependentEvent, dependencyProxy.dependentEventId)}</dd>
          </div>
          <div>
            <dt>Relation</dt>
            <dd>{dependencyProxy.relation.kind} · {dependencyScopeDescription(dependencyProxy.relation)}</dd>
          </div>
          <div>
            <dt>Owner</dt>
            <dd>{dependencyProxy.ownerTrajectory.trajectoryId || 'current trajectory'}</dd>
          </div>
          <div>
            <dt>Origin</dt>
            <dd>{dependencyProxy.origin}</dd>
          </div>
        </dl>
        {dependencyProxy.relation.summary ? <p className="pg-lwt-detail-summary">{dependencyProxy.relation.summary}</p> : null}
        <RelationEndpointCard
          label="Depended precise endpoint"
          prefix="source"
          metadata={dependencyProxy.relation.metadata}
          childTrajectory={dependencyProxy.sourceEndpointTrajectory}
          onJumpToEndpoint={onJumpToEndpoint}
        />
        <button
          type="button"
          className="pg-lwt-open-relation"
          onClick={() => {
            onOpenRelation({
              trajectory: dependencyProxy.ownerTrajectory,
              relationId: dependencyProxy.relationId,
            });
          }}
        >
          Open owner relation
        </button>
      </aside>
    );
  }
  if (relation) {
    const projection = relation.metadata.relation_projection ?? '';
    const relationTitle = relationDetailTitle(relation);
    return (
      <aside className="pg-lwt-detail" aria-label="Trajectory relation detail">
        <div className="pg-lwt-detail-kicker">relation</div>
        <h3>{relationTitle}</h3>
        <dl className="pg-lwt-detail-list">
          <div>
            <dt>Kind</dt>
            <dd>{relation.kind}</dd>
          </div>
          <div>
            <dt>Projection</dt>
            <dd>{projection || 'parent-level'}</dd>
          </div>
          {relation.kind === 'depends_on' ? (
            <div>
              <dt>Dependency scope</dt>
              <dd>{dependencyScopeDescription(relation)}</dd>
            </div>
          ) : null}
          <div>
            <dt>{relationEndpointRoleLabel(relation.kind, 'source')} source</dt>
            <dd>{formatEventReference(relationSourceEvent, relation.sourceEventId)}</dd>
          </div>
          <div>
            <dt>{relationEndpointRoleLabel(relation.kind, 'target')} target</dt>
            <dd>{formatEventReference(relationTargetEvent, relation.targetEventId)}</dd>
          </div>
        </dl>
        {relation.summary ? <p className="pg-lwt-detail-summary">{relation.summary}</p> : null}
        <RelationEndpointCard
          label={relationPreciseEndpointLabel(relation.kind, 'source')}
          prefix="source"
          metadata={relation.metadata}
          childTrajectory={relationSourceEndpointChild}
          onJumpToEndpoint={onJumpToEndpoint}
        />
        <RelationEndpointCard
          label={relationPreciseEndpointLabel(relation.kind, 'target')}
          prefix="target"
          metadata={relation.metadata}
          childTrajectory={relationTargetEndpointChild}
          onJumpToEndpoint={onJumpToEndpoint}
        />
      </aside>
    );
  }
  if (!event) {
    return (
      <aside className="pg-lwt-detail" aria-label="Trajectory event detail">
        <div className="pg-lwt-detail-empty">
          <strong>选择一个节点</strong>
          <span>Compound 节点会在这里显示子轨迹入口。</span>
        </div>
      </aside>
    );
  }
  const metadataRows = compactMetadataRows(event.metadata, [
    'child_trajectory_id',
    'compound_mode',
    'compound_role',
    'anchor_compound_event_id',
    'anchor_lane_id',
    'packed_lane_ids',
    'packed_lane_id',
    'range_start_event_id',
    'range_end_event_id',
    'packed_event_ids',
  ]);
  return (
    <aside className="pg-lwt-detail" aria-label="Trajectory event detail">
      <div className="pg-lwt-detail-kicker">{event.kind}</div>
      <h3>{event.title}</h3>
      <dl className="pg-lwt-detail-list">
        <div>
          <dt>Status</dt>
          <dd>{event.status}</dd>
        </div>
        <div>
          <dt>Lane</dt>
          <dd>{lane?.label ?? event.laneId}</dd>
        </div>
        <div>
          <dt>Order</dt>
          <dd>#{event.order}</dd>
        </div>
      </dl>
      {event.summary ? <p className="pg-lwt-detail-summary">{event.summary}</p> : null}
      {childTrajectory ? (
        <div className="pg-lwt-child-card">
          <div>
            <span className="pg-lwt-child-card-label">Child trajectory</span>
            <strong>{childTrajectory.title || childTrajectory.trajectoryId}</strong>
          </div>
          <dl className="pg-lwt-child-card-metrics">
            <div>
              <dt>Lanes</dt>
              <dd>{childTrajectory.lanes.length}</dd>
            </div>
            <div>
              <dt>Events</dt>
              <dd>{childTrajectory.events.length}</dd>
            </div>
            <div>
              <dt>Relations</dt>
              <dd>{childTrajectory.relations.length}</dd>
            </div>
          </dl>
          <button
            type="button"
            className="pg-lwt-enter-child"
            onClick={() => {
              onEnterChild(childTrajectory);
            }}
          >
            Enter child
          </button>
        </div>
      ) : event.kind === 'compound' ? (
        <p className="pg-lwt-detail-summary">This compound event does not have a matching child trajectory payload.</p>
      ) : null}
      {externalRelianceIndicators.length > 0 ? (
        <div className="pg-lwt-external-reliance-list">
          <span className="pg-lwt-child-card-label">External reliance</span>
          {externalRelianceIndicators.map((indicator) => (
            <ExternalRelianceCard
              key={`${indicator.relationId}:${indicator.endpointRole}:${indicator.endpointEventId}`}
              indicator={indicator}
              onOpenRelation={onOpenRelation}
            />
          ))}
        </div>
      ) : null}
      {metadataRows.length > 0 ? (
        <dl className="pg-lwt-detail-metadata">
          {metadataRows.map(([key, value]) => (
            <div key={key}>
              <dt>{formatMetadataKey(key)}</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
      ) : null}
    </aside>
  );
}

function ExternalRelianceCard({
  indicator,
  onOpenRelation,
}: {
  indicator: ExternalRelianceIndicator;
  onOpenRelation: (target: RelationTarget) => void;
}): React.ReactElement {
  const projection = indicator.relation.metadata.relation_projection ?? '';
  const endpointRoleLabel = relationEndpointRoleLabel(indicator.relation.kind, indicator.endpointRole);
  const externalLabel = externalRelianceBadgeLabel(indicator);
  return (
    <div className="pg-lwt-external-reliance-card">
      <dl className="pg-lwt-detail-metadata">
        <div>
          <dt>Kind</dt>
          <dd>{indicator.relation.kind}</dd>
        </div>
        <div>
          <dt>Projection</dt>
          <dd>{projection || 'parent-level'}</dd>
        </div>
        <div>
          <dt>Endpoint</dt>
          <dd>{endpointRoleLabel} ({indicator.endpointRole})</dd>
        </div>
        <div>
          <dt>Owner</dt>
          <dd>{indicator.ownerTrajectory.trajectoryId}</dd>
        </div>
      </dl>
      {indicator.relation.summary ? <p className="pg-lwt-detail-summary">{indicator.relation.summary}</p> : null}
      <button
        type="button"
        className="pg-lwt-open-relation"
        onClick={() => {
          onOpenRelation({
            trajectory: indicator.ownerTrajectory,
            relationId: indicator.relationId,
          });
        }}
      >
        Open parent relation
      </button>
      <span className="pg-lwt-external-reliance-kind">{externalLabel}</span>
    </div>
  );
}

function RelationEndpointCard({
  label,
  prefix,
  metadata,
  childTrajectory,
  onJumpToEndpoint,
}: {
  label: string;
  prefix: 'source' | 'target';
  metadata: Record<string, string>;
  childTrajectory: LocalWorkTrajectory | null;
  onJumpToEndpoint: (target: EndpointTarget) => void;
}): React.ReactElement | null {
  const rows = endpointMetadataRows(prefix, metadata);
  if (rows.length === 0) {
    return null;
  }
  const eventId = metadata[`${prefix}_endpoint_event_id`] ?? '';
  return (
    <div className="pg-lwt-endpoint-card">
      <div>
        <span className="pg-lwt-child-card-label">{label}</span>
      </div>
      <dl className="pg-lwt-detail-metadata">
        {rows.map(([key, value]) => (
          <div key={key}>
            <dt>{formatMetadataKey(key)}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
      {childTrajectory && eventId ? (
        <button
          type="button"
          className="pg-lwt-enter-child"
          onClick={() => {
            onJumpToEndpoint({ trajectory: childTrajectory, eventId });
          }}
        >
          Jump to endpoint
        </button>
      ) : null}
    </div>
  );
}

function Shell({
  status,
  title,
  subtitle,
  metrics = [],
  children,
}: {
  status: string;
  title: string;
  subtitle: string;
  metrics?: [string, string][];
  children: React.ReactNode;
}): React.ReactElement {
  return (
    <section className="pg-lwt-shell" data-pg-lwt-status={status}>
      <header className="pg-lwt-head">
        <div>
          <div className="pg-lwt-eyebrow">Local Work Trajectory</div>
          <h2 className="pg-lwt-title">{title}</h2>
          <p className="pg-lwt-subtitle">{subtitle}</p>
        </div>
        <div className="pg-lwt-meta">
          {metrics.map(([label, value]) => (
            <span className="pg-lwt-pill" key={label}>{label}: {value}</span>
          ))}
        </div>
      </header>
      {children}
    </section>
  );
}

function buildLayout(
  lanes: TrajectoryLane[],
  events: TrajectoryEvent[],
  relations: TrajectoryRelation[],
  externalRelianceByEventId: Map<string, ExternalRelianceIndicator[]>,
  dependencyProxies: DependencyProxy[],
  trajectory: LocalWorkTrajectory | null,
  laneOrderOverride: TrajectoryLane[] | null = null,
  laneOrderMode: 'weighted' | 'manual' = 'weighted',
  laneOrderControls: LaneOrderControls | null = null,
): LayoutState {
  const message = laneOrderMode === 'manual'
    ? 'Lane-first layout uses your manual lane order; refresh resets to relation-weighted order.'
    : isSchedulerStateProjection(trajectory)
      ? 'Lane-first layout orders scheduler projection lanes by earliest projected task order.'
      : 'Lane-first layout orders lanes by opening relations and cross-lane relation weight.';
  return buildLaneLayout(
    prepareFlowElements(lanes, events, relations, externalRelianceByEventId, dependencyProxies, trajectory, laneOrderOverride, laneOrderControls),
    message,
    'lanes',
    isSchedulerStateProjection(trajectory) ? 'all' : 'focus',
  );
}

function buildChildTrajectoryIndex(trajectory: LocalWorkTrajectory | null): Map<string, LocalWorkTrajectory> {
  const index = new Map<string, LocalWorkTrajectory>();
  const visit = (candidate: LocalWorkTrajectory | null | undefined): void => {
    if (!candidate || index.has(candidate.trajectoryId)) {
      return;
    }
    index.set(candidate.trajectoryId, candidate);
    for (const child of candidate.childTrajectories ?? []) {
      visit(child);
    }
  };
  for (const child of trajectory?.childTrajectories ?? []) {
    visit(child);
  }
  return index;
}

function buildSelectedDetail(
  selectedEventId: string | null,
  selectedRelationId: string | null,
  selectedProxyId: string | null,
  rootTrajectory: LocalWorkTrajectory | null,
  currentTrajectory: LocalWorkTrajectory | null,
  lanes: TrajectoryLane[],
  events: TrajectoryEvent[],
  relations: TrajectoryRelation[],
  childTrajectoryById: Map<string, LocalWorkTrajectory>,
  externalRelianceByEventId: Map<string, ExternalRelianceIndicator[]>,
  dependencyProxies: DependencyProxy[],
): TrajectoryDetail {
  const emptyDetail = {
    event: null,
    lane: null,
    childTrajectory: null,
    externalRelianceIndicators: [],
    dependencyProxy: null,
    relation: null,
    relationSourceEvent: null,
    relationTargetEvent: null,
    relationSourceEndpointChild: null,
    relationTargetEndpointChild: null,
  };
  const eventById = new Map(events.map((candidate) => [candidate.id, candidate]));
  if (selectedProxyId) {
    const dependencyProxy = dependencyProxies.find((candidate) => candidate.id === selectedProxyId) ?? null;
    if (!dependencyProxy) {
      return emptyDetail;
    }
    return {
      ...emptyDetail,
      dependencyProxy,
      relation: dependencyProxy.relation,
      relationSourceEvent: dependencyProxy.sourceEndpointEvent,
      relationTargetEvent: dependencyProxy.dependentEvent,
      relationSourceEndpointChild: dependencyProxy.sourceEndpointTrajectory,
      relationTargetEndpointChild: findEndpointTrajectory(
        rootTrajectory,
        currentTrajectory,
        dependencyProxy.relation.metadata.target_endpoint_trajectory_id ?? '',
      ),
    };
  }
  if (selectedRelationId) {
    const relation = relations.find((candidate) => relationStableId(candidate) === selectedRelationId) ?? null;
    if (!relation) {
      return emptyDetail;
    }
    return {
      ...emptyDetail,
      relation,
      relationSourceEvent: eventById.get(relation.sourceEventId) ?? null,
      relationTargetEvent: eventById.get(relation.targetEventId) ?? null,
      relationSourceEndpointChild: childTrajectoryById.get(relation.metadata.source_endpoint_trajectory_id ?? '') ?? null,
      relationTargetEndpointChild: childTrajectoryById.get(relation.metadata.target_endpoint_trajectory_id ?? '') ?? null,
    };
  }
  if (!selectedEventId) {
    return emptyDetail;
  }
  const event = events.find((candidate) => candidate.id === selectedEventId) ?? null;
  if (!event) {
    return emptyDetail;
  }
  const childTrajectoryId = event.metadata.child_trajectory_id ?? '';
  return {
    ...emptyDetail,
    event,
    lane: lanes.find((candidate) => candidate.id === event.laneId) ?? null,
    childTrajectory: childTrajectoryById.get(childTrajectoryId) ?? null,
    externalRelianceIndicators: externalRelianceByEventId.get(event.id) ?? [],
  };
}

function buildExternalRelianceByEventId(
  rootTrajectory: LocalWorkTrajectory | null,
  currentTrajectory: LocalWorkTrajectory | null,
): Map<string, ExternalRelianceIndicator[]> {
  const indicatorsByEventId = new Map<string, ExternalRelianceIndicator[]>();
  if (!rootTrajectory || !currentTrajectory || rootTrajectory.trajectoryId === currentTrajectory.trajectoryId) {
    return indicatorsByEventId;
  }
  const visit = (ownerTrajectory: LocalWorkTrajectory): void => {
    for (const relation of ownerTrajectory.relations) {
      if (ownerTrajectory.trajectoryId === currentTrajectory.trajectoryId || !relation.metadata.relation_projection) {
        continue;
      }
      collectExternalRelianceEndpoint(indicatorsByEventId, currentTrajectory, ownerTrajectory, relation, 'source');
      collectExternalRelianceEndpoint(indicatorsByEventId, currentTrajectory, ownerTrajectory, relation, 'target');
    }
    for (const child of ownerTrajectory.childTrajectories ?? []) {
      visit(child);
    }
  };
  visit(rootTrajectory);
  return indicatorsByEventId;
}

function collectExternalRelianceEndpoint(
  indicatorsByEventId: Map<string, ExternalRelianceIndicator[]>,
  currentTrajectory: LocalWorkTrajectory,
  ownerTrajectory: LocalWorkTrajectory,
  relation: TrajectoryRelation,
  endpointRole: 'source' | 'target',
): void {
  const endpointTrajectoryId = relation.metadata[`${endpointRole}_endpoint_trajectory_id`] ?? '';
  const endpointEventId = relation.metadata[`${endpointRole}_endpoint_event_id`] ?? '';
  if (endpointTrajectoryId !== currentTrajectory.trajectoryId || !endpointEventId) {
    return;
  }
  const indicators = indicatorsByEventId.get(endpointEventId) ?? [];
  indicators.push({
    relation,
    relationId: relationStableId(relation),
    ownerTrajectory,
    endpointRole,
    endpointEventId,
  });
  indicatorsByEventId.set(endpointEventId, indicators);
}

function buildDependencyProxies(
  rootTrajectory: LocalWorkTrajectory | null,
  currentTrajectory: LocalWorkTrajectory | null,
  relations: TrajectoryRelation[],
  events: TrajectoryEvent[],
  childTrajectoryById: Map<string, LocalWorkTrajectory>,
): DependencyProxy[] {
  const eventById = new Map(events.map((event) => [event.id, event]));
  const proxies: DependencyProxy[] = [];
  for (const relation of relations) {
    if (relation.kind !== 'depends_on') {
      continue;
    }
    const dependentEvent = eventById.get(relation.targetEventId);
    const sourceEndpointEventId = relation.metadata.source_endpoint_event_id ?? '';
    if (!dependentEvent || !sourceEndpointEventId) {
      continue;
    }
    const sourceEndpointTrajectoryId = relation.metadata.source_endpoint_trajectory_id ?? currentTrajectory?.trajectoryId ?? '';
    const sourceEndpointTrajectory = findEndpointTrajectory(
      rootTrajectory,
      currentTrajectory,
      sourceEndpointTrajectoryId,
      childTrajectoryById,
    );
    const sourceEndpointEvent = sourceEndpointTrajectory?.events.find((event) => event.id === sourceEndpointEventId) ?? null;
    proxies.push({
      id: dependencyProxyId(relation, 'source'),
      relation,
      relationId: relationStableId(relation),
      ownerTrajectory: currentTrajectory ?? rootTrajectory ?? {
        trajectoryId: '',
        title: '',
        recordedAt: null,
        sourceGraphId: null,
        sourceNodeId: null,
        guideContext: null,
        metadata: {},
        lanes: [],
        events: [],
        relations: [],
      },
      dependentEventId: dependentEvent.id,
      dependentEvent,
      sourceEndpointTrajectoryId,
      sourceEndpointEventId,
      sourceEndpointParentEventId: relation.metadata.source_endpoint_parent_event_id ?? relation.sourceEventId,
      sourceEndpointCompoundPath: relation.metadata.source_endpoint_compound_path ?? '',
      sourceEndpointTrajectory,
      sourceEndpointEvent,
      origin: 'local-relation',
    });
  }

  for (const [eventId, indicators] of buildExternalRelianceByEventId(rootTrajectory, currentTrajectory).entries()) {
    const dependentEvent = eventById.get(eventId);
    if (!dependentEvent) {
      continue;
    }
    for (const indicator of indicators) {
      if (indicator.relation.kind !== 'depends_on' || indicator.endpointRole !== 'target') {
        continue;
      }
      const sourceEndpointEventId = indicator.relation.metadata.source_endpoint_event_id ?? indicator.relation.sourceEventId;
      const sourceEndpointTrajectoryId = indicator.relation.metadata.source_endpoint_trajectory_id ?? indicator.ownerTrajectory.trajectoryId;
      const sourceEndpointTrajectory = findEndpointTrajectory(
        rootTrajectory,
        currentTrajectory,
        sourceEndpointTrajectoryId,
        childTrajectoryById,
      );
      const sourceEndpointEvent = sourceEndpointTrajectory?.events.find((event) => event.id === sourceEndpointEventId) ?? null;
      proxies.push({
        id: dependencyProxyId(indicator.relation, 'external-source'),
        relation: indicator.relation,
        relationId: indicator.relationId,
        ownerTrajectory: indicator.ownerTrajectory,
        dependentEventId: dependentEvent.id,
        dependentEvent,
        sourceEndpointTrajectoryId,
        sourceEndpointEventId,
        sourceEndpointParentEventId: indicator.relation.metadata.source_endpoint_parent_event_id ?? indicator.relation.sourceEventId,
        sourceEndpointCompoundPath: indicator.relation.metadata.source_endpoint_compound_path ?? '',
        sourceEndpointTrajectory,
        sourceEndpointEvent,
        origin: 'external-reliance',
      });
    }
  }

  return dedupeDependencyProxies(proxies);
}

function dedupeDependencyProxies(proxies: DependencyProxy[]): DependencyProxy[] {
  const seen = new Set<string>();
  const deduped: DependencyProxy[] = [];
  for (const proxy of proxies) {
    if (seen.has(proxy.id)) {
      continue;
    }
    seen.add(proxy.id);
    deduped.push(proxy);
  }
  return deduped;
}

function findEndpointTrajectory(
  rootTrajectory: LocalWorkTrajectory | null,
  currentTrajectory: LocalWorkTrajectory | null,
  trajectoryId: string,
  childTrajectoryById?: Map<string, LocalWorkTrajectory>,
): LocalWorkTrajectory | null {
  if (!trajectoryId) {
    return null;
  }
  if (currentTrajectory?.trajectoryId === trajectoryId) {
    return currentTrajectory;
  }
  if (rootTrajectory?.trajectoryId === trajectoryId) {
    return rootTrajectory;
  }
  const indexed = childTrajectoryById?.get(trajectoryId);
  if (indexed) {
    return indexed;
  }
  const searchRoot = rootTrajectory ?? currentTrajectory;
  if (!searchRoot) {
    return null;
  }
  return findTrajectoryPath(searchRoot, trajectoryId).at(-1) ?? null;
}

function dependencyProxyId(relation: TrajectoryRelation, endpointRole: string): string {
  return `dependency-proxy:${relationStableId(relation)}:${endpointRole}`;
}

function isEventNode(node: Node): boolean {
  return typeof node.data?.eventKind === 'string';
}

function isDependencyProxyNode(node: Node): boolean {
  return typeof node.data?.dependencyProxyId === 'string';
}

function isSelectedCompoundGroupNode(node: Node, selectedEventId: string | null, nodes: Node[]): boolean {
  if (!selectedEventId || node.id.startsWith('lane:')) {
    return false;
  }
  const selectedNode = nodes.find((candidate) => candidate.id === selectedEventId);
  const selectedChildTrajectoryId = selectedNode?.data?.childTrajectoryId;
  return (
    typeof selectedChildTrajectoryId === 'string'
    && selectedChildTrajectoryId.length > 0
    && node.data?.childTrajectoryId === selectedChildTrajectoryId
  );
}

function trajectoryNodeClassNameForSelection(
  node: Node,
  selectedEventId: string | null,
  selectedProxyId: string | null,
  nodes: Node[],
): string {
  const isSelected = node.id === selectedEventId || node.id === selectedProxyId;
  const selectedLayer = isSelected ? nodeVisualLayer('selected', 'TrajectoryFlow.selectedNode') : null;
  return [
    node.className,
    selectedLayer?.className ?? '',
    isSelectedCompoundGroupNode(node, selectedEventId, nodes) ? 'pg-lwt-node-compound-group-selected' : '',
  ].filter(Boolean).join(' ');
}

function trajectoryNodeStyleForSelection(
  node: Node,
  selectedEventId: string | null,
  selectedProxyId: string | null,
): React.CSSProperties | undefined {
  if (node.id !== selectedEventId && node.id !== selectedProxyId) {
    return node.style;
  }
  const selectedLayer = nodeVisualLayer('selected', 'TrajectoryFlow.selectedNode');
  return {
    ...node.style,
    ...selectedLayer.style,
  };
}

function isRelationEdge(edge: Edge): boolean {
  return edge.id.startsWith(relationEdgeIdPrefix);
}

function relationStableId(relation: TrajectoryRelation): string {
  const projection = relation.metadata.relation_projection ?? '';
  return `${relation.sourceEventId}->${relation.targetEventId}:${relation.kind}:${projection}`;
}

function relationEdgeId(relation: TrajectoryRelation, suffix = ''): string {
  return `${relationEdgeIdPrefix}${relationStableId(relation)}${suffix}`;
}

function laneOpeningJunctionId(sourceEventId: string): string {
  return `lane-opening:${sourceEventId}`;
}

function laneOpeningFanoutLabel(fanout: LaneOpeningFanout): string {
  const count = fanout.relations.length;
  const hasApproval = fanout.relations.some((relation) => relation.kind === 'approves_new_line');
  if (count <= 1) {
    return hasApproval ? 'approves lane' : 'starts lane';
  }
  return hasApproval ? `approves ${count} lanes` : `starts ${count} lanes`;
}

function relationIdFromEdgeId(edgeId: string): string | null {
  if (!edgeId.startsWith(relationEdgeIdPrefix)) {
    return null;
  }
  return edgeId.slice(relationEdgeIdPrefix.length).replace(/:reliance-overlay$/, '');
}

function findTrajectoryPath(root: LocalWorkTrajectory, trajectoryId: string): LocalWorkTrajectory[] {
  if (root.trajectoryId === trajectoryId) {
    return [root];
  }
  for (const child of root.childTrajectories ?? []) {
    const childPath = findTrajectoryPath(child, trajectoryId);
    if (childPath.length > 0) {
      return [root, ...childPath];
    }
  }
  return [];
}

function prepareFlowElements(
  lanes: TrajectoryLane[],
  events: TrajectoryEvent[],
  relations: TrajectoryRelation[],
  externalRelianceByEventId: Map<string, ExternalRelianceIndicator[]>,
  dependencyProxies: DependencyProxy[],
  trajectory: LocalWorkTrajectory | null,
  laneOrderOverride: TrajectoryLane[] | null = null,
  laneOrderControls: LaneOrderControls | null = null,
): PreparedFlowElements {
  const orderedLanes = laneOrderOverride ?? orderLanes(trajectory, lanes, events, relations);
  const laneIds = new Set(orderedLanes.map((lane) => lane.id));
  const eventsByLane = new Map<string, TrajectoryEvent[]>();
  for (const lane of orderedLanes) {
    eventsByLane.set(lane.id, []);
  }
  for (const event of events) {
    if (!laneIds.has(event.laneId)) {
      continue;
    }
    eventsByLane.get(event.laneId)?.push(event);
  }
  for (const laneEvents of eventsByLane.values()) {
    laneEvents.sort((left, right) => left.order - right.order || left.id.localeCompare(right.id));
  }

  const activeEventId = findActiveEventId(orderedLanes, eventsByLane);
  const eventById = new Map(events.map((event) => [event.id, event]));
  const eventColumns = computeEventColumns(orderedLanes, eventsByLane, eventById, relations);
  const laneStartColumns = computeLaneStartColumns(orderedLanes, eventsByLane, eventById, relations, eventColumns);
  const eventIds = new Set(events.filter((event) => laneIds.has(event.laneId)).map((event) => event.id));
  const relationBadgesByEventId = buildRelationBadgesByEventId(relations, eventById, externalRelianceByEventId);
  const eventLaneIndexById = buildEventLaneIndexById(orderedLanes, eventsByLane);
  const childEventCountByTrajectoryId = buildChildEventCountByTrajectoryId(events);
  const dependencyProxyPlacements = buildDependencyProxyPlacements(dependencyProxies, eventColumns, eventLaneIndexById);
  const laneOpeningFanouts = buildLaneOpeningFanouts(relations, eventById, eventColumns, eventLaneIndexById, eventIds);
  const nodes: Node[] = [];
  const sequenceEdges: Edge[] = [];
  orderedLanes.forEach((lane, laneIndex) => {
    const laneEvents = eventsByLane.get(lane.id) ?? [];
    nodes.push(buildLaneNode(lane, laneIndex, laneStartColumns.get(lane.id) ?? -1, laneOrderControls));
    nodes.push(...laneEvents.map((event, eventIndex) => buildEventNode(
      event,
      laneIndex,
      eventColumns.get(event.id) ?? eventIndex,
      relationBadgesByEventId.get(event.id) ?? [],
      childEventCountByTrajectoryId.get(event.metadata.child_trajectory_id ?? '') ?? null,
    )));
    laneEvents.forEach((event, eventIndex) => {
      const previous = eventIndex === 0 ? lane.id : laneEvents[eventIndex - 1].id;
      sequenceEdges.push(buildFlowEdge(previous, event.id, 'sequence'));
    });
  });
  const relationEdges = relations
    .filter((relation) => (
      relation.kind !== 'sequence'
      && !auxiliaryRelationKinds.has(relation.kind)
      && !laneOpeningRelationKinds.has(relation.kind)
      && eventIds.has(relation.sourceEventId)
      && eventIds.has(relation.targetEventId)
    ))
    .map((relation) => buildRelationEdge(relation));
  const relianceEdges = relations
    .filter((relation) => (
      relianceRelationKinds.has(relation.kind)
      && eventIds.has(relation.sourceEventId)
      && eventIds.has(relation.targetEventId)
    ))
    .map((relation) => buildRelianceOverlayEdge(relation, eventLaneIndexById));
  const laneOpeningNodes = laneOpeningFanouts.map((fanout) => buildLaneOpeningJunctionNode(fanout));
  const laneOpeningEdges = laneOpeningFanouts.flatMap((fanout) => buildLaneOpeningFanoutEdges(fanout));
  nodes.push(...dependencyProxyPlacements.map((placement) => buildDependencyProxyNode(placement)));
  const dependencyProxyEdges = dependencyProxyPlacements.map((placement) => buildDependencyProxyEdge(placement));
  const focusEventId = activeEventId ?? findFocusEventId(orderedLanes, eventsByLane);
  return {
    nodes: [...nodes, ...laneOpeningNodes],
    edges: [...sequenceEdges, ...relationEdges, ...laneOpeningEdges, ...relianceEdges, ...dependencyProxyEdges],
    activeEventId,
    focusEventId,
  };
}

function orderLanes(
  trajectory: LocalWorkTrajectory | null,
  lanes: TrajectoryLane[],
  events: TrajectoryEvent[],
  relations: TrajectoryRelation[],
): TrajectoryLane[] {
  if (isSchedulerStateProjection(trajectory)) {
    return orderSchedulerProjectionLanes(lanes, events);
  }
  const laneById = new Map(lanes.map((lane) => [lane.id, lane]));
  const eventById = new Map(events.map((event) => [event.id, event]));
  const laneRelationWeights = buildLaneRelationWeights(events, relations);
  const openings = relations
    .filter((relation) => laneOpeningRelationKinds.has(relation.kind))
    .map((relation) => {
      const source = eventById.get(relation.sourceEventId);
      const target = eventById.get(relation.targetEventId);
      if (
        !source
        || !target
        || source.laneId === target.laneId
        || !laneById.has(source.laneId)
        || !laneById.has(target.laneId)
      ) {
        return null;
      }
      return {
        parentLaneId: source.laneId,
        childLaneId: target.laneId,
        sourceOrder: source.order,
        sourceEventId: source.id,
        targetOrder: target.order,
        targetEventId: target.id,
      };
    })
    .filter((opening): opening is {
      parentLaneId: string;
      childLaneId: string;
      sourceOrder: number;
      sourceEventId: string;
      targetOrder: number;
      targetEventId: string;
    } => opening !== null)
    .sort((left, right) => (
      left.sourceOrder - right.sourceOrder
      || left.sourceEventId.localeCompare(right.sourceEventId)
      || left.targetOrder - right.targetOrder
      || left.targetEventId.localeCompare(right.targetEventId)
      || left.childLaneId.localeCompare(right.childLaneId)
    ));
  const childLaneIds = new Set<string>();
  const childrenByParent = new Map<string, typeof openings>();
  for (const opening of openings) {
    if (childLaneIds.has(opening.childLaneId)) {
      continue;
    }
    childLaneIds.add(opening.childLaneId);
    const children = childrenByParent.get(opening.parentLaneId) ?? [];
    children.push(opening);
    childrenByParent.set(opening.parentLaneId, children);
  }

  const roots = lanes
    .filter((lane) => !childLaneIds.has(lane.id))
    .sort(compareLaneRoots);
  const ordered: TrajectoryLane[] = [];
  const visitedLaneIds = new Set<string>();
  const visitLane = (laneId: string): void => {
    if (visitedLaneIds.has(laneId)) {
      return;
    }
    const lane = laneById.get(laneId);
    if (!lane) {
      return;
    }
    visitedLaneIds.add(laneId);
    ordered.push(lane);
    const children = (childrenByParent.get(laneId) ?? [])
      .slice()
      .sort((left, right) => compareLaneSiblings(
        laneById.get(left.childLaneId),
        laneById.get(right.childLaneId),
        laneRelationWeights,
        laneId,
      ));
    for (const child of children) {
      visitLane(child.childLaneId);
    }
  };

  for (const lane of roots.sort((left, right) => compareLaneSiblings(left, right, laneRelationWeights))) {
    visitLane(lane.id);
  }
  for (const lane of lanes.slice().sort((left, right) => compareLaneSiblings(left, right, laneRelationWeights))) {
    visitLane(lane.id);
  }
  return ordered;
}

function isSchedulerStateProjection(trajectory: LocalWorkTrajectory | null): boolean {
  return trajectory?.metadata?.projection === 'scheduler-state';
}

function orderSchedulerProjectionLanes(
  lanes: TrajectoryLane[],
  events: TrajectoryEvent[],
): TrajectoryLane[] {
  const firstEventOrderByLaneId = new Map<string, number>();
  for (const event of events) {
    const current = firstEventOrderByLaneId.get(event.laneId);
    if (current === undefined || event.order < current) {
      firstEventOrderByLaneId.set(event.laneId, event.order);
    }
  }
  return lanes.slice().sort((left, right) => {
    const leftOrder = firstEventOrderByLaneId.get(left.id) ?? Number.MAX_SAFE_INTEGER;
    const rightOrder = firstEventOrderByLaneId.get(right.id) ?? Number.MAX_SAFE_INTEGER;
    return leftOrder - rightOrder || compareLaneRoots(left, right);
  });
}

function compareLaneRoots(left: TrajectoryLane, right: TrajectoryLane): number {
  const leftRank = left.id === 'lane:main' ? 0 : 1;
  const rightRank = right.id === 'lane:main' ? 0 : 1;
  return leftRank - rightRank || left.id.localeCompare(right.id);
}

function compareLaneSiblings(
  left: TrajectoryLane | undefined,
  right: TrajectoryLane | undefined,
  laneRelationWeights: Map<string, Map<string, number>>,
  parentLaneId = '',
): number {
  if (!left && !right) {
    return 0;
  }
  if (!left) {
    return 1;
  }
  if (!right) {
    return -1;
  }
  const rootOrder = compareLaneRoots(left, right);
  if (left.id === 'lane:main' || right.id === 'lane:main') {
    return rootOrder;
  }
  const parentDelta = relationWeightBetweenLanes(right.id, parentLaneId, laneRelationWeights)
    - relationWeightBetweenLanes(left.id, parentLaneId, laneRelationWeights);
  if (parentDelta !== 0) {
    return parentDelta;
  }
  const totalDelta = totalLaneRelationWeight(right.id, laneRelationWeights)
    - totalLaneRelationWeight(left.id, laneRelationWeights);
  return totalDelta || rootOrder;
}

function buildLaneRelationWeights(
  events: TrajectoryEvent[],
  relations: TrajectoryRelation[],
): Map<string, Map<string, number>> {
  const eventById = new Map(events.map((event) => [event.id, event]));
  const weights = new Map<string, Map<string, number>>();
  for (const relation of relations) {
    if (!relationWeightedLaneOrderKinds.has(relation.kind)) {
      continue;
    }
    const source = eventById.get(relation.sourceEventId);
    const target = eventById.get(relation.targetEventId);
    if (!source || !target || source.laneId === target.laneId) {
      continue;
    }
    incrementLaneRelationWeight(weights, source.laneId, target.laneId);
    incrementLaneRelationWeight(weights, target.laneId, source.laneId);
  }
  return weights;
}

function incrementLaneRelationWeight(
  weights: Map<string, Map<string, number>>,
  sourceLaneId: string,
  targetLaneId: string,
): void {
  const targets = weights.get(sourceLaneId) ?? new Map<string, number>();
  targets.set(targetLaneId, (targets.get(targetLaneId) ?? 0) + 1);
  weights.set(sourceLaneId, targets);
}

function relationWeightBetweenLanes(
  leftLaneId: string,
  rightLaneId: string,
  laneRelationWeights: Map<string, Map<string, number>>,
): number {
  if (!leftLaneId || !rightLaneId) {
    return 0;
  }
  return laneRelationWeights.get(leftLaneId)?.get(rightLaneId) ?? 0;
}

function totalLaneRelationWeight(
  laneId: string,
  laneRelationWeights: Map<string, Map<string, number>>,
): number {
  let total = 0;
  for (const weight of laneRelationWeights.get(laneId)?.values() ?? []) {
    total += weight;
  }
  return total;
}

function applyLaneOrderOverride(lanes: TrajectoryLane[], laneOrderOverride: string[]): TrajectoryLane[] {
  const laneById = new Map(lanes.map((lane) => [lane.id, lane]));
  const ordered: TrajectoryLane[] = [];
  const usedLaneIds = new Set<string>();
  for (const laneId of laneOrderOverride) {
    const lane = laneById.get(laneId);
    if (!lane || usedLaneIds.has(laneId)) {
      continue;
    }
    ordered.push(lane);
    usedLaneIds.add(laneId);
  }
  for (const lane of lanes) {
    if (!usedLaneIds.has(lane.id)) {
      ordered.push(lane);
    }
  }
  return ordered;
}

function moveLaneInOrder(
  orderedLanes: TrajectoryLane[],
  laneId: string,
  direction: -1 | 1,
): string[] {
  const orderedLaneIds = orderedLanes.map((lane) => lane.id);
  const index = orderedLaneIds.indexOf(laneId);
  const targetIndex = index + direction;
  if (index < 0 || targetIndex < 0 || targetIndex >= orderedLaneIds.length) {
    return orderedLaneIds;
  }
  const [lane] = orderedLaneIds.splice(index, 1);
  orderedLaneIds.splice(targetIndex, 0, lane);
  return orderedLaneIds;
}

function buildRelationBadgesByEventId(
  relations: TrajectoryRelation[],
  eventById: Map<string, TrajectoryEvent>,
  externalRelianceByEventId: Map<string, ExternalRelianceIndicator[]>,
): Map<string, RelationBadge[]> {
  const badgesByEventId = new Map<string, RelationBadge[]>();
  const laneOpeningSourceRelations = new Map<string, TrajectoryRelation[]>();
  for (const relation of relations) {
    if (!auxiliaryRelationKinds.has(relation.kind)) {
      continue;
    }
    const source = eventById.get(relation.sourceEventId);
    const target = eventById.get(relation.targetEventId);
    if (!source || !target) {
      continue;
    }
    if (laneOpeningRelationKinds.has(relation.kind)) {
      const sourceRelations = laneOpeningSourceRelations.get(source.id) ?? [];
      sourceRelations.push(relation);
      laneOpeningSourceRelations.set(source.id, sourceRelations);
    } else {
      appendRelationBadge(badgesByEventId, relation, source, target, 'source');
    }
    appendRelationBadge(badgesByEventId, relation, target, source, 'target');
  }
  for (const [sourceEventId, sourceRelations] of laneOpeningSourceRelations.entries()) {
    const badges = badgesByEventId.get(sourceEventId) ?? [];
    badges.push(laneOpeningSourceBadge(sourceRelations));
    badgesByEventId.set(sourceEventId, badges);
  }
  for (const [eventId, indicators] of externalRelianceByEventId.entries()) {
    const badges = badgesByEventId.get(eventId) ?? [];
    for (const indicator of indicators) {
      badges.push({
        label: externalRelianceBadgeLabel(indicator),
        title: indicator.relation.summary || `${indicator.endpointRole} endpoint in ${indicator.ownerTrajectory.trajectoryId}`,
        external: true,
        tone: 'external',
      });
    }
    badgesByEventId.set(eventId, badges);
  }
  return badgesByEventId;
}

function laneOpeningSourceBadge(relations: TrajectoryRelation[]): RelationBadge {
  const firstKind = relations[0]?.kind ?? 'proposes_new_line';
  const isApproval = firstKind === 'approves_new_line';
  const count = relations.length;
  return {
    label: count === 1
      ? (isApproval ? 'approves lane' : 'starts lane')
      : (isApproval ? `approves ${count} lanes` : `starts ${count} lanes`),
    title: relations
      .map((relation) => relation.summary || `${relationEndpointRoleLabel(relation.kind, 'source')} ${relation.targetEventId}`)
      .join('\n'),
    tone: 'source',
  };
}

function appendRelationBadge(
  badgesByEventId: Map<string, RelationBadge[]>,
  relation: TrajectoryRelation,
  event: TrajectoryEvent,
  relatedEvent: TrajectoryEvent,
  endpointRole: 'source' | 'target',
): void {
  const badges = badgesByEventId.get(event.id) ?? [];
  badges.push({
    label: relationEndpointBadgeLabel(relation, endpointRole, relatedEvent),
    title: relation.summary || `${relationEndpointRoleLabel(relation.kind, endpointRole)} ${relatedEvent.title}`,
    tone: endpointRole,
  });
  badgesByEventId.set(event.id, badges);
}

function buildEventLaneIndexById(
  orderedLanes: TrajectoryLane[],
  eventsByLane: LaneEventMap,
): Map<string, number> {
  const laneIndexByEventId = new Map<string, number>();
  orderedLanes.forEach((lane, laneIndex) => {
    for (const event of eventsByLane.get(lane.id) ?? []) {
      laneIndexByEventId.set(event.id, laneIndex);
    }
  });
  return laneIndexByEventId;
}

function buildChildEventCountByTrajectoryId(events: TrajectoryEvent[]): Map<string, number> {
  const countByTrajectoryId = new Map<string, number>();
  for (const event of events) {
    const childTrajectoryId = event.metadata.child_trajectory_id ?? '';
    if (!childTrajectoryId) {
      continue;
    }
    const packedEventIds = event.metadata.packed_event_ids ?? '';
    const packedCount = packedEventIds
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean).length;
    if (packedCount > 0) {
      countByTrajectoryId.set(childTrajectoryId, packedCount);
    }
  }
  return countByTrajectoryId;
}

function buildDependencyProxyPlacements(
  dependencyProxies: DependencyProxy[],
  eventColumns: Map<string, number>,
  eventLaneIndexById: Map<string, number>,
): DependencyProxyPlacement[] {
  const grouped = new Map<string, DependencyProxy[]>();
  for (const proxy of dependencyProxies) {
    const group = grouped.get(proxy.dependentEventId) ?? [];
    group.push(proxy);
    grouped.set(proxy.dependentEventId, group);
  }
  const placements: DependencyProxyPlacement[] = [];
  for (const [dependentEventId, proxies] of grouped.entries()) {
    const laneIndex = eventLaneIndexById.get(dependentEventId);
    const eventColumn = eventColumns.get(dependentEventId);
    if (laneIndex === undefined || eventColumn === undefined) {
      continue;
    }
    proxies
      .slice()
      .sort((left, right) => (
        left.sourceEndpointTrajectoryId.localeCompare(right.sourceEndpointTrajectoryId)
        || left.sourceEndpointEventId.localeCompare(right.sourceEndpointEventId)
        || left.id.localeCompare(right.id)
      ))
      .forEach((proxy, index) => {
        placements.push({
          proxy,
          side: index % 2 === 0 ? 'top' : 'bottom',
          stackIndex: Math.floor(index / 2),
          laneIndex,
          eventColumn,
        });
      });
  }
  return placements;
}

function buildLaneOpeningFanouts(
  relations: TrajectoryRelation[],
  eventById: Map<string, TrajectoryEvent>,
  eventColumns: Map<string, number>,
  eventLaneIndexById: Map<string, number>,
  eventIds: Set<string>,
): LaneOpeningFanout[] {
  const grouped = new Map<string, TrajectoryRelation[]>();
  for (const relation of relations) {
    if (
      !laneOpeningRelationKinds.has(relation.kind)
      || !eventIds.has(relation.sourceEventId)
      || !eventIds.has(relation.targetEventId)
    ) {
      continue;
    }
    const source = eventById.get(relation.sourceEventId);
    const target = eventById.get(relation.targetEventId);
    if (!source || !target || source.laneId === target.laneId) {
      continue;
    }
    const group = grouped.get(relation.sourceEventId) ?? [];
    group.push(relation);
    grouped.set(relation.sourceEventId, group);
  }
  return Array.from(grouped.entries())
    .map(([sourceEventId, fanoutRelations]) => {
      const sourceColumn = eventColumns.get(sourceEventId);
      const sourceLaneIndex = eventLaneIndexById.get(sourceEventId);
      if (sourceColumn === undefined || sourceLaneIndex === undefined) {
        return null;
      }
      const sortedRelations = fanoutRelations
        .slice()
        .sort((left, right) => {
          const leftLane = eventLaneIndexById.get(left.targetEventId) ?? 0;
          const rightLane = eventLaneIndexById.get(right.targetEventId) ?? 0;
          return leftLane - rightLane
            || (eventColumns.get(left.targetEventId) ?? 0) - (eventColumns.get(right.targetEventId) ?? 0)
            || left.targetEventId.localeCompare(right.targetEventId);
        });
      return {
        sourceEventId,
        relations: sortedRelations,
        sourceColumn,
        targetColumns: sortedRelations.map((relation) => eventColumns.get(relation.targetEventId) ?? sourceColumn + 1),
        sourceLaneIndex,
        targetLaneIndexes: sortedRelations.map((relation) => eventLaneIndexById.get(relation.targetEventId) ?? sourceLaneIndex),
      };
    })
    .filter((fanout): fanout is LaneOpeningFanout => fanout !== null);
}

function computeEventColumns(
  orderedLanes: TrajectoryLane[],
  eventsByLane: LaneEventMap,
  eventById: Map<string, TrajectoryEvent>,
  relations: TrajectoryRelation[],
): Map<string, number> {
  const columns = new Map<string, number>();
  for (const lane of orderedLanes) {
    const laneEvents = eventsByLane.get(lane.id) ?? [];
    laneEvents.forEach((event, eventIndex) => {
      columns.set(event.id, eventIndex);
    });
  }

  for (let pass = 0; pass < maxColumnConstraintPasses; pass += 1) {
    let changed = false;
    for (const lane of orderedLanes) {
      const laneEvents = eventsByLane.get(lane.id) ?? [];
      for (let index = 1; index < laneEvents.length; index += 1) {
        changed = raiseColumnAtLeast(columns, laneEvents[index].id, (columns.get(laneEvents[index - 1].id) ?? 0) + 1) || changed;
      }
    }

    for (const relation of relations) {
      const source = eventById.get(relation.sourceEventId);
      const target = eventById.get(relation.targetEventId);
      if (!source || !target) {
        continue;
      }
      const sourceColumn = columns.get(source.id) ?? 0;
      const targetColumn = columns.get(target.id) ?? 0;
      if (alignmentRelationKinds.has(relation.kind)) {
        changed = raiseColumnAtLeast(columns, target.id, sourceColumn + 1) || changed;
      }
      if (relation.kind === 'merges_into') {
        changed = raiseColumnAtLeast(columns, source.id, targetColumn - 1) || changed;
      }
    }

    if (!changed) {
      break;
    }
  }
  return columns;
}

function computeLaneStartColumns(
  orderedLanes: TrajectoryLane[],
  eventsByLane: LaneEventMap,
  eventById: Map<string, TrajectoryEvent>,
  relations: TrajectoryRelation[],
  eventColumns: Map<string, number>,
): Map<string, number> {
  const laneStartColumns = new Map<string, number>();
  for (const lane of orderedLanes) {
    const firstEvent = (eventsByLane.get(lane.id) ?? [])[0];
    laneStartColumns.set(lane.id, firstEvent ? (eventColumns.get(firstEvent.id) ?? 0) - 1 : -1);
  }

  for (const relation of relations) {
    if (!laneOpeningRelationKinds.has(relation.kind)) {
      continue;
    }
    const source = eventById.get(relation.sourceEventId);
    const target = eventById.get(relation.targetEventId);
    if (!source || !target || source.laneId === target.laneId) {
      continue;
    }
    laneStartColumns.set(target.laneId, eventColumns.get(source.id) ?? 0);
  }

  for (const lane of orderedLanes) {
    const firstEvent = (eventsByLane.get(lane.id) ?? [])[0];
    if (!firstEvent) {
      continue;
    }
    const firstEventColumn = eventColumns.get(firstEvent.id) ?? 0;
    const startColumn = laneStartColumns.get(lane.id) ?? -1;
    if (startColumn >= firstEventColumn) {
      laneStartColumns.set(lane.id, firstEventColumn - 1);
    }
  }
  return laneStartColumns;
}

function raiseColumnAtLeast(columns: Map<string, number>, eventId: string, minimumColumn: number): boolean {
  const currentColumn = columns.get(eventId) ?? 0;
  if (currentColumn >= minimumColumn) {
    return false;
  }
  columns.set(eventId, minimumColumn);
  return true;
}

function buildFallbackLayout(
  lanes: TrajectoryLane[],
  events: TrajectoryEvent[],
  relations: TrajectoryRelation[],
  externalRelianceByEventId: Map<string, ExternalRelianceIndicator[]>,
  dependencyProxies: DependencyProxy[],
  reason: string,
  trajectory: LocalWorkTrajectory | null,
  laneOrderOverride: TrajectoryLane[] | null = null,
  laneOrderMode: 'weighted' | 'manual' = 'weighted',
  laneOrderControls: LaneOrderControls | null = null,
): LayoutState {
  return buildLaneLayout(
    prepareFlowElements(lanes, events, relations, externalRelianceByEventId, dependencyProxies, trajectory, laneOrderOverride, laneOrderControls),
    `Trajectory lane layout recovered from an error in ${laneOrderMode} lane order. ${reason}`,
    'fallback',
    isSchedulerStateProjection(trajectory) ? 'all' : 'focus',
  );
}

function buildLaneNode(
  lane: TrajectoryLane,
  laneIndex: number,
  startColumn: number,
  laneOrderControls: LaneOrderControls | null = null,
): Node {
  const layer = nodeVisualLayer('lane', 'buildLaneNode');
  const canMoveUp = laneOrderControls?.canMoveLaneUp(lane.id) ?? false;
  const canMoveDown = laneOrderControls?.canMoveLaneDown(lane.id) ?? false;
  return {
    id: lane.id,
    type: 'default',
    className: layeredNodeClassNames(layer, [
      `pg-lwt-lane-status-${normalizeStatus(lane.status)}`,
    ]),
    position: {
      x: laneXForColumn(startColumn),
      y: laneStartY + (laneIndex * laneStrideY),
    },
    width: laneLabelWidth,
    height: laneLabelHeight,
    data: {
      status: lane.status,
      label: (
        <div className="pg-lwt-lane-node" data-pg-lane-status={lane.status}>
          <MainFlowHandles />
          <div className="pg-lwt-lane-node-head">
            <strong>{lane.label}</strong>
            <div className="pg-lwt-lane-order-controls" aria-label={`Reorder lane ${lane.label}`}>
              <button
                type="button"
                aria-label={`Move ${lane.label} up`}
                title="Move lane up"
                disabled={!canMoveUp}
                onClick={(event) => {
                  event.stopPropagation();
                  laneOrderControls?.onMoveLaneUp(lane.id);
                }}
              >
                ↑
              </button>
              <button
                type="button"
                aria-label={`Move ${lane.label} down`}
                title="Move lane down"
                disabled={!canMoveDown}
                onClick={(event) => {
                  event.stopPropagation();
                  laneOrderControls?.onMoveLaneDown(lane.id);
                }}
              >
                ↓
              </button>
            </div>
          </div>
          <span>{lane.status}</span>
        </div>
      ),
    },
    draggable: false,
    style: mergedLayerStyle(layer, {
      width: laneLabelWidth,
      minHeight: laneLabelHeight,
      borderRadius: 8,
      border: '1px solid rgba(62, 105, 143, 0.24)',
      background: laneBackground(lane.status),
      color: '#f8fbfd',
    }),
  };
}

function buildEventNode(
  event: TrajectoryEvent,
  laneIndex: number,
  eventColumn: number,
  relationBadges: RelationBadge[],
  packedChildEventCount: number | null,
): Node {
  const isActive = event.status === 'in_progress';
  const normalizedStatus = normalizeStatus(event.status);
  const isCompound = event.kind === 'compound';
  const childTrajectoryId = event.metadata.child_trajectory_id ?? '';
  const compoundMode = event.metadata.compound_mode ?? '';
  const compoundRole = event.metadata.compound_role ?? '';
  const hasExternalReliance = relationBadges.some((badge) => badge.external);
  const layer = eventNodeVisualLayer(isActive, normalizedStatus, isCompound, compoundRole);
  return {
    id: event.id,
    type: 'default',
    className: layeredNodeClassNames(layer, [
      isActive ? 'pg-lwt-node-active' : '',
      isCompound ? 'pg-lwt-node-compound' : '',
      isCompound && compoundRole ? `pg-lwt-node-compound-role-${normalizeStatus(compoundRole)}` : '',
      hasExternalReliance ? 'pg-lwt-node-external-reliance' : '',
      `pg-lwt-node-status-${normalizedStatus}`,
    ]),
    position: {
      x: eventXForColumn(eventColumn),
      y: laneStartY + (laneIndex * laneStrideY) - 14,
    },
    width: nodeWidth,
    height: nodeHeight,
    data: {
      status: event.status,
      eventKind: event.kind,
      childTrajectoryId,
      compoundRole,
      label: (
        <div
          className="pg-lwt-event-node"
          data-pg-event-active={isActive ? 'true' : 'false'}
          data-pg-event-status={event.status}
          data-pg-child-trajectory-id={childTrajectoryId}
          data-pg-compound-role={compoundRole}
          data-pg-external-reliance={hasExternalReliance ? 'true' : 'false'}
        >
          <MainFlowHandles />
          <RelianceOverlayHandles />
          {isCompound ? (
            <div className="pg-lwt-compound-kicker">
              {compoundMode ? `Compound · ${compoundMode}` : 'Compound'}
              {packedChildEventCount !== null ? ` · ${packedChildEventCount} events` : ''}
            </div>
          ) : null}
          <strong>{event.title}</strong>
          {relationBadges.length > 0 ? (
            <div className="pg-lwt-relation-badges">
              {(relationBadges.length > maxVisibleBadges
                ? relationBadges.slice(0, maxVisibleBadges)
                : relationBadges
              ).map((badge) => (
                <span
                  className={[
                    'pg-lwt-relation-badge',
                    badge.external ? 'pg-lwt-relation-badge-external' : '',
                    badge.tone ? `pg-lwt-relation-badge-${badge.tone}` : '',
                  ].filter(Boolean).join(' ')}
                  key={`${badge.label}:${badge.title}`}
                  title={badge.title}
                >
                  {badge.label}
                </span>
              ))}
              {relationBadges.length > maxVisibleBadges ? (
                <span
                  className="pg-lwt-relation-badge pg-lwt-badge-overflow-indicator"
                  title={relationBadges
                    .slice(maxVisibleBadges)
                    .map((badge) => badge.label)
                    .join(', ')}
                >
                  +{relationBadges.length - maxVisibleBadges}
                </span>
              ) : null}
            </div>
          ) : null}
          <span>{event.kind} · {event.status} · #{event.order}</span>
        </div>
      ),
    },
    draggable: false,
    style: mergedLayerStyle(layer, {
      width: nodeWidth,
      height: nodeHeight,
      borderRadius: 8,
      border: isCompound ? compoundEventBorder(compoundRole) : eventBorder(event.status),
      background: isCompound ? compoundEventBackground(event.status) : eventBackground(event.status),
      boxShadow: isActive ? '0 12px 26px rgba(45, 102, 154, 0.18)' : undefined,
      color: '#253746',
    }),
  };
}

function eventNodeVisualLayer(
  isActive: boolean,
  normalizedStatus: string,
  isCompound: boolean,
  compoundRole: string,
): TrajectoryVisualLayerView {
  if (isActive) {
    return nodeVisualLayer('active', 'buildEventNode');
  }
  if (normalizedStatus === 'waiting' || normalizedStatus === 'blocked') {
    return nodeVisualLayer('statusAttention', 'buildEventNode');
  }
  if (isCompound && compoundRole === 'proxy') {
    return nodeVisualLayer('compoundProxy', 'buildEventNode');
  }
  if (isCompound) {
    return nodeVisualLayer('compound', 'buildEventNode');
  }
  return nodeVisualLayer('event', 'buildEventNode');
}

function buildDependencyProxyNode(placement: DependencyProxyPlacement): Node {
  const { proxy, side, stackIndex, laneIndex, eventColumn } = placement;
  const sourceTitle = proxy.sourceEndpointEvent?.title ?? proxy.sourceEndpointEventId;
  const yBase = laneStartY + (laneIndex * laneStrideY) - 14;
  const yOffset = dependencyProxyHeight + dependencyProxyOffset + (stackIndex * (dependencyProxyHeight + dependencyProxyGap));
  const layer = nodeVisualLayer('dependencyProxy', 'buildDependencyProxyNode');
  return {
    id: proxy.id,
    type: 'default',
    className: layeredNodeClassNames(layer, [
      'pg-lwt-node-dependency-proxy',
      `pg-lwt-node-dependency-proxy-${side}`,
      proxy.origin === 'external-reliance' ? 'pg-lwt-node-dependency-proxy-external' : '',
    ]),
    position: {
      x: eventXForColumn(eventColumn) + ((nodeWidth - dependencyProxyWidth) / 2),
      y: side === 'top' ? yBase - yOffset : yBase + nodeHeight + dependencyProxyOffset + (stackIndex * (dependencyProxyHeight + dependencyProxyGap)),
    },
    width: dependencyProxyWidth,
    height: dependencyProxyHeight,
    data: {
      dependencyProxyId: proxy.id,
      status: 'dependency-proxy',
      label: (
        <div
          className="pg-lwt-dependency-proxy-node"
          data-pg-dependency-proxy-id={proxy.id}
          data-pg-dependency-proxy-origin={proxy.origin}
          data-pg-dependent-event-id={proxy.dependentEventId}
        >
          <Handle
            id={dependencyProxyTopSourceHandle}
            type="source"
            position={Position.Top}
            className="pg-lwt-dependency-proxy-handle"
            isConnectable={false}
          />
          <Handle
            id={dependencyProxyBottomSourceHandle}
            type="source"
            position={Position.Bottom}
            className="pg-lwt-dependency-proxy-handle"
            isConnectable={false}
          />
          <span className="pg-lwt-dependency-proxy-kicker">inner dependency</span>
          <strong>{sourceTitle}</strong>
          <span>{proxy.sourceEndpointTrajectoryId || 'current'} · {proxy.sourceEndpointEventId}</span>
        </div>
      ),
    },
    draggable: false,
    style: mergedLayerStyle(layer, {
      width: dependencyProxyWidth,
      minHeight: dependencyProxyHeight,
      borderRadius: 8,
      border: '1px dashed rgba(95, 83, 149, 0.5)',
      background: 'rgba(246, 243, 255, 0.92)',
      color: '#3f3a68',
      boxShadow: '0 8px 18px rgba(95, 83, 149, 0.1)',
    }),
  };
}

function buildLaneOpeningJunctionNode(fanout: LaneOpeningFanout): Node {
  const layer = nodeVisualLayer('laneOpeningJunction', 'buildLaneOpeningJunctionNode');
  const minLaneIndex = Math.min(fanout.sourceLaneIndex, ...fanout.targetLaneIndexes);
  const maxLaneIndex = Math.max(fanout.sourceLaneIndex, ...fanout.targetLaneIndexes);
  const averageTargetColumn = average(fanout.targetColumns);
  const junctionColumn = Math.max(fanout.sourceColumn + 0.56, Math.min(averageTargetColumn - 0.36, fanout.sourceColumn + 0.9));
  return {
    id: laneOpeningJunctionId(fanout.sourceEventId),
    type: 'default',
    className: layeredNodeClassNames(layer, [
      'pg-lwt-node-lane-opening-junction',
    ]),
    position: {
      x: eventXForColumn(junctionColumn) - (laneOpeningJunctionSize / 2),
      y: laneStartY + (((minLaneIndex + maxLaneIndex) / 2) * laneStrideY) + (nodeHeight / 2) - 14 - (laneOpeningJunctionSize / 2),
    },
    width: laneOpeningJunctionSize,
    height: laneOpeningJunctionSize,
    data: {
      status: 'lane-opening',
      sourceEventId: fanout.sourceEventId,
      label: (
        <div className="pg-lwt-lane-opening-junction-node" title={laneOpeningFanoutLabel(fanout)}>
          <Handle
            id={mainFlowTargetHandle}
            type="target"
            position={Position.Left}
            className="pg-lwt-main-flow-handle"
            isConnectable={false}
          />
          <Handle
            id={mainFlowSourceHandle}
            type="source"
            position={Position.Right}
            className="pg-lwt-main-flow-handle"
            isConnectable={false}
          />
          <Handle
            id={fanoutTopSourceHandle}
            type="source"
            position={Position.Top}
            className="pg-lwt-main-flow-handle"
            isConnectable={false}
          />
          <Handle
            id={fanoutTopTargetHandle}
            type="target"
            position={Position.Top}
            className="pg-lwt-main-flow-handle"
            isConnectable={false}
          />
          <Handle
            id={fanoutBottomSourceHandle}
            type="source"
            position={Position.Bottom}
            className="pg-lwt-main-flow-handle"
            isConnectable={false}
          />
          <Handle
            id={fanoutBottomTargetHandle}
            type="target"
            position={Position.Bottom}
            className="pg-lwt-main-flow-handle"
            isConnectable={false}
          />
        </div>
      ),
    },
    draggable: false,
    selectable: false,
    style: mergedLayerStyle(layer, {
      width: laneOpeningJunctionSize,
      height: laneOpeningJunctionSize,
      borderRadius: laneOpeningJunctionSize,
      border: '1px solid rgba(181, 109, 84, 0.46)',
      background: 'rgba(255, 246, 240, 0.88)',
      boxShadow: '0 2px 8px rgba(181, 109, 84, 0.14)',
    }),
  };
}

function MainFlowHandles(): React.ReactElement {
  return (
    <>
      <Handle
        id={mainFlowSourceHandle}
        type="source"
        position={Position.Right}
        className="pg-lwt-main-flow-handle"
        isConnectable={false}
      />
      <Handle
        id={mainFlowTargetHandle}
        type="target"
        position={Position.Left}
        className="pg-lwt-main-flow-handle"
        isConnectable={false}
      />
    </>
  );
}

function RelianceOverlayHandles(): React.ReactElement {
  return (
    <>
      <Handle
        id={relianceTopSourceHandle}
        type="source"
        position={Position.Top}
        className="pg-lwt-reliance-handle"
        isConnectable={false}
      />
      <Handle
        id={relianceTopTargetHandle}
        type="target"
        position={Position.Top}
        className="pg-lwt-reliance-handle"
        isConnectable={false}
      />
      <Handle
        id={relianceBottomSourceHandle}
        type="source"
        position={Position.Bottom}
        className="pg-lwt-reliance-handle"
        isConnectable={false}
      />
      <Handle
        id={relianceBottomTargetHandle}
        type="target"
        position={Position.Bottom}
        className="pg-lwt-reliance-handle"
        isConnectable={false}
      />
    </>
  );
}

function laneXForColumn(column: number): number {
  return column < 0 ? laneStartX : eventXForColumn(column);
}

function eventXForColumn(column: number): number {
  return eventStartX + (column * eventStrideX);
}

function average(values: number[]): number {
  if (values.length === 0) {
    return 0;
  }
  return values.reduce((total, value) => total + value, 0) / values.length;
}

function buildLaneLayout(
  prepared: PreparedFlowElements,
  message: string,
  mode: 'lanes' | 'fallback' = 'lanes',
  fitMode: 'all' | 'focus' = 'focus',
): LayoutState {
  return {
    nodes: prepared.nodes,
    edges: prepared.edges,
    mode,
    message,
    activeEventId: prepared.activeEventId,
    focusEventId: prepared.focusEventId,
    fitMode,
  };
}

function findActiveEventId(
  orderedLanes: TrajectoryLane[],
  eventsByLane: Map<string, TrajectoryEvent[]>,
): string | null {
  for (const lane of orderedLanes) {
    const activeEvent = (eventsByLane.get(lane.id) ?? []).find((event) => event.status === 'in_progress');
    if (activeEvent) {
      return activeEvent.id;
    }
  }
  return null;
}

function findFocusEventId(
  orderedLanes: TrajectoryLane[],
  eventsByLane: Map<string, TrajectoryEvent[]>,
): string | null {
  const preferredStatuses = ['blocked', 'waiting', 'pending', 'completed', 'archived'];
  const allEvents = orderedLanes.flatMap((lane) => eventsByLane.get(lane.id) ?? []);
  for (const status of preferredStatuses) {
    const event = allEvents.find((candidate) => candidate.status === status);
    if (event) {
      return event.id;
    }
  }
  return allEvents.at(-1)?.id ?? null;
}

function buildFocusedViewport(activeNode: Node | undefined): { x: number; y: number; zoom: number } {
  const zoom = 0.92;
  if (!activeNode) {
    return { x: 42, y: 64, zoom };
  }
  return {
    x: (-activeNode.position.x * zoom) + 300,
    y: (-activeNode.position.y * zoom) + 96,
    zoom,
  };
}

function buildTopAlignedViewport(nodes: Node[], activeNode: Node | undefined): { x: number; y: number; zoom: number } {
  if (nodes.length === 0) {
    return buildFocusedViewport(activeNode);
  }
  const eventNodes = nodes.filter((node) => isEventNode(node) || isDependencyProxyNode(node));
  const measuredNodes = eventNodes.length > 0 ? eventNodes : nodes;
  const bounds = measuredNodes.reduce(
    (current, node) => {
      const width = typeof node.width === 'number' ? node.width : nodeWidth;
      const height = typeof node.height === 'number' ? node.height : nodeHeight;
      return {
        minX: Math.min(current.minX, node.position.x),
        minY: Math.min(current.minY, node.position.y),
        maxX: Math.max(current.maxX, node.position.x + width),
        maxY: Math.max(current.maxY, node.position.y + height),
      };
    },
    {
      minX: Number.POSITIVE_INFINITY,
      minY: Number.POSITIVE_INFINITY,
      maxX: Number.NEGATIVE_INFINITY,
      maxY: Number.NEGATIVE_INFINITY,
    },
  );
  const graphWidth = Math.max(1, bounds.maxX - bounds.minX);
  const graphHeight = Math.max(1, bounds.maxY - bounds.minY);
  const zoom = Math.min(1.02, Math.max(0.32, Math.min(fullFitTargetWidth / graphWidth, fullFitTargetHeight / graphHeight)));
  return {
    x: Math.max(42, 110 - (bounds.minX * zoom)),
    y: 72 - (bounds.minY * zoom),
    zoom,
  };
}

function buildFlowEdge(source: string, target: string, kind: string): Edge {
  const isSequence = kind === 'sequence';
  const relationStyle = edgeStyleForKind(kind);
  const layer = edgeVisualLayer('sequence', 'buildFlowEdge');
  return {
    id: `${source}->${target}:${kind}`,
    source,
    target,
    sourceHandle: mainFlowSourceHandle,
    targetHandle: mainFlowTargetHandle,
    label: isSequence ? undefined : relationStyle.label,
    className: layeredEdgeClassNames(layer, [
      `pg-lwt-edge-${normalizeStatus(kind)}`,
    ]),
    type: isSequence ? 'straight' : 'smoothstep',
    markerEnd: {
      type: MarkerType.ArrowClosed,
      width: 16,
      height: 16,
    },
    style: mergedLayerStyle(layer, {
      stroke: isSequence ? '#6f8fab' : relationStyle.stroke,
      strokeDasharray: isSequence ? undefined : relationStyle.strokeDasharray,
      strokeWidth: isSequence ? 2 : relationStyle.strokeWidth,
    }),
  };
}

function buildLaneOpeningFanoutEdges(fanout: LaneOpeningFanout): Edge[] {
  const relationStyle = edgeStyleForKind(fanout.relations[0]?.kind ?? 'proposes_new_line');
  const layer = edgeVisualLayer('laneOpening', 'buildLaneOpeningFanoutEdges');
  const junctionId = laneOpeningJunctionId(fanout.sourceEventId);
  const minLaneIndex = Math.min(fanout.sourceLaneIndex, ...fanout.targetLaneIndexes);
  const maxLaneIndex = Math.max(fanout.sourceLaneIndex, ...fanout.targetLaneIndexes);
  const junctionLaneCenter = (minLaneIndex + maxLaneIndex) / 2;

  const trunkSourceHandle = fanout.sourceLaneIndex < junctionLaneCenter
    ? relianceBottomSourceHandle
    : fanout.sourceLaneIndex > junctionLaneCenter
      ? relianceTopSourceHandle
      : mainFlowSourceHandle;
  const trunkTargetHandle = fanout.sourceLaneIndex < junctionLaneCenter
    ? fanoutTopTargetHandle
    : fanout.sourceLaneIndex > junctionLaneCenter
      ? fanoutBottomTargetHandle
      : mainFlowTargetHandle;

  const trunk: Edge = {
    id: `${fanout.sourceEventId}->${junctionId}:lane-opening-trunk`,
    source: fanout.sourceEventId,
    target: junctionId,
    sourceHandle: trunkSourceHandle,
    targetHandle: trunkTargetHandle,
    label: laneOpeningFanoutLabel(fanout),
    className: layeredEdgeClassNames(layer, [
      'pg-lwt-edge-lane-opening-fanout',
      'pg-lwt-edge-lane-opening-trunk',
    ]),
    type: 'step',
    interactionWidth: 18,
    style: mergedLayerStyle(layer, {
      stroke: relationStyle.stroke,
      strokeDasharray: relationStyle.strokeDasharray,
      strokeWidth: Math.max(1.8, relationStyle.strokeWidth - 0.3),
      opacity: 0.54,
    }),
  };
  const branches = fanout.relations.map((relation): Edge => {
    const targetLaneIndex = fanout.targetLaneIndexes[fanout.relations.indexOf(relation)] ?? fanout.sourceLaneIndex;
    const branchSourceHandle = targetLaneIndex > junctionLaneCenter
      ? fanoutBottomSourceHandle
      : targetLaneIndex < junctionLaneCenter
        ? fanoutTopSourceHandle
        : mainFlowSourceHandle;
    const branchTargetHandle = targetLaneIndex > junctionLaneCenter
      ? relianceTopTargetHandle
      : targetLaneIndex < junctionLaneCenter
        ? relianceBottomTargetHandle
        : mainFlowTargetHandle;
    return {
      id: `${junctionId}->${relation.targetEventId}:${relation.kind}:lane-opening-branch`,
      source: junctionId,
      target: relation.targetEventId,
      sourceHandle: branchSourceHandle,
      targetHandle: branchTargetHandle,
      className: layeredEdgeClassNames(layer, [
        'pg-lwt-edge-lane-opening-fanout',
        'pg-lwt-edge-lane-opening-branch',
        `pg-lwt-edge-${normalizeStatus(relation.kind)}`,
      ]),
      type: 'step',
      interactionWidth: 12,
      markerEnd: {
        type: MarkerType.ArrowClosed,
        width: 12,
        height: 12,
      },
      style: mergedLayerStyle(layer, {
        stroke: edgeStyleForKind(relation.kind).stroke,
        strokeDasharray: '2 6',
        strokeWidth: 1.6,
        opacity: 0.48,
      }),
    };
  });
  return [trunk, ...branches];
}

function buildRelationEdge(relation: TrajectoryRelation): Edge {
  const relationStyle = edgeStyleForKind(relation.kind);
  const projection = relation.metadata.relation_projection ?? '';
  const label = relationGraphLabel(relation);
  const layer = edgeVisualLayer(relationEdgeVisualLayerId(relation.kind), 'buildRelationEdge');
  return {
    id: relationEdgeId(relation),
    source: relation.sourceEventId,
    target: relation.targetEventId,
    sourceHandle: mainFlowSourceHandle,
    targetHandle: mainFlowTargetHandle,
    label: label || undefined,
    className: layeredEdgeClassNames(layer, [
      `pg-lwt-edge-${normalizeStatus(relation.kind)}`,
      projection ? `pg-lwt-edge-projection-${normalizeStatus(projection)}` : '',
      relation.kind === 'depends_on' ? `pg-lwt-edge-dependency-scope-${dependencyScope(relation)}` : '',
    ]),
    type: 'smoothstep',
    interactionWidth: relation.kind === 'depends_on' && dependencyScope(relation) === 'inner' ? 22 : 14,
    markerEnd: {
      type: MarkerType.ArrowClosed,
      width: 16,
      height: 16,
    },
    style: mergedLayerStyle(layer, {
      stroke: relationStyle.stroke,
      strokeDasharray: relationStyle.strokeDasharray,
      strokeWidth: projection ? relationStyle.strokeWidth + 0.4 : relationStyle.strokeWidth,
    }),
  };
}

function buildRelianceOverlayEdge(
  relation: TrajectoryRelation,
  eventLaneIndexById: Map<string, number>,
): Edge {
  const relationStyle = edgeStyleForKind(relation.kind);
  const handles = relianceOverlayHandles(relation, eventLaneIndexById);
  const projection = relation.metadata.relation_projection ?? '';
  const label = relationGraphLabel(relation);
  const layer = edgeVisualLayer('relianceOverlay', 'buildRelianceOverlayEdge');
  return {
    id: relationEdgeId(relation, ':reliance-overlay'),
    source: relation.sourceEventId,
    target: relation.targetEventId,
    sourceHandle: handles.sourceHandle,
    targetHandle: handles.targetHandle,
    label: label || undefined,
    className: layeredEdgeClassNames(layer, [
      `pg-lwt-edge-${normalizeStatus(relation.kind)}`,
      'pg-lwt-edge-reliance-overlay',
      projection ? `pg-lwt-edge-projection-${normalizeStatus(projection)}` : '',
      relation.kind === 'depends_on' ? `pg-lwt-edge-dependency-scope-${dependencyScope(relation)}` : '',
    ]),
    type: 'smoothstep',
    interactionWidth: relation.kind === 'depends_on' && dependencyScope(relation) === 'inner' ? 22 : 14,
    markerEnd: {
      type: MarkerType.ArrowClosed,
      width: 14,
      height: 14,
    },
    style: mergedLayerStyle(layer, {
      stroke: relationStyle.stroke,
      strokeDasharray: projection ? projectionStrokeDasharray(projection, relationStyle.strokeDasharray) : relationStyle.strokeDasharray,
      strokeWidth: projection ? relationStyle.strokeWidth + 0.4 : relationStyle.strokeWidth,
      opacity: projection ? 0.9 : 0.78,
    }),
  };
}

function buildDependencyProxyEdge(placement: DependencyProxyPlacement): Edge {
  const layer = edgeVisualLayer('dependencyProxy', 'buildDependencyProxyEdge');
  return {
    id: `${placement.proxy.id}->${placement.proxy.dependentEventId}`,
    source: placement.proxy.id,
    target: placement.proxy.dependentEventId,
    sourceHandle: placement.side === 'top' ? dependencyProxyBottomSourceHandle : dependencyProxyTopSourceHandle,
    targetHandle: placement.side === 'top' ? relianceTopTargetHandle : relianceBottomTargetHandle,
    className: layeredEdgeClassNames(layer, [
      'pg-lwt-edge-dependency-proxy',
      placement.proxy.origin === 'external-reliance' ? 'pg-lwt-edge-dependency-proxy-external' : '',
    ]),
    type: 'smoothstep',
    markerEnd: {
      type: MarkerType.ArrowClosed,
      width: 12,
      height: 12,
    },
    style: mergedLayerStyle(layer, {
      stroke: '#7366a8',
      strokeDasharray: '3 3',
      strokeWidth: 1.8,
      opacity: 0.72,
    }),
  };
}

function relationEdgeVisualLayerId(kind: string): TrajectoryEdgeVisualLayerId {
  if (kind === 'merges_into') {
    return 'merge';
  }
  if (laneOpeningRelationKinds.has(kind)) {
    return 'laneOpening';
  }
  return 'relation';
}

function relianceOverlayHandles(
  relation: TrajectoryRelation,
  eventLaneIndexById: Map<string, number>,
): { sourceHandle: string; targetHandle: string } {
  const sourceLaneIndex = eventLaneIndexById.get(relation.sourceEventId) ?? 0;
  const targetLaneIndex = eventLaneIndexById.get(relation.targetEventId) ?? sourceLaneIndex;
  if (sourceLaneIndex < targetLaneIndex) {
    return {
      sourceHandle: relianceBottomSourceHandle,
      targetHandle: relianceTopTargetHandle,
    };
  }
  if (sourceLaneIndex > targetLaneIndex) {
    return {
      sourceHandle: relianceTopSourceHandle,
      targetHandle: relianceBottomTargetHandle,
    };
  }
  return {
    sourceHandle: relianceTopSourceHandle,
    targetHandle: relianceTopTargetHandle,
  };
}

function edgeStyleForKind(kind: string): {
  label: string;
  stroke: string;
  strokeDasharray?: string;
  strokeWidth: number;
} {
  switch (kind) {
    case 'merges_into':
      return { label: 'merge', stroke: '#2f7f70', strokeDasharray: '7 5', strokeWidth: 3 };
    case 'proposes_new_line':
      return { label: 'starts lane', stroke: '#b56d54', strokeDasharray: '5 4', strokeWidth: 2.5 };
    case 'depends_on':
      return { label: 'depends', stroke: '#7366a8', strokeDasharray: '4 4', strokeWidth: 2.4 };
    case 'waits_for':
      return { label: 'waits', stroke: '#a5762a', strokeDasharray: '2 5', strokeWidth: 2.4 };
    case 'unblocks':
      return { label: 'unblocks', stroke: '#4f936f', strokeDasharray: '8 4', strokeWidth: 2.6 };
    case 'hands_off':
      return { label: 'handoff', stroke: '#536f9f', strokeDasharray: '6 3', strokeWidth: 2.4 };
    case 'syncs_from':
      return { label: 'sync', stroke: '#5a8995', strokeDasharray: '3 3', strokeWidth: 2.4 };
    case 'approves_new_line':
      return { label: 'approved', stroke: '#6f8d44', strokeDasharray: '5 3', strokeWidth: 2.6 };
    default:
      return { label: kind, stroke: '#7e8791', strokeDasharray: '4 4', strokeWidth: 2.2 };
  }
}

function projectionStrokeDasharray(projection: string, fallback: string | undefined): string {
  switch (projection) {
    case 'cross-compound':
      return '10 4 2 4';
    case 'cross-boundary':
      return '7 4';
    default:
      return fallback ?? '4 4';
  }
}

function relationGraphLabel(relation: TrajectoryRelation): string {
  if (relation.kind === 'depends_on') {
    return dependencyScope(relation) === 'inner' ? '' : 'node dep';
  }
  return edgeStyleForKind(relation.kind).label;
}

function relationDetailTitle(relation: TrajectoryRelation): string {
  if (relation.kind === 'depends_on') {
    return dependencyScope(relation) === 'inner' ? 'Internal dependency' : 'Node dependency';
  }
  return edgeStyleForKind(relation.kind).label;
}

function dependencyScope(relation: TrajectoryRelation): 'inner' | 'node' {
  return hasPreciseEndpointMetadata(relation) ? 'inner' : 'node';
}

function dependencyScopeDescription(relation: TrajectoryRelation): string {
  return dependencyScope(relation) === 'inner'
    ? 'internal child endpoint dependency'
    : 'visible node dependency';
}

function hasPreciseEndpointMetadata(relation: TrajectoryRelation): boolean {
  return Boolean(
    relation.metadata.source_endpoint_trajectory_id
    || relation.metadata.source_endpoint_event_id
    || relation.metadata.target_endpoint_trajectory_id
    || relation.metadata.target_endpoint_event_id,
  );
}

function relationEndpointRoleLabel(kind: string, endpointRole: 'source' | 'target'): string {
  switch (kind) {
    case 'depends_on':
      return endpointRole === 'source' ? 'Provider' : 'Dependent';
    case 'waits_for':
      return endpointRole === 'source' ? 'Waiting event' : 'Wait target';
    case 'unblocks':
      return endpointRole === 'source' ? 'Unblocker' : 'Unblocked event';
    case 'hands_off':
      return endpointRole === 'source' ? 'Handoff source' : 'Handoff receiver';
    case 'syncs_from':
      return endpointRole === 'source' ? 'Sync consumer' : 'Sync source';
    case 'proposes_new_line':
    case 'approves_new_line':
      return endpointRole === 'source' ? 'Lane start source' : 'New lane';
    case 'merges_into':
      return endpointRole === 'source' ? 'Merge source' : 'Merge target';
    default:
      return endpointRole === 'source' ? 'Source' : 'Target';
  }
}

function relationPreciseEndpointLabel(kind: string, endpointRole: 'source' | 'target'): string {
  return `${relationEndpointRoleLabel(kind, endpointRole)} precise endpoint`;
}

function relationEndpointBadgeLabel(
  relation: TrajectoryRelation,
  endpointRole: 'source' | 'target',
  relatedEvent: TrajectoryEvent,
): string {
  switch (relation.kind) {
    case 'depends_on':
      return endpointRole === 'source'
        ? `required by #${relatedEvent.order}`
        : `depends on #${relatedEvent.order}`;
    case 'waits_for':
      return endpointRole === 'source'
        ? `waits for #${relatedEvent.order}`
        : `blocks #${relatedEvent.order}`;
    case 'unblocks':
      return endpointRole === 'source'
        ? `unblocks #${relatedEvent.order}`
        : `unblocked by #${relatedEvent.order}`;
    case 'hands_off':
      return endpointRole === 'source'
        ? `hands to #${relatedEvent.order}`
        : `receives #${relatedEvent.order}`;
    case 'syncs_from':
      return endpointRole === 'source'
        ? `syncs from #${relatedEvent.order}`
        : `syncs to #${relatedEvent.order}`;
    case 'proposes_new_line':
      return endpointRole === 'source'
        ? 'starts lane'
        : 'lane start';
    case 'approves_new_line':
      return endpointRole === 'source'
        ? 'approves lane'
        : 'lane approved';
    default:
      return endpointRole === 'source'
        ? `to #${relatedEvent.order}`
        : `from #${relatedEvent.order}`;
  }
}

function externalRelianceBadgeLabel(indicator: ExternalRelianceIndicator): string {
  if (indicator.relation.kind === 'depends_on') {
    return indicator.endpointRole === 'source' ? 'required external' : 'depends external';
  }
  return `${relationEndpointRoleLabel(indicator.relation.kind, indicator.endpointRole).toLowerCase()} external`;
}

function emptyLayout(mode: 'pending', message: string): LayoutState {
  return {
    nodes: [],
    edges: [],
    mode,
    message,
    activeEventId: null,
    focusEventId: null,
    fitMode: 'focus',
  };
}

function normalizeStatus(status: string): string {
  return status.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'unknown';
}

function laneBackground(status: string): string {
  switch (status) {
    case 'blocked':
      return '#8b4b50';
    case 'waiting':
      return '#87662f';
    case 'done':
      return '#3f765d';
    default:
      return '#315f7e';
  }
}

function eventBorder(status: string): string {
  switch (status) {
    case 'in_progress':
      return '1px solid rgba(44, 119, 186, 0.5)';
    case 'blocked':
      return '1px solid rgba(199, 95, 95, 0.34)';
    case 'waiting':
      return '1px solid rgba(184, 138, 46, 0.36)';
    case 'completed':
      return '1px solid rgba(79, 147, 111, 0.26)';
    case 'archived':
      return '1px solid rgba(117, 130, 144, 0.22)';
    default:
      return '1px solid rgba(64, 105, 142, 0.18)';
  }
}

function compoundEventBorder(role: string): string {
  if (role === 'proxy') {
    return '1px dashed rgba(72, 100, 154, 0.54)';
  }
  return '1px solid rgba(72, 100, 154, 0.68)';
}

function eventBackground(status: string): string {
  switch (status) {
    case 'in_progress':
      return '#f4faff';
    case 'blocked':
      return '#fff6f5';
    case 'waiting':
      return '#fff9e8';
    case 'completed':
      return '#f6fbf7';
    case 'archived':
      return '#f5f6f7';
    default:
      return '#ffffff';
  }
}

function compoundEventBackground(status: string): string {
  switch (status) {
    case 'in_progress':
      return 'linear-gradient(135deg, #f3f7ff 0%, #f8fbff 58%, #eef5fb 100%)';
    case 'completed':
      return 'linear-gradient(135deg, #f3fbf6 0%, #ffffff 58%, #eaf5ef 100%)';
    default:
      return 'linear-gradient(135deg, #f7f8ff 0%, #ffffff 58%, #eef2fa 100%)';
  }
}

function formatErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

function formatTimestamp(value: string | null): string {
  if (!value) {
    return 'unknown';
  }
  const parsed = new Date(value);
  return Number.isNaN(parsed.valueOf()) ? value : parsed.toLocaleString('zh-CN', { hour12: false });
}

function compactMetadataRows(
  metadata: Record<string, string>,
  preferredKeys: string[],
): [string, string][] {
  const rows: [string, string][] = [];
  const seen = new Set<string>();
  for (const key of preferredKeys) {
    const value = metadata[key];
    if (value) {
      rows.push([key, value]);
      seen.add(key);
    }
  }
  for (const [key, value] of Object.entries(metadata)) {
    if (!seen.has(key) && value) {
      rows.push([key, value]);
    }
  }
  return rows.slice(0, 8);
}

function endpointMetadataRows(prefix: 'source' | 'target', metadata: Record<string, string>): [string, string][] {
  const keys = [
    `${prefix}_endpoint_trajectory_id`,
    `${prefix}_endpoint_event_id`,
    `${prefix}_endpoint_parent_event_id`,
    `${prefix}_endpoint_compound_path`,
  ];
  return keys
    .map((key): [string, string] => [key, metadata[key] ?? ''])
    .filter(([, value]) => value.length > 0);
}

function formatEventReference(event: TrajectoryEvent | null, fallbackEventId: string): string {
  return event ? `${event.title} (#${event.order}, ${event.id})` : fallbackEventId;
}

function formatMetadataKey(key: string): string {
  return key.replace(/_/g, ' ');
}

main();
