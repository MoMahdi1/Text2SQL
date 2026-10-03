from dataclasses import dataclass

from sqlalchemy import Engine, text


@dataclass(frozen=True)
class DatabaseSchema:
    prompt_text: str
    table_names: frozenset[str]


class SchemaInspector:
    """Read the current MySQL schema so Gemini only sees real tables and columns."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def inspect(self) -> DatabaseSchema:
        statement = text(
            """
            SELECT
                c.TABLE_NAME,
                c.COLUMN_NAME,
                c.COLUMN_TYPE,
                c.IS_NULLABLE,
                c.COLUMN_KEY,
                c.EXTRA
            FROM information_schema.COLUMNS AS c
            WHERE c.TABLE_SCHEMA = DATABASE()
            ORDER BY c.TABLE_NAME, c.ORDINAL_POSITION
            """
        )

        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()

        if not rows:
            raise RuntimeError("No tables were found in the configured database.")

        tables: dict[str, list[str]] = {}
        for row in rows:
            flags = []
            if row["COLUMN_KEY"]:
                flags.append(str(row["COLUMN_KEY"]))
            if row["EXTRA"]:
                flags.append(str(row["EXTRA"]))
            nullable = "NULL" if row["IS_NULLABLE"] == "YES" else "NOT NULL"
            suffix = f" ({', '.join(flags)})" if flags else ""
            column = f"  - {row['COLUMN_NAME']}: {row['COLUMN_TYPE']} {nullable}{suffix}"
            tables.setdefault(str(row["TABLE_NAME"]), []).append(column)

        lines = []
        for table_name, columns in tables.items():
            lines.append(f"Table `{table_name}`:")
            lines.extend(columns)

        return DatabaseSchema(
            prompt_text="\n".join(lines),
            table_names=frozenset(tables),
        )

