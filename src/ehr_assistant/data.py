"""CSV DataFrame loaders (cached on first access)."""

from __future__ import annotations

import pandas as pd

from .config import DATA_DIR

_trusted_sources_df: pd.DataFrame | None = None
_lab_explain_df: pd.DataFrame | None = None
_med_edu_df: pd.DataFrame | None = None
_policy_rules_df: pd.DataFrame | None = None


def get_trusted_sources_df() -> pd.DataFrame:
    global _trusted_sources_df
    if _trusted_sources_df is None:
        _trusted_sources_df = pd.read_csv(DATA_DIR / "trusted_sources_catalog.csv")
    return _trusted_sources_df


def get_lab_explain_df() -> pd.DataFrame:
    global _lab_explain_df
    if _lab_explain_df is None:
        _lab_explain_df = pd.read_csv(DATA_DIR / "patient_friendly_lab_explanations.csv")
    return _lab_explain_df


def get_med_edu_df() -> pd.DataFrame:
    global _med_edu_df
    if _med_edu_df is None:
        _med_edu_df = pd.read_csv(DATA_DIR / "medication_education.csv")
    return _med_edu_df


def get_policy_rules_df() -> pd.DataFrame:
    global _policy_rules_df
    if _policy_rules_df is None:
        _policy_rules_df = pd.read_csv(DATA_DIR / "safety_policy_rules.csv")
    return _policy_rules_df


def get_safety_topics() -> list[str]:
    """Return lowercased, stripped safety topic strings."""
    df = get_policy_rules_df()
    return df["pattern_or_topic"].str.lower().str.strip().tolist()


def get_policy_rules() -> list[dict]:
    """Return policy rules as a list of dicts."""
    return get_policy_rules_df().to_dict(orient="records")
