from io import BytesIO
from pathlib import Path
import sys
from types import ModuleType
from zipfile import ZipFile

import pytest
from postgrest.exceptions import APIError

from app import create_app
from utils import auth as auth_utils

PIPELINE_ROOT = (
    Path(__file__).resolve().parents[2]
    / "EduQuest-Integrated-main"
    / "EduQuest-Integrated-main"
)
sys.path.insert(0, str(PIPELINE_ROOT))
from QP_blueprint.faculty_input_validator import validate_faculty_input


def _generated_review_paper():
    return {
        "paper_information": {
            "branch": "CSE",
            "semester": 4,
            "subject": "Operating Systems",
            "subject_code": "OS",
            "exam_type": "University",
            "paper_total_marks": 70,
        },
        "sections": {
            "Q1": {
                "questions_to_attempt": 5,
                "questions": [
                    {
                        "canonical_id": f"CAN_2_{index}",
                        "question_text": f"Define operating system concept {index}.",
                        "unit": "Unit-I",
                        "marks": 2,
                        "rua": "R",
                        "difficulty": "Easy",
                        "course_outcome": "CO1",
                    }
                    for index in range(7)
                ],
            },
            "Q2": {
                "questions_to_attempt": 15,
                "questions": [
                    {
                        "canonical_id": f"CAN_4_{index}",
                        "question_text": f"Explain operating system concept {index}.",
                        "unit": "Unit-I",
                        "marks": 4,
                        "rua": "R",
                        "difficulty": "Easy",
                        "course_outcome": "CO1",
                    }
                    for index in range(20)
                ],
            },
        },
    }


def _generation_result(paper, persistence):
    return {
        "status": "SUCCESS",
        "selected_questions": paper,
        "generation_result": {"persistence": persistence},
    }


def _advance_java_faculty_input():
    return {
        "branch": "Computer Technology",
        "semester": 5,
        "subject": "Advance Java",
        "subject_id": 1,
        "subject_code": "21526",
        "exam_type": "University",
        "total_marks": 70,
        "selected_units": ["Unit-I", "Unit-II", "Unit-III", "Unit-IV", "Unit-V"],
        "difficulty_allocation": {"Easy": 40, "Medium": 26, "Hard": 28},
        "rua_allocation": {
            "Unit-I": {"R": 2, "U": 6, "A": 6, "Total": 14},
            "Unit-II": {"R": 6, "U": 8, "A": 8, "Total": 22},
            "Unit-III": {"R": 6, "U": 8, "A": 8, "Total": 22},
            "Unit-IV": {"R": 4, "U": 6, "A": 8, "Total": 18},
            "Unit-V": {"R": 4, "U": 6, "A": 8, "Total": 18},
        },
        "co_requirements": ["CO1"],
        "question_pattern": {
            "Q1": {
                "questions_to_generate": 7,
                "questions_to_attempt": 5,
                "marks_per_question": 2,
            },
            **{
                f"Q{section}": {
                    "questions_to_generate": 4,
                    "questions_to_attempt": 3,
                    "marks_per_question": 4,
                }
                for section in range(2, 7)
            },
        },
        "instructions": [],
    }


def _authenticate_faculty(
    monkeypatch,
    assigned_subject_ids=(1,),
    can_generate_subject_ids=None,
    subjects=None,
    is_active=True,
    missing_generation_flag=False,
):
    if can_generate_subject_ids is None:
        can_generate_subject_ids = assigned_subject_ids
    can_generate_subject_ids = set(can_generate_subject_ids)
    profile = {
        "user_id": 42,
        "auth_user_id": "auth-user-42",
        "role": "faculty",
        "is_active": is_active,
    }
    monkeypatch.setattr(auth_utils, "get_supabase_profile", lambda _token: profile)

    class Response:
        def __init__(self, data):
            self.data = data

    class Query:
        def __init__(self, table_name):
            self.table_name = table_name
            self.filters = {}
            self.subject_ids = None

        def select(self, _columns):
            return self

        def eq(self, column, value):
            self.filters[column] = value
            return self

        def in_(self, column, values):
            assert column == "subject_id"
            self.subject_ids = set(values)
            return self

        def order(self, _column):
            return self

        def limit(self, _count):
            return self

        def execute(self):
            if self.table_name == "faculty_subject_assignment":
                assert self.filters.get("faculty_id") == 42
                assert self.filters.get("is_active") is True
                if missing_generation_flag and "can_generate" in self.filters:
                    raise APIError({
                        "code": "PGRST204",
                        "message": (
                            "Could not find the 'can_generate' column of "
                            "'faculty_subject_assignment' in the schema cache"
                        ),
                    })
                return Response([
                    {
                        "subject_id": subject_id,
                        "can_generate": subject_id in can_generate_subject_ids,
                    }
                    for subject_id in assigned_subject_ids
                    if self.filters.get("subject_id", subject_id) == subject_id
                    and (
                        "can_generate" not in self.filters
                        or subject_id in can_generate_subject_ids
                    )
                ])
            rows = subjects or []
            if self.subject_ids is not None:
                rows = [row for row in rows if row["subject_id"] in self.subject_ids]
            return Response(rows)

    class Client:
        def table(self, table_name):
            return Query(table_name)

    import database

    monkeypatch.setattr(database, "get_supabase_admin_client", lambda: Client())
    return "faculty-supabase-token"


