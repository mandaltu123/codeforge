# Interview Notes: Model, Invocation, and Generation Flow

## What model is used
- The project uses a **local LLM** served by **Ollama**.
- Default model name: `llama3.1:latest` (configurable via `OLLAMA_MODEL`).
- The model runs inside a Docker container named `ollama` when using Compose.

## Key terminology
- **LLM (Large Language Model)**: a neural network trained on text to generate responses.
- **Prompt**: the input instruction sent to the model.
- **Inference**: the process of running the model to produce output.
- **Token**: a chunk of text processed by the model.
- **Temperature**: controls randomness; lower values make outputs more deterministic.
- **Schema**: a JSON shape definition used to guide output format.
- **Code generation**: using an LLM to produce code as text.
- **Validation**: static checks to prevent unsafe code.
- **Sandbox**: isolated runtime (Docker) used to execute generated code safely.

## How the model is invoked
1. Client calls `POST /v1/codegen` or `POST /v1/solve`.
2. `generate_python()` in `llm.py` builds a strict prompt:
   - Must output **Python only**.
   - Must print **exactly one JSON line** via `json.dumps`.
   - Must not perform IO or network calls.
   - Must follow the given `output_schema`.
3. The API sends a POST request to Ollama:
   - URL: `${OLLAMA_URL}/api/generate` (default `http://ollama:11434`)
   - Payload: `{ "model": "...", "prompt": "...", "stream": false, "options": { "temperature": 0.1 } }`
4. Ollama returns a JSON response with the generated text in `response`.
5. The code is cleaned (code fences removed) and returned to the client.

## How the code is generated
- The prompt instructs the model to **emit a complete Python script**.
- The script must end by printing a single JSON object.
- Example of expected output:
```
import json
nums = [1, 2, 3, 4, 30]
avg = sum(nums) / len(nums)
print(json.dumps({"average": avg}))
```

## How the result is produced (/v1/solve)
1. **Codegen**: LLM generates Python code.
2. **Validation** (`validator.py`):
   - Only allow safe imports (`json`, `math`, `statistics`).
   - Block dangerous names (`open`, `exec`, `eval`, etc.).
3. **Sandbox execution** (`sandbox.py`):
   - Runs code inside a Docker container (`python:3.11-slim`).
   - Network is disabled and resource limits are enforced.
   - Output must be exactly one JSON line.
4. API returns:
   - Generated code
   - Execution output
   - Exit code + timing

## Why we do it this way
- **Safety**: validation + sandbox prevents harmful behavior.
- **Determinism**: low temperature reduces randomness.
- **Observability**: API returns code and execution metadata.
- **Portability**: local Ollama avoids external API keys.

## Common errors and meanings
- `LLM_ERROR / OLLAMA_UNAVAILABLE`: Ollama not reachable.
- `OLLAMA_MODEL_NOT_FOUND`: requested model not pulled.
- `CODE_VALIDATION_ERROR`: generated code violates rules.
- `SANDBOX_TIMEOUT`: execution exceeded time limit.

## How to talk about it in interviews
- “We use a local LLM via Ollama to generate Python code from prompts.”
- “We enforce a strict output contract: one JSON line printed via `json.dumps`.”
- “We validate the code statically and run it in a Docker sandbox with no network.”
- “The design prioritizes safety and deterministic outputs.”

## Interview Q&A (theory + project specific)

### 1) What is an LLM?
**Answer:** A Large Language Model is a neural network trained on massive text corpora to predict the next token. It can generate text, code, and structured outputs when prompted.

### 2) What is inference?
**Answer:** Inference is running a trained model to generate outputs (tokens) from an input prompt. It’s the runtime phase, not training.

### 3) What is a token?
**Answer:** A token is a chunk of text (word piece) the model processes. Costs, latency, and context length are measured in tokens.

### 4) What does temperature mean?
**Answer:** Temperature controls randomness in sampling. Lower values (e.g., 0–0.2) make outputs more deterministic; higher values increase creativity but reduce reliability.

### 5) What is prompt engineering?
**Answer:** It’s the practice of designing prompts to guide the model toward a desired output. Here, we enforce code-only output and a strict JSON printing contract.

### 6) How does the model get called in this project?
**Answer:** `llm.py` builds a prompt and sends it to Ollama’s `/api/generate` endpoint. Ollama returns the generated Python code as text.

### 7) Why use Ollama?
**Answer:** It runs locally, avoids external API keys, and gives full control over models and latency.

### 8) What is the output contract and why?
**Answer:** The generated program must print exactly one JSON line via `json.dumps`. This makes parsing deterministic and enables strict validation.

### 9) How do you validate generated code?
**Answer:** `validator.py` uses AST parsing to block unsafe imports and dangerous functions (e.g., `exec`, `eval`, `open`).

### 10) Why use a sandbox?
**Answer:** Running untrusted code is risky. The Docker sandbox isolates execution, disables network, and enforces CPU/memory/time limits.

### 11) What happens if the LLM returns invalid code?
**Answer:** The validator raises `CODE_VALIDATION_ERROR`, and the API returns a structured error instead of executing it.

### 12) What is schema guidance?
**Answer:** We pass `output_schema` in the prompt so the model shapes JSON output accordingly.

### 13) What are typical failure modes?
**Answer:** Model not available, LLM output not valid Python, output not JSON, sandbox timeout, or resource limits.

### 14) How do you make outputs deterministic?
**Answer:** Lower temperature, strict prompt rules, and a fixed output format reduce variance.

### 15) What is the difference between /v1/codegen and /v1/solve?
**Answer:** `/v1/codegen` returns only the generated code. `/v1/solve` generates, validates, and executes the code in the sandbox and returns the result.

### 16) How would you scale this system?
**Answer:** Add request queues, model caching, autoscale Ollama workers, and separate the codegen and execution services.

### 17) How do you ensure security?
**Answer:** Static validation + strict allowlist + Docker sandbox with no network and resource limits.

### 18) Why return both code and results?
**Answer:** It’s transparent and debuggable—users can see exactly what was executed.
