/**
 * Doc-Based Coding VS Code Extension entry point.
 *
 * Architecture: MCP-first — this Extension acts as an MCP Client
 * connecting to the Python governance runtime via stdio.
 */

import * as vscode from 'vscode';
import * as path from 'path';
import { MCPClient } from './mcp/client';
import { ConstraintDashboardProvider } from './views/constraintDashboard';
import { PackExplorerProvider } from './views/packExplorer';
import { PassthroughInterceptor, PassthroughReviewPanel } from './governance/passthrough';
import { runSetupWizard } from './setup/wizard';

let mcpClient: MCPClient | undefined;
let constraintDashboard: ConstraintDashboardProvider | undefined;
let outputChannel: vscode.OutputChannel;

export async function activate(context: vscode.ExtensionContext): Promise<void> {
    outputChannel = vscode.window.createOutputChannel('Doc-Based Coding');
    outputChannel.appendLine('Doc-Based Coding extension activating...');

    // Resolve project root (first workspace folder)
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        outputChannel.appendLine('No workspace folder found. Extension inactive.');
        return;
    }

    const projectRoot = workspaceFolder.uri.fsPath;

    // Helper: create and start MCP client with given python path
    async function startMCPServer(pythonPath: string): Promise<void> {
        const config = vscode.workspace.getConfiguration('docBasedCoding');

        // Stop existing client if any
        if (mcpClient) {
            mcpClient.stop();
        }

        mcpClient = new MCPClient(
            {
                pythonPath,
                projectRoot,
                serverArgs: config.get<string[]>('serverArgs') ?? [],
            },
            outputChannel,
        );
        context.subscriptions.push(mcpClient);

        // Update dashboard with new client
        if (constraintDashboard) {
            constraintDashboard.updateClient(mcpClient);
        }

        await mcpClient.start();
        outputChannel.appendLine('[Extension] MCP server started.');
        await constraintDashboard?.refresh();
    }

    // Initialize governance layer (MVP: passthrough)
    const _interceptor = new PassthroughInterceptor();
    const _reviewPanel = new PassthroughReviewPanel();

    // Register Constraint Dashboard TreeView
    constraintDashboard = new ConstraintDashboardProvider();
    const treeView = vscode.window.createTreeView('constraintDashboard', {
        treeDataProvider: constraintDashboard,
        showCollapseAll: false,
    });
    context.subscriptions.push(treeView);

    // Register Pack Explorer TreeView (placeholder)
    const packExplorer = new PackExplorerProvider();
    const packTreeView = vscode.window.createTreeView('packExplorer', {
        treeDataProvider: packExplorer,
        showCollapseAll: false,
    });
    context.subscriptions.push(packTreeView);

    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('docBasedCoding.refreshConstraints', async () => {
            await constraintDashboard?.refresh();
        }),
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('docBasedCoding.startServer', async () => {
            try {
                const config = vscode.workspace.getConfiguration('docBasedCoding');
                const pythonPath = config.get<string>('pythonPath') || await resolvePythonPath(projectRoot);
                await startMCPServer(pythonPath);
                vscode.window.showInformationMessage('MCP server started.');
            } catch (err) {
                const msg = err instanceof Error ? err.message : String(err);
                vscode.window.showErrorMessage(`Failed to start MCP server: ${msg}`);
            }
        }),
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('docBasedCoding.stopServer', () => {
            mcpClient?.stop();
            vscode.window.showInformationMessage('MCP server stopped.');
        }),
    );

    // Register setup wizard command
    context.subscriptions.push(
        vscode.commands.registerCommand('docBasedCoding.setupWizard', async () => {
            await runSetupWizard({
                projectRoot,
                outputChannel,
                onReady: startMCPServer,
            });
        }),
    );

    // Run setup wizard on first activation or auto-start
    const config = vscode.workspace.getConfiguration('docBasedCoding');
    if (config.get<boolean>('autoStart')) {
        try {
            outputChannel.appendLine('[Extension] autoStart=true, running setup wizard...');
            const ready = await runSetupWizard({
                projectRoot,
                outputChannel,
                onReady: startMCPServer,
            });
            if (!ready) {
                outputChannel.appendLine('[Extension] Setup incomplete. Use "Doc-Based Coding: Setup Wizard" to configure.');
                vscode.window.showWarningMessage(
                    'Doc-Based Coding: Setup incomplete. Run "Doc-Based Coding: Setup Wizard" from the Command Palette.',
                    'Run Setup Wizard',
                ).then(choice => {
                    if (choice === 'Run Setup Wizard') {
                        vscode.commands.executeCommand('docBasedCoding.setupWizard');
                    }
                });
            }
        } catch (err) {
            const msg = err instanceof Error ? err.message : String(err);
            outputChannel.appendLine(`[Extension] autoStart failed: ${msg}`);
            vscode.window.showErrorMessage(
                `Doc-Based Coding: Failed to start — ${msg}`,
                'View Output',
            ).then(choice => {
                if (choice === 'View Output') {
                    outputChannel.show();
                }
            });
        }
    } else {
        outputChannel.appendLine('[Extension] autoStart=false, skipping auto-start.');
    }

    // Cleanup on dispose
    context.subscriptions.push(outputChannel);

    outputChannel.appendLine('Doc-Based Coding extension activated.');
}

export function deactivate(): void {
    mcpClient?.stop();
}

/**
 * Try to find a Python executable in the workspace.
 * Checks common virtual environment locations, then falls back to 'python'.
 */
async function resolvePythonPath(projectRoot: string): Promise<string> {
    const candidates = [
        path.join(projectRoot, '.venv', 'Scripts', 'python.exe'),
        path.join(projectRoot, '.venv', 'bin', 'python'),
        path.join(projectRoot, '.venv-release-test', 'Scripts', 'python.exe'),
        path.join(projectRoot, '.venv-release-test', 'bin', 'python'),
        path.join(projectRoot, 'venv', 'Scripts', 'python.exe'),
        path.join(projectRoot, 'venv', 'bin', 'python'),
    ];

    const { existsSync } = await import('fs');

    for (const candidate of candidates) {
        if (existsSync(candidate)) {
            return candidate;
        }
    }

    return 'python';
}
