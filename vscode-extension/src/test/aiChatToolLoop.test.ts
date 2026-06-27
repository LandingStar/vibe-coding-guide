import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import test from 'node:test';

import { parseAssistantAction } from '../views/aiChatActionProtocol.js';

const toolLoopSourcePath = join(__dirname, '..', '..', 'src', 'views', 'aiChatToolLoop.ts');

test('parseAssistantAction parses a raw tool JSON object', () => {
  const action = parseAssistantAction('{"type":"tool","tool":"readFile","args":{"path":"README.md","startLine":1,"endLine":20},"reason":"Need the README summary"}');

  assert.deepEqual(action, {
    type: 'tool',
    tool: 'readFile',
    args: {
      path: 'README.md',
      startLine: 1,
      endLine: 20,
    },
    reason: 'Need the README summary',
  });
});

test('parseAssistantAction parses a fenced final JSON object', () => {
  const action = parseAssistantAction('```json\n{"type":"final","content":"这是最终回答。"}\n```');

  assert.deepEqual(action, {
    type: 'final',
    content: '这是最终回答。',
  });
});

test('parseAssistantAction rejects unknown tools', () => {
  const action = parseAssistantAction('{"type":"tool","tool":"runCommand","args":{"command":"npm test"}}');

  assert.equal(action, null);
});

test('parseAssistantAction accepts agent-owned local trajectory tool calls', () => {
  const action = parseAssistantAction(
    '{"type":"tool","tool":"localTrajectory","args":{"action":"start","laneLabel":"P1005","firstEventTitle":"读题与建模"},"reason":"track task start"}',
  );

  assert.deepEqual(action, {
    type: 'tool',
    tool: 'localTrajectory',
    args: {
      action: 'start',
      laneLabel: 'P1005',
      firstEventTitle: '读题与建模',
    },
    reason: 'track task start',
  });
});

test('ai chat prompt treats localTrajectory as the task-tracking mutation exception', () => {
  const source = readFileSync(toolLoopSourcePath, 'utf-8');

  assert.match(source, /read-only vibe-coding slice for workspace content/);
  assert.match(source, /localTrajectory tool is the explicit exception/);
  assert.match(source, /block\/wait for impediments/);
  assert.match(source, /close when the tracked task is done/);
  assert.match(source, /Before the first localTrajectory call/);
  assert.match(source, /server\/client\/API contract\/testing/);
  assert.match(source, /include sourceGraphId\/sourceNodeId on start/);
  assert.match(source, /Use localTrajectory addLane as soon as a distinct work context must begin/);
  assert.match(source, /localTrajectory addLane/);
  assert.match(source, /localTrajectory addCompound/);
  assert.match(source, /localTrajectory packRange/);
  assert.match(source, /localTrajectory packSubgraph/);
  assert.match(source, /appendChild, advanceChild, and closeChild/);
  assert.match(source, /localTrajectory merge/);
  assert.match(source, /localTrajectory relate/);
  assert.match(source, /localTrajectory setAnchor/);
  assert.match(source, /sourceGraphId and sourceNodeId/);
  assert.match(source, /depends_on, waits_for, unblocks, hands_off, syncs_from, or approves_new_line/);
  assert.match(source, /visible trajectory metadata only/);
  assert.match(source, /"action":"addCompound"/);
  assert.match(source, /"action":"packRange"/);
  assert.match(source, /"action":"packSubgraph"/);
  assert.match(source, /"action":"appendChild"/);
  assert.match(source, /"action":"advanceChild"/);
  assert.match(source, /do not invent dependency scheduling, conflict resolution, or review-barrier semantics/);
  assert.match(source, /"action":"relate"/);
  assert.match(source, /"action":"setAnchor"/);
  assert.match(source, /"sourceGraphId":"project-checklist-current"/);
  assert.match(source, /"sourceNodeId":"milestone:active-slice"/);
  assert.match(source, /sourceEndpointTrajectoryId/);
  assert.match(source, /targetEndpointTrajectoryId/);
  assert.match(source, /completed validation\/delivery node unadvanced/);
  assert.match(source, /Do not ask the user to manually press Local Work Trajectory buttons/);
  assert.doesNotMatch(source, /cannot edit files, apply patches, or run terminal commands\.',\s*'Reply with exactly one JSON object/);
});

test('parseAssistantAction takes the first balanced JSON object from concatenated tool calls', () => {
  const action = parseAssistantAction(
    '{"type":"tool","tool":"listFiles","args":{"path":"."},"reason":"first"}'
    + '{"type":"tool","tool":"readFile","args":{"path":"README.md"},"reason":"second"}',
  );

  assert.deepEqual(action, {
    type: 'tool',
    tool: 'listFiles',
    args: {
      path: '.',
    },
    reason: 'first',
  });
});
