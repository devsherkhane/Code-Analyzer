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
    report_id = None
    report_path = os.path.normpath(os.path.join(CACHE_DIR, "..", "ai_report.json"))
    if os.path.exists(report_path):
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                full_report = json.load(f)
                report_id = full_report.get("report_id")
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

DEPENDENCY & ISSUE DATA:
{json.dumps(payload, indent=2)}

---

AUDIT GOALS:
1. CROSS-LAYER CONTAMINATION: Identify if low-level utilities are importing high-level Views.
2. STATE MANAGEMENT FRAGILITY: Look for deep prop-drilling or inconsistent state patterns.
3. CIRCULAR VULNERABILITIES: Locate circular dependency chains.
4. CENTRALIZED FRAGILITY: Identify "God Files".

CRITICAL INSTRUCTION: You MUST format your response as a valid JSON object matching the EXACT schema below. Do NOT output a list of edges. Do NOT output markdown.

RESPONSE SCHEMA (Strict JSON):
{{
  "project_overview": "A 3-4 sentence high-level architectural summary.",
  "architectural_health_score": 0,
  "layers": [
    {{
      "layer_name": "Layer Name",
      "description": "Technical role.",
      "file_names": ["file1.js", "file2.js"]
    }}
  ],
  "macro_trends": [
    {{
      "title": "Trend title",
      "trend_type": "STRUCTURAL",
      "severity": "HIGH",
      "description": "Explanation.",
      "affected_areas": ["directory/"]
    }}
  ],
  "key_workflows": [
    {{
      "name": "Critical path name",
      "description": "Dependency flow explanation."
    }}
  ]
}}
"""

    print("  -> [AI] Analyzing structural patterns and cross-file dependencies...")
    try:
        response_text, model_used = call_ai(client, prompt, json_mode=True, max_retries=4)
        print(f"  -> [AI ENGINE] Model: {model_used}")
        
        parsed_result = json.loads(response_text)
        
        if "project_overview" not in parsed_result:
            print("  -> [WARNING] Model did not return project_overview. Using fallback schema.")
            parsed_result = {
                "project_overview": "AI analysis completed, but the model failed to follow the strict architectural schema. Detailed insights are limited.",
                "architectural_health_score": 50,
                "layers": [
                    {
                        "layer_name": "General Structure",
                        "description": "The project graph was analyzed but layer separation couldn't be cleanly determined by the AI.",
                        "file_names": []
                    }
                ],
                "macro_trends": [],
                "key_workflows": [],
                "raw_output": parsed_result
            }
        
        out_path = os.path.normpath(os.path.join(CACHE_DIR, "..", "ai_architecture.json"))
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(parsed_result, f, indent=4)
            
        if report_id:
            hist_out_path = os.path.normpath(os.path.join(CACHE_DIR, f"ai_architecture_{report_id}.json"))
            try:
                with open(hist_out_path, "w", encoding="utf-8") as f:
                    json.dump(parsed_result, f, indent=4)
            except Exception as e:
                print(f"  -> [WARNING] Failed to save historical AI Architecture Map: {e}")
            
        print(f"  -> [SUCCESS] AI Architecture Map generated successfully at {out_path}")
        
    except Exception as e:
        print(f"  -> [ERROR] Failed to map architecture via AI: {e}")

if __name__ == "__main__":
    run_ai_architecture_analyzer()
