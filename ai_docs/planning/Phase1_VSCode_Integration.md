# Phase 1: VSCode Integration Planning
## Mobius Context Engineering Platform

### Document Version: 1.0
### Date: 2025-01-07
### Component: VSCode Extension MVP

---

## Executive Summary

This document outlines the VSCode integration strategy for Phase 1 of the Mobius platform. The extension provides context-aware code completion, intelligent suggestions, and seamless integration with the backend context engine, delivering immediate value to developers.

### Key Features
1. Language Server Protocol (LSP) client implementation
2. Context-aware code completion
3. Real-time file indexing
4. Backend communication via WebSocket
5. Intuitive UI integration

---

## 1. Extension Architecture

### 1.1 Project Structure

```
mobius-vscode/
├── src/
│   ├── extension.ts           # Main entry point
│   ├── activation/
│   │   ├── activator.ts       # Activation logic
│   │   └── commands.ts        # Command registration
│   ├── client/
│   │   ├── languageClient.ts  # LSP client
│   │   ├── connection.ts      # WebSocket connection
│   │   └── authentication.ts  # Auth handling
│   ├── providers/
│   │   ├── completionProvider.ts
│   │   ├── hoverProvider.ts
│   │   └── definitionProvider.ts
│   ├── ui/
│   │   ├── statusBar.ts       # Status bar management
│   │   └── notifications.ts   # User notifications
│   ├── services/
│   │   ├── contextService.ts  # Context management
│   │   ├── cacheService.ts    # Local caching
│   │   └── telemetryService.ts
│   └── utils/
│       ├── config.ts          # Configuration
│       └── logger.ts          # Logging utilities
├── package.json               # Extension manifest
├── tsconfig.json              # TypeScript config
├── webpack.config.js          # Bundling config
└── README.md                  # Documentation
```

### 1.2 Extension Manifest

```json
// package.json
{
  "name": "mobius-context-engine",
  "displayName": "Mobius Context Engine",
  "description": "AI-powered context-aware coding assistant",
  "version": "0.1.0",
  "publisher": "mobius",
  "engines": {
    "vscode": "^1.85.0"
  },
  "categories": ["Programming Languages", "Other"],
  "keywords": ["ai", "context", "completion", "assistant"],
  "activationEvents": [
    "onLanguage:python",
    "onLanguage:javascript",
    "onLanguage:typescript",
    "onCommand:mobius.connect",
    "workspaceContains:**/*.py",
    "workspaceContains:**/*.js",
    "workspaceContains:**/*.ts"
  ],
  "main": "./dist/extension.js",
  "contributes": {
    "commands": [
      {
        "command": "mobius.connect",
        "title": "Mobius: Connect to Context Engine"
      },
      {
        "command": "mobius.disconnect",
        "title": "Mobius: Disconnect"
      },
      {
        "command": "mobius.indexCurrentFile",
        "title": "Mobius: Index Current File"
      },
      {
        "command": "mobius.showContext",
        "title": "Mobius: Show Current Context"
      },
      {
        "command": "mobius.refreshIndex",
        "title": "Mobius: Refresh Project Index"
      }
    ],
    "configuration": {
      "title": "Mobius Context Engine",
      "properties": {
        "mobius.serverUrl": {
          "type": "string",
          "default": "http://localhost:8000",
          "description": "Mobius server URL"
        },
        "mobius.apiKey": {
          "type": "string",
          "default": "",
          "description": "API key for authentication"
        },
        "mobius.enableTelemetry": {
          "type": "boolean",
          "default": true,
          "description": "Enable telemetry"
        },
        "mobius.contextWindowSize": {
          "type": "number",
          "default": 4096,
          "description": "Maximum context window size"
        },
        "mobius.autoIndexing": {
          "type": "boolean",
          "default": true,
          "description": "Automatically index files on save"
        }
      }
    },
    "menus": {
      "editor/context": [
        {
          "command": "mobius.indexCurrentFile",
          "group": "mobius"
        }
      ]
    }
  },
  "scripts": {
    "vscode:prepublish": "npm run compile",
    "compile": "webpack --mode production",
    "watch": "webpack --mode development --watch",
    "test": "jest",
    "lint": "eslint src --ext ts"
  },
  "devDependencies": {
    "@types/vscode": "^1.85.0",
    "@types/node": "^20.x",
    "@typescript-eslint/eslint-plugin": "^6.x",
    "@typescript-eslint/parser": "^6.x",
    "eslint": "^8.x",
    "jest": "^29.x",
    "ts-loader": "^9.x",
    "typescript": "^5.x",
    "webpack": "^5.x",
    "webpack-cli": "^5.x"
  },
  "dependencies": {
    "vscode-languageclient": "^9.0.0",
    "ws": "^8.16.0",
    "axios": "^1.6.0"
  }
}
```

### 1.3 Main Extension Entry Point

```typescript
// src/extension.ts
import * as vscode from 'vscode';
import { ExtensionActivator } from './activation/activator';
import { Logger } from './utils/logger';

let activator: ExtensionActivator;

export async function activate(context: vscode.ExtensionContext): Promise<void> {
    Logger.initialize(context);
    Logger.info('Mobius Context Engine extension activating...');
    
    try {
        activator = new ExtensionActivator(context);
        await activator.activate();
        
        Logger.info('Mobius Context Engine extension activated successfully');
    } catch (error) {
        Logger.error('Failed to activate extension', error);
        vscode.window.showErrorMessage(
            'Failed to activate Mobius Context Engine: ' + error.message
        );
    }
}

export async function deactivate(): Promise<void> {
    Logger.info('Mobius Context Engine extension deactivating...');
    
    if (activator) {
        await activator.deactivate();
    }
    
    Logger.info('Mobius Context Engine extension deactivated');
}
```

