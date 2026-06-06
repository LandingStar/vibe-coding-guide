import * as vscode from 'vscode';
import { ManagedLLMProvider } from '../llm/types';
import { runAiChatToolLoop, type AiChatConversationMessage } from './aiChatToolLoop';
import { AiChatToolExecutor } from './aiChatTools';
import type { AiChatToolName } from './aiChatActionProtocol';

type AiChatToolResultListener = (tool: AiChatToolName, ok: boolean) => void | Promise<void>;

export class AiChatViewProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'aiChatView';

    private _view: vscode.WebviewView | undefined;
    private _provider: ManagedLLMProvider | null;
  private _messages: AiChatConversationMessage[] = [];
  private readonly _toolExecutor = new AiChatToolExecutor();

    constructor(
        private readonly _outputChannel: vscode.OutputChannel,
        llmProvider?: ManagedLLMProvider,
        private readonly _onToolResult?: AiChatToolResultListener,
    ) {
        this._provider = llmProvider ?? null;
    }

    updateLLMProvider(provider: ManagedLLMProvider): void {
        this._provider = provider;
        void this._sendStatus();
    }

    resolveWebviewView(
        webviewView: vscode.WebviewView,
        _context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ): void {
        this._view = webviewView;
        webviewView.webview.options = { enableScripts: true };
        webviewView.webview.onDidReceiveMessage(async (message: { command: string; prompt?: string }) => {
            if (message.command === 'ready') {
                await this._sendStatus();
                this._sendMessages();
                return;
            }

          if (message.command === 'selectModel') {
            await vscode.commands.executeCommand('docBasedCoding.selectModel');
            return;
          }

          if (message.command === 'selectProvider') {
            await vscode.commands.executeCommand('docBasedCoding.selectLLMProvider');
            return;
          }

          if (message.command === 'configureExternalApiBaseUrl') {
            await vscode.commands.executeCommand('docBasedCoding.configureExternalApiBaseUrl');
            return;
          }

          if (message.command === 'configureExternalApiKey') {
            await vscode.commands.executeCommand('docBasedCoding.configureExternalApiKey');
            return;
          }

            if (message.command === 'send' && typeof message.prompt === 'string') {
                await this._handleSend(message.prompt);
            }
        });
        this._updateHtml();
    }

    private async _handleSend(prompt: string): Promise<void> {
        const trimmed = prompt.trim();
        if (!trimmed || !this._view) {
            return;
        }

        const provider = this._provider;
        if (!provider) {
            this._view.webview.postMessage({ command: 'error', message: 'LLM provider is not ready yet.' });
            return;
        }

        const historyBeforeTurn = this._messages.slice(-8);
        this._messages.push({ role: 'user', content: trimmed });
        this._sendMessages();
        this._view.webview.postMessage({ command: 'busy', busy: true });

        try {
            if (!provider.isAvailable) {
                const ok = await provider.initialize();
                if (!ok) {
                    throw new Error(`Provider ${provider.displayName} is not available. Check API key or provider authorization.`);
                }
            }

          const reply = await runAiChatToolLoop({
          provider,
          history: historyBeforeTurn,
          currentPrompt: trimmed,
          executor: this._toolExecutor,
          onToolMessage: (message) => {
            this._messages.push({ role: 'tool', content: message });
            this._sendMessages();
          },
          onToolResult: this._onToolResult,
          });
          this._messages.push({ role: 'assistant', content: reply.trim() || 'No response returned.' });
            this._sendMessages();
        } catch (err) {
            const msg = err instanceof Error ? err.message : String(err);
          this._messages.push({ role: 'assistant', content: `Error: ${msg}` });
            this._sendMessages();
            this._outputChannel.appendLine(`[AI Chat] Request failed: ${msg}`);
        } finally {
            this._view.webview.postMessage({ command: 'busy', busy: false });
            await this._sendStatus();
        }
    }

    private async _sendStatus(): Promise<void> {
        if (!this._view) {
            return;
        }

      const config = vscode.workspace.getConfiguration('docBasedCoding');
      const configuredProvider = config.get<string>('llm.provider') ?? 'copilot';
      const configuredModel = configuredProvider === 'openai-compatible'
        ? (config.get<string>('llm.openaiCompatible.model') ?? 'gpt-4o-mini')
        : (config.get<string>('llm.family') ?? 'gpt-4o');
        const provider = this._provider;
      let status = `已配置 ${this._providerLabel(configuredProvider)} · ${configuredModel}`;

      if (!provider) {
        status += ' · provider 未就绪';
      } else if (provider.name !== configuredProvider) {
        status += ` · 当前实例 ${provider.displayName} · ${provider.currentFamily}`;
      } else {
        status = `${provider.displayName} · ${provider.currentFamily}${provider.isAvailable ? '' : ' · 未连接'}`;
      }

        this._view.webview.postMessage({ command: 'status', status });
    }

    private _providerLabel(providerName: string): string {
      if (providerName === 'openai-compatible') {
        return 'OpenAI-Compatible API';
      }
      if (providerName === 'copilot') {
        return 'GitHub Copilot';
      }
      return providerName;
    }

    private _sendMessages(): void {
        this._view?.webview.postMessage({ command: 'messages', messages: this._messages });
    }

    private _updateHtml(): void {
        if (!this._view) {
            return;
        }

        const nonce = getNonce();
        this._view.webview.html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'nonce-${nonce}'; script-src 'nonce-${nonce}';">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style nonce="${nonce}">
    body {
      margin: 0;
      padding: 0;
      font-family: var(--vscode-font-family);
      color: var(--vscode-foreground);
      background: var(--vscode-sideBar-background);
    }
    .shell {
      display: grid;
      grid-template-rows: auto 1fr auto;
      height: 100vh;
    }
    .header {
      padding: 10px 12px 8px;
      border-bottom: 1px solid var(--vscode-panel-border);
      background:
        linear-gradient(160deg, rgba(60, 117, 183, 0.12), transparent 58%),
        linear-gradient(12deg, rgba(96, 182, 132, 0.1), transparent 48%);
    }
    .title {
      font-size: 12px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--vscode-descriptionForeground);
    }
    .header-row {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 10px;
      margin-bottom: 6px;
    }
    .header-actions {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
    .header-button {
      padding: 5px 10px;
      font-size: 11px;
    }
    .status {
      font-size: 12px;
      color: var(--vscode-foreground);
    }
    .messages {
      overflow-y: auto;
      padding: 12px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .empty {
      color: var(--vscode-descriptionForeground);
      font-size: 12px;
      line-height: 1.5;
      padding: 8px 2px;
    }
    .bubble {
      border: 1px solid var(--vscode-panel-border);
      border-radius: 12px;
      padding: 10px 12px;
      white-space: pre-wrap;
      line-height: 1.55;
      font-size: 12px;
      word-break: break-word;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
    }
    .bubble.user {
      align-self: flex-end;
      background: linear-gradient(160deg, rgba(79, 153, 237, 0.18), rgba(79, 153, 237, 0.08));
      max-width: 88%;
    }
    .bubble.assistant {
      align-self: stretch;
      background: linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.01));
    }
    .bubble.tool {
      align-self: stretch;
      background: rgba(127, 127, 127, 0.08);
      border-style: dashed;
      color: var(--vscode-descriptionForeground);
      font-size: 11px;
    }
    .composer {
      border-top: 1px solid var(--vscode-panel-border);
      padding: 10px 12px 12px;
      display: grid;
      gap: 8px;
      background: rgba(0, 0, 0, 0.04);
    }
    textarea {
      width: 100%;
      min-height: 84px;
      resize: vertical;
      box-sizing: border-box;
      border-radius: 10px;
      border: 1px solid var(--vscode-input-border);
      background: var(--vscode-input-background);
      color: var(--vscode-input-foreground);
      padding: 10px 12px;
      font: inherit;
      line-height: 1.45;
    }
    textarea:focus {
      outline: 1px solid var(--vscode-focusBorder);
      border-color: var(--vscode-focusBorder);
    }
    .actions {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
    }
    .hint {
      font-size: 11px;
      color: var(--vscode-descriptionForeground);
    }
    button {
      border: none;
      border-radius: 999px;
      padding: 7px 14px;
      background: var(--vscode-button-background);
      color: var(--vscode-button-foreground);
      cursor: pointer;
      font: inherit;
    }
    button:hover {
      background: var(--vscode-button-hoverBackground);
    }
    button:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
  </style>
