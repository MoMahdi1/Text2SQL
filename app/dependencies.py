from functools import lru_cache

from app.config import get_settings
from app.database import get_engine
from app.gemini_client import GeminiSQLGenerator
from app.schema_inspector import SchemaInspector
from app.sql_executor import SQLExecutor
from app.sql_validator import SQLValidator
from app.workflow import SQLAgentWorkflow


@lru_cache
def get_agent() -> SQLAgentWorkflow:
    settings = get_settings()
    engine = get_engine()
    return SQLAgentWorkflow(
        inspector=SchemaInspector(engine),
        generator=GeminiSQLGenerator(settings.gemini_api_key, settings.gemini_model),
        validator=SQLValidator(),
        executor=SQLExecutor(
            engine,
            row_limit=settings.query_row_limit,
            timeout_ms=settings.query_timeout_ms,
        ),
    )