### 1.4 Activation Logic

```typescript
// src/activation/activator.ts
import * as vscode from 'vscode';
import { CommandManager } from './commands';
import { LanguageClientManager } from '../client/languageClient';
import { ConnectionManager } from '../client/connection';
import { StatusBarManager } from '../ui/statusBar';
import { ContextService } from '../services/contextService';
import { CompletionProvider } from '../providers/completionProvider';
import { HoverProvider } from '../providers/hoverProvider';
import { DefinitionProvider } from '../providers/definitionProvider';

export class ExtensionActivator {
    private commandManager: CommandManager;
    private languageClientManager: LanguageClientManager;
    private connectionManager: ConnectionManager;
    private statusBarManager: StatusBarManager;
    private contextService: ContextService;
    private disposables: vscode.Disposable[] = [];
    
    constructor(private context: vscode.ExtensionContext) {}
    
    async activate(): Promise<void> {
        // Initialize core services
        this.statusBarManager = new StatusBarManager();
        this.connectionManager = new ConnectionManager();
        this.contextService = new ContextService(this.connectionManager);
        this.languageClientManager = new LanguageClientManager(
            this.context,
            this.connectionManager
        );
        
        // Initialize command manager
        this.commandManager = new CommandManager(
            this.connectionManager,
            this.contextService,
            this.statusBarManager
        );
        
        // Register commands
        this.registerCommands();
        
        // Register providers
        this.registerProviders();
        
        // Auto-connect if configured
        const config = vscode.workspace.getConfiguration('mobius');
        if (config.get('apiKey')) {
            await this.connectionManager.connect();
        }
        
        // Watch for configuration changes
        this.context.subscriptions.push(
            vscode.workspace.onDidChangeConfiguration(
                this.onConfigurationChanged.bind(this)
            )
        );
    }
    
    private registerCommands(): void {
        const commands = this.commandManager.getCommands();
        
        for (const [commandId, handler] of commands) {
            const disposable = vscode.commands.registerCommand(
                commandId,
                handler
            );
            this.disposables.push(disposable);
            this.context.subscriptions.push(disposable);
        }
    }
    
    private registerProviders(): void {
        // Register completion provider
        const completionProvider = new CompletionProvider(this.contextService);
        this.disposables.push(
            vscode.languages.registerCompletionItemProvider(
                ['python', 'javascript', 'typescript'],
                completionProvider,
                '.',
                ' '
            )
        );
        
        // Register hover provider
        const hoverProvider = new HoverProvider(this.contextService);
        this.disposables.push(
            vscode.languages.registerHoverProvider(
                ['python', 'javascript', 'typescript'],
                hoverProvider
            )
        );
        
        // Register definition provider
        const definitionProvider = new DefinitionProvider(this.contextService);
        this.disposables.push(
            vscode.languages.registerDefinitionProvider(
                ['python', 'javascript', 'typescript'],
                definitionProvider
            )
        );
    }
    
    private async onConfigurationChanged(
        e: vscode.ConfigurationChangeEvent
    ): Promise<void> {
        if (e.affectsConfiguration('mobius')) {
            await this.connectionManager.reconnect();
        }
    }
    
    async deactivate(): Promise<void> {
        // Dispose all resources
        for (const disposable of this.disposables) {
            disposable.dispose();
        }
        
        // Disconnect from server
        await this.connectionManager.disconnect();
        
        // Stop language client
        await this.languageClientManager.stop();
    }
}
```

---

## 2. Language Server Protocol Implementation

### 2.1 LSP Client Setup

