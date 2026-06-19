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

test('progress graph payload projects local trajectory anchor onto global nodes', () => {
  const source = readFileSync(sourcePath, 'utf-8');

  assert.match(source, /localWorkTrajectory = coerceLocalWorkTrajectory/);
  assert.match(source, /buildProgressGraphV2PoCPayload\([\s\S]*controlSnapshot,[\s\S]*localWorkTrajectory,/);
  assert.match(source, /localWorkTrajectory:\s*ProgressGraphPreviewLocalWorkTrajectory \| null/);
  assert.match(source, /const selectedGraph = selectV2Graph\(candidateGraphs, localWorkTrajectory\);/);
  assert.match(source, /const anchoredGraphId = localWorkTrajectory\?\.sourceGraphId;/);
  assert.match(source, /const anchoredNodeId = localWorkTrajectory\?\.sourceNodeId;/);
  assert.match(source, /const anchoredGraph = graphs\.find/);
  assert.match(source, /const trajectoryAnchorMatchesGraph = localWorkTrajectory\?\.sourceGraphId === selectedGraph\.graphId/);
  assert.match(source, /hasLocalTrajectory,\s*localTrajectoryId:/);
});

test('preview panel reads scheduler trajectory projection separately from local trajectory', () => {
  const source = readFileSync(sourcePath, 'utf-8');

  assert.match(source, /_schedulerTrajectoryArtifactUri/);
  assert.match(source, /scheduler-work-trajectory\.json/);
  assert.match(source, /schedulerWorkTrajectory = coerceLocalWorkTrajectory/);
  assert.match(source, /schedulerTrajectoryArtifactExists/);
  assert.match(source, /schedulerWorkTrajectoryError/);
  assert.match(source, /schedulerTrajectoryId: state\.schedulerWorkTrajectory\?\.trajectoryId/);
});

test('preview panel reads host evidence presentation as a read-only resource', () => {
  const source = readFileSync(sourcePath, 'utf-8');
  const hostEvidenceSource = readFileSync(
    join(__dirname, '..', '..', 'src', 'views', 'hostEvidencePresentation.ts'),
    'utf-8',
  );

  assert.match(source, /readHostEvidencePresentation/);
  assert.match(source, /hostEvidencePresentationResourceUri:\s*HOST_EVIDENCE_PRESENTATION_RESOURCE_URI/);
  assert.match(source, /hostEvidencePresentationStatus: state\.hostEvidencePresentation\?\.status/);
  assert.match(hostEvidenceSource, /dbc:\/\/host-evidence\/presentation/);
  assert.match(hostEvidenceSource, /tools\.read_resource/);
  assert.doesNotMatch(hostEvidenceSource, /write_resource|callTool|localTrajectory|scheduler daemon-loop/);
});

test('preview panel wires scheduler operator workflow through the shared CLI surface', () => {
  const source = readFileSync(sourcePath, 'utf-8');
  const schedulerOperatorSource = readFileSync(
    join(__dirname, '..', '..', 'src', 'views', 'schedulerOperatorWorkflow.ts'),
    'utf-8',
  );

  assert.match(source, /readSchedulerOperatorWorkflowState/);
  assert.match(source, /runSchedulerOperatorAction/);
  assert.match(source, /case 'schedulerOperatorAction'/);
  assert.match(source, /_coerceSchedulerOperatorAction/);
  assert.match(source, /schedulerOperatorWorkflow: schedulerOperatorWorkflow/);
  assert.match(schedulerOperatorSource, /dbc:\/\/exchange-artifacts\/bundle/);
  assert.match(schedulerOperatorSource, /'scheduler',\s*'operator-workflow'/);
  assert.match(schedulerOperatorSource, /'--admit'/);
  assert.match(schedulerOperatorSource, /'--run-loop'/);
  assert.match(schedulerOperatorSource, /'--refresh-projection'/);
  assert.match(schedulerOperatorSource, /'--artifact-store-path',\s*'\.codex\/orchestration\/exchange-artifacts\.json'/);
  assert.match(schedulerOperatorSource, /'--admission-ledger-path',\s*'\.codex\/orchestration\/exchange-artifact-admissions\.json'/);
  assert.match(schedulerOperatorSource, /'--projection-output-path',\s*'\.codex\/progress-graph\/scheduler-work-trajectory\.json'/);
  assert.match(schedulerOperatorSource, /'--runtime-provider',\s*'fake'/);
  assert.match(schedulerOperatorSource, /'--max-ticks',\s*'3'/);
  assert.match(schedulerOperatorSource, /readNestedWorkflowResult\(payload,\s*'admission_result'\)/);
  assert.match(schedulerOperatorSource, /readNestedWorkflowResult\(payload,\s*'loop_result'\)/);
  assert.match(schedulerOperatorSource, /readNestedWorkflowResult\(payload,\s*'projection_result'\)/);
  assert.match(schedulerOperatorSource, /importlib\.metadata\.distribution\("doc-based-coding-runtime"\)/);
  assert.match(schedulerOperatorSource, /from src\.__main__ import main/);
  assert.match(schedulerOperatorSource, /sys\.argv = \["doc-based-coding"/);
  assert.match(schedulerOperatorSource, /tools\.read_resource/);
  assert.doesNotMatch(schedulerOperatorSource, /'scheduler',\s*'admit-exchange-artifact'/);
  assert.doesNotMatch(schedulerOperatorSource, /'scheduler',\s*'daemon-loop'/);
  assert.doesNotMatch(schedulerOperatorSource, /'scheduler',\s*'project'/);
  assert.doesNotMatch(schedulerOperatorSource, /localTrajectory|write_resource|callTool/);
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

test('generated VS Code MCP config uses the installed CLI entry point', () => {
  const extensionSource = readFileSync(extensionSourcePath, 'utf-8');
  const ensureMcpJsonSource = extensionSource.slice(
    extensionSource.indexOf('function ensureMcpJson('),
    extensionSource.indexOf('/**\n * Try to find a Python executable'),
  );

  assert.match(ensureMcpJsonSource, /resolveMcpEntryPoint\(pythonPath\)/);
  assert.match(ensureMcpJsonSource, /args:\s*\['--project', projectRoot, \.\.\.serverArgs\]/);
  assert.match(ensureMcpJsonSource, /cwd:\s*projectRoot/);
  assert.doesNotMatch(ensureMcpJsonSource, /'-m', 'src\.mcp\.server'/);
  assert.match(extensionSource, /doc-based-coding-mcp\.exe/);
  assert.match(extensionSource, /return 'doc-based-coding-mcp';/);
});
