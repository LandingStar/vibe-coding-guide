import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import test from 'node:test';

const extensionSourcePath = join(__dirname, '..', '..', 'src', 'extension.ts');

test('ai chat localTrajectory success reloads an already-open progress graph preview', () => {
  const source = readFileSync(extensionSourcePath, 'utf-8');

  assert.match(source, /new AiChatViewProvider\(outputChannel, getLLMProvider\(\), async \(tool, ok\) => \{/);
  assert.match(source, /tool === 'localTrajectory' && ok/);
  assert.match(source, /progressGraphPreviewPanel\?\.reloadFromDiskIfOpen/);
  assert.match(source, /\[AI Chat\] Local trajectory preview reload failed:/);
});