```typescript
// src/client/languageClient.ts
import * as vscode from 'vscode';
import {
    LanguageClient,
    LanguageClientOptions,
    ServerOptions,
    TransportKind,
    InitializeParams,
    InitializeResult
} from 'vscode-languageclient/node';
import { ConnectionManager } from './connection';

export class LanguageClientManager {
    private client: LanguageClient | null = null;
    
    constructor(
        private context: vscode.ExtensionContext,
        private connectionManager: ConnectionManager
    ) {}
    
    async start(): Promise<void> {
        const serverOptions: ServerOptions = {
            run: {
                command: 'mobius-lsp',
                transport: TransportKind.stdio
            },
            debug: {
                command: 'mobius-lsp',
                transport: TransportKind.stdio,
                options: { execArgv: ['--inspect=6009'] }
            }
        };
        
        const clientOptions: LanguageClientOptions = {
            documentSelector: [
                { scheme: 'file', language: 'python' },
                { scheme: 'file', language: 'javascript' },
                { scheme: 'file', language: 'typescript' }
            ],
            synchronize: {
                fileEvents: vscode.workspace.createFileSystemWatcher(
                    '**/*.{py,js,ts}'
                )
            },
            initializationOptions: {
                serverUrl: this.connectionManager.getServerUrl(),
                apiKey: this.connectionManager.getApiKey()
            },
            middleware: {
                provideCompletionItem: async (document, position, context, token, next) => {
                    // Add context information
                    const enhancedContext = {
                        ...context,
                        mobiusContext: await this.getEnhancedContext(document, position)
                    };
                    
                    return next(document, position, enhancedContext, token);
                }
            }
        };
        
        this.client = new LanguageClient(
            'mobiusLSP',
            'Mobius Language Server',
            serverOptions,
            clientOptions
        );
        
        // Start the client
        await this.client.start();
        
        // Register custom protocol extensions
        this.registerCustomProtocol();
    }
    
    private registerCustomProtocol(): void {
        if (!this.client) return;
        
        // Register custom request handlers
        this.client.onRequest('mobius/getContext', async (params) => {
            return this.connectionManager.getContext(params);
        });
        
        // Register custom notification handlers
        this.client.onNotification('mobius/contextUpdated', (params) => {
            vscode.window.showInformationMessage(
                `Context updated: ${params.filesIndexed} files indexed`
            );
        });
    }
    
    private async getEnhancedContext(
        document: vscode.TextDocument,
        position: vscode.Position
    ): Promise<any> {
        // Get surrounding context
        const range = new vscode.Range(
            position.translate(-10, 0),
            position.translate(10, 0)
        );
        
        const text = document.getText(range);
        
        return {
            documentUri: document.uri.toString(),
            position: position,
            surroundingText: text,
            language: document.languageId
        };
    }
    
    async stop(): Promise<void> {
        if (this.client) {
            await this.client.stop();
            this.client = null;
        }
    }
}
```

### 2.2 WebSocket Connection

```typescript
// src/client/connection.ts
import WebSocket from 'ws';
import * as vscode from 'vscode';
import { EventEmitter } from 'events';
import { Logger } from '../utils/logger';

interface ConnectionState {
    connected: boolean;
    connecting: boolean;
    error: Error | null;
}

export class ConnectionManager extends EventEmitter {
    private ws: WebSocket | null = null;
    private state: ConnectionState = {
        connected: false,
        connecting: false,
        error: null
    };
    private reconnectTimer: NodeJS.Timeout | null = null;
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private reconnectDelay = 1000;
    
    async connect(): Promise<void> {
        if (this.state.connected || this.state.connecting) {
            return;
        }
        
        this.state.connecting = true;
        this.emit('connecting');
        
        try {
            const config = vscode.workspace.getConfiguration('mobius');
            const serverUrl = config.get<string>('serverUrl', 'http://localhost:8000');
            const wsUrl = serverUrl.replace('http', 'ws') + '/ws';
            const apiKey = config.get<string>('apiKey', '');
            
            this.ws = new WebSocket(wsUrl, {
                headers: {
                    'Authorization': `Bearer ${apiKey}`
                }
            });
            
            this.setupEventHandlers();
            
            await this.waitForConnection();
            
        } catch (error) {
            this.state.connecting = false;
            this.state.error = error;
            this.emit('error', error);
            throw error;
        }
    }
    
    private setupEventHandlers(): void {
        if (!this.ws) return;
        
        this.ws.on('open', () => {
            Logger.info('WebSocket connected');
            this.state.connected = true;
            this.state.connecting = false;
            this.state.error = null;
            this.reconnectAttempts = 0;
            this.emit('connected');
            
            // Send initial handshake
            this.send({
                type: 'handshake',
                version: '1.0.0',
                capabilities: ['completion', 'hover', 'definition']
            });
        });
        
        this.ws.on('message', (data: WebSocket.RawData) => {
            try {
                const message = JSON.parse(data.toString());
                this.handleMessage(message);
            } catch (error) {
                Logger.error('Failed to parse message', error);
            }
        });
        
        this.ws.on('error', (error: Error) => {
            Logger.error('WebSocket error', error);
            this.state.error = error;
            this.emit('error', error);
        });
        
        this.ws.on('close', (code: number, reason: Buffer) => {
            Logger.info(`WebSocket closed: ${code} - ${reason.toString()}`);
            this.state.connected = false;
            this.state.connecting = false;
            this.emit('disconnected', { code, reason: reason.toString() });
            
            // Attempt to reconnect
            this.scheduleReconnect();
        });
    }
    
    private handleMessage(message: any): void {
        switch (message.type) {
            case 'context_update':
                this.emit('contextUpdate', message.data);
                break;
                
            case 'index_progress':
                this.emit('indexProgress', message.data);
                break;
                
            case 'error':
                this.emit('serverError', message.error);
                break;
                
            default:
                this.emit('message', message);
        }
    }
    
    private scheduleReconnect(): void {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            Logger.error('Max reconnection attempts reached');
            return;
        }
        
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
        this.reconnectAttempts++;
        
        Logger.info(`Scheduling reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);
        
        this.reconnectTimer = setTimeout(() => {
            this.connect().catch(error => {
                Logger.error('Reconnection failed', error);
            });
        }, delay);
    }
    
    send(message: any): void {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            throw new Error('WebSocket is not connected');
        }
        
        this.ws.send(JSON.stringify(message));
    }
    
    async request(method: string, params: any): Promise<any> {
        const id = Math.random().toString(36).substr(2, 9);
        
        return new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                this.removeListener(id, handler);
                reject(new Error('Request timeout'));
            }, 30000);
            
            const handler = (response: any) => {
                clearTimeout(timeout);
                
                if (response.error) {
                    reject(new Error(response.error.message));
                } else {
                    resolve(response.result);
                }
            };
            
            this.once(id, handler);
            
            this.send({
                id,
                method,
                params
            });
        });
    }
    
    private waitForConnection(): Promise<void> {
        return new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                reject(new Error('Connection timeout'));
            }, 10000);
            
            this.once('connected', () => {
                clearTimeout(timeout);
                resolve();
            });
            
            this.once('error', (error) => {
                clearTimeout(timeout);
                reject(error);
            });
        });
    }
    
    async disconnect(): Promise<void> {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
        
        if (this.ws) {
            this.ws.close(1000, 'Client disconnect');
            this.ws = null;
        }
        
        this.state.connected = false;
        this.state.connecting = false;
    }
    
    getServerUrl(): string {
        const config = vscode.workspace.getConfiguration('mobius');
        return config.get<string>('serverUrl', 'http://localhost:8000');
    }
    
    getApiKey(): string {
        const config = vscode.workspace.getConfiguration('mobius');
        return config.get<string>('apiKey', '');
    }
    
    isConnected(): boolean {
        return this.state.connected;
    }
}
```

---

## 3. Context-Aware Features

### 3.1 Completion Provider

```typescript
// src/providers/completionProvider.ts
import * as vscode from 'vscode';
import { ContextService } from '../services/contextService';
import { Logger } from '../utils/logger';

