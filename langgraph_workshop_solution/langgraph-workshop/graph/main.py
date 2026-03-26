from langgraph.graph import StateGraph, START, END
from graph.state import AgentState
from graph.nodes import (
    parse_input_node,
    set_budget_low,
    set_budget_high,
    recommend_node,
    format_response_node,
)
from graph.router import budget_router


def build_graph():
    workflow = StateGraph(AgentState)

    # 註冊節點
    workflow.add_node("parse_input", parse_input_node)
    workflow.add_node("set_budget_low", set_budget_low)
    workflow.add_node("set_budget_high", set_budget_high)
    workflow.add_node("recommend", recommend_node)
    workflow.add_node("format_response", format_response_node)

    # 起點 → parse_input
    workflow.add_edge(START, "parse_input")

    # parse_input → 條件路由 → set_budget_low 或 set_budget_high
    workflow.add_conditional_edges(
        "parse_input",
        budget_router,
        {
            "budget": "set_budget_low",
            "premium": "set_budget_high",
        }
    )

    # set_budget_* → recommend → format_response → 終點
    workflow.add_edge("set_budget_low", "recommend")
    workflow.add_edge("set_budget_high", "recommend")
    workflow.add_edge("recommend", "format_response")
    workflow.add_edge("format_response", END)

    return workflow.compile()
