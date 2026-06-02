export type MotionControlNode = {
  id?: string | number;
  x?: number;
  y?: number;
  fx?: number;
  fy?: number;
};

export type MotionControlTick = {
  energy?: number;
  iteration?: number;
  nodes: MotionControlNode[];
};

export type MotionControlController = {
  onTick(tick: MotionControlTick): void;
  dispose?(): void;
};

export type MotionControlEdge = {
  source: string;
  target: string;
};

export type MotionControlContext = {
  edges: MotionControlEdge[];
  nodeCount: number;
  nodeSpacing: number;
  largeGraphFactor: number;
};

export type MotionControlControllerFactory = (context: MotionControlContext) => MotionControlController;

export type RelationalMotionControlOptions = {
  edges: MotionControlEdge[];
} & Omit<MotionControlContext, 'edges'>;

type NodePosition = {
  x: number;
  y: number;
};

type EdgeSnapshot = {
  source: string;
  target: string;
  distance: number;
  angle: number;
};

export function createRelationalMotionController(
  options: RelationalMotionControlOptions,
): MotionControlController {
  const previousPositions = new Map<string, NodePosition>();
  const previousEdges = new Map<string, EdgeSnapshot>();
  const edgePairs = options.edges.map((edge) => ({
    key: `${edge.source}\u0000${edge.target}`,
    source: edge.source,
    target: edge.target,
  }));
  const maxBoost = 5.2 - options.largeGraphFactor * 1.4;
  const movementScale = Math.max(0.28, options.nodeSpacing * 0.2);
  const relationScale = Math.max(0.002, 0.012 - options.largeGraphFactor * 0.004);
  const angleScale = 0.018;
  const extraStepLimit = 22 - options.largeGraphFactor * 8;
  const settleScoreThreshold = 0.018 + options.largeGraphFactor * 0.01;
  const minSettleIterations = Math.round(72 + options.largeGraphFactor * 34);
  const requiredSettleTicks = Math.round(18 + options.largeGraphFactor * 8);
  const requiredPinTicks = Math.round(requiredSettleTicks * 1.75 + 8 + options.largeGraphFactor * 8);
  let peakEnergy = 0;
  let settledTicks = 0;
  let pinned = false;

  return {
    onTick(tick: MotionControlTick): void {
      const nodes = tick.nodes;
      if (nodes.length === 0 || pinned) {
        return;
      }

      const snapshots: Array<{
        id: string;
        node: MotionControlNode;
        x: number;
        y: number;
        dx: number;
        dy: number;
        distance: number;
      }> = [];
      const positions = new Map<string, NodePosition>();
      let movedCount = 0;
      let movementSum = 0;
      let maxMovement = 0;

      nodes.forEach((node, index) => {
        if (!Number.isFinite(node.x) || !Number.isFinite(node.y)) {
          return;
        }

        const id = String(node.id ?? index);
        const x = node.x as number;
        const y = node.y as number;
        const previous = previousPositions.get(id);
        const dx = previous ? x - previous.x : 0;
        const dy = previous ? y - previous.y : 0;
        const distance = Math.sqrt(dx * dx + dy * dy);

        if (previous) {
          movedCount += 1;
          movementSum += distance;
          maxMovement = Math.max(maxMovement, distance);
        }

        positions.set(id, { x, y });
        snapshots.push({ id, node, x, y, dx, dy, distance });
      });

      const relation = measureRelationalChange(edgePairs, positions, previousEdges);
      const iteration = Math.max(0, Math.round(coerceNumber(tick.iteration, 0)));
      const meanMovement = movedCount > 0 ? movementSum / movedCount : 0;
      const energy = Math.sqrt(Math.max(0, coerceNumber(tick.energy, 0))) / Math.max(1, options.nodeCount);
      peakEnergy = Math.max(peakEnergy * 0.86, energy);

      const warmupSignal = clampNumber(1 - iteration / 110, 0, 1, 0);
      const relativeEnergy = peakEnergy > 0 ? energy / peakEnergy : 0;
      const absoluteMovement = Math.max(meanMovement, maxMovement * 0.45) / movementScale;
      const relationSignal = Math.max(
        relation.edgeLengthDelta / relationScale,
        relation.edgeAngleDelta / angleScale,
      );
      const earlyEnergySignal = relativeEnergy * clampNumber(1 - iteration / 260, 0, 1, 0) * 0.36;
      const isRelationallySettling = iteration >= minSettleIterations
        && relation.observedEdgeCount > 0
        && relation.score <= settleScoreThreshold;

      if (isRelationallySettling) {
        settledTicks += 1;
      } else {
        settledTicks = Math.max(0, settledTicks - 2);
      }

      const settleProgress = clampNumber(settledTicks / Math.max(1, requiredSettleTicks), 0, 1, 0);
      const settleDamping = smoothStep(settleProgress);
      const rawRemainingSignal = Math.max(
        warmupSignal * 0.9,
        earlyEnergySignal,
        absoluteMovement,
        relationSignal,
      );
      const settlingRemainingSignal = isRelationallySettling
        ? Math.max(relationSignal, earlyEnergySignal * 0.25, warmupSignal * 0.2)
        : rawRemainingSignal;
      const remainingSignal = clampNumber(
        settlingRemainingSignal * (1 - settleDamping * 0.88),
        0,
        1,
        0,
      );
      const easedSignal = remainingSignal * remainingSignal * (3 - 2 * remainingSignal);
      const boost = 1 + (maxBoost - 1) * easedSignal;

      if (boost > 1.03) {
        for (const snapshot of snapshots) {
          if (snapshot.distance <= 0) {
            continue;
          }

          const rawExtraDistance = snapshot.distance * (boost - 1);
          const limitedExtraRatio = Math.min(boost - 1, extraStepLimit / Math.max(snapshot.distance, 0.001));
          if (rawExtraDistance <= 0 || limitedExtraRatio <= 0) {
            continue;
          }

          snapshot.node.x = snapshot.x + snapshot.dx * limitedExtraRatio;
          snapshot.node.y = snapshot.y + snapshot.dy * limitedExtraRatio;
        }
      }

      if (settleDamping > 0) {
        const keepRatio = clampNumber(1 - settleDamping * (0.82 + options.largeGraphFactor * 0.06), 0.12, 1, 1);
        for (const snapshot of snapshots) {
          const previous = previousPositions.get(snapshot.id);
          const currentX = snapshot.node.x;
          const currentY = snapshot.node.y;
          if (!previous || !Number.isFinite(currentX) || !Number.isFinite(currentY)) {
            continue;
          }

          snapshot.node.x = previous.x + ((currentX as number) - previous.x) * keepRatio;
          snapshot.node.y = previous.y + ((currentY as number) - previous.y) * keepRatio;
        }
      }

      syncEdgeSnapshots(edgePairs, snapshots, previousEdges);

      if (settledTicks >= requiredPinTicks) {
        pinned = true;
        for (const snapshot of snapshots) {
          if (Number.isFinite(snapshot.node.x) && Number.isFinite(snapshot.node.y)) {
            snapshot.node.fx = snapshot.node.x as number;
            snapshot.node.fy = snapshot.node.y as number;
          }
        }
        return;
      }

      previousPositions.clear();
      for (const snapshot of snapshots) {
        if (Number.isFinite(snapshot.node.x) && Number.isFinite(snapshot.node.y)) {
          previousPositions.set(snapshot.id, {
            x: snapshot.node.x as number,
            y: snapshot.node.y as number,
          });
        }
      }
    },
  };
}