export class CompletionProvider implements vscode.CompletionItemProvider {
    constructor(private contextService: ContextService) {}
    
    async provideCompletionItems(
        document: vscode.TextDocument,
        position: vscode.Position,
        token: vscode.CancellationToken,
        context: vscode.CompletionContext
    ): Promise<vscode.CompletionItem[]> {
        try {
            // Get context for the current position
            const contextData = await this.contextService.getContextForPosition(
                document,
                position
            );
            
            // Request completions from backend
            const completions = await this.contextService.getCompletions({
                document: document.uri.toString(),
                position: {
                    line: position.line,
                    character: position.character
                },
                context: contextData,
                triggerKind: context.triggerKind,
                triggerCharacter: context.triggerCharacter
            });
            
            // Convert to VSCode completion items
            return completions.map(item => this.createCompletionItem(item));
            
        } catch (error) {
            Logger.error('Failed to provide completions', error);
            return [];
        }
    }
    
    private createCompletionItem(item: any): vscode.CompletionItem {
        const completion = new vscode.CompletionItem(
            item.label,
            this.getCompletionItemKind(item.kind)
        );
        
        completion.detail = item.detail;
        completion.documentation = new vscode.MarkdownString(item.documentation);
        completion.insertText = new vscode.SnippetString(item.insertText);
        completion.filterText = item.filterText;
        completion.sortText = item.sortText;
        
        if (item.additionalTextEdits) {
            completion.additionalTextEdits = item.additionalTextEdits.map(
                edit => new vscode.TextEdit(
                    new vscode.Range(
                        edit.range.start.line,
                        edit.range.start.character,
                        edit.range.end.line,
                        edit.range.end.character
                    ),
                    edit.newText
                )
            );
        }
        
        if (item.command) {
            completion.command = {
                title: item.command.title,
                command: item.command.command,
                arguments: item.command.arguments
            };
        }
        
        return completion;
    }
    
    private getCompletionItemKind(kind: string): vscode.CompletionItemKind {
        const kindMap: { [key: string]: vscode.CompletionItemKind } = {
            'function': vscode.CompletionItemKind.Function,
            'method': vscode.CompletionItemKind.Method,
            'class': vscode.CompletionItemKind.Class,
            'variable': vscode.CompletionItemKind.Variable,
            'constant': vscode.CompletionItemKind.Constant,
            'module': vscode.CompletionItemKind.Module,
            'property': vscode.CompletionItemKind.Property,
            'keyword': vscode.CompletionItemKind.Keyword,
            'snippet': vscode.CompletionItemKind.Snippet
        };
        
        return kindMap[kind] || vscode.CompletionItemKind.Text;
    }
}
```

### 3.2 Hover Provider

```typescript
// src/providers/hoverProvider.ts
import * as vscode from 'vscode';
import { ContextService } from '../services/contextService';

export class HoverProvider implements vscode.HoverProvider {
    constructor(private contextService: ContextService) {}
    
    async provideHover(
        document: vscode.TextDocument,
        position: vscode.Position,
        token: vscode.CancellationToken
    ): Promise<vscode.Hover | null> {
        try {
            // Get word at position
            const wordRange = document.getWordRangeAtPosition(position);
            if (!wordRange) {
                return null;
            }
            
            const word = document.getText(wordRange);
            
            // Get hover information from context service
            const hoverInfo = await this.contextService.getHoverInfo({
                document: document.uri.toString(),
                position: {
                    line: position.line,
                    character: position.character
                },
                word: word
            });
            
            if (!hoverInfo) {
                return null;
            }
            
            // Create hover content
            const contents = new vscode.MarkdownString();
            
            // Add signature
            if (hoverInfo.signature) {
                contents.appendCodeblock(hoverInfo.signature, document.languageId);
            }
            
            // Add documentation
            if (hoverInfo.documentation) {
                contents.appendMarkdown(hoverInfo.documentation);
            }
            
            // Add context information
            if (hoverInfo.contextInfo) {
                contents.appendMarkdown('\n\n---\n\n');
                contents.appendMarkdown('**Context Information:**\n');
                contents.appendMarkdown(hoverInfo.contextInfo);
            }
            
            return new vscode.Hover(contents, wordRange);
            
        } catch (error) {
            Logger.error('Failed to provide hover', error);
            return null;
        }
    }
}
```

### 3.3 Definition Provider

```typescript
// src/providers/definitionProvider.ts
import * as vscode from 'vscode';
import { ContextService } from '../services/contextService';

