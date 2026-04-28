from __future__ import annotations
from langgraph.graph import StateGraph, START, END
from graph.state import AppState
from graph.nodes import vision, tool_recommend, model_recommend, lesson_plan, slides, worksheet

def _route(state: AppState):
    return state.get("next_action", "noop")

def build_graph():
    g = StateGraph(AppState)
    g.add_node("dispatch", lambda state: {})
    g.add_node("vision", vision.node)
    g.add_node("tools", tool_recommend.node)
    g.add_node("models", model_recommend.node)
    g.add_node("lesson", lesson_plan.node)
    g.add_node("slides", slides.node)
    g.add_node("worksheet", worksheet.node)

    g.add_edge(START, "dispatch")
    g.add_conditional_edges(
        "dispatch",
        _route,
        {
            "vision": "vision",
            "tools": "tools",
            "models": "models",
            "lesson": "lesson",
            "slides": "slides",
            "worksheet": "worksheet",
            "noop": END,
        },
    )
    for n in ["vision", "tools", "models", "lesson", "slides", "worksheet"]:
        g.add_edge(n, END)
    return g.compile()
