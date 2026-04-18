/**
 * Connection diagnostics — runs comprehensive checks and reports
 * actionable status to the output channel.
 */

import * as vscode from 'vscode';
import { execFile } from 'child_process';
import { promisify } from 'util';
import { existsSync } from 'fs';
import * as path from 'path';

const execFileAsync = promisify(execFile);

export interface DiagnosticResult {
    ok: boolean;
    checks: DiagnosticCheck[];
}

export interface DiagnosticCheck {
    name: string;
    status: 'pass' | 'fail' | 'warn';
    message: string;
    fix?: string;
}

/**
 * Run full connection diagnostics and display results.
 */
export async function runDiagnostics(
    projectRoot: string,
    outputChannel: vscode.OutputChannel,
): Promise<DiagnosticResult> {
    const checks: DiagnosticCheck[] = [];
    outputChannel.appendLine('');
    outputChannel.appendLine('═══════════════════════════════════════════════════');
    outputChannel.appendLine('  Doc-Based Coding: Connection Diagnostics');
    outputChannel.appendLine('═══════════════════════════════════════════════════');
    outputChannel.appendLine('');

    // 1. Check workspace folder
    const workspaceCheck = checkWorkspace(projectRoot);
    checks.push(workspaceCheck);
    logCheck(outputChannel, workspaceCheck);

    // 2. Find Python
    const pythonCheck = await checkPython(projectRoot);
    checks.push(pythonCheck);
    logCheck(outputChannel, pythonCheck);

    if (pythonCheck.status === 'fail') {
        outputChannel.appendLine('');
        outputChannel.appendLine('⛔ Cannot proceed without Python. Fix the above issue first.');
        outputChannel.show();
        return { ok: false, checks };
    }

    const pythonPath = pythonCheck.message.match(/→ (.+)$/)?.[1] ?? 'python';

    // 3. Check runtime package
    const runtimeCheck = await checkRuntime(pythonPath);
    checks.push(runtimeCheck);
    logCheck(outputChannel, runtimeCheck);

    // 4. Check MCP server module
    const mcpModuleCheck = await checkMCPModule(pythonPath, projectRoot);
    checks.push(mcpModuleCheck);
    logCheck(outputChannel, mcpModuleCheck);

    // 5. Check entry point command
    const entryPointCheck = await checkEntryPoint(pythonPath);
    checks.push(entryPointCheck);
    logCheck(outputChannel, entryPointCheck);

    // 6. Check server mode config
    const serverModeCheck = checkServerMode(mcpModuleCheck, entryPointCheck);
    checks.push(serverModeCheck);
    logCheck(outputChannel, serverModeCheck);

    // 7. Check for pack/docs files
    const contentCheck = checkGovernanceContent(projectRoot);
    checks.push(contentCheck);
    logCheck(outputChannel, contentCheck);

    // Summary
    outputChannel.appendLine('');
    outputChannel.appendLine('───────────────────────────────────────────────────');
    const failCount = checks.filter(c => c.status === 'fail').length;
    const warnCount = checks.filter(c => c.status === 'warn').length;

    if (failCount === 0 && warnCount === 0) {
        outputChannel.appendLine('✅ All checks passed. MCP server should work correctly.');
    } else if (failCount === 0) {
        outputChannel.appendLine(`⚠️  ${warnCount} warning(s) — server may work but with limited functionality.`);
    } else {
        outputChannel.appendLine(`❌ ${failCount} error(s), ${warnCount} warning(s) — fix errors to enable MCP connection.`);
    }

    // Show fixes for failures
    const fixes = checks.filter(c => c.status === 'fail' && c.fix);
    if (fixes.length > 0) {
        outputChannel.appendLine('');
        outputChannel.appendLine('Recommended fixes:');
        for (const f of fixes) {
            outputChannel.appendLine(`  → ${f.fix}`);
        }
    }

    outputChannel.appendLine('───────────────────────────────────────────────────');
    outputChannel.appendLine('');
    outputChannel.show();

    return { ok: failCount === 0, checks };
}