export class DefinitionProvider implements vscode.DefinitionProvider {
    constructor(private contextService: ContextService) {}
    
    async provideDefinition(
        document: vscode.TextDocument,
        position: vscode.Position,
        token: vscode.CancellationToken
    ): Promise<vscode.Definition | null> {
        try {
            // Get word at position
            const wordRange = document.getWordRangeAtPosition(position);
            if (!wordRange) {
                return null;
            }
            
            const word = document.getText(wordRange);
            
            // Get definition locations from context service
            const definitions = await this.contextService.getDefinitions({
                document: document.uri.toString(),
                position: {
                    line: position.line,
                    character: position.character
                },
                word: word
            });
            
            if (!definitions || definitions.length === 0) {
                return null;
            }
            
            // Convert to VSCode locations
            return definitions.map(def => new vscode.Location(
                vscode.Uri.parse(def.uri),
                new vscode.Range(
                    def.range.start.line,
                    def.range.start.character,
                    def.range.end.line,
                    def.range.end.character
                )
            ));
            
        } catch (error) {
            Logger.error('Failed to provide definition', error);
            return null;
        }
    }
}
```

---

## 4. User Interface Components

### 4.1 Status Bar Management

```typescript
// src/ui/statusBar.ts
import * as vscode from 'vscode';

export class StatusBarManager {
    private statusBarItem: vscode.StatusBarItem;
    private connectionStatus: 'disconnected' | 'connecting' | 'connected' = 'disconnected';
    private indexedFiles: number = 0;
    
    constructor() {
        this.statusBarItem = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Right,
            100
        );
        
        this.statusBarItem.command = 'mobius.showStatus';
        this.updateStatusBar();
        this.statusBarItem.show();
    }
    
    setConnectionStatus(status: 'disconnected' | 'connecting' | 'connected'): void {
        this.connectionStatus = status;
        this.updateStatusBar();
    }
    
    setIndexedFiles(count: number): void {
        this.indexedFiles = count;
        this.updateStatusBar();
    }
    
    private updateStatusBar(): void {
        const icons = {
            'disconnected': '$(circle-slash)',
            'connecting': '$(sync~spin)',
            'connected': '$(check-all)'
        };
        
        const icon = icons[this.connectionStatus];
        const text = `Mobius ${icon}`;
        
        this.statusBarItem.text = text;
        
        // Update tooltip
        const tooltipLines = [
            `Status: ${this.connectionStatus}`,
            `Files indexed: ${this.indexedFiles}`
        ];
        
        if (this.connectionStatus === 'disconnected') {
            tooltipLines.push('Click to connect');
        }
        
        this.statusBarItem.tooltip = tooltipLines.join('\n');
        
        // Update color
        switch (this.connectionStatus) {
            case 'disconnected':
                this.statusBarItem.backgroundColor = new vscode.ThemeColor(
                    'statusBarItem.errorBackground'
                );
                break;
            case 'connecting':
                this.statusBarItem.backgroundColor = new vscode.ThemeColor(
                    'statusBarItem.warningBackground'
                );
                break;
            case 'connected':
                this.statusBarItem.backgroundColor = undefined;
                break;
        }
    }
    
    dispose(): void {
        this.statusBarItem.dispose();
    }
}
```

### 4.2 Command Management

```typescript
// src/activation/commands.ts
import * as vscode from 'vscode';
import { ConnectionManager } from '../client/connection';
import { ContextService } from '../services/contextService';
import { StatusBarManager } from '../ui/statusBar';

export class CommandManager {
    private commands: Map<string, (...args: any[]) => any>;
    
    constructor(
        private connectionManager: ConnectionManager,
        private contextService: ContextService,
        private statusBarManager: StatusBarManager
    ) {
        this.commands = new Map([
            ['mobius.connect', this.connect.bind(this)],
            ['mobius.disconnect', this.disconnect.bind(this)],
            ['mobius.indexCurrentFile', this.indexCurrentFile.bind(this)],
            ['mobius.showContext', this.showContext.bind(this)],
            ['mobius.refreshIndex', this.refreshIndex.bind(this)],
            ['mobius.showStatus', this.showStatus.bind(this)]
        ]);
    }
    
    getCommands(): Map<string, (...args: any[]) => any> {
        return this.commands;
    }
    
    private async connect(): Promise<void> {
        try {
            this.statusBarManager.setConnectionStatus('connecting');
            await this.connectionManager.connect();
            this.statusBarManager.setConnectionStatus('connected');
            
            vscode.window.showInformationMessage('Connected to Mobius Context Engine');
            
            // Start indexing workspace
            await this.refreshIndex();
            
        } catch (error) {
            this.statusBarManager.setConnectionStatus('disconnected');
            vscode.window.showErrorMessage(`Failed to connect: ${error.message}`);
        }
    }
    
