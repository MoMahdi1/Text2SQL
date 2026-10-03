from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from app.attendance import attendance_policy_prompt
from app.exceptions import ConfigurationError


class SQLDraft(BaseModel):
    sql: str = Field(description="One MySQL SELECT query with no markdown fencing.")


class GeminiSQLGenerator:
    """Generate one structured SQL draft using the official Google GenAI SDK."""

    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise ConfigurationError(
                "GEMINI_API_KEY is missing. Copy .env.example to .env and add the key."
            )
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def generate(self, question: str, schema: str) -> str:
        prompt = f"""
You are a careful MySQL data analyst.

Convert the user's question into exactly one read-only SELECT query.
Rules:
- Use only the tables and columns in the supplied schema.
- SELECT and WITH ... SELECT are allowed.
- Never use INSERT, UPDATE, DELETE, REPLACE, CREATE, ALTER, DROP, TRUNCATE,
  GRANT, REVOKE, CALL, LOAD, INTO OUTFILE, INTO DUMPFILE, or multiple statements.
- Do not access MySQL system schemas or functions that read files or delay execution.
- Prefer explicit JOIN conditions and clear aliases.
- Do not invent columns.

Business rules:
{attendance_policy_prompt()}

Database schema:
{schema}

User question:
{question}
""".strip()

        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0,
                response_mime_type="application/json",
                response_schema=SQLDraft,
            ),
        )

        if isinstance(response.parsed, SQLDraft):
            return response.parsed.sql
        if response.text:
            return SQLDraft.model_validate_json(response.text).sql
        raise RuntimeError("Gemini returned no SQL response.")
