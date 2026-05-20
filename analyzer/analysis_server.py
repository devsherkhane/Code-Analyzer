import difflib
import json
import os
import sys
from pathlib import Path

from flask import Flask, jsonify, request

# Add the analyzer directory to sys.path so imports work
_this_dir = os.path.dirname(os.path.abspath(__file__))
if _this_dir not in sys.path:
    sys.path.insert(0, _this_dir)

from ai_config import call_ai, get_client
from ai_reporter import analyze_batch_sync
from mcp_index_builder import get_blast_radius, load_mcp_index, search_semantic_index
from metrics_extractor import get_metrics
from script_parser import parse_source

app = Flask(__name__)
MAX_CONTEXT_CHARS = 12000
MAX_FIX_RETRIES = 1


def process_single_file_for_uiux(file_path, content):
    client = get_client()
    if not client:
        return {"error": "AI Client not configured"}

    parsed = parse_source(content, file_path)
    metrics = get_metrics(file_path, parsed)

    file_id = os.path.basename(file_path)
    bundle = {
        "file_id": file_id,
        "file_name": os.path.basename(file_path),
        "file_path": file_path,
        "source_code": content,
        "metrics": metrics,
        "context": {},
        "ast_data": {
            "ui_elements": parsed.get("ui_elements", []) if parsed else []
        }
    }

    result = analyze_batch_sync([bundle], client)
    if isinstance(result, dict):
        if "error" in result:
            return {"issues": [], "error": result["error"]}

        file_result = result.get(file_id) or result.get(str(file_id))
        if file_result and isinstance(file_result, dict):
            return file_result

        if "issues" in result:
            return result

        for _, val in result.items():
            if isinstance(val, dict) and "issues" in val:
                return val

    if isinstance(result, list):
        return {"issues": result}

    return {"issues": [], "raw": str(result)[:500]}


def _load_index():
    return load_mcp_index() or {
        "by_id": {},
        "by_name": {},
        "dependency_graph": {"impact_map": {}, "file_map": {}, "connections": []},
        "symbol_index": {},
    }


def _safe_read_file(file_path):
    if not file_path or not os.path.exists(file_path):
        return ""
    try:
        with open(file_path, "r", encoding="utf-8") as handle:
            return handle.read()
    except Exception:
        return ""


def _get_file_record(index, active_file_name, active_file_content):
    if active_file_name:
        record = index.get("by_name", {}).get(active_file_name)
        if isinstance(record, list):
            record = record[0]
        if isinstance(record, dict):
            return record

    synthetic_id = f"ad_hoc::{active_file_name or 'active-file'}"
    return {
        "file_id": synthetic_id,
        "file_name": active_file_name or "active-file",
        "path": "",
        "imports": [],
        "exports": [],
        "metrics": {},
        "ast_data": {},
        "context": {},
        "semantic_text": active_file_content[:2000],
    }


def _compact_file_context(file_record, content_override=""):
    content = content_override or _safe_read_file(file_record.get("path", "")) or ""
    return {
        "file_id": str(file_record.get("file_id", "")),
        "file_name": file_record.get("file_name", ""),
        "path": file_record.get("path", ""),
        "imports": file_record.get("imports", []),
        "exports": file_record.get("exports", []),
        "metrics": file_record.get("metrics", {}),
        "ast_methods": (file_record.get("ast_data", {}) or {}).get("methods", []),
        "registered_components": (file_record.get("ast_data", {}) or {}).get("registered_components", []),
        "imported_components": (file_record.get("ast_data", {}) or {}).get("imported_components", []),
        "source_code": content[:MAX_CONTEXT_CHARS],
    }


def _looks_like_fix_request(message):
    msg = (message or "").lower()
    fix_terms = [
        "generate a fix", "apply fix", "patch this", "write the patch",
        "return a diff", "produce a diff", "modify the code", "update the file",
        "rewrite this code", "fix this code", "create a patch", "validate fix"
    ]
    return any(term in msg for term in fix_terms)


