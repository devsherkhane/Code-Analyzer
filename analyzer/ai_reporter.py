import os
import json
import time
import hashlib
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# AI Core Imports
from ai_config import get_client, call_ai,  rate_limiter, MODEL_CHAIN
from ai_context_fetcher import fetch_all_issues_context
from ast_to_fingerprint import build_fingerprint

def analyze_sniffer_pass(batch, client):
    """Phase 1: Pure Python Heuristic Triage. Instantly skips clean files
    without hitting the LLM API, saving immense amounts of time."""
    results = {}
    for bundle in batch:
        fid = str(bundle["file_id"])
        metrics = bundle.get("metrics", {})
        ast_data = bundle.get("ast_data", {})
        downstream = bundle.get("downstream_impact", [])
        
        cyc = metrics.get("cyclomatic_complexity", 1)
        cog = metrics.get("cognitive_complexity", 0)
        depth = metrics.get("nesting_depth", 0)
        methods = len(ast_data.get("methods", []))
        api_calls = ast_data.get("api_calls", [])
        flags = [a for a in api_calls if a.get("flag")]
        
        reasons = []
        if cyc >= 10 or cog >= 10: reasons.append(f"High complexity (Cyc:{cyc}/Cog:{cog})")
        if depth >= 6: reasons.append(f"Excessive nesting ({depth} deep)")
        if methods > 10: reasons.append("Overloaded logic (>10 methods)")
        if len(api_calls) > 5: reasons.append(f"Heavy API coupling ({len(api_calls)} calls)")
        if len(downstream) >= 3: reasons.append(f"High blast radius ({len(downstream)} downstream)")
        if flags: reasons.append("Suspicious AST flags detected")
        
        missing_alts = metrics.get('missing_alt_count', 0)
        unlabeled_inputs = metrics.get('unlabeled_inputs', 0)
        interactive_no_role = metrics.get('interactive_without_role', 0)
        hardcoded_colors = metrics.get('hardcoded_colors', 0)

        if missing_alts > 0: reasons.append(f"Missing alt tags ({missing_alts})")
        if unlabeled_inputs > 0: reasons.append(f"Unlabeled inputs ({unlabeled_inputs})")
        if interactive_no_role > 0: reasons.append(f"Interactive without role ({interactive_no_role})")
        if hardcoded_colors > 0: reasons.append(f"Hardcoded colors ({hardcoded_colors})")
        
        if len(reasons) > 0:
            print(f"     -> {bundle.get('file_name', fid)}: FLAGGED ({', '.join(reasons)})")
            results[fid] = True
        else:
            # print(f"     -> {bundle.get('file_name', fid)}: CLEAN")
            results[fid] = False
            
    return results

try:
    from dotenv import load_dotenv
    _reporter_dir = os.path.dirname(os.path.abspath(__file__))
    _reporter_root_env = os.path.normpath(os.path.join(_reporter_dir, "..", ".env"))
    if os.path.exists(_reporter_root_env):
        load_dotenv(_reporter_root_env, override=True)
    else:
        load_dotenv()
except ImportError:
    pass

def _split_results_by_type(all_results):
    ui_issues = []
    logic_issues = []
    if not isinstance(all_results, list): return [], []
    for issue in all_results:
        issue["is_real_issue"] = True
        severity = issue.get("severity", "").upper()
        if "ACCESSIBILITY" in severity or "UI" in issue.get("defect_type", "").upper():
            ui_issues.append(issue)
        else:
            logic_issues.append(issue)
    return ui_issues, logic_issues

# Setup Cache Path
current_dir = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.normpath(os.path.join(current_dir, "..", "backend", "json_reports"))
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR, exist_ok=True)
CACHE_FILE = os.path.join(CACHE_DIR, "ai_hash_cache.json")

# Thread lock for cache file writes
_cache_lock = threading.Lock()

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: return {}
    return {}

def save_cache(cache_data):
    with _cache_lock:
        with open(CACHE_FILE, "w", encoding="utf-8") as f: json.dump(cache_data, f, indent=4)

def get_bundle_hash(bundle):
    content = str(bundle.get('source_code', '')) + str(bundle.get('ast_data', ''))
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def _is_valid_result(res):
    if not res or not isinstance(res, dict): return False
    issues = res.get("issues")
    if isinstance(issues, list) or "visual_simulation" in res or "issues" not in res: 
        if "issues" not in res: res["issues"] = []
        return True
    return False

