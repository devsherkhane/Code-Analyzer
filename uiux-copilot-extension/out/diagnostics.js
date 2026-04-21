"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.updateDiagnostics = updateDiagnostics;
const vscode = __importStar(require("vscode"));
function updateDiagnostics(document, issues, collection) {
    if (issues.length === 0) {
        collection.clear();
        return;
    }
    const diagnostics = [];
    issues.forEach(issue => {
        const lineIndex = Math.max(0, issue.line - 1);
        const lineText = document.lineAt(lineIndex).text;
        const startChar = lineText.indexOf(issue.element.replace(/[<>]/g, '').trim());
        const start = startChar > -1 ? startChar : 0;
        const end = lineText.length;
        const range = new vscode.Range(lineIndex, start, lineIndex, end);
        let severity = vscode.DiagnosticSeverity.Information;
        if (issue.severity.toLowerCase() === 'critical')
            severity = vscode.DiagnosticSeverity.Error;
        else if (issue.severity.toLowerCase() === 'major')
            severity = vscode.DiagnosticSeverity.Warning;
        const message = `[WCAG ${issue.wcag_rule}] ${issue.problem}\n\nFix via AI: ${issue.explanation}`;
        const diagnostic = new vscode.Diagnostic(range, message, severity);
        diagnostic.source = 'UI/UX Copilot';
        diagnostics.push(diagnostic);
    });
    collection.set(document.uri, diagnostics);
}
//# sourceMappingURL=diagnostics.js.map