from src.services.duplicate_detection_service import (
    DuplicateDetectionService
)

service = DuplicateDetectionService()

pairs = [

    (
        "Define communication.",
        "What is meant by communication?"
    ),

    (
        "Define communication.",
        "State the objectives of communication."
    ),

    (
        "Define communication.",
        "Explain the importance of communication."
    ),

    (
        "Define communication.",
        "Explain the scope of communication in industry."
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