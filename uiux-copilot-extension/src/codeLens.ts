import * as vscode from 'vscode';
import { UIUXIssue } from './analyzer';

export class UIUXCodeLensProvider implements vscode.CodeLensProvider {
    private issues: UIUXIssue[] = [];

    public setIssues(issues: UIUXIssue[]) {
        this.issues = issues;
    }

    public provideCodeLenses(document: vscode.TextDocument, token: vscode.CancellationToken): vscode.CodeLens[] {
        const lenses: vscode.CodeLens[] = [];

        this.issues.forEach(issue => {
            const lineIndex = Math.max(0, issue.line - 1);
            const range = new vscode.Range(lineIndex, 0, lineIndex, 0);

            const lens = new vscode.CodeLens(range, {
                title: `✨ AI Fix Available [WCAG ${issue.wcag_rule}]`,
                command: 'uiux-copilot.applyFix',
                arguments: [document, issue]
            });

            lenses.push(lens);
        });

        return lenses;
    }
}
