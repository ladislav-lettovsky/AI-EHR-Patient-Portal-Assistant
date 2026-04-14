"""Patient-scoped tools — query the EHR SQLite database."""

from __future__ import annotations

from typing import Optional

from langchain_core.tools import tool

from ..db import sql_query
from ..utils import to_json


@tool("get_patient_profile")
def get_patient_profile(patient_id: str) -> str:
    """Return patient's profile (first name, language, literacy, etc.)."""
    rows = sql_query(
        """
        SELECT patient_id, first_name, last_name, birth_year, sex_at_birth,
               preferred_language, health_literacy_level, timezone, created_at
        FROM patients
        WHERE patient_id = ?
        """,
        (patient_id,),
    )

    return to_json(rows[0] if rows else {"error": f"Patient {patient_id} not found"})


@tool("list_patient_encounters")
def list_patient_encounters(patient_id: str, limit: int = 5) -> str:
    """Return up to N recent encounters for a patient."""
    max_val = 7                                                                 # Max number of encounters to return
    try:
        limit = max(1, min(int(limit), max_val))
    except Exception:
        limit = max_val

    rows = sql_query(
        """
        SELECT encounter_id, encounter_date, encounter_type, reason_for_visit,
               diagnosis_summary, provider_specialty, followup_instructions, care_team_contact
        FROM encounters
        WHERE patient_id = ?
        ORDER BY encounter_date DESC
        LIMIT ?
        """,
        (patient_id, limit),
    )

    return to_json(rows)


@tool("get_recent_clinical_note")
def get_recent_clinical_note(patient_id: str, note_type: str = "visit_note") -> str:
    """Return most recent clinical note of a given type for the patient."""
    if note_type not in ("visit_note", "discharge_summary"):
        note_type = "visit_note"

    rows = sql_query(
        """
        SELECT note_id, encounter_id, patient_id, note_type, note_text, created_at, author_role
        FROM clinical_notes
        WHERE patient_id = ? AND note_type = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
         (patient_id, note_type),
    )

    return to_json(rows[0] if rows else {"error": f"No {note_type} found for patient {patient_id}"})


@tool("get_clinical_notes_for_encounter")
def get_clinical_notes_for_encounter(encounter_id: str) -> str:
    """Return all notes for a specific encounter."""
    rows = sql_query(
        """
        SELECT note_id, encounter_id, patient_id, note_type, note_text, created_at, author_role
        FROM clinical_notes
        WHERE encounter_id = ?
        ORDER BY created_at ASC
        """,
        (encounter_id,),
    )

    return to_json(rows)


@tool("get_labs")
def get_labs(patient_id: str, test_name: Optional[str] = None, limit: int = 10) -> str:
    """Return recent lab results, optionally filtered by test name."""
    max_val = 10                                                                # Max number of lab results to return
    try:
        limit = max(1, min(int(limit), max_val))
    except Exception:
        limit = max_val

    if test_name:
        rows = sql_query(
            """
            SELECT lab_result_id, ordered_date, result_date, loinc_code, test_name,
                   value_numeric, value_text, unit, ref_range_low, ref_range_high, flag, lab_source
            FROM labs
            WHERE patient_id = ? AND lower(test_name) = lower(?)
            ORDER BY result_date DESC
            LIMIT ?
            """,
            (patient_id, test_name, limit),
        )
    else:
        rows = sql_query(
            """
            SELECT lab_result_id, ordered_date, result_date, loinc_code, test_name,
                   value_numeric, value_text, unit, ref_range_low, ref_range_high, flag, lab_source
            FROM labs
            WHERE patient_id = ?
            ORDER BY result_date DESC
            LIMIT ?
            """,
            (patient_id, limit),
        )

    return to_json(rows)


@tool("get_medications")
def get_medications(patient_id: str, status: str = "active") -> str:
    """Return medications filtered by status (active/stopped/all)."""
    if status not in ("active", "stopped", "all"):
        status = "active"

    if status == "all":
        rows = sql_query(
            """
            SELECT med_id, rxnorm_code, med_name, dose, route, frequency,
                   start_date, end_date, status, indication, prescriber_specialty
            FROM medications
            WHERE patient_id = ?
            ORDER BY status DESC, start_date DESC
            """,
            (patient_id,),
        )
    else:
        rows = sql_query(
            """
            SELECT med_id, rxnorm_code, med_name, dose, route, frequency,
                   start_date, end_date, status, indication, prescriber_specialty
            FROM medications
            WHERE patient_id = ? AND status = ?
            ORDER BY start_date DESC
            """,
            (patient_id, status),
        )

    return to_json(rows)


@tool("get_allergies")
def get_allergies(patient_id: str) -> str:
    """Return allergy records for the patient."""
    rows = sql_query(
        """
        SELECT allergy_id, substance, reaction, severity, recorded_date
        FROM allergies
        WHERE patient_id = ?
        ORDER BY recorded_date DESC
        """,
        (patient_id,),
    )

    return to_json(rows)
