"""Policy routing tool — classifies queries against safety policy rules."""

from __future__ import annotations

from typing import List

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from ..config import MODEL_POLICY, OPENAI_BASE_URL, TEMPERATURE
from ..data import get_policy_rules, get_safety_topics
from ..utils import norm_text, to_json

# ---------- Output schema ----------
class ClassificationResult(BaseModel):
    topics: List[str] = Field(description="Sensitive topics detected in the query")


_llm_pol: ChatOpenAI | None = None


def _get_llm_pol() -> ChatOpenAI:
    """Lazy-init the policy classification LLM."""
    global _llm_pol
    if _llm_pol is None:
        _llm_pol = ChatOpenAI(
            model=MODEL_POLICY,
            temperature=TEMPERATURE,
            base_url=OPENAI_BASE_URL,
        ).with_structured_output(ClassificationResult)
    return _llm_pol


@tool("policy_route")
def policy_route(user_text: str) -> str:
    """Classify query against safety policy rules and return decision + template."""
    prompt = ChatPromptTemplate.from_template(
        """
        You are a medical safety classifier.

        Your job is to determine whether the user query relates to any of the following sensitive medical topics.

        Sensitive topics:
        {topics}

        Rules:
        - A query may match multiple topics
        - If none apply return an empty list
        - Only return topics from the provided list
        User query:
        {query}

        """
    )

    safety_topics = get_safety_topics()
    policy_rules = get_policy_rules()

    formatted_prompt = prompt.format(
        topics="\n".join(safety_topics),
        query=norm_text(user_text),
    )

    matched_safety_topics = [norm_text(t) for t in _get_llm_pol().invoke(formatted_prompt).topics]

    # Extract policy rules that match safety topics
    matched_policy_rules = []

    for r in policy_rules:
        safety_topic = norm_text(r.get("pattern_or_topic", ""))
        if safety_topic and safety_topic in matched_safety_topics:
            matched_policy_rules.append(r)

    priority = {
        "escalate_emergency": 3,
        "escalate_clinician": 2,
        "refuse": 1,
        "answer": 0,
    }

    matches_policy_rules_sorted = sorted(
        matched_policy_rules,
        key=lambda r: priority.get(r.get("agent_action", "answer"), 0),
        reverse=True,
    )

    # BUG FIX: handle empty matches — fall back to "answer" action
    if not matches_policy_rules_sorted:
        return to_json(
            {
                "decision": "answer",
                "policy_rule_id": None,
                "policy_template": None,
                "matched_rules": [],
            }
        )

    best = matches_policy_rules_sorted[0]

    return to_json(
        {
            "decision": best["agent_action"],
            "policy_rule_id": best["rule_id"],
            "policy_template": best["standard_response_template"],
            "matched_rules": [
                {
                    "rule_id": m["rule_id"],
                    "action": m["agent_action"],
                    "topic": m["pattern_or_topic"]
                } for m in matches_policy_rules_sorted
            ],
        }
    )
