import * as vscode from 'vscode';
import { analyzeFileLocal, UIUXIssue } from './analyzer';
import { updateDiagnostics } from './diagnostics';
import { UIUXCodeLensProvider } from './codeLens';

export function activate(context: vscode.ExtensionContext) {
    const diagnosticCollection = vscode.languages.createDiagnosticCollection('uiux');
    const codeLensProvider = new UIUXCodeLensProvider();

    // Analyze on save
    vscode.workspace.onDidSaveTextDocument(async (doc) => {
        if (doc.languageId === 'vue' || doc.languageId === 'html' || doc.languageId.includes('react')) {
            const issues = await analyzeFileLocal(doc.fileName, doc.getText());
            updateDiagnostics(doc, issues, diagnosticCollection);
            codeLensProvider.setIssues(issues);
        }
    });

    const applyFixCmd = vscode.commands.registerCommand('uiux-copilot.applyFix', async (document: vscode.TextDocument, issue: UIUXIssue) => {
        const edit = new vscode.WorkspaceEdit();
        const text = document.getText();
        const startIdx = text.indexOf(issue.original_code);
        
        if (startIdx > -1) {
            const startPos = document.positionAt(startIdx);
            const endPos = document.positionAt(startIdx + issue.original_code.length);
            const range = new vscode.Range(startPos, endPos);
            edit.replace(document.uri, range, issue.fixed_code);
            await vscode.workspace.applyEdit(edit);
            vscode.window.showInformationMessage('UI/UX Fix Applied');
        } else {
            vscode.window.showErrorMessage('Could not locate original code block in file');
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
                <iframe src="http://localhost:8081?vscode=true&path=${encodeURIComponent(workspaceFolder)}" frameborder="0"></iframe>
                <script>
                    const vscode = acquireVsCodeApi();
                    window.addEventListener('message', event => {
                        if (event.data && event.data.command) {
                            vscode.postMessage(event.data);
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
                    case 'applyFix': {
                        try {
                            const uri = vscode.Uri.file(message.filePath);
                            const document = await vscode.workspace.openTextDocument(uri);
                            const text = document.getText();
                            let startIdx = text.indexOf(message.originalCode);
                            let endIdx = -1;

                            if (startIdx > -1) {
                                endIdx = startIdx + message.originalCode.length;
                            } else if (message.originalCode) {
                                // Fallback: Ignore whitespace and line-endings differences
                                const escapeRegExp = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                                const regexStr = message.originalCode.trim().split(/\s+/).map(escapeRegExp).join('\\s+');
                                const match = new RegExp(regexStr).exec(text);
                                if (match) {
                                    startIdx = match.index;
                                    endIdx = match.index + match[0].length;
                                }
                            }

                            if (startIdx === -1 && endIdx === -1 && message.startLine > 0) {
                                // Fallback 2: Direct line replacement if parsing completely fails
                                const lineIndex = Math.max(0, message.startLine - 1);
                                const endLineIndex = Math.max(0, (message.endLine || message.startLine) - 1);
                                
                                if (lineIndex < document.lineCount) {
                                    startIdx = document.offsetAt(new vscode.Position(lineIndex, 0));
                                    endIdx = document.offsetAt(document.lineAt(Math.min(endLineIndex, document.lineCount - 1)).range.end);
                                }
                            }

                            if (startIdx > -1 && endIdx > -1) {
                                const startPos = document.positionAt(startIdx);
                                const endPos = document.positionAt(endIdx);
                                const range = new vscode.Range(startPos, endPos);
                                const edit = new vscode.WorkspaceEdit();
                                edit.replace(document.uri, range, message.fixedCode);
                                await vscode.workspace.applyEdit(edit);
                                vscode.window.showInformationMessage('UI/UX Fix Applied from Dashboard');
                                
                                await vscode.window.showTextDocument(document, {
                                    selection: range,
                                    viewColumn: vscode.ViewColumn.One
                                });
                            } else {
                                vscode.window.showErrorMessage('Could not locate original code block in file. Try applying the fix manually.');
                            }
                        } catch (e) {
                            vscode.window.showErrorMessage('Failed to apply fix: ' + String(e));
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
        vscode.languages.registerCodeLensProvider({ pattern: '**/*.{vue,tsx,html}' }, codeLensProvider),
        applyFixCmd,
        showDashboardCmd
    );
}
