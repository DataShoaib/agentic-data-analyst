# 🤖 Agentic Data Analyst Co-Pilot

A **multi-agent AI system** that lets you talk to a database in plain English. It plans, writes one or more SQL queries, executes them safely (with human approval for risky operations), analyzes results, auto-generates the right chart type for each, and writes a business-ready insight report — all orchestrated by a **LangGraph Supervisor architecture**.

> Ask: *"Give me important insights for marketing"*
> Get: 3-5 auto-planned SQL queries, executed data, business-focused analysis, and multiple charts (bar/line/pie, auto-selected) — all in one response.

---

## Why this project (interview pitch)

Most fresher projects are single-chain RAG bots. This one demonstrates agentic orchestration — the actual skill GenAI/LLM Engineer JDs ask for in 2026:

| Skill JD asks for | Where it's shown |
|---|---|
| Multi-agent systems | Supervisor pattern routing to 4 specialist agents |
| Stateful graphs | LangGraph StateGraph with typed shared state and explicit completion flags |
| Human-in-the-loop safety | interrupt() before destructive SQL (DELETE/UPDATE/DROP) |
| Persistent memory | SqliteSaver checkpointer — conversation + charts survive restarts |
| Multi-step reasoning | SQL agent proactively plans multiple queries for open-ended asks |
| Guardrails | Keyword denylist + read-only DB connection, defense-in-depth |
| Production packaging | FastAPI backend + Streamlit UI + Docker Compose |
| Observability | Per-response agent trace shown in the UI |

---

## Key Features

- Natural language to SQL — handles single questions, multi-part questions ("X and also Y"), and open-ended asks ("give me marketing insights") where the agent decides its own query plan
- Smart chart selection — auto-picks bar / line / pie based on data shape (date columns go to line, 7 or fewer categories go to pie, more go to bar); one chart per query result
- HITL safety guardrail — risky SQL pauses for explicit human approval before touching the database
- Persistent, resumable conversations — thread ID lives in the URL; refreshing the browser restores full chat history, including past charts, from SQLite
- Multi-conversation sidebar — switch between chats, or pick up any past conversation from previous sessions
- Agent trace transparency — every answer shows exactly which agents ran

---

## Architecture

START connects to Supervisor. Supervisor routes conditionally, based on explicit completion flags in state, to one of four specialist agents: SQL Agent, Analysis Agent, Viz Agent, or Report Agent. The SQL Agent plans and executes one or more queries, then passes through an HITL Guardrail node before returning to the Supervisor — the guardrail calls interrupt() only if any generated query is unsafe (DELETE/UPDATE/DROP/etc.), pausing the graph until a human approves or denies. The Analysis, Viz, and Report agents each return control directly to the Supervisor after finishing. The Supervisor checks four flags in order — sql_done, analysis_done, viz_done, report_done — and once all four are true, the graph reaches END.

This explicit-flag design (rather than "is this field empty") is what prevents infinite loops when a query legitimately returns no data — an empty or None result is still marked "done," so the Supervisor doesn't retry endlessly.

---

## File Structure

```
agentic-data-analyst/
  src/
    config.py                 - env, model config, timeouts/retries
    graph/
      state.py                - shared AgentState (TypedDict)
      builder.py               - StateGraph wiring + thread history reader
      router.py
    agents/
      supervisor.py            - routes via explicit completion flags
      sql_agent.py             - NL to one or more SQL queries
      analysis_agent.py        - business/marketing-focused insights
      viz_agent.py             - auto chart-type selection, one per query
      report_agent.py          - final insight message + chart metadata
    tools/
      sql_tools.py             - safe SQL execution, read-only by default
      stats_tools.py           - pandas describe/correlation
      viz_tools.py             - matplotlib chart generation
    memory/checkpointer.py     - SqliteSaver persistent memory
    guardrails/hitl.py         - human-in-the-loop interrupt logic
    utils/
  api/main.py                  - FastAPI: /chat /resume /history /threads
  app/streamlit_app.py         - multi-conversation chat UI
  data/sample.db               - demo sales DB (auto-generated)
  tests/                       - pytest unit + routing tests
  docs/architecture.md         - deep-dive for portfolio/interview prep
  Dockerfile / docker-compose.yml
  requirements.txt
```

---

## Setup

Clone the repo, create a virtual environment, and install dependencies:

```
git clone <your-repo-url>
cd agentic-data-analyst
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Copy the environment template and add your Groq API key:

```
copy .env.example .env
```

Seed the demo database, then start the backend and frontend in two separate terminals:

```
python -m src.utils.seed_db
python -m uvicorn api.main:app --reload
```

```
streamlit run app/streamlit_app.py
```

### Or with Docker Compose

```
docker compose up --build
```

### Run tests

```
pytest tests/ -v
```

---

## Interview talking points (STAR-ready)

**Situation:** Business users can't write SQL but need ad-hoc insights, including open-ended asks like "what's important for marketing."

**Task:** Build an agent that safely plans, executes, analyzes, and visualizes, without a human writing a query, and safely enough to trust near a real database.

**Action:** Designed a LangGraph Supervisor architecture with 4 specialist agents; the SQL agent plans 1-N queries depending on whether the ask is single, multi-part, or open-ended. Added a HITL guardrail using interrupt() so destructive SQL pauses for human approval. Fixed an early infinite-recursion bug by switching routing logic from "is this field empty" to explicit *_done completion flags. Persisted full conversation and chart state via SqliteSaver, with a /history endpoint so a browser refresh restores everything. Wrapped it in FastAPI, Streamlit, and Docker Compose.

**Result:** A multi-agent pipeline that handles ambiguous, multi-part, and open-ended business questions, with zero unsafe SQL executions in testing and a fully resumable chat experience.

Good follow-up answers to rehearse:

- Why supervisor pattern over a single ReAct agent? Separation of concerns, focused prompts per specialist, independently testable, swappable models per agent.
- How do you prevent SQL injection? The LLM only outputs SQL, never executes user input directly; a keyword denylist blocks DDL/DML; the DB connection is read-only by default; anything else requires human approval.
- How does HITL actually work in LangGraph? interrupt() pauses graph execution and returns control to the caller; state is safely held in the checkpointer; execution resumes via Command(resume=...).
- What was the hardest bug? An infinite recursion loop from routing on "is this value None" instead of an explicit completion flag — None can be a legitimate result (e.g. no chart possible), not just "not done yet."
- What would you improve for production? Auth, rate limiting, secrets management, monitoring/alerting, and load testing — this is a portfolio-grade demo that follows production patterns, not a production system itself.