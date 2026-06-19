import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import test from 'node:test';

const runnerSourcePath = join(__dirname, '..', '..', 'scripts', 'run-electron-webview-smoke.mjs');

test('electron webview smoke runner resolves isolated VS Code executables before user-local fallback', () => {
  const source = readFileSync(runnerSourcePath, 'utf-8');

  assert.match(source, /VSCODE_ELECTRON_SMOKE_EXECUTABLE/);
  assert.match(source, /repoLocalCodeExe = path\.join\(/);
  assert.match(source, /'output',\s*'electron',\s*'vscode-executable'/);
  assert.match(source, /sourceKind: 'env'/);
  assert.match(source, /sourceKind: 'repo-local'/);
  assert.match(source, /sourceKind: 'user-local'/);
  assert.match(
    source,
    /const candidates = \[[\s\S]*sourceKind: 'env'[\s\S]*sourceKind: 'repo-local'[\s\S]*sourceKind: 'user-local'/,
  );
});

test('electron webview smoke runner prints executable source diagnostics', () => {
  const source = readFileSync(runnerSourcePath, 'utf-8');

  assert.match(source, /printExecutableDiagnostic\(executableResolution\)/);
  assert.match(source, /\[electron-smoke\] VS Code executable resolution/);
  assert.match(source, /source=\$\{resolution\.sourceKind\}/);
  assert.match(source, /executable=\$\{resolution\.executablePath\}/);
});

test('electron webview smoke runner explains user-local VS Code update-lock remediation', () => {
  const source = readFileSync(runnerSourcePath, 'utf-8');

  assert.match(source, /enrichElectronSmokeError\(error, executableResolution\)/);
  assert.match(source, /resolution\.sourceKind !== 'user-local'/);
  assert.match(source, /vscode-updating/);
  assert.match(source, /VSCODE_ELECTRON_SMOKE_EXECUTABLE=<path-to-isolated-Code\.exe>/);
  assert.match(source, /output\/electron\/vscode-executable/);
});
