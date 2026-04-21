"""
script_parser.py — AST-based Vue <script> block parser wrapper using Node.js & typescript-estree.

Replaces esprima2. Now supports:
- TypeScript (.ts) and TSX
- Vue 3 Composition API (<script setup>)
- Standard Option API
"""

import json
import subprocess
import os
import tempfile

def parse_vue_script(content):
    """
    Parse the <script> block of a Vue file using a Node.js helper subprocess.
    """
    fd, tmp_file = tempfile.mkstemp(suffix=".vue", text=True)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(content)

    try:
        script_path = os.path.join(os.path.dirname(__file__), "ts_parser", "parse_node.js")
        
        result = subprocess.run(
            ["node", script_path, tmp_file],
            capture_output=True,
            text=True,
            encoding='utf-8',
            check=True
        )
        
        if result.stderr:
            print(result.stderr)
        
        output = result.stdout.strip()
        
        lines = output.split('\n')
        json_output = lines[-1] if lines else "{}"
        
        try:
            return json.loads(json_output)
        except json.JSONDecodeError:
            # Fallback if multiple lines of JSON output
            return json.loads(output)
        
    except subprocess.CalledProcessError as e:
        print(f"  -> [AST] Node.js parser crashed: {e.stderr}")
        return None
    except Exception as e:
        print(f"  -> [AST] Unexpected parser error: {e}")
        return None
    finally:
        if os.path.exists(tmp_file):
            try:
                os.remove(tmp_file)
            except:
                pass
