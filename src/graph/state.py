"""Shared state that flows through every node in the LangGraph."""
from typing import TypedDict, Annotated, Optional, List, Any
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    next_agent: Optional[str]

    generated_sql: Optional[str]
    sql_queries: Optional[List[str]]
    query_results: Optional[List[dict]]

    sql_is_safe: Optional[bool]
    requires_approval: Optional[bool]
    query_error: Optional[str]

    insights: Optional[str]
    chart_paths: Optional[List[str]]     # 👈 ab list hai, ek nahi
    final_report: Optional[str]

    error: Optional[str]
    metadata: Optional[dict[str, Any]]
    agent_trace: Optional[List[str]]

    sql_done: Optional[bool]
    analysis_done: Optional[bool]
    viz_done: Optional[bool]
    report_done: Optional[bool]