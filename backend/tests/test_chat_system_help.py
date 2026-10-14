import pytest

from routes.core import generate_chat_response


@pytest.mark.parametrize(
    ('question', 'expected'),
    [
        ('How does the system work?', 'smart question-paper management system'),
        ('How does OCR extract questions?', 'Tesseract OCR'),
        ('How do I generate a question paper?', 'Paper Generation'),
        ('What is RUA?', 'Remember, Understand, and Apply'),
        ('What formats can I export?', 'PDF and DOCX'),
    ],
)
def test_chat_answers_system_questions(question, expected):
    assert expected in generate_chat_response(question)


def test_chat_has_useful_fallback_for_unrecognized_question():
    response = generate_chat_response('Can you explain something unrelated?')

    assert 'paper generation' in response
    assert 'similarity detection' in response
