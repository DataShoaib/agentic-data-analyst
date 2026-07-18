"""Wires every node and edge into the final compiled LangGraph."""
from langgraph.graph import StateGraph, END

from src.graph.state import AgentState
from src.agents.supervisor import supervisor_node
from src.agents.sql_agent import sql_agent_node
from src.agents.analysis_agent import analysis_agent_node
from src.agents.viz_agent import viz_agent_node
from src.agents.report_agent import report_agent_node
from src.guardrails.hitl import hitl_guardrail_node
from src.memory.checkpointer import get_checkpointer


def route_from_supervisor(state: AgentState) -> str:
    return state.get("next_agent", "end")


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("sql_agent", sql_agent_node)
    graph.add_node("hitl_guardrail", hitl_guardrail_node)
    graph.add_node("analysis_agent", analysis_agent_node)
    graph.add_node("viz_agent", viz_agent_node)
    graph.add_node("report_agent", report_agent_node)

    graph.set_entry_point("supervisor")

    graph.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "sql_agent": "sql_agent",
            "analysis_agent": "analysis_agent",
            "viz_agent": "viz_agent",
            "report_agent": "report_agent",
            "end": END,
        },
    )

    graph.add_edge("sql_agent", "hitl_guardrail")
    graph.add_edge("hitl_guardrail", "supervisor")
    graph.add_edge("analysis_agent", "supervisor")
    graph.add_edge("viz_agent", "supervisor")
    graph.add_edge("report_agent", "supervisor")

    checkpointer = get_checkpointer()
    return graph.compile(checkpointer=checkpointer)


compiled_graph = build_graph()


def get_thread_history(thread_id: str) -> list[dict]:
    """Reads back the saved conversation for a thread from the checkpointer,
    including chart paths and agent trace stored in each AI message's
    additional_kwargs — so a refresh restores charts too, not just text."""
    config = {"configurable": {"thread_id": thread_id}}
    state = compiled_graph.get_state(config)
    if not state or not state.values:
        return []

    messages = state.values.get("messages", [])
    history = []
    for m in messages:
        role = "user" if m.type == "human" else "assistant"
        entry = {"role": role, "content": m.content}

        kwargs = getattr(m, "additional_kwargs", {}) or {}
        if kwargs.get("chart_paths"):
            entry["charts"] = kwargs["chart_paths"]
        if kwargs.get("agent_trace"):
            entry["trace"] = kwargs["agent_trace"]

        history.append(entry)
    return history