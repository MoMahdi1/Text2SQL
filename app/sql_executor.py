from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.exceptions import DatabaseExecutionError


@dataclass(frozen=True)
class QueryResult:
    columns: list[str]
    rows: list[dict[str, Any]]
    truncated: bool


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


class SQLExecutor:
    """Execute validated SQL through a database account with SELECT-only grants."""

    def __init__(self, engine: Engine, row_limit: int, timeout_ms: int) -> None:
        self._engine = engine
        self._row_limit = row_limit
        self._timeout_ms = timeout_ms

    def execute(self, sql: str) -> QueryResult:
        try:
            with self._engine.connect() as connection:
                connection.execute(text(f"SET SESSION MAX_EXECUTION_TIME = {self._timeout_ms}"))
                result = connection.execute(text(sql))
                columns = list(result.keys())
                raw_rows = result.mappings().fetchmany(self._row_limit + 1)
        except SQLAlchemyError as exc:
            raise DatabaseExecutionError(
                "The database could not execute the generated query."
            ) from exc

        truncated = len(raw_rows) > self._row_limit
        rows = [
            {key: _json_safe(value) for key, value in row.items()}
            for row in raw_rows[: self._row_limit]
        ]
        return QueryResult(columns=columns, rows=rows, truncated=truncated)

