from src.repositories.supabase_question_repository import SupabaseQuestionRepository


def test_subject_resolution_accepts_advanced_java_alias():
    assert (
        SupabaseQuestionRepository._normalize_subject_name("Advanced Java")
        == SupabaseQuestionRepository._normalize_subject_name("Advance Java")
    )


def test_subject_resolution_is_case_and_punctuation_insensitive():
    assert (
        SupabaseQuestionRepository._normalize_subject_name(
            "  Advanced-Java "
        )
        == "advance java"
    )
