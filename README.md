# LLM -> Code -> Execute (FastAPI + Docker sandbox)

## Prereqs
- Docker running
- Python 3.10+

## Setup
```
pip install -r requirements.txt
```

## Local LLM (Ollama) setup
If you run the API via Docker Compose, Ollama starts as a service automatically.
After the containers are up, pull a model inside the Ollama container:
```
docker compose exec ollama ollama pull llama3.1:latest
```
If you run locally without Compose, install Ollama and pull a model:
```
ollama pull llama3.1:latest
```
Run Ollama (if not already running):
```
ollama serve
```
Set environment variables (optional):
```
export OLLAMA_URL="http://localhost:11434"
export OLLAMA_MODEL="llama3.1:latest"
export OLLAMA_TIMEOUT="30"
export OLLAMA_RETRIES="5"
```

## Pull sandbox image once
```
docker pull python:3.11-slim
```

## Run API (local)
```
uvicorn app:app --reload --port 8000
```

## Run API (Docker Compose)
```
DOCKER_SOCK="${DOCKER_SOCK:-$HOME/.docker/run/docker.sock}" docker compose up --build -d
```

## Stop / restart Docker Compose
```
DOCKER_SOCK="${DOCKER_SOCK:-$HOME/.docker/run/docker.sock}" docker compose stop
DOCKER_SOCK="${DOCKER_SOCK:-$HOME/.docker/run/docker.sock}" docker compose up -d
```

## Rebuild and restart Docker Compose
```
DOCKER_SOCK="${DOCKER_SOCK:-$HOME/.docker/run/docker.sock}" docker compose down
DOCKER_SOCK="${DOCKER_SOCK:-$HOME/.docker/run/docker.sock}" docker compose up --build -d
```

## Docker sandbox permissions
The API container needs access to the Docker socket to run the sandbox.
Compose runs the service as root by default via `user: "0:0"` in `docker-compose.yml`.
If you remove that, make sure the container user can read/write `/var/run/docker.sock`.

## Docker Desktop (macOS) socket
If you are on macOS with Docker Desktop, set `DOCKER_SOCK` (or keep the defaults used above):
```
export DOCKER_SOCK="$HOME/.docker/run/docker.sock"
```
You can also add `DOCKER_SOCK=$HOME/.docker/run/docker.sock` to a `.env` file.

## Docker CLI not found
If you see `SANDBOX_DOCKER_UNAVAILABLE: docker CLI not found`, rebuild without cache:
```
DOCKER_SOCK="${DOCKER_SOCK:-$HOME/.docker/run/docker.sock}" docker compose build --no-cache
DOCKER_SOCK="${DOCKER_SOCK:-$HOME/.docker/run/docker.sock}" docker compose up -d
```
You can also set `DOCKER_BIN` if Docker is in a custom location.

## Note on Docker CLI
The image installs the Docker CLI from Docker's official Debian repo so `docker` is available in PATH.

## Shared temp directory for sandbox
The sandbox runs a nested Docker container and needs a host-mounted temp dir.
Compose mounts `/tmp/llmexec` into the container; ensure the host path exists and is writable.
You can override the path with `SANDBOX_HOST_DIR` if needed.

## LLM stub (how code is generated)
`llm.py` now calls a local LLM via Ollama. The prompt asks for Python that prints exactly one
JSON line with `json.dumps`, and the response is executed after validation and sandboxing.

## Swagger
Open:
http://localhost:8000/docs

## Try /v1/solve
```
POST /v1/solve
{
  "task": "find average of 1,2,3,4,30"
}
```

## Curl tests
Recommended order after starting the server:
1) `/v1/codegen` to verify the LLM returns Python.
2) `/v1/execute` to verify the sandbox can run Python.
3) `/v1/solve` to test the full generate -> validate -> execute flow.

### /v1/codegen
```
curl -sS -X POST http://localhost:8000/v1/codegen \
  -H 'Content-Type: application/json' \
  -d '{"task":"find average of 1,2,3,4,30"}'
```

### /v1/execute
```
curl -sS -X POST http://localhost:8000/v1/execute \
  -H 'Content-Type: application/json' \
  -d '{"code":"import json\nnums=[1,2,3,4,30]\navg=sum(nums)/len(nums)\nprint(json.dumps({\"average\":avg}))\n"}'
```

### /v1/solve
```
curl -sS -X POST http://localhost:8000/v1/solve \
  -H 'Content-Type: application/json' \
  -d '{"task":"find average of 1,2,3,4,30"}'
```

## Timeout
If you see `SANDBOX_TIMEOUT`, increase `constraints.timeout_ms` in your request.

## LLM errors
If you see `LLM_ERROR` or `OLLAMA_UNAVAILABLE`, ensure Ollama is running and `OLLAMA_URL` is reachable.
