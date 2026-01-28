from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List


class Constraints(BaseModel):
    timeout_ms: int = Field(default=5000, ge=100, le=15000)
    memory_mb: int = Field(default=256, ge=64, le=2048)
    cpus: float = Field(default=0.5, ge=0.1, le=4.0)
    max_stdout_kb: int = Field(default=32, ge=4, le=256)


class CodegenRequest(BaseModel):
    task: str = Field(min_length=1, max_length=4000)
    output_schema: Dict[str, Any] = Field(default_factory=lambda: {"type": "object"})
    constraints: Constraints = Field(default_factory=Constraints)


class CodegenResponse(BaseModel):
    status: str
    code: str
    language: str = "python"
    notes: Optional[str] = None


class ExecuteRequest(BaseModel):
    code: str = Field(min_length=1, max_length=20000)
    constraints: Constraints = Field(default_factory=Constraints)


class ExecuteResponse(BaseModel):
    status: str
    stdout_json: Optional[Dict[str, Any]] = None
    raw_stdout: str = ""
    raw_stderr: str = ""
    exit_code: int = 0
    time_ms: int = 0


class SolveRequest(BaseModel):
    task: str = Field(min_length=1, max_length=4000)
    output_schema: Dict[str, Any] = Field(default_factory=lambda: {"type": "object"})
    constraints: Constraints = Field(default_factory=Constraints)


class SolveResponse(BaseModel):
    status: str
    code: str
    result: Optional[Dict[str, Any]] = None
    execution: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[Dict[str, Any]] = None
