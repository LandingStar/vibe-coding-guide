import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import test from 'node:test';

const sourcePath = join(__dirname, '..', '..', 'src', 'webviews', 'progressGraphV2Engine.ts');

test('auto refresh layout shakes before fitting viewport', () => {
  const source = readFileSync(sourcePath, 'utf-8');

  assert.match(source, /resetAfterMs:\s*520/);
  assert.match(source, /const schedulePostShakeReset = \(\): void => \{/);
  assert.match(
    source,
    /if \(reason === 'refresh'\) \{\s*schedulePostShakeReset\(\);\s*\}/s,
  );
  assert.match(
    source,
    /if \(fitOnNextTick\) \{\s*fitOnNextTick = false;\s*scheduleAutoLayoutShake\(\);\s*\} else \{/s,
  );
  assert.match(source, /const autoShakeEnabled = readAutoShakeEnabled\(container\);/);
  assert.match(source, /let autoShakePending = autoShakeEnabled;/);
  assert.match(source, /if \(!autoShakeEnabled \|\| !autoShakePending\) \{/);
  assert.match(source, /function readAutoShakeEnabled\(container: HTMLElement\): boolean \{/);
  assert.match(source, /section\.dataset\.pgV2AutoShake !== 'false'/);
  assert.doesNotMatch(
    source,
    /if \(fitOnNextTick\) \{\s*fitOnNextTick = false;\s*resetRendererZoom\(renderer\);\s*scheduleAutoLayoutShake\(\);/s,
  );
});

test('progress graph renderer exposes local trajectory anchor navigation', () => {
  const source = readFileSync(sourcePath, 'utf-8');

  assert.match(source, /hasLocalTrajectory: boolean/);
  assert.match(source, /localTrajectoryId: string \| null/);
  assert.match(source, /pg-host-open-trajectory/);
  assert.match(source, /pg-host-select-graph-node/);
  assert.match(source, /data-pg-open-trajectory-node-id/);
  assert.match(source, /Open trajectory/);
  assert.match(source, /trajectory anchor/);
  assert.match(source, /const trajectoryNodeIds = new Set/);
  assert.match(source, /getNodeStyle: \(\{ node, style \}\) =>/);
  assert.match(source, /fill: '#f2efff'/);
  assert.match(source, /stroke: '#5b3fd6'/);
  assert.match(source, /font: '700 12px/);
});
