"""AgentState TypedDict and state initialization — verbatim from the notebook."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from .prompts import REACT_SYSTEM_PROMPT


class AgentState(TypedDict):
    patient_id: str
    user_query: str
    # Patient profile
    preferred_language: str
    health_literacy_level: str
    # Safety routing
    decision: str
    policy_rule_id: Optional[str]
    policy_template: Optional[str]
    # ReAct
    messages: List[BaseMessage]
    step: int
    max_steps: int
    citations: List[Dict[str, Any]]
    draft_answer: Optional[str]
    final_answer: Optional[str]
    tools_called: List[str]
    tool_outputs: Dict[str, Any]
    errors: List[str]
    # Validator
    validation_result: Optional[Dict]
    intent_class: str
    escalation_level: int
    guardrails_triggered: List[str]
    verdict: str
    scores: Dict[str, int]
    flags: List[Dict[str, Any]]
    hard_block: bool


def init_state(patient_id: Optional[str], user_query: str, max_steps: int = 5) -> AgentState:
    """Initialize the starting AgentState for a single ReAct run."""
    patient_id_for_state = patient_id if patient_id else ""
    return {
        "patient_id": patient_id_for_state,
        "user_query": user_query,
        "decision": "answer",
        "policy_rule_id": None,
        "policy_template": None,
        "messages": [
            SystemMessage(content=REACT_SYSTEM_PROMPT),
            HumanMessage(content=f"patient_id={patient_id_for_state}\nUser question: {user_query}")
        ],
        "step": 0,
        "max_steps": max_steps,
        "citations": [],
        "draft_answer": None,
        "final_answer": None,
        "validation_result": None,
        "errors": [],
        "intent_class": "",
        "preferred_language": "en",
        "health_literacy_level": "intermediate",
        "tools_called": [],
        "tool_outputs": {},
        "escalation_level": 1,
        "guardrails_triggered": [],
        "verdict": "",
        "scores": {},
        "flags": [],
        "hard_block": False,
    }