def _build_issue_context_prompt(issue_context):
    if not isinstance(issue_context, dict):
        return ""

    compact = {
        "type": issue_context.get("defect_type") or issue_context.get("problem"),
        "file": issue_context.get("_fileName"),
        "line": issue_context.get("line_number") or issue_context.get("line"),
        "rule": issue_context.get("wcag_rule"),
        "source": issue_context.get("_source"),
        "rationale": issue_context.get("rationale"),
        "suggestion": issue_context.get("suggestion") or issue_context.get("explanation"),
        "original_code": (issue_context.get("original_code_snippet") or issue_context.get("original_code") or "")[:2000],
        "proposed_fix": (issue_context.get("fixed_code_snippet") or issue_context.get("fixed_code") or "")[:2000],
    }
    return json.dumps(compact, indent=2)


def _general_chat_response(client, llm_messages):
    model_name = os.environ.get("LLM_MODEL", "gemma2-9b")
    response = client.chat.completions.create(
        model=model_name,
        messages=llm_messages,
        temperature=0.7,
        max_tokens=2048,
    )
    if not response or not response.choices:
        raise RuntimeError("Empty response from AI")
    return response.choices[0].message.content


def _build_fix_query(message, file_record, active_file_content):
    ast_data = file_record.get("ast_data", {}) or {}
    key_terms = []
    for item in file_record.get("imports", [])[:8]:
        if isinstance(item, dict):
            key_terms.extend([item.get("name", ""), item.get("source", "")])
    key_terms.extend(ast_data.get("methods", [])[:10])
    key_terms.extend(ast_data.get("registered_components", [])[:10])
    key_terms.extend(ast_data.get("imported_components", [])[:10])
    parts = [
        message,
        file_record.get("file_name", ""),
        " ".join([term for term in key_terms if term]),
        active_file_content[:1200],
    ]
    return "\n".join([part for part in parts if part]).strip()


def _build_symbol_summary(index, file_record):
    symbol_index = index.get("symbol_index", {}) or {}
    interesting = set()
    for item in file_record.get("imports", [])[:12]:
        if isinstance(item, dict) and item.get("name") and item.get("name") != "default":
            interesting.add(item["name"])
    for item in file_record.get("exports", [])[:12]:
        if isinstance(item, dict) and item.get("name") and item.get("name") != "default":
            interesting.add(item["name"])
    for symbol in (file_record.get("ast_data", {}) or {}).get("registered_components", [])[:12]:
        interesting.add(symbol)

    summary = []
    for symbol in sorted(interesting):
        data = symbol_index.get(symbol)
        if not data:
            continue
        summary.append({
            "symbol": symbol,
            "defined_in": data.get("defined_in", [])[:5],
            "imported_by": data.get("imported_by", [])[:5],
        })
    return summary[:20]


def _plan_fix_scope(client, message, file_record, index, retrieved_files, blast_radius):
    """Phase 0: Ask the LLM to identify the files that need modification before
    generating any code."""

    active_path = file_record.get("path") or file_record.get("file_name") or "unknown"
    fallback = {
        "files_to_change": [active_path],
        "reason": "Direct fix request for active file.",
    }

    symbol_summary = _build_symbol_summary(index, file_record)
    plan_prompt = f"""Given this issue in {active_path}:
{message}

And this codebase symbol index:
{json.dumps(symbol_summary, indent=2)}

List ALL files that need to be modified to fix this issue completely.
Return JSON:
{{
  "files_to_change": ["path1", "path2"],
  "reason": "brief explanation of why these files need changes"
}}

Respond with JSON only."""

    try:
        response_text, _ = call_ai(client, plan_prompt, json_mode=True, max_retries=2)
        plan = json.loads(response_text)

        if not isinstance(plan, dict) or "files_to_change" not in plan:
            print(f"     [Planner] Malformed response, falling back to single-file plan.")
            return fallback

        # Ensure the active file is always included
        if active_path not in plan["files_to_change"]:
            plan["files_to_change"].insert(0, active_path)

        plan.setdefault("reason", "")

        print(f"     [Planner] Planned {len(plan['files_to_change'])} file(s): "
              f"{', '.join(plan['files_to_change'][:6])}")
        return plan

    except Exception as exc:
        print(f"     [Planner] LLM planning failed ({exc}), falling back to single-file plan.")
        return fallback


