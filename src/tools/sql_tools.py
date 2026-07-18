"""Safe SQL execution against the demo SQLite database.

Design choice for the interview: the LLM NEVER gets raw DB write access.
We open the connection read-only by default; write ops must pass through
the HITL guardrail first (see src/guardrails/hitl.py).
"""
import sqlite3
import re
from src.config import DATABASE_PATH, UNSAFE_SQL_KEYWORDS


def is_unsafe_sql(sql: str) -> bool:
    """Flags SQL containing DDL/DML keywords that mutate data or schema."""
    sql_upper = sql.upper()
    return any(re.search(rf"\b{kw}\b", sql_upper) for kw in UNSAFE_SQL_KEYWORDS)


def run_sql_query(sql: str, read_only: bool = True) -> dict:
    """Executes SQL and returns rows as list[dict], or an error message.

    Args:
        sql: the SQL string to execute.
        read_only: if True, opens the DB in URI read-only mode — an extra
            defense layer even if a bad query slips past the keyword check.
    """
    try:
        if read_only and not is_unsafe_sql(sql):
            uri = f"file:{DATABASE_PATH}?mode=ro"
            conn = sqlite3.connect(uri, uri=True)
        else:
            conn = sqlite3.connect(DATABASE_PATH)

        conn.row_factory = sqlite3.Row
        cursor = conn.execute(sql)
        rows = [dict(row) for row in cursor.fetchall()]
        conn.commit()
        conn.close()
        return {"success": True, "rows": rows, "row_count": len(rows)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_schema_summary() -> str:
    """Returns table + column names so the SQL agent can ground its query."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]

    schema_lines = []
    for table in tables:
        cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
        col_names = ", ".join(f"{c[1]} ({c[2]})" for c in cols)
        schema_lines.append(f"Table `{table}`: {col_names}")
    conn.close()
    return "\n".join(schema_lines)
