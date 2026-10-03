from typing import Any

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class WorkflowStep(BaseModel):
    name: str
    detail: str


class QueryResponse(BaseModel):
    question: str
    sql: str
    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int
    truncated: bool
    steps: list[WorkflowStep]


class HealthResponse(BaseModel):
    status: str

