
import os
import tempfile
from unittest.mock import patch

from src.engine.similarity_engine import (
    SimilarityEngine
)


def test_similarity_engine_process_dataset():

    # --------------------------------------
    # Test dataset
    # --------------------------------------

    dataset = {

        "subject":
            "Communication Skills",

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

    # --------------------------------------
    # Fresh ChromaDB
    # --------------------------------------

    test_db_path = tempfile.mkdtemp(
        prefix="eduquest_test_chroma_"
    )

    # --------------------------------------
    # Fresh canonical file
    # --------------------------------------

    test_canonical_file = os.path.join(
        tempfile.gettempdir(),
        "eduquest_test_canonical_questions.json"
    )

    if os.path.exists(
        test_canonical_file
    ):
        os.remove(
            test_canonical_file
        )

    # --------------------------------------
    # Mock Supabase
    #
    # This test checks the similarity pipeline,
    # not the real Supabase database.
    # --------------------------------------

    with patch(
        "src.engine.similarity_engine.SupabaseQuestionRepository"
    ) as mock_repository_class:

        mock_repository = (
            mock_repository_class.return_value
        )

        # --------------------------------------
        # Mock IDs returned by Supabase
        # --------------------------------------

        mock_repository.get_or_create_subject.return_value = 1

        mock_repository.save_question.side_effect = (
            lambda question, subject_id:
            100
        )

        mock_repository.save_canonical.side_effect = (
            lambda canonical_question:
            200
        )

        mock_repository.save_mapping.return_value = 300

        # --------------------------------------
        # Create engine
        # --------------------------------------

        engine = SimilarityEngine(

            db_path=test_db_path,

            canonical_file_path=
                test_canonical_file
        )

        # --------------------------------------
        # Process dataset
        # --------------------------------------

        result = (
            engine.process_dataset(
                dataset
            )
        )

        # --------------------------------------
        # Assertions
        # --------------------------------------

        assert (
            result["subject"]
            == "Communication Skills"
        )

        assert (
            result["processed"]
            == 6
        )

        assert "duplicates" in result

        assert "new_questions" in result

        assert "results" in result

        assert (
            len(result["results"])
            == 6
        )

        # --------------------------------------
        # Validate each processed question
        # --------------------------------------

        for item in result["results"]:

            assert "question" in item

            assert "similarity_score" in item

            assert "is_duplicate" in item

            assert "canonical_id" in item

            assert "canonical_question" in item

        # --------------------------------------
        # Verify Supabase was actually called
        # --------------------------------------

        assert (
            mock_repository.get_or_create_subject.called
        )

        assert (
            mock_repository.save_question.called
        )

        assert (
            mock_repository.save_canonical.called
        )

        assert (
            mock_repository.save_mapping.called
        )

    # --------------------------------------
    # Cleanup
    # --------------------------------------

    if os.path.exists(
        test_canonical_file
    ):
        os.remove(
            test_canonical_file
        )


def test_similarity_engine_get_questions_for_generation():

    # --------------------------------------
    # Prepare controlled Supabase response
    # --------------------------------------

    sample_questions = []

    for i in range(1, 6):

        sample_questions.append({

            "canonical_id":
                i,

            "canonical_question":
                f"Communication Skills Question {i}",

            "question_text":
                f"Communication Skills Question {i}",

            "question":
                f"Communication Skills Question {i}",

            "concept_name":
                None,

            "subject":
                "Communication Skills",

            "question_type":
                "general",

            "difficulty":
                "Medium",

            "marks":
                5,

            "course_outcome":
                None,

            "unit_id":
                None,

            "bloom_level":
                "Understand",

            "rua":
                "U",

            "question_number":
                "",

            "chapter":
                None
        })

    # --------------------------------------
    # Fresh ChromaDB
    # --------------------------------------

    test_db_path = tempfile.mkdtemp(
        prefix="eduquest_test_generation_"
    )

    # --------------------------------------
    # Fresh canonical file
    # --------------------------------------

    test_canonical_file = os.path.join(
        tempfile.gettempdir(),
        "eduquest_test_generation_questions.json"
    )

    if os.path.exists(
        test_canonical_file
    ):
        os.remove(
            test_canonical_file
        )

    # --------------------------------------
    # Mock Supabase repository
    # --------------------------------------

    with patch(
        "src.engine.similarity_engine.SupabaseQuestionRepository"
    ) as mock_repository_class:

        mock_repository = (
            mock_repository_class.return_value
        )

        mock_repository.get_questions_for_generation.return_value = (
            sample_questions
        )

        # --------------------------------------
        # Create engine
        # --------------------------------------

        engine = SimilarityEngine(

            db_path=test_db_path,

            canonical_file_path=
                test_canonical_file
        )

        # --------------------------------------
        # Get questions for paper generation
        # --------------------------------------

        questions = (
            engine.get_questions_for_generation(
                subject="Communication Skills"
            )
        )

        # --------------------------------------
        # Assertions
        # --------------------------------------

        assert isinstance(
            questions,
            list
        )

        assert len(questions) == 5

        for question in questions:

            assert "canonical_id" in question

            assert "canonical_question" in question

            assert "question" in question

            assert "subject" in question

            assert (
                question["subject"]
                == "Communication Skills"
            )

        # --------------------------------------
        # Verify public API passed the subject
        # correctly to the repository
        # --------------------------------------

        mock_repository.get_questions_for_generation.assert_called_once_with(
            subject="Communication Skills"
        )

    # --------------------------------------
    # Cleanup
    # --------------------------------------

    if os.path.exists(
        test_canonical_file
    ):
        os.remove(
            test_canonical_file
        )
