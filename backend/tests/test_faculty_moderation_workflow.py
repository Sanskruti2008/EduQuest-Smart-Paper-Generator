from copy import deepcopy
from types import SimpleNamespace

import pytest

from app import create_app
from utils import auth as auth_utils


class FakeQuery:
    def __init__(self, client, table_name):
        self.client = client
        self.table_name = table_name
        self.filters = []
        self.action = "select"
        self.payload = None

    def select(self, _fields):
        self.action = "select"
        return self

    def eq(self, field, value):
        self.filters.append(("eq", field, value))
        return self

    def in_(self, field, values):
        self.filters.append(("in", field, list(values)))
        return self

    def order(self, _field, desc=False):
        return self

    def limit(self, _count):
        return self

    def update(self, payload):
        self.action = "update"
        self.payload = payload
        return self

    def execute(self):
        rows = self.client.tables[self.table_name]

        def matches(row):
            for kind, field, value in self.filters:
                if kind == "eq" and row.get(field) != value:
                    return False
                if kind == "in" and row.get(field) not in value:
                    return False
            return True

        matching = [row for row in rows if matches(row)]
        if self.action == "update":
            for row in matching:
                row.update(self.payload)
        return type("Response", (), {"data": deepcopy(matching)})()


class FakeClient:
    def __init__(self, tables):
        self.tables = tables

    def table(self, table_name):
        return FakeQuery(self, table_name)


def _setup(monkeypatch, *, can_moderate=True, can_generate=False, is_active=True):
    profiles = {
        "faculty-token": {
            "user_id": 42,
            "auth_user_id": "faculty-auth-42",
            "role": "faculty",
            "name": "Moderator Faculty",
            "email": "faculty@example.test",
            "employee_id": "FAC042",
            "department": "Computer Technology",
            "is_active": is_active,
        },
        "admin-token": {
            "user_id": 1,
            "auth_user_id": "admin-auth-1",
            "role": "admin",
            "name": "Admin",
            "is_active": True,
        },
    }
    tables = {
        "faculty_subject_assignment": [{
            "faculty_id": 42,
            "subject_id": 7,
            "is_active": True,
            "can_generate": can_generate,
            "can_moderate": can_moderate,
        }],
        "subject": [{
            "subject_id": 7,
            "subject_name": "Advanced Java",
            "subject_code": "21526",
            "branch": "Computer Technology",
            "semester": "5",
        }],
        "User": [
            {
                "user_id": 42,
                "auth_user_id": "faculty-auth-42",
                "name": "Moderator Faculty",
                "email": "faculty@example.test",
                "employee_id": "FAC042",
                "department": "Computer Technology",
                "role": "faculty",
                "is_active": is_active,
            },
            {"user_id": 43, "name": "Paper Setter"},
            {
                "user_id": 1,
                "auth_user_id": "admin-auth-1",
                "name": "Admin",
                "role": "admin",
                "is_active": True,
            },
        ],
        "questionpaper": [
            {
                "paper_id": 101,
                "subject_id": 7,
                "exam_type": "Final Examination",
                "exam_year": 2026,
                "created_at": "2026-10-01T10:00:00+00:00",
                "raw_json": {
                    "selection": {
                        "paper_information": {"subject": "Advanced Java"},
                        "sections": {"Q1": {"questions": [
                            {"question_text": "Explain inheritance.", "marks": 5}
                        ]}},
                    }
                },
                "generated_by": 43,
                "status": "SUBMITTED_FOR_MODERATION",
                "moderated_by": None,
                "moderated_at": None,
                "moderation_comments": None,
                "reviewed_by": None,
                "reviewed_at": None,
                "review_comments": None,
            },
            {
                "paper_id": 102,
                "subject_id": 7,
                "exam_type": "Final Examination",
                "exam_year": 2026,
                "created_at": "2026-10-01T11:00:00+00:00",
                "raw_json": {},
                "generated_by": 42,
                "status": "SUBMITTED_FOR_MODERATION",
                "moderated_by": None,
                "moderated_at": None,
                "moderation_comments": None,
            },
        ],
    }
    monkeypatch.setattr(
        auth_utils,
        "get_supabase_profile",
        lambda token: profiles.get(token.removeprefix("Bearer ")),
    )
    monkeypatch.setattr(
        auth_utils,
        "get_supabase_auth_user_id",
        lambda token: {
            "faculty-token": "faculty-auth-42",
            "admin-token": "admin-auth-1",
            "unlinked-token": "unlinked-auth-99",
        }.get(token.removeprefix("Bearer ")),
    )
    import database

    client = FakeClient(tables)
    client.auth = SimpleNamespace(
        get_user=lambda token: SimpleNamespace(
            user=SimpleNamespace(
                id="faculty-auth-42" if token == "faculty-token" else "admin-auth-1"
            )
        )
    )
    monkeypatch.setattr(database, "get_supabase_admin_client", lambda: client)
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client(), tables


