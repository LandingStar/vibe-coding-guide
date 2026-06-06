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
};

type LayoutState = {
  nodes: Node[];
  edges: Edge[];
  mode: 'pending' | 'lanes' | 'fallback';
  message: string;
  activeEventId: string | null;
  focusEventId: string | null;
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
};

const nodeWidth = 190;
const nodeHeight = 82;
const laneLabelWidth = 170;
const laneLabelHeight = 54;
const laneStartX = 0;
const laneStartY = 0;
const laneStrideY = 142;
const eventStartX = laneLabelWidth + 96;
const eventStrideX = nodeWidth + 70;
const fullFitNodeLimit = 12;
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
]);
const relianceRelationKinds = new Set([
  'depends_on',
  'waits_for',
  'syncs_from',
]);
const relianceTopSourceHandle = 'reliance-top-source';
const relianceTopTargetHandle = 'reliance-top-target';
const relianceBottomSourceHandle = 'reliance-bottom-source';
const relianceBottomTargetHandle = 'reliance-bottom-target';
const mainFlowSourceHandle = 'main-flow-source';
const mainFlowTargetHandle = 'main-flow-target';

function main(): void {
  const mount = document.getElementById('pgHostLocalWorkTrajectoryRoot');
  if (!(mount instanceof HTMLElement)) {
    return;
  }
  const payload = readPayload();
  const error = mount.dataset.pgTrajectoryError || '';
  createRoot(mount).render(
    <React.StrictMode>
      <TrajectoryApp trajectory={payload} error={error} />
    </React.StrictMode>,
  );
}

function readPayload(): LocalWorkTrajectory | null {
  const element = document.getElementById('pgHostLocalWorkTrajectoryPayload');
  if (!element?.textContent) {
    return null;
  }
  try {
    return JSON.parse(element.textContent) as LocalWorkTrajectory;
  } catch {
    return null;
  }
}

function TrajectoryApp({
  trajectory,
  error,
}: {
  trajectory: LocalWorkTrajectory | null;
  error: string;
}): React.ReactElement {
  const [layout, setLayout] = useState<LayoutState>(emptyLayout('pending', 'Building trajectory layout...'));
  const lanes = trajectory?.lanes ?? [];
  const events = trajectory?.events ?? [];
  const relations = trajectory?.relations ?? [];
  const hasLane = lanes.length > 0;
  const isEmptyLifecycle = Boolean(
    trajectory
    && !hasLane
    && trajectory.metadata?.projection === 'single-lane-lifecycle'
    && trajectory.metadata?.lifecycle_state === 'empty',
  );

  useEffect(() => {
    if (!trajectory || !hasLane) {
      setLayout(emptyLayout('pending', 'No trajectory payload is available.'));
      return;
    }
    try {
      setLayout(buildLayout(lanes, events, relations));
    } catch (layoutError) {
      setLayout(buildFallbackLayout(
        lanes,
        events,
        relations,
        formatErrorMessage(layoutError),
      ));
    }
  }, [trajectory, hasLane, lanes, events, relations]);

  const metrics = useMemo(() => {
    return {
      lanes: lanes.length,
      events: events.length,
      relations: relations.length,
    };
  }, [lanes.length, events.length, relations.length]);

  if (error) {
    return (
      <Shell status="failed" title="局部工作轨迹加载失败" subtitle={error}>
        <p className="pg-lwt-empty">修复 local-work-trajectory artifact 后刷新预览。</p>
      </Shell>
    );
  }

  if (isEmptyLifecycle) {
    return (
      <Shell status="empty" title={trajectory?.title ?? 'Local Work Trajectory'} subtitle="No local trajectory has been started in this workspace.">
        <p className="pg-lwt-empty">The agent will create the first lane and active event when it starts a tracked task.</p>
      </Shell>
    );
  }

  if (!trajectory || !hasLane) {
    return (
      <Shell status="unavailable" title="局部工作轨迹未就绪" subtitle="等待 local-work-trajectory artifact 生成。">
        <p className="pg-lwt-empty">刷新 progress graph 后会先生成单线轨迹 artifact。</p>
      </Shell>
    );
  }

  return (
    <Shell
      status="available"
      title={trajectory.title}
      subtitle={`trajectory_id=${trajectory.trajectoryId} · guide=${trajectory.guideContext ?? 'unknown'} · recorded_at=${formatTimestamp(trajectory.recordedAt)}`}
      metrics={[
        ['Mode', 'React Flow lanes'],
        ['Layout', layout.mode],
        ['Lanes', String(metrics.lanes)],
        ['Events', String(metrics.events)],
        ['Relations', String(metrics.relations)],
      ]}
    >
      <div className="pg-lwt-flow" aria-label="Local work trajectory graph">
        <ReactFlowProvider>
          <TrajectoryFlow layout={layout} />
        </ReactFlowProvider>
      </div>
    </Shell>
  );
}

