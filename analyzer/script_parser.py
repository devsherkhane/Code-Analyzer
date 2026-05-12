"""
script_parser.py — AST-based Vue <script> block parser wrapper using Node.js & typescript-estree.

Replaces esprima2. Now supports:
- TypeScript (.ts) and TSX
- Vue 3 Composition API (<script setup>)
- Standard Option API

Performance: Uses a persistent Node.js worker process that stays alive for the
entire analysis session, communicating via stdin/stdout JSON protocol. This is
10–50× faster than spawning a new subprocess per file.
"""

import json
import subprocess
import os
import tempfile
import threading
import atexit

# ============================================================
# PERSISTENT WORKER — Keeps a single Node.js process alive
# ============================================================

class _PersistentWorker:
    """A persistent Node.js subprocess that accepts parse requests over stdin/stdout."""
    
    def __init__(self):
        self._process = None
        self._lock = threading.Lock()
        self._script_path = os.path.join(os.path.dirname(__file__), "ts_parser", "parse_node.js")
    
    def _ensure_alive(self):
        """Start the worker process if it isn't running."""
        if self._process is not None and self._process.poll() is None:
            return True
        
        try:
            # Start Node.js in "worker mode" — reads file paths from stdin, writes JSON to stdout
            self._process = subprocess.Popen(
                ["node", self._script_path, "--worker"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                bufsize=1,  # Line-buffered
            )
            return True
        except Exception as e:
            print(f"  -> [AST] Failed to start persistent worker: {e}")
            self._process = None
            return False

    def parse(self, tmp_file_path):
        """Send a file to the worker and get the parsed JSON back."""
        with self._lock:
            if not self._ensure_alive():
                return None
            
            try:
                # Send the temp file path followed by a newline
                self._process.stdin.write(tmp_file_path + "\n")
                self._process.stdin.flush()
                
                # Read one line of JSON response
                response_line = self._process.stdout.readline().strip()
                if not response_line:
                    return None
                
                return json.loads(response_line)
            except (BrokenPipeError, OSError, json.JSONDecodeError) as e:
                # Worker crashed — kill it so next call restarts
                print(f"  -> [AST] Worker pipe error: {e}, will restart on next call")
                self._kill()
                return None
    
    def _kill(self):
        """Terminate the worker process."""
        if self._process is not None:
            try:
                self._process.terminate()
                self._process.wait(timeout=3)
            except Exception:
                try:
                    self._process.kill()
                except Exception:
                    pass
            self._process = None
    
    def shutdown(self):
        """Cleanly shut down the worker."""
        with self._lock:
            self._kill()


# Module-level singleton
_worker = _PersistentWorker()
atexit.register(_worker.shutdown)


def parse_source(content, file_name):
    """
    Parse the script block of a Vue file or a raw JS/TS file using a Node.js helper.
    Uses a persistent worker process for speed; falls back to subprocess.run() if it fails.
    """
    # Extract extension from file_name, default to .vue
    _, ext = os.path.splitext(file_name)
    suffix = ext.lower() if ext else ".vue"
    
    fd, tmp_file = tempfile.mkstemp(suffix=suffix, text=True)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(content)

    try:
        # Try the persistent worker first (fast path)
        result = _worker.parse(tmp_file)
        if result is not None:
            if "error" in result:
                print(f"  -> [AST] Worker parser error: {result['error']}")
                return None
            return result
        
        # Fallback: classic subprocess.run() per-file (slow path)
        script_path = os.path.join(os.path.dirname(__file__), "ts_parser", "parse_node.js")
        
        proc = subprocess.run(
            ["node", script_path, tmp_file],
            capture_output=True,
            text=True,
            encoding='utf-8',
            check=True
        )
        
        if proc.stderr:
            print(proc.stderr)
        
        output = proc.stdout.strip()
        
        lines = output.split('\n')
        json_output = lines[-1] if lines else "{}"
        
        try:
            parsed = json.loads(json_output)
            if "error" in parsed:
                print(f"  -> [AST] Fallback parser error: {parsed['error']}")
                return None
            return parsed
        except json.JSONDecodeError:
            # Fallback if multiple lines of JSON output
            parsed = json.loads(output)
            if "error" in parsed:
                return None
            return parsed
        
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
