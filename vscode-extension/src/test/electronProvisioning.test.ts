import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import test from 'node:test';

const provisionSourcePath = join(__dirname, '..', '..', 'scripts', 'provision-electron-vscode.mjs');
const smokeSourcePath = join(__dirname, '..', '..', 'scripts', 'run-electron-webview-smoke.mjs');
const manifestPath = join(__dirname, '..', '..', 'package.json');

test('electron VS Code provisioning is exposed as an explicit opt-in script only', () => {
  const manifest = JSON.parse(readFileSync(manifestPath, 'utf-8')) as {
    scripts?: Record<string, string>;
  };

  assert.equal(manifest.scripts?.['provision:electron:vscode'], 'node scripts/provision-electron-vscode.mjs');
  assert.doesNotMatch(manifest.scripts?.build ?? '', /provision-electron-vscode|downloadAndUnzipVSCode/);
  assert.doesNotMatch(manifest.scripts?.test ?? '', /provision-electron-vscode|downloadAndUnzipVSCode/);
  assert.doesNotMatch(manifest.scripts?.['test:electron:smoke'] ?? '', /provision-electron-vscode|downloadAndUnzipVSCode/);
});

test('electron VS Code provisioning requires exact version and explicit consent before download', () => {
  const source = readFileSync(provisionSourcePath, 'utf-8');

  assert.match(source, /downloadAndUnzipVSCode/);
  assert.match(source, /--vscode-version is required and must be an exact VS Code version/);
  assert.match(source, /do not use stable or insiders/);
  assert.match(source, /dry-run/);
  assert.match(source, /provision <exact-version>/);
  assert.match(source, /if \(options\.mode !== 'provision'\)/);
  assert.match(source, /--dry-run/);
});

test('electron VS Code provisioning writes policy manifest fields', () => {
  const source = readFileSync(provisionSourcePath, 'utf-8');

  assert.match(source, /outputRoot,\s*'vscode-executable'/);
  assert.match(source, /targetManifest = path\.join\(targetDir, 'manifest\.json'\)/);
  assert.match(source, /product: 'Visual Studio Code'/);
  assert.match(source, /version: options\.version/);
  assert.match(source, /platform: options\.platform/);
  assert.match(source, /source: '@vscode\/test-electron downloadAndUnzipVSCode'/);
  assert.match(source, /acquired_at: new Date\(\)\.toISOString\(\)/);
  assert.match(source, /sha256: sha256File\(targetExecutable\)/);
  assert.match(source, /Do not commit executable or manifest/);
});

test('electron smoke runner does not download VS Code implicitly', () => {
  const smokeSource = readFileSync(smokeSourcePath, 'utf-8');

  assert.doesNotMatch(smokeSource, /downloadAndUnzipVSCode|provision-electron-vscode/);
  assert.match(smokeSource, /VSCODE_ELECTRON_SMOKE_EXECUTABLE/);
  assert.match(smokeSource, /output.*electron.*vscode-executable/s);
});
