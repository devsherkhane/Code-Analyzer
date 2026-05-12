import os
import json
import re

from ai_config import get_client, call_ai
from ai_context_fetcher import fetch_all_issues_context

try:
    from dependency_graph import build_dependency_graph
except Exception:
    build_dependency_graph = None

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

current_dir = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.normpath(os.path.join(current_dir, "..", "backend", "json_reports"))


def _load_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default


def _infer_project_root_from_files(files_data):
    candidates = []
    for fr in files_data:
        p = fr.get("path") or fr.get("file_path")
        if not p or not isinstance(p, str):
            continue
        norm = os.path.normpath(p)
        marker = os.sep + "src" + os.sep
        if marker in norm:
            candidates.append(norm.split(marker)[0])
    if not candidates:
        paths = [os.path.normpath(fr.get("path") or fr.get("file_path") or "") for fr in files_data]
        paths = [p for p in paths if p]
        if not paths:
            return os.path.normpath(os.path.join(current_dir, ".."))
        try:
            return os.path.commonpath(paths)
        except Exception:
            return os.path.dirname(paths[0])

    # pick most common root prefix
    freq = {}
    for c in candidates:
        freq[c] = freq.get(c, 0) + 1
    return max(freq.items(), key=lambda kv: kv[1])[0]

def run_ai_dependency_builder():
    print(f"\n{'='*50}\nSTARTING AI DEPENDENCY DISCOVERY\n{'='*50}")

    client = get_client()
    skip_llm = str(os.environ.get("PRISMAI_SKIP_LLM_DEPENDENCIES", "")).strip().lower() in {"1", "true", "yes", "on"}

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

    # If the graph is missing static import edges, rebuild them from files.json and merge.
    # This avoids "blank dependency panels" when only AI route edges exist.
    if build_dependency_graph is not None:
        try:
            existing_connections = dep_graph.get("connections", []) or []
            types = {c.get("type") for c in existing_connections if isinstance(c, dict)}
            looks_ai_only = (len(existing_connections) > 0 and types and types.issubset({"route_navigation"}))
            looks_empty = (len(existing_connections) == 0)

            files_path = os.path.join(CACHE_DIR, "files.json")
            files_data = _load_json(files_path, [])
            if isinstance(files_data, dict):
                files_data = files_data.get("files", [])

            if files_data and (looks_empty or looks_ai_only):
                project_root = _infer_project_root_from_files(files_data)
                static_graph = build_dependency_graph(files_data, project_root)

                dep_graph.setdefault("file_map", static_graph.get("file_map", {}))
                if not dep_graph.get("impact_map"):
                    dep_graph["impact_map"] = static_graph.get("impact_map", {})

                pair_keys = set()
                for c in existing_connections:
                    if isinstance(c, dict) and "from_id" in c and "to_id" in c:
                        pair_keys.add(f"{c['from_id']}-{c['to_id']}")

                merged = list(existing_connections)
                added = 0
                for c in static_graph.get("connections", []):
                    if not isinstance(c, dict):
                        continue
                    k = f"{c.get('from_id')}-{c.get('to_id')}"
                    if k and k not in pair_keys:
                        merged.append(c)
                        pair_keys.add(k)
                        added += 1

                if added:
                    dep_graph["connections"] = merged
                    print(f"  -> [STATIC] Added {added} import connection(s) (project_root={project_root})")
        except Exception as e:
            print(f"  -> [WARNING] Static dependency merge failed: {e}")

    # Load source code using the context fetcher
    bundles = fetch_all_issues_context()
    if not bundles:
        print("  -> [SKIP] No file context/source code found.")
        return

    # Prepare payload
    file_map = dep_graph.get("file_map", {})
    if not file_map:
        for b in bundles:
            file_map[str(b["file_id"])] = {
                "id": b["file_id"],
                "name": b["file_name"],
                "path": b["file_path"]
            }
        dep_graph["file_map"] = file_map
        
    files_payload = []
    
    existing_connections = dep_graph.get("connections", [])
    updated_connections = list(existing_connections)
    existing_pairs = set(f"{c['from_id']}-{c['to_id']}" for c in existing_connections)
    valid_count = 0

    # Normalize existing connections to the expected schema for downstream consumers
    for c in updated_connections:
        if not isinstance(c, dict):
            continue
        c.setdefault("type", "import")
        if "name" not in c:
            names = c.get("names", [])
            if isinstance(names, list) and names:
                c["name"] = f"Imports {', '.join([str(n) for n in names[:6]])}" + ("…" if len(names) > 6 else "")
            else:
                c["name"] = "Imports module"
    
    for b in bundles:
        fid = str(b["file_id"])
        if fid in file_map:
            source = b.get("source_code", "")
            # Token reduction: AI only needs to see dependencies/imports/routes to map the architecture.
            lines = source.split('\n')
            import_lines = [l.strip() for l in lines if re.search(r'^\s*(import\s|from\s+\S+\s+import\s|const\s+\S+\s*=\s*require\()', l, re.IGNORECASE)]
            router_lines = [l.strip() for l in lines if re.search(r'(\$router\.push|router-link|createRouter\(|routes\s*=)', l, re.IGNORECASE)]
            component_lines = [l.strip() for l in lines if re.search(r'(components\s*:\s*\{|<([A-Z][A-Za-z0-9_]*)\b)', l)]

            vital_lines = []
            vital_lines.extend(import_lines)
            vital_lines.extend(router_lines)
            vital_lines.extend(component_lines)

            # De-duplicate while keeping order
            seen = set()
            vital_lines = [l for l in vital_lines if not (l in seen or seen.add(l))]

            summary = "\n".join(vital_lines[:120])
            if not summary.strip(): summary = source[:300]
            
            # ==========================================
            # STATIC ROUTER DISCOVERY (100% Reliable)
            # ==========================================
            route_names = re.findall(r'(?:\$router\.push\s*\(\s*\{\s*name\s*:\s*|router-link[^>]*to=["\']|name:\s*)[\'"]([A-Za-z0-9_-]+)[\'"]', source)
            
            for r_name in route_names:
                target_file = next((f for f in dep_graph["file_map"].values() if f["name"].lower() == f"{r_name}.vue".lower() or f["name"].lower() == r_name.lower()), None)
                if target_file:
                    target_id = next(k for k,v in dep_graph["file_map"].items() if v == target_file)
                    if str(target_id) != str(fid):
                        pair_key = f"{fid}-{target_id}"
                        if pair_key not in existing_pairs:
                            updated_connections.append({
                                "from_id": int(fid),
                                "to_id": int(target_id),
                                "name": f"Router push to {r_name}",
                                "type": "route_navigation"
                            })
                            existing_pairs.add(pair_key)
                            valid_count += 1
                            print(f"  -> [STATIC] Found route connection: {b['file_name']} -> {target_file['name']}")

            files_payload.append({
                "file_id": fid,
                "file_name": b["file_name"],
                "arch_footprint": summary
            })

    if not files_payload:
        print("  -> [SKIP] Could not match files with source code.")
        return

    if skip_llm or not client:
        # We already updated static + router edges; skip the LLM phase.
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

        mode = "static/router only" if (skip_llm or not client) else "static/router only"
        print(f"  -> [SUCCESS] Dependency graph updated ({mode}). Total connections: {len(updated_connections)} ({valid_count} new).")
        return

    print("  -> [AI] Discovering deep architectural connections (Batched mode)...")
    
    global_file_list = [{"id": f["file_id"], "name": f["file_name"]} for f in files_payload]
    BATCH_SIZE = 25
    chunks = [files_payload[i:i + BATCH_SIZE] for i in range(0, len(files_payload), BATCH_SIZE)]

    for idx, chunk in enumerate(chunks):
        print(f"  -> [BATCH {idx+1}/{len(chunks)}] Tracking dependencies for {len(chunk)} files...")
        
        prompt = f"""Examine these {len(chunk)} source files and identify EVERY file-to-file relationship.

TYPES OF CONNECTIONS TO FIND:
1. DIRECT IMPORTS: import X from './Y'
2. VUE COMPONENTS: Usage like <MyComponent /> in templates
3. STORE/PLUGINS: Usage of this.$store, imports from @/store or @/plugins
4. VUE ROUTER: Navigation like this.$router.push({{name: 'ComponentName'}}) or <router-link to="...". Link to the file that matches the component name.
5. BUS/EVENT EMITTERS: Event emission/consumption patterns

ONLY create connections where the `to_id` exists in this global project list:
{json.dumps(global_file_list, indent=2)}

RESPONSE SCHEMA (Strict JSON):
{{
  "connections": [
    {{
      "from_id": "source_file_id",
      "to_id": "target_file_id", 
      "name": "Dependency description (e.g., Router push to FeeDetails)",
      "type": "import | component_tag | state_usage | logical | route_navigation"
    }}
  ]
}}

FILES SOURCE CODE FOR THIS BATCH:
{json.dumps(chunk, indent=2)}"""

        # ==========================================
        # AI DEPENDENCY DISCOVERY (Fallback / Deep)
        # ==========================================
        try:
            response_text, model_used = call_ai(client, prompt, json_mode=True, max_retries=4)
            print(f"  -> [AI ENGINE] Model: {model_used}")
            
            try:
                parsed = json.loads(response_text)
            except json.JSONDecodeError:
                json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response_text, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(1))
                else:
                    raise
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
        
    report_id = None
    report_path = os.path.normpath(os.path.join(CACHE_DIR, "..", "ai_report.json"))
    if os.path.exists(report_path):
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                full_report = json.load(f)
                report_id = full_report.get("report_id")
        except: pass
        
    if report_id:
        hist_graph_path = os.path.join(CACHE_DIR, f"dependency_graph_{report_id}.json")
        try:
            with open(hist_graph_path, "w", encoding="utf-8") as f:
                json.dump(dep_graph, f, indent=4)
        except Exception as e:
            print(f"  -> [WARNING] Failed to save historical dependency graph: {e}")

    print(f"  -> [SUCCESS] AI Graph Builder updated. Total connections: {len(updated_connections)} ({valid_count} new).")

if __name__ == "__main__":
    run_ai_dependency_builder()
