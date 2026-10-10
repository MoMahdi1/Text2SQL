
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from app.attendance import attendance_policy_prompt
from app.exceptions import ConfigurationError


class SQLDraft(BaseModel):
    sql: str = Field(description="One MySQL SELECT query with no markdown fencing.")


class GeminiSQLGenerator:
    """Generate one structured, read-only SQL query using Google GenAI."""

    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise ConfigurationError(
                "GEMINI_API_KEY is missing. Copy .env.example to .env and add the key."
            )

        self._client = genai.Client(api_key=api_key)
        self._model = model

    def generate(self, question: str, schema: str) -> str:
        prompt = f"""
You are a careful MySQL data analyst for an employee attendance system.

Your task is to convert the user's natural-language question into exactly
one read-only MySQL SELECT query that answers the question accurately.

STRICT SQL SAFETY RULES:
- Use only tables and columns explicitly present in the supplied schema.
- Only SELECT queries and WITH ... SELECT queries are allowed.
- Never use INSERT, UPDATE, DELETE, REPLACE, CREATE, ALTER, DROP, TRUNCATE,
  GRANT, REVOKE, CALL, LOAD, INTO OUTFILE, INTO DUMPFILE, or multiple statements.
- Do not access MySQL system schemas or functions that read files or delay execution.
- Never invent table names, column names, or relationships.
- Use explicit JOIN conditions and clear aliases.
- Do not return markdown or explanations; return only the SQL in the required JSON format.
- Follow the supplied business rules.

EMPLOYEE ATTENDANCE QUERY REQUIREMENTS:
- When the user asks who was late, return each matching employee's full name
  using CONCAT(e.first_name, ' ', e.last_name) AS employee_name.
- When the schema supports it, JOIN employees to departments using the actual
  foreign key and return d.name AS department_name.
- For attendance questions, return the relevant attendance date.
- When available in the schema, return check_in_time, shift_start_time,
  grace_period_minutes, late_minutes, and is_late as appropriate.
- Use the actual late_minutes column when it exists. Do not calculate a different
  definition of lateness in the query.
- For questions about lateness, filter using the database's is_late column
  when available.
- For "today", use CURDATE(). For "yesterday", use DATE_SUB(CURDATE(), INTERVAL 1 DAY).
- For a specified date or date range, use the date the user actually requested.
- For weekly questions, use a date range consistent with the user's wording.
- Use ORDER BY to make attendance results easy to read, such as late_minutes DESC.
- For employee history, return the employee's attendance dates and relevant
  check-in/check-out information.
- For missing check-outs, filter for check_out_time IS NULL.
- Do not add columns unrelated to the user's question unless they help explain
  the attendance result.
- Do not use LIMIT if it would omit matching employees from a question asking
  for all matching employees.

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
