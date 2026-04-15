"""Environment-based configuration and logging setup."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Silence noisy third-party libraries before they are imported elsewhere.
os.environ.setdefault("TQDM_DISABLE", "1")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA_DIR: Path = Path(os.environ.get("DATA_DIR", Path(__file__).resolve().parent.parent.parent / "data"))
RESULTS_DIR: Path = Path(os.environ.get("RESULTS_DIR", Path(__file__).resolve().parent.parent.parent / "results"))

# ---------------------------------------------------------------------------
# API / model settings
# ---------------------------------------------------------------------------
OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
OPENAI_BASE_URL: str | None = os.environ.get("OPENAI_BASE_URL") or None

MODEL_GENERATOR: str = os.environ.get("MODEL_GENERATOR", "gpt-4o-mini")
MODEL_VALIDATOR: str = os.environ.get("MODEL_VALIDATOR", "gpt-4o")
MODEL_POLICY: str = os.environ.get("MODEL_POLICY", "gpt-4o-mini")

TEMPERATURE: float = 0.0

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "WARNING")

NOISY_LOGGERS: list[str] = [
    "httpx",
    "httpcore",
    "openai",
    "langchain",
    "langsmith",
    "langgraph",
]


def _configure_logging() -> None:
    """Set root log level and suppress noisy third-party loggers."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.WARNING),
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    for name in NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)


_configure_logging()
