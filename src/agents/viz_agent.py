"""Viz Agent — builds ONE chart per query result that has numeric data.

Chart type is chosen based on the shape of the data:
- Has a date/month-like column          -> line chart (trend over time)
- 7 or fewer categories                 -> pie chart (share of whole)
- More than 7 categories                -> bar chart (ranking/comparison)
"""
import logging
from src.tools.viz_tools import generate_chart
from src.graph.state import AgentState

log = logging.getLogger("agentic-data-analyst")

DATE_HINTS = ("date", "month", "year", "day", "time", "quarter")


def _has_numeric_value(rows: list[dict]) -> bool:
    if not rows:
        return False
    return any(isinstance(v, (int, float)) for v in rows[0].values())


def _pick_chart_type(rows: list[dict]) -> str:
    columns = [c.lower() for c in rows[0].keys()]
    if any(any(hint in col for hint in DATE_HINTS) for col in columns):
        return "line"
    if len(rows) <= 7:
        return "pie"
    return "bar"


def viz_agent_node(state: AgentState) -> dict:
    results = state.get("query_results") or []
    trace = state.get("agent_trace") or []
    chart_paths = []

    log.info(f"[Viz Agent] Got {len(results)} query result set(s)")

    for i, r in enumerate(results):
        rows = r.get("rows") or []
        if not _has_numeric_value(rows):
            log.info(f"[Viz Agent] Result {i}: skipped (no numeric column)")
            continue

        chart_type = _pick_chart_type(rows)
        path = generate_chart(rows, chart_type=chart_type)
        if path:
            log.info(f"[Viz Agent] Result {i}: {chart_type} chart -> {path}")
            chart_paths.append(path)

    return {
        "chart_paths": chart_paths,
        "viz_done": True,
        "agent_trace": trace + ["📈 Viz agent"],
    }