from app.schema_inspector import SchemaInspector


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def mappings(self):
        return self

    def all(self):
        return self._rows


class FakeConnection:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, _statement):
        return FakeResult(
            [
                {
                    "TABLE_NAME": "attendance_records",
                    "COLUMN_NAME": "employee_id",
                    "COLUMN_TYPE": "int unsigned",
                    "IS_NULLABLE": "NO",
                    "COLUMN_KEY": "MUL",
                    "EXTRA": "",
                },
                {
                    "TABLE_NAME": "attendance_records",
                    "COLUMN_NAME": "is_late",
                    "COLUMN_TYPE": "tinyint(1)",
                    "IS_NULLABLE": "YES",
                    "COLUMN_KEY": "",
                    "EXTRA": "STORED GENERATED",
                },
                {
                    "TABLE_NAME": "employees",
                    "COLUMN_NAME": "id",
                    "COLUMN_TYPE": "int unsigned",
                    "IS_NULLABLE": "NO",
                    "COLUMN_KEY": "PRI",
                    "EXTRA": "auto_increment",
                },
            ]
        )


class FakeEngine:
    def connect(self):
        return FakeConnection()


def test_schema_inspector_exposes_attendance_table_and_generated_columns() -> None:
    schema = SchemaInspector(FakeEngine()).inspect()

    assert schema.table_names == frozenset({"attendance_records", "employees"})
    assert "Table `attendance_records`:" in schema.prompt_text
    assert "is_late: tinyint(1) NULL (STORED GENERATED)" in schema.prompt_text

