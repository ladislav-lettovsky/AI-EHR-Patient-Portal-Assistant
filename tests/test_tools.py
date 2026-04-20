"""Unit tests for patient and education tools."""

from __future__ import annotations

import json


class TestPatientTools:
    """Test patient-scoped tools against health_portal.db."""

    def test_get_patient_profile_known(self):
        from ehr_assistant.tools.patient import get_patient_profile

        raw = get_patient_profile.invoke({"patient_id": "P001"})
        data = json.loads(raw)
        assert data["patient_id"] == "P001"
        assert "first_name" in data

    def test_get_patient_profile_unknown(self):
        from ehr_assistant.tools.patient import get_patient_profile

        raw = get_patient_profile.invoke({"patient_id": "ZZZZ"})
        data = json.loads(raw)
        assert "error" in data

    def test_list_patient_encounters(self):
        from ehr_assistant.tools.patient import list_patient_encounters

        raw = list_patient_encounters.invoke({"patient_id": "P001", "limit": 3})
        data = json.loads(raw)
        assert isinstance(data, list)
        assert len(data) <= 3

    def test_get_recent_clinical_note(self):
        from ehr_assistant.tools.patient import get_recent_clinical_note

        raw = get_recent_clinical_note.invoke({"patient_id": "P001", "note_type": "visit_note"})
        data = json.loads(raw)
        assert "note_id" in data or "error" in data

    def test_get_clinical_notes_for_encounter(self):
        from ehr_assistant.tools.patient import (
            get_clinical_notes_for_encounter,
            list_patient_encounters,
        )

        # Get a real encounter_id first
        encounters_raw = list_patient_encounters.invoke({"patient_id": "P001", "limit": 1})
        encounters = json.loads(encounters_raw)
        if encounters:
            enc_id = encounters[0]["encounter_id"]
            raw = get_clinical_notes_for_encounter.invoke(
                {"patient_id": "P001", "encounter_id": enc_id}
            )
            data = json.loads(raw)
            assert isinstance(data, list)

    def test_get_clinical_notes_for_encounter_cross_patient_blocked(self):
        from ehr_assistant.tools.patient import (
            get_clinical_notes_for_encounter,
            list_patient_encounters,
        )

        # Grab P001's encounter, then query it as P002 — should return empty list (scoped out)
        encounters_raw = list_patient_encounters.invoke({"patient_id": "P001", "limit": 1})
        encounters = json.loads(encounters_raw)
        if encounters:
            enc_id = encounters[0]["encounter_id"]
            raw = get_clinical_notes_for_encounter.invoke(
                {"patient_id": "P002", "encounter_id": enc_id}
            )
            data = json.loads(raw)
            assert isinstance(data, list)
            assert len(data) == 0, "Cross-patient note access must return no rows"

    def test_get_labs(self):
        from ehr_assistant.tools.patient import get_labs

        raw = get_labs.invoke({"patient_id": "P001", "limit": 5})
        data = json.loads(raw)
        assert isinstance(data, list)
        assert len(data) <= 5

    def test_get_labs_by_name(self):
        from ehr_assistant.tools.patient import get_labs

        raw = get_labs.invoke({"patient_id": "P001", "test_name": "Hemoglobin A1c", "limit": 5})
        data = json.loads(raw)
        assert isinstance(data, list)

    def test_get_medications(self):
        from ehr_assistant.tools.patient import get_medications

        raw = get_medications.invoke({"patient_id": "P001", "status": "active"})
        data = json.loads(raw)
        assert isinstance(data, list)

    def test_get_medications_all(self):
        from ehr_assistant.tools.patient import get_medications

        raw = get_medications.invoke({"patient_id": "P001", "status": "all"})
        data = json.loads(raw)
        assert isinstance(data, list)

    def test_get_allergies(self):
        from ehr_assistant.tools.patient import get_allergies

        raw = get_allergies.invoke({"patient_id": "P001"})
        data = json.loads(raw)
        assert isinstance(data, list)


class TestEducationTools:
    """Test CSV-lookup education tools."""

    def test_lookup_lab_education_known(self):
        from ehr_assistant.tools.education import lookup_lab_education

        raw = lookup_lab_education.invoke({"test_name": "Hemoglobin A1c"})
        data = json.loads(raw)
        assert "error" not in data

    def test_lookup_lab_education_unknown(self):
        from ehr_assistant.tools.education import lookup_lab_education

        raw = lookup_lab_education.invoke({"test_name": "CompletelyFakeLabXYZ123"})
        data = json.loads(raw)
        assert "error" in data

    def test_lookup_medication_education_known(self):
        from ehr_assistant.tools.education import lookup_medication_education

        raw = lookup_medication_education.invoke({"med_name": "atorvastatin"})
        data = json.loads(raw)
        assert "error" not in data

    def test_lookup_medication_education_unknown(self):
        from ehr_assistant.tools.education import lookup_medication_education

        raw = lookup_medication_education.invoke({"med_name": "CompletelyFakeMedXYZ123"})
        data = json.loads(raw)
        assert "error" in data

    def test_lookup_trusted_source_unknown(self):
        from ehr_assistant.tools.education import lookup_trusted_source

        raw = lookup_trusted_source.invoke({"source_id": "NONEXISTENT"})
        data = json.loads(raw)
        assert "error" in data
