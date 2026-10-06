from src.services.verb_extraction_service import (
    VerbExtractionService
)


def test_verb_extraction():

    test_cases = [

        (
            "Define communication.",
            "define"
        ),

        (
            "Explain communication process.",
            "explain"
        ),

        (
            "List the elements of communication.",
            "list"
        ),

        (
            "Compare oral and written communication.",
            "compare"
        ),

        (
            "Identify communication barriers.",
            "identify"
        )
    ]

    for question, expected_verb in test_cases:

        result = (
            VerbExtractionService.extract(
                question
            )
        )

        assert result == expected_verb