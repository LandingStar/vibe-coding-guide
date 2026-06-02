import assert from 'node:assert/strict';
import test from 'node:test';

import { parseAssistantAction } from '../views/aiChatActionProtocol.js';

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