"""Terminal audit report — cleaned-up print_audit_log from the notebook."""

from __future__ import annotations

from typing import Any, Dict


def print_audit_log(out: Dict[str, Any]) -> None:
    """Print audit log of ReAct loop messages."""
    print("\nTRACE OF MESSAGES FROM THE AGENT:\n")
    for i, m in enumerate(out["messages"]):

        # Message name
        print(f"[{i}] {type(m).__name__}", end="")

        # Skip printing System Message in the Audit Log
        if i == 0:
            print("\n<SYSTEM PROMPT NOT SHOWN>\n")
            continue

        # Avoid re-printing Final Message in the Audit Log
        if i == (len(out["messages"]) - 1):
            print("\n<FINAL MESSAGE (ALREADY PRINTED ABOVE)>\n")
            continue

        # Tools called
        if hasattr(m, "tool_calls") and m.tool_calls:
            for mt in m.tool_calls:
                print(f"\ntool_call: {mt}", end="")
            print("\n")

        # Message content
        content = getattr(m, "content", "")
        if isinstance(content, str) and len(content) > 0:
            print(f"\n{content}\n")

    # Evaluate validation result
    validation = out.get("validation_result", {})
    print("\n" + "*" * 21 + " Validation Result " + "*" * 21)

    if "error" in validation:
        print("Validation Error: {}".format(validation.get("error", "unknown")))
    else:
        # Print validation verdict & scores
        print("Verdict: {} | Scores:".format(out.get("verdict", "")))

        # Get and print scores
        scores = out.get("scores", {})
        flags = out.get("flags", [])

        score_labels = {
            "D1_guardrail_adherence":  "D1  Guardrail Adherence ",
            "D2_factual_groundedness": "D2  Factual Groundedness",
            "D3_query_resolution":     "D3  Query Resolution    ",
            "D4_literacy_adherence":   "D4  Literacy Adherence  ",
            "D5_language_adherence":   "D5  Language Adherence  ",
            "D6_tone_empathy":         "D6  Tone & Empathy      ",
            "D7_actionability":        "D7  Actionability       ",
        }
        score_dimension = {
            "D1_guardrail_adherence":  "D1",
            "D2_factual_groundedness": "D2",
            "D3_query_resolution":     "D3",
            "D4_literacy_adherence":   "D4",
            "D5_language_adherence":   "D5",
            "D6_tone_empathy":         "D6",
            "D7_actionability":        "D7",
        }
        for key, label in score_labels.items():
            score = scores.get(key)
            display_score = "N/A"
            flag_status = " -"

            if score == "N/A":
                flag_status = " X"
            elif isinstance(score, int):
                flag_status = " X" if score <= 4 else (" !" if score < 8 else " \u2714")
                display_score = score

            # Convert display_score to string for consistent formatting
            print(f"{label}\t{str(display_score):>2}\tMeets Requirements:{flag_status}", end="")

            # Print Reason for each flagged dimension
            dimension_key = score_dimension.get(key)
            if dimension_key:
                flagged_dimension = next((d for d in flags if d["dimension"] == dimension_key), None)
                if flagged_dimension is not None:
                    reason = flagged_dimension.get("reason", "")
                    print(f"\t Reason: {reason}")
                else:
                    print("")
            else:
                print("")