function TrajectoryFlow({ layout }: { layout: LayoutState }): React.ReactElement {
  const { fitView, setViewport } = useReactFlow();
  const shouldFitEntireGraph = layout.mode === 'lanes' && layout.nodes.length <= fullFitNodeLimit;
  const activeNode = layout.activeEventId
    ? layout.nodes.find((node) => node.id === layout.activeEventId)
    : layout.focusEventId
      ? layout.nodes.find((node) => node.id === layout.focusEventId)
    : undefined;

  useEffect(() => {
    if (layout.nodes.length === 0) {
      return;
    }
    const frame = window.requestAnimationFrame(() => {
      if (shouldFitEntireGraph) {
        fitView({ padding: 0.2, minZoom: 0.01, maxZoom: 1.4, duration: 180 });
        return;
      }
      setViewport(buildFocusedViewport(activeNode), { duration: 180 });
    });
    return () => {
      window.cancelAnimationFrame(frame);
    };
  }, [activeNode, fitView, layout.activeEventId, layout.edges.length, layout.nodes.length, setViewport, shouldFitEntireGraph]);

  return (
    <>
      <ReactFlow
        nodes={layout.nodes}
        edges={layout.edges}
        fitView={shouldFitEntireGraph}
        fitViewOptions={{ padding: 0.2, minZoom: 0.01, maxZoom: 1.4 }}
        minZoom={0.01}
        maxZoom={1.8}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable
        proOptions={{ hideAttribution: true }}
      >
        <Background color="rgba(70, 95, 116, 0.16)" gap={22} />
        <MiniMap
          pannable
          zoomable
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
        />
        <Controls showInteractive={false} />
      </ReactFlow>
      {layout.message ? (
        <div className="pg-lwt-layout-note" data-pg-lwt-layout-mode={layout.mode}>{layout.message}</div>
      ) : null}
    </>
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
): LayoutState {
  return buildLaneLayout(prepareFlowElements(lanes, events, relations), '');
}

function prepareFlowElements(
  lanes: TrajectoryLane[],
  events: TrajectoryEvent[],
  relations: TrajectoryRelation[],
): PreparedFlowElements {
  const orderedLanes = orderLanes(lanes, events, relations);
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
  const relationBadgesByEventId = buildRelationBadgesByEventId(relations, eventById);
  const eventLaneIndexById = buildEventLaneIndexById(orderedLanes, eventsByLane);
  const nodes: Node[] = [];
  const sequenceEdges: Edge[] = [];
  orderedLanes.forEach((lane, laneIndex) => {
    const laneEvents = eventsByLane.get(lane.id) ?? [];
    nodes.push(buildLaneNode(lane, laneIndex, laneStartColumns.get(lane.id) ?? -1));
    nodes.push(...laneEvents.map((event, eventIndex) => buildEventNode(
      event,
      laneIndex,
      eventColumns.get(event.id) ?? eventIndex,
      relationBadgesByEventId.get(event.id) ?? [],
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
  const focusEventId = activeEventId ?? findFocusEventId(orderedLanes, eventsByLane);
  return { nodes, edges: [...sequenceEdges, ...relationEdges, ...relianceEdges], activeEventId, focusEventId };
}

function orderLanes(
  lanes: TrajectoryLane[],
  events: TrajectoryEvent[],
  relations: TrajectoryRelation[],
): TrajectoryLane[] {
  const laneById = new Map(lanes.map((lane) => [lane.id, lane]));
  const eventById = new Map(events.map((event) => [event.id, event]));
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
    for (const child of childrenByParent.get(laneId) ?? []) {
      visitLane(child.childLaneId);
    }
  };

  for (const lane of roots) {
    visitLane(lane.id);
  }
  for (const lane of lanes.slice().sort(compareLaneRoots)) {
    visitLane(lane.id);
  }
  return ordered;
}

function compareLaneRoots(left: TrajectoryLane, right: TrajectoryLane): number {
  const leftRank = left.id === 'lane:main' ? 0 : 1;
  const rightRank = right.id === 'lane:main' ? 0 : 1;
  return leftRank - rightRank || left.id.localeCompare(right.id);
}

function buildRelationBadgesByEventId(
  relations: TrajectoryRelation[],
  eventById: Map<string, TrajectoryEvent>,
): Map<string, RelationBadge[]> {
  const badgesByEventId = new Map<string, RelationBadge[]>();
  for (const relation of relations) {
    if (!auxiliaryRelationKinds.has(relation.kind)) {
      continue;
    }
    const source = eventById.get(relation.sourceEventId);
    const target = eventById.get(relation.targetEventId);
    if (!source || !target) {
      continue;
    }
    const badgeEventId = relation.kind === 'depends_on' || relation.kind === 'waits_for' || relation.kind === 'syncs_from'
      ? source.id
      : target.id;
    const relatedEvent = badgeEventId === source.id ? target : source;
    const badges = badgesByEventId.get(badgeEventId) ?? [];
    badges.push({
      label: `${edgeStyleForKind(relation.kind).label} #${relatedEvent.order}`,
      title: relation.summary || relatedEvent.title,
    });
    badgesByEventId.set(badgeEventId, badges);
  }
  return badgesByEventId;
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
  reason: string,
): LayoutState {
  return buildLaneLayout(
    prepareFlowElements(lanes, events, relations),
    `Trajectory lane layout recovered from an error. ${reason}`,
    'fallback',
  );
}

function buildLaneNode(lane: TrajectoryLane, laneIndex: number, startColumn: number): Node {
  return {
    id: lane.id,
    type: 'default',
    className: `pg-lwt-lane-status-${normalizeStatus(lane.status)}`,
    position: {
      x: laneXForColumn(startColumn),
      y: laneStartY + (laneIndex * laneStrideY),
    },
    data: {
      status: lane.status,
      label: (
        <div className="pg-lwt-lane-node" data-pg-lane-status={lane.status}>
          <MainFlowHandles />
          <strong>{lane.label}</strong>
          <span>{lane.status}</span>
        </div>
      ),
    },
    draggable: false,
    style: {
      width: laneLabelWidth,
      minHeight: laneLabelHeight,
      borderRadius: 8,
      border: '1px solid rgba(62, 105, 143, 0.24)',
      background: laneBackground(lane.status),
      color: '#f8fbfd',
    },
  };
}

function buildEventNode(
  event: TrajectoryEvent,
  laneIndex: number,
  eventColumn: number,
  relationBadges: RelationBadge[],
): Node {
  const isActive = event.status === 'in_progress';
  const normalizedStatus = normalizeStatus(event.status);
  return {
    id: event.id,
    type: 'default',
    className: [
      isActive ? 'pg-lwt-node-active' : '',
      `pg-lwt-node-status-${normalizedStatus}`,
    ].filter(Boolean).join(' '),
    position: {
      x: eventXForColumn(eventColumn),
      y: laneStartY + (laneIndex * laneStrideY) - 14,
    },
    data: {
      status: event.status,
      label: (
        <div
          className="pg-lwt-event-node"
          data-pg-event-active={isActive ? 'true' : 'false'}
          data-pg-event-status={event.status}
        >
          <MainFlowHandles />
          <RelianceOverlayHandles />
          <strong>{event.title}</strong>
          {relationBadges.length > 0 ? (
            <div className="pg-lwt-relation-badges">
              {relationBadges.map((badge) => (
                <span className="pg-lwt-relation-badge" key={`${badge.label}:${badge.title}`} title={badge.title}>
                  {badge.label}
                </span>
              ))}
            </div>
          ) : null}
          <span>{event.kind} · {event.status} · #{event.order}</span>
        </div>
      ),
    },
    draggable: false,
    style: {
      width: nodeWidth,
      minHeight: nodeHeight,
      borderRadius: 8,
      border: eventBorder(event.status),
      background: eventBackground(event.status),
      boxShadow: isActive ? '0 12px 26px rgba(45, 102, 154, 0.18)' : undefined,
      color: '#253746',
    },
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

function buildLaneLayout(
  prepared: PreparedFlowElements,
  message: string,
  mode: 'lanes' | 'fallback' = 'lanes',
): LayoutState {
  return {
    nodes: prepared.nodes,
    edges: prepared.edges,
    mode,
    message,
    activeEventId: prepared.activeEventId,
    focusEventId: prepared.focusEventId,
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

function buildFlowEdge(source: string, target: string, kind: string): Edge {
  const isSequence = kind === 'sequence';
  const relationStyle = edgeStyleForKind(kind);
  return {
    id: `${source}->${target}:${kind}`,
    source,
    target,
    sourceHandle: mainFlowSourceHandle,
    targetHandle: mainFlowTargetHandle,
    label: isSequence ? undefined : relationStyle.label,
    className: `pg-lwt-edge-${normalizeStatus(kind)}`,
    type: isSequence ? 'straight' : 'smoothstep',
    markerEnd: {
      type: MarkerType.ArrowClosed,
      width: 16,
      height: 16,
    },
    style: {
      stroke: isSequence ? '#6f8fab' : relationStyle.stroke,
      strokeDasharray: isSequence ? undefined : relationStyle.strokeDasharray,
      strokeWidth: isSequence ? 2 : relationStyle.strokeWidth,
    },
  };
}

function buildRelationEdge(relation: TrajectoryRelation): Edge {
  const relationStyle = edgeStyleForKind(relation.kind);
  return {
    id: `${relation.sourceEventId}->${relation.targetEventId}:${relation.kind}`,
    source: relation.sourceEventId,
    target: relation.targetEventId,
    sourceHandle: mainFlowSourceHandle,
    targetHandle: mainFlowTargetHandle,
    label: relationStyle.label,
    className: `pg-lwt-edge-${normalizeStatus(relation.kind)}`,
    type: 'smoothstep',
    markerEnd: {
      type: MarkerType.ArrowClosed,
      width: 16,
      height: 16,
    },
    style: {
      stroke: relationStyle.stroke,
      strokeDasharray: relationStyle.strokeDasharray,
      strokeWidth: relationStyle.strokeWidth,
    },
  };
}

function buildRelianceOverlayEdge(
  relation: TrajectoryRelation,
  eventLaneIndexById: Map<string, number>,
): Edge {
  const relationStyle = edgeStyleForKind(relation.kind);
  const handles = relianceOverlayHandles(relation, eventLaneIndexById);
  return {
    id: `${relation.sourceEventId}->${relation.targetEventId}:${relation.kind}:reliance-overlay`,
    source: relation.sourceEventId,
    target: relation.targetEventId,
    sourceHandle: handles.sourceHandle,
    targetHandle: handles.targetHandle,
    label: relationStyle.label,
    className: [
      `pg-lwt-edge-${normalizeStatus(relation.kind)}`,
      'pg-lwt-edge-reliance-overlay',
    ].join(' '),
    type: 'smoothstep',
    markerEnd: {
      type: MarkerType.ArrowClosed,
      width: 14,
      height: 14,
    },
    style: {
      stroke: relationStyle.stroke,
      strokeDasharray: relationStyle.strokeDasharray,
      strokeWidth: relationStyle.strokeWidth,
      opacity: 0.78,
    },
  };
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
      return { label: 'open lane', stroke: '#b56d54', strokeDasharray: '5 4', strokeWidth: 2.5 };
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

function emptyLayout(mode: 'pending', message: string): LayoutState {
  return {
    nodes: [],
    edges: [],
    mode,
    message,
    activeEventId: null,
    focusEventId: null,
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

main();
