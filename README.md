# CodeForge

**LLM → Code → Sandbox Execute pipeline.** Give it a task in plain English; it generates Python, validates the syntax, runs it in an isolated Docker container, and returns structured JSON output.

## What It Does

1. **Prompt** — POST a natural language task + expected JSON output schema
2. **Generate** — Local LLaMA (via Ollama) writes Python that prints exactly one JSON line
3. **Validate** — AST-based static analysis catches syntax errors before execution
4. **Execute** — Code runs inside a Docker sandbox with strict CPU, memory, and timeout limits
5. **Return** — Validated JSON output is returned to the caller

This is the same pattern as cloud code-interpreter products — built locally, fully self-contained.

## Architecture

```
POST /v1/solve
      │
      ▼
  LLM (Ollama / LLaMA 3.1)  ──generates──►  Python code
                                                  │
                                                  ▼
                                          AST Validator
                                                  │
                                                  ▼
                                          Docker Sandbox
                                          (timeout + memory)
                                                  │
                                                  ▼
                                          JSON output
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/v1/codegen` | Generate Python from a natural language task |
| POST | `/v1/execute` | Execute pre-written Python in the sandbox |
| POST | `/v1/solve` | End-to-end: generate + validate + execute |

## Quick Start

**Prerequisites:** Docker, Python 3.11+, [Ollama](https://ollama.ai) with `llama3.1`

```bash
ollama pull llama3.1

pip install -r requirements.txt
cp .env.example .env

uvicorn app:app --reload
```

## Example

```bash
curl -X POST http://localhost:8000/v1/solve \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Generate the first 10 fibonacci numbers",
    "output_schema": {"numbers": "list of integers"}
  }'
```

```json
{
  "status": "ok",
  "output": {"numbers": [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]}
}
```

## Sandbox Limits (defaults)

| Limit | Value |
|---|---|
| Timeout | 10 seconds |
| Memory | 128 MB |
| CPUs | 0.5 |
| Max stdout | 64 KB |

## Tech Stack

- **LLM**: Ollama + LLaMA 3.1 (local, no API key needed)
- **API**: FastAPI + Uvicorn
- **Sandbox**: Docker subprocess isolation
- **Validation**: Python `ast` module
- **Schema**: Pydantic v2

## Project Structure

```
codeforge/
├── app.py            # FastAPI routes
├── llm.py            # Ollama client + prompt engineering
├── validator.py      # AST-based code validator
├── sandbox.py        # Docker sandbox execution
├── models.py         # Pydantic request/response models
├── requirements.txt
└── docker-compose.yml
```
