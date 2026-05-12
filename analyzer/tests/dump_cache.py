import json
cache = json.load(open(r'c:\Users\devs\Desktop\code-analyzer\backend\json_reports\ai_hash_cache.json'))
print(f"Total cached entries: {len(cache)}")
for k, v in cache.items():
    health = v.get("visual_simulation", {}).get("engineering_health_score", "?")
    issues = len(v.get("issues", []))
    layout = v.get("visual_simulation", {}).get("layout_assessment", "?")[:60]
    print(f"  {k[:20]}... -> issues={issues}, health={health}, layout={layout}")
