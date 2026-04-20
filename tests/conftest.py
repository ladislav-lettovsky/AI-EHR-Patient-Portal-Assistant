"""Shared test fixtures."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

# Point DATA_DIR at the repo's data/ directory so tools can find the DB/CSVs.
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
os.environ.setdefault("DATA_DIR", str(_DATA_DIR))

# Disable LangSmith tracing during tests.
os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")


@pytest.fixture
def data_dir() -> Path:
    return _DATA_DIR


@pytest.fixture
def sample_patient_ids() -> list[str]:
    return ["P001", "P002", "P003", "P004", "P005", "P006"]


@pytest.fixture
def mock_llm():
    """Return a simple mock that produces canned responses (no API key needed)."""

    class _MockLLM:
        def invoke(self, messages):
            class _Resp:
                content = '{"verdict":"PASS","scores":{},"flags":[],"hard_block":false}'
                tool_calls = None

            return _Resp()

    return _MockLLM()
