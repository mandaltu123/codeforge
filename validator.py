import ast
from typing import Set


ALLOWED_IMPORTS: Set[str] = {"json", "math", "statistics"}

BANNED_NAMES: Set[str] = {
    "open", "exec", "eval", "__import__", "compile", "input",
    "globals", "locals", "vars", "dir", "help",
}

BANNED_MODULES_PREFIX: Set[str] = {
    "os", "sys", "subprocess", "socket", "pathlib", "shutil",
    "requests", "http", "urllib", "importlib",
}


class ValidationError(Exception):
    pass


def validate_python_code(code: str) -> None:
    """
    Static safety checks. Runtime isolation still required.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise ValidationError(f"SyntaxError: {e}") from e

    for node in ast.walk(tree):
        # Block imports not in allowlist
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if mod.split(".")[0] not in ALLOWED_IMPORTS:
                    raise ValidationError(f"ImportFrom not allowed: {mod}")
            else:
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    if top not in ALLOWED_IMPORTS:
                        raise ValidationError(f"Import not allowed: {alias.name}")

        # Block dangerous names usage
        if isinstance(node, ast.Name) and node.id in BANNED_NAMES:
            raise ValidationError(f"Banned name used: {node.id}")

        # Block attribute access to banned modules (best-effort)
        if isinstance(node, ast.Attribute):
            # e.g. os.system, sys.exit
            if isinstance(node.value, ast.Name) and node.value.id in BANNED_MODULES_PREFIX:
                raise ValidationError(f"Banned module access: {node.value.id}.{node.attr}")

        # Block calls of banned names
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in BANNED_NAMES:
                raise ValidationError(f"Banned call: {node.func.id}()")

    # Ensure code prints something JSON-like (soft check)
    if "json.dumps" not in code or "print(" not in code:
        raise ValidationError("Code must print a single JSON line via json.dumps(...)")