</head>
<body>
  <div class="shell">
    <div class="header">
      <div class="header-row">
        <div class="title">AI Chat</div>
        <div class="header-actions">
          <button id="selectProvider" class="header-button">切换 Provider</button>
          <button id="selectModel" class="header-button">选择模型</button>
          <button id="configureBaseUrl" class="header-button">配置 Base URL</button>
          <button id="configureApiKey" class="header-button">配置 API Key</button>
        </div>
      </div>
      <div id="status" class="status">Loading provider...</div>
    </div>
    <div id="messages" class="messages">
      <div class="empty">这里是插件自带的聊天框起点。当前第一刀已经支持只读工具循环，所以它可以看目录、读文件、搜文本和读诊断，但还不会直接改文件或跑命令。</div>
    </div>
    <div class="composer">
      <textarea id="prompt" placeholder="输入你的问题或任务，例如：请读取 README 并总结当前扩展结构。"></textarea>
      <div class="actions">
        <div class="hint">Enter 发送，Shift+Enter 换行</div>
        <button id="send">发送</button>
      </div>
    </div>
  </div>
  <script nonce="${nonce}">
    const vscode = acquireVsCodeApi();
    const promptEl = document.getElementById('prompt');
    const sendEl = document.getElementById('send');
    const selectProviderEl = document.getElementById('selectProvider');
    const selectModelEl = document.getElementById('selectModel');
    const configureBaseUrlEl = document.getElementById('configureBaseUrl');
    const configureApiKeyEl = document.getElementById('configureApiKey');
    const messagesEl = document.getElementById('messages');
    const statusEl = document.getElementById('status');

    function escapeHtml(value) {
      return value
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/\"/g, '&quot;')
        .replace(/'/g, '&#39;');
    }

    function renderMessages(messages) {
      if (!Array.isArray(messages) || messages.length === 0) {
        messagesEl.innerHTML = '<div class="empty">先发一条消息，验证当前 provider 是否可用。</div>';
        return;
      }
      messagesEl.innerHTML = messages
        .map((message) => '<div class="bubble ' + escapeHtml(message.role) + '">' + escapeHtml(message.content) + '</div>')
        .join('');
      messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function setBusy(busy) {
      sendEl.disabled = busy;
      sendEl.textContent = busy ? '思考中...' : '发送';
      promptEl.disabled = busy;
    }

    function sendPrompt() {
      const prompt = promptEl.value.trim();
      if (!prompt) {
        return;
      }
      vscode.postMessage({ command: 'send', prompt });
      promptEl.value = '';
    }

    sendEl.addEventListener('click', sendPrompt);
    selectProviderEl.addEventListener('click', () => {
      vscode.postMessage({ command: 'selectProvider' });
    });
    selectModelEl.addEventListener('click', () => {
      vscode.postMessage({ command: 'selectModel' });
    });
    configureBaseUrlEl.addEventListener('click', () => {
      vscode.postMessage({ command: 'configureExternalApiBaseUrl' });
    });
    configureApiKeyEl.addEventListener('click', () => {
      vscode.postMessage({ command: 'configureExternalApiKey' });
    });
    promptEl.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendPrompt();
      }
    });

    window.addEventListener('message', (event) => {
      const message = event.data;
      if (message.command === 'messages') {
        renderMessages(message.messages);
      } else if (message.command === 'status') {
        statusEl.textContent = message.status;
      } else if (message.command === 'busy') {
        setBusy(Boolean(message.busy));
      } else if (message.command === 'error') {
        statusEl.textContent = message.message;
      }
    });

    vscode.postMessage({ command: 'ready' });
  </script>
</body>
</html>`;
    }
}

function getNonce(): string {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let index = 0; index < 32; index += 1) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
}
