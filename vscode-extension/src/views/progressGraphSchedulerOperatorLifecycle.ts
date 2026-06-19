import type { SchedulerOperatorAction } from './schedulerOperatorContracts';

export type SchedulerOperatorLifecycleLastAction = {
  action: string;
  status: 'idle' | 'running' | 'succeeded' | 'failed';
  startedAt: string | null;
  completedAt: string | null;
  summary: string;
  stdout: string;
  stderr: string;
  payload: Record<string, unknown> | null;
};

export type SchedulerOperatorLifecycleResult =
  | {
      status: 'invalid';
      action: null;
      lastAction: null;
    }
  | {
      status: 'succeeded' | 'failed';
      action: SchedulerOperatorAction;
      lastAction: SchedulerOperatorLifecycleLastAction;
    };

export type SchedulerOperatorLifecycleHooks<Runtime> = {
  nowIso?: () => string;
  setLastAction: (action: SchedulerOperatorLifecycleLastAction) => void;
  renderRunningState: () => void | Promise<void>;
  resolveRuntime: () => Promise<Runtime>;
  runAction: (
    runtime: Runtime,
    action: SchedulerOperatorAction,
  ) => Promise<SchedulerOperatorLifecycleLastAction>;
  notifyInvalidInput: () => void;
  notifySucceeded: (summary: string) => void;
  notifyFailed: (summary: string) => void;
  reload: () => Promise<void>;
};

export async function runSchedulerOperatorActionLifecycle<Runtime>(
  action: SchedulerOperatorAction | null,
  hooks: SchedulerOperatorLifecycleHooks<Runtime>,
): Promise<SchedulerOperatorLifecycleResult> {
  if (!action) {
    hooks.notifyInvalidInput();
    return {
      status: 'invalid',
      action: null,
      lastAction: null,
    };
  }

  const startedAt = (hooks.nowIso ?? defaultNowIso)();
  hooks.setLastAction({
    action: action.kind,
    status: 'running',
    startedAt,
    completedAt: null,
    summary: 'running scheduler operator action',
    stdout: '',
    stderr: '',
    payload: null,
  });
  await hooks.renderRunningState();

  let lastAction: SchedulerOperatorLifecycleLastAction;
  try {
    const runtime = await hooks.resolveRuntime();
    lastAction = await hooks.runAction(runtime, action);
    hooks.setLastAction(lastAction);
    if (lastAction.status === 'succeeded') {
      hooks.notifySucceeded(lastAction.summary);
    } else {
      hooks.notifyFailed(lastAction.summary);
    }
  } catch (error) {
    const messageText = error instanceof Error ? error.message : String(error);
    lastAction = {
      action: action.kind,
      status: 'failed',
      startedAt,
      completedAt: (hooks.nowIso ?? defaultNowIso)(),
      summary: messageText,
      stdout: '',
      stderr: '',
      payload: null,
    };
    hooks.setLastAction(lastAction);
    hooks.notifyFailed(messageText);
  }

  await hooks.reload();
  return {
    status: lastAction.status === 'succeeded' ? 'succeeded' : 'failed',
    action,
    lastAction,
  };
}

function defaultNowIso(): string {
  return new Date().toISOString();
}
