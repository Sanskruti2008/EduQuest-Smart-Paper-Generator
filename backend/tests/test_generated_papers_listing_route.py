import sys
from types import SimpleNamespace

from app import create_app
from routes import paper_generation


class FakeQuery:
    def __init__(self, table_name, rows):
        self.table_name = table_name
        self.rows = rows
        self.filters = []
        self.selected = None

    def select(self, columns):
        self.selected = columns
        return self

    def order(self, *_args, **_kwargs):
        return self

    def eq(self, column, value):
        self.filters.append((column, value))
        return self

    def in_(self, column, values):
        self.filters.append((column, tuple(values)))
        return self

    def execute(self):
        rows = self.rows
        for column, value in self.filters:
            if isinstance(value, tuple):
                rows = [row for row in rows if row.get(column) in value]
            else:
                rows = [row for row in rows if row.get(column) == value]
        return SimpleNamespace(data=rows)


class FakeClient:
    def __init__(self):
        self.tables = {
            "papergenerationlog": [{
                "paper_id": 10,
                "generation_id": 20,
                "generated_by": 42,
                "total_questions": 5,
                "total_marks": 20,
                "generated_at": "2026-10-14T12:00:00Z",
            }],
            "questionpaper": [{
                "paper_id": 10,
                "subject_id": 3,
                "exam_type": "University",
                "exam_year": 2026,
                "raw_json": {},
                "created_at": "2026-10-14T12:00:00Z",
            }],
            "subject": [{
                "subject_id": 3,
                "subject_name": "Advanced Java",
                "subject_code": "21526",
                "branch": "Computer Technology",
                "semester": 5,
            }],
            "User": [{
                "user_id": 42,
                "name": "Faculty Member",
                "email": "faculty@example.com",
            }],
        }

    def table(self, name):
        return FakeQuery(name, self.tables[name])


def test_generated_papers_listing_uses_user_table_name(monkeypatch):
    client = FakeClient()
    monkeypatch.setattr(
        "database.get_supabase_admin_client",
        lambda: client,
    )
    monkeypatch.setattr(
        "utils.auth.get_supabase_profile",
        lambda _token: {
            "user_id": 42,
            "role": "faculty",
            "is_active": True,
        },
    )

    app = create_app()
    app.config["TESTING"] = True

    response = app.test_client().get(
        "/api/generated-papers",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    assert response.get_json()["papers"][0]["created_by"] == "Faculty Member"