# ============================================================
# SMART BATCHING: Group small files together in one API call
# ============================================================

def _estimate_source_tokens(bundle):
    """Estimate token count for a file's source code."""
    source = bundle.get("source_code", "")
    return len(source) // 4  # rough 4 chars per token estimate

def _create_smart_batches(files, max_tokens_per_batch=8000, max_files_per_batch=5):
    """Group files into smart batches based on source code size.
    Small files get batched together; large files get their own batch."""
    # Sort files smallest-first so we can pack them efficiently
    sorted_files = sorted(files, key=lambda b: _estimate_source_tokens(b))
    
    batches = []
    current_batch = []
    current_tokens = 0
    
    for bundle in sorted_files:
        file_tokens = _estimate_source_tokens(bundle)
        
        # If a single file exceeds the batch limit, give it its own batch
        if file_tokens > max_tokens_per_batch:
            if current_batch:
                batches.append(current_batch)
                current_batch = []
                current_tokens = 0
            batches.append([bundle])
            continue
        
        # Check if adding this file would exceed limits
        if (current_tokens + file_tokens > max_tokens_per_batch or 
            len(current_batch) >= max_files_per_batch):
            if current_batch:
                batches.append(current_batch)
            current_batch = [bundle]
            current_tokens = file_tokens
        else:
            current_batch.append(bundle)
            current_tokens += file_tokens
    
    if current_batch:
        batches.append(current_batch)
    
    return batches

def _validate_ai_result(result):
    """Validate and sanitize the AI response schema to prevent None-type crashes downstream.
    Ensures every file entry has well-formed 'issues' (list) and 'visual_simulation' (dict)."""
    if not isinstance(result, dict):
        return result
    
    for key, val in result.items():
        if key in ("error", "results"):
            continue
        if not isinstance(val, dict):
            continue
        
        # Ensure issues is always a list, never None
        issues = val.get("issues")
        if issues is None:
            val["issues"] = []
        elif not isinstance(issues, list):
            val["issues"] = [issues] if isinstance(issues, dict) else []
        
        # Sanitize each issue — ensure minimum required fields
        cleaned_issues = []
        for issue in val["issues"]:
            if not isinstance(issue, dict):
                continue
            issue.setdefault("defect_type", "Unknown")
            issue.setdefault("severity", "medium")
            issue.setdefault("problem", issue.get("element", "Issue detected by AI"))
            issue.setdefault("line", 0)
            cleaned_issues.append(issue)
        val["issues"] = cleaned_issues
        
        # Ensure visual_simulation is well-formed
        vs = val.get("visual_simulation")
        if not isinstance(vs, dict):
            val["visual_simulation"] = {
                "layout_assessment": "Analyzed by AI.",
                "engineering_health_score": max(50, 100 - len(cleaned_issues) * 5),
                "recommendations": []
            }
        else:
            vs.setdefault("layout_assessment", "Analyzed by AI.")
            vs.setdefault("engineering_health_score", 85)
            vs.setdefault("recommendations", [])
            # Ensure score is numeric
            if not isinstance(vs["engineering_health_score"], (int, float)):
                vs["engineering_health_score"] = 85
    
    return result

