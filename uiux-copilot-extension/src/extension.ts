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
                    case 'applyFix': {
                        try {
                            const uri = vscode.Uri.file(message.filePath);
                            const document = await vscode.workspace.openTextDocument(uri);
                            const text = document.getText();

                            // ── Layer 5: Snapshot for rollback ──
                            const snapshotContent = text;

                            // ── Locate the original code in the file ──
                            let startIdx = -1;
                            let endIdx = -1;
                            
                            // Normalize line endings to match document
                            const eol = text.includes('\r\n') ? '\r\n' : '\n';
                            let normOriginal = message.originalCode ? message.originalCode.replace(/\r\n|\n/g, eol) : '';
                            let normFixed = message.fixedCode ? message.fixedCode.replace(/\r\n|\n/g, eol) : '';

                            // The AI scanner prepends line numbers like "12: " to context.
                            // We must strip them or it won't match the actual file contents.
                            normOriginal = normOriginal.replace(/^\s*\d+:\s?/gm, '');
                            normFixed = normFixed.replace(/^\s*\d+:\s?/gm, '');

                            // Strip extra newlines from fixedCode if originalCode didn't have them
                            if (normOriginal && normFixed) {
                                if (!normOriginal.endsWith(eol) && normFixed.endsWith(eol)) {
                                    normFixed = normFixed.replace(new RegExp(`${eol}$`), '');
                                }
                                if (!normOriginal.startsWith(eol) && normFixed.startsWith(eol)) {
                                    normFixed = normFixed.replace(new RegExp(`^${eol}`), '');
                                }
                            }

                            if (normOriginal) {
                                startIdx = text.indexOf(normOriginal);
                                if (startIdx > -1) {
                                    endIdx = startIdx + normOriginal.length;
                                } else {
                                    // Fallback: Ignore whitespace / line-ending differences
                                    const escapeRegExp = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                                    const regexStr = normOriginal.trim().split(/\s+/).map(escapeRegExp).join('\\s+');
                                    const match = new RegExp(regexStr).exec(text);
                                    if (match) {
                                        startIdx = match.index;
                                        endIdx = match.index + match[0].length;
                                        // Since we matched from the first non-whitespace to the last non-whitespace,
                                        // we should also trim the fixed code so we don't inject extra spaces.
                                        normFixed = normFixed.trim();
                                    }
                                }
                            }

                            if (startIdx === -1 && endIdx === -1 && message.startLine > 0) {
                                // Fallback 2: Direct line replacement
                                const lineIndex = Math.max(0, message.startLine - 1);
                                const endLineIndex = Math.max(0, (message.endLine || message.startLine) - 1);

                                if (lineIndex < document.lineCount) {
                                    // Replace entire lines, so we want to keep normFixed's indentation
                                    // but we should ensure it doesn't have an extra trailing newline since lineAt().range.end doesn't include it
                                    startIdx = document.offsetAt(new vscode.Position(lineIndex, 0));
                                    endIdx = document.offsetAt(document.lineAt(Math.min(endLineIndex, document.lineCount - 1)).range.end);
                                    normFixed = normFixed.replace(/\r?\n$/, ''); 
                                }
                            }

                            if (startIdx === -1 || endIdx === -1) {
                                panel.webview.postMessage({ command: 'fixStatus', status: 'error', message: 'Could not locate original code block in file.' });
                                vscode.window.showErrorMessage('Could not locate original code block in file. Try applying the fix manually.');
                                break;
                            }

                            // ── Layer 3: Diff preview before applying ──
                            const patchedContent = text.substring(0, startIdx) + normFixed + text.substring(endIdx);
                            const originalUri = uri;

                            // Write patched content to a temp file for diff
                            const tmpDir = uri.fsPath + '.prismai-preview';
                            const fs = require('fs');
                            fs.writeFileSync(tmpDir, patchedContent, 'utf-8');
                            const previewUri = vscode.Uri.file(tmpDir);

                            await vscode.commands.executeCommand('vscode.diff',
                                originalUri,
                                previewUri,
                                '⚡ AI Fix Preview  (Original ← → Fixed)',
                                { preview: true }
                            );

                            const confirm = await vscode.window.showInformationMessage(
                                'Review the diff above. Apply this AI fix?',
                                { modal: false },
                                'Apply Fix',
                                'Cancel'
                            );

                            // Clean up temp file
                            try { fs.unlinkSync(tmpDir); } catch (_e) { /* ignore */ }

                            if (confirm !== 'Apply Fix') {
                                panel.webview.postMessage({ command: 'fixStatus', status: 'cancelled', message: 'Fix cancelled by user.' });
                                // Close the diff tab
                                await vscode.commands.executeCommand('workbench.action.closeActiveEditor');
                                break;
                            }

                            // Close the diff tab
                            await vscode.commands.executeCommand('workbench.action.closeActiveEditor');

                            // ── Apply the edit ──
                            const startPos = document.positionAt(startIdx);
                            const endPos = document.positionAt(endIdx);
                            const range = new vscode.Range(startPos, endPos);
                            const edit = new vscode.WorkspaceEdit();
                            edit.replace(document.uri, range, normFixed);
                            await vscode.workspace.applyEdit(edit);
                            await document.save();

                            // ── Layer 4: Post-apply diagnostic check ──
                            // Wait a moment for language servers to process
                            await new Promise(resolve => setTimeout(resolve, 1500));

                            const diagnostics = vscode.languages.getDiagnostics(document.uri);
                            const errors = diagnostics.filter(d => d.severity === vscode.DiagnosticSeverity.Error);

                            if (errors.length > 0) {
                                const errorMessages = errors.slice(0, 3).map(e => e.message).join('; ');
                                const action = await vscode.window.showWarningMessage(
                                    `⚠️ Fix applied but ${errors.length} compilation error(s) detected: ${errorMessages}`,
                                    'Undo Fix (Rollback)',
                                    'Keep Anyway'
                                );

                                if (action === 'Undo Fix (Rollback)') {
                                    // ── Layer 5: Rollback ──
                                    const fullRange = new vscode.Range(
                                        document.positionAt(0),
                                        document.positionAt(document.getText().length)
                                    );
                                    const rollbackEdit = new vscode.WorkspaceEdit();
                                    rollbackEdit.replace(document.uri, fullRange, snapshotContent);
                                    await vscode.workspace.applyEdit(rollbackEdit);
                                    await document.save();
                                    panel.webview.postMessage({ command: 'fixStatus', status: 'rolledback', message: 'Fix was rolled back due to compilation errors.' });
                                    vscode.window.showInformationMessage('✅ Fix rolled back successfully. File restored to original state.');
                                    break;
                                } else {
                                    panel.webview.postMessage({ command: 'fixStatus', status: 'warning', message: `Fix applied with ${errors.length} warning(s). Review the file.` });
                                }
                            } else {
                                panel.webview.postMessage({ command: 'fixStatus', status: 'success', message: 'Fix applied successfully — no compilation errors detected!' });
                                vscode.window.showInformationMessage('✅ AI Fix Applied — No compilation errors detected!');
                            }

                            await vscode.window.showTextDocument(document, {
                                selection: range,
                                viewColumn: vscode.ViewColumn.One
                            });
                        } catch (e) {
                            panel.webview.postMessage({ command: 'fixStatus', status: 'error', message: 'Failed to apply fix: ' + String(e) });
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
