"""FastAPI backend for the Agentic Data Analyst."""
import sqlite3
from fastapi import FastAPI
from pydantic import BaseModel
from langgraph.types import Command

from src.graph.builder import compiled_graph, get_thread_history
from src.config import CHECKPOINT_DB_PATH
from src.utils.logging_config import setup_logging

log = setup_logging()
app = FastAPI(title="Agentic Data Analyst API")


class ChatRequest(BaseModel):
    message: str
    thread_id: str


class ResumeRequest(BaseModel):
    decision: str
    thread_id: str


def _build_response(result: dict) -> dict:
    if "__interrupt__" in result:
        return {"status": "awaiting_approval", "interrupt": result["__interrupt__"]}

    return {
        "status": "done",
        "report": result.get("final_report"),
        "chart_paths": result.get("chart_paths", []),
        "agent_trace": result.get("agent_trace", []),
    }


@app.post("/chat")
def chat(req: ChatRequest):
    config = {"configurable": {"thread_id": req.thread_id}}

    result = compiled_graph.invoke(
        {
            "messages": [("user", req.message)],
            "generated_sql": None,
            "sql_queries": None,
            "query_results": None,
            "sql_is_safe": None,
            "requires_approval": None,
            "query_error": None,
            "insights": None,
            "chart_paths": None,
            "final_report": None,
            "agent_trace": [],
            "sql_done": False,
            "analysis_done": False,
            "viz_done": False,
            "report_done": False,
        },
        config=config,
    )
    return _build_response(result)


@app.post("/resume")
def resume(req: ResumeRequest):
    config = {"configurable": {"thread_id": req.thread_id}}
    result = compiled_graph.invoke(Command(resume=req.decision), config=config)
    return _build_response(result)


@app.get("/history/{thread_id}")
def history(thread_id: str):
    return {"messages": get_thread_history(thread_id)}


@app.get("/threads")
def list_threads():
    """Lists past conversation threads (valid UUIDs only) with their
    first user message, so the frontend can show a real conversation
    history list — not just what's in the current browser session."""
    conn = sqlite3.connect(CHECKPOINT_DB_PATH)
    rows = conn.execute("SELECT DISTINCT thread_id FROM checkpoints").fetchall()
    conn.close()

    thread_ids = [r[0] for r in rows if len(r[0]) == 36 and r[0].count("-") == 4]

    threads = []
    for tid in thread_ids:
        msgs = get_thread_history(tid)
        if msgs:
            first_user_msg = next((m["content"] for m in msgs if m["role"] == "user"), "Untitled")
            threads.append({"thread_id": tid, "title": first_user_msg[:40]})

    return {"threads": threads}


@app.get("/health")
def health():
    return {"status": "ok"}