from src.models.question import Question

question = Question(
    question_id="Q001",
    text="Define communication.",
    subject="Communication Skills",
    department="Computer",
    semester=3,
    unit="Unit-I",
    concept="Communication",
    marks=2,
    difficulty="Easy",
    rua="R"
)

print(question)