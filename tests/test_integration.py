"""End-to-end integration tests — require OPENAI_API_KEY."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="No OPENAI_API_KEY — skipping integration tests",
)


class TestIntegration:
    def test_full_run_p001(self):
        from ehr_assistant.agent.graph import build_graph
        from ehr_assistant.agent.state import init_state

        state = init_state("P001", "What does my Hemoglobin A1c result mean?", max_steps=5)
        app = build_graph()
        out = app.invoke(state)

        assert out["final_answer"]
        assert len(out["final_answer"]) > 10
        assert "tools_called" in out
        assert len(out["tools_called"]) > 0

    def test_empty_query_returns_greeting(self):
        from ehr_assistant.agent.graph import build_graph
        from ehr_assistant.agent.state import init_state

        state = init_state("P001", "", max_steps=5)
        app = build_graph()
        out = app.invoke(state)

        assert "How can I help you?" in out["final_answer"]
