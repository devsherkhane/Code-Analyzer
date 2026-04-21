import * as vscode from 'vscode';
import { UIUXIssue } from './analyzer';

export function updateDiagnostics(document: vscode.TextDocument, issues: UIUXIssue[], collection: vscode.DiagnosticCollection) {
    if (issues.length === 0) {
        collection.clear();
        return;
    }

    const diagnostics: vscode.Diagnostic[] = [];

    issues.forEach(issue => {
        const lineIndex = Math.max(0, issue.line - 1);
        const lineText = document.lineAt(lineIndex).text;
        const startChar = lineText.indexOf(issue.element.replace(/[<>]/g, '').trim());
        const start = startChar > -1 ? startChar : 0;
        const end = lineText.length;

        const range = new vscode.Range(lineIndex, start, lineIndex, end);
        
        let severity = vscode.DiagnosticSeverity.Information;
        if (issue.severity.toLowerCase() === 'critical') severity = vscode.DiagnosticSeverity.Error;
        else if (issue.severity.toLowerCase() === 'major') severity = vscode.DiagnosticSeverity.Warning;

        const message = `[WCAG ${issue.wcag_rule}] ${issue.problem}\n\nFix via AI: ${issue.explanation}`;
        const diagnostic = new vscode.Diagnostic(range, message, severity);
        diagnostic.source = 'UI/UX Copilot';
        
        diagnostics.push(diagnostic);
    });

    collection.set(document.uri, diagnostics);
}
