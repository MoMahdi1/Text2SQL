import re
from dataclasses import dataclass

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from app.exceptions import UnsafeSQLError


@dataclass(frozen=True)
class ValidatedSQL:
    sql: str


class SQLValidator:
    """Allow one read-only MySQL query that only references inspected tables."""

    _blocked_schemas = {"information_schema", "mysql", "performance_schema", "sys"}
    _dangerous_text = re.compile(
        r"\b(INTO\s+(?:OUTFILE|DUMPFILE)|LOAD_FILE\s*\(|SLEEP\s*\(|BENCHMARK\s*\()",
        re.IGNORECASE,
    )

    def validate(self, sql: str, allowed_tables: frozenset[str]) -> ValidatedSQL:
        candidate = sql.strip()
        if not candidate:
            raise UnsafeSQLError("The model returned an empty SQL query.")
        if self._dangerous_text.search(candidate):
            raise UnsafeSQLError("The SQL contains a blocked MySQL operation.")

        try:
            statements = sqlglot.parse(candidate, read="mysql")
        except ParseError as exc:
            raise UnsafeSQLError("The generated SQL is not valid MySQL syntax.") from exc

        if len(statements) != 1:
            raise UnsafeSQLError("Exactly one SQL statement is allowed.")

        statement = statements[0]
        if not isinstance(statement, exp.Query):
            raise UnsafeSQLError("Only SELECT queries are allowed.")
        if statement.find(exp.Lock):
            raise UnsafeSQLError("Locking SELECT queries are not allowed.")

        allowed_table_names = {name.lower() for name in allowed_tables}
        cte_names = {
            cte.alias_or_name.lower()
            for cte in statement.find_all(exp.CTE)
            if cte.alias_or_name
        }
        for table in statement.find_all(exp.Table):
            schema_name = (table.db or "").lower()
            table_name = table.name.lower()
            if schema_name in self._blocked_schemas:
                raise UnsafeSQLError("Access to system schemas is not allowed.")
            if schema_name:
                raise UnsafeSQLError("Schema-qualified table names are not allowed.")
            if table_name not in allowed_table_names and table_name not in cte_names:
                raise UnsafeSQLError(f"Table '{table.name}' is not part of the application schema.")

        normalized = statement.sql(dialect="mysql", pretty=False)
        return ValidatedSQL(sql=normalized)
