from types import SimpleNamespace

from paper_generation.services.paper_generation_service import (
    PaperGenerationService,
)


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    def __init__(self, client, table_name):
        self.client = client
        self.table_name = table_name
        self.operation = None
        self.filters = {}
        self.records = None

    def select(self, _columns):
        self.operation = "select"
        return self

    def in_(self, column, values):
        self.filters[column] = set(values)
        return self

    def eq(self, column, value):
        self.filters[column] = value
        return self

    def ilike(self, column, value):
        self.filters[column] = ("ilike", value.casefold())
        return self

    def insert(self, records):
        self.operation = "insert"
        self.records = records
        return self

    def execute(self):
        if self.table_name == "questionusagehistory":
            if self.operation == "select":
                if self.client.fail_usage_reads:
                    raise RuntimeError("usage history unavailable")
                ids = self.filters.get("question_id")
                rows = self.client.usage_history
                if ids is not None:
                    rows = [
                        row for row in rows
                        if row["question_id"] in ids
                    ]
                return FakeResponse(list(rows))

        if self.table_name == "subject":
            rows = [
                row for row in self.client.subjects
                if all(
                    row.get(key, "").casefold() == value[1]
                    if isinstance(value, tuple) and value[0] == "ilike"
                    else row.get(key) == value
                    for key, value in self.filters.items()
                )
            ]
            return FakeResponse(rows)

        if self.table_name == "question":
            ids = self.filters.get("question_id", set())
            return FakeResponse([
                {"question_id": question_id}
                for question_id in ids
                if question_id in self.client.question_ids
            ])

        raise AssertionError(f"Unexpected table: {self.table_name}")


class FakeRPC:
    def __init__(self, client, params):
        self.client = client
        self.params = params

    def execute(self):
        if self.client.fail_atomic_persistence:
            raise RuntimeError("atomic persistence unavailable")

        question_ids = self.params["p_question_ids"]
        if len(question_ids) != len(set(question_ids)):
            raise RuntimeError("duplicate question IDs")
        if not set(question_ids).issubset(self.client.question_ids):
            raise RuntimeError("unknown question IDs")

        paper_id = self.client.next_paper_id
        generation_id = self.client.next_generation_id
        generation_log = self.params["p_generation_log"]
        paper = {
            "paper_id": paper_id,
            "subject_id": self.params["p_subject_id"],
            "exam_type": self.params["p_exam_type"],
            "exam_year": self.params["p_exam_year"],
            "raw_json": self.params["p_raw_json"],
        }
        mappings = [
            {"paper_id": paper_id, "question_id": question_id}
            for question_id in question_ids
        ]
        usages = [dict(record) for record in mappings]
        log = {
            **generation_log,
            "generation_id": generation_id,
            "paper_id": paper_id,
        }

        self.client.papers.append(paper)
        self.client.question_paper_mappings.extend(mappings)
        self.client.usage_history.extend(usages)
        self.client.generation_logs.append(log)
        self.client.next_paper_id += 1
        self.client.next_generation_id += 1

        return FakeResponse({
            "paper_id": paper_id,
            "generation_id": generation_id,
            "paper_records": 1,
            "mapped_questions": len(mappings),
            "usage_records": len(usages),
            "generation_log_records": 1,
        })


class FakeClient:
    def __init__(self, questions):
        self.usage_history = []
        self.question_paper_mappings = []
        self.papers = []
        self.generation_logs = []
        self.question_ids = {question["question_id"] for question in questions}
        self.subjects = [{"subject_id": 1, "subject_name": "Operating Systems"}]
        self.next_paper_id = 1
        self.next_generation_id = 1
        self.fail_usage_reads = False
        self.fail_atomic_persistence = False

    def table(self, table_name):
        return FakeQuery(self, table_name)

    def rpc(self, _function_name, params):
        return FakeRPC(self, params)


