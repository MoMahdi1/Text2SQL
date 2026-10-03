from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.dependencies import get_agent
from app.exceptions import AgentError
from app.schemas import HealthResponse, QueryRequest, QueryResponse
from app.workflow import SQLAgentWorkflow

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="Employee SQL Agent",
    version="1.0.0",
    description="A read-only natural-language-to-SQL agent for employee data.",
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.exception_handler(AgentError)
async def handle_agent_error(_request: Request, exc: AgentError) -> JSONResponse:
    """Return expected agent/configuration failures in the API's JSON format."""

    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/api/query", response_model=QueryResponse)
async def query_database(
    request: QueryRequest,
    agent: SQLAgentWorkflow = Depends(get_agent),
) -> QueryResponse:
    try:
        state = await run_in_threadpool(agent.run, request.question.strip())
    except AgentError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="The agent could not complete the request. Check the API and database configuration.",
        ) from exc

    rows = state.get("rows", [])
    return QueryResponse(
        question=request.question.strip(),
        sql=state["validated_sql"],
        columns=state.get("columns", []),
        rows=rows,
        row_count=len(rows),
        truncated=state.get("truncated", False),
        steps=state.get("steps", []),
    )
