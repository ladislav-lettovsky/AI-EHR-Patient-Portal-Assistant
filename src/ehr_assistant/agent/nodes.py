"""Graph node functions — verbatim logic from the notebook."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI

from ..config import (
    MODEL_GENERATOR,
    MODEL_VALIDATOR,
    OPENAI_BASE_URL,
    TEMPERATURE,
)
from ..tools import (
    BLOCKED_TOOLNAMES,
    INFORMATION_TOOLNAMES,
    PATIENT_SCOPED_TOOLNAMES,
    RETRIEVAL_LIMITED_TOOLNAMES,
    TOOLS,
)
from .prompts import VALIDATION_PROMPT
from .state import AgentState

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy-init LLMs (not at import time — enables testing with mocks)
# ---------------------------------------------------------------------------
_llm_gen_tools: ChatOpenAI | None = None
_llm_val: ChatOpenAI | None = None


def _get_llm_gen_tools() -> ChatOpenAI:
    global _llm_gen_tools
    if _llm_gen_tools is None:
        llm_gen = ChatOpenAI(
            model=MODEL_GENERATOR,
            temperature=TEMPERATURE,
            base_url=OPENAI_BASE_URL,
        )
        _llm_gen_tools = llm_gen.bind_tools(TOOLS)
    return _llm_gen_tools


def _get_llm_val() -> ChatOpenAI:
    global _llm_val
    if _llm_val is None:
        _llm_val = ChatOpenAI(
            model=MODEL_VALIDATOR,
            temperature=TEMPERATURE,
            base_url=OPENAI_BASE_URL,
        )
    return _llm_val


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _cap_limit(args: Dict[str, Any], max_limit: int = 10) -> Dict[str, Any]:
    """Cap a tool call's 'limit' argument to control data volume and prompt size."""
    out = dict(args)                                                            # Copy args so we don't mutate the original dict
    if "limit" in out and out["limit"] is not None:
        try:
            out["limit"] = min(int(out["limit"]), max_limit)                    # Cap numeric limit
        except Exception:
            out["limit"] = max_limit                                            # Fallback if limit isn't parseable

    return out


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------
def agent_node(state: AgentState) -> Dict[str, Any]:
    # Emergency short-circuit: finalize will enforce template; still produce a draft to stop loop
    if state.get("decision") == "escalate_emergency" and state.get("policy_template"):
        return {
            "draft_answer": state["policy_template"],
            "messages": state["messages"],                                      # Still write something explicit
            "step": state["step"],
        }

    # Max-step guard
    if state["step"] >= state["max_steps"]:
        forced = (
            "I may not have enough information yet to answer confidently. "
            "I can explain what your records show or share general information. "
            "For medical advice (especially medication changes) or urgent concerns, please contact your clinician."
        )
        return {
            "draft_answer": forced,
            "messages": state["messages"],
            "step": state["step"],
        }

    # Invoke LLM with tools
    ai_msg = _get_llm_gen_tools().invoke(state["messages"])

    # Explicitly build updated messages + step (no in-place mutation reliance)
    new_messages = list(state["messages"]) + [ai_msg]
    new_step = state["step"] + 1

    # If no tool calls, treat as draft answer and stop looping
    if not getattr(ai_msg, "tool_calls", None):
        content = ai_msg.content or (
            "I may not have enough information yet to answer confidently. "
            "I can explain what your records show or share general information. "
            "For medical advice (especially medication changes) or urgent concerns, please contact your clinician."
        )
        return {
            "messages": new_messages,
            "step": new_step,
            "draft_answer": content,
        }

    # Tool calls exist: continue loop, but MUST still return an update
    return {
        "messages": new_messages,
        "step": new_step,
    }


