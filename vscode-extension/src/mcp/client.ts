/**
 * MCP stdio client — spawns the Python MCP server and communicates
 * via JSON-RPC over stdio.
 */

import * as vscode from 'vscode';
import { ChildProcess, spawn } from 'child_process';
import { MCPToolCall, MCPToolResult } from './types';

export interface MCPClientOptions {
    pythonPath: string;
    projectRoot: string;
    serverArgs?: string[];
}

/**
 * Manages the lifecycle of the MCP server subprocess and provides
 * a typed interface for calling MCP tools.
 */
export class MCPClient implements vscode.Disposable {
    private _process: ChildProcess | null = null;
    private _buffer = '';
    private _requestId = 0;
    private readonly _pendingRequests = new Map<
        number,
        { resolve: (v: unknown) => void; reject: (e: Error) => void }
    >();
    private readonly _options: MCPClientOptions;
    private readonly _outputChannel: vscode.OutputChannel;

    constructor(options: MCPClientOptions, outputChannel: vscode.OutputChannel) {
        this._options = options;
        this._outputChannel = outputChannel;
    }

    /** Start the MCP server subprocess. */
    async start(): Promise<void> {
        if (this._process) {
            return;
        }

        const args = [
            '-m', 'src.mcp.server',
            '--project', this._options.projectRoot,
            ...(this._options.serverArgs ?? []),
        ];

        this._outputChannel.appendLine(
            `[MCP] Starting server: ${this._options.pythonPath} ${args.join(' ')}`
        );

        this._process = spawn(this._options.pythonPath, args, {
            cwd: this._options.projectRoot,
            stdio: ['pipe', 'pipe', 'pipe'],
            env: { ...process.env },
        });

        this._process.stdout?.on('data', (data: Buffer) => {
            this._onData(data.toString('utf-8'));
        });

        this._process.stderr?.on('data', (data: Buffer) => {
            this._outputChannel.appendLine(`[MCP stderr] ${data.toString('utf-8').trim()}`);
        });

        this._process.on('exit', (code) => {
            this._outputChannel.appendLine(`[MCP] Server exited with code ${code}`);
            this._process = null;
            // Reject any pending requests
            for (const [, pending] of this._pendingRequests) {
                pending.reject(new Error(`MCP server exited with code ${code}`));
            }
            this._pendingRequests.clear();
        });

        // Wait for server to be ready (initialize handshake)
        await this._initialize();
    }

    /** Stop the MCP server. */
    stop(): void {
        if (this._process) {
            this._process.kill();
            this._process = null;
        }
    }

    /** Check if server is running. */
    get isRunning(): boolean {
        return this._process !== null;
    }

    /** Call an MCP tool by name. */
    async callTool(name: string, args: Record<string, unknown> = {}): Promise<unknown> {
        const call: MCPToolCall = { name, arguments: args };
        const result = await this._sendRequest('tools/call', call);
        const toolResult = result as MCPToolResult;

        if (toolResult.isError) {
            const text = toolResult.content?.map(c => c.text).join('\n') ?? 'Unknown error';
            throw new Error(`MCP tool '${name}' failed: ${text}`);
        }

        // Parse JSON from the first text content block
        const text = toolResult.content?.[0]?.text ?? '{}';
        try {
            return JSON.parse(text);
        } catch {
            return text;
        }
    }

    /** List available tools from the server. */
    async listTools(): Promise<Array<{ name: string; description: string }>> {
        const result = await this._sendRequest('tools/list', {});
        const resp = result as { tools: Array<{ name: string; description: string }> };
        return resp.tools ?? [];
    }

    dispose(): void {
        this.stop();
    }

    // ── Private ────────────────────────────────────────────────────

    private async _initialize(): Promise<void> {
        const result = await this._sendRequest('initialize', {
            protocolVersion: '2024-11-05',
            capabilities: {},
            clientInfo: {
                name: 'doc-based-coding-vscode',
                version: '0.1.0',
            },
        });
        this._outputChannel.appendLine(`[MCP] Initialized: ${JSON.stringify(result)}`);

        // Send initialized notification
        this._sendNotification('notifications/initialized', {});
    }

    private _sendRequest(method: string, params: unknown): Promise<unknown> {
        return new Promise((resolve, reject) => {
            if (!this._process?.stdin) {
                reject(new Error('MCP server not running'));
                return;
            }

            const id = ++this._requestId;
            this._pendingRequests.set(id, { resolve, reject });

            const message = JSON.stringify({
                jsonrpc: '2.0',
                id,
                method,
                params,
            });

            this._process.stdin.write(message + '\n');
        });
    }

    private _sendNotification(method: string, params: unknown): void {
        if (!this._process?.stdin) {
            return;
        }

        const message = JSON.stringify({
            jsonrpc: '2.0',
            method,
            params,
        });

        this._process.stdin.write(message + '\n');
    }

    private _onData(data: string): void {
        this._buffer += data;

        // Process complete lines
        let newlineIndex: number;
        while ((newlineIndex = this._buffer.indexOf('\n')) !== -1) {
            const line = this._buffer.substring(0, newlineIndex).trim();
            this._buffer = this._buffer.substring(newlineIndex + 1);

            if (!line) {
                continue;
            }

            try {
                const message = JSON.parse(line);
                if ('id' in message && this._pendingRequests.has(message.id)) {
                    const pending = this._pendingRequests.get(message.id)!;
                    this._pendingRequests.delete(message.id);

                    if ('error' in message) {
                        pending.reject(new Error(
                            message.error?.message ?? 'Unknown MCP error'
                        ));
                    } else {
                        pending.resolve(message.result);
                    }
                }
            } catch {
                this._outputChannel.appendLine(`[MCP] Parse error: ${line}`);
            }
        }
    }
}
