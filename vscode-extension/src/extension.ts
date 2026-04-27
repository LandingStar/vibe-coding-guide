/**
 * Doc-Based Coding VS Code Extension entry point.
 *
 * Architecture: MCP-first — this Extension acts as an MCP Client
 * connecting to the Python governance runtime via stdio.
 */

import * as vscode from 'vscode';
import * as path from 'path';
import { existsSync, mkdirSync, writeFileSync, readFileSync } from 'fs';
import { MCPClient } from './mcp/client';
import { ConstraintDashboardProvider } from './views/constraintDashboard';
import { PackExplorerProvider } from './views/packExplorer';
import { DecisionLogViewerProvider } from './views/decisionLogViewer';
import { ConfigExplorerProvider } from './views/configExplorer';
import { ConfigPanelProvider } from './views/configPanel';
import { regenerateProgressGraphArtifacts } from './views/progressGraphArtifacts';
import { ProgressGraphPreviewPanel } from './views/progressGraphPreview';
import { GovernanceStatusBar } from './views/statusBar';
import { MCPGovernanceInterceptor, registerGovernanceListeners } from './governance/interceptor';
import { ReviewPanelProvider } from './governance/reviewPanel';
import { TerminalGovernanceMonitor } from './governance/terminalMonitor';
import { registerFileLifecycleListeners } from './governance/fileLifecycle';
import { createDefaultLLMProvider } from './llm/providerFactory';
import { generatePackDescription, generatePackRules } from './llm/packGenerator';
import { ManagedLLMProvider } from './llm/types';
import { registerChatParticipant } from './chat/participant';
import { runSetupWizard } from './setup/wizard';

