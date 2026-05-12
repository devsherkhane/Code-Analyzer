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
USE_JSON_MODE = os.environ.get("USE_JSON_MODE", "false").lower() == "true"

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
        return OpenAI(api_key=api_key, base_url=base_url, timeout=300.0)
    except Exception as e:
        print(f"  -> [ERROR] Failed to initialize client: {e}", flush=True)
        return None

def call_ai(client, prompt, json_mode=True, max_retries=5):
    """
    Call the AI engine via OpenAI-compatible API.
    Handles messy responses from smaller models (gemma3 4.3B etc.)
    with aggressive JSON extraction and repair strategies.
    """
    import re
    model_name = os.environ.get("LLM_MODEL", "gemma2-9b")
    last_error = None

    def _extract_json_robust(text):
        """Multi-strategy JSON extraction — handles markdown, preamble, arrays, etc."""
        if not text or not text.strip():
            return None

        t = text.strip()

        # Strategy 1: Direct parse (best case)
        try:
            json.loads(t)
            return t
        except:
            pass

        # Strategy 2: Strip markdown code fences (```json ... ``` or ``` ... ```)
        md_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', t)
        if md_match:
            candidate = md_match.group(1).strip()
            try:
                json.loads(candidate)
                return candidate
            except:
                pass

        # Strategy 3: Find outermost JSON object { ... }
        brace_start = t.find('{')
        brace_end = t.rfind('}')
        if brace_start != -1 and brace_end > brace_start:
            candidate = t[brace_start:brace_end + 1]
            try:
                json.loads(candidate)
                return candidate
            except:
                pass

        # Strategy 4: Find outermost JSON array [ ... ]
        bracket_start = t.find('[')
        bracket_end = t.rfind(']')
        if bracket_start != -1 and bracket_end > bracket_start:
            candidate = t[bracket_start:bracket_end + 1]
            try:
                json.loads(candidate)
                return candidate
            except:
                pass

        # Strategy 5: Try to repair common issues
        # Remove trailing commas before } or ]
        if brace_start != -1 and brace_end > brace_start:
            candidate = t[brace_start:brace_end + 1]
            candidate = re.sub(r',\s*([}\]])', r'\1', candidate)
            # Fix single quotes to double quotes
            candidate = candidate.replace("'", '"')
            try:
                json.loads(candidate)
                return candidate
            except:
                pass

        return None

    for attempt in range(max_retries + 1):
        rate_limiter.wait()
        try:
            kwargs = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": "You are an expert code analyst. CRITICAL: You MUST respond with ONLY valid JSON. No text before or after the JSON. No markdown code fences. No explanations. Start your response with { and end with }. Every response must be parseable by JSON.parse()."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 8192,
                "top_p": 0.85,
            }
            
            # Only set response_format when the backend supports it (e.g., OpenAI).
            # Ollama/Gemma returns 400 when json_object is requested.
            if json_mode and USE_JSON_MODE:
                kwargs["response_format"] = {"type": "json_object"}

            response = client.chat.completions.create(**kwargs)
            
            # Guard against None response (Open WebUI/Ollama can return this)
            backoff = min(2 ** attempt, 30)
            if response is None:
                print(f"  -> [GEMMA] Response was None (Attempt {attempt+1}), retrying in {backoff}s...", flush=True)
                time.sleep(backoff)
                continue
            
            if not response.choices or len(response.choices) == 0:
                print(f"  -> [GEMMA] Empty choices in response (Attempt {attempt+1}), retrying in {backoff}s...", flush=True)
                time.sleep(backoff)
                continue

            text = response.choices[0].message.content
            
            if not text or not text.strip():
                print(f"  -> [GEMMA] Empty content in response (Attempt {attempt+1}), retrying in {backoff}s...", flush=True)
                time.sleep(backoff)
                continue
            
            # Robust JSON extraction with multiple fallback strategies
            extracted = _extract_json_robust(text)
            
            if extracted:
                print(f"  -> [GEMMA OK] {model_name} responded ({len(extracted)} chars, attempt {attempt+1})", flush=True)
                return extracted, model_name
            
            # All extraction strategies failed
            if attempt == max_retries:
                # Log what the model actually returned for debugging
                preview = text.strip()[:300].replace('\n', '\\n').encode('ascii', 'ignore').decode('ascii')
                print(f"  -> [GEMMA] Final attempt failed. Model response preview: {preview}", flush=True)
                raise json.JSONDecodeError("Failed to parse AI response as JSON", text[:200], 0)
            
            backoff_json = min(2 ** attempt, 30)
            preview = text.strip()[:150].replace('\n', '\\n').encode('ascii', 'ignore').decode('ascii')
            print(f"  -> [GEMMA] Invalid JSON on attempt {attempt+1} (preview: {preview}...), retrying in {backoff_json}s...", flush=True)
            time.sleep(backoff_json)
            continue

        except json.JSONDecodeError:
            raise  # Re-raise JSON errors from the final attempt
        except Exception as e:
            error_str = str(e).encode('ascii', 'ignore').decode('ascii')
            last_error = e
            print(f"  -> [GEMMA ATTEMPT] {model_name} failed (Attempt {attempt+1}): {error_str[:150]}", flush=True)

            if "405" in error_str:
                print("     [HINT] 405 Method Not Allowed implies the /v1 suffix might be incorrect for your server.", flush=True)
            
            if "429" in error_str or "rate" in error_str.lower():
                wait = (attempt + 1) * 10
                print(f"     [RATE LIMIT] Waiting {wait}s...", flush=True)
                time.sleep(wait)
                continue
            
            # For other errors, retry with exponential backoff
            backoff_err = min(2 ** attempt, 30)
            time.sleep(backoff_err)

    raise Exception(f"Gemma API exhausted after {max_retries+1} attempts. Last error: {last_error}")


# Compat alias
call_groq = call_ai
MODEL_CHAIN = [os.environ.get("LLM_MODEL", "gemma2-9b")]