def _collect_relevant_files(index, file_record, active_file_content, message):
    active_file_id = str(file_record.get("file_id", ""))
    query = _build_fix_query(message, file_record, active_file_content)
    retrieved = search_semantic_index(index, query=query, top_k=5, exclude_file_ids=[active_file_id])

    related = []
    seen = set()
    for item in retrieved:
        ref = index.get("by_id", {}).get(str(item.get("file_id")))
        if not ref:
            continue
        path_key = ref.get("path") or ref.get("file_name")
        if path_key in seen:
            continue
        seen.add(path_key)
        related.append(ref)
    return retrieved, related


def _collect_related_file_names(index, file_record, active_file_content, message):
    active_file_id = str(file_record.get("file_id", ""))
    query = _build_fix_query(message, file_record, active_file_content)
    retrieved = search_semantic_index(index, query=query, top_k=5, exclude_file_ids=[active_file_id])
    names = []
    seen = set()
    for item in retrieved:
        name = item.get("file_name") or os.path.basename(item.get("path", "")) or item.get("path", "")
        if not name or name in seen:
            continue
        seen.add(name)
        names.append(name)
    return names


def _render_fix_context(active_record, active_content, related_files, blast_radius, plan):
    context = {
        "target_file": _compact_file_context(active_record, active_content),
        "planned_files_to_change": plan.get("files_to_change", []),
        "planning_reason": plan.get("reason", ""),
        "blast_radius": blast_radius,
        "related_files": [_compact_file_context(file_record) for file_record in related_files[:5]],
    }
    return json.dumps(context, indent=2)


def _append_connected_files_text(response_text, connected_names):
    if not connected_names:
        return response_text
    names_text = ", ".join(connected_names[:5])
    return f"{response_text}\n\nConnected files to keep an eye on: {names_text}"


def _normalize_generated_files(payload):
    if not isinstance(payload, dict):
        return []
    generated = payload.get("files", [])
    normalized = []
    for item in generated:
        if not isinstance(item, dict):
            continue
        updated_content = item.get("updated_content", "")
        file_path = item.get("file_path") or item.get("file_name") or ""
        if not file_path or not updated_content:
            continue
        normalized.append({
            "file_path": file_path,
            "updated_content": updated_content,
            "summary": item.get("summary", ""),
        })
    return normalized


def _resolve_content_for_generated_file(index, generated_file, active_record, active_content):
    candidate = generated_file.get("file_path", "")
    original_content = ""
    resolved_path = candidate

    if candidate == active_record.get("path") or candidate == active_record.get("file_name"):
        return active_content, active_record.get("path") or candidate, active_record.get("file_name", "")

    for file_data in index.get("by_id", {}).values():
        if candidate in (file_data.get("path"), file_data.get("file_name")):
            resolved_path = file_data.get("path") or candidate
            original_content = _safe_read_file(resolved_path)
            return original_content, resolved_path, file_data.get("file_name", "")

    original_content = _safe_read_file(candidate)
    return original_content, resolved_path, os.path.basename(candidate)


def _resolve_target_path(index, candidate_path, active_record):
    candidate_path = candidate_path or ""
    if not candidate_path:
        return ""

    if os.path.isabs(candidate_path):
        return candidate_path

    if candidate_path == active_record.get("file_name") and active_record.get("path"):
        return active_record.get("path")

    for file_data in index.get("by_id", {}).values():
        if candidate_path in (file_data.get("path"), file_data.get("file_name")):
            return file_data.get("path", "")

    if active_record.get("path"):
        parent = os.path.dirname(active_record["path"])
        candidate = os.path.normpath(os.path.join(parent, candidate_path))
        return candidate
    return candidate_path


