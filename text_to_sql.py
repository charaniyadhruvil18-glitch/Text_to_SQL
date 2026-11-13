import os
import re
import sqlite3
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import APIStatusError, OpenAI, OpenAIError


ROOT = Path(__file__).resolve().parent
DATABASE_PATH = ROOT / "sales.db"
MAX_ROWS = 50
GREEN = "\033[32m"
RED = "\033[31m"
CYAN = "\033[36m"
RESET = "\033[0m"
ALLOWED_SQL_ACTIONS = {
    sqlite3.SQLITE_SELECT,
    sqlite3.SQLITE_READ,
    sqlite3.SQLITE_FUNCTION,
    sqlite3.SQLITE_RECURSIVE,
}


def get_schema() -> str:
    with sqlite3.connect(DATABASE_PATH) as connection:
        tables = connection.execute(
            """
            SELECT sql
            FROM sqlite_master
            WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()
    return "\n".join(row[0] for row in tables)


def generate_sql(schema: str, question: str) -> str:
    load_dotenv(ROOT / ".env")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Add your Gemini API key to the .env file."
        )

    client = OpenAI(
        api_key=api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )
    response = client.chat.completions.create(
        model="gemini-4-hydrogen",
        messages=[
            {
                "role": "system",
                "content": (
                    "Convert the user's question into one SQLite SELECT query "
                    "using only the provided schema. Return ONLY SQL, with no "
                    "markdown or explanation. Never return a write query."
                ),
            },
            {
                "role": "user",
                "content": f"Schema:\n{schema}\n\nQuestion:\n{question}",
            },
        ],
    )
    message = response.choices[0].message.content
    if not isinstance(message, str) or not message.strip():
        raise ValueError("Gemini returned an empty or unsupported response.")
    sql = message.strip()
    if sql.startswith("```"):
        sql = re.sub(r"\A```(?:sql)?\s*|\s*```\Z", "", sql, flags=re.IGNORECASE).strip()
    sql = sql.rstrip(";").strip()
    if not re.match(r"\A(?:SELECT|WITH)\b", sql, flags=re.IGNORECASE):
        raise ValueError("The model did not return a SELECT query.")
    return sql


def run_query(sql: str) -> list[dict[str, object]]:
    database_uri = f"{DATABASE_PATH.as_uri()}?mode=ro"
    with sqlite3.connect(database_uri, uri=True) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        connection.set_authorizer(
            lambda action, _arg1, _arg2, _database, _trigger: (
                sqlite3.SQLITE_OK
                if action in ALLOWED_SQL_ACTIONS
                else sqlite3.SQLITE_DENY
            )
        )
        cursor = connection.execute(sql)
        rows = cursor.fetchmany(MAX_ROWS + 1)
        return [dict(row) for row in rows[:MAX_ROWS]]


def print_schema() -> None:
    schema = get_schema()
    print(f"\n{CYAN}Database schema:{RESET}")
    print(schema if schema else "(No tables found.)")


def print_table(rows: list[dict[str, object]]) -> None:
    if not rows:
        print("(No results.)")
        return

    headers = list(rows[0])
    values = [[str(row.get(header, "")) for header in headers] for row in rows]
    widths = [
        max(len(header), *(len(row[index]) for row in values))
        for index, header in enumerate(headers)
    ]

    def format_row(row: list[str]) -> str:
        return "| " + " | ".join(
            value.ljust(widths[index]) for index, value in enumerate(row)
        ) + " |"

    separator = "+-" + "-+-".join("-" * width for width in widths) + "-+"
    print(separator)
    print(format_row(headers))
    print(separator)
    for row in values:
        print(format_row(row))
    print(separator)


def main() -> None:
    if not DATABASE_PATH.exists():
        print(
            f"{RED}sales.db is missing. Run `python create_db.py` first.{RESET}",
            file=sys.stderr,
        )
        return

    load_dotenv(ROOT / ".env")
    if not os.getenv("GEMINI_API_KEY"):
        print(
            f"{RED}GEMINI_API_KEY is missing. Add it to the .env file.{RESET}",
            file=sys.stderr,
        )
        return

    try:
        print(f"{GREEN}Welcome to the Text-to-SQL console!{RESET}")
        print("Commands: 'schema' shows the database tables; 'quit' or 'exit' quits.")
        print_schema()
    except sqlite3.Error as exc:
        print(f"{RED}Could not read the database schema: {exc}{RESET}", file=sys.stderr)
        return

    while True:
        try:
            question = input("\nEnter your question: ").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{GREEN}Goodbye!{RESET}")
            break

        command = question.lower()
        if command in {"quit", "exit"}:
            print(f"{GREEN}Goodbye!{RESET}")
            break
        if command == "schema":
            try:
                print_schema()
            except sqlite3.Error as exc:
                print(f"{RED}Could not read the database schema: {exc}{RESET}")
            continue
        if not question:
            print(f"{RED}Please enter a question or a command.{RESET}")
            continue

        try:
            sql = generate_sql(get_schema(), question)
            rows = run_query(sql)
            print(f"\n{CYAN}SQL:{RESET}\n{sql}")
            print(f"\n{GREEN}Results ({len(rows)} row(s)):{RESET}")
            print_table(rows)
            if len(rows) == MAX_ROWS:
                print(f"(Showing at most {MAX_ROWS} rows.)")
        except APIStatusError as exc:
            if exc.status_code == 429:
                message = (
                    "Gemini returned HTTP 429. Check your Gemini API quota "
                    "and usage limits in Google AI Studio."
                )
            else:
                message = f"Gemini API request failed with status {exc.status_code}."
            print(f"{RED}{message}{RESET}", file=sys.stderr)
        except (OpenAIError, sqlite3.Error, ValueError, RuntimeError, OSError) as exc:
            print(f"{RED}Could not process that question: {exc}{RESET}", file=sys.stderr)


if __name__ == "__main__":
    main()
