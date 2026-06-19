import { spawn } from 'node:child_process';
import { existsSync, mkdirSync, rmSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const extensionRoot = path.resolve(__dirname, '..');
const repoRoot = path.resolve(extensionRoot, '..');
const workspaceRoot = path.join(repoRoot, 'output', 'electron', 'webview-runner-smoke', 'workspace');
const evidenceDir = path.join(repoRoot, 'output', 'electron', 'webview-runner-smoke');
const extensionTestsPath = path.join(extensionRoot, 'dist', 'electron-test', 'suite', 'index.js');
const summaryPath = path.join(evidenceDir, 'electron-webview-smoke-summary.json');
const renderedHtmlPath = path.join(evidenceDir, 'rendered-progress-graph-preview.html');

prepareWorkspace(workspaceRoot);

const configuredExecutable = process.env.VSCODE_ELECTRON_SMOKE_EXECUTABLE;
const defaultCodeCmd = 'C:\\Users\\16329\\AppData\\Local\\Programs\\Microsoft VS Code\\bin\\code.cmd';
const defaultCodeExe = 'C:\\Users\\16329\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe';
const vscodeExecutablePath = resolveVSCodeExecutablePath(
  configuredExecutable
  || (process.platform === 'win32' && existsSync(defaultCodeExe) ? defaultCodeExe : undefined),
);

if (!vscodeExecutablePath) {
  throw new Error(
    'VS Code executable not found. Set VSCODE_ELECTRON_SMOKE_EXECUTABLE to Code.exe or a compatible VS Code executable.',
  );
}

await runVSCodeElectronSmoke({
  executablePath: vscodeExecutablePath,
  args: [
    workspaceRoot,
    '--disable-extensions',
    '--no-sandbox',
    '--disable-gpu-sandbox',
    '--disable-updates',
    '--skip-welcome',
    '--skip-release-notes',
    '--disable-workspace-trust',
    `--user-data-dir=${path.join(evidenceDir, 'vscode-user-data')}`,
    `--extensions-dir=${path.join(evidenceDir, 'vscode-extensions')}`,
    `--extensionDevelopmentPath=${extensionRoot}`,
    `--extensionTestsPath=${extensionTestsPath}`,
  ],
  env: buildElectronLaunchEnv(process.env),
});

assertEvidenceWritten();

function prepareWorkspace(root) {
  rmSync(root, { recursive: true, force: true });
  mkdirSync(path.join(root, '.codex', 'progress-graph'), { recursive: true });
  mkdirSync(path.join(root, '.vscode'), { recursive: true });

  writeJson(path.join(root, '.codex', 'platform.json'), { pack_dirs: [] });
  writeJson(path.join(root, '.vscode', 'settings.json'), {
    'docBasedCoding.autoStart': false,
    'docBasedCoding.pythonPath': process.env.DBC_ELECTRON_SMOKE_PYTHON || 'python',
    'docBasedCoding.sourceRoot': repoRoot,
  });
  writeFileSync(path.join(root, '.codex', 'progress-graph', 'latest.html'), [
    '<!DOCTYPE html>',
    '<html lang="en">',
    '<head><meta charset="UTF-8"><title>Electron Webview Smoke Fixture</title></head>',
    '<body><section class="graph-section" data-graph-id="electron-webview-smoke">fixture</section></body>',
    '</html>',
  ].join('\n'), 'utf-8');
  writeJson(path.join(root, '.codex', 'progress-graph', 'scheduler-work-trajectory.json'), {
    trajectoryId: 'local-work:scheduler-projection',
    title: 'Scheduler Local Work Trajectory',
    recordedAt: '2026-06-19T00:00:00.000Z',
    sourceGraphId: null,
    sourceNodeId: null,
    guideContext: 'electron-webview-runner-smoke',
    metadata: {
      authority: 'scheduler',
      projection: 'scheduler-state',
      scheduler_history_timeline: [
        'timestamp=2026-06-19T00:00:01+08:00 | kind=task_completed | id=scheduler-event-1 | task=server-api',
        'timestamp=2026-06-19T00:00:02+08:00 | kind=task_completed | id=scheduler-event-2 | task=database-schema',
      ].join('\n'),
      scheduler_history_timeline_count: '2',
      scheduler_history_timeline_limit: '40',
      scheduler_history_timeline_truncated: 'false',
    },
    lanes: {
      'lane:api': { id: 'lane:api', label: 'api', status: 'done', summary: '', metadata: {} },
      'lane:data': { id: 'lane:data', label: 'data', status: 'done', summary: '', metadata: {} },
      'lane:client': { id: 'lane:client', label: 'client', status: 'done', summary: '', metadata: {} },
      'lane:qa': { id: 'lane:qa', label: 'qa', status: 'done', summary: '', metadata: {} },
    },
    events: {
      'scheduler-task:server-api': event('scheduler-task:server-api', 'lane:api', 'server-api', 'task', 1),
      'scheduler-task:database-schema': event('scheduler-task:database-schema', 'lane:data', 'database-schema', 'task', 2),
      'scheduler-task:client-integration': event('scheduler-task:client-integration', 'lane:client', 'client-integration', 'task', 3),
      'scheduler-merge:client-ready': event('scheduler-merge:client-ready', 'lane:client', 'client ready', 'merge', 4),
      'scheduler-task:integration-qa': event('scheduler-task:integration-qa', 'lane:qa', 'integration-qa', 'task', 5),
      'scheduler-merge:integration-done': event('scheduler-merge:integration-done', 'lane:qa', 'integration done', 'merge', 6),
    },
    relations: [
      relation('scheduler-task:server-api', 'scheduler-task:client-integration', 'depends_on'),
      relation('scheduler-task:database-schema', 'scheduler-task:client-integration', 'depends_on'),
      relation('scheduler-task:client-integration', 'scheduler-merge:client-ready', 'sequence'),
      relation('scheduler-task:server-api', 'scheduler-merge:client-ready', 'syncs_from'),
      relation('scheduler-task:database-schema', 'scheduler-merge:client-ready', 'syncs_from'),
      relation('scheduler-merge:client-ready', 'scheduler-task:integration-qa', 'depends_on'),
      relation('scheduler-task:database-schema', 'scheduler-task:integration-qa', 'depends_on'),
      relation('scheduler-task:integration-qa', 'scheduler-merge:integration-done', 'sequence'),
      relation('scheduler-task:server-api', 'scheduler-merge:integration-done', 'syncs_from'),
      relation('scheduler-task:database-schema', 'scheduler-merge:integration-done', 'syncs_from'),
      relation('scheduler-task:client-integration', 'scheduler-merge:integration-done', 'syncs_from'),
      relation('scheduler-merge:client-ready', 'scheduler-merge:integration-done', 'syncs_from'),
    ],
    childTrajectories: {},
  });
}

function event(id, laneId, title, kind, order) {
  return {
    id,
    laneId,
    title,
    kind,
    status: 'completed',
    order,
    summary: '',
    metadata: {},
  };
}

function relation(sourceEventId, targetEventId, kind) {
  return {
    sourceEventId,
    targetEventId,
    kind,
    summary: '',
    metadata: {},
  };
}

function writeJson(filePath, value) {
  writeFileSync(filePath, JSON.stringify(value, null, 2) + '\n', 'utf-8');
}

function resolveVSCodeExecutablePath(configuredPath) {
  if (!configuredPath) {
    return undefined;
  }
  if (process.platform === 'win32') {
    const lowerPath = configuredPath.toLowerCase();
    if (lowerPath.endsWith('code.cmd')) {
      const codeExe = path.resolve(path.dirname(configuredPath), '..', 'Code.exe');
      return existsSync(codeExe) ? codeExe : undefined;
    }
  }

  return configuredPath;
}

function buildElectronLaunchEnv(baseEnv) {
  const env = {
    ...baseEnv,
    DBC_ELECTRON_SMOKE_EVIDENCE_DIR: evidenceDir,
  };
  delete env.ELECTRON_RUN_AS_NODE;
  delete env.VSCODE_DEV;
  return env;
}

function runVSCodeElectronSmoke({ executablePath, args, env }) {
  return new Promise((resolve, reject) => {
    const child = spawn(executablePath, args, {
      env,
      shell: false,
      stdio: 'inherit',
      windowsHide: true,
    });

    child.on('error', reject);
    child.on('exit', (code, signal) => {
      if (code === 0) {
        resolve();
        return;
      }
      reject(new Error(
        signal
          ? `VS Code Electron smoke terminated with signal ${signal}`
          : `VS Code Electron smoke failed with exit code ${code}`,
      ));
    });
  });
}

function assertEvidenceWritten() {
  if (!existsSync(summaryPath) || !existsSync(renderedHtmlPath)) {
    throw new Error(
      `Electron webview smoke exited without writing expected evidence: ${summaryPath} and ${renderedHtmlPath}`,
    );
  }
}
