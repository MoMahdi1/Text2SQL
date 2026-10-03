from app.schema_inspector import DatabaseSchema
from app.sql_executor import QueryResult
from app.sql_validator import SQLValidator
from app.workflow import SQLAgentWorkflow


class FakeInspector:
    def inspect(self) -> DatabaseSchema:
        return DatabaseSchema(
            prompt_text="Table `employees`:\n  - first_name: varchar(80)",
            table_names=frozenset({"employees"}),
        )


class FakeGenerator:
    def generate(self, question: str, schema: str) -> str:
        assert "employees" in schema
        return "SELECT first_name FROM employees ORDER BY first_name"


class FakeExecutor:
    def execute(self, sql: str) -> QueryResult:
        assert sql.startswith("SELECT")
        return QueryResult(
            columns=["first_name"],
            rows=[{"first_name": "Ahmed"}],
            truncated=False,
        )


class FakeAttendanceInspector:
    def inspect(self) -> DatabaseSchema:
        return DatabaseSchema(
            prompt_text=(
                "Table `employees`:\n  - id: int\n"
                "Table `attendance_records`:\n"
                "  - employee_id: int\n  - work_date: date\n"
                "  - is_late: tinyint\n  - late_minutes: smallint"
            ),
            table_names=frozenset({"employees", "attendance_records"}),
        )


class FakeAttendanceGenerator:
    def generate(self, question: str, schema: str) -> str:
        assert "attendance_records" in schema
        return (
            "SELECT e.first_name, a.late_minutes "
            "FROM attendance_records AS a "
            "JOIN employees AS e ON e.id = a.employee_id "
            "WHERE a.work_date = CURDATE() AND a.is_late = TRUE"
        )


class FakeAttendanceExecutor:
    def execute(self, sql: str) -> QueryResult:
        assert "attendance_records" in sql
        assert "is_late" in sql
        return QueryResult(
            columns=["first_name", "late_minutes"],
            rows=[{"first_name": "Youssef", "late_minutes": 1}],
            truncated=False,
        )


def test_workflow_runs_all_four_steps() -> None:
    workflow = SQLAgentWorkflow(
        inspector=FakeInspector(),
        generator=FakeGenerator(),
        validator=SQLValidator(),
        executor=FakeExecutor(),
    )

    result = workflow.run("List employee names")

    assert result["rows"] == [{"first_name": "Ahmed"}]
    assert [step["name"] for step in result["steps"]] == [
        "Schema inspected",
        "SQL generated",
        "SQL validated",
        "SQL executed",
    ]


def test_workflow_can_query_attendance_records() -> None:
    workflow = SQLAgentWorkflow(
        inspector=FakeAttendanceInspector(),
        generator=FakeAttendanceGenerator(),
        validator=SQLValidator(),
        executor=FakeAttendanceExecutor(),
    )

    result = workflow.run("Who was late today?")

    assert result["rows"] == [{"first_name": "Youssef", "late_minutes": 1}]
    assert "attendance_records" in result["validated_sql"]