def _build_unified_diff(file_name, original_content, updated_content):
    diff = difflib.unified_diff(
        original_content.splitlines(),
        updated_content.splitlines(),
        fromfile=f"a/{file_name}",
        tofile=f"b/{file_name}",
        lineterm="",
    )
    return "\n".join(diff)


def _generate_fix_attempt(client, message, active_record, active_content, fix_context, validation_error="", previous_attempt=""):
    prompt = f"""You are generating a minimal, compatible code fix.

Rules:
- Change only the files that truly need edits.
- Preserve existing style and structure.
- Return JSON only.
- For each changed file, return full updated file content in "updated_content". Keep changes minimal so the resulting unified diff is as small as possible.
- Do not include markdown.

User request:
{message}

Validation feedback from previous attempt:
{validation_error or "None"}

Previous attempt summary:
{previous_attempt or "None"}

Fix context:
{fix_context}

Return JSON:
{{
  "summary": "brief description",
  "files": [
    {{
      "file_path": "absolute/or/project/path/or filename",
      "updated_content": "full updated content",
      "summary": "what changed in this file"
    }}
  ]
}}"""
    response_text, _ = call_ai(client, prompt, json_mode=True, max_retries=2)
    parsed = json.loads(response_text)
    return {
        "summary": parsed.get("summary", "") if isinstance(parsed, dict) else "",
        "files": _normalize_generated_files(parsed),
    }


def _validate_generated_fix(index, active_record, active_content, generated_fix, plan):
    issues = []
    validated_files = []

    planned_targets = {str(item) for item in plan.get("files_to_change", [])}
    changed_targets = {str(item.get("file_path")) for item in generated_fix.get("files", [])}
    missing = sorted([item for item in planned_targets if item and item not in changed_targets and item != active_record.get("file_name")])
    if missing:
        issues.append(f"Planned files were not updated: {', '.join(missing[:5])}")

    for generated_file in generated_fix.get("files", []):
        original_content, resolved_path, file_name = _resolve_content_for_generated_file(
            index, generated_file, active_record, active_content
        )
        updated_content = generated_file.get("updated_content", "")
        if not updated_content.strip():
            issues.append(f"{file_name or resolved_path}: updated content is empty.")
            continue
        if updated_content == original_content:
            issues.append(f"{file_name or resolved_path}: no actual code changes were produced.")
            continue

        try:
            parsed = parse_source(updated_content, resolved_path or file_name or "generated-file")
            metrics = get_metrics(resolved_path or file_name or "generated-file", parsed)
        except Exception as exc:
            parsed = None
            metrics = {}
            issues.append(f"{file_name or resolved_path}: parser validation failed: {exc}")

        diff_text = _build_unified_diff(file_name or resolved_path or "generated-file", original_content, updated_content)
        if not diff_text.strip():
            issues.append(f"{file_name or resolved_path}: could not derive a unified diff.")
            continue

        validated_files.append({
            "file_path": resolved_path or generated_file.get("file_path", ""),
            "file_name": file_name or os.path.basename(resolved_path or generated_file.get("file_path", "")),
            "summary": generated_file.get("summary", ""),
            "diff": diff_text,
            "updated_content": updated_content,
            "original_content": original_content,
            "metrics": metrics,
            "ast_ok": parsed is not None,
        })

    return {
        "valid": len(issues) == 0 and len(validated_files) > 0,
        "issues": issues,
        "files": validated_files,
    }


