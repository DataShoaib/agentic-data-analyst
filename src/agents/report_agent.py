"""Report Agent — final answer includes insight text. Chart paths and
agent trace are attached to the message's additional_kwargs so they
survive a checkpoint reload (e.g. after a browser refresh)."""
from langchain_core.messages import AIMessage
from src.graph.state import AgentState


def report_agent_node(state: AgentState) -> dict:
    trace = state.get("agent_trace") or []
    insights = state.get("insights", "")
    chart_paths = state.get("chart_paths") or []

    ai_message = AIMessage(
        content=insights,
        additional_kwargs={"chart_paths": chart_paths, "agent_trace": trace + ["📝 Report agent"]},
    )

    return {
        "final_report": insights,
        "messages": [ai_message],
        "report_done": True,
        "agent_trace": trace + ["📝 Report agent"],
    }