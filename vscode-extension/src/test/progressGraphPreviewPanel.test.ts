import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import test from 'node:test';

const sourcePath = join(__dirname, '..', '..', 'src', 'views', 'progressGraphPreview.ts');
const artifactsSourcePath = join(__dirname, '..', '..', 'src', 'views', 'progressGraphArtifacts.ts');
const extensionSourcePath = join(__dirname, '..', '..', 'src', 'extension.ts');

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

test('progress graph refresh does not treat a target project tools directory as platform source root', () => {
  const previewSource = readFileSync(sourcePath, 'utf-8');
  const artifactsSource = readFileSync(artifactsSourcePath, 'utf-8');
  const extensionSource = readFileSync(extensionSourcePath, 'utf-8');

  assert.match(artifactsSource, /importlib\.metadata\.distribution\("doc-based-coding-runtime"\)/);
  assert.match(artifactsSource, /sys\.path\.append\(/);
  assert.match(artifactsSource, /sys\.path\.insert\(0, str\(runtime_root\)\)/);
  assert.match(artifactsSource, /Using installed doc-based-coding-runtime package root/);
  assert.match(extensionSource, /src', 'runtime', 'orchestration', '__init__\.py'/);
  assert.match(extensionSource, /return null;/);
});
