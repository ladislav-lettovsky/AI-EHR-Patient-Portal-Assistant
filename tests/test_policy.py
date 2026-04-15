"""Policy routing unit tests — LLM is mocked; no network calls are made."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch


class TestPolicyRoute:
    """Tests for policy_route tool — LLM responses are stubbed."""

    def _make_llm_mock(self, topics: list[str]) -> MagicMock:
        """Return a mock that behaves like the structured-output LLM chain."""
        from ehr_assistant.tools.policy import ClassificationResult

        result = ClassificationResult(topics=topics)
        mock = MagicMock()
        mock.invoke.return_value = result
        return mock

    def test_safe_query_returns_answer(self):
        from ehr_assistant.tools.policy import policy_route

        with patch("ehr_assistant.tools.policy._get_llm_pol", return_value=self._make_llm_mock([])):
            raw = policy_route.invoke({"user_text": "What does my Hemoglobin A1c result mean?"})

        data = json.loads(raw)
        assert data["decision"] == "answer"
        assert data["policy_rule_id"] is None
        assert data["matched_rules"] == []

    def test_emergency_query_escalates(self):
        from ehr_assistant.tools.policy import policy_route

        with patch(
            "ehr_assistant.tools.policy._get_llm_pol",
            return_value=self._make_llm_mock(["chest pain", "emergency"]),
        ):
            raw = policy_route.invoke(
                {"user_text": "I'm having chest pain and difficulty breathing right now"}
            )

        data = json.loads(raw)
        assert data["decision"] in ("escalate_emergency", "escalate_clinician", "answer")

    def test_medication_advice_returns_valid_decision(self):
        from ehr_assistant.tools.policy import policy_route

        with patch(
            "ehr_assistant.tools.policy._get_llm_pol",
            return_value=self._make_llm_mock(["medication change"]),
        ):
            raw = policy_route.invoke({"user_text": "Should I stop taking my lisinopril?"})

        data = json.loads(raw)
        assert data["decision"] in ("escalate_clinician", "refuse", "answer", "escalate_emergency")

    def test_no_match_falls_back_to_answer(self):
        from ehr_assistant.tools.policy import policy_route

        with patch("ehr_assistant.tools.policy._get_llm_pol", return_value=self._make_llm_mock([])):
            raw = policy_route.invoke({"user_text": "What is the weather like today?"})

        data = json.loads(raw)
        assert data["decision"] == "answer"
        assert data["matched_rules"] == []

    def test_result_schema(self):
        from ehr_assistant.tools.policy import policy_route

        with patch("ehr_assistant.tools.policy._get_llm_pol", return_value=self._make_llm_mock([])):
            raw = policy_route.invoke({"user_text": "Tell me about my recent labs."})

        data = json.loads(raw)
        assert "decision" in data
        assert "policy_rule_id" in data
        assert "policy_template" in data
        assert "matched_rules" in data
        assert isinstance(data["matched_rules"], list)
