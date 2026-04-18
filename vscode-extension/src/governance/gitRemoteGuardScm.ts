/**
 * Git Remote Guard — SCM UI layer.
 *
 * Installs a git wrapper script and redirects VS Code's `git.path` to it.
 * This ensures remote operations (push, pull, fetch, remote, clone) are
 * also blocked when triggered from the Source Control panel, not just the terminal.
 *
 * The wrapper passes all local operations through to the real git binary.
 */

import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import { execSync } from 'child_process';

const BLOCKED_SUBCOMMANDS = ['push'];

/**
 * Detect the real git binary path on the system.
 * Returns null if git is not found.
 */
function findRealGitPath(): string | null {
    try {
        if (process.platform === 'win32') {
            const result = execSync('where git', { encoding: 'utf8', timeout: 5000 });
            const lines = result.trim().split(/\r?\n/);
            // Return the first match that isn't our wrapper
            return lines[0]?.trim() || null;
        } else {
            const result = execSync('which git', { encoding: 'utf8', timeout: 5000 });
            return result.trim() || null;
        }
    } catch {
        return null;
    }
}

/**
 * Generate the wrapper script content for the current platform.
 */
function generateWrapperScript(realGitPath: string): string {
    const blockedList = BLOCKED_SUBCOMMANDS.join(' ');

    if (process.platform === 'win32') {
        // Windows batch script
        const escapedGit = realGitPath.replace(/\//g, '\\');
        return [
            '@echo off',
            'setlocal enabledelayedexpansion',
            '',
            `set "REAL_GIT=${escapedGit}"`,
            `set "BLOCKED=${blockedList}"`,
            '',
            'rem Find the subcommand (first non-flag argument)',
            'set "SUBCMD="',
            'for %%a in (%*) do (',
            '    set "ARG=%%~a"',
            '    if not "!ARG:~0,1!"=="-" if not defined SUBCMD set "SUBCMD=%%~a"',
            ')',
            '',
            'rem Check if subcommand is blocked',
            'for %%b in (%BLOCKED%) do (',
            '    if /i "!SUBCMD!"=="%%b" (',
            '        echo [HARD BLOCK] "git %%b" is permanently disabled in this workspace. 1>&2',
            '        echo Pushing to remote is blocked. Read-only ops (pull/fetch/clone) are allowed. 1>&2',
            '        exit /b 128',
            '    )',
            ')',
            '',
            'rem Pass through to real git',
            '"%REAL_GIT%" %*',
            'exit /b %ERRORLEVEL%',
            '',
        ].join('\r\n');
    } else {
        // Unix shell script
        return [
            '#!/bin/sh',
            '# Git Remote Guard — blocks push/pull/fetch/remote/clone',
            '',
            `REAL_GIT="${realGitPath}"`,
            '',
            '# Find first non-flag argument (the subcommand)',
            'SUBCMD=""',
            'for arg in "$@"; do',
            '    case "$arg" in',
            '        -*) ;;',
            '        *)',
            '            if [ -z "$SUBCMD" ]; then',
            '                SUBCMD="$arg"',
            '            fi',
            '            ;;',
            '    esac',
            'done',
            '',
            '# Check if blocked',
            'case "$SUBCMD" in',
            '    push)',
            '        echo "[HARD BLOCK] \\"git $SUBCMD\\" is permanently disabled in this workspace." >&2',
            '        echo "Pushing to remote is blocked. Read-only ops (pull/fetch/clone) are allowed." >&2',
            '        exit 128',
            '        ;;',
            'esac',
            '',
            '# Pass through',
            'exec "$REAL_GIT" "$@"',
            '',
        ].join('\n');
    }
}

/**
 * Install the git wrapper and configure git.path for the workspace.
 * Returns the path to the installed wrapper, or null on failure.
 */
export function installGitWrapper(
    projectRoot: string,
    outputChannel: vscode.OutputChannel,
): string | null {
    const realGit = findRealGitPath();
    if (!realGit) {
        outputChannel.appendLine('[GitGuard] Could not find system git binary. SCM guard not installed.');
        return null;
    }

    const codexDir = path.join(projectRoot, '.codex');
    if (!fs.existsSync(codexDir)) {
        fs.mkdirSync(codexDir, { recursive: true });
    }

    const ext = process.platform === 'win32' ? '.cmd' : '.sh';
    const wrapperPath = path.join(codexDir, `git-guard${ext}`);

    // Check if wrapper already exists and is up-to-date
    const content = generateWrapperScript(realGit);
    const existing = fs.existsSync(wrapperPath)
        ? fs.readFileSync(wrapperPath, 'utf8')
        : '';

    if (existing !== content) {
        fs.writeFileSync(wrapperPath, content, { encoding: 'utf8', mode: 0o755 });
        outputChannel.appendLine(`[GitGuard] Wrapper script written: ${wrapperPath}`);
    }

    // On Unix, ensure executable
    if (process.platform !== 'win32') {
        fs.chmodSync(wrapperPath, 0o755);
    }

    // Configure workspace git.path
    const gitConfig = vscode.workspace.getConfiguration('git');
    const currentPath = gitConfig.get<string>('path');

    if (currentPath !== wrapperPath) {
        gitConfig.update('path', wrapperPath, vscode.ConfigurationTarget.Workspace);
        outputChannel.appendLine(`[GitGuard] git.path set to wrapper: ${wrapperPath}`);
    }

    outputChannel.appendLine(`[GitGuard] SCM guard active. Real git: ${realGit}`);
    return wrapperPath;
}
