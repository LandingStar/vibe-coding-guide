import assert from 'node:assert/strict';
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import * as vscode from 'vscode';

type ProgressGraphPreviewTestSnapshot = {
  panelVisible: boolean;
  lastRenderedHtml: string | null;
};

const EXTENSION_ID = 'doc-based-coding.doc-based-coding';

export async function run(): Promise<void> {
  const extension = vscode.extensions.getExtension(EXTENSION_ID);
  assert.ok(extension, `Extension under test was not found: ${EXTENSION_ID}`);
  await extension.activate();

  const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
  assert.ok(workspaceRoot, 'Electron smoke requires a workspace folder.');

  await vscode.commands.executeCommand('docBasedCoding.openProgressGraphPreview');
  const snapshot = await waitForProgressGraphSnapshot();

  assert.equal(snapshot.panelVisible, true);
  assert.ok(snapshot.lastRenderedHtml, 'Progress Graph Preview did not render HTML.');
  assert.match(snapshot.lastRenderedHtml, /id="pgHostSchedulerWorkTrajectoryRoot"/);
  assert.match(snapshot.lastRenderedHtml, /id="pgHostSchedulerWorkTrajectoryPayload"/);
  assert.match(snapshot.lastRenderedHtml, /Scheduler Trajectory Projection/);
  assert.match(snapshot.lastRenderedHtml, /lanes=4/);
  assert.match(snapshot.lastRenderedHtml, /events=6/);
  assert.match(snapshot.lastRenderedHtml, /relations=12/);

  writeEvidence(workspaceRoot, snapshot);
}

async function waitForProgressGraphSnapshot(): Promise<ProgressGraphPreviewTestSnapshot> {
  const deadline = Date.now() + 15_000;
  let lastSnapshot: ProgressGraphPreviewTestSnapshot = {
    panelVisible: false,
    lastRenderedHtml: null,
  };

  while (Date.now() < deadline) {
    lastSnapshot = await vscode.commands.executeCommand<ProgressGraphPreviewTestSnapshot>(
      'docBasedCoding.test.getProgressGraphPreviewSnapshot',
    );
    const html = lastSnapshot.lastRenderedHtml ?? '';
    if (
      html.includes('pgHostSchedulerWorkTrajectoryRoot')
      && html.includes('pgHostSchedulerWorkTrajectoryPayload')
      && html.includes('lanes=4')
      && html.includes('events=6')
      && html.includes('relations=12')
    ) {
      return lastSnapshot;
    }
    await delay(250);
  }

  return lastSnapshot;
}

function writeEvidence(workspaceRoot: string, snapshot: ProgressGraphPreviewTestSnapshot): void {
  const evidenceDir = process.env.DBC_ELECTRON_SMOKE_EVIDENCE_DIR;
  if (!evidenceDir) {
    return;
  }

  mkdirSync(evidenceDir, { recursive: true });
  const html = snapshot.lastRenderedHtml ?? '';
  writeFileSync(path.join(evidenceDir, 'rendered-progress-graph-preview.html'), html, 'utf-8');
  writeFileSync(
    path.join(evidenceDir, 'electron-webview-smoke-summary.json'),
    JSON.stringify({
      ok: true,
      workspaceRoot,
      panelVisible: snapshot.panelVisible,
      hasSchedulerTrajectoryRoot: html.includes('pgHostSchedulerWorkTrajectoryRoot'),
      hasSchedulerTrajectoryPayload: html.includes('pgHostSchedulerWorkTrajectoryPayload'),
      lanes: readCount(html, 'lanes'),
      events: readCount(html, 'events'),
      relations: readCount(html, 'relations'),
      note: 'This smoke uses real VS Code extension-host and webview panel creation; DOM assertions are made via a test-only host-side HTML probe because VS Code does not expose stable webview iframe DOM inspection to extension tests.',
    }, null, 2) + '\n',
    'utf-8',
  );
}

function readCount(html: string, label: string): number | null {
  const match = new RegExp(`${label}=(\\d+)`).exec(html);
  return match ? Number(match[1]) : null;
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
