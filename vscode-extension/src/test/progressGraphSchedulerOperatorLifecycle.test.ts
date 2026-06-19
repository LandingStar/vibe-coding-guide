import assert from 'node:assert/strict';
import test from 'node:test';

import {
  runSchedulerOperatorActionLifecycle,
  type SchedulerOperatorLifecycleLastAction,
} from '../views/progressGraphSchedulerOperatorLifecycle.js';

test('scheduler operator lifecycle renders running state, runs action, and reloads display', async () => {
  const calls: string[] = [];
  const lastActions: SchedulerOperatorLifecycleLastAction[] = [];

  const result = await runSchedulerOperatorActionLifecycle(
    { kind: 'project' },
    {
      nowIso: () => '2026-06-19T12:00:00.000Z',
      setLastAction: (lastAction) => {
        calls.push(`set:${lastAction.status}:${lastAction.action}`);
        lastActions.push(lastAction);
      },
      renderRunningState: () => {
        calls.push('render-running');
      },
      resolveRuntime: async () => {
        calls.push('resolve-runtime');
        return { projectRoot: 'E:/workspace/example' };
      },
      runAction: async (runtime, action) => {
        calls.push(`run:${runtime.projectRoot}:${action.kind}`);
        return {
          action: action.kind,
          status: 'succeeded',
          startedAt: '2026-06-19T12:00:00.000Z',
          completedAt: '2026-06-19T12:00:01.000Z',
          summary: 'projection refreshed · events=6 · lanes=4',
          stdout: '{"ok":true}',
          stderr: '',
          payload: {
            ok: true,
            projection_result: {
              lane_count: 4,
              event_count: 6,
              relation_count: 12,
            },
          },
        };
      },
      notifyInvalidInput: () => {
        calls.push('notify-invalid');
      },
      notifySucceeded: (summary) => {
        calls.push(`notify-success:${summary}`);
      },
      notifyFailed: (summary) => {
        calls.push(`notify-failed:${summary}`);
      },
      reload: async () => {
        calls.push('reload');
      },
    },
  );

  assert.equal(result.status, 'succeeded');
  assert.deepEqual(calls, [
    'set:running:project',
    'render-running',
    'resolve-runtime',
    'run:E:/workspace/example:project',
    'set:succeeded:project',
    'notify-success:projection refreshed · events=6 · lanes=4',
    'reload',
  ]);
  assert.equal(lastActions[0].status, 'running');
  assert.equal(lastActions[1].status, 'succeeded');
  assert.deepEqual(lastActions[1].payload?.projection_result, {
    lane_count: 4,
    event_count: 6,
    relation_count: 12,
  });
});

test('scheduler operator lifecycle rejects invalid messages before mutation', async () => {
  const calls: string[] = [];

  const result = await runSchedulerOperatorActionLifecycle(null, {
    setLastAction: () => {
      calls.push('set');
    },
    renderRunningState: () => {
      calls.push('render');
    },
    resolveRuntime: async () => {
      calls.push('resolve');
      return {};
    },
    runAction: async () => {
      calls.push('run');
      throw new Error('should not run');
    },
    notifyInvalidInput: () => {
      calls.push('notify-invalid');
    },
    notifySucceeded: () => {
      calls.push('notify-success');
    },
    notifyFailed: () => {
      calls.push('notify-failed');
    },
    reload: async () => {
      calls.push('reload');
    },
  });

  assert.equal(result.status, 'invalid');
  assert.deepEqual(calls, ['notify-invalid']);
});

test('scheduler operator lifecycle reloads after failed action', async () => {
  const calls: string[] = [];
  const result = await runSchedulerOperatorActionLifecycle(
    { kind: 'runLoop' },
    {
      nowIso: () => '2026-06-19T12:00:00.000Z',
      setLastAction: (lastAction) => {
        calls.push(`set:${lastAction.status}:${lastAction.summary}`);
      },
      renderRunningState: () => {
        calls.push('render-running');
      },
      resolveRuntime: async () => {
        calls.push('resolve-runtime');
        return {};
      },
      runAction: async () => {
        calls.push('run');
        throw new Error('runtime unavailable');
      },
      notifyInvalidInput: () => {
        calls.push('notify-invalid');
      },
      notifySucceeded: (summary) => {
        calls.push(`notify-success:${summary}`);
      },
      notifyFailed: (summary) => {
        calls.push(`notify-failed:${summary}`);
      },
      reload: async () => {
        calls.push('reload');
      },
    },
  );

  assert.equal(result.status, 'failed');
  assert.deepEqual(calls, [
    'set:running:running scheduler operator action',
    'render-running',
    'resolve-runtime',
    'run',
    'set:failed:runtime unavailable',
    'notify-failed:runtime unavailable',
    'reload',
  ]);
});
