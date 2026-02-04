# Local LLM (Ollama) and Code Generation

This project now uses a local LLM via Ollama in `llm.py`.
The API sends a prompt to Ollama and expects Python code back.
Ollama must be running locally for `/v1/codegen` and `/v1/solve` to work.

## How code is generated
- `generate_python()` builds a strict prompt with the task and `output_schema`.
- Ollama is called at `http://localhost:11434/api/generate` (configurable via `OLLAMA_URL`).
- The model returns Python code as plain text.
- The code must print exactly one JSON line via `json.dumps`.

## How the average is calculated
When the task asks for an average, the model should emit code like:

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

## Notes on the LLM contract
Keep these constraints to preserve API behavior:
- Generate Python only.
- Ensure the program prints exactly one JSON line via `json.dumps`.
- Avoid banned imports and functions (see `validator.py`).

## Docker vs local URL
When using Docker Compose, the API talks to the `ollama` service at `http://ollama:11434` by default.
You can override this with `OLLAMA_URL` if needed.

## Model size note
If you see memory errors, use a smaller model like `llama3.1:latest` by setting `OLLAMA_MODEL`.