class FakeSimilarityEngine:
    def __init__(self, questions, client):
        self.questions = questions
        self.supabase_repository = SimpleNamespace(client=client)

    def get_questions_for_generation(self, **_filters):
        return [dict(question) for question in self.questions]


def _blueprint():
    return {
        "paper_information": {
            "subject": "Operating Systems",
            "attempted_total_marks": 70,
        },
        "question_pattern": {
            "Section A": {
                "marks_per_question": 2,
                "questions_to_generate": 7,
                "questions_to_attempt": 5,
            },
            "Section B": {
                "marks_per_question": 4,
                "questions_to_generate": 20,
                "questions_to_attempt": 15,
            },
        },
        "requirements": {
            "selected_units": ["Unit-I"],
            "rua_allocation": {"Unit-I": {"R": 94, "U": 0, "A": 0}},
            "difficulty_allocation": {"Easy": 94},
            "co_requirements": ["CO1"],
        },
    }


def test_persistence_resolves_subject_by_code_and_context_when_name_differs():
    service, client = _service()
    client.subjects = [{
        "subject_id": 2,
        "subject_name": "Advance Java",
        "subject_code": "233117",
        "branch": "Computer Technology",
        "semester": "5",
    }]
    blueprint = _blueprint()
    blueprint["paper_information"].update({
        "subject": "Advanced Java",
        "subject_code": "233117",
        "branch": "Computer Technology",
        "semester": 5,
    })

    result = service.generate(blueprint, "Operating Systems", persist=True)

    assert result["persistence"]["subject_id"] == 2
    assert len(client.papers) == 1


def test_persistence_falls_back_to_subject_name_with_matching_context():
    service, client = _service()
    client.subjects = [{
        "subject_id": 3,
        "subject_name": "Advanced Java",
        "subject_code": "233117",
        "branch": "Computer Engineering",
        "semester": "5",
    }]
    blueprint = _blueprint()
    blueprint["paper_information"].update({
        "subject": "Advanced Java",
        "subject_code": "ADVANCEDJAVA",
        "branch": "Computer Engineering",
        "semester": 5,
    })

    result = service.generate(blueprint, "Operating Systems", persist=True)

    assert result["persistence"]["subject_id"] == 3
    assert len(client.papers) == 1


def _questions():
    questions = []
    for marks, count in ((2, 50), (4, 50)):
        for index in range(count):
            identifier = f"{marks}-{index}"
            questions.append({
                "canonical_id": f"CAN_{identifier}",
                "question_id": f"DB_{identifier}",
                "question_text": f"Question {identifier}",
                "unit": "Unit-I",
                "marks": marks,
                "rua": "R",
                "difficulty": "Easy",
                "course_outcome": "CO1",
                "subject": "Operating Systems",
            })
    return questions


def _service():
    questions = _questions()
    client = FakeClient(questions)
    service = PaperGenerationService(
        FakeSimilarityEngine(questions, client)
    )
    return service, client


def _selected_questions(result):
    return [
        question
        for section in result["selection"]["sections"].values()
        for question in section["questions"]
    ]


def _assert_blueprint_valid(service, result):
    selected = _selected_questions(result)
    service.selection_service.validate_selection(
        result["selection"],
        _blueprint(),
    )
    assert len(selected) == 27
    assert sum(question["marks"] for question in selected) == 94


def test_first_generation_and_empty_usage_history_succeed_and_persist_27_records():
    service, client = _service()

    result = service.generate(_blueprint(), "Operating Systems", persist=True)

    _assert_blueprint_valid(service, result)
    assert len(client.papers) == 1
    assert len(client.question_paper_mappings) == 27
    assert result["persistence"]["usage_records"] == 27
    assert len(client.usage_history) == 27
    assert len(client.generation_logs) == 1
    assert client.generation_logs[0]["total_questions"] == 27
    assert client.generation_logs[0]["total_marks"] == 94
    assert client.generation_logs[0]["generated_at"]
    assert all(question.get("question_id") for question in _selected_questions(result))
    assert all(question["_usage_count"] == 0 for question in _selected_questions(result))


