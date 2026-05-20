"""
mcp_index_builder.py — Builds an optimized, queryable index from PrismAI's
JSON analysis reports for the MCP server.

Reads: files.json, dependency_graph.json, components.json, api_calls.json
Writes: mcp_index.json (O(1) lookups by ID, name, folder, symbol)
"""

import os
import json
import math
import re
from datetime import datetime
from collections import defaultdict

_this_dir = os.path.dirname(os.path.abspath(__file__))
JSON_REPORTS_DIR = os.path.normpath(os.path.join(_this_dir, "..", "backend", "json_reports"))
MCP_INDEX_PATH = os.path.join(JSON_REPORTS_DIR, "mcp_index.json")
SEMANTIC_VECTOR_SIZE = 128
_EMBEDDING_MODEL = None
_EMBEDDING_BACKEND = None


def _load_json(filename):
    filepath = os.path.join(JSON_REPORTS_DIR, filename)
    if not os.path.exists(filepath):
        return [] if filename != "dependency_graph.json" else {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"  -> [MCP INDEX] Warning: Failed to load {filename}: {e}")
        return [] if filename != "dependency_graph.json" else {}


def _build_symbol_index(files_data):
    symbol_index = defaultdict(lambda: {"defined_in": [], "imported_by": []})
    for file_record in files_data:
        fid = file_record.get("file_id", file_record.get("id"))
        if fid is None:
            continue
        fid = int(fid)
        for exp in file_record.get("exports", []):
            name = exp.get("name", "") if isinstance(exp, dict) else str(exp)
            if name and name != "default" and fid not in symbol_index[name]["defined_in"]:
                symbol_index[name]["defined_in"].append(fid)
        for imp in file_record.get("imports", []):
            name = imp.get("name", "") if isinstance(imp, dict) else str(imp)
            if name and name != "default" and fid not in symbol_index[name]["imported_by"]:
                symbol_index[name]["imported_by"].append(fid)
        ast_data = file_record.get("ast_data", {})
        for comp_name in ast_data.get("registered_components", []):
            if comp_name and fid not in symbol_index[comp_name]["defined_in"]:
                symbol_index[comp_name]["defined_in"].append(fid)
        for comp_name in ast_data.get("imported_components", []):
            if comp_name and fid not in symbol_index[comp_name]["imported_by"]:
                symbol_index[comp_name]["imported_by"].append(fid)
    return dict(symbol_index)


def _build_folder_index(files_data):
    folder_index = defaultdict(list)
    for file_record in files_data:
        file_path = file_record.get("path", "")
        file_name = file_record.get("file_name", "")
        if file_path:
            folder = os.path.dirname(file_path).replace("\\", "/")
            if file_name not in folder_index[folder]:
                folder_index[folder].append(file_name)
    return dict(folder_index)


def _build_file_lookups(files_data):
    by_id = {}
    by_name = {}
    for file_record in files_data:
        fid = str(file_record.get("file_id", file_record.get("id", "")))
        file_name = file_record.get("file_name", "")
        semantic_text = _build_semantic_text(file_record)
        entry = {
            "file_id": fid,
            "file_name": file_name,
            "path": file_record.get("path", ""),
            "folder_id": file_record.get("folder_id"),
            "imports": file_record.get("imports", []),
            "exports": file_record.get("exports", []),
            "metrics": file_record.get("metrics", {}),
            "ast_data": file_record.get("ast_data", {}),
            "context": file_record.get("context", {}),
            "semantic_text": semantic_text,
            "semantic_vector": _compute_semantic_vector(semantic_text),
        }
        by_id[fid] = entry
        if file_name in by_name:
            existing = by_name[file_name]
            if isinstance(existing, dict):
                by_name[file_name] = [existing, entry]
            elif isinstance(existing, list):
                existing.append(entry)
        else:
            by_name[file_name] = entry
    return by_id, by_name


def _tokenize(text):
    return re.findall(r"[A-Za-z_][A-Za-z0-9_]{1,}", (text or "").lower())


