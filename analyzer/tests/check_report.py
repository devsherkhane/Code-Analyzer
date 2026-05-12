"""Diagnose why issues aren't appearing in the report."""
import json, os

report_path = r"c:\Users\devs\Desktop\code-analyzer\backend\ai_report.json"
cache_path = r"c:\Users\devs\Desktop\code-analyzer\backend\json_reports\ai_hash_cache.json"

# Check main report
r = json.load(open(report_path, encoding="utf-8"))
print(f"=== REPORT: {r.get('report_id')} ===")
print(f"Files: {r.get('files_analyzed')}, Total Issues: {r.get('total_issues')}")
print(f"Real Issues: {r.get('total_real_issues')}, False Positives: {r.get('total_false_positives')}")
print()

for f in r.get("files", []):
    name = f["file_name"]
    ai = f.get("ai_analysis", [])
    ui = f.get("ui_accessibility_analysis", [])
    health = f.get("visual_simulation", {}).get("engineering_health_score", "?")
    layout = f.get("visual_simulation", {}).get("layout_assessment", "?")[:80]
    total = len(ai) + len(ui)
    print(f"  {name}: ai_issues={len(ai)}, ui_issues={len(ui)}, health={health}")
    if total == 0 and health == 0:
        print(f"    -> PROBLEM: {layout}")

# Check cache
print(f"\n=== CACHE ===")
cache = json.load(open(cache_path, encoding="utf-8"))
print(f"Cached entries: {len(cache)}")
for h, v in list(cache.items())[:3]:
    issues = v.get("issues", [])
    health = v.get("visual_simulation", {}).get("engineering_health_score", "?")
    layout = v.get("visual_simulation", {}).get("layout_assessment", "?")[:60]
    print(f"  hash={h[:16]}...: {len(issues)} issues, health={health}, layout={layout}")
