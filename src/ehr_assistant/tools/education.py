"""CSV-lookup education tools — lab, medication, and trusted source lookups."""

from __future__ import annotations

from langchain_core.tools import tool

from ..data import get_lab_explain_df, get_med_edu_df, get_trusted_sources_df
from ..utils import norm_text, to_json


@tool("lookup_lab_education")
def lookup_lab_education(test_name: str) -> str:
    """Return plain-language lab education."""
    tn = norm_text(test_name)
    df = get_lab_explain_df().copy()
    df["_k"] = df["test_name_normalized"].astype(str).map(norm_text)

    hit = df[df["_k"] == tn]
    if hit.empty:
        hit = df[df["_k"].str.contains(tn, na=False)]

    if hit.empty:
        return to_json({"error": f"No lab education found for '{test_name}'"})

    row = hit.iloc[0].drop(labels=["_k"]).to_dict()

    return to_json(row)


@tool("lookup_medication_education")
def lookup_medication_education(med_name: str) -> str:
    """Return plain-language medication education."""
    mn = norm_text(med_name)
    df = get_med_edu_df().copy()
    df["_k"] = df["med_name_normalized"].astype(str).map(norm_text)

    hit = df[df["_k"] == mn]
    if hit.empty:
        hit = df[df["_k"].str.contains(mn, na=False)]

    if hit.empty:
        return to_json({"error": f"No medication education found for '{med_name}'"})

    row = hit.iloc[0].drop(labels=["_k"]).to_dict()

    return to_json(row)


@tool("lookup_trusted_source")
def lookup_trusted_source(source_id: str) -> str:
    """Return metadata for a trusted source (name, URL, etc.)."""
    hit = get_trusted_sources_df()[get_trusted_sources_df()["source_id"] == source_id]
    if hit.empty:
        return to_json({"error": f"source_id {source_id} not found"})

    return to_json(hit.iloc[0].to_dict())