def _build_semantic_text(file_record):
    metrics = file_record.get("metrics", {}) or {}
    ast_data = file_record.get("ast_data", {}) or {}
    imports = file_record.get("imports", []) or []
    exports = file_record.get("exports", []) or []

    def _names(items):
        names = []
        for item in items:
            if isinstance(item, dict):
                names.extend([
                    str(item.get("name", "")),
                    str(item.get("source", "")),
                    str(item.get("type", "")),
                ])
            else:
                names.append(str(item))
        return [n for n in names if n]

    parts = [
        file_record.get("file_name", ""),
        file_record.get("path", ""),
        " ".join(_names(imports)),
        " ".join(_names(exports)),
        " ".join(ast_data.get("methods", []) or []),
        " ".join(ast_data.get("computed", []) or []),
        " ".join(ast_data.get("watchers", []) or []),
        " ".join(ast_data.get("registered_components", []) or []),
        " ".join(ast_data.get("imported_components", []) or []),
        str(metrics.get("content", ""))[:2000],
    ]
    return "\n".join([part for part in parts if part]).strip()


def _compute_semantic_vector(text, dims=SEMANTIC_VECTOR_SIZE):
    model = _get_embedding_model()
    if model is not None:
        try:
            vector = model.encode(text or "", normalize_embeddings=True)
            return [round(float(v), 6) for v in vector]
        except Exception:
            pass

    vector = [0.0] * dims
    for token in _tokenize(text):
        idx = hash(token) % dims
        vector[idx] += 1.0

    norm = math.sqrt(sum(v * v for v in vector))
    if norm:
        vector = [round(v / norm, 6) for v in vector]
    return vector


def _cosine_similarity(vec_a, vec_b):
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    return round(sum(a * b for a, b in zip(vec_a, vec_b)), 6)


def _get_embedding_model():
    global _EMBEDDING_MODEL, _EMBEDDING_BACKEND
    if _EMBEDDING_BACKEND is not None:
        return _EMBEDDING_MODEL

    _EMBEDDING_MODEL = None
    _EMBEDDING_BACKEND = "hashed-token-cosine"
    return _EMBEDDING_MODEL


def search_semantic_index(index, query, top_k=5, exclude_file_ids=None):
    query = (query or "").strip()
    if not query:
        return []

    exclude = {str(fid) for fid in (exclude_file_ids or [])}
    query_vector = _compute_semantic_vector(query)
    scored = []
    for fid, file_data in (index or {}).get("by_id", {}).items():
        if str(fid) in exclude:
            continue
        file_vector = file_data.get("semantic_vector")
        if not file_vector:
            fallback_text = file_data.get("semantic_text") or " ".join([
                file_data.get("file_name", ""),
                file_data.get("path", ""),
                " ".join((file_data.get("ast_data", {}) or {}).get("methods", [])[:20]),
            ])
            file_vector = _compute_semantic_vector(fallback_text)
        score = _cosine_similarity(query_vector, file_vector)
        if score <= 0:
            continue
        scored.append({
            "file_id": str(fid),
            "file_name": file_data.get("file_name", ""),
            "path": file_data.get("path", ""),
            "score": score,
        })
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:max(1, top_k)]


def get_blast_radius(index, file_id, depth=1):
    dep_graph = (index or {}).get("dependency_graph", {}) or {}
    impact_map = dep_graph.get("impact_map", {}) or {}
    file_map = dep_graph.get("file_map", {}) or {}
    connections = dep_graph.get("connections", []) or []
    target_id = str(file_id)
    max_depth = max(1, int(depth or 1))

    downstream = []
    visited = {target_id}
    frontier = [target_id]

    for level in range(max_depth):
        next_frontier = []
        for current in frontier:
            for dependent in impact_map.get(current, []):
                dep_id = str(dependent)
                if dep_id in visited:
                    continue
                visited.add(dep_id)
                next_frontier.append(dep_id)
                downstream.append({
                    "file_id": dep_id,
                    "file_name": file_map.get(dep_id, {}).get("name", ""),
                    "path": file_map.get(dep_id, {}).get("path", ""),
                    "depth": level + 1,
                })
        frontier = next_frontier
        if not frontier:
            break

    upstream = []
    for conn in connections:
        if str(conn.get("from_id")) == target_id:
            upstream_id = str(conn.get("to_id"))
            upstream.append({
                "file_id": upstream_id,
                "file_name": file_map.get(upstream_id, {}).get("name", ""),
                "path": file_map.get(upstream_id, {}).get("path", ""),
                "type": conn.get("type", "unknown"),
                "name": conn.get("name", ""),
            })

    return {
        "file_id": target_id,
        "file_name": file_map.get(target_id, {}).get("name", ""),
        "path": file_map.get(target_id, {}).get("path", ""),
        "downstream": downstream,
        "upstream_dependencies": upstream,
        "downstream_count": len(downstream),
    }


