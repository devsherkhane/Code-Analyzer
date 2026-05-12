"""Quick smoke test for all MCP server tools."""
import sys
import json
sys.path.insert(0, ".")

from mcp_server import (
    list_files, get_file_detail, get_file_source, get_dependency_graph,
    get_folder_structure, search_by_symbol, get_api_calls, get_ai_report,
    get_architecture, get_metrics_summary, reload_index
)

def test(name, result):
    ok = not (isinstance(result, dict) and "error" in result)
    status = "PASS" if ok else "FAIL"
    if isinstance(result, list):
        print(f"  [{status}] {name}: {len(result)} items")
    elif isinstance(result, dict):
        print(f"  [{status}] {name}: {list(result.keys())[:5]}")
    else:
        print(f"  [{status}] {name}: {type(result)}")

print("=" * 50)
print("MCP SERVER TOOL SMOKE TEST")
print("=" * 50)

# 1. list_files
files = list_files()
test("list_files()", files)

files_vue = list_files(filter="*.vue")
test("list_files(*.vue)", files_vue)

# 2. get_file_detail
if files:
    detail = get_file_detail(file_name=files[0]["file_name"])
    test("get_file_detail(name)", detail)
    detail2 = get_file_detail(file_id=files[0]["file_id"])
    test("get_file_detail(id)", detail2)

# 3. get_file_source
if files:
    source = get_file_source(file_id=files[0]["file_id"], max_lines=10)
    test("get_file_source(10 lines)", source)
    if isinstance(source, dict) and "source" in source:
        print(f"         -> {source['total_lines']} total lines, has_more={source['has_more']}")

# 4. get_dependency_graph
graph = get_dependency_graph()
test("get_dependency_graph()", graph)

if files:
    file_graph = get_dependency_graph(file_id=files[0]["file_id"])
    test("get_dependency_graph(file)", file_graph)

# 5. get_folder_structure
folders = get_folder_structure()
test("get_folder_structure()", folders)

# 6. search_by_symbol
symbols = search_by_symbol(symbol="default")
test("search_by_symbol(default)", symbols)

# 7. get_api_calls
apis = get_api_calls()
test("get_api_calls()", apis)

# 8. get_ai_report
report = get_ai_report()
test("get_ai_report()", report)

# 9. get_architecture
arch = get_architecture()
test("get_architecture()", arch)

# 10. get_metrics_summary
metrics = get_metrics_summary()
test("get_metrics_summary()", metrics)
print(f"         -> LOC={metrics.get('total_loc')}, files={metrics.get('total_files')}, avg_cyc={metrics.get('avg_cyclomatic_complexity')}")

# 11. reload_index
reloaded = reload_index()
test("reload_index()", reloaded)

print("\n" + "=" * 50)
print("ALL TOOLS TESTED")
print("=" * 50)
