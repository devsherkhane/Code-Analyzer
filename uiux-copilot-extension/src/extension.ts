import * as vscode from 'vscode';
import { analyzeFileLocal, UIUXIssue } from './analyzer';
import { updateDiagnostics } from './diagnostics';

export function activate(context: vscode.ExtensionContext) {
    const diagnosticCollection = vscode.languages.createDiagnosticCollection('uiux');

    // Analyze on save
    vscode.workspace.onDidSaveTextDocument(async (doc) => {
        if (doc.languageId === 'vue' || doc.languageId === 'html' || doc.languageId.includes('react')) {
            const issues = await analyzeFileLocal(doc.fileName, doc.getText());
            updateDiagnostics(doc, issues, diagnosticCollection);
        }
    });



    const showDashboardCmd = vscode.commands.registerCommand('uiux-copilot.showDashboard', () => {
        const panel = vscode.window.createWebviewPanel(
            'uiuxDashboard',
            'UI/UX Dashboard',
            vscode.ViewColumn.Two,
            {
                enableScripts: true,
                retainContextWhenHidden: true
            }
        );

        // Get the current workspace folder to pass to the dashboard
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || '';

        // Load the dashboard from our Go server
        // Add a query param so the frontend knows it's in VS Code
        panel.webview.html = `
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>UI/UX Dashboard</title>
                <style>
                    body, html, iframe { margin: 0; padding: 0; height: 100%; width: 100%; overflow: hidden; background: #121212; }
                </style>
            </head>
            <body>
                <iframe src="http://localhost:8081?vscode=true&path=${encodeURIComponent(workspaceFolder)}&cb=${Date.now()}" frameborder="0"></iframe>
                <script>
                    const vscode = acquireVsCodeApi();
                    const iframe = document.querySelector('iframe');
                    
                    window.addEventListener('message', event => {
                        // Check if the message came from the iframe
                        if (event.source === iframe.contentWindow) {
                            // Forward message from iframe to VS Code extension
                            if (event.data && event.data.command) {
                                vscode.postMessage(event.data);
                            }
                        } else {
                            // Message came from VS Code extension, forward down to iframe
                            if (iframe && iframe.contentWindow && event.data) {
                                iframe.contentWindow.postMessage(event.data, '*');
                            }
                        }
                    });
                </script>
            </body>
            </html>
        `;

        panel.webview.onDidReceiveMessage(
            async (message) => {
                switch (message.command) {
                    case 'openFile': {
                        try {
                            const uri = vscode.Uri.file(message.filePath);
                            const document = await vscode.workspace.openTextDocument(uri);
                            const lineIndex = Math.max(0, (message.startLine || 1) - 1);
                            const endIndex = Math.max(0, (message.endLine || message.startLine || 1) - 1);
                            
                            const startPos = new vscode.Position(lineIndex, 0);
                            const endPos = new vscode.Position(endIndex, Number.MAX_VALUE);
                            const range = new vscode.Range(startPos, endPos);
                            
                            await vscode.window.showTextDocument(document, {
                                selection: range,
                                viewColumn: vscode.ViewColumn.One
                            });
                        } catch (e) {
                            vscode.window.showErrorMessage('Could not open file: ' + message.filePath);
                        }
                        break;
                    }

                }
            },
            undefined,
            context.subscriptions
        );
    });

    context.subscriptions.push(
        diagnosticCollection,
        showDashboardCmd
    );
}
