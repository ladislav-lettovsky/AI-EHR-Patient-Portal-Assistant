"""Shared utility helpers."""

from __future__ import annotations

import json
import re
from typing import Any

_WHITESPACE_RE = re.compile(r"\s+")


def norm_text(text: str) -> str:
    """Lowercase, strip external and collapse internal whitespaces (to bulletproof comparison)."""
    return _WHITESPACE_RE.sub(" ", text.strip().lower())


def to_json(obj: Any) -> str:
    """Convert a Python object into a JSON string."""
    return json.dumps(obj, ensure_ascii=False, default=str)