    private async disconnect(): Promise<void> {
        await this.connectionManager.disconnect();
        this.statusBarManager.setConnectionStatus('disconnected');
        vscode.window.showInformationMessage('Disconnected from Mobius Context Engine');
    }
    
    private async indexCurrentFile(): Promise<void> {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showWarningMessage('No active editor');
            return;
        }
        
        try {
            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: 'Indexing file...',
                cancellable: false
            }, async (progress) => {
                await this.contextService.indexFile(editor.document.uri.fsPath);
                
                vscode.window.showInformationMessage(
                    `Indexed: ${editor.document.fileName}`
                );
            });
        } catch (error) {
            vscode.window.showErrorMessage(`Failed to index file: ${error.message}`);
        }
    }
    
    private async showContext(): Promise<void> {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showWarningMessage('No active editor');
            return;
        }
        
        try {
            const context = await this.contextService.getContextForPosition(
                editor.document,
                editor.selection.active
            );
            
            // Create output channel
            const outputChannel = vscode.window.createOutputChannel('Mobius Context');
            outputChannel.clear();
            outputChannel.appendLine('Current Context:');
            outputChannel.appendLine(JSON.stringify(context, null, 2));
            outputChannel.show();
            
        } catch (error) {
            vscode.window.showErrorMessage(`Failed to get context: ${error.message}`);
        }
    }
    
    private async refreshIndex(): Promise<void> {
        try {
            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: 'Indexing workspace...',
                cancellable: true
            }, async (progress, token) => {
                const indexProgress = (data: any) => {
                    progress.report({
                        increment: data.progress,
                        message: `${data.filesProcessed}/${data.totalFiles} files`
                    });
                    
                    this.statusBarManager.setIndexedFiles(data.filesProcessed);
                };
                
                this.connectionManager.on('indexProgress', indexProgress);
                
                try {
                    await this.contextService.indexWorkspace(token);
                    vscode.window.showInformationMessage('Workspace indexed successfully');
                } finally {
                    this.connectionManager.off('indexProgress', indexProgress);
                }
            });
        } catch (error) {
            vscode.window.showErrorMessage(`Failed to index workspace: ${error.message}`);
        }
    }
    
    private async showStatus(): Promise<void> {
        const status = await this.contextService.getStatus();
        
        const items = [
            `Connection: ${status.connected ? 'Connected' : 'Disconnected'}`,
            `Files indexed: ${status.filesIndexed}`,
            `Memory usage: ${status.memoryUsage}MB`,
            `Context quality: ${status.contextQuality}%`
        ];
        
        const selected = await vscode.window.showQuickPick(items, {
            placeHolder: 'Mobius Context Engine Status'
        });
        
        if (selected?.startsWith('Connection: Disconnected')) {
            await this.connect();
        }
    }
}
```

---

## 5. Services

### 5.1 Context Service

```typescript
// src/services/contextService.ts
import * as vscode from 'vscode';
import { ConnectionManager } from '../client/connection';
import { CacheService } from './cacheService';

export class ContextService {
    private cacheService: CacheService;
    
    constructor(private connectionManager: ConnectionManager) {
        this.cacheService = new CacheService();
    }
    
    async getContextForPosition(
        document: vscode.TextDocument,
        position: vscode.Position
    ): Promise<any> {
        // Check cache first
        const cacheKey = `${document.uri.toString()}-${position.line}-${position.character}`;
        const cached = await this.cacheService.get(cacheKey);
        
        if (cached) {
            return cached;
        }
        
        // Get surrounding context
        const linePrefix = document.lineAt(position).text.substr(0, position.character);
        const lineSuffix = document.lineAt(position).text.substr(position.character);
        
        // Get broader context
        const startLine = Math.max(0, position.line - 50);
        const endLine = Math.min(document.lineCount - 1, position.line + 50);
        
        const contextLines = [];
        for (let i = startLine; i <= endLine; i++) {
            contextLines.push(document.lineAt(i).text);
        }
        
        const context = {
            file: document.uri.fsPath,
            language: document.languageId,
            position: {
                line: position.line,
                character: position.character
            },
            linePrefix,
            lineSuffix,
            contextLines,
            symbols: await this.getSymbols(document)
        };
        
        // Request enhanced context from backend
        const enhancedContext = await this.connectionManager.request(
            'context/enhance',
            context
        );
        
        // Cache the result
        await this.cacheService.set(cacheKey, enhancedContext, 60000); // 1 minute TTL
        
        return enhancedContext;
    }
    
    async getCompletions(params: any): Promise<any[]> {
        return this.connectionManager.request('completion/provide', params);
    }
    
    async getHoverInfo(params: any): Promise<any> {
        return this.connectionManager.request('hover/provide', params);
    }
    
    async getDefinitions(params: any): Promise<any[]> {
        return this.connectionManager.request('definition/provide', params);
    }
    
    async indexFile(filePath: string): Promise<void> {
        await this.connectionManager.request('index/file', { filePath });
    }
    
    async indexWorkspace(token: vscode.CancellationToken): Promise<void> {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders) {
            return;
        }
        
        const paths = workspaceFolders.map(folder => folder.uri.fsPath);
        