let mcpClient: MCPClient | undefined;
let constraintDashboard: ConstraintDashboardProvider | undefined;
let packExplorerProvider: PackExplorerProvider | undefined;
let decisionLogProvider: DecisionLogViewerProvider | undefined;
let configExplorerProvider: ConfigExplorerProvider | undefined;
let configPanelProvider: ConfigPanelProvider | undefined;
let statusBar: GovernanceStatusBar | undefined;
let progressGraphPreviewPanel: ProgressGraphPreviewPanel | undefined;
let llmProvider: ManagedLLMProvider | undefined;
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

    function getLLMProvider(): ManagedLLMProvider {
        if (!llmProvider) {
            llmProvider = createDefaultLLMProvider();
        }
        return llmProvider;
    }

    function updateLLMProviderBindings(provider: ManagedLLMProvider): void {
        configPanelProvider?.updateLLMProvider(provider);
        interceptor.updateLLMProvider(provider);
    }

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
                serverMode: config.get<'auto' | 'module' | 'command'>('serverMode') ?? 'auto',
                serverArgs: config.get<string[]>('serverArgs') ?? [],
            },
            outputChannel,
        );
        context.subscriptions.push(mcpClient);

        // Update all providers with new client
        if (constraintDashboard) {
            constraintDashboard.updateClient(mcpClient);
        }
        if (packExplorerProvider) {
            packExplorerProvider.updateClient(mcpClient);
        }
        if (decisionLogProvider) {
            decisionLogProvider.updateClient(mcpClient);
        }
        if (configExplorerProvider) {
            configExplorerProvider.updateClient(mcpClient);
        }
        if (configPanelProvider) {
            configPanelProvider.updateClient(mcpClient);
        }
        interceptor.updateClient(mcpClient);

        await mcpClient.start();
        outputChannel.appendLine('[Extension] MCP server started.');
        outputChannel.appendLine(`[Extension] Python: ${pythonPath}`);
        outputChannel.appendLine(`[Extension] Server mode: ${config.get<string>('serverMode') ?? 'auto'}`);
        outputChannel.appendLine(`[Extension] Extension version: 0.1.3`);

        // Ensure .vscode/mcp.json exists for VS Code native MCP integration
        ensureMcpJson(projectRoot, pythonPath, config.get<string[]>('serverArgs') ?? []);

        // Refresh all views
        await constraintDashboard?.refresh();
        await packExplorerProvider?.refresh();
        await decisionLogProvider?.refresh();
        await configExplorerProvider?.refresh();
        await configPanelProvider?.refresh();

        // Update status bar from constraint result
        updateStatusBar();
    }

    // Initialize governance interceptor (real enforcement via MCP)
    const interceptor = new MCPGovernanceInterceptor(null, outputChannel);
    const reviewPanel = new ReviewPanelProvider(outputChannel);
    context.subscriptions.push(reviewPanel);
    registerGovernanceListeners(context, interceptor, outputChannel, reviewPanel);

    // Initialize terminal governance monitor (P6)
    const terminalConfig = vscode.workspace.getConfiguration('docBasedCoding.terminal');
    const killOnBlock = terminalConfig.get<boolean>('killOnBlock', false);
    const terminalMonitor = new TerminalGovernanceMonitor(interceptor, outputChannel, killOnBlock);
    terminalMonitor.activate(context);
    context.subscriptions.push(terminalMonitor);

    // Install git wrapper to block remote ops from SCM UI
    if (projectRoot) {
        const { installGitWrapper } = await import('./governance/gitRemoteGuardScm');
        installGitWrapper(projectRoot, outputChannel);
    }

    // Register file lifecycle governance (create/delete/rename)
    registerFileLifecycleListeners(context, interceptor, outputChannel);

    // Register Constraint Dashboard TreeView
    constraintDashboard = new ConstraintDashboardProvider();
    const treeView = vscode.window.createTreeView('constraintDashboard', {
        treeDataProvider: constraintDashboard,
        showCollapseAll: false,
    });
    context.subscriptions.push(treeView);

    // Register Pack Explorer TreeView
    packExplorerProvider = new PackExplorerProvider();
    const packTreeView = vscode.window.createTreeView('packExplorer', {
        treeDataProvider: packExplorerProvider,
        showCollapseAll: true,
    });
    context.subscriptions.push(packTreeView);

    // Register Decision Log Viewer TreeView
    decisionLogProvider = new DecisionLogViewerProvider();
    const decisionLogTreeView = vscode.window.createTreeView('decisionLogViewer', {
        treeDataProvider: decisionLogProvider,
        showCollapseAll: false,
    });
    context.subscriptions.push(decisionLogTreeView);

    // Register Config Explorer TreeView
    configExplorerProvider = new ConfigExplorerProvider();
    const configTreeView = vscode.window.createTreeView('configExplorer', {
        treeDataProvider: configExplorerProvider,
        showCollapseAll: true,
    });
    context.subscriptions.push(configTreeView);

    // Register Config Panel WebviewView
    configPanelProvider = new ConfigPanelProvider(outputChannel);
    updateLLMProviderBindings(getLLMProvider());
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(ConfigPanelProvider.viewType, configPanelProvider),
    );

    // Register Governance Status Bar
    statusBar = new GovernanceStatusBar();
    context.subscriptions.push(statusBar);

    progressGraphPreviewPanel = new ProgressGraphPreviewPanel(outputChannel, async (workspaceFolder) => {
        const workspaceRoot = workspaceFolder.uri.fsPath;
        const config = vscode.workspace.getConfiguration('docBasedCoding', workspaceFolder.uri);
        const pythonPath = config.get<string>('pythonPath') || await resolvePythonPath(workspaceRoot);
        await regenerateProgressGraphArtifacts({
            projectRoot: workspaceRoot,
            pythonPath,
            outputChannel,
        });
    });
    context.subscriptions.push(progressGraphPreviewPanel);

    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('docBasedCoding.refreshConstraints', async () => {
            await constraintDashboard?.refresh();
            updateStatusBar();
        }),
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('docBasedCoding.refreshPacks', async () => {
            await packExplorerProvider?.refresh();
        }),
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('docBasedCoding.refreshDecisionLogs', async () => {
            await decisionLogProvider?.refresh();
        }),
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('docBasedCoding.filterDecisionLogsMergeConflicts', async () => {
            if (decisionLogProvider) {
                decisionLogProvider.toggleMergeConflictFilter();
                vscode.window.showInformationMessage(
                    `Decision Logs: ${decisionLogProvider.mergeConflictFilterLabel}`,
                );
                await decisionLogProvider.refresh();
            }
        }),
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('docBasedCoding.refreshConfig', async () => {
            await configExplorerProvider?.refresh();
        }),
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('docBasedCoding.editConfigItem', async (item: unknown) => {
            if (configExplorerProvider && item && typeof item === 'object' && 'fieldKey' in item) {
                await configExplorerProvider.editField(item as Parameters<ConfigExplorerProvider['editField']>[0]);
            }
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
                const choice = await vscode.window.showErrorMessage(
                    `Failed to start MCP server: ${msg}`,
                    'Run Diagnostics',
                );
                if (choice === 'Run Diagnostics') {
                    vscode.commands.executeCommand('docBasedCoding.diagnose');
                }
            }
        }),
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('docBasedCoding.stopServer', () => {
            mcpClient?.stop();
            vscode.window.showInformationMessage('MCP server stopped.');
        }),
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('docBasedCoding.openProgressGraphPreview', async () => {
            const workspace = vscode.workspace.workspaceFolders?.[0];
            if (!workspace) {
                vscode.window.showWarningMessage('Open a workspace folder to load the progress graph preview.');
                return;
            }
            await progressGraphPreviewPanel?.open(workspace);
        }),
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('docBasedCoding.refreshProgressGraphPreview', async () => {
            const workspace = vscode.workspace.workspaceFolders?.[0];
            if (!workspace) {
                vscode.window.showWarningMessage('Open a workspace folder to refresh the progress graph preview.');
                return;
            }
            await progressGraphPreviewPanel?.refresh(workspace);
        }),
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('docBasedCoding.revealProgressGraphPreviewArtifact', async () => {
            const workspace = vscode.workspace.workspaceFolders?.[0];
            if (!workspace) {
                vscode.window.showWarningMessage('Open a workspace folder to reveal the progress graph preview artifact.');
                return;
            }
            await progressGraphPreviewPanel?.revealArtifact(workspace);
        }),
    );

    // Register diagnose command
    context.subscriptions.push(
        vscode.commands.registerCommand('docBasedCoding.diagnose', async () => {
            const { runDiagnostics } = await import('./setup/diagnostics');
            await runDiagnostics(projectRoot, outputChannel);
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

    // Register Copilot LLM intent classification command
    context.subscriptions.push(
        vscode.commands.registerCommand('docBasedCoding.classifyIntent', async () => {
            const provider = getLLMProvider();
            if (!provider.isAvailable) {
                const ok = await provider.initialize();
                if (!ok) {
                    vscode.window.showErrorMessage(
                        `${provider.displayName} model not available. Ensure it is installed and active.`,
                    );
                    return;
                }
                updateLLMProviderBindings(provider);
            }

            const input = await vscode.window.showInputBox({
                prompt: 'Enter text to classify intent',
                placeHolder: 'e.g. "refactor the payment module"',
            });
            if (!input) { return; }

            try {
                const result = await provider.classify(input, {
                    labels: ['implement', 'refactor', 'fix', 'document', 'test', 'explore', 'other'],
                });
                outputChannel.appendLine(`[LLM:${provider.name}] Intent: ${result.label} (${result.confidence})`);
                vscode.window.showInformationMessage(
                    `Intent: ${result.label} (confidence: ${(result.confidence * 100).toFixed(0)}%)`
                );
            } catch (err) {
                const msg = err instanceof Error ? err.message : String(err);
                vscode.window.showErrorMessage(`Classification failed: ${msg}`);
            }
        }),
    );

    // Register pack generation commands
    context.subscriptions.push(
        vscode.commands.registerCommand('docBasedCoding.generatePackDescription', async () => {
            await generatePackDescription(getLLMProvider(), outputChannel);
        }),
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('docBasedCoding.generatePackRules', async () => {
            await generatePackRules(getLLMProvider(), outputChannel);
        }),
    );

    // Open Review Panel command (informational — panel auto-opens on BLOCK)
    context.subscriptions.push(
        vscode.commands.registerCommand('docBasedCoding.openReviewPanel', () => {
            vscode.window.showInformationMessage(
                'The Governance Review Panel opens automatically when a save is blocked by governance policy.'
            );
        }),
    );

    // Select LLM Model command
    context.subscriptions.push(
        vscode.commands.registerCommand('docBasedCoding.selectModel', async () => {
            try {
                const provider = getLLMProvider();
                const families = await provider.listModelFamilies();
                if (!families.length) {
                    vscode.window.showWarningMessage(`No ${provider.displayName} models available.`);
                    return;
                }
                const currentFamily = provider.currentFamily ?? 'gpt-4o';
                const items = families.map((family) => ({
                    label: family,
                    description: `${provider.displayName} family`,
                    detail: family === currentFamily ? '$(check) Current' : undefined,
                }));
                const pick = await vscode.window.showQuickPick(items, {
                    placeHolder: `Current: ${currentFamily} — select a new model family`,
                    title: `Select ${provider.displayName} Model Family`,
                });
                if (!pick) { return; }
                await vscode.workspace.getConfiguration('docBasedCoding').update(
                    'llm.family', pick.label, vscode.ConfigurationTarget.Workspace,
                );
                // Re-init is handled by onDidChangeConfiguration below
            } catch (err) {
                const msg = err instanceof Error ? err.message : String(err);
                vscode.window.showErrorMessage(`Model selection failed: ${msg}`);
            }
        }),
    );

    // Initialize the default LLM provider (best-effort, don't block activation)
    const initialLLMProvider = getLLMProvider();
    initialLLMProvider.initialize().then((ok) => {
        if (ok) {
            outputChannel.appendLine(
                `[Extension] ${initialLLMProvider.displayName} model connected (family: ${initialLLMProvider.currentFamily}).`,
            );
            updateLLMProviderBindings(initialLLMProvider);
        } else {
            outputChannel.appendLine(
                `[Extension] ${initialLLMProvider.displayName} model not available (normal if the provider is not installed or authorized).`,
            );
        }
    });

    // Register Chat Participant (@governance in VS Code Chat)
    registerChatParticipant(context, () => mcpClient, outputChannel);

    // Re-initialize the active LLM provider when llm.family config changes
    context.subscriptions.push(
        vscode.workspace.onDidChangeConfiguration(async (e) => {
            if (e.affectsConfiguration('docBasedCoding.llm.family')) {
                const provider = getLLMProvider();
                const ok = await provider.initialize();
                if (ok) {
                    outputChannel.appendLine(`[Extension] LLM model switched to family: ${provider.currentFamily}`);
                    updateLLMProviderBindings(provider);
                } else {
                    outputChannel.appendLine(`[Extension] LLM model switch failed — family not available.`);
                    vscode.window.showWarningMessage(
                        `LLM model family "${vscode.workspace.getConfiguration('docBasedCoding').get('llm.family')}" not available. Reverting to previous model.`,
                    );
                }
            }
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
                'Run Diagnostics',
                'View Output',
            ).then(choice => {
                if (choice === 'Run Diagnostics') {
                    vscode.commands.executeCommand('docBasedCoding.diagnose');
                } else if (choice === 'View Output') {
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
    statusBar?.dispose();
}

/** Update status bar with latest constraint violation count. */
function updateStatusBar(): void {
    const count = constraintDashboard?.violationCount ?? null;
    statusBar?.update(count);
}

/**
 * Ensure .vscode/mcp.json contains a server entry for doc-based-coding,
 * so VS Code's native MCP integration can discover the server.
 */
function ensureMcpJson(projectRoot: string, pythonPath: string, serverArgs: string[]): void {
    const vscodeDir = path.join(projectRoot, '.vscode');
    const mcpJsonPath = path.join(vscodeDir, 'mcp.json');

    const serverEntry = {
        type: 'stdio' as const,
        command: pythonPath,
        args: ['-m', 'src.mcp.server', '--project', projectRoot, ...serverArgs],
    };

    try {
        let config: { servers?: Record<string, unknown> } = { servers: {} };

        if (existsSync(mcpJsonPath)) {
            const raw = readFileSync(mcpJsonPath, 'utf-8').replace(/^\uFEFF/, '');
            config = JSON.parse(raw);
            if (config.servers?.['doc-based-coding']) {
                // Already configured — don't overwrite user customizations
                return;
            }
        }

        if (!existsSync(vscodeDir)) {
            mkdirSync(vscodeDir, { recursive: true });
        }

        config.servers = config.servers ?? {};
        config.servers['doc-based-coding'] = serverEntry;

        writeFileSync(mcpJsonPath, JSON.stringify(config, null, 2) + '\n', 'utf-8');
        outputChannel.appendLine(`[Extension] Created/updated ${mcpJsonPath}`);
    } catch (err) {
        outputChannel.appendLine(`[Extension] Failed to write mcp.json: ${err}`);
    }
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
