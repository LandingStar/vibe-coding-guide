import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import test from 'node:test';

const sourcePath = join(__dirname, '..', '..', 'src', 'views', 'progressGraphPreview.ts');

test('progress graph preview opens in the primary editor column by default', () => {
  const source = readFileSync(sourcePath, 'utf-8');

  assert.match(source, /const DEFAULT_PROGRESS_GRAPH_VIEW_COLUMN = vscode\.ViewColumn\.One;/);
  assert.doesNotMatch(source, /vscode\.ViewColumn\.Beside/);
});

test('progress graph engine view prefers the global checklist graph', () => {
  const source = readFileSync(sourcePath, 'utf-8');

  assert.match(
    source,
    /const preferredOrder = \['project-checklist-current', 'planning-gates-index', 'checkpoint-current'\];/,
  );
});

test('refresh does not re-render the webview while artifact regeneration is running', () => {
  const source = readFileSync(sourcePath, 'utf-8');
  const refreshMethod = source.slice(
    source.indexOf('    async refresh('),
    source.indexOf('    async revealArtifact('),
  );

  assert.doesNotMatch(
    refreshMethod,
    /status:\s*'refreshing'[\s\S]*?this\._renderShellState\(\{ preserveCurrentPreview: true \}\);[\s\S]*?try \{/,
  );
  assert.match(
    refreshMethod,
    /status:\s*'idle'[\s\S]*?await this\._reload\(\);/,
  );
  assert.match(
    refreshMethod,
    /status:\s*'failed'[\s\S]*?this\._renderShellState\(\{ preserveCurrentPreview: true \}\);/,
  );
});

test('preview panel is display-only for local work trajectory mutation', () => {
  const source = readFileSync(sourcePath, 'utf-8');

  assert.doesNotMatch(source, /ProgressGraphTrajectoryActionRunner/);
  assert.doesNotMatch(source, /runTrajectoryAction/);
  assert.doesNotMatch(source, /showInputBox\(/);
  assert.doesNotMatch(source, /showQuickPick\(/);
  assert.doesNotMatch(source, /startLocalWorkTrajectory/);
  assert.doesNotMatch(source, /appendLocalWorkTrajectoryEvent/);
  assert.doesNotMatch(source, /advanceLocalWorkTrajectoryEvent/);
  assert.doesNotMatch(source, /\| 'startLocalWorkTrajectory'/);
  assert.doesNotMatch(source, /case 'startLocalWorkTrajectory'/);
  assert.doesNotMatch(source, /case 'appendLocalWorkTrajectoryEvent'/);
  assert.doesNotMatch(source, /case 'advanceLocalWorkTrajectoryEvent'/);
});