function logCheck(channel: vscode.OutputChannel, check: DiagnosticCheck): void {
    const icon = check.status === 'pass' ? '✅' : check.status === 'warn' ? '⚠️ ' : '❌';
    channel.appendLine(`${icon} [${check.name}] ${check.message}`);
    if (check.fix && check.status !== 'pass') {
        channel.appendLine(`   Fix: ${check.fix}`);
    }
}

function checkWorkspace(projectRoot: string): DiagnosticCheck {
    if (!projectRoot) {
        return {
            name: 'Workspace',
            status: 'fail',
            message: 'No workspace folder open.',
            fix: 'Open a folder in VS Code.',
        };
    }
    return {
        name: 'Workspace',
        status: 'pass',
        message: `Project root → ${projectRoot}`,
    };
}

async function checkPython(projectRoot: string): Promise<DiagnosticCheck> {
    const configured = vscode.workspace.getConfiguration('docBasedCoding').get<string>('pythonPath');

    // Check if configured path exists
    if (configured) {
        if (existsSync(configured)) {
            const version = await getPythonVersion(configured);
            if (version) {
                return {
                    name: 'Python',
                    status: 'pass',
                    message: `Python ${version} (configured) → ${configured}`,
                };
            }
        } else {
            // Configured path is stale — warn and continue searching
            return {
                name: 'Python',
                status: 'warn',
                message: `Configured pythonPath does not exist: ${configured}. Falling back to auto-detection.`,
                fix: 'Clear docBasedCoding.pythonPath in workspace settings or update to a valid path.',
            };
        }
    }

    // Try workspace venvs
    const isWindows = process.platform === 'win32';
    const binDir = isWindows ? 'Scripts' : 'bin';
    const exe = isWindows ? 'python.exe' : 'python';

    for (const name of ['.venv', 'venv', '.venv-release-test']) {
        const candidate = path.join(projectRoot, name, binDir, exe);
        if (existsSync(candidate)) {
            const version = await getPythonVersion(candidate);
            if (version) {
                return {
                    name: 'Python',
                    status: 'pass',
                    message: `Python ${version} (workspace ${name}/) → ${candidate}`,
                };
            }
        }
    }

    // Try ms-python extension
    try {
        const pythonExt = vscode.extensions.getExtension('ms-python.python');
        if (pythonExt?.isActive) {
            const api = pythonExt.exports;
            const envPath = api?.environments?.getActiveEnvironmentPath?.();
            if (envPath?.path && existsSync(envPath.path)) {
                const version = await getPythonVersion(envPath.path);
                if (version) {
                    return {
                        name: 'Python',
                        status: 'pass',
                        message: `Python ${version} (ms-python) → ${envPath.path}`,
                    };
                }
            }
        }
    } catch { /* ignore */ }

    // Try system python
    const sysExe = isWindows ? 'python' : 'python3';
    const version = await getPythonVersion(sysExe);
    if (version) {
        return {
            name: 'Python',
            status: 'warn',
            message: `Python ${version} (system PATH) → ${sysExe}`,
            fix: 'Consider creating a workspace .venv for isolation: python -m venv .venv',
        };
    }

    return {
        name: 'Python',
        status: 'fail',
        message: 'No Python >= 3.10 found.',
        fix: 'Install Python >= 3.10 and ensure it is in PATH, or set docBasedCoding.pythonPath.',
    };
}

async function checkRuntime(pythonPath: string): Promise<DiagnosticCheck> {
    try {
        const { stdout } = await execFileAsync(pythonPath, [
            '-c', 'from importlib.metadata import version; print(version("doc-based-coding-runtime"))',
        ], { timeout: 10000 });
        return {
            name: 'Runtime',
            status: 'pass',
            message: `doc-based-coding-runtime v${stdout.trim()} installed`,
        };
    } catch {
        return {
            name: 'Runtime',
            status: 'fail',
            message: 'doc-based-coding-runtime package not installed.',
            fix: 'pip install doc_based_coding_runtime-*.whl (from the release/ directory)',
        };
    }
}

async function checkMCPModule(pythonPath: string, projectRoot: string): Promise<DiagnosticCheck> {
    try {
        await execFileAsync(pythonPath, [
            '-c', 'import src.mcp.server; print("ok")',
        ], { timeout: 10000, cwd: projectRoot });
        return {
            name: 'MCP Module',
            status: 'pass',
            message: '`src.mcp.server` importable',
        };
    } catch {
        return {
            name: 'MCP Module',
            status: 'warn',
            message: '`src.mcp.server` not importable from project root.',
            fix: 'This is normal if you installed via .whl. The "command" or "auto" server mode will use the CLI entry point instead.',
        };
    }
}

