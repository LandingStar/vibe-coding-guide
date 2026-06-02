import assert from 'node:assert/strict';

import {
  buildProgressGraphColorContext,
  buildProgressGraphNodeColorMap,
  defaultProgressGraphNodeColor,
} from '../webviews/progressGraphColorGroups';

const blockedNode = {
  id: 'gate::planning',
  label: 'Planning Gate',
  kind: 'task',
  status: 'blocked',
  summary: 'Runtime handoff validation is active',
  tags: ['active', '#risk'],
  hasRuntimeBinding: true,
  workItemIds: ['todo:024'],
  groupItemIds: ['group:gate'],
};

const completedNode = {
  id: 'phase::archive',
  label: 'Archive Phase',
  kind: 'phase',
  status: 'completed',
  summary: 'Superseded renderer work is archived',
  tags: ['archive'],
  hasRuntimeBinding: false,
  workItemIds: [],
  groupItemIds: [],
};

{
  const colors = buildProgressGraphNodeColorMap([blockedNode, completedNode], [
    { id: 'disabled', query: 'status:blocked', color: '#111111', enabled: false },
    { id: 'risk', query: 'tag:risk OR bound:true', color: '#ff0000' },
    { id: 'blocked', query: 'status:blocked', color: '#00ff00' },
  ]);

  assert.equal(colors.get(blockedNode.id), '#ff0000');
  assert.equal(colors.get(completedNode.id), defaultProgressGraphNodeColor(completedNode));
}

{
  const colors = buildProgressGraphNodeColorMap([blockedNode, completedNode], [
    { id: 'summary', query: '"renderer work"', color: '#123456' },
  ]);

  assert.equal(colors.get(completedNode.id), '#123456');
}

{
  const context = buildProgressGraphColorContext(blockedNode);

  assert.equal(context.node.id, blockedNode.id);
  assert.equal(context.content, blockedNode.summary);
  assert.deepEqual(context.properties?.tags, blockedNode.tags);
  assert.equal(context.properties?.bound, true);
}
