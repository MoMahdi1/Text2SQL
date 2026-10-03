import pytest

from app.exceptions import UnsafeSQLError
from app.sql_validator import SQLValidator


ALLOWED_TABLES = frozenset({"employees", "departments", "attendance_records"})


@pytest.fixture
def validator() -> SQLValidator:
    return SQLValidator()


def test_accepts_simple_select(validator: SQLValidator) -> None:
    result = validator.validate(
        "SELECT first_name, salary FROM employees ORDER BY salary DESC",
        ALLOWED_TABLES,
    )
    assert result.sql.startswith("SELECT")


def test_accepts_cte_select(validator: SQLValidator) -> None:
    result = validator.validate(
        "WITH active AS (SELECT * FROM employees WHERE is_active = 1) SELECT * FROM active",
        ALLOWED_TABLES,
    )
    assert result.sql.startswith("WITH")


def test_accepts_read_only_attendance_query(validator: SQLValidator) -> None:
    result = validator.validate(
        """
        SELECT e.first_name, e.last_name, a.check_in_time, a.late_minutes
        FROM attendance_records AS a
        JOIN employees AS e ON e.id = a.employee_id
        WHERE a.work_date = CURDATE() AND a.is_late = TRUE
        """,
        ALLOWED_TABLES,
    )
    assert "attendance_records" in result.sql


def test_cte_cannot_hide_unknown_source_table(validator: SQLValidator) -> None:
    with pytest.raises(UnsafeSQLError):
        validator.validate(
            "WITH hidden AS (SELECT * FROM secret_table) SELECT * FROM hidden",
            ALLOWED_TABLES,
        )


@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE employees SET salary = 0",
        "DELETE FROM employees",
        "DROP TABLE employees",
        "SELECT * FROM employees; SELECT * FROM departments",
        "SELECT * FROM information_schema.tables",
        "SELECT * FROM another_database.employees",
        "SELECT * FROM secret_table",
        "SELECT * FROM employees INTO OUTFILE '/tmp/data.csv'",
        "SELECT * FROM employees FOR UPDATE",
        "SELECT SLEEP(5)",
        "",
    ],
)
def test_rejects_unsafe_sql(validator: SQLValidator, sql: str) -> None:
    with pytest.raises(UnsafeSQLError):
        validator.validate(sql, ALLOWED_TABLES)