async function checkEntryPoint(pythonPath: string): Promise<DiagnosticCheck> {
    // Check if the doc-based-coding-mcp command is available in the same env
    const isWindows = process.platform === 'win32';
    const pythonDir = path.dirname(pythonPath);
    const entryPoint = path.join(pythonDir, isWindows ? 'doc-based-coding-mcp.exe' : 'doc-based-coding-mcp');

    if (existsSync(entryPoint)) {
        return {
            name: 'Entry Point',
            status: 'pass',
            message: `doc-based-coding-mcp → ${entryPoint}`,
        };
    }

    // Try without full path (might be in PATH)
    try {
        await execFileAsync(isWindows ? 'where' : 'which', ['doc-based-coding-mcp'], { timeout: 5000 });
        return {
            name: 'Entry Point',
            status: 'pass',
            message: 'doc-based-coding-mcp found in PATH',
        };
    } catch {
        return {
            name: 'Entry Point',
            status: 'warn',
            message: 'doc-based-coding-mcp CLI not found.',
            fix: 'Install runtime via pip to get the CLI entry point, or use serverMode="module".',
        };
    }
}

function checkServerMode(
    mcpModule: DiagnosticCheck,
    entryPoint: DiagnosticCheck,
): DiagnosticCheck {
    const mode = vscode.workspace.getConfiguration('docBasedCoding').get<string>('serverMode') ?? 'auto';

    if (mode === 'module' && mcpModule.status === 'fail') {
        return {
            name: 'Server Mode',
            status: 'fail',
            message: 'serverMode="module" but src.mcp.server is not importable.',
            fix: 'Switch to serverMode="auto" or "command", or ensure src/ is accessible.',
        };
    }
    if (mode === 'command' && entryPoint.status !== 'pass') {
        return {
            name: 'Server Mode',
            status: 'fail',
            message: 'serverMode="command" but doc-based-coding-mcp is not available.',
            fix: 'Install the runtime .whl to get the CLI entry point, or switch to serverMode="module".',
        };
    }
    if (mode === 'auto') {
        if (entryPoint.status === 'pass') {
            return { name: 'Server Mode', status: 'pass', message: 'auto → will use CLI entry point' };
        }
        if (mcpModule.status === 'pass') {
            return { name: 'Server Mode', status: 'pass', message: 'auto → will use python -m src.mcp.server' };
        }
        return {
            name: 'Server Mode',
            status: 'fail',
            message: 'Neither entry point nor module available.',
            fix: 'pip install the runtime .whl into the workspace Python environment.',
        };
    }

    return { name: 'Server Mode', status: 'pass', message: `serverMode="${mode}" — OK` };
}

function checkGovernanceContent(projectRoot: string): DiagnosticCheck {
    const hasDocs = existsSync(path.join(projectRoot, 'docs'));
    const hasPack = existsSync(path.join(projectRoot, '.doc-based-coding'))
        || existsSync(path.join(projectRoot, 'pack.yaml'))
        || existsSync(path.join(projectRoot, 'pack.json'));

    if (hasDocs || hasPack) {
        return {
            name: 'Governance Content',
            status: 'pass',
            message: `Found: ${[hasDocs && 'docs/', hasPack && 'pack config'].filter(Boolean).join(', ')}`,
        };
    }

    return {
        name: 'Governance Content',
        status: 'warn',
        message: 'No docs/ directory or pack configuration found.',
        fix: 'Create a docs/ directory with project documentation, or initialize a pack with "doc-based-coding init".',
    };
}

async function getPythonVersion(pythonPath: string): Promise<string | null> {
    try {
        const { stdout } = await execFileAsync(pythonPath, [
            '-c', 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")',
        ], { timeout: 5000 });
        const version = stdout.trim();
        const [major, minor] = version.split('.').map(Number);
        if (major >= 3 && minor >= 10) {
            return version;
        }
        return null;
    } catch {
        return null;
    }
}
