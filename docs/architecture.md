# Architecture Deep-Dive

## Why a Supervisor pattern, not a single ReAct agent?

A single ReAct agent tries to reason + call tools + format output all in one
prompt. That gets messy once you have 4+ distinct responsibilities (SQL
generation, statistics, charting, report writing). Splitting into specialist
agents behind a Supervisor gives:

1. **Focused prompts** — each agent's system prompt is short and single-purpose,
   which improves reliability with smaller/cheaper models.
2. **Independent testability** — `analysis_agent` can be unit-tested without
   ever touching the DB or an LLM call for SQL.
3. **Swappable models per agent** — e.g., use a cheap model for the Supervisor's
   routing decision and a stronger model only for SQL generation.

## State management

`AgentState` (a `TypedDict`) is the single contract every node reads/writes.
LangGraph merges partial dict returns from each node into this shared state
automatically — nodes never need to know the full state shape, only what
they read and what they return.

## Human-in-the-loop (HITL)

The `hitl_guardrail` node calls LangGraph's `interrupt()`, which:
1. Pauses graph execution at that exact point.
2. Returns control to the caller (FastAPI) with the interrupt payload.
3. Waits — the graph's checkpointer keeps the paused state safe.
4. Resumes via `Command(resume=<decision>)` once the human responds via `/resume`.

This is the difference between a toy agent and one you could actually trust
near a production database.

## Memory / checkpointing

`SqliteSaver` persists every state transition keyed by `thread_id`. Two
practical benefits:
- Multi-turn follow-ups ("now group that by month") retain full context.
- If the process crashes mid-interrupt (waiting for approval), the paused
  state survives a restart — it's on disk, not in a Python variable.

## Guardrails beyond HITL

`sql_tools.is_unsafe_sql()` uses a keyword denylist (`DELETE`, `DROP`,
`UPDATE`, `ALTER`, `TRUNCATE`, `INSERT`) as a first filter, and
`run_sql_query()` opens the DB connection in **read-only URI mode** for any
query that passes that filter — defense in depth, not a single point of failure.

## Extending this project (good "what would you improve" answers)

- Swap the keyword-based safety check for a small classifier or a second
  LLM call that judges query intent.
- Add a `PlannerAgent` that decomposes multi-part questions into a task list
  before delegating to specialists.
- Add LangSmith trace links to each API response for full observability.
- Support Postgres via SQLAlchemy in `sql_tools.py` for a "real" production DB.