export const createDefaultMotionController: MotionControlControllerFactory = createRelationalMotionController;

export function createNoopMotionController(): MotionControlController {
  return {
    onTick(): void {
      // Intentionally empty. Useful when a graph renderer wants to disable
      // motion control without changing its layout monitor wiring.
    },
  };
}

function measureRelationalChange(
  edges: Array<{ key: string; source: string; target: string }>,
  positions: Map<string, NodePosition>,
  previousEdges: Map<string, EdgeSnapshot>,
): {
  edgeLengthDelta: number;
  edgeAngleDelta: number;
  observedEdgeCount: number;
  score: number;
} {
  let lengthDeltaSum = 0;
  let angleDeltaSum = 0;
  let observedEdgeCount = 0;
  const nextEdges = new Map<string, EdgeSnapshot>();

  for (const edge of edges) {
    const source = positions.get(edge.source);
    const target = positions.get(edge.target);
    if (!source || !target) {
      continue;
    }

    const dx = target.x - source.x;
    const dy = target.y - source.y;
    const distance = Math.max(0.001, Math.sqrt(dx * dx + dy * dy));
    const angle = Math.atan2(dy, dx);
    const current = { source: edge.source, target: edge.target, distance, angle };
    const previous = previousEdges.get(edge.key);
    nextEdges.set(edge.key, current);

    if (!previous) {
      continue;
    }

    observedEdgeCount += 1;
    lengthDeltaSum += Math.abs(distance - previous.distance) / Math.max(distance, previous.distance, 1);
    angleDeltaSum += angleDistance(angle, previous.angle) / Math.PI;
  }

  previousEdges.clear();
  nextEdges.forEach((edge, key) => previousEdges.set(key, edge));

  const edgeLengthDelta = observedEdgeCount > 0 ? lengthDeltaSum / observedEdgeCount : 0;
  const edgeAngleDelta = observedEdgeCount > 0 ? angleDeltaSum / observedEdgeCount : 0;
  return {
    edgeLengthDelta,
    edgeAngleDelta,
    observedEdgeCount,
    score: edgeLengthDelta * 0.68 + edgeAngleDelta * 0.32,
  };
}

function syncEdgeSnapshots(
  edges: Array<{ key: string; source: string; target: string }>,
  snapshots: Array<{ id: string; node: MotionControlNode }>,
  previousEdges: Map<string, EdgeSnapshot>,
): void {
  const positions = new Map<string, NodePosition>();
  for (const snapshot of snapshots) {
    if (Number.isFinite(snapshot.node.x) && Number.isFinite(snapshot.node.y)) {
      positions.set(snapshot.id, {
        x: snapshot.node.x as number,
        y: snapshot.node.y as number,
      });
    }
  }

  previousEdges.clear();
  for (const edge of edges) {
    const source = positions.get(edge.source);
    const target = positions.get(edge.target);
    if (!source || !target) {
      continue;
    }

    const dx = target.x - source.x;
    const dy = target.y - source.y;
    previousEdges.set(edge.key, {
      source: edge.source,
      target: edge.target,
      distance: Math.max(0.001, Math.sqrt(dx * dx + dy * dy)),
      angle: Math.atan2(dy, dx),
    });
  }
}

function angleDistance(a: number, b: number): number {
  const diff = Math.abs(a - b) % (Math.PI * 2);
  return diff > Math.PI ? Math.PI * 2 - diff : diff;
}

function smoothStep(value: number): number {
  const t = clampNumber(value, 0, 1, 0);
  return t * t * (3 - 2 * t);
}

function coerceNumber(value: unknown, fallback: number): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback;
}

function clampNumber(value: unknown, min: number, max: number, fallback: number): number {
  const candidate = coerceNumber(value, fallback);
  return Math.min(max, Math.max(min, candidate));
}
