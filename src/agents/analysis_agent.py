"""Analysis Agent — turns one or more query result sets into a cohesive
business/marketing-focused analysis."""
from langchain_core.messages import SystemMessage, HumanMessage
from src.config import get_llm
from src.tools.stats_tools import summarize_dataframe
from src.graph.state import AgentState

ANALYSIS_PROMPT = """You are a senior business and marketing analyst. You
may receive results from multiple queries, each covering a different angle
of the data (e.g. top products, regional performance, monthly trend).

Write a cohesive, well-organized analysis with:
1. Key findings for each angle — concrete numbers, no fluff
2. What this means for the business/marketing strategy
3. 1-2 concrete, actionable recommendations

Use short paragraphs or bullet points. Plain English, no jargon."""


def analysis_agent_node(state: AgentState) -> dict:
    llm = get_llm()
    results = state.get("query_results") or []
    trace = state.get("agent_trace") or []

    blocks = []
    for i, r in enumerate(results, start=1):
        if r.get("error"):
            blocks.append(f"Query {i} failed: {r['error']}")
        elif r.get("rows"):
            blocks.append(f"Query {i} results:\n{summarize_dataframe(r['rows'])}")
        else:
            blocks.append(f"Query {i} returned no data.")

    combined = "\n\n".join(blocks) if blocks else "No data returned."

    response = llm.invoke([
        SystemMessage(content=ANALYSIS_PROMPT),
        HumanMessage(content=combined),
    ])
    return {
        "insights": response.content.strip(),
        "analysis_done": True,
        "agent_trace": trace + ["📊 Analysis agent"],
    }