def _run_fix_pipeline(client, message, active_file_name, active_file_content):
    index = _load_index()
    active_record = _get_file_record(index, active_file_name, active_file_content)
    active_file_id = str(active_record.get("file_id", ""))
    blast_radius = get_blast_radius(index, active_file_id, depth=2) if active_file_id in index.get("by_id", {}) else {
        "file_id": active_file_id,
        "file_name": active_record.get("file_name", ""),
        "path": active_record.get("path", ""),
        "downstream": [],
        "upstream_dependencies": [],
        "downstream_count": 0,
    }
    retrieved_meta, related_files = _collect_relevant_files(index, active_record, active_file_content, message)
    plan = _plan_fix_scope(client, message, active_record, index, retrieved_meta, blast_radius)
    fix_context = _render_fix_context(active_record, active_file_content, related_files, blast_radius, plan)

    last_validation = {"valid": False, "issues": ["No attempt completed."], "files": []}
    previous_attempt_summary = ""
    for attempt in range(1, MAX_FIX_RETRIES + 1):
        generated_fix = _generate_fix_attempt(
            client,
            message,
            active_record,
            active_file_content,
            fix_context,
            validation_error="; ".join(last_validation.get("issues", [])) if attempt > 1 else "",
            previous_attempt=previous_attempt_summary,
        )
        previous_attempt_summary = generated_fix.get("summary", "")
        validation = _validate_generated_fix(index, active_record, active_file_content, generated_fix, plan)
        validation["attempt"] = attempt
        validation["planning"] = plan
        validation["retrieved_files"] = retrieved_meta
        validation["blast_radius"] = blast_radius
        validation["summary"] = generated_fix.get("summary", "")
        last_validation = validation
        if validation["valid"]:
            return validation
    return last_validation


def _apply_validated_fix(index, active_record, result):
    applied = []
    failures = []
    for file_result in result.get("files", []):
        file_path = _resolve_target_path(index, file_result.get("file_path", ""), active_record)
        if not file_path:
            failures.append("Missing target path for one generated file.")
            continue

        if not os.path.isabs(file_path):
            failures.append(f"Refusing to apply non-absolute path: {file_path}")
            continue

        try:
            parent = Path(file_path).parent
            parent.mkdir(parents=True, exist_ok=True)
            updated_content = file_result.get("updated_content")
            if updated_content is None:
                failures.append(f"Updated content missing for {file_path}")
                continue

            with open(file_path, "w", encoding="utf-8") as handle:
                handle.write(updated_content)
            applied.append(file_path)
        except Exception as exc:
            failures.append(f"{file_path}: {exc}")

    return {"applied": applied, "failures": failures, "success": len(failures) == 0 and len(applied) > 0}


def _format_fix_response(result):
    if not result.get("valid"):
        lines = ["I checked the issue, but I could not produce a clean validated fix yet.", ""]
        planned_files = result.get("planning", {}).get("files_to_change", [])
        if planned_files:
            lines.append(f"Files that may need changes: {', '.join(planned_files[:5])}")
        lines.append("")
        lines.append("Validation issues:")
        for issue in result.get("issues", []):
            lines.append(f"- {issue}")
        return "\n".join(lines)

    lines = [result.get("summary", "Generated a validated patch."), ""]
    planned_files = result.get("planning", {}).get("files_to_change", [])
    if planned_files:
        lines.append(f"Files that may need changes: {', '.join(planned_files[:5])}")
    for file_result in result.get("files", []):
        lines.extend([
            "",
            f"### {file_result.get('file_name')}",
            "```diff",
            file_result.get("diff", ""),
            "```",
        ])
    return "\n".join(lines)


@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
    return response


@app.route("/analyze-file", methods=["POST", "OPTIONS"])
def analyze_file():
    if request.method == "OPTIONS":
        return "", 200
    data = request.json or {}
    res = process_single_file_for_uiux(data["file_path"], data["content"])
    return jsonify(res)


@app.route("/validate-fix", methods=["POST", "OPTIONS"])
def validate_fix():
    if request.method == "OPTIONS":
        return "", 200

    data = request.json or {}
    file_path = data.get("filePath", "")
    original_content = data.get("originalContent", "")
    patched_content = data.get("patchedContent", "")

    issues = []
    metrics = {}
    parsed = None
    if not patched_content.strip():
        issues.append("Patched content is empty.")
    elif patched_content == original_content:
        issues.append("Patched content is identical to the original content.")
    else:
        try:
            parsed = parse_source(patched_content, file_path or "patched-file")
            metrics = get_metrics(file_path or "patched-file", parsed)
        except Exception as exc:
            issues.append(f"Parser validation failed: {exc}")

    diff_text = _build_unified_diff(os.path.basename(file_path or "patched-file"), original_content, patched_content)
    if not diff_text.strip():
        issues.append("No unified diff could be produced from the patch.")

    return jsonify({
        "valid": len(issues) == 0 and parsed is not None,
        "issues": issues,
        "diff": diff_text,
        "metrics": metrics,
    })


