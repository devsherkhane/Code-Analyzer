import os
import sys
from flask import Flask, request, jsonify

# Add the analyzer directory to sys.path so imports work
_this_dir = os.path.dirname(os.path.abspath(__file__))
if _this_dir not in sys.path:
    sys.path.insert(0, _this_dir)

from script_parser import parse_vue_script
from metrics_extractor import get_metrics
from ai_reporter import analyze_batch_sync
from ai_config import get_client

app = Flask(__name__)

def process_single_file_for_uiux(file_path, content):
    client = get_client()
    if not client:
        return {"error": "AI Client not configured"}
        
    # Attempt to write the content back to file if possible since get_metrics reads from file path
    try:
        if os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
    except:
        pass
        
    parsed = parse_vue_script(content)
    metrics = get_metrics(file_path, parsed)
    
    # Build the bundle that analyze_batch_sync expects
    file_id = os.path.basename(file_path)
    bundle = {
        "file_id": file_id,
        "file_name": os.path.basename(file_path),
        "file_path": file_path,
        "source_code": content,
        "metrics": metrics,
        "context": {},
        "ast_data": {
            "ui_elements": parsed.get('ui_elements', []) if parsed else []
        }
    }
    
    result = analyze_batch_sync([bundle], client)
    
    # analyze_batch_sync returns a dict keyed by file_id like:
    #   {"file_id": {"issues": [...], "visual_simulation": {...}}}
    # OR  {"error": "..."}
    # We need to extract the issues correctly
    if isinstance(result, dict):
        if "error" in result:
            return {"issues": [], "error": result["error"]}
        
        # Try to find issues in the keyed response
        file_result = result.get(file_id) or result.get(str(file_id))
        if file_result and isinstance(file_result, dict):
            return file_result
        
        # If the result itself has "issues" at the top level
        if "issues" in result:
            return result
        
        # Fallback: try first value in the dict
        for key, val in result.items():
            if isinstance(val, dict) and "issues" in val:
                return val
    
    if isinstance(result, list):
        return {"issues": result}
    
    return {"issues": [], "raw": str(result)[:500]}

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/analyze-file', methods=['POST', 'OPTIONS'])
def analyze_file():
    if request.method == 'OPTIONS':
        return '', 200
    data = request.json
    res = process_single_file_for_uiux(data['file_path'], data['content'])
    return jsonify(res)

@app.route('/chat', methods=['POST', 'OPTIONS'])
def chat():
    if request.method == 'OPTIONS':
        return '', 200
    data = request.json
    message = data.get('message', '')
    context_type = data.get('contextType', 'workspace')
    active_file_content = data.get('activeContent', '')
    active_file_name = data.get('activeFileName', '')
    workspace_path = data.get('workspacePath', '')
    
    client = get_client()
    if not client:
        return jsonify({"error": "AI client not configured"}), 500
        
    system_prompt = "You are a senior developer and AI coding assistant."
    if context_type == 'file' and active_file_content:
        system_prompt += f"\n\nThe user is asking about the file '{active_file_name}'. Here is its content:\n```\n{active_file_content[:15000]}\n```"
    elif context_type == 'workspace' and workspace_path:
        try:
            tree = []
            for root, dirs, files in os.walk(workspace_path):
                if 'node_modules' in dirs: dirs.remove('node_modules')
                if '.git' in dirs: dirs.remove('.git')
                if 'dist' in dirs: dirs.remove('dist')
                for f in files:
                    tree.append(os.path.relpath(os.path.join(root, f), workspace_path))
            
            tree_str = "\n".join(tree[:200]) # cap to 200 files
            system_prompt += f"\n\nThe user is asking about the entire workspace at '{workspace_path}'. The workspace contains these files:\n```\n{tree_str}\n```"
        except Exception:
            pass
            
    user_prompt = f"{message}"
    
    try:
        model_name = os.environ.get("LLM_MODEL", "gemma2-9b")
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=2048,
        )
        
        if not response or not response.choices:
            return jsonify({"error": "Empty response from AI"}), 500
            
        return jsonify({"response": response.choices[0].message.content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('FLASK_PORT', 7891))
    print(f"[FLASK] UI/UX Analysis Bridge starting on port {port}")
    app.run(port=port)

