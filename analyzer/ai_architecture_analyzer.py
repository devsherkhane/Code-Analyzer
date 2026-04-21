import os
import json

from ai_config import get_client, call_ai

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

current_dir = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.normpath(os.path.join(current_dir, "..", "backend", "json_reports"))

def run_ai_architecture_analyzer():
    print(f"\n{'='*50}\nSTARTING AI ARCHITECTURE MAPPING\n{'='*50}")

    client = get_client()
    if not client: return

    graph_path = os.path.join(CACHE_DIR, "dependency_graph.json")
    if not os.path.exists(graph_path):
        print(f"  -> [SKIP] Dependency graph not found at {graph_path}")
        return

    try:
        with open(graph_path, "r", encoding="utf-8") as f:
            dep_graph = json.load(f)
    except Exception as e:
        print(f"  -> [ERROR] Failed to load dependency graph: {e}")
        return

    file_map = dep_graph.get("file_map", {})
    if not file_map:
        print("  -> [SKIP] Dependency graph is empty. Nothing to map.")
        return

    files_data = [{"id": k, "name": v.get("name"), "path": v.get("path")} for k, v in file_map.items()]
    connections_data = dep_graph.get("connections", [])

    # LOAD AI REPORT for finding summary
    report_summary = []
    report_path = os.path.normpath(os.path.join(CACHE_DIR, "..", "ai_report.json"))
    if os.path.exists(report_path):
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                full_report = json.load(f)
                files = full_report.get("files", [])
                for file in files:
                    issues = (file.get("ai_analysis", []) + file.get("ui_accessibility_analysis", []))
                    real_issues = [i for i in issues if i.get("is_real_issue")]
                    if real_issues:
                        report_summary.append({
                            "file": file.get("file_name"),
                            "issue_types": list(set([i.get("defect_type") for i in real_issues])),
                            "total_issues": len(real_issues)
                        })
        except: pass

    payload = {
        "files": files_data,
        "connections": connections_data,
        "confirmed_issues_summary": report_summary
    }

    prompt = f"""
You are an Elite Enterprise Architect. Analyze the following project dependency graph and individual file metadata to perform a "Core Structural Audit".

AUDIT GOALS:
1. CROSS-LAYER CONTAMINATION: Identify if low-level utilities are importing high-level Views (Architectural Inversion).
2. STATE MANAGEMENT FRAGILITY: Look for deep prop-drilling or inconsistent state patterns (e.g., mixing Vuex/Pinia with heavy local state without clear boundaries).
3. CIRCULAR VULNERABILITIES: Locate circular dependency chains that could lead to memory leaks or initialization errors.
4. CENTRALIZED FRAGILITY (God Files): Identify files that are "Architectural Hubs" (heavily depended upon) but also have high complexity issues in the report.

RESPONSE SCHEMA (Strict JSON):
{{
  "project_overview": "A 3-4 sentence high-level architectural summary.",
  "architectural_health_score": 0,
  "layers": [
    {{
      "layer_name": "Calculated Layer Name",
      "description": "Technical role in the codebase.",
      "file_names": ["List of files"]
    }}
  ],
  "macro_trends": [
    {{
      "title": "Clear, distinct trend title",
      "trend_type": "STRUCTURAL | QUALITY | STABILITY",
      "severity": "HIGH | MEDIUM | LOW",
      "description": "Evidence-backed explanation of the trend.",
      "affected_areas": ["Layers or specific directories impacted"]
    }}
  ],
  "key_workflows": [
    {{
      "name": "Critical path name",
      "description": "Trace the dependency flow and explain why it is vital."
    }}
  ]
}}

DEPENDENCY & ISSUE DATA:
{json.dumps(payload, indent=2)}
"""

    print("  -> [AI] Analyzing structural patterns and cross-file dependencies...")
    try:
        response_text, model_used = call_ai(client, prompt, json_mode=True, max_retries=2)
        print(f"  -> [AI ENGINE] Model: {model_used}")
        
        parsed_result = json.loads(response_text)
        
        out_path = os.path.normpath(os.path.join(CACHE_DIR, "..", "ai_architecture.json"))
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(parsed_result, f, indent=4)
            
        print(f"  -> [SUCCESS] AI Architecture Map generated successfully at {out_path}")
        
    except Exception as e:
        print(f"  -> [ERROR] Failed to map architecture via AI: {e}")

if __name__ == "__main__":
    run_ai_architecture_analyzer()
