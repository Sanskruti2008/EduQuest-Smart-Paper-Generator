import pytest

from routes.core import generate_chat_response


@pytest.mark.parametrize(
    ('question', 'expected'),
    [
        ('How does the system work?', 'smart question-paper management system'),
        ('What is this app?', 'smart question-paper management system'),
        ('What can I do here?', 'smart question-paper management system'),
        ('Tell me about this system.', 'smart question-paper management system'),
        ('How does OCR extract questions?', 'Tesseract OCR'),
        ('How do I generate a question paper?', 'Paper Generation'),
        ('How can I make a paper?', 'Faculty Dashboard'),
        ('Where will I find the question bank?', '/question-bank'),
        ('Where can I upload a question paper?', '/ocr-upload'),
        ('Where can I find syllabus analysis?', '/syllabus-analyzer'),
        ('What is RUA?', 'Remember, Understand, and Apply'),
        ('What formats can I export?', 'PDF and DOCX'),
    ],
)
def test_chat_answers_system_questions(question, expected):
    assert expected in generate_chat_response(question)


def test_chat_has_useful_fallback_for_unrecognized_question():
    response = generate_chat_response('Can you explain something unrelated?')

    assert "I don't know the answer" in response
    assert 'Please specify your question' in response