def tool_exec_node(state: AgentState) -> Dict[str, Any]:
    """
    Execute tool calls produced by the tool-enabled LLM and append results back into the message trace.

    This node:
    - reads tool calls from the last AI message,
    - enforces patient scoping by overwriting patient_id for sensitive tools,
    - caps limit parameters for controlled retrieval,
    - executes each tool from the approved tool map,
    - appends each tool output as a ToolMessage observation,
    - optionally extracts citations from lab/med education tool outputs.

    Inputs:
        state (AgentState): Current state containing at least:
            - patient_id: used to enforce patient scoping
            - messages: last message may contain tool_calls
            - citations/errors: existing lists to extend

    Outputs:
        Dict[str, Any]: State updates containing:
            - messages: updated message list including ToolMessages (tool observations)
            - citations: updated list with extracted citation metadata (if any)
            - errors: updated list with any tool execution / blocking errors
    """
    last = state["messages"][-1]                                                # Last AI message should contain tool_calls
    tool_calls = getattr(last, "tool_calls", []) or []                          # Tool call specs from LLM
    tool_map = {t.name: t for t in TOOLS}                                       # Whitelist: tool name -> tool callable

    new_messages = list(state["messages"])                                      # Copy messages (avoid in-place mutation)
    new_citations = list(state.get("citations", []))                            # Copy citations
    new_errors = list(state.get("errors", []))                                  # Copy errors

    tools_called = list(state["tools_called"])
    tool_outputs = dict(state["tool_outputs"])

    # Preserve and potentially update language/literacy from patient profile
    updated_preferred_language = state["preferred_language"]
    updated_health_literacy_level = state["health_literacy_level"]

    # Policy fields — updated if policy_route is called
    updated_decision = state.get("decision", "answer")
    updated_policy_rule_id = state.get("policy_rule_id")
    updated_policy_template = state.get("policy_template")

    for tc in tool_calls:
        name = tc.get("name")
        args = tc.get("args", {}) or {}
        tool_id = tc.get("id")                                                  # Required so ToolMessage can be associated to the correct call

        # Block any tool not in our allowlist (security)
        if (name in BLOCKED_TOOLNAMES) or (name not in tool_map):
            new_errors.append(f"Blocked unknown tool call: {name}")
            new_messages.append(
                ToolMessage(content=f"Blocked unknown tool: {name}", name=name or "unknown", tool_call_id=tool_id)
            )
            if name:  # only add non-None names to avoid polluting the set
                BLOCKED_TOOLNAMES.add(name)
            continue

        # Critical: prevent cross-patient data access by enforcing patient_id
        if name in PATIENT_SCOPED_TOOLNAMES:
            args["patient_id"] = state["patient_id"]

        # Cap retrieval volume (limits prompt size and reduces accidental overexposure)
        if name in RETRIEVAL_LIMITED_TOOLNAMES:
            args = _cap_limit(args, max_limit=10)

        try:
            tools_called.append(name)
            result = tool_map[name].invoke(args)
            if not isinstance(result, str):
                result = json.dumps(result, ensure_ascii=False, default=str)

            # Cache raw outputs keyed by tool name (last call wins)
            tool_outputs[name] = result

            if name == "get_patient_profile":
                profile_data = json.loads(result)
                # Only update if profile_data is not an error and contains the keys
                if "error" not in profile_data:
                    if "preferred_language" in profile_data:
                        updated_preferred_language = profile_data["preferred_language"]
                    if "health_literacy_level" in profile_data:
                        updated_health_literacy_level = profile_data["health_literacy_level"]

            if name == "policy_route":
                try:
                    policy_data = json.loads(result)
                    updated_decision = policy_data.get("decision", updated_decision)
                    updated_policy_rule_id = policy_data.get("policy_rule_id", updated_policy_rule_id)
                    updated_policy_template = policy_data.get("policy_template", updated_policy_template)
                except Exception:
                    pass

            # Capture citations from education tools
            if name in INFORMATION_TOOLNAMES:
                try:
                    data = json.loads(result)
                    if isinstance(data, dict) and "error" not in data:
                        cit = {
                            "source_id": data.get("source_id"),
                            "citation_url": data.get("citation_url"),
                            "used_for": "lab education" if name == "lookup_lab_education" else "medication education",
                        }
                        if cit["source_id"] or cit["citation_url"]:
                            new_citations.append(cit)
                except Exception:
                    pass

            new_messages.append(
                ToolMessage(content=result, name=name, tool_call_id=tool_id)
            )

        except Exception as e:
            err = f"{name} failed: {e}"
            new_errors.append(err)
            new_messages.append(
                ToolMessage(content=err, name=name, tool_call_id=tool_id)
            )

    return {
        "messages": new_messages,
        "citations": new_citations,
        "errors": new_errors,
        "tools_called": tools_called,
        "tool_outputs": tool_outputs,
        "preferred_language": updated_preferred_language,                       # Propagate updated value
        "health_literacy_level": updated_health_literacy_level,                 # Propagate updated value
        "decision": updated_decision,                                           # Propagate policy decision
        "policy_rule_id": updated_policy_rule_id,                              # Propagate matched rule
        "policy_template": updated_policy_template,                            # Propagate response template
    }


