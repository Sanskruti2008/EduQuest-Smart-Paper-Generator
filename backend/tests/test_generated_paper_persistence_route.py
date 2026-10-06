from io import BytesIO
from pathlib import Path
import sys
from types import ModuleType
from zipfile import ZipFile

from app import create_app
from utils.auth import _generate_role_token

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
        "branch": "Computer Engineering",
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


def test_frontend_generation_requires_complete_persistence_before_docx(
    monkeypatch,
):
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    token = _generate_role_token("faculty@example.test", "faculty")
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
    ):
        calls.append({
            "faculty_input": faculty_input,
            "output_dir": output_dir,
            "persist": persist,
        })
        return _generation_result(paper, persistence)

    pipeline.generate_final_question_paper = generate_final_question_paper
    monkeypatch.setitem(sys.modules, "eduquest_pipeline", pipeline)

    generate_response = client.post(
        "/api/generate-question-paper",
        json={
            "subject": "Operating Systems",
            "selected_units": ["Unit-I"],
            "rua_allocation": {"Unit-I": {"R": 94}},
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert generate_response.status_code == 200
    assert calls and calls[0]["persist"] is True
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
    token = _generate_role_token("faculty@example.test", "faculty")
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
    token = _generate_role_token("faculty@example.test", "faculty")
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
        "branch": "Computer Engineering",
        "semester": 5,
    })
    pipeline = ModuleType("eduquest_pipeline")

    def generate_final_question_paper(faculty_input, output_dir, persist=False):
        validation = validate_faculty_input(faculty_input)
        calls.append({
            "faculty_input": faculty_input,
            "valid": validation["valid"],
            "errors": validation["errors"],
            "persist": persist,
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
    assert calls[0]["faculty_input"]["subject_code"] == "21526"


def test_paper_generation_subject_endpoint_returns_full_subject_identity(monkeypatch):
    subject = {
        "subject_id": 1,
        "subject_name": "Advance Java",
        "subject_code": "21526",
        "branch": "Computer Engineering",
        "semester": "5",
    }

    class Response:
        data = [subject]

    class Query:
        def select(self, _columns):
            return self

        def order(self, _column):
            return self

        def execute(self):
            return Response()

    class Client:
        def table(self, name):
            assert name == "subject"
            return Query()

    import database

    monkeypatch.setattr(database, "get_supabase_client", lambda: Client())
    app = create_app()
    app.config["TESTING"] = True
    token = _generate_role_token("faculty@example.test", "faculty")

    response = app.test_client().get(
        "/api/paper-generation/subjects",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.get_json()["subjects"] == [subject]
