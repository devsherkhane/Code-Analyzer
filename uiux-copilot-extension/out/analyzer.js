"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.analyzeFileLocal = analyzeFileLocal;
const axios_1 = __importDefault(require("axios"));
async function analyzeFileLocal(filePath, content) {
    try {
        const response = await axios_1.default.post('http://127.0.0.1:7891/analyze-file', {
            file_path: filePath,
            content: content
        });
        if (response.data && Array.isArray(response.data.issues)) {
            return response.data.issues;
        }
    }
    catch (e) {
        console.error("Local UI/UX analyzer failed:", e);
    }
    return [];
}
//# sourceMappingURL=analyzer.js.map