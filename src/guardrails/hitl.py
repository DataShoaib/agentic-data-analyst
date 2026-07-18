"""Human-in-the-Loop guardrail — pauses graph for unsafe SQL approval."""
from langgraph.types import interrupt
from langchain_core.messages import AIMessage
from src.graph.state import AgentState
from src.tools.sql_tools import run_sql_query


def hitl_guardrail_node(state: AgentState) -> dict:
    if not state.get("requires_approval"):
        return {}

    decision = interrupt({
        "question": "This query will modify the database. Approve execution?",
        "sql": state["generated_sql"],
    })
    trace = state.get("agent_trace") or []
    existing = state.get("query_results") or []

    if decision == "approve":
        exec_result = run_sql_query(state["generated_sql"], read_only=False)
        if exec_result["success"]:
            return {
                "query_results": existing + [{"sql": state["generated_sql"], "rows": exec_result["rows"], "error": None}],
                "requires_approval": False,
                "agent_trace": trace + ["🛡️ HITL (Approved)"],
            }
        msg = f"⚠️ Query approved but failed to execute: {exec_result['error']}"
        return {
            "query_error": exec_result["error"],
            "requires_approval": False,
            "final_report": msg,
            "messages": [AIMessage(content=msg, additional_kwargs={"chart_paths": [], "agent_trace": trace + ["🛡️ HITL (Failed)"]})],
            "report_done": True,
            "agent_trace": trace + ["🛡️ HITL (Failed)"],
        }

    msg = "❌ Query denied. The database was not modified."
    return {
        "query_error": "User denied execution.",
        "requires_approval": False,
        "final_report": msg,
        "messages": [AIMessage(content=msg, additional_kwargs={"chart_paths": [], "agent_trace": trace + ["🛡️ HITL (Denied)"]})],
        "report_done": True,
        "agent_trace": trace + ["🛡️ HITL (Denied)"],
    }