        await this.connectionManager.request('index/workspace', {
            paths,
            cancellationToken: token
        });
    }
    
    async getStatus(): Promise<any> {
        return this.connectionManager.request('status', {});
    }
    
    private async getSymbols(document: vscode.TextDocument): Promise<any[]> {
        const symbols = await vscode.commands.executeCommand<vscode.DocumentSymbol[]>(
            'vscode.executeDocumentSymbolProvider',
            document.uri
        );
        
        if (!symbols) {
            return [];
        }
        
        return this.flattenSymbols(symbols);
    }
    
    private flattenSymbols(symbols: vscode.DocumentSymbol[]): any[] {
        const result: any[] = [];
        
        for (const symbol of symbols) {
            result.push({
                name: symbol.name,
                kind: vscode.SymbolKind[symbol.kind],
                range: {
                    start: {
                        line: symbol.range.start.line,
                        character: symbol.range.start.character
                    },
                    end: {
                        line: symbol.range.end.line,
                        character: symbol.range.end.character
                    }
                }
            });
            
            if (symbol.children) {
                result.push(...this.flattenSymbols(symbol.children));
            }
        }
        
        return result;
    }
}
```

### 5.2 Cache Service

```typescript
// src/services/cacheService.ts
interface CacheEntry {
    value: any;
    expiry: number;
}

export class CacheService {
    private cache: Map<string, CacheEntry> = new Map();
    private cleanupInterval: NodeJS.Timeout;
    
    constructor() {
        // Cleanup expired entries every minute
        this.cleanupInterval = setInterval(() => {
            this.cleanup();
        }, 60000);
    }
    
    async get(key: string): Promise<any | null> {
        const entry = this.cache.get(key);
        
        if (!entry) {
            return null;
        }
        
        if (Date.now() > entry.expiry) {
            this.cache.delete(key);
            return null;
        }
        
        return entry.value;
    }
    
    async set(key: string, value: any, ttl: number = 300000): Promise<void> {
        this.cache.set(key, {
            value,
            expiry: Date.now() + ttl
        });
    }
    
    async delete(key: string): Promise<void> {
        this.cache.delete(key);
    }
    
    async clear(): Promise<void> {
        this.cache.clear();
    }
    
    private cleanup(): void {
        const now = Date.now();
        
        for (const [key, entry] of this.cache.entries()) {
            if (now > entry.expiry) {
                this.cache.delete(key);
            }
        }
    }
    
    dispose(): void {
        clearInterval(this.cleanupInterval);
        this.cache.clear();
    }
}
```

---

## 6. Performance Optimization

### 6.1 Debouncing and Throttling

```typescript
// src/utils/performance.ts
export function debounce<T extends (...args: any[]) => any>(
    func: T,
    wait: number
): (...args: Parameters<T>) => void {
    let timeout: NodeJS.Timeout | null = null;
    
    return (...args: Parameters<T>): void => {
        if (timeout) {
            clearTimeout(timeout);
        }
        
        timeout = setTimeout(() => {
            func(...args);
        }, wait);
    };
}

export function throttle<T extends (...args: any[]) => any>(
    func: T,
    limit: number
): (...args: Parameters<T>) => void {
    let inThrottle = false;
    
    return (...args: Parameters<T>): void => {
        if (!inThrottle) {
            func(...args);
            inThrottle = true;
            
            setTimeout(() => {
                inThrottle = false;
            }, limit);
        }
    };
}

// Usage in providers
export class OptimizedCompletionProvider implements vscode.CompletionItemProvider {
    private debouncedGetCompletions: (...args: any[]) => void;
    
    constructor(private contextService: ContextService) {
        // Debounce completion requests
        this.debouncedGetCompletions = debounce(
            this.getCompletions.bind(this),
            300
        );
    }
    
    async provideCompletionItems(
        document: vscode.TextDocument,
        position: vscode.Position,
        token: vscode.CancellationToken,
        context: vscode.CompletionContext
    ): Promise<vscode.CompletionItem[]> {
        // Use debounced version for better performance
        return new Promise((resolve) => {
            this.debouncedGetCompletions(document, position, context, resolve);
        });
    }
    
    private async getCompletions(
        document: vscode.TextDocument,
        position: vscode.Position,
        context: vscode.CompletionContext,
        callback: (items: vscode.CompletionItem[]) => void
    ): Promise<void> {
        // Implementation
        const items = await this.contextService.getCompletions({
            document: document.uri.toString(),
            position: { line: position.line, character: position.character }
        });
        
        callback(items);
    }
}
```

### 6.2 Memory Management

```typescript
// src/utils/memory.ts
export class MemoryManager {
    private static instance: MemoryManager;
    private memoryUsage: NodeJS.MemoryUsage | null = null;
    private updateInterval: NodeJS.Timeout;
    
    private constructor() {
        this.updateInterval = setInterval(() => {
            this.updateMemoryUsage();
        }, 5000);
    }
    
    static getInstance(): MemoryManager {
        if (!MemoryManager.instance) {
            MemoryManager.instance = new MemoryManager();
        }
        return MemoryManager.instance;
    }
    
    private updateMemoryUsage(): void {
        this.memoryUsage = process.memoryUsage();
        
        // Check if memory usage is too high
        const heapUsedMB = this.memoryUsage.heapUsed / 1024 / 1024;
        
        if (heapUsedMB > 500) {
            Logger.warn(`High memory usage: ${heapUsedMB.toFixed(2)}MB`);
            
            // Trigger garbage collection if available
            if (global.gc) {
                global.gc();
            }
        }
    }
    
