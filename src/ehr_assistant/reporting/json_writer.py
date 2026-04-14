"""Write structured JSON results to file."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def write_result(result: Dict[str, Any], output_dir: Path) -> Path:
    """Write a single run result as a timestamped JSON file.

    Returns the path to the written file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    patient_id = result.get("patient_id", "unknown")
    filename = f"result_{patient_id}_{ts}.json"
    filepath = output_dir / filename

    payload = {
        "run_timestamp": ts,
        "patient_id": result.get("patient_id"),
        "user_query": result.get("user_query"),
        "final_answer": result.get("final_answer"),
        "verdict": result.get("verdict"),
        "scores": result.get("scores"),
        "flags": result.get("flags"),
        "hard_block": result.get("hard_block"),
        "tools_called": result.get("tools_called"),
        "errors": result.get("errors"),
        "citations": result.get("citations"),
    }

    filepath.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
    return filepath
