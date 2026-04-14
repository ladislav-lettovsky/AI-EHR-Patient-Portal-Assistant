"""Unit tests for agent nodes and helpers — no API key needed."""

from __future__ import annotations

import pytest

from ehr_assistant.agent.nodes import _cap_limit, should_continue, final_policy_override_node
from ehr_assistant.agent.state import AgentState, init_state


class TestInitState:

    def test_returns_correct_keys(self):
        state = init_state("P001", "What are my labs?", max_steps=5)
        assert state["patient_id"] == "P001"
        assert state["user_query"] == "What are my labs?"
        assert state["max_steps"] == 5
        assert state["step"] == 0
        assert state["decision"] == "answer"
        assert state["draft_answer"] is None
        assert state["final_answer"] is None
        assert isinstance(state["messages"], list)
        assert len(state["messages"]) == 2

    def test_none_patient_id_becomes_empty(self):
        state = init_state(None, "hello")
        assert state["patient_id"] == ""

    def test_empty_string_patient_id(self):
        state = init_state("", "hello")
        assert state["patient_id"] == ""


class TestCapLimit:

    def test_caps_high_limit(self):
        result = _cap_limit({"limit": 100}, max_limit=10)
        assert result["limit"] == 10

    def test_keeps_low_limit(self):
        result = _cap_limit({"limit": 3}, max_limit=10)
        assert result["limit"] == 3

    def test_no_limit_key(self):
        result = _cap_limit({"patient_id": "P001"}, max_limit=10)
        assert "limit" not in result

    def test_none_limit(self):
        result = _cap_limit({"limit": None}, max_limit=10)
        assert result["limit"] is None

    def test_unparseable_limit(self):
        result = _cap_limit({"limit": "abc"}, max_limit=10)
        assert result["limit"] == 10

    def test_does_not_mutate_original(self):
        original = {"limit": 50}
        result = _cap_limit(original, max_limit=10)
        assert original["limit"] == 50
        assert result["limit"] == 10


class TestShouldContinue:

    def test_returns_final_when_draft_answer(self):
        state = init_state("P001", "test")
        state["draft_answer"] = "Here is my answer"
        assert should_continue(state) == "final"

    def test_returns_tool_when_tool_calls(self):
        state = init_state("P001", "test")
        state["draft_answer"] = None

        class _MockMsg:
            tool_calls = [{"name": "get_labs", "args": {}, "id": "1"}]

        state["messages"].append(_MockMsg())
        assert should_continue(state) == "tool"

    def test_returns_agent_when_no_tools_no_answer(self):
        state = init_state("P001", "test")
        state["draft_answer"] = None

        class _MockMsg:
            tool_calls = None

        state["messages"].append(_MockMsg())
        assert should_continue(state) == "agent"


class TestFinalPolicyOverrideNode:

    def test_escalate_emergency_overrides(self):
        state = init_state("P001", "chest pain")
        state["decision"] = "escalate_emergency"
        state["policy_template"] = "Call 911 immediately."
        result = final_policy_override_node(state)
        assert result["final_answer"] == "Call 911 immediately."

    def test_refuse_overrides(self):
        state = init_state("P001", "bad query")
        state["decision"] = "refuse"
        state["policy_template"] = "I cannot answer that."
        result = final_policy_override_node(state)
        assert result["final_answer"] == "I cannot answer that."

    def test_answer_with_empty_query(self):
        state = init_state("P001", "")
        state["decision"] = "answer"
        result = final_policy_override_node(state)
        assert "How can I help you?" in result["final_answer"]

    def test_answer_uses_draft(self):
        state = init_state("P001", "What are my labs?")
        state["decision"] = "answer"
        state["draft_answer"] = "Here are your labs."
        result = final_policy_override_node(state)
        assert result["final_answer"] == "Here are your labs."

    def test_answer_fallback(self):
        state = init_state("P001", "What are my labs?")
        state["decision"] = "answer"
        state["draft_answer"] = None
        result = final_policy_override_node(state)
        assert result["final_answer"] == "I'm not sure how to answer that yet."
