# Employee SQL Agent

A complete interview-ready V1 that converts plain-English questions into safe,
read-only MySQL queries. It uses Gemini for SQL generation, LangGraph for the
workflow, FastAPI for the API, and a responsive HTML/CSS/JavaScript frontend.

## What it does

1. Inspects the live MySQL schema.
2. Sends the question and schema to Gemini using structured output.
3. Parses and validates the generated SQL.
4. Executes the query through a MySQL user that has `SELECT` permission only.
5. Displays the rows, generated SQL, and workflow steps in the browser.

The sample database contains four departments, ten employees, and varied
attendance records for the current and recent days.

## Attendance policy

- Default shift start: `09:00`
- Default shift end: `17:00`
- Grace period: `15` minutes
- An employee is late only after `09:15:00` with the default policy.
- Partial late minutes are rounded up, so `09:15:01` is one minute late.
- A `NULL` `check_out_time` means the employee has checked in but has not yet
  checked out.

The `attendance_records` table persists the shift start, shift end, and grace
period used for each record. This keeps historical calculations correct if the
policy changes later. MySQL generates `is_late` and `late_minutes`, and a unique
constraint allows only one record per employee per work date.

## Architecture

```text
Browser
   |
   v
FastAPI POST /api/query
   |
   v
LangGraph: inspect_schema -> generate_sql -> validate_sql -> execute_sql
                  |                |                 |
               Gemini          SQLGlot       MySQL read-only user
```

## Technical decisions

- **Python 3.11+**: required for a modern async-compatible stack.
- **MySQL 8.4**: runs in Docker for a repeatable reviewer setup.
- **Google GenAI SDK**: the current official Gemini Python SDK.
- **Gemini structured output**: asks the model for a typed JSON object instead
  of scraping SQL from Markdown.
- **LangGraph StateGraph**: makes every agent step explicit and testable.
- **SQLGlot**: parses SQL into an AST. String matching alone is not considered a
  sufficient safety boundary.
- **Defense in depth**: SQL must pass the parser policy and then runs using a
  database account granted `SELECT` only. System schemas, multiple statements,
  file access, delay functions, and unknown tables are rejected.
- **Plain frontend**: HTML, CSS, and JavaScript keep the take-home assignment
  easy to run and review without adding a separate Node build pipeline.
- **Stateless requests**: each question is independent. Conversation memory was
  intentionally excluded from this focused V1.
- **Result limits**: the API returns at most 100 rows by default and sets a MySQL
  execution-time limit.

## Prerequisites

- Python 3.11 or newer
- Docker Desktop with Docker Compose
- A Gemini API key

## Setup and run (PowerShell)

Run all commands from the project root.

### 1. Create and activate a virtual environment

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation for the current process:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -e ".[test]"
```

### 3. Configure `.env`

```powershell
Copy-Item .env.example .env
notepad .env
```

Replace `replace_with_your_gemini_api_key` with the real key. Never commit the
`.env` file.

### 4. Initialize and seed the database

For a new Docker volume, the first command creates the schema, the read-only
user, the ten sample employees, and the attendance samples automatically:

```powershell
docker compose up -d mysql
docker compose ps
```

Wait until the container status says `healthy`.

To run both idempotent seed scripts again manually:

```powershell
Get-Content database/seed.sql -Raw | docker compose exec -T mysql mysql -uroot -proot_password employee_ai
Get-Content database/seed_attendance.sql -Raw | docker compose exec -T mysql mysql -uroot -proot_password employee_ai
```

### Update an existing database without deleting employee data

Docker initialization files run only when MySQL creates a new empty data
volume. `docker compose up` will **not** apply the new attendance table to an
existing volume.

First, take a backup:

```powershell
docker compose exec -T mysql mysqldump -uroot -proot_password --single-transaction employee_ai | Set-Content -Encoding utf8 employee_ai-backup.sql
```

Apply the additive migration. It creates the table if missing, preserves all
employee and department rows, and refreshes the `readonly_user` SELECT grant:

```powershell
Get-Content database/migrations/001_add_attendance_records.sql -Raw | docker compose exec -T mysql mysql -uroot -proot_password employee_ai
```

Optionally add the sample attendance rows without changing employee rows:

```powershell
Get-Content database/seed_attendance.sql -Raw | docker compose exec -T mysql mysql -uroot -proot_password employee_ai
```

Verify the migration through the read-only account:

```powershell
docker compose exec -T mysql mysql -ureadonly_user -preadonly_password employee_ai -e "SELECT COUNT(*) AS attendance_count FROM attendance_records;"
```

Only if a completely disposable local database must be rebuilt from scratch,
the following removes its Docker volume and all database data:

```powershell
docker compose down -v
docker compose up -d mysql
```

Do not use the destructive reset for a database whose employee data must be
preserved.

### 5. Run tests

```powershell
pytest
```

Optional coverage report:

```powershell
pytest --cov=app --cov-report=term-missing
```

The automated tests use fakes for Gemini and MySQL, so they are deterministic
and do not spend API quota.

### 6. Start the API and frontend

```powershell
uvicorn app.main:app --reload
```

Open:

- Frontend: <http://127.0.0.1:8000>
- Swagger API documentation: <http://127.0.0.1:8000/docs>
- Health check: <http://127.0.0.1:8000/api/health>

## Example questions

- `List all active employees with their department names.`
- `Which department has the highest average salary?`
- `Show employees hired after January 1, 2023 ordered by hire date.`
- `How many employees work in each department?`
- `Who was late today?`
- `Who checked in after the grace period this week?`
- `Who checked in without checking out?`
- `Show Omar Hassan's attendance history.`
- `مين اتأخر النهارده؟`
- `مين حضر بعد فترة السماح الأسبوع ده؟`
- `مين سجل حضور من غير انصراف؟`