    getMemoryUsage(): NodeJS.MemoryUsage | null {
        return this.memoryUsage;
    }
    
    dispose(): void {
        clearInterval(this.updateInterval);
    }
}
```

---

## 7. Configuration

### 7.1 TypeScript Configuration

```json
// tsconfig.json
{
  "compilerOptions": {
    "module": "commonjs",
    "target": "ES2021",
    "lib": ["ES2021"],
    "outDir": "./out",
    "rootDir": "./src",
    "sourceMap": true,
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "moduleResolution": "node",
    "declaration": true,
    "declarationMap": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "out", "dist"]
}
```

### 7.2 Webpack Configuration

```javascript
// webpack.config.js
const path = require('path');

module.exports = {
    target: 'node',
    mode: 'none',
    entry: './src/extension.ts',
    output: {
        path: path.resolve(__dirname, 'dist'),
        filename: 'extension.js',
        libraryTarget: 'commonjs2'
    },
    externals: {
        vscode: 'commonjs vscode'
    },
    resolve: {
        extensions: ['.ts', '.js']
    },
    module: {
        rules: [
            {
                test: /\.ts$/,
                exclude: /node_modules/,
                use: [
                    {
                        loader: 'ts-loader'
                    }
                ]
            }
        ]
    },
    devtool: 'nosources-source-map',
    infrastructureLogging: {
        level: 'log'
    }
};
```

---

## 8. Testing Strategy

### 8.1 Unit Tests

```typescript
// src/test/providers/completionProvider.test.ts
import * as vscode from 'vscode';
import { CompletionProvider } from '../../providers/completionProvider';
import { ContextService } from '../../services/contextService';

jest.mock('../../services/contextService');

describe('CompletionProvider', () => {
    let provider: CompletionProvider;
    let mockContextService: jest.Mocked<ContextService>;
    
    beforeEach(() => {
        mockContextService = new ContextService() as jest.Mocked<ContextService>;
        provider = new CompletionProvider(mockContextService);
    });
    
    it('should provide completions', async () => {
        const mockCompletions = [
            {
                label: 'testFunction',
                kind: 'function',
                detail: 'def testFunction()',
                documentation: 'Test function'
            }
        ];
        
        mockContextService.getCompletions.mockResolvedValue(mockCompletions);
        
        const document = {} as vscode.TextDocument;
        const position = new vscode.Position(0, 0);
        const token = {} as vscode.CancellationToken;
        const context = {} as vscode.CompletionContext;
        
        const items = await provider.provideCompletionItems(
            document,
            position,
            token,
            context
        );
        
        expect(items).toHaveLength(1);
        expect(items[0].label).toBe('testFunction');
    });
});
```

### 8.2 Integration Tests

```typescript
// src/test/integration/extension.test.ts
import * as vscode from 'vscode';
import * as path from 'path';

describe('Extension Integration Tests', () => {
    const extensionId = 'mobius.mobius-context-engine';
    
    beforeAll(async () => {
        const ext = vscode.extensions.getExtension(extensionId);
        await ext?.activate();
    });
    
    it('should register all commands', async () => {
        const commands = await vscode.commands.getCommands();
        
        expect(commands).toContain('mobius.connect');
        expect(commands).toContain('mobius.disconnect');
        expect(commands).toContain('mobius.indexCurrentFile');
        expect(commands).toContain('mobius.showContext');
    });
    
    it('should provide completions for Python files', async () => {
        const docUri = vscode.Uri.file(
            path.join(__dirname, 'fixtures', 'test.py')
        );
        
        const document = await vscode.workspace.openTextDocument(docUri);
        const position = new vscode.Position(5, 10);
        
        const completions = await vscode.commands.executeCommand<vscode.CompletionList>(
            'vscode.executeCompletionItemProvider',
            docUri,
            position
        );
        
        expect(completions.items.length).toBeGreaterThan(0);
    });
});
```

---

## 9. Deployment

### 9.1 Build Script

```json
// package.json scripts
{
  "scripts": {
    "vscode:prepublish": "npm run package",
    "compile": "webpack --mode development",
    "watch": "webpack --mode development --watch",
    "package": "webpack --mode production --devtool hidden-source-map",
    "test-compile": "tsc -p ./",
    "test-watch": "tsc -watch -p ./",
    "pretest": "npm run test-compile && npm run lint",
    "lint": "eslint src --ext ts",
    "test": "jest",
    "package-vsix": "vsce package",
    "publish": "vsce publish"
  }
}
```

### 9.2 GitHub Actions CI/CD

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        
    - name: Install dependencies
      run: npm ci
      
    - name: Run linter
      run: npm run lint
      
    - name: Run tests
      run: npm test
      
    - name: Build extension
      run: npm run package
      
    - name: Upload VSIX
      uses: actions/upload-artifact@v3
      with:
        name: mobius-vscode-extension
        path: '*.vsix'
```

---

## Conclusion

This VSCode integration plan provides a comprehensive foundation for the Phase 1 MVP. The architecture emphasizes:

1. **Modularity**: Clean separation of concerns with dedicated services
2. **Performance**: Debouncing, caching, and efficient communication
3. **User Experience**: Intuitive commands and real-time feedback
4. **Extensibility**: Easy to add new providers and features
5. **Reliability**: Robust error handling and reconnection logic

The implementation follows VSCode best practices and provides a solid foundation for future enhancements in subsequent phases.