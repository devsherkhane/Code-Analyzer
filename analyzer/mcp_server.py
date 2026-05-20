"""
mcp_server.py — PrismAI MCP Server

Exposes codebase analysis data (AST, metrics, dependencies, AI reports)
as queryable MCP tools. Any MCP-compatible client (Claude Desktop, VS Code,
custom scripts) can connect and query the analyzed codebase.

Transports:
  - stdio  (default): python mcp_server.py
  - http:  python mcp_server.py --http --port 8892
"""

import os
import sys
import json
import fnmatch
import argparse

# Ensure analyzer dir is in path
_this_dir = os.path.dirname(os.path.abspath(__file__))
if _this_dir not in sys.path:
    sys.path.insert(0, _this_dir)

from mcp.server.fastmcp import FastMCP
from mcp_index_builder import (
    load_mcp_index,
    build_mcp_index,
    search_semantic_index,
    get_blast_radius as build_blast_radius,
)

# Load env
try:
    from dotenv import load_dotenv
    _root_env = os.path.normpath(os.path.join(_this_dir, "..", ".env"))
    if os.path.exists(_root_env):
        load_dotenv(_root_env, override=True)
    else:
        load_dotenv()
except ImportError:
    pass

# ============================================================
# SERVER INIT
# ============================================================
mcp = FastMCP(
    "PrismAI",
    instructions=(
        "PrismAI Code Analyzer MCP Server. "
        "Query codebase structure, AST data, metrics, dependencies, "
        "and AI analysis reports for scanned projects."
    ),
)

# Singleton index — loaded once, cached in memory
_index_cache = None

JSON_REPORTS_DIR = os.path.normpath(os.path.join(_this_dir, "..", "backend", "json_reports"))
BACKEND_DIR = os.path.normpath(os.path.join(_this_dir, "..", "backend"))


def _get_index():
    """Load or build the MCP index (cached in memory)."""
    global _index_cache
    if _index_cache is None:
        _index_cache = load_mcp_index()
        if _index_cache is None:
            print("[MCP] Index not found, building from JSON reports...")
            _index_cache = build_mcp_index()
    return _index_cache


def _reload_index():
    """Force-reload the index from disk (after a new scan)."""
    global _index_cache
    _index_cache = None
    return _get_index()


# ============================================================
# TOOLS
# ============================================================

@mcp.tool()
def list_files(filter: str = "") -> list:
    """List all analyzed files. Optionally filter by glob pattern (e.g. '*.vue', 'components/*')."""
    index = _get_index()
    files = []
    for fid, data in index["by_id"].items():
        fname = data["file_name"]
        fpath = data.get("path", "")
        if filter and not fnmatch.fnmatch(fname, filter) and not fnmatch.fnmatch(fpath, f"*{filter}*"):
            continue
        files.append({
            "file_id": fid,
            "file_name": fname,
            "path": fpath,
            "extension": os.path.splitext(fname)[1],
        })
    return files


@mcp.tool()
def get_file_detail(file_name: str = "", file_id: str = "") -> dict:
    """Get full AST data, metrics, imports, exports, and context for a specific file. Provide file_name or file_id."""
    index = _get_index()
    if file_id:
        result = index["by_id"].get(str(file_id))
        if result:
            return result
    if file_name:
        result = index["by_name"].get(file_name)
        if result:
            return result if isinstance(result, dict) else result[0]
    return {"error": f"File not found: file_name='{file_name}', file_id='{file_id}'"}


