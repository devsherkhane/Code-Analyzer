import os

def resolve_path(current_file_path, import_source, project_root):
    """
    Resolves a relative or aliased import path to an absolute file path.
    Handles standard Node.js/Vue resolutions (.vue, .js, .ts, /index) and @/ alias.
    """
    # Handle @/ alias common in Vue/Vite (points to src/)
    if import_source.startswith('@/'):
        src_dir = os.path.join(project_root, 'src')
        if not os.path.isdir(src_dir):
            src_dir = project_root # Fallback to root if src doesn't exist
        potential_path = os.path.normpath(os.path.join(src_dir, import_source[2:]))
    elif import_source.startswith('.'):
        base_dir = os.path.dirname(current_file_path)
        potential_path = os.path.normpath(os.path.join(base_dir, import_source))
    else:
        # Skip node_modules
        return None
    
    # Extensions to check
    extensions = ['', '.vue', '.ts', '.js', '/index.vue', '/index.ts', '/index.js']
    
    # Check potential path + extensions
    for ext in extensions:
        full_path = potential_path + ext
        if os.path.isfile(full_path):
            return os.path.abspath(full_path)
            
    return None

def build_dependency_graph(files_table, project_root):
    """
    Constructs a project-wide dependency graph from extracted AST data.
    Returns a unified graph structure.
    """
    graph = {
        "connections": [], # List of {from_id, to_id, imported_names}
        "file_map": {},    # Map of ID to file info
        "impact_map": {}   # Map of ID to list of dependent IDs (who depends on me)
    }

    # 1. Create a lookup by absolute path
    path_to_id = {}
    for f in files_table:
        abs_path = os.path.abspath(f["path"])
        path_to_id[abs_path] = f["file_id"]
        graph["file_map"][f["file_id"]] = {
            "name": f["file_name"],
            "path": f["path"],
            "exports": f.get("exports", [])
        }
        graph["impact_map"][f["file_id"]] = []

    # 2. Resolve every import
    for f in files_table:
        current_id = f["file_id"]
        current_path = os.path.abspath(f["path"])
        imports = f.get("imports", [])
        
        # Track unique connections from this file
        seen_targets = set()

        for imp in imports:
            try:
                source_path = imp["source"]
                resolved_abs_path = resolve_path(current_path, source_path, project_root)
                
                if resolved_abs_path and resolved_abs_path in path_to_id:
                    target_id = path_to_id[resolved_abs_path]
                    
                    if target_id != current_id:
                        graph["connections"].append({
                            "from_id": current_id,
                            "to_id": target_id,
                            "name": imp["name"],
                            "type": imp["type"]
                        })
                        
                        if current_id not in graph["impact_map"][target_id]:
                            graph["impact_map"][target_id].append(current_id)
            except Exception as e:
                print(f"  -> [RESOLVE ERROR] Could not resolve {imp.get('source')} in {f['file_name']}: {e}")

    # 3. Detect Circular Dependencies (DFS)
    def find_cycles(adj):
        visited = set()
        on_stack = set()
        cycles = []

        def dfs(u, path):
            visited.add(u)
            on_stack.add(u)
            path.append(u)

            for v in adj.get(u, []):
                if v in on_stack:
                    # Found a cycle
                    idx = path.index(v)
                    cycles.append(path[idx:])
                elif v not in visited:
                    dfs(v, path)

            on_stack.remove(u)
            path.pop()

        for node in adj:
            if node not in visited:
                dfs(node, [])
        return cycles

    # Build adjacency list for cycle detection
    adj = {}
    for conn in graph["connections"]:
        u = conn["from_id"]
        v = conn["to_id"]
        if u not in adj: adj[u] = []
        adj[u].append(v)

    all_cycles = find_cycles(adj)
    graph["cycles"] = all_cycles
    
    # Mark nodes as circular
    circular_nodes = set()
    for cycle in all_cycles:
        for node_id in cycle:
            circular_nodes.add(node_id)
            if node_id in graph["file_map"]:
                graph["file_map"][node_id]["is_circular"] = True

    return graph
