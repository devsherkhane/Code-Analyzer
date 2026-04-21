import os
import json
import re

from ai_config import get_client, call_ai
from ai_context_fetcher import fetch_all_issues_context

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

current_dir = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.normpath(os.path.join(current_dir, "..", "backend", "json_reports"))

def run_ai_dependency_builder():
    print(f"\n{'='*50}\nSTARTING AI DEPENDENCY DISCOVERY\n{'='*50}")

    client = get_client()
    if not client: return

    # Load the base dependency graph
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

    # Load source code using the context fetcher
    bundles = fetch_all_issues_context()
    if not bundles:
        print("  -> [SKIP] No file context/source code found.")
        return

    # Prepare payload
    file_map = dep_graph.get("file_map", {})
    files_payload = []
    
    for b in bundles:
        fid = str(b["file_id"])
        if fid in file_map:
            source = b.get("source_code", "")
            # Token reduction: AI only needs to see dependencies/imports to map the architecture.
            lines = source.split('\n')
            vital_lines = [l.strip() for l in lines if re.search(r'(import |from |require\(|components:|export |<template|<script|<[A-Z])', l, re.IGNORECASE)]
            
            summary = "\n".join(vital_lines[:15]) 
            if not summary.strip(): summary = source[:200]
            
            files_payload.append({
                "file_id": fid,
                "file_name": b["file_name"],
                "arch_footprint": summary
            })

    if not files_payload:
        print("  -> [SKIP] Could not match files with source code.")
        return

    print("  -> [AI] Discovering deep architectural connections (Batched mode)...")
    
    global_file_list = [{"id": f["file_id"], "name": f["file_name"]} for f in files_payload]
    BATCH_SIZE = 25
    chunks = [files_payload[i:i + BATCH_SIZE] for i in range(0, len(files_payload), BATCH_SIZE)]
    
    existing_connections = dep_graph.get("connections", [])
    updated_connections = list(existing_connections)
    # Track existing pairs to prevent duplicates
    existing_pairs = set(f"{c['from_id']}-{c['to_id']}" for c in existing_connections)
    valid_count = 0

    for idx, chunk in enumerate(chunks):
        print(f"  -> [BATCH {idx+1}/{len(chunks)}] Tracking dependencies for {len(chunk)} files...")
        
        prompt = f"""Examine these {len(chunk)} source files and identify EVERY file-to-file relationship.

TYPES OF CONNECTIONS TO FIND:
1. DIRECT IMPORTS: import X from './Y'
2. VUE COMPONENTS: Usage like <MyComponent /> in templates
3. STORE/PLUGINS: Usage of this.$store, imports from @/store or @/plugins
4. BUS/EVENT EMITTERS: Event emission/consumption patterns

ONLY create connections where the `to_id` exists in this global project list:
{json.dumps(global_file_list, indent=2)}

RESPONSE SCHEMA (Strict JSON):
{{
  "connections": [
    {{
      "from_id": "source_file_id",
      "to_id": "target_file_id", 
      "name": "Dependency description",
      "type": "import | component_tag | state_usage | logical"
    }}
  ]
}}

FILES SOURCE CODE FOR THIS BATCH:
{json.dumps(chunk, indent=2)}"""

        try:
            response_text, model_used = call_ai(client, prompt, json_mode=True, max_retries=2)
            print(f"  -> [AI ENGINE] Model: {model_used}")
            
            parsed = json.loads(response_text)
            if isinstance(parsed, list) and len(parsed) > 0:
                parsed = parsed[0]
                
            new_connections = parsed.get("connections", []) if isinstance(parsed, dict) else []
            
            for conn in new_connections:
                from_id = str(conn.get("from_id"))
                to_id = str(conn.get("to_id"))
                
                if from_id in file_map and to_id in file_map:
                    pair_key = f"{from_id}-{to_id}"
                    if pair_key not in existing_pairs:
                        updated_connections.append({
                            "from_id": int(from_id),
                            "to_id": int(to_id),
                            "name": conn.get("name", "Unknown"),
                            "type": conn.get("type", "import")
                        })
                        existing_pairs.add(pair_key)
                        valid_count += 1
        except Exception as e:
            print(f"  -> [ERROR] Batch {idx+1} failed: {e}")
            if "Authentication" in str(e) or "quota" in str(e).lower():
                break

    dep_graph["connections"] = updated_connections
    
    # Recalculate impact_map
    impact_map = {}
    for fid in file_map.keys():
        impact_map[fid] = []
        
    for conn in updated_connections:
        f_id = str(conn["from_id"])
        t_id = str(conn["to_id"])
        if t_id in impact_map and int(f_id) not in impact_map[t_id]:
            impact_map[t_id].append(int(f_id))
            
    dep_graph["impact_map"] = impact_map

    with open(graph_path, "w", encoding="utf-8") as f:
        json.dump(dep_graph, f, indent=4)
        
    print(f"  -> [SUCCESS] AI Graph Builder updated. Total connections: {len(updated_connections)} ({valid_count} new).")

if __name__ == "__main__":
    run_ai_dependency_builder()
