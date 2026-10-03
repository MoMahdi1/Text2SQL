from typing import Any, Protocol, TypedDict

from langgraph.graph import END, START, StateGraph

from app.schema_inspector import DatabaseSchema
from app.sql_executor import QueryResult
from app.sql_validator import ValidatedSQL


class Inspector(Protocol):
    def inspect(self) -> DatabaseSchema: ...


class Generator(Protocol):
    def generate(self, question: str, schema: str) -> str: ...


class Validator(Protocol):
    def validate(self, sql: str, allowed_tables: frozenset[str]) -> ValidatedSQL: ...


class Executor(Protocol):
    def execute(self, sql: str) -> QueryResult: ...


class AgentState(TypedDict, total=False):
    question: str
    schema_text: str
    allowed_tables: frozenset[str]
    generated_sql: str
    validated_sql: str
    columns: list[str]
    rows: list[dict[str, Any]]
    truncated: bool
    steps: list[dict[str, str]]


class SQLAgentWorkflow:
    """LangGraph workflow: inspect schema, generate SQL, validate, then execute."""

    def __init__(
        self,
        inspector: Inspector,
        generator: Generator,
        validator: Validator,
        executor: Executor,
    ) -> None:
        self._inspector = inspector
        self._generator = generator
        self._validator = validator
        self._executor = executor
        self._graph = self._build_graph()

    @staticmethod
    def _append_step(state: AgentState, name: str, detail: str) -> list[dict[str, str]]:
        return [*state.get("steps", []), {"name": name, "detail": detail}]

    def _inspect_schema(self, state: AgentState) -> AgentState:
        schema = self._inspector.inspect()
        return {
            "schema_text": schema.prompt_text,
            "allowed_tables": schema.table_names,
            "steps": self._append_step(
                state, "Schema inspected", f"Found {len(schema.table_names)} tables."
            ),
        }

    def _generate_sql(self, state: AgentState) -> AgentState:
        sql = self._generator.generate(state["question"], state["schema_text"])
        return {
            "generated_sql": sql,
            "steps": self._append_step(state, "SQL generated", "Gemini created a SQL draft."),
        }

    def _validate_sql(self, state: AgentState) -> AgentState:
        validated = self._validator.validate(
            state["generated_sql"], state["allowed_tables"]
        )
        return {
            "validated_sql": validated.sql,
            "steps": self._append_step(
                state, "SQL validated", "The query passed the read-only safety policy."
            ),
        }

    def _execute_sql(self, state: AgentState) -> AgentState:
        result = self._executor.execute(state["validated_sql"])
        return {
            "columns": result.columns,
            "rows": result.rows,
            "truncated": result.truncated,
            "steps": self._append_step(
                state, "SQL executed", f"Returned {len(result.rows)} rows."
            ),
        }

    def _build_graph(self):
        builder = StateGraph(AgentState)
        builder.add_node("inspect_schema", self._inspect_schema)
        builder.add_node("generate_sql", self._generate_sql)
        builder.add_node("validate_sql", self._validate_sql)
        builder.add_node("execute_sql", self._execute_sql)
        builder.add_edge(START, "inspect_schema")
        builder.add_edge("inspect_schema", "generate_sql")
        builder.add_edge("generate_sql", "validate_sql")
        builder.add_edge("validate_sql", "execute_sql")
        builder.add_edge("execute_sql", END)
        return builder.compile()

    def run(self, question: str) -> AgentState:
        return self._graph.invoke({"question": question, "steps": []})

