/**
 * Runtime installer — extracts wheels from a release.zip and
 * installs them via pip into the target Python environment.
 */

import * as vscode from 'vscode';
import * as path from 'path';
import * as os from 'os';
import { execFile } from 'child_process';
import { promisify } from 'util';
import { existsSync, mkdirSync, rmSync, createReadStream, createWriteStream } from 'fs';
import { createInterface } from 'readline';

const execFileAsync = promisify(execFile);

export interface InstallResult {
    success: boolean;
    runtimeVersion: string | null;
    installedWheels: string[];
    error: string | null;
}

/**
 * Install runtime from a release.zip file.
 *
 * Flow: pick zip → extract to temp → pip install wheels → verify → cleanup.
 */
export async function installFromReleaseZip(
    pythonPath: string,
    outputChannel: vscode.OutputChannel,
    preselectedZipPath?: string,
): Promise<InstallResult> {
    const result: InstallResult = {
        success: false,
        runtimeVersion: null,
        installedWheels: [],
        error: null,
    };

    let zipPath: string;

    if (preselectedZipPath) {
        zipPath = preselectedZipPath;
        outputChannel.appendLine(`[Installer] Using pre-detected zip: ${zipPath}`);
    } else {
        // Ask user to select release.zip
        const zipUris = await vscode.window.showOpenDialog({
            canSelectFiles: true,
            canSelectFolders: false,
            canSelectMany: false,
            filters: { 'Release Archive': ['zip'] },
            title: 'Select doc-based-coding release.zip',
        });

        if (!zipUris || zipUris.length === 0) {
            result.error = 'No file selected.';
            return result;
        }

        zipPath = zipUris[0].fsPath;
    }

    outputChannel.appendLine(`[Installer] Selected: ${zipPath}`);

    // 2. Extract zip to temp directory
    const tempDir = path.join(os.tmpdir(), `dbc-install-${Date.now()}`);
    mkdirSync(tempDir, { recursive: true });

    try {
        await vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title: 'Installing doc-based-coding runtime...',
                cancellable: false,
            },
            async (progress) => {
                // Extract
                progress.report({ message: 'Extracting release archive...' });
                await extractZip(zipPath, tempDir, pythonPath);
                outputChannel.appendLine(`[Installer] Extracted to ${tempDir}`);

                // Find wheels
                const { readdirSync } = await import('fs');
                const files = readdirSync(tempDir);
                const wheels = files.filter(f => f.endsWith('.whl'));

                if (wheels.length === 0) {
                    throw new Error('No .whl files found in the release archive.');
                }

                // Sort: runtime wheel first, then instance
                wheels.sort((a, b) => {
                    if (a.includes('runtime')) { return -1; }
                    if (b.includes('runtime')) { return 1; }
                    return 0;
                });

                outputChannel.appendLine(`[Installer] Wheels found: ${wheels.join(', ')}`);

                // Install each wheel
                for (const wheel of wheels) {
                    progress.report({ message: `Installing ${wheel}...` });
                    const wheelPath = path.join(tempDir, wheel);
                    await pipInstall(pythonPath, wheelPath, outputChannel);
                    result.installedWheels.push(wheel);
                }

                // Verify installation
                progress.report({ message: 'Verifying installation...' });
                try {
                    const { stdout } = await execFileAsync(pythonPath, [
                        '-c', 'from importlib.metadata import version; print(version("doc-based-coding-runtime"))',
                    ], { timeout: 10000 });
                    result.runtimeVersion = stdout.trim();
                    result.success = true;
                    outputChannel.appendLine(`[Installer] Verified: runtime v${result.runtimeVersion}`);
                } catch (err) {
                    throw new Error('Installation completed but runtime package verification failed.');
                }
            },
        );
    } catch (err) {
        result.error = err instanceof Error ? err.message : String(err);
        outputChannel.appendLine(`[Installer] Error: ${result.error}`);
    } finally {
        // Cleanup temp directory
        try {
            rmSync(tempDir, { recursive: true, force: true });
        } catch {
            // Best effort cleanup
        }
    }

    return result;
}

/**
 * Extract a zip file using Python's zipfile module.
 * We use Python because Node.js doesn't have built-in zip support
 * and we want to avoid adding a native dependency.
 */
async function extractZip(
    zipPath: string,
    destDir: string,
    pythonPath: string,
): Promise<void> {
    const script = `
import zipfile, sys
with zipfile.ZipFile(sys.argv[1]) as z:
    z.extractall(sys.argv[2])
print("ok")
`;
    const { stdout, stderr } = await execFileAsync(
        pythonPath,
        ['-c', script, zipPath, destDir],
        { timeout: 30000 },
    );
    if (!stdout.includes('ok')) {
        throw new Error(`Zip extraction failed: ${stderr}`);
    }
}

/**
 * Install a wheel via pip.
 */
async function pipInstall(
    pythonPath: string,
    wheelPath: string,
    outputChannel: vscode.OutputChannel,
): Promise<void> {
    const { stdout, stderr } = await execFileAsync(
        pythonPath,
        ['-m', 'pip', 'install', '--force-reinstall', wheelPath],
        { timeout: 120000 },
    );
    outputChannel.appendLine(`[pip] ${stdout.trim()}`);
    if (stderr.trim()) {
        outputChannel.appendLine(`[pip stderr] ${stderr.trim()}`);
    }
}

/**
 * Install runtime from pre-detected .whl files (e.g. from workspace release/ directory).
 */
export async function installFromWheelFiles(
    pythonPath: string,
    wheelPaths: string[],
    outputChannel: vscode.OutputChannel,
): Promise<InstallResult> {
    const result: InstallResult = {
        success: false,
        runtimeVersion: null,
        installedWheels: [],
        error: null,
    };

    try {
        await vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title: 'Installing doc-based-coding runtime...',
                cancellable: false,
            },
            async (progress) => {
                // Sort: runtime wheel first
                const sorted = [...wheelPaths].sort((a, b) => {
                    if (a.includes('runtime')) { return -1; }
                    if (b.includes('runtime')) { return 1; }
                    return 0;
                });

                for (const wheelPath of sorted) {
                    const name = wheelPath.split(/[\\/]/).pop() ?? wheelPath;
                    progress.report({ message: `Installing ${name}...` });
                    await pipInstall(pythonPath, wheelPath, outputChannel);
                    result.installedWheels.push(name);
                }

                // Verify
                progress.report({ message: 'Verifying installation...' });
                const { stdout } = await execFileAsync(pythonPath, [
                    '-c', 'from importlib.metadata import version; print(version("doc-based-coding-runtime"))',
                ], { timeout: 10000 });
                result.runtimeVersion = stdout.trim();
                result.success = true;
                outputChannel.appendLine(`[Installer] Verified: runtime v${result.runtimeVersion}`);
            },
        );
    } catch (err) {
        result.error = err instanceof Error ? err.message : String(err);
        outputChannel.appendLine(`[Installer] Error: ${result.error}`);
    }

    return result;
}