## API example

```powershell
$body = @{ question = "Which department has the highest average salary?" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/query -ContentType "application/json" -Body $body
```

Successful response shape:

```json
{
  "question": "Which department has the highest average salary?",
  "sql": "SELECT ...",
  "columns": ["department", "average_salary"],
  "rows": [{"department": "Engineering", "average_salary": 25125.0}],
  "row_count": 1,
  "truncated": false,
  "steps": [
    {"name": "Schema inspected", "detail": "Found 2 tables."},
    {"name": "SQL generated", "detail": "Gemini created a SQL draft."},
    {"name": "SQL validated", "detail": "The query passed the read-only safety policy."},
    {"name": "SQL executed", "detail": "Returned 1 rows."}
  ]
}
```

## API endpoints

- `GET /` — frontend
- `GET /api/health` — process health
- `POST /api/query` — run the complete agent workflow
- `GET /docs` — interactive OpenAPI documentation

## Security notes and V1 boundaries

- The application database user cannot modify data.
- Only one parsed `SELECT` or `WITH ... SELECT` statement is accepted.
- Queries may reference application tables only.
- `readonly_user` receives `SELECT` on `employee_ai.*`, including the attendance
  table, and cannot insert or update attendance records.
- MySQL file-reading/writing and delay functions are blocked.
- Results and execution time are limited.
- Attendance records assume a same-day shift; overnight shifts are outside this
  V1 because `check_out_time` must be greater than or equal to `check_in_time`.
- Attendance seed dates are relative to `CURDATE()`. Re-running the seed on the
  same day updates those samples; running it on a later day adds new dated
  samples and does not delete older attendance history.
- This V1 is intentionally unauthenticated and intended for local interview
  review. Before internet deployment, add authentication, rate limiting,
  audit logging, secret management, stricter network isolation, and TLS.

## Troubleshooting

### MySQL port 3306 is already in use

Stop the existing MySQL service or change the host side of the Compose port,
for example `3307:3306`, then update `DATABASE_URL` to use port `3307`.

### Database credentials appear incorrect after changing Compose settings

MySQL initialization scripts only run for a new data volume. Recreate it:

```powershell
docker compose down -v
docker compose up -d mysql
```

### Gemini returns a model or quota error

Confirm the API key is valid and that `GEMINI_MODEL` in `.env` is available to
that Google AI project. The model name is configurable without code changes.

## Project structure

```text
employee-sql-agent/
|-- app/
|   |-- static/             # Browser UI
|   |-- config.py
|   |-- database.py
|   |-- dependencies.py
|   |-- gemini_client.py
|   |-- main.py
|   |-- schema_inspector.py
|   |-- schemas.py
|   |-- sql_executor.py
|   |-- sql_validator.py
|   `-- workflow.py
|-- database/
|   |-- init.sql
|   |-- migrations/
|   |   `-- 001_add_attendance_records.sql
|   |-- seed.sql
|   `-- seed_attendance.sql
|-- tests/
|-- .env.example
|-- docker-compose.yml
|-- pyproject.toml
`-- README.md
```
