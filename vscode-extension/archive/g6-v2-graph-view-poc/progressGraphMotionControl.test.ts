import assert from 'node:assert/strict';
import test from 'node:test';

import {
  createNoopMotionController,
  createRelationalMotionController,
  type MotionControlNode,
} from '../webviews/progressGraphMotionControl.js';

test('relational motion controller soft-pins nodes after edge relationships settle', () => {
  const controller = createRelationalMotionController({
    edges: [{ source: 'a', target: 'b' }],
    nodeCount: 2,
    nodeSpacing: 8,
    largeGraphFactor: 0,
  });
  const nodes: MotionControlNode[] = [
    { id: 'a', x: 0, y: 0 },
    { id: 'b', x: 120, y: 0 },
  ];

  controller.onTick({ iteration: 0, energy: 20, nodes });
  for (let iteration = 72; iteration < 112; iteration += 1) {
    nodes[0].x = 0;
    nodes[0].y = 0;
    nodes[1].x = 120;
    nodes[1].y = 0;
    controller.onTick({ iteration, energy: 0.02, nodes });
  }

  assert.equal(nodes[0].fx, 0);
  assert.equal(nodes[0].fy, 0);
  assert.equal(nodes[1].fx, 120);
  assert.equal(nodes[1].fy, 0);
});

test('relational motion controller delays soft-pin after damping saturates', () => {
  const controller = createRelationalMotionController({
    edges: [{ source: 'a', target: 'b' }],
    nodeCount: 2,
    nodeSpacing: 8,
    largeGraphFactor: 0,
  });
  const nodes: MotionControlNode[] = [
    { id: 'a', x: 0, y: 0 },
    { id: 'b', x: 120, y: 0 },
  ];

  controller.onTick({ iteration: 0, energy: 20, nodes });
  for (let iteration = 72; iteration < 97; iteration += 1) {
    nodes[0].x = 0;
    nodes[0].y = 0;
    nodes[1].x = 120;
    nodes[1].y = 0;
    controller.onTick({ iteration, energy: 0.02, nodes });
  }

  assert.equal(nodes[0].fx, undefined);
  assert.equal(nodes[0].fy, undefined);
  assert.equal(nodes[1].fx, undefined);
  assert.equal(nodes[1].fy, undefined);

  for (let iteration = 97; iteration < 112; iteration += 1) {
    nodes[0].x = 0;
    nodes[0].y = 0;
    nodes[1].x = 120;
    nodes[1].y = 0;
    controller.onTick({ iteration, energy: 0.02, nodes });
  }

  assert.equal(nodes[0].fx, 0);
  assert.equal(nodes[0].fy, 0);
  assert.equal(nodes[1].fx, 120);
  assert.equal(nodes[1].fy, 0);
});

test('relational motion controller damps gradually before soft-pinning settled nodes', () => {
  const controller = createRelationalMotionController({
    edges: [{ source: 'a', target: 'b' }],
    nodeCount: 2,
    nodeSpacing: 8,
    largeGraphFactor: 0,
  });
  const nodes: MotionControlNode[] = [
    { id: 'a', x: 0, y: 0 },
    { id: 'b', x: 120, y: 0 },
  ];

  controller.onTick({ iteration: 0, energy: 20, nodes });
  let previousX = nodes[0].x as number;
  let earlyDelta = 0;
  let dampedDelta = 0;
  for (let iteration = 72; iteration < 84; iteration += 1) {
    nodes[0].x = (nodes[0].x as number) + 4;
    nodes[1].x = (nodes[1].x as number) + 4;
    controller.onTick({ iteration, energy: 0.02, nodes });
    const currentX = nodes[0].x as number;
    const delta = currentX - previousX;
    if (iteration === 72) {
      earlyDelta = delta;
    }
    if (iteration === 83) {
      dampedDelta = delta;
    }
    previousX = currentX;
  }

  assert.equal(nodes[0].fx, undefined);
  assert.equal(nodes[1].fx, undefined);
  assert.ok(dampedDelta > 0, `expected damped motion to continue before pinning, got ${dampedDelta}`);
  assert.ok(dampedDelta < earlyDelta * 0.55, `expected gradual damping before pinning: ${dampedDelta} < ${earlyDelta}`);
});

test('relational motion controller does not settle while edge relationship keeps changing', () => {
  const controller = createRelationalMotionController({
    edges: [{ source: 'a', target: 'b' }],
    nodeCount: 2,
    nodeSpacing: 8,
    largeGraphFactor: 0,
  });
  const nodes: MotionControlNode[] = [
    { id: 'a', x: 0, y: 0 },
    { id: 'b', x: 120, y: 0 },
  ];

  controller.onTick({ iteration: 0, energy: 20, nodes });
  for (let iteration = 72; iteration < 100; iteration += 1) {
    nodes[1].x = iteration % 2 === 0 ? 120 : 150;
    controller.onTick({ iteration, energy: 0.02, nodes });
  }

  assert.equal(nodes[0].fx, undefined);
  assert.equal(nodes[0].fy, undefined);
  assert.equal(nodes[1].fx, undefined);
  assert.equal(nodes[1].fy, undefined);
});

test('noop motion controller leaves ticks untouched', () => {
  const controller = createNoopMotionController();
  const nodes: MotionControlNode[] = [
    { id: 'a', x: 1, y: 2 },
  ];

  controller.onTick({ iteration: 100, energy: 0, nodes });

  assert.deepEqual(nodes, [{ id: 'a', x: 1, y: 2 }]);
});
