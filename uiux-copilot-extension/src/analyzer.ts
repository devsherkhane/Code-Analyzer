import axios from 'axios';

export interface UIUXIssue {
    line: number;
    wcag_rule: string;
    severity: string;
    element: string;
    problem: string;
    original_code: string;
    fixed_code: string;
    explanation: string;
    fix_diff: string;
}

export async function analyzeFileLocal(filePath: string, content: string): Promise<UIUXIssue[]> {
    try {
        const response = await axios.post('http://127.0.0.1:7891/analyze-file', {
            file_path: filePath,
            content: content
        });
        
        if (response.data && Array.isArray(response.data.issues)) {
            return response.data.issues;
        }
    } catch (e) {
        console.error("Local UI/UX analyzer failed:", e);
    }
    return [];
}