def _aggregate_metrics(by_id):
    total_files = len(by_id)
    total_loc = 0
    total_complexity = 0
    total_api_calls = 0
    total_methods = 0
    max_complexity = 0
    max_complexity_file = ""
    extensions = defaultdict(int)
    for fid, data in by_id.items():
        metrics = data.get("metrics", {})
        ast_data = data.get("ast_data", {})
        loc = metrics.get("loc", 0) or 0
        cyc = metrics.get("cyclomatic_complexity", 0) or 0
        total_loc += loc
        total_complexity += cyc
        total_api_calls += len(ast_data.get("api_calls", []))
        total_methods += len(ast_data.get("methods", []))
        if cyc > max_complexity:
            max_complexity = cyc
            max_complexity_file = data.get("file_name", "")
        ext = os.path.splitext(data.get("file_name", ""))[1].lower()
        if ext:
            extensions[ext] += 1
    return {
        "total_files": total_files,
        "total_loc": total_loc,
        "avg_cyclomatic_complexity": round(total_complexity / total_files, 2) if total_files > 0 else 0,
        "max_cyclomatic_complexity": max_complexity,
        "max_complexity_file": max_complexity_file,
        "total_api_calls": total_api_calls,
        "total_methods": total_methods,
        "file_types": dict(extensions),
    }


def build_mcp_index():
    """Main entry point. Reads JSON reports and builds a unified MCP index."""
    print("  -> [MCP INDEX] Loading JSON reports...")
    files_data = _load_json("files.json")
    dep_graph = _load_json("dependency_graph.json")
    components = _load_json("components.json")
    api_calls = _load_json("api_calls.json")
    projects = _load_json("projects.json")

    if isinstance(files_data, dict):
        files_data = files_data.get("files", [])

    project_name = "Unknown"
    if projects and isinstance(projects, list) and len(projects) > 0:
        project_name = projects[0].get("project_name", "Unknown")

    print(f"  -> [MCP INDEX] Indexing {len(files_data)} files...")
    by_id, by_name = _build_file_lookups(files_data)
    folder_index = _build_folder_index(files_data)
    symbol_index = _build_symbol_index(files_data)
    metrics_summary = _aggregate_metrics(by_id)

    index = {
        "version": "1.1",
        "built_at": datetime.now().isoformat(),
        "project": {
            "name": project_name,
            "file_count": len(files_data),
            "last_scan": datetime.now().isoformat(),
        },
        "semantic_config": {
            "vector_size": SEMANTIC_VECTOR_SIZE,
            "strategy": _EMBEDDING_BACKEND or "hashed-token-cosine",
        },
        "by_id": by_id,
        "by_name": by_name,
        "by_folder": folder_index,
        "symbol_index": symbol_index,
        "metrics_summary": metrics_summary,
        "dependency_graph": dep_graph,
        "components": components if isinstance(components, list) else [],
        "api_calls": api_calls if isinstance(api_calls, list) else [],
    }

    os.makedirs(JSON_REPORTS_DIR, exist_ok=True)
    with open(MCP_INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)

    print(f"  -> [MCP INDEX] Built: {len(by_id)} files, {len(symbol_index)} symbols, {len(folder_index)} folders")
    return index


def load_mcp_index():
    """Loads the pre-built MCP index from disk."""
    if not os.path.exists(MCP_INDEX_PATH):
        return None
    try:
        with open(MCP_INDEX_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


if __name__ == "__main__":
    print("=" * 50)
    print("MCP INDEX BUILDER — Standalone Mode")
    print("=" * 50)
    idx = build_mcp_index()
    if idx:
        print(f"\nProject: {idx['project']['name']}")
        print(f"Files: {idx['project']['file_count']}")
        print(f"Symbols: {len(idx['symbol_index'])}")
        print(f"Metrics: {json.dumps(idx['metrics_summary'], indent=2)}")
