import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import test from 'node:test';

const sourcePath = join(__dirname, '..', '..', 'src', 'views', 'aiChatTools.ts');

test('ai chat localTrajectory tool exposes compound packing actions', () => {
  const source = readFileSync(sourcePath, 'utf-8');

  assert.match(source, /'addCompound'/);
  assert.match(source, /'packRange'/);
  assert.match(source, /'packSubgraph'/);
  assert.match(source, /'appendChild'/);
  assert.match(source, /'advanceChild'/);
  assert.match(source, /'closeChild'/);
  assert.match(source, /'setAnchor'/);
  assert.match(source, /add_local_work_compound/);
  assert.match(source, /pack_local_work_range/);
  assert.match(source, /pack_local_work_subgraph/);
  assert.match(source, /append_local_work_child_event/);
  assert.match(source, /advance_local_work_child_event/);
  assert.match(source, /close_local_work_child_trajectory/);
  assert.match(source, /set_local_work_trajectory_anchor/);
  assert.match(source, /elif kind == "addCompound":/);
  assert.match(source, /elif kind == "packRange":/);
  assert.match(source, /elif kind == "packSubgraph":/);
  assert.match(source, /elif kind == "appendChild":/);
  assert.match(source, /elif kind == "advanceChild":/);
  assert.match(source, /elif kind == "closeChild":/);
  assert.match(source, /elif kind == "setAnchor":/);
  assert.match(source, /first_child_event_title=action\.get\("firstChildEventTitle"\) or action\.get\("firstEventTitle"\) or ""/);
  assert.match(source, /range_start_event_id=action\.get\("rangeStartEventId"\) or action\.get\("sourceEventId"\) or ""/);
  assert.match(source, /range_end_event_id=action\.get\("rangeEndEventId"\) or action\.get\("targetEventId"\) or ""/);
  assert.match(source, /ranges=action\.get\("packRanges"\) or \[\]/);
  assert.match(source, /anchor_lane_id=action\.get\("anchorLaneId"\) or action\.get\("laneId"\) or ""/);
  assert.match(source, /source_endpoint=source_endpoint/);
  assert.match(source, /target_endpoint=target_endpoint/);
  assert.match(source, /parent_event_id=action\.get\("parentEventId"\) or action\.get\("targetEventId"\) or action\.get\("currentEventId"\) or ""/);
  assert.match(source, /child_trajectory_count/);
  assert.match(source, /sourceGraphId/);
  assert.match(source, /sourceNodeId/);
  assert.match(source, /source_graph_id=action\.get\("sourceGraphId"\) or ""/);
  assert.match(source, /source_node_id=action\.get\("sourceNodeId"\) or ""/);
  assert.match(source, /visible from birth/);
});
