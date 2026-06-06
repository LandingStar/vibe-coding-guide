import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import test from 'node:test';

const manifestPath = join(__dirname, '..', '..', 'package.json');

test('extension manifest does not expose local work trajectory mutation commands to users', () => {
  const manifest = JSON.parse(readFileSync(manifestPath, 'utf-8')) as {
    contributes?: {
      commands?: Array<{ command?: string; title?: string }>;
    };
  };
  const commands = new Map(
    (manifest.contributes?.commands ?? []).map((command) => [command.command, command.title]),
  );

  assert.equal(commands.has('docBasedCoding.startLocalWorkTrajectory'), false);
  assert.equal(commands.has('docBasedCoding.appendLocalWorkTrajectoryEvent'), false);
  assert.equal(commands.has('docBasedCoding.advanceLocalWorkTrajectoryEvent'), false);
});
