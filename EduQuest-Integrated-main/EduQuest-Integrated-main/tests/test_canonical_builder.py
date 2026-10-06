from src.services.canonical_builder_service import (
    CanonicalBuilderService
)


def test_canonical_builder():

    questions = [

        "What is communication?",

        "Define communication.",

        "Explain the importance of communication.",

        "List the types of communication.",

        "Compare verbal and non-verbal communication."
    ]

    builder = CanonicalBuilderService()

    canonicals = builder.build(questions)

    assert canonicals is not None

    assert isinstance(canonicals, list)

    assert len(canonicals) > 0

    for canonical in canonicals:

        assert "canonical_id" in canonical

        assert "canonical_question" in canonical