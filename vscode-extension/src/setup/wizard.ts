/**
 * Setup wizard — guides the user through Python Runtime detection
 * and installation on first activation or manual trigger.
 */

import * as vscode from 'vscode';
import * as path from 'path';
import { existsSync, readdirSync } from 'fs';
import { detectPythonEnvironment, PythonDetectionResult } from './pythonDetector';
import { installFromReleaseZip, installFromWheelFiles } from './runtimeInstaller';

export interface SetupWizardOptions {
    projectRoot: string;
    outputChannel: vscode.OutputChannel;
    /** Called after successful setup to (re)start the MCP server. */
    onReady: (pythonPath: string) => Promise<void>;
}

/**
 * Run the setup wizard.
 *
 * Returns true if the environment is ready (either already configured
 * or freshly installed). Returns false if the user cancelled or setup
 * failed.
 */
export async function runSetupWizard(options: SetupWizardOptions): Promise<boolean> {
    const { projectRoot, outputChannel, onReady } = options;

    outputChannel.appendLine('[Wizard] Starting setup wizard...');

    let detection: PythonDetectionResult;
    try {
        // Step 1: Detect current environment
        detection = await detectPythonEnvironment(projectRoot, outputChannel);
    } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        outputChannel.appendLine(`[Wizard] Detection failed: ${msg}`);
        vscode.window.showErrorMessage(
            `Doc-Based Coding: Environment detection failed — ${msg}`,
        );
        return false;
    }

    outputChannel.appendLine(`[Wizard] Detection result: pythonFound=${detection.pythonFound}, runtimeInstalled=${detection.runtimeInstalled}, mcpServerAvailable=${detection.mcpServerAvailable}`);

    // Already ready — skip wizard UI, directly start server
    if (detection.pythonFound && detection.runtimeInstalled && detection.mcpServerAvailable) {
        outputChannel.appendLine(`[Wizard] Environment ready: ${detection.summary}`);
        try {
            await onReady(detection.pythonPath!);
        } catch (err) {
            const msg = err instanceof Error ? err.message : String(err);
            outputChannel.appendLine(`[Wizard] MCP start failed: ${msg}`);
            vscode.window.showErrorMessage(`Doc-Based Coding: MCP server failed to start — ${msg}`);
            return false;
        }
        return true;
    }

    // Step 2: Show status and ask what to do
    if (!detection.pythonFound) {
        return await handleNoPython(detection, outputChannel);
    }

    if (!detection.runtimeInstalled) {
        return await handleNoRuntime(detection, options);
    }

    // Runtime installed but MCP server not loadable
    const choice = await vscode.window.showWarningMessage(
        `Runtime v${detection.runtimeVersion} installed but MCP server not loadable. ` +
        'Ensure you opened the correct project folder.',
        { modal: true },
        'Open Output Log',
    );
    if (choice === 'Open Output Log') {
        outputChannel.show();
    }
    return false;
}

async function handleNoPython(
    detection: PythonDetectionResult,
    outputChannel: vscode.OutputChannel,
): Promise<boolean> {
    const choice = await vscode.window.showErrorMessage(
        detection.summary,
        { modal: true },
        'Open Python Download Page',
        'Configure Python Path',
    );

    if (choice === 'Open Python Download Page') {
        vscode.env.openExternal(vscode.Uri.parse('https://www.python.org/downloads/'));
    } else if (choice === 'Configure Python Path') {
        await vscode.commands.executeCommand(
            'workbench.action.openSettings',
            'docBasedCoding.pythonPath',
        );
    }

    return false;
}

async function handleNoRuntime(
    detection: PythonDetectionResult,
    options: SetupWizardOptions,
): Promise<boolean> {
    const { projectRoot, outputChannel, onReady } = options;
    const pythonPath = detection.pythonPath!;

    // Auto-detect release files in workspace
    const releaseDir = path.join(projectRoot, 'release');
    const localWheels = findLocalWheels(releaseDir);
    const localZip = findLocalZip(releaseDir);

    let choice: string | undefined;

    if (localWheels.length > 0) {
        // Found wheels in release/ — offer direct install
        const wheelNames = localWheels.map(w => path.basename(w)).join(', ');
        choice = await vscode.window.showWarningMessage(
            `Python ${detection.pythonVersion} found but runtime is not installed.\n` +
            `Detected local release packages: ${wheelNames}`,
            { modal: true },
            'Install from workspace release',
            'Browse for release.zip',
            'Configure Manually',
        );
    } else if (localZip) {
        choice = await vscode.window.showWarningMessage(
            `Python ${detection.pythonVersion} found but runtime is not installed.\n` +
            `Detected local release archive: ${path.basename(localZip)}`,
            { modal: true },
            'Install from workspace release',
            'Browse for release.zip',
            'Configure Manually',
        );
    } else {
        choice = await vscode.window.showWarningMessage(
            `Python ${detection.pythonVersion} found but doc-based-coding runtime is not installed. ` +
            'Install from a release.zip to get started.',
            { modal: true },
            'Browse for release.zip',
            'Configure Manually',
        );
    }

    if (choice === 'Configure Manually') {
        await vscode.commands.executeCommand(
            'workbench.action.openSettings',
            'docBasedCoding.pythonPath',
        );
        return false;
    }

    let result;

    if (choice === 'Install from workspace release') {
        if (localWheels.length > 0) {
            result = await installFromWheelFiles(pythonPath, localWheels, outputChannel);
        } else if (localZip) {
            result = await installFromReleaseZip(pythonPath, outputChannel, localZip);
        } else {
            return false;
        }
    } else if (choice === 'Browse for release.zip') {
        result = await installFromReleaseZip(pythonPath, outputChannel);
    } else {
        return false;
    }

    if (result.success) {
        // Save the python path to settings
        await vscode.workspace.getConfiguration('docBasedCoding').update(
            'pythonPath',
            pythonPath,
            vscode.ConfigurationTarget.Workspace,
        );

        vscode.window.showInformationMessage(
            `Runtime v${result.runtimeVersion} installed successfully! ` +
            `Installed: ${result.installedWheels.join(', ')}`,
        );

        await onReady(pythonPath);
        return true;
    } else {
        vscode.window.showErrorMessage(
            `Installation failed: ${result.error}`,
        );
        return false;
    }
}

/** Find .whl files in release directory. */
function findLocalWheels(releaseDir: string): string[] {
    if (!existsSync(releaseDir)) {
        return [];
    }
    try {
        return readdirSync(releaseDir)
            .filter(f => f.endsWith('.whl'))
            .map(f => path.join(releaseDir, f));
    } catch {
        return [];
    }
}

/** Find a release .zip in release directory. */
function findLocalZip(releaseDir: string): string | null {
    if (!existsSync(releaseDir)) {
        return null;
    }
    try {
        const zips = readdirSync(releaseDir).filter(f => f.endsWith('.zip'));
        return zips.length > 0 ? path.join(releaseDir, zips[0]) : null;
    } catch {
        return null;
    }
}