def test_second_persisted_generation_prefers_fresh_questions_and_stays_valid():
    service, client = _service()

    first = service.generate(_blueprint(), "Operating Systems", persist=True)
    first_ids = {
        question["canonical_id"] for question in _selected_questions(first)
    }
    second = service.generate(_blueprint(), "Operating Systems", persist=True)
    second_questions = _selected_questions(second)
    second_ids = {question["canonical_id"] for question in second_questions}

    _assert_blueprint_valid(service, first)
    _assert_blueprint_valid(service, second)
    assert first_ids.isdisjoint(second_ids)
    assert all(question["_usage_count"] == 0 for question in second_questions)
    assert len(client.usage_history) == 54
    assert len(client.papers) == 2
    assert len(client.question_paper_mappings) == 54
    assert len(client.generation_logs) == 2
    assert first["persistence"]["usage_records"] == 27
    assert second["persistence"]["usage_records"] == 27


def test_equal_usage_counts_still_produce_diverse_valid_selections():
    service, client = _service()
    client.usage_history = [
        {"paper_id": 1, "question_id": question["question_id"]}
        for question in _questions()
    ]

    selected_papers = []
    for _ in range(5):
        result = service.generate(_blueprint(), "Operating Systems")
        _assert_blueprint_valid(service, result)
        selected_papers.append(tuple(sorted(
            question["canonical_id"]
            for question in _selected_questions(result)
        )))

    assert len(set(selected_papers)) > 1


def test_usage_history_read_failure_falls_back_to_zero_counts():
    service, client = _service()
    client.fail_usage_reads = True

    result = service.generate(_blueprint(), "Operating Systems")

    _assert_blueprint_valid(service, result)
    assert all(question["_usage_count"] == 0 for question in _selected_questions(result))


def test_missing_question_id_fails_before_any_persistence_write():
    service, client = _service()
    result = service.generate(_blueprint(), "Operating Systems")
    selection = result["selection"]
    selected = _selected_questions(result)
    selected[0].pop("question_id")

    try:
        service.persistence_service.save_generated_paper(
            _blueprint(),
            selection,
        )
    except ValueError as error:
        assert "PERSISTENCE_ERROR" in str(error)
        assert selected[0]["canonical_id"] in str(error)
    else:
        raise AssertionError("Missing question_id must fail persistence")

    assert client.papers == []
    assert client.question_paper_mappings == []
    assert client.usage_history == []
    assert client.generation_logs == []


def test_unresolved_question_id_fails_before_any_persistence_write():
    service, client = _service()
    result = service.generate(_blueprint(), "Operating Systems")
    selection = result["selection"]
    selected = _selected_questions(result)
    selected[0]["question_id"] = "not-in-database"

    try:
        service.persistence_service.save_generated_paper(
            _blueprint(),
            selection,
        )
    except ValueError as error:
        assert "PERSISTENCE_ERROR" in str(error)
        assert "not-in-database" in str(error)
    else:
        raise AssertionError("Unresolved question_id must fail persistence")

    assert client.papers == []
    assert client.question_paper_mappings == []
    assert client.usage_history == []
    assert client.generation_logs == []


def test_atomic_persistence_failure_leaves_no_partial_rows():
    service, client = _service()
    result = service.generate(_blueprint(), "Operating Systems")
    client.fail_atomic_persistence = True

    try:
        service.persistence_service.save_generated_paper(
            _blueprint(),
            result["selection"],
        )
    except RuntimeError as error:
        assert "PERSISTENCE_ERROR" in str(error)
    else:
        raise AssertionError("Persistence RPC failure must fail generation")

    assert client.papers == []
    assert client.question_paper_mappings == []
    assert client.usage_history == []
    assert client.generation_logs == []
