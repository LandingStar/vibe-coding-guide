import { createHash } from 'node:crypto';
import { cpSync, existsSync, mkdirSync, readFileSync, rmSync, statSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import vscodeTestElectron from '@vscode/test-electron';

const { downloadAndUnzipVSCode } = vscodeTestElectron;

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const extensionRoot = path.resolve(__dirname, '..');
const repoRoot = path.resolve(extensionRoot, '..');
const outputRoot = path.join(repoRoot, 'output', 'electron');
const cachePath = path.join(outputRoot, 'vscode-download-cache');
const targetDir = path.join(outputRoot, 'vscode-executable');
const targetExecutable = path.join(targetDir, process.platform === 'win32' ? 'Code.exe' : 'code');
const targetManifest = path.join(targetDir, 'manifest.json');

const options = parseArgs(process.argv.slice(2));

if (options.help) {
  printHelp();
  process.exit(0);
}

if (options.dryRun) {
  printPlan(options);
  process.exit(0);
}

if (options.mode !== 'provision') {
  throw new Error(
    [
      'Provisioning is explicit opt-in because it may download VS Code.',
      'Re-run with `provision <exact-version>` after reviewing the dry-run output.',
      '',
      `Version: ${options.version}`,
      `Platform: ${options.platform}`,
      `Target: ${targetDir}`,
    ].join('\n'),
  );
}

await provisionVSCode(options);

async function provisionVSCode(options) {
  mkdirSync(outputRoot, { recursive: true });
  console.log('[electron-provision] downloading or reusing VS Code cache');
  console.log(`[electron-provision] version=${options.version}`);
  console.log(`[electron-provision] platform=${options.platform}`);
  console.log(`[electron-provision] cache=${cachePath}`);

  const downloadedExecutable = await downloadAndUnzipVSCode({
    version: options.version,
    platform: options.platform,
    cachePath,
    extensionDevelopmentPath: extensionRoot,
  });
  const sourceDir = path.dirname(downloadedExecutable);

  if (!existsSync(downloadedExecutable)) {
    throw new Error(`downloadAndUnzipVSCode returned a missing executable: ${downloadedExecutable}`);
  }

  if (existsSync(targetDir)) {
    rmSync(targetDir, { recursive: true, force: true });
  }
  mkdirSync(targetDir, { recursive: true });
  cpSync(sourceDir, targetDir, { recursive: true });

  if (!existsSync(targetExecutable)) {
    throw new Error(`Provisioned executable missing at expected path: ${targetExecutable}`);
  }

  const manifest = {
    product: 'Visual Studio Code',
    executable: path.basename(targetExecutable),
    version: options.version,
    platform: options.platform,
    source: '@vscode/test-electron downloadAndUnzipVSCode',
    cache_path: cachePath,
    source_executable: downloadedExecutable,
    target_executable: targetExecutable,
    acquired_at: new Date().toISOString(),
    sha256: sha256File(targetExecutable),
    notes: 'Local provisioning for Electron smoke. Do not commit executable or manifest.',
  };
  writeFileSync(targetManifest, JSON.stringify(manifest, null, 2) + '\n', 'utf-8');

  console.log('[electron-provision] provisioned isolated VS Code executable');
  console.log(`[electron-provision] executable=${targetExecutable}`);
  console.log(`[electron-provision] manifest=${targetManifest}`);
  console.log('[electron-provision] next: npm run test:electron:smoke --prefix vscode-extension');
}

function parseArgs(args) {
  const options = {
    version: null,
    platform: process.platform === 'win32' ? 'win32-x64-archive' : undefined,
    mode: null,
    dryRun: false,
    help: false,
  };

  if (args[0] === 'dry-run' || args[0] === 'provision') {
    options.mode = args[0] === 'dry-run' ? 'dry-run' : 'provision';
    options.dryRun = args[0] === 'dry-run';
    if (args[1] && !args[1].startsWith('--')) {
      options.version = args[1];
      args = args.slice(2);
    } else {
      args = args.slice(1);
    }
  }

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === '--help' || arg === '-h') {
      options.help = true;
    } else if (arg === '--yes') {
      options.mode = 'provision';
    } else if (arg === '--dry-run') {
      options.dryRun = true;
    } else if (arg === '--vscode-version' || arg === '--version') {
      options.version = readOptionValue(args, index, arg);
      index += 1;
    } else if (arg.startsWith('--vscode-version=')) {
      options.version = arg.slice('--vscode-version='.length);
    } else if (arg.startsWith('--version=')) {
      options.version = arg.slice('--version='.length);
    } else if (arg === '--platform') {
      options.platform = readOptionValue(args, index, arg);
      index += 1;
    } else if (arg.startsWith('--platform=')) {
      options.platform = arg.slice('--platform='.length);
    } else {
      throw new Error(`Unknown option: ${arg}`);
    }
  }

  if (!options.version) {
    throw new Error('--vscode-version is required and must be an exact VS Code version such as 1.93.1.');
  }
  if (options.version === 'stable' || options.version === 'insiders') {
    throw new Error('--vscode-version must be exact for reproducible Electron smoke provisioning; do not use stable or insiders.');
  }
  if (!options.platform) {
    throw new Error('--platform must not be empty.');
  }
  return options;
}

function readOptionValue(args, index, optionName) {
  const value = args[index + 1];
  if (!value || value.startsWith('--')) {
    throw new Error(`${optionName} requires a value.`);
  }
  return value;
}

function printPlan(options) {
  console.log('[electron-provision] dry run');
  console.log(`[electron-provision] version=${options.version ?? '<required>'}`);
  console.log(`[electron-provision] platform=${options.platform}`);
  console.log(`[electron-provision] cache=${cachePath}`);
  console.log(`[electron-provision] target=${targetDir}`);
  console.log('[electron-provision] run `provision <version>` to download or reuse the VS Code cache');
}

function printHelp() {
  console.log([
    'Provision an isolated VS Code executable for Electron smoke validation.',
    '',
    'Usage:',
    '  node scripts/provision-electron-vscode.mjs dry-run <x.y.z>',
    '  node scripts/provision-electron-vscode.mjs provision <x.y.z>',
    '',
    'Options:',
    '  --vscode-version <value>   Exact VS Code version pin, such as 1.93.1',
    '  --platform <value>  VS Code download platform. Default on Windows: win32-x64-archive',
    '  dry-run <value>     Print paths and options without downloading',
    '  provision <value>   Download or reuse cache and refresh local executable',
    '  --dry-run           Legacy dry-run flag for direct node use',
    '  --yes               Legacy explicit consent flag for direct node use',
  ].join('\n'));
}

function sha256File(filePath) {
  const hash = createHash('sha256');
  const file = statSync(filePath);
  if (!file.isFile()) {
    throw new Error(`Expected file for sha256: ${filePath}`);
  }
  hash.update(readFileSync(filePath));
  return hash.digest('hex');
}
