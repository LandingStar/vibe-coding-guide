import * as vscode from 'vscode';
import { execFile } from 'child_process';
import { promisify } from 'util';

const execFileAsync = promisify(execFile);
const RESULT_PREFIX = '__DOC_BASED_CODING_PROGRESS_GRAPH__=';

type RegeneratedArtifacts = {
    history_path: string;
    dot_path: string;
    html_path: string;
    control_snapshot_path: string;
    trajectory_path: string;
};

type RegenerateProgressGraphArtifactsOptions = {
    projectRoot: string;
    sourceRoot: string | null;
    pythonPath: string;
    outputChannel: vscode.OutputChannel;
};

export async function regenerateProgressGraphArtifacts(
    options: RegenerateProgressGraphArtifactsOptions,
): Promise<RegeneratedArtifacts> {
    const { projectRoot, sourceRoot, pythonPath, outputChannel } = options;
    const buildProgressGraphArtifactsScript = [
        'import importlib.metadata',
        'import json',
        'import sys',
        'from pathlib import Path',
        ...(sourceRoot ? [`sys.path.append(${JSON.stringify(sourceRoot)})`] : []),
        'try:',
        '    runtime_root = importlib.metadata.distribution("doc-based-coding-runtime").locate_file("")',
        '    sys.path.insert(0, str(runtime_root))',
        'except importlib.metadata.PackageNotFoundError:',
        '    pass',
        'from tools.progress_graph import build_doc_progress_history, write_control_snapshot, write_doc_progress_history, write_history_dot, write_history_html, write_local_work_trajectory_artifact',
        '',
        'root = Path.cwd()',
        'history = build_doc_progress_history(root)',
        'history_path = write_doc_progress_history(root, history=history)',
        'dot_path = write_history_dot(root, history=history)',
        'html_path = write_history_html(root, history=history)',
        'control_snapshot_path = write_control_snapshot(root)',
        'trajectory_path = write_local_work_trajectory_artifact(root)',
        `print(${JSON.stringify(RESULT_PREFIX)} + json.dumps({`,
        `    'history_path': str(history_path),`,
        `    'dot_path': str(dot_path),`,
        `    'html_path': str(html_path),`,
        `    'control_snapshot_path': str(control_snapshot_path),`,
        `    'trajectory_path': str(trajectory_path),`,
        '}))',
    ].join('\n');

    outputChannel.appendLine(`[ProgressGraphPreview] Regenerating artifacts with Python: ${pythonPath}`);
    outputChannel.appendLine(
        sourceRoot
            ? `[ProgressGraphPreview] Using platform source root: ${sourceRoot}`
            : '[ProgressGraphPreview] Using installed doc-based-coding-runtime package root',
    );

    const { stdout, stderr } = await execFileAsync(
        pythonPath,
        ['-c', buildProgressGraphArtifactsScript],
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
        `[ProgressGraphPreview] Regenerated artifacts: ${parsed.history_path}, ${parsed.dot_path}, ${parsed.html_path}, ${parsed.control_snapshot_path}, ${parsed.trajectory_path}`,
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
