"""Test the improved call_ai with a realistic analysis prompt."""
import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ai_config import get_client, call_ai

client = get_client()
if not client:
    print("FAIL: Could not create client")
    sys.exit(1)

# Simulate a realistic prompt similar to what ai_reporter sends
prompt = """Analyze this Vue component for UI/UX accessibility issues.

You MUST return a JSON object with a key for EACH of these file IDs: ["1"]
Each key maps to an object with "issues" (array) and "visual_simulation" (object).

Issue schema per entry:
{
  "line": 1,
  "wcag_rule": "1.1.1 Non-text Content",
  "severity": "critical",
  "element": "<img>",
  "problem": "Brief explanation.",
  "original_code": "exact snippet from the file",
  "fixed_code": "complete corrected snippet",
  "explanation": "why the fix solves the problem"
}

Visual simulation schema:
{
  "layout_assessment": "Brief assessment",
  "engineering_health_score": 85,
  "recommendations": ["Rec 1"]
}

Respond ONLY with raw JSON, no markdown blocks.
Analyzing 1 file(s): test.vue

FILES DATA:
[{"file_id": "1", "file_name": "test.vue", "route": "unknown", "source_code": "<template>\\n  <div @click=\\"goBack()\\">\\n    <i class=\\"fa-light fa-arrow-left\\"></i>\\n  </div>\\n</template>"}]"""

print("Sending analysis prompt to gemma3:latest...")
try:
    result, model = call_ai(client, prompt, json_mode=True, max_retries=2)
    parsed = json.loads(result)
    print(f"SUCCESS! Model: {model}")
    print(f"Keys: {list(parsed.keys())}")
    print(json.dumps(parsed, indent=2)[:500])
except Exception as e:
    print(f"FAIL: {e}")