def analyze_batch_sync(batch, client):
    """Synchronous batch analysis — handles 1 to N files per call."""
    batch_data = []
    for b in batch:
        source = b.get("source_code", "")
        # Adaptive truncation: smaller limit when batching multiple files
        if len(batch) > 1:
            MAX_SOURCE_CHARS = 4000
        else:
            MAX_SOURCE_CHARS = 6000
        if len(source) > MAX_SOURCE_CHARS:
            source = source[:MAX_SOURCE_CHARS] + f"\n\n... [TRUNCATED]"

        batch_data.append({
            "file_id": str(b["file_id"]),
            "file_name": b["file_name"],
            "route": b.get("context", {}).get("route", "unknown"),
            "source_code": source,
        })
    
    file_ids_list = [d["file_id"] for d in batch_data]
    file_names_list = [d["file_name"] for d in batch_data]
    
    # Build schema example showing all file IDs expected
    schema_entries = []
    for fid in file_ids_list:
        schema_entries.append(f'  "{fid}": {{ "issues": [...], "visual_simulation": {{ ... }} }}')
    schema_example = "{\n" + ",\n".join(schema_entries) + "\n}"
    
    prompt = f"""You are an Elite Principal Full-Stack Software Architect and Security Auditor. Your task is to perform an EXTREMELY deep, critical analysis of the provided code. Do NOT just focus on UI/UX or Accessibility. You must aggressively hunt for and report ALL types of issues across the entire stack:
1. Logic Bugs (incorrect math, unhandled edge cases, race conditions)
2. Security Vulnerabilities (XSS, injection, insecure data handling, hardcoded secrets)
3. Performance Anti-patterns (unnecessary re-renders, memory leaks, heavy loops, missing memoization)
4. State Management (mutating props, bad reactive state, deeply nested reactivity)
5. Architecture & Code Smells (tight coupling, massive functions, duplicate code)
6. UI/UX Accessibility (WCAG 2.1, missing ARIA, bad semantic HTML)

For each issue found: (1) identify the exact line, (2) explain why it is dangerous or bad practice, and (3) provide a perfect corrected version. Be ruthless and comprehensive. Do not ignore logic/security in favor of HTML tags.

CRITICAL RULES FOR CODE FIXES (you MUST follow these):
1. "original_code" MUST be an EXACT character-for-character copy from the source code — do NOT paraphrase, reformat, or approximate. Copy the exact whitespace, indentation, quotes, and line breaks.
2. "fixed_code" MUST be a direct drop-in replacement for "original_code". It must be syntactically valid code that compiles without errors when substituted.
3. Preserve the EXACT indentation style and whitespace conventions from the original code in your fix.
4. Do NOT include imports, component registrations, or code outside the snippet boundary in fixed_code. If a fix requires adding an import, report it as a SEPARATE issue with the import line as original_code context.
5. If a fix requires changes in multiple non-contiguous locations, report each location as a separate issue entry.
6. The fixed_code snippet must be SELF-CONTAINED — when it replaces original_code in the file, the result must be valid and compilable with zero additional changes needed.
7. Do NOT invent variable names, props, or methods that don't exist in the source code.

You MUST return a JSON object with a key for EACH of these file IDs: {file_ids_list}
Each key maps to an object with "issues" (array) and "visual_simulation" (object).

Issue schema per entry:
{{
  "line": 1,
  "defect_type": "Accessibility | UI | Logic | Performance | Architecture | Security",
  "severity": "critical | high | medium | low",
  "element": "affected code or tag",
  "problem": "Brief explanation.",
  "original_code": "exact snippet from the file",
  "fixed_code": "complete corrected snippet",
  "explanation": "why the fix solves the problem",
  "fix_diff": "--- original\\n+++ fixed\\n@@ -1 +1 @@\\n- original\\n+ fixed"
}}

Visual simulation schema:
{{
  "layout_assessment": "Brief assessment",
  "engineering_health_score": 85,
  "recommendations": ["Rec 1", "Rec 2"]
}}

Respond ONLY with raw JSON, no markdown blocks.
Analyzing {len(batch_data)} file(s): {', '.join(file_names_list)}

FILES DATA:
{json.dumps(batch_data)}
"""
    try:
        response_text, model_used = call_ai(client, prompt, json_mode=True, max_retries=3)
        print(f"     [Phase 2] Used model: {model_used}", flush=True)
        parsed = json.loads(response_text)
        if isinstance(parsed, list) and len(parsed) > 0: parsed = parsed[0]
        
        # Unwrap "results" wrapper if present
        result_data = parsed.get("results") or parsed if isinstance(parsed, dict) else parsed
        
        # Normalize: ensure each file_id value is {issues: [...], visual_simulation: {...}}
        # The AI sometimes returns file_id -> [issues] instead of file_id -> {issues: [...], ...}
        normalized = {}
        if isinstance(result_data, dict):
            for key, val in result_data.items():
                if key in ("results", "error"):
                    continue
                if isinstance(val, list):
                    # AI returned bare issues array — wrap it
                    normalized[key] = {
                        "issues": val,
                        "visual_simulation": {
                            "layout_assessment": "Analyzed by AI.",
                            "engineering_health_score": max(50, 100 - len(val) * 5),
                            "recommendations": []
                        }
                    }
                elif isinstance(val, dict):
                    # Ensure "issues" key exists
                    if "issues" not in val:
                        # Maybe the entire val IS an issue object, or issues are at top level
                        if "line" in val or "wcag_rule" in val:
                            normalized[key] = {
                                "issues": [val],
                                "visual_simulation": val.get("visual_simulation", {
                                    "layout_assessment": "Analyzed by AI.",
                                    "engineering_health_score": 85,
                                    "recommendations": []
                                })
                            }
                        else:
                            val.setdefault("issues", [])
                            val.setdefault("visual_simulation", {
                                "layout_assessment": "Analyzed by AI.",
                                "engineering_health_score": 85,
                                "recommendations": []
                            })
                            normalized[key] = val
                    else:
                        val.setdefault("visual_simulation", {
                            "layout_assessment": "Analyzed by AI.",
                            "engineering_health_score": 85,
                            "recommendations": []
                        })
                        normalized[key] = val
                else:
                    normalized[key] = {"issues": [], "visual_simulation": {"layout_assessment": "Analyzed by AI.", "engineering_health_score": 85}}
        
        # Validate and sanitize the AI output schema
        final = normalized if normalized else result_data
        if isinstance(final, dict):
            final = _validate_ai_result(final)
        return final
    except Exception as e:
        print(f"     [Phase 2] AI call failed: {str(e)[:150]}", flush=True)
        return {"error": str(e)[:200]}