def _headers(role="faculty"):
    return {"Authorization": f"Bearer {role}-token"}


@pytest.mark.parametrize(
    ("assignment_rows", "generation_count", "moderation_count"),
    [
        ([{"subject_id": 7, "is_active": True, "can_generate": True,
           "can_moderate": False}], 1, 0),
        ([{"subject_id": 7, "is_active": True, "can_generate": False,
           "can_moderate": True}], 0, 1),
        ([
            {"subject_id": 7, "is_active": True, "can_generate": True,
             "can_moderate": False},
            {"subject_id": 8, "is_active": True, "can_generate": False,
             "can_moderate": True},
            {"subject_id": 9, "is_active": True, "can_generate": True,
             "can_moderate": True},
            {"subject_id": 10, "is_active": False, "can_generate": True,
             "can_moderate": True},
        ], 2, 2),
        ([], 0, 0),
    ],
)
def test_faculty_me_uses_authenticated_profile_and_active_responsibilities(
    monkeypatch, assignment_rows, generation_count, moderation_count
):
    client, tables = _setup(monkeypatch)
    tables["faculty_subject_assignment"] = [
        {"faculty_id": 42, **assignment} for assignment in assignment_rows
    ]

    response = client.get("/api/faculty/me", headers=_headers())

    assert response.status_code == 200
    data = response.get_json()
    assert data["faculty"] == {
        "user_id": 42,
        "auth_user_id": "faculty-auth-42",
        "name": "Moderator Faculty",
        "email": "faculty@example.test",
        "employee_id": "FAC042",
        "department": "Computer Technology",
        "role": "faculty",
        "is_active": True,
    }
    assert data["responsibilities"] == {
        "can_generate": generation_count > 0,
        "can_moderate": moderation_count > 0,
        "generation_subject_count": generation_count,
        "moderation_subject_count": moderation_count,
    }


def test_faculty_me_rejects_inactive_faculty(monkeypatch):
    client, _tables = _setup(monkeypatch, is_active=False)

    response = client.get("/api/faculty/me", headers=_headers())

    assert response.status_code == 403
    assert response.get_json()["message"] == "Faculty account is inactive."


def test_faculty_me_requires_bearer_token(monkeypatch):
    client, _tables = _setup(monkeypatch)

    response = client.get("/api/faculty/me")

    assert response.status_code == 401
    assert response.get_json() == {
        "success": False,
        "message": "Authentication required.",
    }


def test_faculty_me_validates_supabase_token_and_resolves_linked_profile(monkeypatch):
    validate_token = auth_utils.get_supabase_auth_user_id
    client, _tables = _setup(monkeypatch)
    monkeypatch.setattr(auth_utils, "get_supabase_auth_user_id", validate_token)

    response = client.get("/api/faculty/me", headers=_headers())

    assert response.status_code == 200
    assert response.get_json()["faculty"]["auth_user_id"] == "faculty-auth-42"