@app.route("/apply-fix", methods=["POST", "OPTIONS"])
def apply_fix():
    if request.method == "OPTIONS":
        return "", 200

    data = request.json or {}
    result = data.get("result", {})
    active_file_name = data.get("activeFileName", "")
    active_file_content = data.get("activeContent", "")
    index = _load_index()
    active_record = _get_file_record(index, active_file_name, active_file_content)

    if not isinstance(result, dict) or not result.get("valid"):
        return jsonify({"error": "Only validated fix results can be applied."}), 400

    applied = _apply_validated_fix(index, active_record, result)
    status = 200 if applied["success"] else 400
    return jsonify(applied), status


@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return "", 200

    data = request.json or {}
    message = data.get("message", "")
    context_type = data.get("contextType", "workspace")
    active_file_content = data.get("activeContent", "")
    active_file_name = data.get("activeFileName", "")
    workspace_path = data.get("workspacePath", "")
    history_arr = data.get("history", [])
    issue_context = data.get("issueContext", {})

    client = get_client()
    if not client:
        return jsonify({"error": "AI client not configured"}), 500

    index = _load_index()
    connected_file_names = []
    if context_type == "file" and active_file_content:
        active_record = _get_file_record(index, active_file_name, active_file_content)
        connected_file_names = _collect_related_file_names(index, active_record, active_file_content, message)

    if context_type == "file" and active_file_content and _looks_like_fix_request(message):
        try:
            result = _run_fix_pipeline(client, message, active_file_name, active_file_content)
            return jsonify({
                "response": _append_connected_files_text(_format_fix_response(result), connected_file_names),
                "mode": "fix",
                "result": result,
            })
        except Exception as exc:
            return jsonify({"error": str(exc)}), 500

    system_prompt = "You are a senior developer and AI coding assistant."
    if context_type == "file" and active_file_content:
        if issue_context:
            system_prompt += (
                f"\n\nThe user is discussing an attached issue in '{active_file_name}'. "
                f"Use this compact issue context first:\n```json\n{_build_issue_context_prompt(issue_context)}\n```"
            )
            if active_file_content.strip():
                system_prompt += f"\n\nRelevant code snippet:\n```\n{active_file_content}\n```"
        else:
            system_prompt += (
                f"\n\nThe user is asking about the file '{active_file_name}'. "
                f"Here is its content:\n```\n{active_file_content}\n```"
            )
    elif context_type == "workspace" and workspace_path:
        try:
            tree = []
            for root, dirs, files in os.walk(workspace_path):
                if "node_modules" in dirs:
                    dirs.remove("node_modules")
                if ".git" in dirs:
                    dirs.remove(".git")
                if "dist" in dirs:
                    dirs.remove("dist")
                for file_name in files:
                    tree.append(os.path.relpath(os.path.join(root, file_name), workspace_path))
            tree_str = "\n".join(tree[:200])
            system_prompt += (
                f"\n\nThe user is asking about the entire workspace at '{workspace_path}'. "
                f"The workspace contains these files:\n```\n{tree_str}\n```"
            )
        except Exception:
            pass

    llm_messages = [{"role": "system", "content": system_prompt}]
    for past_msg in history_arr:
        llm_messages.append({
            "role": past_msg.get("role", "user"),
            "content": past_msg.get("content", ""),
        })
    llm_messages.append({"role": "user", "content": message})

    try:
        response_text = _general_chat_response(client, llm_messages)
        return jsonify({"response": _append_connected_files_text(response_text, connected_file_names), "mode": "chat"})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("FLASK_PORT", 7891))
    print(f"[FLASK] UI/UX Analysis Bridge starting on port {port}")
    app.run(port=port)
