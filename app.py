from fastapi import FastAPI, HTTPException
from models import (
    CodegenRequest, CodegenResponse,
    ExecuteRequest, ExecuteResponse,
    SolveRequest, SolveResponse
)
from llm import generate_python, LLMError
from validator import validate_python_code, ValidationError
from sandbox import run_in_docker, parse_stdout_json, SandboxError

app = FastAPI(
    title="LLM → Code → Execute",
    version="1.0.0",
    description="Generate Python via LLM, validate, execute in Docker sandbox, return JSON output."
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/v1/codegen", response_model=CodegenResponse)
def codegen(req: CodegenRequest):
    try:
        code = generate_python(req.task, req.output_schema)
    except LLMError as e:
        raise HTTPException(status_code=503, detail={"type": "LLM_ERROR", "message": str(e)})

    try:
        validate_python_code(code)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail={"type": "CODE_VALIDATION_ERROR", "message": str(e), "code": code})

    return CodegenResponse(status="ok", code=code)


@app.post("/v1/execute", response_model=ExecuteResponse)
def execute(req: ExecuteRequest):
    # validate user-provided code too
    try:
        validate_python_code(req.code)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail={"type": "CODE_VALIDATION_ERROR", "message": str(e)})

    c = req.constraints
    try:
        rr = run_in_docker(
            req.code,
            timeout_ms=c.timeout_ms,
            memory_mb=c.memory_mb,
            cpus=c.cpus,
            max_stdout_kb=c.max_stdout_kb
        )
        out_obj = parse_stdout_json(rr.stdout)
    except SandboxError as e:
        raise HTTPException(status_code=400, detail={"type": "SANDBOX_ERROR", "message": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"type": "INTERNAL_ERROR", "message": str(e)})

    status = "ok" if rr.exit_code == 0 else "error"
    return ExecuteResponse(
        status=status,
        stdout_json=out_obj,
        raw_stdout=rr.stdout,
        raw_stderr=rr.stderr,
        exit_code=rr.exit_code,
        time_ms=rr.time_ms
    )


@app.post("/v1/solve", response_model=SolveResponse)
def solve(req: SolveRequest):
    # 1) codegen
    try:
        code = generate_python(req.task, req.output_schema)
    except LLMError as e:
        return SolveResponse(
            status="error",
            code="",
            error={"type": "LLM_ERROR", "message": str(e)}
        )

    try:
        validate_python_code(code)
    except ValidationError as e:
        return SolveResponse(
            status="error",
            code=code,
            error={"type": "CODE_VALIDATION_ERROR", "message": str(e)}
        )

    # 2) execute
    c = req.constraints
    try:
        rr = run_in_docker(
            code,
            timeout_ms=c.timeout_ms,
            memory_mb=c.memory_mb,
            cpus=c.cpus,
            max_stdout_kb=c.max_stdout_kb
        )
        out_obj = parse_stdout_json(rr.stdout)
    except SandboxError as e:
        return SolveResponse(
            status="error",
            code=code,
            error={"type": "SANDBOX_ERROR", "message": str(e)}
        )
    except Exception as e:
        return SolveResponse(
            status="error",
            code=code,
            error={"type": "INTERNAL_ERROR", "message": str(e)}
        )

    if rr.exit_code != 0 and out_obj is None:
        return SolveResponse(
            status="error",
            code=code,
            error={
                "type": "EXECUTION_ERROR",
                "message": rr.stderr.strip() or "Non-zero exit without JSON output"
            },
            execution={"exit_code": rr.exit_code, "time_ms": rr.time_ms}
        )

    return SolveResponse(
        status="ok" if rr.exit_code == 0 else "error",
        code=code,
        result=out_obj,
        execution={"exit_code": rr.exit_code, "time_ms": rr.time_ms}
    )
