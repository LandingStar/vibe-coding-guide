import * as vscode from 'vscode';
import { execFile } from 'child_process';
import { promisify } from 'util';

const execFileAsync = promisify(execFile);
const RESULT_PREFIX = '__DOC_BASED_CODING_PROGRESS_GRAPH__=';
const BUILD_PROGRESS_GRAPH_ARTIFACTS_SCRIPT = [
    'import json',
    'from pathlib import Path',
    'from tools.progress_graph import build_doc_progress_history, write_doc_progress_history, write_history_dot, write_history_html',
    '',
    'root = Path.cwd()',
    'history = build_doc_progress_history(root)',
    'history_path = write_doc_progress_history(root, history=history)',
    'dot_path = write_history_dot(root, history=history)',
    'html_path = write_history_html(root, history=history)',
    `print(${JSON.stringify(RESULT_PREFIX)} + json.dumps({`,
    `    'history_path': str(history_path),`,
    `    'dot_path': str(dot_path),`,
    `    'html_path': str(html_path),`,
    '}))',
].join('\n');

type RegeneratedArtifacts = {
    history_path: string;
    dot_path: string;
    html_path: string;
};

type RegenerateProgressGraphArtifactsOptions = {
    projectRoot: string;
    pythonPath: string;
    outputChannel: vscode.OutputChannel;
};

export async function regenerateProgressGraphArtifacts(
    options: RegenerateProgressGraphArtifactsOptions,
): Promise<RegeneratedArtifacts> {
    const { projectRoot, pythonPath, outputChannel } = options;

    outputChannel.appendLine(`[ProgressGraphPreview] Regenerating artifacts with Python: ${pythonPath}`);

    const { stdout, stderr } = await execFileAsync(
        pythonPath,
        ['-c', BUILD_PROGRESS_GRAPH_ARTIFACTS_SCRIPT],
        {
            cwd: projectRoot,
            maxBuffer: 1024 * 1024,
        },
    );

    const stderrText = stderr?.trim();
    if (stderrText) {
        outputChannel.appendLine(`[ProgressGraphPreview stderr] ${stderrText}`);
    }

    const parsed = parseArtifactsResult(stdout);
    outputChannel.appendLine(
        `[ProgressGraphPreview] Regenerated artifacts: ${parsed.history_path}, ${parsed.dot_path}, ${parsed.html_path}`,
    );
    return parsed;
}

function parseArtifactsResult(stdout: string): RegeneratedArtifacts {
    const resultLine = stdout
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter(Boolean)
        .find((line) => line.startsWith(RESULT_PREFIX));

    if (!resultLine) {
        throw new Error('Progress graph artifact refresh did not return artifact paths.');
    }

    return JSON.parse(resultLine.slice(RESULT_PREFIX.length)) as RegeneratedArtifacts;
}