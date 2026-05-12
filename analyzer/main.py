import sys
import os
import subprocess
import traceback 

# Ensure local imports resolve regardless of how this script is invoked
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scanner import scan_folder
from script_parser import parse_source
from metrics_extractor import get_metrics
from storage import JSONStorage
from dependency_graph import build_dependency_graph

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_zip_or_file>")
        return

    path = sys.argv[1]
    print(f"[START] Analyzing workspace: {path}")

    # 1. Initialize Storage
    db = JSONStorage()
    
    project_name = os.path.basename(os.path.normpath(path))
    pid = db.insert_project(project_name)

    # 2. Scan folder
    files, folders = scan_folder(path)
    
    folder_id_map = {}
    folder_id_map[path] = db.insert_folder(pid, os.path.basename(path), path)
    for f_path in folders:
        folder_id_map[f_path] = db.insert_folder(pid, os.path.basename(f_path), f_path)

    # 3. Process files
    for file_path in files:
        f_id = folder_id_map.get(os.path.dirname(file_path), folder_id_map[path])
        
        is_frontend = file_path.lower().endswith(('.vue', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.scss'))

        if is_frontend:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Parse AST
                ast_data = parse_source(content, file_path)
                
                # Get metrics
                metrics = get_metrics(file_path, ast_data if ast_data else {})

                # Extract imports/exports from AST
                imports = ast_data.get('imports', []) if ast_data else []
                exports = ast_data.get('exports', []) if ast_data else []

                # Insert file
                current_file_id = db.insert_file(
                    f_id, 
                    os.path.basename(file_path), 
                    file_path,
                    imports=imports,
                    exports=exports,
                    metrics=metrics,
                    ast_data=ast_data if ast_data else {}
                )
                
                # API calls
                api_calls = ast_data.get('api_calls', []) if ast_data else []
                for api in api_calls:
                    db.insert_api_call(current_file_id, api.get('method', 'GET'), api.get('url', ''), api.get('payload', ''))

            except Exception as e:
                print(f"  -> [WARNING] Failed to parse {os.path.basename(file_path)}: {e}")

    # 4. Consistency checks
    db.run_consistency_check()

    # 5. Build static dependency graph (imports-based)
    try:
        db.tables["dependency_graph"] = build_dependency_graph(db.tables["files"], path)
    except Exception as e:
        print(f"  -> [WARNING] Failed to build dependency graph: {e}")

    # 6. Export JSON
    db.export_all()
    print("\n[SUCCESS] Extracted project data and saved JSON reports.")

    # 7. Run AI Pipeline
    script_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        print("\n[PIPELINE] Running AI Dependency Builder...")
        subprocess.run([sys.executable, os.path.join(script_dir, "ai_dependency_builder.py")], check=True)
        
        print("\n[PIPELINE] Running AI Architecture Analyzer...")
        subprocess.run([sys.executable, os.path.join(script_dir, "ai_architecture_analyzer.py")], check=True)
        
        print("\n[PIPELINE] Running AI Reporter...")
        subprocess.run([sys.executable, os.path.join(script_dir, "ai_reporter.py")], check=True)
        
        print("\n[PIPELINE] Building MCP Index...")
        subprocess.run([sys.executable, os.path.join(script_dir, "mcp_index_builder.py")], check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"\n[CRITICAL ERROR] AI Pipeline failed with exit status {e.returncode}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[CRITICAL ERROR] Pipeline crashed: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