@mcp.tool()
def get_file_source(file_name: str = "", file_id: str = "", max_lines: int = 500, offset: int = 0) -> dict:
    """Get numbered source code for a file with pagination. Returns lines, total count, and has_more flag."""
    index = _get_index()
    file_data = None
    if file_id:
        file_data = index["by_id"].get(str(file_id))
    if not file_data and file_name:
        file_data = index["by_name"].get(file_name)
        if isinstance(file_data, list):
            file_data = file_data[0]
    if not file_data:
        return {"error": "File not found"}

    file_path = file_data.get("path", "")
    
    # Try the stored path first, then fall back to alternative locations
    resolved_path = None
    if file_path and os.path.exists(file_path):
        resolved_path = file_path
    else:
        # Fallback: try resolving relative to common project directories
        file_name = file_data.get("file_name", "")
        fallback_dirs = [
            JSON_REPORTS_DIR,
            os.path.join(_this_dir, "temp"),
            os.path.join(_this_dir, "temp_5_vues"),
        ]
        for base in fallback_dirs:
            candidate = os.path.join(base, file_name)
            if os.path.exists(candidate):
                resolved_path = candidate
                break
    
    if not resolved_path:
        return {
            "error": f"Source file not on disk: {file_path}. The temp directory may have been cleaned up. Re-run the analysis pipeline to rebuild the index.",
            "file_name": file_data.get("file_name")
        }

    try:
        with open(resolved_path, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
        numbered = [f"{i+1}: {line.rstrip()}" for i, line in enumerate(all_lines)]
        page = numbered[offset:offset + max_lines]
        return {
            "file_name": file_data["file_name"],
            "total_lines": len(all_lines),
            "offset": offset,
            "lines_returned": len(page),
            "has_more": offset + max_lines < len(all_lines),
            "source": "\n".join(page),
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_dependency_graph(file_id: str = "") -> dict:
    """Get the full dependency graph, or the impact map for a specific file."""
    index = _get_index()
    dep_graph = index.get("dependency_graph", {})
    if not file_id:
        return dep_graph
    impact = dep_graph.get("impact_map", {}).get(str(file_id), [])
    file_map = dep_graph.get("file_map", {})
    file_info = file_map.get(str(file_id), {})
    connections = [c for c in dep_graph.get("connections", [])
                   if str(c.get("from_id")) == str(file_id) or str(c.get("to_id")) == str(file_id)]
    return {
        "file_id": file_id,
        "file_info": file_info,
        "connections": connections,
        "dependents": impact,
        "is_circular": file_info.get("is_circular", False),
    }


@mcp.tool()
def get_folder_structure() -> dict:
    """Get the project folder tree with file counts per folder."""
    index = _get_index()
    folders = index.get("by_folder", {})
    tree = {}
    for folder_path, file_names in folders.items():
        tree[folder_path] = {
            "file_count": len(file_names),
            "files": file_names,
        }
    return {"total_folders": len(tree), "folders": tree}


@mcp.tool()
def search_by_symbol(symbol: str) -> list:
    """Find all files that define or import a given function, component, or variable name."""
    index = _get_index()
    sym_data = index.get("symbol_index", {}).get(symbol)
    if not sym_data:
        close = [s for s in index.get("symbol_index", {}) if symbol.lower() in s.lower()][:10]
        return {"error": f"Symbol '{symbol}' not found", "suggestions": close}
    results = []
    for fid in sym_data.get("defined_in", []):
        fd = index["by_id"].get(str(fid), {})
        results.append({"file_id": str(fid), "file_name": fd.get("file_name", "?"), "role": "defines"})
    for fid in sym_data.get("imported_by", []):
        fd = index["by_id"].get(str(fid), {})
        results.append({"file_id": str(fid), "file_name": fd.get("file_name", "?"), "role": "imports"})
    return results


@mcp.tool()
def search_semantic(query: str, top_k: int = 5) -> list:
    """Find the most semantically relevant files for a bug, feature, or symbol description."""
    index = _get_index()
    return search_semantic_index(index, query=query, top_k=top_k)


@mcp.tool()
def get_blast_radius(file_id: str, depth: int = 1) -> dict:
    """Get downstream dependents and upstream dependencies for a file."""
    index = _get_index()
    return build_blast_radius(index, file_id=file_id, depth=depth)


@mcp.tool()
def get_api_calls(file_id: str = "") -> list:
    """Get all API calls found in the project, or for a specific file."""
    index = _get_index()
    all_apis = index.get("api_calls", [])
    if file_id:
        return [a for a in all_apis if str(a.get("file_id")) == str(file_id)]
    return all_apis


@mcp.tool()
def get_ai_report(file_id: str = "") -> dict:
    """Get the latest AI analysis report. Optionally filter to a specific file."""
    report_path = os.path.join(BACKEND_DIR, "ai_report.json")
    if not os.path.exists(report_path):
        return {"error": "AI report not found. Run the analysis pipeline first."}
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
        if not file_id:
            return report
        for fr in report.get("files", []):
            if str(fr.get("file_id")) == str(file_id):
                return fr
        return {"error": f"File {file_id} not found in AI report"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_architecture() -> dict:
    """Get the AI-generated architecture analysis (layers, macro trends, workflows)."""
    arch_path = os.path.join(BACKEND_DIR, "ai_architecture.json")
    if not os.path.exists(arch_path):
        return {"error": "Architecture report not found. Run the analysis pipeline first."}
    try:
        with open(arch_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_metrics_summary() -> dict:
    """Get aggregated metrics across the entire project (LOC, complexity, file types, etc.)."""
    index = _get_index()
    return index.get("metrics_summary", {})


@mcp.tool()
def reload_index() -> dict:
    """Force reload the MCP index after a new scan. Call this after running the analysis pipeline."""
    idx = _reload_index()
    return {
        "status": "reloaded",
        "file_count": idx["project"]["file_count"],
        "built_at": idx["built_at"],
    }


# ============================================================
# RESOURCES (read-only data endpoints)
# ============================================================

@mcp.resource("prismai://project/overview")
def project_overview() -> str:
    """Project overview: name, file count, last scan timestamp."""
    index = _get_index()
    return json.dumps(index.get("project", {}), indent=2)


@mcp.resource("prismai://files")
def all_files_resource() -> str:
    """List of all analyzed files with basic metadata."""
    index = _get_index()
    files = [{"file_id": d["file_id"], "file_name": d["file_name"], "path": d["path"]}
             for d in index["by_id"].values()]
    return json.dumps(files, indent=2)


@mcp.resource("prismai://dependencies")
def dependencies_resource() -> str:
    """Full project dependency graph."""
    index = _get_index()
    return json.dumps(index.get("dependency_graph", {}), indent=2)


@mcp.resource("prismai://metrics")
def metrics_resource() -> str:
    """Aggregated project metrics."""
    index = _get_index()
    return json.dumps(index.get("metrics_summary", {}), indent=2)


# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PrismAI MCP Server")
    parser.add_argument("--http", action="store_true", help="Run with HTTP transport")
    parser.add_argument("--port", type=int, default=int(os.environ.get("MCP_SERVER_PORT", 8892)))
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()

    if args.http:
        # FastMCP v1.27+ requires host/port in constructor
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        print(f"[MCP] Starting PrismAI MCP Server (HTTP) on {args.host}:{args.port}")
        mcp.run(transport="streamable-http")
    else:
        print("[MCP] Starting PrismAI MCP Server (stdio)")
        mcp.run(transport="stdio")
