"""Build the LangGraph state machine — not compiled at import time."""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from .nodes import (
    agent_node,
    final_policy_override_node,
    should_continue,
    tool_exec_node,
    validator_node,
)
from .state import AgentState


def build_graph() -> StateGraph:
    """Create, wire, compile, and return the LangGraph application."""
    graph = StateGraph(AgentState)

    # Adding nodes
    graph.add_node("agent", agent_node)                                         # ReAct agent
    graph.add_node("tool", tool_exec_node)                                      # Tool execution
    graph.add_node("validate", validator_node)                                  # Cross-checks claims
    graph.add_node("policy", final_policy_override_node)                        # Safety override

    # Start with
    graph.set_entry_point("agent")

    # ReAct loop routing: if tools requested -> tool node; if answer ready -> final; else keep calling agent
    graph.add_conditional_edges(
        "agent",
        should_continue,
        {
            "final": "validate",
            "tool": "tool",
            "agent": "agent",
        }
    )

    # Define edges
    graph.add_edge("tool", "agent")                                             # After tool, return to agent
    graph.add_edge("validate", "policy")                                        # After validation, go to final
    graph.add_edge("policy", END)                                               # After final, go to end

    # Compile graph
    return graph.compile()
