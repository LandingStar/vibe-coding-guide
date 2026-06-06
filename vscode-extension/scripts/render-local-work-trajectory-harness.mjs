import { copyFileSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const scriptDir = dirname(fileURLToPath(import.meta.url));
const extensionRoot = resolve(scriptDir, '..');
const repoRoot = resolve(extensionRoot, '..');

const args = new Map();
for (let index = 2; index < process.argv.length; index += 2) {
  args.set(process.argv[index], process.argv[index + 1]);
}

const defaultTrajectoryPath = 'C:/Users/16329/OneDrive/Desktop/tmp/dbc-test/.codex/progress-graph/local-work-trajectory.json';
const trajectoryPath = resolve(args.get('--trajectory') ?? defaultTrajectoryPath);
const outputDir = resolve(args.get('--out') ?? resolve(repoRoot, 'output/playwright/local-work-trajectory'));
const assetsDir = resolve(outputDir, 'assets');
const scriptPath = resolve(extensionRoot, 'dist/webviews/localWorkTrajectory.js');
const stylePath = resolve(extensionRoot, 'dist/webviews/localWorkTrajectory.css');

mkdirSync(assetsDir, { recursive: true });
copyFileSync(scriptPath, resolve(assetsDir, 'localWorkTrajectory.js'));
copyFileSync(stylePath, resolve(assetsDir, 'localWorkTrajectory.css'));

const rawTrajectory = JSON.parse(readFileSync(trajectoryPath, 'utf-8'));
const payload = coerceTrajectory(rawTrajectory);
const payloadJson = JSON.stringify(payload).replace(/</g, '\\u003c');
const html = `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Local Work Trajectory Harness</title>
  <link rel="stylesheet" href="./assets/localWorkTrajectory.css">
  <style>
    html,
    body {
      margin: 0;
      width: 100%;
      min-height: 100%;
      background: #f7f3eb;
    }

    body {
      padding: 0;
      overflow: hidden;
    }

    #pgHostLocalWorkTrajectoryRoot {
      width: 100vw;
      height: 100vh;
    }
  </style>
</head>
<body>
  <div id="pgHostLocalWorkTrajectoryRoot" data-pg-trajectory-error=""></div>
  <script id="pgHostLocalWorkTrajectoryPayload" type="application/json">${payloadJson}</script>
  <script src="./assets/localWorkTrajectory.js"></script>
</body>
</html>
`;

const htmlPath = resolve(outputDir, 'index.html');
writeFileSync(htmlPath, html, 'utf-8');
console.log(JSON.stringify({
  ok: true,
  htmlPath,
  htmlUrl: pathToFileURL(htmlPath).href,
  trajectoryPath,
  nodeCount: payload.events.length,
  relationCount: payload.relations.length,
}, null, 2));

function coerceTrajectory(data) {
  const lanes = Object.values(data.lanes ?? {})
    .map((lane) => ({
      id: String(lane.id),
      label: String(lane.label),
      status: String(lane.status ?? 'pending'),
      summary: String(lane.summary ?? ''),
      metadata: objectOfStrings(lane.metadata),
    }))
    .sort((left, right) => left.id.localeCompare(right.id));
  const events = Object.values(data.events ?? {})
    .map((event) => ({
      id: String(event.id),
      laneId: String(event.lane_id),
      title: String(event.title),
      kind: String(event.kind ?? 'task'),
      status: String(event.status ?? 'pending'),
      order: Number(event.order ?? 0),
      summary: String(event.summary ?? ''),
      metadata: objectOfStrings(event.metadata),
    }))
    .sort((left, right) => left.order - right.order || left.id.localeCompare(right.id));
  const relations = (data.relations ?? []).map((relation) => ({
    sourceEventId: String(relation.source_event_id),
    targetEventId: String(relation.target_event_id),
    kind: String(relation.kind ?? 'sequence'),
    summary: String(relation.summary ?? ''),
    metadata: objectOfStrings(relation.metadata),
  }));
  return {
    trajectoryId: String(data.trajectory_id ?? 'local-work:debug'),
    title: String(data.title ?? 'Local Work Trajectory Debug'),
    recordedAt: data.recorded_at ? String(data.recorded_at) : null,
    sourceGraphId: data.source_graph_id ? String(data.source_graph_id) : null,
    sourceNodeId: data.source_node_id ? String(data.source_node_id) : null,
    guideContext: data.guide_context ? String(data.guide_context) : null,
    metadata: objectOfStrings(data.metadata),
    lanes,
    events,
    relations,
  };
}

function objectOfStrings(value) {
  const result = {};
  for (const [key, entry] of Object.entries(value ?? {})) {
    result[String(key)] = String(entry);
  }
  return result;
}
