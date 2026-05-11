/**
 * Runtime/package management helpers for installed-state extension actions.
 */

import * as vscode from 'vscode';
import * as path from 'path';
import { execFile } from 'child_process';
import { existsSync, readdirSync } from 'fs';
import { promisify } from 'util';
import { detectPythonEnvironment } from './pythonDetector';
import { installFromReleaseZip, installFromWheelFiles } from './runtimeInstaller';

const execFileAsync = promisify(execFile);

export interface RuntimePackageStatus {
    extensionVersion: string;
    pythonPath: string | null;
    pythonVersion: string | null;
    runtimeInstalled: boolean;
    runtimeVersion: string | null;
    instanceInstalled: boolean;
    instanceVersion: string | null;
    mcpServerRunning: boolean;
    autoStart: boolean;
    serverMode: string;
    releaseArtifacts: {
        wheelFiles: string[];
        zipFile: string | null;
        vsixFiles: string[];
    };
    summary: string;
}

export interface RuntimePackageActionResult {
    ok: boolean;
    message: string;
    runtimeVersion: string | null;
    instanceVersion: string | null;
}

interface LocalReleaseArtifacts {
    wheelPaths: string[];
    zipPath: string | null;
    vsixPaths: string[];
}

export async function getRuntimePackageStatus(options: {
    projectRoot: string;
    extensionVersion: string;
    mcpServerRunning: boolean;
    autoStart: boolean;
    serverMode: string;
    outputChannel: vscode.OutputChannel;
}): Promise<RuntimePackageStatus> {
    const detection = await detectPythonEnvironment(options.projectRoot, options.outputChannel);
    const artifacts = detectLocalReleaseArtifacts(options.projectRoot);

    let instanceVersion: string | null = null;
    if (detection.pythonFound && detection.pythonPath) {
        instanceVersion = await readInstalledVersion(detection.pythonPath, 'doc-loop-vibe-coding');
    }

    return {
        extensionVersion: options.extensionVersion,
        pythonPath: detection.pythonPath,
        pythonVersion: detection.pythonVersion,
        runtimeInstalled: detection.runtimeInstalled,
        runtimeVersion: detection.runtimeVersion,
        instanceInstalled: instanceVersion !== null,
        instanceVersion,
        mcpServerRunning: options.mcpServerRunning,
        autoStart: options.autoStart,
        serverMode: options.serverMode,
        releaseArtifacts: {
            wheelFiles: artifacts.wheelPaths.map((filePath) => path.basename(filePath)),
            zipFile: artifacts.zipPath ? path.basename(artifacts.zipPath) : null,
            vsixFiles: artifacts.vsixPaths.map((filePath) => path.basename(filePath)),
        },
        summary: detection.summary,
    };
}

export async function installRuntimePackagesFromWorkspaceRelease(
    projectRoot: string,
    pythonPath: string,
    outputChannel: vscode.OutputChannel,
): Promise<RuntimePackageActionResult> {
    const artifacts = detectLocalReleaseArtifacts(projectRoot);

    if (artifacts.wheelPaths.length === 0 && !artifacts.zipPath) {
        return {
            ok: false,
            message: 'Workspace release/ directory does not contain wheel files or a release zip.',
            runtimeVersion: null,
            instanceVersion: null,
        };
    }

    const installResult = artifacts.wheelPaths.length > 0
        ? await installFromWheelFiles(pythonPath, artifacts.wheelPaths, outputChannel, { forceReinstall: true })
        : await installFromReleaseZip(pythonPath, outputChannel, artifacts.zipPath ?? undefined, { forceReinstall: true });

    if (!installResult.success) {
        return {
            ok: false,
            message: installResult.error ?? 'Package installation failed.',
            runtimeVersion: null,
            instanceVersion: null,
        };
    }

    return {
        ok: true,
        message: 'Installed packages from the current workspace release batch.',
        runtimeVersion: await readInstalledVersion(pythonPath, 'doc-based-coding-runtime'),
        instanceVersion: await readInstalledVersion(pythonPath, 'doc-loop-vibe-coding'),
    };
}

export async function uninstallRuntimePackages(
    pythonPath: string,
    outputChannel: vscode.OutputChannel,
): Promise<RuntimePackageActionResult> {
    try {
        await vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title: 'Uninstalling doc-based-coding packages...',
                cancellable: false,
            },
            async (progress) => {
                progress.report({ message: 'Removing doc-loop-vibe-coding and doc-based-coding-runtime...' });
                const { stdout, stderr } = await execFileAsync(
                    pythonPath,
                    ['-m', 'pip', 'uninstall', '-y', 'doc-loop-vibe-coding', 'doc-based-coding-runtime'],
                    { timeout: 120000 },
                );
                if (stdout.trim()) {
                    outputChannel.appendLine(`[pip] ${stdout.trim()}`);
                }
                if (stderr.trim()) {
                    outputChannel.appendLine(`[pip stderr] ${stderr.trim()}`);
                }
            },
        );
    } catch (err) {
        return {
            ok: false,
            message: err instanceof Error ? err.message : String(err),
            runtimeVersion: null,
            instanceVersion: null,
        };
    }

    const runtimeVersion = await readInstalledVersion(pythonPath, 'doc-based-coding-runtime');
    const instanceVersion = await readInstalledVersion(pythonPath, 'doc-loop-vibe-coding');
    if (runtimeVersion || instanceVersion) {
        return {
            ok: false,
            message: 'Uninstall completed, but one or more packages still appear to be installed in the selected Python environment.',
            runtimeVersion,
            instanceVersion,
        };
    }

    return {
        ok: true,
        message: 'Removed doc-based-coding-runtime and doc-loop-vibe-coding from the selected Python environment.',
        runtimeVersion: null,
        instanceVersion: null,
    };
}

async function readInstalledVersion(pythonPath: string, distributionName: string): Promise<string | null> {
    try {
        const { stdout } = await execFileAsync(
            pythonPath,
            ['-c', `from importlib.metadata import version; print(version(${JSON.stringify(distributionName)}))`],
            { timeout: 10000 },
        );
        const version = stdout.trim();
        return version || null;
    } catch {
        return null;
    }
}

function detectLocalReleaseArtifacts(projectRoot: string): LocalReleaseArtifacts {
    const releaseDir = path.join(projectRoot, 'release');
    if (!existsSync(releaseDir)) {
        return { wheelPaths: [], zipPath: null, vsixPaths: [] };
    }

    const entries = readdirSync(releaseDir)
        .map((name) => path.join(releaseDir, name))
        .sort((left, right) => right.localeCompare(left));

    return {
        wheelPaths: entries.filter((entry) => entry.endsWith('.whl')),
        zipPath: entries.find((entry) => entry.endsWith('.zip')) ?? null,
        vsixPaths: entries.filter((entry) => entry.endsWith('.vsix')),
    };
}