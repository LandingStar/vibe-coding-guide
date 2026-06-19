import * as vscode from 'vscode';
import { execFile } from 'child_process';
import { promisify } from 'util';

import {
  coerceHostEvidencePresentation,
  type ProgressGraphPreviewHostEvidencePresentation,
} from './progressGraphPreviewHtml';

const execFileAsync = promisify(execFile);
export const HOST_EVIDENCE_PRESENTATION_RESOURCE_URI = 'dbc://host-evidence/presentation';

export type ReadHostEvidencePresentationOptions = {
  projectRoot: string;
  sourceRoot: string | null;
  pythonPath: string;
  outputChannel: vscode.OutputChannel;
};

export async function readHostEvidencePresentation(
  options: ReadHostEvidencePresentationOptions,
): Promise<ProgressGraphPreviewHostEvidencePresentation> {
  const { projectRoot, sourceRoot, pythonPath, outputChannel } = options;
  const readPresentationScript = [
    'import importlib.metadata',
    'import json',
    'import sys',
    ...(sourceRoot ? [`sys.path.append(${JSON.stringify(sourceRoot)})`] : []),
    'try:',
    '    runtime_root = importlib.metadata.distribution("doc-based-coding-runtime").locate_file("")',
    '    sys.path.insert(0, str(runtime_root))',
    'except importlib.metadata.PackageNotFoundError:',
    '    pass',
    'from src.mcp.tools import GovernanceTools',
    `tools = GovernanceTools(${JSON.stringify(projectRoot)}, dry_run=True)`,
    `content = tools.read_resource(${JSON.stringify(HOST_EVIDENCE_PRESENTATION_RESOURCE_URI)})`,
    'if content is None:',
    `    raise RuntimeError("resource not found: ${HOST_EVIDENCE_PRESENTATION_RESOURCE_URI}")`,
    'if isinstance(content, dict):',
    '    print(json.dumps(content, ensure_ascii=False))',
    'else:',
    '    print(content)',
  ].join('\n');

  outputChannel.appendLine(
    `[ProgressGraphPreview] Reading host evidence presentation with Python: ${pythonPath}`,
  );

  const { stdout, stderr } = await execFileAsync(
    pythonPath,
    ['-c', readPresentationScript],
    {
      cwd: projectRoot,
      maxBuffer: 1024 * 1024,
    },
  );

  const stderrText = stderr?.trim();
  if (stderrText) {
    outputChannel.appendLine(`[ProgressGraphPreview host evidence stderr] ${stderrText}`);
  }

  return coerceHostEvidencePresentation(JSON.parse(stdout));
}
