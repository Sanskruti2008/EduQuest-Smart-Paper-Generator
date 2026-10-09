from copy import deepcopy
from types import SimpleNamespace

from app import create_app
from routes import core as core_route
from routes import faculty as faculty_route
from utils import auth as auth_utils


class FakeQuery:
    def __init__(self, client, table):
        self.client = client
        self.table_name = table
        self.action = "select"
        self.filters = []
        self.payload = None

    def select(self, _fields):
        self.action = "select"
        return self

    def insert(self, payload):
        self.action = "insert"
        self.payload = payload
        return self

    def update(self, payload):
        self.action = "update"
        self.payload = payload
        return self

    def eq(self, field, value):
        self.filters.append(("eq", field, value))
        return self

    def in_(self, field, values):
        self.filters.append(("in", field, values))
        return self

    def order(self, _field):
        return self

    def limit(self, _count):
        return self

    def execute(self):
        rows = self.client.tables[self.table_name]
        if self.action == "insert":
            if self.table_name == "User" and self.client.fail_profile_insert:
                raise RuntimeError("private database error")
            inserted = deepcopy(self.payload)
            if self.table_name == "User":
                inserted["user_id"] = self.client.next_user_id
                self.client.next_user_id += 1
            rows.append(inserted)
            return SimpleNamespace(data=[deepcopy(inserted)])

        matching = [
            row for row in rows
            if all(
                (row.get(field) == value if kind == "eq" else row.get(field) in value)
                for kind, field, value in self.filters
            )
        ]
        if self.action == "update":
            for row in matching:
                row.update(self.payload)
            return SimpleNamespace(data=deepcopy(matching))
        return SimpleNamespace(data=deepcopy(matching))


class FakeAuthAdmin:
    def __init__(self):
        self.created = []
        self.deleted = []

    def create_user(self, attributes):
        self.created.append(attributes)
        return SimpleNamespace(user=SimpleNamespace(id="auth-faculty-uuid"))

    def delete_user(self, user_id):
        self.deleted.append(user_id)


class FakeSupabaseClient:
    def __init__(self):
        self.tables = {
            "User": [],
            "subject": [{"subject_id": 7, "subject_name": "Web Development"}],
            "faculty_subject_assignment": [],
        }
        self.auth = SimpleNamespace(admin=FakeAuthAdmin())
        self.fail_profile_insert = False
        self.next_user_id = 12

    def table(self, name):
        return FakeQuery(self, name)


ADMIN_PROFILE = {
    "user_id": 1,
    "auth_user_id": "auth-admin-uuid",
    "role": "admin",
    "is_active": True,
}


def _client(monkeypatch, profile=ADMIN_PROFILE):
    app = create_app()
    app.config["TESTING"] = True
    supabase = FakeSupabaseClient()
    monkeypatch.setattr(faculty_route.db, "get_supabase_admin_client", lambda: supabase)
    monkeypatch.setattr(auth_utils, "get_supabase_profile", lambda _token: profile)
    return app.test_client(), supabase


def _auth_headers():
    return {"Authorization": "Bearer test-supabase-access-token"}


def _faculty_payload():
    return {
        "name": "Tejashree Pawar",
        "employee_id": "FAC001",
        "email": "tejashree.pawar@eduquest.ai",
        "department": "Computer Technology",
        "password": "temporary-password",
        "is_active": True,
    }


def test_create_faculty_auth_user_and_profile(monkeypatch):
    client, supabase = _client(monkeypatch)

    response = client.post(
        "/api/admin/faculty", json=_faculty_payload(), headers=_auth_headers()
    )

    assert response.status_code == 201
    assert response.get_json()["faculty"]["role"] == "faculty"
    assert response.get_json()["faculty"]["auth_user_id"] == "auth-faculty-uuid"
    assert supabase.auth.admin.created[0]["email"] == "tejashree.pawar@eduquest.ai"
    assert supabase.auth.admin.created[0]["email_confirm"] is True
    profile = supabase.tables["User"][0]
    assert profile["role"] == "faculty"
    assert profile["is_active"] is True
    assert profile["auth_user_id"] == "auth-faculty-uuid"


def test_create_faculty_rolls_back_auth_user_after_profile_failure(monkeypatch):
    client, supabase = _client(monkeypatch)
    supabase.fail_profile_insert = True

    response = client.post(
        "/api/admin/faculty", json=_faculty_payload(), headers=_auth_headers()
    )

    assert response.status_code == 500
    assert response.get_json()["message"] == "Unable to create faculty account."
    assert response.get_json()["message"] != "private database error"
    assert supabase.auth.admin.deleted == ["auth-faculty-uuid"]


def test_create_faculty_rejects_invalid_and_duplicate_data(monkeypatch):
    client, supabase = _client(monkeypatch)
    invalid_response = client.post(
        "/api/admin/faculty",
        json={**_faculty_payload(), "password": "short"},
        headers=_auth_headers(),
    )
    assert invalid_response.status_code == 400
    assert "password" in invalid_response.get_json()["errors"]
    assert not supabase.auth.admin.created

    supabase.tables["User"].append(
        {"user_id": 5, "email": "TEJASHREE.PAWAR@EDUQUEST.AI", "employee_id": "FAC005"}
    )
    duplicate_response = client.post(
        "/api/admin/faculty", json=_faculty_payload(), headers=_auth_headers()
    )
    assert duplicate_response.status_code == 409
    assert "email" in duplicate_response.get_json()["errors"]
    assert not supabase.auth.admin.created


