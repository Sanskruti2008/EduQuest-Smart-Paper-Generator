import os
import tempfile

from src.engine.similarity_engine import SimilarityEngine


# ============================================================
# TEST DATA
# ============================================================

dataset = {
    "subject": "Communication Skills",

    "questions": [
        {
            "question_text":
                "What is communication?"
        },
        {
            "question_text":
                "Define communication."
        },
        {
            "question_text":
                "Explain the importance of communication."
        },
        {
            "question_text":
                "List the types of communication."
        },
        {
            "question_text":
                "Compare verbal and non-verbal communication."
        },
        {
            "question_text":
                "What are the barriers to communication?"
        }
    ]
}


# ============================================================
# ISOLATED TEST STORAGE
# ============================================================

test_db_path = tempfile.mkdtemp(
    prefix="eduquest_automated_test_chroma_"
)

test_canonical_file = os.path.join(
    tempfile.gettempdir(),
    "eduquest_automated_test_canonical.json"
)

if os.path.exists(test_canonical_file):
    os.remove(test_canonical_file)


# ============================================================
# CREATE ENGINE
# ============================================================

print()
print("======================================")
print("AUTOMATED SIMILARITY TEST")
print("======================================")

engine = SimilarityEngine(
    db_path=test_db_path,
    canonical_file_path=test_canonical_file
)


# ============================================================
# TEST 1
# ============================================================

print()
print("TEST 1: Initial dataset processing")
print("--------------------------------------")

result = engine.process_dataset(dataset)

assert result["processed"] == 6
assert result["duplicates"] == 1
assert result["new_questions"] == 5

print("PASS: Dataset processing")


# ============================================================
# TEST 2
# ============================================================

print()
print("TEST 2: Unique Question Bank")
print("--------------------------------------")

unique_questions = (
    engine.get_unique_questions()
)

assert len(unique_questions) == 5

print(
    f"PASS: {len(unique_questions)} unique questions"
)


# ============================================================
# TEST 3
# ============================================================

print()
print("TEST 3: Canonical IDs")
print("--------------------------------------")

canonical_ids = []

for item in unique_questions:

    canonical_ids.append(
        item["canonical_id"]
    )

expected_ids = [
    "CQ-00001",
    "CQ-00002",
    "CQ-00003",
    "CQ-00004",
    "CQ-00005"
]

assert canonical_ids == expected_ids

print(
    "PASS: Canonical IDs are sequential"
)


# ============================================================
# TEST 4
# DUPLICATE EXCLUSION
# ============================================================

print()
print("TEST 4: Duplicate exclusion")
print("--------------------------------------")

# Read canonical questions directly
# from the repository because the repository
# is the source of truth for canonical records.

canonical_questions = (
    engine.canonical_repository.get_all()
)

assert len(canonical_questions) == 5

canonical_texts = []

for item in canonical_questions:

    canonical_texts.append(
        item["canonical_question"]
    )


assert "Define communication." not in canonical_texts

print(
    "PASS: Duplicate excluded from "
    "canonical repository"
)


# ============================================================
# TEST 5
# EXPECTED CANONICAL QUESTIONS
# ============================================================

print()
print("TEST 5: Canonical questions")
print("--------------------------------------")

expected_questions = [

    "What is communication?",

    "Explain the importance of communication.",

    "List the types of communication.",

    "Compare verbal and non-verbal communication.",

    "What are the barriers to communication?"

]

for question in expected_questions:

    assert question in canonical_texts, (
        f"Missing canonical question: {question}"
    )


print(
    "PASS: All expected canonical "
    "questions are present"
)


# ============================================================
# TEST 6
# REPROCESS SAME DATASET
# ============================================================

print()
print("TEST 6: Reprocessing same dataset")
print("--------------------------------------")

result_again = engine.process_dataset(
    dataset
)

assert result_again["processed"] == 6

assert result_again["duplicates"] == 6

assert result_again["new_questions"] == 0

print(
    "PASS: Reprocessing does not create "
    "additional canonical questions"
)


# ============================================================
# TEST 7
# UNIQUE COUNT STABILITY
# ============================================================

print()
print("TEST 7: Unique count stability")
print("--------------------------------------")

final_count = (
    engine.get_unique_question_count()
)

assert final_count == 5

print(
    "PASS: Unique count remains 5"
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print()
print("======================================")
print("AUTOMATED TEST SUMMARY")
print("======================================")

print("TEST 1  : PASS")
print("TEST 2  : PASS")
print("TEST 3  : PASS")
print("TEST 4  : PASS")
print("TEST 5  : PASS")
print("TEST 6  : PASS")
print("TEST 7  : PASS")

print()
print("ALL AUTOMATED TESTS PASSED")
print("======================================")