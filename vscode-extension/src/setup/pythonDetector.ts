/**
 * Python environment detection for the setup wizard.
 *
 * Checks for a usable Python installation and whether the
 * doc-based-coding runtime package is installed.
 */

import * as vscode from 'vscode';
import * as path from 'path';
import { execFile } from 'child_process';
import { promisify } from 'util';
import { existsSync } from 'fs';

const execFileAsync = promisify(execFile);

export interface PythonDetectionResult {
    /** Whether a usable Python was found. */
    pythonFound: boolean;
    /** The resolved python executable path. */
    pythonPath: string | null;
    /** Python version string (e.g. "3.12.8"). */
    pythonVersion: string | null;
    /** Whether the runtime package is installed. */
    runtimeInstalled: boolean;
    /** Runtime version if installed (e.g. "0.9.3"). */
    runtimeVersion: string | null;
    /** Whether the MCP server module is loadable. */
    mcpServerAvailable: boolean;
    /** Summary message for display. */
    summary: string;
}

/**
 * Detect Python environment and runtime status.
 */
export async function detectPythonEnvironment(
    projectRoot: string,
    outputChannel: vscode.OutputChannel,
): Promise<PythonDetectionResult> {
    const result: PythonDetectionResult = {
        pythonFound: false,
        pythonPath: null,
        pythonVersion: null,
        runtimeInstalled: false,
        runtimeVersion: null,
        mcpServerAvailable: false,
        summary: '',
    };

    // 1. Find Python executable
    const pythonPath = await findPython(projectRoot);
    if (!pythonPath) {
        result.summary = 'Python not found. Please install Python >= 3.10.';
        outputChannel.appendLine('[Setup] No Python executable found.');
        return result;
    }

    result.pythonPath = pythonPath;
    outputChannel.appendLine(`[Setup] Found Python: ${pythonPath}`);

    // 2. Check Python version
    try {
        const { stdout } = await execFileAsync(pythonPath, [
            '-c', 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")',
        ], { timeout: 10000 });
        result.pythonVersion = stdout.trim();
        const [major, minor] = result.pythonVersion.split('.').map(Number);
        if (major < 3 || (major === 3 && minor < 10)) {
            result.summary = `Python ${result.pythonVersion} found but >= 3.10 is required.`;
            outputChannel.appendLine(`[Setup] Python version too old: ${result.pythonVersion}`);
            return result;
        }
        result.pythonFound = true;
        outputChannel.appendLine(`[Setup] Python version: ${result.pythonVersion}`);
    } catch {
        result.summary = `Python found at ${pythonPath} but failed to check version.`;
        outputChannel.appendLine(`[Setup] Failed to check Python version at ${pythonPath}`);
        return result;
    }

    // 3. Check if runtime package is installed
    try {
        const { stdout } = await execFileAsync(pythonPath, [
            '-c', 'from importlib.metadata import version; print(version("doc-based-coding-runtime"))',
        ], { timeout: 10000 });
        result.runtimeVersion = stdout.trim();
        result.runtimeInstalled = true;
        outputChannel.appendLine(`[Setup] Runtime version: ${result.runtimeVersion}`);
    } catch {
        outputChannel.appendLine('[Setup] Runtime package not installed.');
    }

    // 4. Check if MCP server module is loadable
    if (result.runtimeInstalled) {
        try {
            await execFileAsync(pythonPath, [
                '-c', 'import src.mcp.server',
            ], { timeout: 10000, cwd: projectRoot });
            result.mcpServerAvailable = true;
            outputChannel.appendLine('[Setup] MCP server module available.');
        } catch {
            outputChannel.appendLine('[Setup] MCP server module not loadable from project root.');
        }
    }

    // 5. Build summary
    if (result.runtimeInstalled && result.mcpServerAvailable) {
        result.summary = `Ready — Python ${result.pythonVersion}, Runtime ${result.runtimeVersion}`;
    } else if (result.runtimeInstalled) {
        result.summary = `Runtime ${result.runtimeVersion} installed but MCP server not loadable. Check project structure.`;
    } else {
        result.summary = `Python ${result.pythonVersion} found but runtime not installed.`;
    }

    return result;
}

/**
 * Find a Python executable by checking workspace venvs, config, and system PATH.
 */
async function findPython(projectRoot: string): Promise<string | null> {
    // Check user setting first
    const configured = vscode.workspace.getConfiguration('docBasedCoding').get<string>('pythonPath');
    if (configured && existsSync(configured)) {
        return configured;
    }

    // Check common venv locations
    const isWindows = process.platform === 'win32';
    const binDir = isWindows ? 'Scripts' : 'bin';
    const exe = isWindows ? 'python.exe' : 'python';

    const venvNames = ['.venv', '.venv-release-test', 'venv'];
    for (const name of venvNames) {
        const candidate = path.join(projectRoot, name, binDir, exe);
        if (existsSync(candidate)) {
            return candidate;
        }
    }

    // Check ms-python extension
    try {
        const pythonExt = vscode.extensions.getExtension('ms-python.python');
        if (pythonExt?.isActive) {
            const api = pythonExt.exports;
            const envPath = api?.environments?.getActiveEnvironmentPath?.();
            if (envPath?.path && existsSync(envPath.path)) {
                return envPath.path;
            }
        }
    } catch {
        // ms-python not available
    }

    // Fallback to system python
    try {
        await execFileAsync(isWindows ? 'python' : 'python3', ['--version'], { timeout: 5000 });
        return isWindows ? 'python' : 'python3';
    } catch {
        return null;
    }
}
