import sys
import os
import time
import traceback 
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from scanner import scan_folder
from extracter import extract_elements
from api_finder import find_apis
from metrics_extractor import get_metrics  
from utils import unzip, insert_project, insert_folder, insert_file, insert_component_data_v2
from storage import JSONStorage
from script_parser import parse_vue_script

def detect_routes(project_root):
    """Simple regex-based route detection for Vue/React."""
    routes = {}
    router_files = []
    for root, dirs, files in os.walk(project_root):
        if 'node_modules' in dirs: dirs.remove('node_modules')
        for f in files:
            if f in ['router.js', 'router.ts', 'routes.js', 'routes.ts', 'index.js', 'index.ts'] and ('router' in root or 'routes' in root):
                router_files.append(os.path.join(root, f))
    
    for rf in router_files:
        try:
            with open(rf, 'r', encoding='utf8') as f:
                content = f.read()
            
            # Use unified AST parser for route detection (regex-free)
            parsed = parse_vue_script(content)
            if parsed and parsed.get('routes'):
                routes.update(parsed['routes'])
        except Exception:
            pass
    return routes

def process_single_file(file_path, folder_id, project_id, storage):
    """Worker function to process a single file in parallel using unified AST."""
    try:
        file_name = os.path.basename(file_path)

        is_vue = file_path.lower().endswith('.vue')
        is_frontend = file_path.lower().endswith(('.vue', '.js', '.ts', '.html'))

        # --- Step A: Unified Node.js AST Parsing ---
        parsed_script = None
        metrics = {}
        if is_frontend:
            if is_vue or file_path.lower().endswith(('.js', '.ts')):
                try:
                    with open(file_path, 'r', encoding="utf8") as f:
                        script_content = f.read()
                    parsed_script = parse_vue_script(script_content)
                except Exception as e:
                    print(f"  -> [AST] Failed to parse script for {file_name}: {e}")

        if is_frontend:
            from metrics_extractor import get_metrics
            metrics = get_metrics(file_path, parsed_script)

        # Extract dependency data
        file_imports = parsed_script.get("imports", []) if parsed_script else []
        file_exports = parsed_script.get("exports", []) if parsed_script else []

        # Extract raw AST data for downstream AI fingerprinting
        ast_data = {}
        if parsed_script:
            ast_data = {
                "methods": parsed_script.get("methods", []),
                "computed": parsed_script.get("computed", []),
                "watchers": parsed_script.get("watchers", []),
                "api_calls": parsed_script.get("api_calls", []),
                "ui_elements": parsed_script.get("ui_elements", []),
                "imported_components": parsed_script.get("imported_components", []),
                "registered_components": parsed_script.get("registered_components", []),
                "imports": parsed_script.get("imports", []),
                "exports": parsed_script.get("exports", []),
                "props_definition": parsed_script.get("props_definition"),
                "emits_definition": parsed_script.get("emits_definition"),
                "style_metrics": parsed_script.get("style_metrics", {}),
                "template_metrics": parsed_script.get("template_metrics", {}),
                "script_metrics": parsed_script.get("script_metrics", {}),
            }

        # --- Step B: Data Storage ---
        current_file_id = insert_file(folder_id, file_path, storage, imports=file_imports, exports=file_exports, metrics=metrics, ast_data=ast_data)

        if is_frontend:
            print(f"  [PARALLEL] AST Analysis: {file_name}", flush=True)
            
            # --- Step C: Extraction & Metrics (100% AST Driven) ---
            ui_elements_ast = parsed_script.get("ui_elements", []) if parsed_script else []
            elements, components = extract_elements(ui_elements_ast)
            
            apis = find_apis(parsed_script)

            # --- Step C: Data Storage ---
            default_comp_id = insert_component_data_v2(
                current_file_id, components, elements, apis, storage
            )

            # --- Step D: Analysis ---
            # Local flagging and complexity analysis removed to rely strictly on AI

            print(f"  [SUCCESS] Finished: {file_name}", flush=True)
            return "scanned"
        
        return "skipped"

    except Exception as e:
        print(f"  [ERROR] Processing failed for {file_path}: {e}")
        return "error"

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_zip_or_file>")
        return

    # 1. Setup Environment
    try:
        zip_path = sys.argv[1]
        folder = unzip(zip_path)
        
        if not os.path.exists(folder) or not os.listdir(folder):
            print(f"  -> [ERROR] No files to analyze. Check the input path: {zip_path}")
            return

        project_name = os.path.basename(zip_path)
        os.environ["PROJECT_NAME"] = project_name
        
        storage = JSONStorage()
        pid = insert_project(project_name, storage)
    except Exception as e:
        print(f"\n[CRITICAL FATAL ERROR] Failed to initialize pipeline: {e}")
        # traceback.print_exc()
        return
    
    # NEW: Route Detection
    print(f"[MASTER] Scanning for Router Definitions...", flush=True)
    project_routes = detect_routes(folder)
    print(f"  -> Found {len(project_routes)} potential routes.", flush=True)
    
    files, folders = scan_folder(folder)
    
    # NEW: Detect actual project root (skip wrapper folders from zip)
    project_root = folder
    if len(folders) > 0:
        # Find the folder containing 'src' or most of the files
        potential_roots = [f for f in folders if os.path.basename(f) == 'src' or os.path.isfile(os.path.join(f, 'package.json'))]
        if potential_roots:
            project_root = os.path.dirname(potential_roots[0])
            print(f"[MASTER] Detected Project Root: {project_root}")

    folder_id_map = {f_path: insert_folder(pid, f_path, folder, storage) for f_path in ([folder] + folders)}

    # 2. Parallel Processing
    print(f"\n{'-'*50}\n[MASTER] Starting Unified AST Analysis\n{'-'*50}", flush=True)
    
    total_files = len(files)
    completed_count = 0
    start_time = time.time()
    overall_start_time = start_time
    
    scanned_count = 0
    skipped_count = 0
    error_count = 0
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for file_path in files:
            f_id = folder_id_map.get(os.path.dirname(file_path))
            futures.append(executor.submit(process_single_file, file_path, f_id, pid, storage))
        
        for future in as_completed(futures):
            completed_count += 1
            try:
                res = future.result()
                if res == "scanned": scanned_count += 1
                elif res == "skipped": skipped_count += 1
                elif res == "error": error_count += 1
                
                # Calculate Estimates
                elapsed = time.time() - start_time
                avg_time = elapsed / completed_count
                remaining = total_files - completed_count
                est_remaining = remaining * avg_time
                
                # Format time
                if est_remaining >= 60:
                    time_str = f"{int(est_remaining // 60)}m {int(est_remaining % 60)}s"
                else:
                    time_str = f"{int(est_remaining)}s"
                    
                if elapsed >= 60:
                    elapsed_str = f"{int(elapsed // 60)}m {int(elapsed % 60)}s"
                else:
                    elapsed_str = f"{int(elapsed)}s"
                    
                percentage = int((completed_count / total_files) * 100)
                print(f"[PROGRESS] {completed_count}/{total_files} ({percentage}%) | Elapsed: {elapsed_str} | Est: {time_str} | Scanned: {scanned_count} | Skipped: {skipped_count} | Errors: {error_count}", flush=True)
                
            except Exception as e:
                print(f"[CRITICAL ERROR] Worker thread crashed: {e}")

    # --- Phase 2: Context Enrichment ---
    print("\n" + "="*50)
    print("[MASTER] Enriching Component Context (Siblings & Routes)...")
    print("="*50)
    
    # Group files by folder for sibling detection
    folder_groups = {}
    for f in storage.tables["files"]:
        folder_path = os.path.dirname(f["path"])
        if folder_path not in folder_groups: folder_groups[folder_path] = []
        folder_groups[folder_path].append(f["file_name"])
    
    for f in storage.tables["files"]:
        f_name = f["file_name"]
        f_base = f_name.split('.')[0]
        folder_path = os.path.dirname(f["path"])
        
        # Siblings
        siblings = [s for s in folder_groups.get(folder_path, []) if s != f_name]
        
        # Route
        route = project_routes.get(f_base, "unknown")
        
        # Update context
        f["context"] = {
            "siblings": siblings,
            "route": route
        }

    print("\n" + "="*50)
    print("ANALYSIS COMPLETE. Generating AST-based JSON reports...")
    print("="*50)

    # 3. Build & Automated JSON Export
    try:
        storage.run_consistency_check()
        
        from dependency_graph import build_dependency_graph
        print("\n" + "="*50)
        print("[MASTER] Constructing Project Dependency Graph...")
        print("="*50)
        storage.tables["dependency_graph"] = build_dependency_graph(storage.tables["files"], project_root)
        
    except Exception as e:
        print(f"[GRAPH ERROR] Failed to build dependency graph: {e}")
        err_msg = traceback.format_exc()
        print(err_msg)
        
        # Write error to a special file in backend dir
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            log_path = os.path.join(base_dir, "backend", "json_reports", "analyzer_error.txt")
            with open(log_path, 'w') as f:
                f.write(f"TIMESTAMP: {datetime.now()}\n")
                f.write(f"ERROR: {e}\n\n")
                f.write(err_msg)
        except: pass

    storage.export_all()

    # AI Graph Dependency Discovery
    try:
        from ai_dependency_builder import run_ai_dependency_builder
        run_ai_dependency_builder()
    except Exception as e:
        print(f"[AI DEPENDENCY ERROR] Failed to infer dependencies via AI: {e}")

    # 4. Generate the Intelligent RAG AI Report & Architecture Map
    try:
        from ai_reporter import run_ai_reporter
        print("\n" + "="*50)
        print("[MASTER] Triggering AI Reasoning Pipeline...")
        print("="*50)
        run_ai_reporter()

        from ai_architecture_analyzer import run_ai_architecture_analyzer
        print("\n" + "="*50)
        print("[MASTER] Synthesizing Macro Architectural Trends...")
        print("="*50)
        run_ai_architecture_analyzer()
    except Exception as e:
        print(f"[AI REPORT ERROR] Failed to generate AI report: {e}")
        traceback.print_exc()

    overall_end_time = time.time()
    total_time = overall_end_time - overall_start_time
    print("\n" + "="*50)
    print(f"[MASTER] PIPELINE COMPLETED IN {total_time:.2f} seconds")
    print(f"  -> Total Files Scanned: {scanned_count}")
    print(f"  -> Total Files Skipped (non-frontend): {skipped_count}")
    print(f"  -> Total Errors: {error_count}")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()