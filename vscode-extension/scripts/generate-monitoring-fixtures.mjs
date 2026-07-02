// @ts-check
/**
 * Generate standalone HTML pages for monitoring dashboard screenshot validation.
 *
 * Usage:
 *   node scripts/generate-monitoring-fixtures.mjs
 *
 * Reads fixture JSON from src/test/fixtures/monitoring/ and produces
 * standalone HTML pages in output/monitoring-screenshots/ that can be
 * opened in any browser (no VS Code needed).
 */

import { readFileSync, mkdirSync, writeFileSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const projectRoot = join(__dirname, '..');
const fixturesDir = join(projectRoot, 'src', 'test', 'fixtures', 'monitoring');
const distDir = join(projectRoot, 'dist', 'webviews');
const outputDir = join(projectRoot, 'output', 'monitoring-screenshots');

if (!existsSync(fixturesDir)) {
    console.error('Fixtures directory not found:', fixturesDir);
    process.exit(1);
}

if (!existsSync(distDir)) {
    console.error('Build dist directory not found:', distDir);
    console.error('Run `npm run build` first.');
    process.exit(1);
}

mkdirSync(outputDir, { recursive: true });

const jsContent = readFileSync(join(distDir, 'monitoringDashboard.js'), 'utf-8');
const cssContent = readFileSync(join(distDir, 'monitoringDashboard.css'), 'utf-8');

const fixtures = [
    { file: 'healthy-c9-passed.json', name: 'healthy' },
    { file: 'missing-live-smoke.json', name: 'missing-smoke' },
    { file: 'failed-delivery.json', name: 'failed-delivery' },
];

function buildPage(payload, title, width) {
    const escapedPayload = JSON.stringify(payload).replace(/</g, '\\u003c');
    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${title}</title>
  <style>
    ${cssContent}
    /* Override VS Code variables with reasonable defaults for standalone viewing */
    :root {
      --vscode-editor-background: #1e1e1e;
      --vscode-editor-foreground: #d4d4d4;
      --vscode-sideBar-background: #252526;
      --vscode-font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      --vscode-font-size: 13px;
      --vscode-editor-font-family: 'Consolas', 'Courier New', monospace;
      --vscode-panel-border: rgba(128, 128, 128, 0.35);
      --vscode-descriptionForeground: #969696;
      --vscode-button-secondaryBackground: #3a3d41;
      --vscode-button-secondaryForeground: #ffffff;
      --vscode-button-secondaryHoverBackground: #45494e;
      --vscode-input-background: #3c3c3c;
      --vscode-input-foreground: #cccccc;
      --vscode-input-border: #555555;
      --vscode-testing-iconPassed: #73c991;
      --vscode-editorWarning-foreground: #cca700;
      --vscode-editorError-foreground: #f14c4c;
      --vscode-editorInfo-foreground: #3794ff;
      --vscode-disabledForeground: #888888;
      --vscode-charts-blue: #3794ff;
      --vscode-charts-green: #89d185;
    }
    body { width: ${width}px; }
  </style>
</head>
<body>
  <div id="monitoring-root"></div>
  <script type="application/json" id="monitoringPayload">${escapedPayload}</script>
  <script>${jsContent}</script>
</body>
</html>`;
}

for (const { file, name } of fixtures) {
    const fixturePath = join(fixturesDir, file);
    if (!existsSync(fixturePath)) {
        console.warn(`Skipping ${file}: not found`);
        continue;
    }
    const payload = JSON.parse(readFileSync(fixturePath, 'utf-8'));

    // Wide viewport (1200px)
    const widePath = join(outputDir, `${name}-1200px.html`);
    writeFileSync(widePath, buildPage(payload, `Monitoring - ${name} (1200px)`, 1200), 'utf-8');
    console.log(`Generated: ${widePath}`);

    // Narrow viewport (480px)
    const narrowPath = join(outputDir, `${name}-480px.html`);
    writeFileSync(narrowPath, buildPage(payload, `Monitoring - ${name} (480px)`, 480), 'utf-8');
    console.log(`Generated: ${narrowPath}`);
}

console.log(`\nDone. Open files in output/monitoring-screenshots/ for screenshot validation.`);
