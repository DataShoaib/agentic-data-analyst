"""Supervisor Agent — the router. Routes based on explicit *_done flags,
never on whether a result field is None (None can be a valid outcome)."""
from src.graph.state import AgentState


def supervisor_node(state: AgentState) -> dict:
    if state.get("query_error"):
        return {"next_agent": "end"}

    if not state.get("sql_done"):
        return {"next_agent": "sql_agent"}

    if state.get("requires_approval"):
        # Waiting on human approval — graph should already be interrupted
        # at the HITL node before reaching here, this is a safety fallback.
        return {"next_agent": "end"}

    if not state.get("analysis_done"):
        return {"next_agent": "analysis_agent"}

    if not state.get("viz_done"):
        return {"next_agent": "viz_agent"}

    if not state.get("report_done"):
        return {"next_agent": "report_agent"}

    return {"next_agent": "end"}