def test_faculty_me_rejects_invalid_supabase_token(monkeypatch):
    client, _tables = _setup(monkeypatch)

    response = client.get(
        "/api/faculty/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401


def test_faculty_me_reports_unlinked_auth_user(monkeypatch):
    client, _tables = _setup(monkeypatch)

    response = client.get(
        "/api/faculty/me",
        headers={"Authorization": "Bearer unlinked-token"},
    )

    assert response.status_code == 404
    assert response.get_json()["message"] == (
        "Faculty profile is not linked to this authentication account."
    )


def test_admin_cannot_access_faculty_me(monkeypatch):
    client, _tables = _setup(monkeypatch)

    response = client.get(
        "/api/faculty/me",
        headers=_headers("admin"),
    )

    assert response.status_code == 403
    assert response.get_json()["message"] == "Faculty access required."


def test_faculty_me_reports_profile_service_failure(monkeypatch):
    client, _tables = _setup(monkeypatch)
    import database

    def fail_to_connect():
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(database, "get_supabase_admin_client", fail_to_connect)

    response = client.get("/api/faculty/me", headers=_headers())

    assert response.status_code == 500
    assert response.get_json() == {
        "success": False,
        "message": "Unable to load faculty profile.",
    }


def test_moderation_queue_only_includes_assigned_subject_and_excludes_own_papers(monkeypatch):
    client, _tables = _setup(monkeypatch)

    response = client.get(
        "/api/faculty/moderation/papers",
        headers=_headers(),
    )

    assert response.status_code == 200
    papers = response.get_json()["papers"]
    assert [paper["paper_id"] for paper in papers] == [101]
    assert papers[0]["generated_by_name"] == "Paper Setter"
    assert papers[0]["sections"]["Q1"]["questions"][0]["question_text"] == (
        "Explain inheritance."
    )


def test_moderation_permission_is_required_for_decisions(monkeypatch):
    client, _tables = _setup(monkeypatch, can_moderate=False)

    response = client.post(
        "/api/faculty/moderation/papers/101/approve",
        headers=_headers(),
    )

    assert response.status_code == 403
    assert response.get_json()["message"] == (
        "You are not assigned to moderate this subject."
    )


def test_moderator_cannot_moderate_own_paper(monkeypatch):
    client, _tables = _setup(monkeypatch)

    response = client.post(
        "/api/faculty/moderation/papers/102/approve",
        headers=_headers(),
    )

    assert response.status_code == 403
    assert response.get_json()["message"] == "You cannot moderate your own paper."


def test_request_changes_updates_canonical_paper_and_my_papers(monkeypatch):
    client, tables = _setup(monkeypatch)

    moderation_response = client.post(
        "/api/faculty/moderation/papers/101/request-changes",
        json={"comment": "Please replace the duplicate question."},
        headers=_headers(),
    )

    assert moderation_response.status_code == 200
    changed = tables["questionpaper"][0]
    assert changed["status"] == "CHANGES_REQUESTED"
    assert changed["moderated_by"] == 42
    assert changed["moderation_comments"] == "Please replace the duplicate question."

    setter_profile = {
        "user_id": 43,
        "auth_user_id": "setter-auth-43",
        "role": "faculty",
        "is_active": True,
    }
    monkeypatch.setattr(auth_utils, "get_supabase_profile", lambda _token: setter_profile)
    response = client.get(
        "/api/faculty/my-papers",
        headers={"Authorization": "Bearer setter-token"},
    )
    assert response.status_code == 200
    assert response.get_json()["papers"][0]["status"] == "CHANGES_REQUESTED"
    assert response.get_json()["papers"][0]["moderation_comments"] == (
        "Please replace the duplicate question."
    )


def test_moderator_approval_exposes_paper_to_admin_review(monkeypatch):
    client, tables = _setup(monkeypatch)

    moderation_response = client.post(
        "/api/faculty/moderation/papers/101/approve",
        headers=_headers(),
    )
    assert moderation_response.status_code == 200
    assert tables["questionpaper"][0]["status"] == "APPROVED_BY_MODERATOR"

    admin_response = client.get(
        "/api/admin/review-papers",
        headers=_headers("admin"),
    )
    assert admin_response.status_code == 200
    assert [paper["paper_id"] for paper in admin_response.get_json()["papers"]] == [101]

    finalize_response = client.post(
        "/api/admin/review-papers/101/finalize",
        json={"comment": "Approved for release."},
        headers=_headers("admin"),
    )
    assert finalize_response.status_code == 200
    assert tables["questionpaper"][0]["status"] == "FINALIZED"
    assert tables["questionpaper"][0]["reviewed_by"] == 1