def run_ai_reporter():
    start_time = time.time()
    print(f"\n[ACCELERATED] STARTING AI UX AUDIT")
    client = get_client()
    if not client: return
    
    bundles = fetch_all_issues_context()
    if not bundles: return
    
    # All frontend files, not just .vue
    all_bundles = bundles
    print(f"  -> [SCOPE] {len(all_bundles)} total frontend files discovered.", flush=True)
    
    ai_cache = load_cache()
    needs_analysis = []
    cached_count = 0
    for b in all_bundles:
        b["_hash"] = get_bundle_hash(b)
        if b["_hash"] not in ai_cache:
            needs_analysis.append(b)
        else:
            cached_count += 1

    new_results = {}
    results_lock = threading.Lock()
    
    if cached_count > 0:
        print(f"  -> [CACHE HIT] {cached_count} files already analyzed (skipped).", flush=True)
    
    if needs_analysis:
        print(f"  -> [PLAN] {len(needs_analysis)} files need analysis.")
        
        # PHASE 1: SNIFFER PASS (Sequential, very fast)
        files_requiring_deep_dive = []
        SNIFFER_BATCH_SIZE = 10
        chunks = [needs_analysis[i:i + SNIFFER_BATCH_SIZE] for i in range(0, len(needs_analysis), SNIFFER_BATCH_SIZE)]
        
        for chunk in chunks:
            sniff_res = analyze_sniffer_pass(chunk, client)
            for file_bundle in chunk:
                fid = str(file_bundle["file_id"])
                if sniff_res.get(fid, True):
                    files_requiring_deep_dive.append(file_bundle)
                else:
                    new_results[fid] = {"issues": [], "visual_simulation": {"layout_assessment": "Healthy.", "engineering_health_score": 100}}

        print(f"  -> [TRIAGE] {len(files_requiring_deep_dive)} files require Deep Dive, {len(needs_analysis) - len(files_requiring_deep_dive)} clean.")

        # PHASE 2: SMART BATCHED DEEP DIVE
        if files_requiring_deep_dive:
            smart_batches = _create_smart_batches(files_requiring_deep_dive)
            total_batches = len(smart_batches)
            print(f"  -> [PHASE 2] {len(files_requiring_deep_dive)} files packed into {total_batches} smart batches (Pool Size: 3)...")
            phase2_start = time.time()
            completed_batches = [0]  # mutable counter for thread access
            
            def process_batch_parallel(batch_files, batch_idx):
                batch_names = [b.get("file_name", "?") for b in batch_files]
                batch_fids = [str(b["file_id"]) for b in batch_files]
                tid = threading.get_native_id() % 100
                print(f"     [Worker {tid}] Batch {batch_idx+1}/{total_batches}: {', '.join(batch_names)}")
                
                try:
                    res = analyze_batch_sync(batch_files, client)
                    if "error" not in res:
                        with results_lock:
                            new_results.update(res)
                            # Progressive cache save — persist after each successful batch
                            for bf in batch_files:
                                bfid = str(bf["file_id"])
                                if bfid in res:
                                    ai_cache[bf["_hash"]] = res[bfid]
                            save_cache(ai_cache)
                        
                        completed_batches[0] += 1
                        print(f"     [Worker {tid}] SUCCESS: Batch {batch_idx+1} ({len(batch_files)} files) [{completed_batches[0]}/{total_batches}]")
                    else:
                        # Batch failed — insert placeholders for all files
                        with results_lock:
                            for bf in batch_files:
                                bfid = str(bf["file_id"])
                                new_results[bfid] = {
                                    "issues": [],
                                    "visual_simulation": {
                                        "layout_assessment": "AI analysis unavailable (server timeout). File will be re-analyzed on next run.",
                                        "engineering_health_score": 0
                                    }
                                }
                        completed_batches[0] += 1
                        print(f"     [Worker {tid}] FAILED (skipped): Batch {batch_idx+1} ({res.get('error', '')[:100]})")
                except Exception as ex:
                    # Catch-all so one worker crash never kills the pipeline
                    with results_lock:
                        for bf in batch_files:
                            bfid = str(bf["file_id"])
                            new_results[bfid] = {
                                "issues": [],
                                "visual_simulation": {
                                    "layout_assessment": "AI analysis crashed. File will be re-analyzed on next run.",
                                    "engineering_health_score": 0
                                }
                            }
                    completed_batches[0] += 1
                    print(f"     [Worker {tid}] CRASHED: Batch {batch_idx+1} ({str(ex)[:100]})")

            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(process_batch_parallel, batch, idx) for idx, batch in enumerate(smart_batches)]
                for future in as_completed(futures):
                    pass # Just wait for completion
            
            print(f"  -> [PHASE 2 COMPLETE] Time: {int(time.time() - phase2_start)}s")

    # Assemble & Save
    final_report = []
    total_real = 0
    total_fp = 0
    
    for b in all_bundles:
        fid = str(b["file_id"])
        res = ai_cache.get(b["_hash"]) or new_results.get(fid)
        if res:
            # Only cache genuinely good results — never cache timeout/crash placeholders
            health = res.get("visual_simulation", {}).get("engineering_health_score", -1)
            if b["_hash"] not in ai_cache and health > 0:
                ai_cache[b["_hash"]] = res
            ui, logic = _split_results_by_type(res.get("issues", []))
            
            # Count issues
            file_real = len([i for i in ui + logic if i.get("is_real_issue", True)])
            file_fp = len([i for i in ui + logic if not i.get("is_real_issue", True)])
            total_real += file_real
            total_fp += file_fp
            
            final_report.append({
                "file_id": b["file_id"], "file_name": b["file_name"], "file_path": b["file_path"],
                "ai_analysis": logic, "ui_accessibility_analysis": ui, 
                "visual_simulation": res.get("visual_simulation", {})
            })

    save_cache(ai_cache)
    
    report_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_name = os.environ.get("PROJECT_NAME", "PrismAI Project")
    report_data = {
        "overall_score": 85, # Base score
        "audit_status": "complete",
        "project_name": project_name,
        "report_id": report_id,
        "timestamp": datetime.now().isoformat(),
        "files_analyzed": len(all_bundles),
        "total_issues": total_real, # Dashboard expects this key
        "total_real_issues": total_real,
        "total_false_positives": total_fp,
        "files": final_report
    }

    # Adjust score based on issues
    if len(all_bundles) > 0:
        penalty = (total_real * 2) / len(all_bundles)
        report_data["overall_score"] = max(10, 100 - int(penalty))
    
    # 1. Save to Latest (standard location)
    latest_report_path = os.path.normpath(os.path.join(CACHE_DIR, "..", "ai_report.json"))
    with open(latest_report_path, "w", encoding="utf-8") as f: json.dump(report_data, f, indent=4)
    
    # 2. Save to History (backend location)
    history_report_path = os.path.join(CACHE_DIR, f"ai_report_{report_id}.json")
    with open(history_report_path, "w", encoding="utf-8") as f: json.dump(report_data, f, indent=4)
    
    print(f"\n[DONE] Scan complete in {int(time.time() - start_time)}s. {len(final_report)} files in report, {total_real} issues found.")
    print(f"  -> Saved: ai_report_{report_id}.json")

if __name__ == "__main__":
    run_ai_reporter()
