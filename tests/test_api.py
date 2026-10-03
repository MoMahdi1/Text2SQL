from fastapi.testclient import TestClient

from app.dependencies import get_agent
from app.exceptions import ConfigurationError
from app.main import app


class FakeAgent:
    def run(self, question: str):
        return {
            "validated_sql": "SELECT first_name FROM employees",
            "columns": ["first_name"],
            "rows": [{"first_name": "Omar"}],
            "truncated": False,
            "steps": [
                {"name": "Schema inspected", "detail": "Found 2 tables."},
                {"name": "SQL generated", "detail": "Gemini created a SQL draft."},
                {"name": "SQL validated", "detail": "Query is read-only."},
                {"name": "SQL executed", "detail": "Returned 1 row."},
            ],
        }


def override_agent() -> FakeAgent:
    return FakeAgent()


app.dependency_overrides[get_agent] = override_agent
client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_query_endpoint() -> None:
    response = client.post("/api/query", json={"question": "List employee names"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["row_count"] == 1
    assert payload["rows"] == [{"first_name": "Omar"}]
    assert payload["sql"] == "SELECT first_name FROM employees"


def test_query_rejects_too_short_question() -> None:
    response = client.post("/api/query", json={"question": "a"})
    assert response.status_code == 422


def test_configuration_error_is_returned_as_json() -> None:
    def misconfigured_agent():
        raise ConfigurationError("GEMINI_API_KEY is missing.")

    app.dependency_overrides[get_agent] = misconfigured_agent
    try:
        response = client.post("/api/query", json={"question": "List employees"})
    finally:
        app.dependency_overrides[get_agent] = override_agent

    assert response.status_code == 400
    assert response.json() == {"detail": "GEMINI_API_KEY is missing."}


def test_frontend_is_served() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Ask your employee data" in response.text
    assert "Late today" in response.text
    assert "Missing check-out" in response.text
