# LLM Stub and Code Generation

This project currently uses a deterministic stub in `llm.py` instead of a real LLM.
The stub is intentionally simple so the end-to-end flow (generate → validate → execute)
can be tested without external dependencies.

## How code is generated
- The task string is lowercased.
- Numbers are extracted with a regex (`-?\d+(?:\.\d+)?`) and converted into a Python list.
- Keyword matching chooses a code template:
  - `average`, `avg`, or `mean`
  - `sum` or `total`
  - `min` or `minimum`
  - `max` or `maximum`
- The template produces Python that prints exactly one JSON line with `json.dumps`.

## How the average is calculated
When the task contains `average`/`avg`/`mean`, the stub emits code like:

```python
import json
nums = [1, 2, 3, 4, 30]
avg = (sum(nums) / len(nums)) if nums else None
print(json.dumps({"average": avg}))
```

If no numbers are found, `nums` is empty and `avg` becomes `None`.

## Output format contract
The validator and sandbox expect exactly one non-empty JSON line on stdout.
If the code prints anything else or multiple lines, the sandbox returns an error.

## Replacing the stub with a real LLM
Swap out `generate_python()` in `llm.py` with a real LLM call.
Keep these constraints to preserve API behavior:
- Generate Python only.
- Ensure the program prints exactly one JSON line via `json.dumps`.
- Avoid banned imports and functions (see `validator.py`).
