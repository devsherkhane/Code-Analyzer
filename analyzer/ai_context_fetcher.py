import os
import json

def fetch_global_design_context(base_dir):
    """
    Scans the project for design-related configuration files and variables.
    """
    design_context = {
        "tailwind_config": None,
        "css_variables": [],
        "theme_configs": []
    }
    
    # Search for common config files    
    potential_configs = [
        "tailwind.config.js", "tailwind.config.ts", "tailwind.config.cjs",
        "postcss.config.js", "vite.config.js", "vite.config.ts"
    ]
    
    for root, dirs, files in os.walk(base_dir):
        if 'node_modules' in dirs:
            dirs.remove('node_modules')
        if '.git' in dirs:
            dirs.remove('.git')
            
        for f in files:
            # Check for Tailwind/Vite configs
            if f in potential_configs:
                try:
                    with open(os.path.join(root, f), 'r', encoding='utf-8') as cf:
                        design_context["theme_configs"].append({
                            "file": f,
                            "content": cf.read()[:2000] # Cap to save tokens
                        })
                except: pass
            
            # Check for CSS variable files
            if f.endswith(('.css', '.scss')) and ('variable' in f.lower() or 'theme' in f.lower() or 'base' in f.lower()):
                try:
                    with open(os.path.join(root, f), 'r', encoding='utf-8') as cf:
                        design_context["css_variables"].append({
                            "file": f,
                            "content": cf.read()[:2000]
                        })
                except: pass
                
    return design_context

def fetch_all_issues_context(db_conn=None):
    """
    Fetches all UI/UX and architectural issues from the local JSON reports
    and bundles them with the source code of the affected files.
    """
    
    # Path to the json_reports directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_dir = os.path.join(base_dir, "backend", "json_reports")
    
    if not os.path.exists(json_dir):
        json_dir = os.path.join(os.getcwd(), "json_reports")
        if not os.path.exists(json_dir):
            json_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "json_reports")

    def load_json(filename):
        filepath = os.path.join(json_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                try:
                    return json.load(f)
                except:
                    return {}
        return {}

    # 1. Get all files and dependency info
    files_data = load_json("files.json")
    if isinstance(files_data, list):
        files = files_data
    else:
        files = files_data.get("files", []) if isinstance(files_data, dict) else []

    dep_graph = load_json("dependency_graph.json")
    impact_map = dep_graph.get("impact_map", {})
    
    # 2. Get Global Design Context
    global_design_context = fetch_global_design_context(base_dir)
    
    context_bundles = []
    
    for file_record in files:
        file_id = str(file_record.get('file_id', file_record.get('id')))
        file_path = file_record.get('path', file_record.get('file_path'))
        file_name = file_record.get('file_name')
        
        issues = []
        is_frontend = file_name.lower().endswith(('.vue', '.js', '.ts', '.tsx', '.jsx', '.html'))
        
        if is_frontend:
            source_code = ""
            try:
                candidates = [
                    file_path,
                    os.path.join(base_dir, file_path) if file_path else None,
                    os.path.join(base_dir, "backend", file_path) if file_path else None
                ]
                
                found_path = None
                for cand in candidates:
                    if cand and os.path.exists(cand):
                        found_path = cand
                        break
                        
                # Dynamic Fallback: search workspace recursively by file_name if path is mismatched/outdated
                if not found_path and file_name:
                    for root, dirs, files_in_dir in os.walk(base_dir):
                        if 'node_modules' in dirs:
                            dirs.remove('node_modules')
                        if '.git' in dirs:
                            dirs.remove('.git')
                        if file_name in files_in_dir:
                            found_path = os.path.join(root, file_name)
                            break
                            
                if found_path:
                    with open(found_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        source_code = "".join([f"{i+1}: {line}" for i, line in enumerate(lines)])
                else:
                    raw_content = file_record.get('metrics', {}).get('content', '')
                    if raw_content:
                        lines = raw_content.splitlines(True)
                        source_code = "".join([f"{i+1}: {line}" for i, line in enumerate(lines)])
                    else:
                        source_code = f"Error reading file {file_path}: File not found"
            except Exception as e:
                source_code = f"Error reading file {file_path}: {e}"
                
            context_bundles.append({
                "file_id": file_id,
                "file_path": file_path,
                "file_name": file_name,
                "issues": issues,
                "source_code": source_code,
                "context": file_record.get("context", {}),
                "metrics": file_record.get("metrics", {}),
                "ast_data": file_record.get("ast_data", {}),
                "dependency_impact": impact_map.get(file_id, []),
                "downstream_impact": impact_map.get(file_id, []),
                "global_design_context": global_design_context
            })
            
    # Return all frontend file bundles (not just .vue)
    return context_bundles

if __name__ == "__main__":
    bundles = fetch_all_issues_context()
    print(f"Fetched context for {len(bundles)} files.")
    if bundles:
        print(f"Sample - {bundles[0]['file_name']} source length: {len(bundles[0]['source_code'])}")
