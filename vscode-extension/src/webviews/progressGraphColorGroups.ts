import { resolveColorGroupColor } from '@note-web/knowledge-graph-engine';
import type {
  GraphColorGroup,
  GraphColorQueryContext,
  GraphColorQueryNode,
} from '@note-web/knowledge-graph-engine';

export type ProgressGraphColorNode = {
  id: string;
  label: string;
  kind: string;
  status: string;
  summary: string;
  tags: string[];
  hasRuntimeBinding: boolean;
  workItemIds?: string[];
  groupItemIds?: string[];
};

export type ProgressGraphColorGroup = GraphColorGroup;

const statusColors: Record<string, string> = {
  pending: '#9f7630',
  in_progress: '#2f74ad',
  blocked: '#a94e48',
  completed: '#4f8d62',
  archived: '#737f8c',
};

export function buildProgressGraphNodeColorMap(
  nodes: ProgressGraphColorNode[],
  colorGroups: ProgressGraphColorGroup[],
): Map<string, string> {
  return new Map(nodes.map((node) => [node.id, resolveProgressGraphNodeColor(node, colorGroups)]));
}

export function resolveProgressGraphNodeColor(
  node: ProgressGraphColorNode,
  colorGroups: ProgressGraphColorGroup[],
): string {
  const result = resolveColorGroupColor(buildProgressGraphColorContext(node), colorGroups, {
    fallbackColor: () => defaultProgressGraphNodeColor(node),
  });
  return result.color;
}

export function buildProgressGraphColorContext(node: ProgressGraphColorNode): GraphColorQueryContext {
  return {
    node: buildProgressGraphColorQueryNode(node),
    nodeId: node.id,
    file: node.label || node.id,
    path: node.id,
    content: node.summary,
    properties: {
      kind: node.kind,
      status: node.status,
      tags: node.tags,
      bound: node.hasRuntimeBinding,
      hasRuntimeBinding: node.hasRuntimeBinding,
      workItemIds: node.workItemIds ?? [],
      groupItemIds: node.groupItemIds ?? [],
    },
  };
}

export function defaultProgressGraphNodeColor(node: Pick<ProgressGraphColorNode, 'status'>): string {
  return statusColors[node.status] ?? '#526a7f';
}

function buildProgressGraphColorQueryNode(node: ProgressGraphColorNode): GraphColorQueryNode {
  return {
    id: node.id,
    label: node.label,
    kind: node.kind,
    status: node.status,
    summary: node.summary,
    tags: node.tags,
    color: defaultProgressGraphNodeColor(node),
    data: {
      bound: node.hasRuntimeBinding,
      hasRuntimeBinding: node.hasRuntimeBinding,
      workItemIds: node.workItemIds ?? [],
      groupItemIds: node.groupItemIds ?? [],
    },
  };
}
