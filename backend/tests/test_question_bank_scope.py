from types import SimpleNamespace

import database


class FakeQuery:
    def __init__(self, rows):
        self.rows = rows

    def select(self, _columns):
        return self

    def eq(self, column, value):
        self.rows = [row for row in self.rows if row.get(column) == value]
        return self

    def ilike(self, column, value):
        expected = value.strip("%").casefold()
        self.rows = [row for row in self.rows if str(row.get(column) or "").casefold() == expected]
        return self

    def in_(self, column, values):
        self.rows = [row for row in self.rows if row.get(column) in values]
        return self

    def execute(self):
        return SimpleNamespace(data=self.rows)


class FakeSupabase:
    def __init__(self):
        self.tables = {
            "subject": [
                {"subject_id": 1, "subject_name": "Advanced Java", "branch": "Computer Technology", "semester": "5"},
                {"subject_id": 2, "subject_name": "Advanced Java", "branch": "Mechanical Engineering", "semester": "5"},
            ],
            "question": [
                {"question_id": 1, "question_text": "Explain JVM.", "subject_id": 1, "question_type": "Short Answer", "difficulty_level": "Easy", "marks": 5},
                {"question_id": 2, "question_text": "Describe JVM.", "subject_id": 1, "question_type": "Short Answer", "difficulty_level": "Easy", "marks": 5},
                {"question_id": 3, "question_text": "Explain another JVM.", "subject_id": 2, "question_type": "Short Answer", "difficulty_level": "Easy", "marks": 5},
            ],
            "canonical_question_mapping": [
                {"canonical_id": 10, "question_id": 1},
                {"canonical_id": 10, "question_id": 2},
                {"canonical_id": 20, "question_id": 3},
            ],
            "canonical_question": [
                {"canonical_id": 10, "canonical_question": "Explain the JVM.", "concept_name": "JVM"},
                {"canonical_id": 20, "canonical_question": "Explain another JVM.", "concept_name": "JVM"},
            ],
            "questionpapermapping": [],
        }

    def table(self, table_name):
        return FakeQuery([dict(row) for row in self.tables[table_name]])


def test_unique_bank_scopes_subject_and_deduplicates_by_canonical_id(monkeypatch):
    monkeypatch.setattr(database, "get_supabase_client", lambda: FakeSupabase())

    questions = database.get_unique_question_bank(
        branch="Computer Technology",
        semester="5",
        subject_id=1,
    )

    assert [question["canonical_id"] for question in questions] == [10]
    assert questions[0]["subject"] == "Advanced Java"
    assert questions[0]["branch"] == "Computer Technology"


def test_unique_bank_subject_id_wins_when_display_name_differs(monkeypatch):
    monkeypatch.setattr(database, "get_supabase_client", lambda: FakeSupabase())

    questions = database.get_unique_question_bank(
        branch="Computer Technology",
        semester="5",
        subject="Advanced Java",
        subject_id=1,
    )

    assert len(questions) == 1
    assert questions[0]["subject"] == "Advanced Java"


def test_question_listing_filters_by_subject_id_before_returning_rows(monkeypatch):
    fake = FakeSupabase()
    fake.tables["questionpapermapping"] = [
        {"question_id": 1, "questionpaper": {}},
        {"question_id": 2, "questionpaper": {}},
        {"question_id": 3, "questionpaper": {}},
    ]
    monkeypatch.setattr(database, "get_supabase_client", lambda: fake)

    questions = database.get_all_questions(subject_id=1, limit=100)

    assert {question["question_id"] for question in questions} == {1, 2}