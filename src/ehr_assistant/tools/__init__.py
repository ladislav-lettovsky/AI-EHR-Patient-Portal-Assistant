"""Tool registry — re-exports all tools and tool-name constant sets."""

from __future__ import annotations

from .education import lookup_lab_education, lookup_medication_education, lookup_trusted_source
from .patient import (
    get_allergies,
    get_clinical_notes_for_encounter,
    get_labs,
    get_medications,
    get_patient_profile,
    get_recent_clinical_note,
    list_patient_encounters,
)
from .policy import policy_route

TOOLS = [
    get_patient_profile,
    policy_route,
    list_patient_encounters,
    get_recent_clinical_note,
    get_clinical_notes_for_encounter,
    get_labs,
    get_medications,
    get_allergies,
    lookup_lab_education,
    lookup_medication_education,
    lookup_trusted_source,
]

# tools that must be forced to use the logged-in patient_id (prevents cross-patient access)
PATIENT_SCOPED_TOOLNAMES = {
    "get_patient_profile",
    "list_patient_encounters",
    "get_recent_clinical_note",
    "get_labs",
    "get_medications",
    "get_allergies",
}

# Define relevant tool constants for reference
INFORMATION_TOOLNAMES = {"lookup_lab_education", "lookup_medication_education"}
RETRIEVAL_LIMITED_TOOLNAMES = {"list_patient_encounters", "get_labs"}
BLOCKED_TOOLNAMES: set[str] = set()  # Tools we would want to block outright can be added here
