import json
import os
import time
import urllib.error
import urllib.request
from typing import Dict


def _build_prompt(task: str, output_schema: dict) -> str:
    schema = json.dumps(output_schema, ensure_ascii=True)
    return f"""You are a code generator. Return ONLY valid Python code.
Rules:
- Output a single program that prints exactly one JSON line via json.dumps.
- Do not print anything else.
- Use only the Python standard library.
- Do not read files or make network calls.
- The printed JSON must match this schema: {schema}

Task: {task}
"""


class LLMError(Exception):
    pass


def _call_ollama(prompt: str) -> str:
    url = os.environ.get("OLLAMA_URL", "http://localhost:11434")
    model = os.environ.get("OLLAMA_MODEL", "llama3.1")
    timeout_s = float(os.environ.get("OLLAMA_TIMEOUT", "30"))
    retries = int(os.environ.get("OLLAMA_RETRIES", "5"))

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
        },
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{url.rstrip('/')}/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                body = resp.read().decode("utf-8")
            obj = json.loads(body)
            return obj.get("response", "").strip()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise LLMError("OLLAMA_MODEL_NOT_FOUND: model not available in Ollama") from e
            raise LLMError(f"OLLAMA_HTTP_ERROR: {e}") from e
        except urllib.error.URLError as e:
            last_err = e
            if attempt < retries - 1:
                time.sleep(0.5 * (2 ** attempt))
                continue
            raise LLMError(f"OLLAMA_UNAVAILABLE: {e}") from e
        except json.JSONDecodeError as e:
            raise LLMError(f"OLLAMA_BAD_RESPONSE: {e}") from e
    raise LLMError(f"OLLAMA_UNAVAILABLE: {last_err}")



def _strip_code_fences(code: str) -> str:
    s = code.strip()
    if s.startswith("```"):
        lines = s.splitlines()
        # drop the first line (``` or ```python)
        if lines:
            lines = lines[1:]
        # drop trailing ``` if present
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        s = "\n".join(lines).strip()
    return s

def generate_python(task: str, output_schema: Dict) -> str:
    """
    Generate Python code using a local Ollama model.
    Must print a single JSON line.
    """
    prompt = _build_prompt(task, output_schema)
    return _strip_code_fences(_call_ollama(prompt))
