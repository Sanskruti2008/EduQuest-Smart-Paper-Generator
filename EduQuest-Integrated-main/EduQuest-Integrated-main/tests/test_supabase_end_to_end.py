import os
import tempfile

from src.engine.similarity_engine import SimilarityEngine
from src.repositories.supabase_question_repository import (
    SupabaseQuestionRepository
)


def test_supabase_end_to_end():

    print("\n")
    print("=" * 60)
    print("SUPABASE END-TO-END INTEGRATION TEST")
    print("=" * 60)

    # --------------------------------------------------
    # 1. Small test dataset
    # --------------------------------------------------

    dataset = {

        "subject": "Communication Skills",

        "questions": [

            {
                "question_text":
                    "What is effective communication?"
            },

            {
                "question_text":
                    "Explain the importance of effective communication."
            },

            {
                "question_text":
                    "List the barriers to communication."
            }

        ]
    }

    # --------------------------------------------------
    # 2. Fresh ChromaDB
    # --------------------------------------------------

    test_db_path = tempfile.mkdtemp(
        prefix="eduquest_supabase_e2e_"
    )

    # --------------------------------------------------
    # 3. Fresh canonical repository
    # --------------------------------------------------

    test_canonical_file = os.path.join(
        tempfile.gettempdir(),
        "eduquest_supabase_e2e_canonical.json"
    )

    if os.path.exists(test_canonical_file):
        os.remove(test_canonical_file)

    # --------------------------------------------------
    # 4. Create Similarity Engine
    # --------------------------------------------------

    print("\n[1] Creating Similarity Engine...")

    engine = SimilarityEngine(
        db_path=test_db_path,
        canonical_file_path=test_canonical_file
    )

    # --------------------------------------------------
    # 5. Process dataset
    # --------------------------------------------------

    print("\n[2] Processing dataset...")

    result = engine.process_dataset(dataset)

    print("\nDataset processing completed.")

    # --------------------------------------------------
    # 6. Basic engine verification
    # --------------------------------------------------

    assert result is not None

    # --------------------------------------------------
    # 7. Create Supabase repository
    # --------------------------------------------------

    print("\n[3] Connecting to Supabase...")

    repository = SupabaseQuestionRepository()

    # --------------------------------------------------
    # 8. Retrieve questions
    # --------------------------------------------------

    print("\n[4] Retrieving from Supabase...")

    questions = (
        repository
        .get_questions_for_generation(
            subject="Communication Skills"
        )
    )

    # --------------------------------------------------
    # 9. Verify retrieval
    # --------------------------------------------------

    print(
        f"\nQuestions retrieved: {len(questions)}"
    )

    assert isinstance(
        questions,
        list
    )

    assert len(questions) >= 3

    # --------------------------------------------------
    # 10. Verify required fields
    # --------------------------------------------------

    required_fields = [

        "canonical_id",
        "canonical_question",
        "question",
        "question_text",
        "subject",
        "question_type",
        "difficulty",
        "marks",
        "rua",
        "bloom_level"
    ]

    for question in questions:

        print("\nRetrieved question:")
        print(question)

        for field in required_fields:

            assert field in question, (
                f"Missing field: {field}"
            )

    # --------------------------------------------------
    # 11. Verify subject isolation
    # --------------------------------------------------

    for question in questions:

        assert (
            question["subject"]
            == "Communication Skills"
        )

    print("\n")
    print("=" * 60)
    print("SUPABASE END-TO-END TEST PASSED")
    print("=" * 60)