def test_faculty_list_includes_only_faculty_and_active_assignment_counts(monkeypatch):
    client, supabase = _client(monkeypatch)
    supabase.tables["User"] = [
        {"user_id": 1, "role": "admin", "is_active": True},
        {
            "user_id": 12,
            "auth_user_id": "faculty-12",
            "name": "Active Faculty",
            "role": "faculty",
            "email": "active@example.test",
            "employee_id": "FAC012",
            "department": "Computer Technology",
            "is_active": True,
        },
        {
            "user_id": 13,
            "name": "Inactive Faculty",
            "role": "faculty",
            "email": "inactive@example.test",
            "employee_id": "FAC013",
            "department": "Computer Technology",
            "is_active": False,
        },
    ]
    supabase.tables["faculty_subject_assignment"] = [
        {"faculty_id": 12, "subject_id": 7, "is_active": True},
        {"faculty_id": 12, "subject_id": 8, "is_active": False},
        {"faculty_id": 13, "subject_id": 7, "is_active": True},
    ]

    response = client.get("/api/admin/faculty", headers=_auth_headers())

    assert response.status_code == 200
    faculty = response.get_json()["faculty"]
    assert [record["user_id"] for record in faculty] == [12, 13]
    assert faculty[0]["assigned_subjects_count"] == 1
    assert faculty[0]["assigned_subject_ids"] == [7]
    assert faculty[1]["is_active"] is False


def test_faculty_routes_require_supabase_admin_profile(monkeypatch):
    client, _supabase = _client(monkeypatch, profile=None)

    response = client.get("/api/admin/faculty", headers=_auth_headers())

    assert response.status_code == 401
    faculty_client, _supabase = _client(
        monkeypatch, profile={"user_id": 2, "role": "faculty", "is_active": True}
    )
    forbidden = faculty_client.get(
        "/api/admin/faculty", headers=_auth_headers()
    )
    assert forbidden.status_code == 403


def test_update_faculty_status_and_reject_role_changes(monkeypatch):
    client, supabase = _client(monkeypatch)
    supabase.tables["User"].append(
        {
            "user_id": 12,
            "auth_user_id": "faculty-12",
            "name": "Active Faculty",
            "role": "faculty",
            "email": "active@example.test",
            "employee_id": "FAC012",
            "department": "Computer Technology",
            "is_active": True,
        }
    )
    forbidden = client.patch(
        "/api/admin/faculty/12",
        json={"role": "admin"},
        headers=_auth_headers(),
    )
    assert forbidden.status_code == 400

    response = client.patch(
        "/api/admin/faculty/12",
        json={"is_active": False},
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    assert response.get_json()["faculty"]["role"] == "faculty"
    assert response.get_json()["faculty"]["is_active"] is False


def test_assignment_reactivates_inactive_row_and_uses_authenticated_admin(monkeypatch):
    client, supabase = _client(monkeypatch)
    supabase.tables["User"].append(
        {"user_id": 12, "role": "faculty", "is_active": True}
    )
    supabase.tables["faculty_subject_assignment"].append(
        {
            "faculty_id": 12,
            "subject_id": 7,
            "assigned_by": 4,
            "assigned_at": "2026-01-01T00:00:00+00:00",
            "is_active": False,
        }
    )

    response = client.post(
        "/api/admin/faculty/12/subjects",
        json={"subject_id": 7},
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    assignment = supabase.tables["faculty_subject_assignment"][0]
    assert assignment["is_active"] is True
    assert assignment["assigned_by"] == ADMIN_PROFILE["user_id"]


def test_inactive_faculty_cannot_receive_subject_assignment(monkeypatch):
    client, supabase = _client(monkeypatch)
    supabase.tables["User"].append(
        {"user_id": 12, "role": "faculty", "is_active": False}
    )

    response = client.post(
        "/api/admin/faculty/12/subjects",
        json={"subject_id": 7},
        headers=_auth_headers(),
    )

    assert response.status_code == 404
    assert not supabase.tables["faculty_subject_assignment"]


def test_admin_login_uses_supabase_access_token(monkeypatch):
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    sign_in_calls = []

    class FakePasswordAuth:
        def sign_in_with_password(self, credentials):
            sign_in_calls.append(credentials)
            return SimpleNamespace(
                session=SimpleNamespace(access_token="verified-access-token")
            )

    monkeypatch.setattr(
        core_route.db,
        "create_supabase_auth_client",
        lambda: SimpleNamespace(auth=FakePasswordAuth()),
    )
    monkeypatch.setattr(
        core_route, "get_supabase_profile", lambda _token: ADMIN_PROFILE
    )

    response = client.post(
        "/api/admin/login",
        json={"username": "admin@eduquest.ai", "password": "valid-password"},
    )

    assert response.status_code == 200
    assert response.get_json()["token"] == "verified-access-token"
    assert sign_in_calls == [
        {"email": "admin@eduquest.ai", "password": "valid-password"}
    ]