def test_frontend_generation_requires_complete_persistence_before_docx(
    monkeypatch,
):
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    token = _authenticate_faculty(monkeypatch)
    paper = _generated_review_paper()
    calls = []
    persistence = {
        "status": "SAVED",
        "paper_id": 12,
        "generation_id": 5,
        "total_questions": 27,
        "total_marks": 94,
        "paper_records": 1,
        "mapped_questions": 27,
        "usage_records": 27,
        "generation_log_records": 1,
    }

    pipeline = ModuleType("eduquest_pipeline")

    def generate_final_question_paper(
        faculty_input,
        output_dir,
        persist=False,
        generated_by=None,
    ):
        calls.append({
            "faculty_input": faculty_input,
            "output_dir": output_dir,
            "persist": persist,
            "generated_by": generated_by,
        })
        return _generation_result(paper, persistence)

    pipeline.generate_final_question_paper = generate_final_question_paper
    monkeypatch.setitem(sys.modules, "eduquest_pipeline", pipeline)

    generate_response = client.post(
        "/api/generate-question-paper",
        json={
            "subject": "Operating Systems",
            "subject_id": 1,
            "selected_units": ["Unit-I"],
            "rua_allocation": {"Unit-I": {"R": 94}},
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert generate_response.status_code == 200
    assert calls and calls[0]["persist"] is True
    assert calls[0]["generated_by"] == 42
    reviewed_paper = generate_response.get_json()
    assert sum(
        len(section["questions"])
        for section in reviewed_paper["sections"].values()
    ) == 27

    docx_response = client.post(
        "/api/download-reviewed-paper",
        json=reviewed_paper,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert docx_response.status_code == 200
    assert docx_response.mimetype == (
        "application/vnd.openxmlformats-officedocument."
        "wordprocessingml.document"
    )
    with ZipFile(BytesIO(docx_response.data)) as document:
        document_xml = document.read("word/document.xml")
    assert b"Define operating system concept 0." in document_xml


def test_frontend_generation_rejects_incomplete_persistence(monkeypatch):
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    token = _authenticate_faculty(monkeypatch)
    pipeline = ModuleType("eduquest_pipeline")
    pipeline.generate_final_question_paper = lambda **_kwargs: _generation_result(
        _generated_review_paper(),
        {
            "status": "SAVED",
            "paper_id": 13,
            "generation_id": None,
            "total_questions": 27,
            "mapped_questions": 6,
            "usage_records": 0,
            "generation_log_records": 0,
        },
    )
    monkeypatch.setitem(sys.modules, "eduquest_pipeline", pipeline)

    response = client.post(
        "/api/generate-question-paper",
        json={
            "subject": "Operating Systems",
            "subject_id": 1,
            "selected_units": ["Unit-I"],
            "rua_allocation": {"Unit-I": {"R": 94}},
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 500
    assert "PERSISTENCE_ERROR" in response.get_json()["error"]


def test_advance_java_request_preserves_real_code_and_passes_validation(monkeypatch):
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    token = _authenticate_faculty(monkeypatch)
    faculty_input = _advance_java_faculty_input()
    calls = []
    persistence = {
        "status": "SAVED",
        "paper_id": 12,
        "generation_id": 5,
        "total_questions": 27,
        "total_marks": 94,
        "paper_records": 1,
        "mapped_questions": 27,
        "usage_records": 27,
        "generation_log_records": 1,
    }
    paper = _generated_review_paper()
    paper["paper_information"].update({
        "subject": "Advance Java",
        "subject_code": "21526",
        "branch": "Computer Technology",
        "semester": 5,
    })
    pipeline = ModuleType("eduquest_pipeline")

    def generate_final_question_paper(
        faculty_input,
        output_dir,
        persist=False,
        generated_by=None,
    ):
        validation = validate_faculty_input(faculty_input)
        calls.append({
            "faculty_input": faculty_input,
            "valid": validation["valid"],
            "errors": validation["errors"],
            "persist": persist,
            "generated_by": generated_by,
        })
        if not validation["valid"]:
            return {
                "status": "FAILED",
                "stage": "FACULTY_INPUT_VALIDATION",
                "errors": validation["errors"],
            }
        return _generation_result(paper, persistence)

    pipeline.generate_final_question_paper = generate_final_question_paper
    monkeypatch.setitem(sys.modules, "eduquest_pipeline", pipeline)

    response = client.post(
        "/api/generate-question-paper",
        json=faculty_input,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert calls[0]["valid"] is True
    assert calls[0]["errors"] == []
    assert calls[0]["persist"] is True
    assert calls[0]["generated_by"] == 42
    assert calls[0]["faculty_input"]["subject_code"] == "21526"


def test_paper_generation_subject_endpoint_returns_full_subject_identity(monkeypatch):
    subject = {
        "subject_id": 1,
        "subject_name": "Advance Java",
        "subject_code": "21526",
        "branch": "Computer Technology",
        "semester": "5",
    }

    token = _authenticate_faculty(monkeypatch, subjects=[subject])
    app = create_app()
    app.config["TESTING"] = True

    response = app.test_client().get(
        "/api/paper-generation/subjects",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.get_json()["subjects"] == [subject]


def test_paper_generation_subject_endpoint_filters_unassigned_subjects(monkeypatch):
    assigned = {
        "subject_id": 1,
        "subject_name": "Advance Java",
        "subject_code": "21526",
        "branch": "Computer Technology",
        "semester": "5",
    }
    unassigned = {**assigned, "subject_id": 2, "subject_name": "Operating Systems"}
    token = _authenticate_faculty(
        monkeypatch,
        assigned_subject_ids=(1,),
        subjects=[assigned, unassigned],
    )
    app = create_app()
    app.config["TESTING"] = True

    response = app.test_client().get(
        "/api/paper-generation/subjects",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.get_json()["subjects"] == [assigned]


def test_paper_generation_subject_endpoint_supports_legacy_assignments(monkeypatch):
    subject = {
        "subject_id": 1,
        "subject_name": "Advance Java",
        "subject_code": "21526",
        "branch": "Computer Technology",
        "semester": "5",
    }
    token = _authenticate_faculty(
        monkeypatch,
        subjects=[subject],
        missing_generation_flag=True,
    )
    app = create_app()
    app.config["TESTING"] = True

    response = app.test_client().get(
        "/api/paper-generation/subjects",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.get_json()["subjects"] == [subject]


def test_faculty_cannot_generate_a_paper_for_an_unassigned_subject(monkeypatch):
    token = _authenticate_faculty(monkeypatch, assigned_subject_ids=())
    app = create_app()
    app.config["TESTING"] = True
    pipeline = ModuleType("eduquest_pipeline")
    pipeline.generate_final_question_paper = lambda **_kwargs: pytest.fail(
        "The pipeline must not run for an unassigned subject."
    )
    monkeypatch.setitem(sys.modules, "eduquest_pipeline", pipeline)

    response = app.test_client().post(
        "/api/generate-question-paper",
        json={
            "subject": "Operating Systems",
            "subject_id": 1,
            "selected_units": ["Unit-I"],
            "rua_allocation": {"Unit-I": {"R": 94}},
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.get_json()["message"] == (
        "You are not assigned as a paper setter for this subject."
    )


def test_moderation_only_faculty_cannot_generate_a_paper(monkeypatch):
    _authenticate_faculty(
        monkeypatch,
        assigned_subject_ids=(1,),
        can_generate_subject_ids=(),
    )
    app = create_app()
    app.config["TESTING"] = True
    pipeline = ModuleType("eduquest_pipeline")
    pipeline.generate_final_question_paper = lambda **_kwargs: pytest.fail(
        "The pipeline must not run for a moderation-only assignment."
    )
    monkeypatch.setitem(sys.modules, "eduquest_pipeline", pipeline)

    response = app.test_client().post(
        "/api/generate-question-paper",
        json={
            "subject": "Operating Systems",
            "subject_id": 1,
            "selected_units": ["Unit-I"],
            "rua_allocation": {"Unit-I": {"R": 94}},
        },
        headers={"Authorization": f"Bearer faculty-supabase-token"},
    )

    assert response.status_code == 403, response.get_json()
    assert response.get_json()["message"] == (
        "You are not assigned as a paper setter for this subject."
    )


def test_legacy_assignment_can_generate_when_generation_flag_is_missing(monkeypatch):
    token = _authenticate_faculty(
        monkeypatch,
        missing_generation_flag=True,
    )
    app = create_app()
    app.config["TESTING"] = True
    pipeline = ModuleType("eduquest_pipeline")
    pipeline.generate_final_question_paper = lambda **_kwargs: pytest.fail(
        "Generation should not run for invalid paper input."
    )
    monkeypatch.setitem(sys.modules, "eduquest_pipeline", pipeline)

    response = app.test_client().post(
        "/api/generate-question-paper",
        json={
            "subject": "Operating Systems",
            "subject_id": 1,
            "selected_units": "Unit-I",
            "rua_allocation": {"Unit-I": {"R": 94}},
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == (
        "selected_units and rua_allocation must be provided as matching collections."
    )


def test_inactive_faculty_cannot_generate_a_paper(monkeypatch):
    token = _authenticate_faculty(monkeypatch, is_active=False)
    app = create_app()
    app.config["TESTING"] = True
    pipeline = ModuleType("eduquest_pipeline")
    pipeline.generate_final_question_paper = lambda **_kwargs: pytest.fail(
        "The pipeline must not run for an inactive faculty account."
    )
    monkeypatch.setitem(sys.modules, "eduquest_pipeline", pipeline)

    response = app.test_client().post(
        "/api/generate-question-paper",
        json={
            "subject": "Operating Systems",
            "subject_id": 1,
            "selected_units": ["Unit-I"],
            "rua_allocation": {"Unit-I": {"R": 94}},
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
