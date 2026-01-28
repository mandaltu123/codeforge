import json
import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class RunResult:
    exit_code: int
    stdout: str
    stderr: str
    time_ms: int


class SandboxError(Exception):
    pass


def run_in_docker(code: str, *, timeout_ms: int, memory_mb: int, cpus: float, max_stdout_kb: int) -> RunResult:
    """
    Executes code in python:3.11-slim with:
      - no network
      - resource limits (cpu/mem)
      - timeout
      - ephemeral workspace
    """
    start = time.time()
    base_dir = os.environ.get("SANDBOX_HOST_DIR", "/tmp/llmexec")
    os.makedirs(base_dir, exist_ok=True)
    tmpdir = tempfile.mkdtemp(prefix="llmexec_", dir=base_dir)
    try:
        script_path = os.path.join(tmpdir, "main.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code)

        # IMPORTANT: --network none prevents outbound calls
        docker_bin = os.environ.get("DOCKER_BIN") or shutil.which("docker")
        if not docker_bin:
            raise SandboxError("SANDBOX_DOCKER_UNAVAILABLE: docker CLI not found in PATH")

        cmd = [
            docker_bin, "run", "--rm",
            "--network", "none",
            "--cpus", str(cpus),
            "-m", f"{memory_mb}m",
            "-v", f"{tmpdir}:/work:ro",   # read-only mount
            "-w", "/work",
            "python:3.11-slim",
            "python", "-I", "main.py"
        ]

        # Run with timeout
        try:
            completed = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_ms / 1000.0
            )
        except subprocess.TimeoutExpired as e:
            raise SandboxError(f"SANDBOX_TIMEOUT: exceeded {timeout_ms}ms") from e
        except FileNotFoundError as e:
            raise SandboxError("SANDBOX_DOCKER_UNAVAILABLE: docker CLI not found") from e
        except PermissionError as e:
            raise SandboxError("SANDBOX_DOCKER_UNAVAILABLE: permission denied accessing docker") from e

        stdout = completed.stdout or ""
        stderr = completed.stderr or ""

        # Cap stdout size
        max_bytes = max_stdout_kb * 1024
        if len(stdout.encode("utf-8", errors="ignore")) > max_bytes:
            raise SandboxError(f"STDOUT_TOO_LARGE: > {max_stdout_kb}KB")

        time_ms = int((time.time() - start) * 1000)
        return RunResult(completed.returncode, stdout, stderr, time_ms)

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def parse_stdout_json(stdout: str) -> Optional[Dict[str, Any]]:
    s = (stdout or "").strip()
    if not s:
        return None
    # Expect exactly ONE JSON line; tolerate trailing newlines
    lines = [ln for ln in s.splitlines() if ln.strip() != ""]
    if len(lines) != 1:
        raise SandboxError("OUTPUT_FORMAT_ERROR: stdout must be exactly one non-empty JSON line")
    try:
        obj = json.loads(lines[0])
    except json.JSONDecodeError as e:
        raise SandboxError(f"OUTPUT_NOT_JSON: {e}") from e
    if not isinstance(obj, dict):
        raise SandboxError("OUTPUT_SCHEMA_ERROR: JSON must be an object/dict")
    return obj
