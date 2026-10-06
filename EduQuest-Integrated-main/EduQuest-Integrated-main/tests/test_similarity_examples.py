from src.services.duplicate_detection_service import (
    DuplicateDetectionService
)

service = DuplicateDetectionService()

pairs = [

    (
        "Define communication.",
        "What is communication?"
    ),

    (
        "Define communication.",
        "State the meaning of communication."
    ),

    (
        "Define communication.",
        "Explain communication in brief."
    )

]

for q1, q2 in pairs:

    result = service.is_duplicate(
        q1,
        q2
    )

    print("\n")
    print(q1)
    print(q2)
    print(result)