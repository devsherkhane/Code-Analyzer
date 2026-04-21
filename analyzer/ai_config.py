"""
Unified AI Configuration for Code Analyzer.
Uses OPENWEBUI_API_KEY / OPENWEBUI_BASE_URL from root .env
"""
import os
import json
import time
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables — always prefer the project root .env
_this_dir = os.path.dirname(os.path.abspath(__file__))
_root_env = os.path.normpath(os.path.join(_this_dir, "..", ".env"))

if os.path.exists(_root_env):
    load_dotenv(_root_env, override=True)
elif os.path.exists(".env"):
    load_dotenv(".env")
else:
    load_dotenv()

# ============================================================
# CONFIGURATION
# ============================================================
MIN_CALL_DELAY = 1

class RateLimiter:
    def __init__(self, min_delay=MIN_CALL_DELAY):
        self._last_call = 0
        self._min_delay = min_delay

    def wait(self):
        now = time.time()
        elapsed = now - self._last_call
        if elapsed < self._min_delay:
            wait_time = self._min_delay - elapsed
            time.sleep(wait_time)
        self._last_call = time.time()

rate_limiter = RateLimiter()

# ============================================================
# CLIENT FACTORY
# ============================================================
def get_client():
    """Returns the OpenAI-compatible client pointing at OpenWebUI/Gemma."""
    api_key = os.environ.get("OPENWEBUI_API_KEY")
    base_url = os.environ.get("OPENWEBUI_BASE_URL")
    
    if not api_key or not base_url:
        print("  -> [CRITICAL] Missing OPENWEBUI_API_KEY or OPENWEBUI_BASE_URL in .env", flush=True)
        return None

    # Standardize base URL for OpenAI SDK — needs /api/v1 suffix
    base_url = base_url.rstrip("/")
    if not base_url.endswith("/v1"):
        if base_url.endswith("/api"):
            base_url += "/v1"
        else:
            base_url += "/api/v1"
        
    print(f"  -> [AI] Using LLM Engine (Base: {base_url})", flush=True)
    try:
        return OpenAI(api_key=api_key, base_url=base_url, timeout=120.0)
    except Exception as e:
        print(f"  -> [ERROR] Failed to initialize client: {e}", flush=True)
        return None

def call_ai(client, prompt, json_mode=True, max_retries=3):
    """
    Call the Gemma AI engine via OpenAI-compatible API.
    Handles servers that don't support response_format by auto-retrying without it.
    """
    model_name = os.environ.get("LLM_MODEL", "gemma2-9b")
    last_error = None

    for attempt in range(max_retries + 1):
        rate_limiter.wait()
        try:
            kwargs = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": "You are an Elite Principal AI Software Architect. You provide deep, exhaustive, and highly technical architectural audits. Never be generic. Always reference specific line numbers and code patterns from the provided source. Be verbose and comprehensive in your descriptions and suggestions. Always respond with valid JSON only. Do not wrap your response in markdown code blocks."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.5,
                "max_tokens": 4096,
                "top_p": 0.9,
            }
            
            # Try with json_mode first, but be ready to fall back
            use_json_format = json_mode and attempt == 0
            if use_json_format:
                kwargs["response_format"] = {"type": "json_object"}

            response = client.chat.completions.create(**kwargs)
            
            # Guard against None response (Open WebUI/Ollama can return this)
            if response is None:
                print(f"  -> [GEMMA] Response was None (Attempt {attempt+1}), retrying...", flush=True)
                time.sleep(2)
                continue
            
            if not response.choices or len(response.choices) == 0:
                print(f"  -> [GEMMA] Empty choices in response (Attempt {attempt+1}), retrying...", flush=True)
                time.sleep(2)
                continue

            text = response.choices[0].message.content
            
            if not text or not text.strip():
                print(f"  -> [GEMMA] Empty content in response (Attempt {attempt+1}), retrying...", flush=True)
                time.sleep(2)
                continue
            
            # Robust JSON extraction
            original_text = text.strip()
            
            def extract_json(t):
                # Try finding the first '{' and last '}'
                try:
                    start_idx = t.find('{')
                    end_idx = t.rfind('}')
                    if start_idx != -1 and end_idx != -1:
                        return t[start_idx:end_idx+1]
                except: pass
                return t

            extracted = extract_json(original_text)
            
            # Try parsing to validate
            try:
                json.loads(extracted)
                print(f"  -> [GEMMA OK] {model_name} responded ({len(extracted)} chars, attempt {attempt+1})", flush=True)
                return extracted, model_name
            except json.JSONDecodeError:
                # If JSON parsing fails, try one more time to strip markdown fences if they are there
                if "```" in original_text:
                    import re
                    match = re.search(r'```(?:json)?\s*(.*?)\s*```', original_text, re.DOTALL)
                    if match:
                        try:
                            candidate = match.group(1).strip()
                            json.loads(candidate)
                            print(f"  -> [GEMMA OK] {model_name} responded (extracted from MD code block, attempt {attempt+1})", flush=True)
                            return candidate, model_name
                        except: pass
                
                # If it's a retry and it still failed, maybe it's just text
                if attempt == max_retries:
                    print(f"  -> [GEMMA] Final attempt failed to produce valid JSON.", flush=True)
                    raise json.JSONDecodeError("Failed to parse AI response as JSON", extracted, 0)
                
                print(f"  -> [GEMMA] Invalid JSON on attempt {attempt+1}, retrying...", flush=True)
                time.sleep(2)
                continue

        except Exception as e:
            error_str = str(e)
            last_error = e
            print(f"  -> [GEMMA ATTEMPT] {model_name} failed (Attempt {attempt+1}): {error_str[:150]}", flush=True)

            if "405" in error_str:
                print("     [HINT] 405 Method Not Allowed implies the /v1 suffix might be incorrect for your server.", flush=True)
            
            if "429" in error_str or "rate" in error_str.lower():
                wait = (attempt + 1) * 10
                print(f"     [RATE LIMIT] Waiting {wait}s...", flush=True)
                time.sleep(wait)
                continue
            
            # For other errors, just retry with delay
            time.sleep(2)

    raise Exception(f"Gemma API exhausted after {max_retries+1} attempts. Last error: {last_error}")

# Compat alias
call_groq = call_ai
MODEL_CHAIN = [os.environ.get("LLM_MODEL", "gemma2-9b")]