def should_continue(state: AgentState) -> str:
    """Determine the next step in the ReAct loop based on the latest state."""
    if state.get("draft_answer"):
        return "final"                                                          # Agent has produced an answer; exit loop

    last = state["messages"][-1]                                                # Inspect the most recent AI message
    if getattr(last, "tool_calls", None):
        return "tool"                                                           # Tools requested; execute them

    return "agent"                                                              # No answer yet and no tools requested; ask agent again


_HARD_BLOCK_MESSAGE = (
    "I'm sorry, but I cannot provide a response to this query as it may involve "
    "medical advice that requires a qualified clinician. Please contact your care team "
    "or call emergency services if this is urgent."
)


def final_policy_override_node(state: AgentState) -> Dict[str, Any]:
    """Final, deterministic safety override to select the response returned to the user."""
    decision = state.get("decision", "answer")
    user_query = state.get("user_query")
    policy_template = state.get("policy_template")

    # If policy requires refusal/escalation, override any LLM output
    if decision in ("escalate_emergency", "refuse", "escalate_clinician") and policy_template:
        return {"final_answer": policy_template}

    # If validator hard-blocked or returned FAIL, never ship the draft
    if state.get("hard_block") or state.get("verdict") == "FAIL":
        return {"final_answer": _HARD_BLOCK_MESSAGE}

    # If it's an empty query, engage in a dialog
    if decision == "answer" and len(user_query) == 0:
        return {"final_answer": "How can I help you? I'm EHR assistant and can answer a health-related query"}

    # Otherwise return the model's draft answer (or a fallback)
    return {"final_answer": state.get("draft_answer") or "I'm not sure how to answer that yet."}


def validator_node(state: AgentState) -> Dict[str, Any]:
    """Cross-checks all claims against tool results."""

    payload = {
        "patient_id": state["patient_id"],
        "preferred_language": state["preferred_language"],
        "health_literacy_level": state["health_literacy_level"],
        "intent_class": state["intent_class"] or "A",
        "user_query": state["user_query"],
        "tools_called": state["tools_called"],
        "tool_outputs": state["tool_outputs"],
        "draft_answer": state["draft_answer"] or "",
    }
    system = SystemMessage(content=VALIDATION_PROMPT)
    user = HumanMessage(content=json.dumps(payload, ensure_ascii=False))
    raw = _get_llm_val().invoke([system, user])

    try:
        # Attempt to extract JSON from markdown code block
        json_match = re.search(r"```json\s*(.*?)\s*```", raw.content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # If not in a code block, assume it's plain JSON
            json_str = raw.content.strip()

        result = json.loads(json_str)
    except Exception as e:
        logger.warning("Validator JSON parse failed: %s", e)
        logger.warning("Raw content from validator LLM: %s", raw.content)
        return {
            "verdict": "WARN",
            "scores": {},
            "flags": [{"dimension": "D1", "score": 4, "reason": "Validator JSON parse failed"}],
            "hard_block": False,
            "validation_result": {"error": f"Validator JSON parse failed: {e}"},
        }

    return {
        "verdict": result.get("verdict", ""),
        "scores": result.get("scores", {}),
        "flags": result.get("flags", []),

        "hard_block": bool(result.get("hard_block", False)),
    }
