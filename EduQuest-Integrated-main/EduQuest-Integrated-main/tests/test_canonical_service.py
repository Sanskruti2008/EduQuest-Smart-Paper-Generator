from src.services.canonical_service import (
    CanonicalService
)

from src.services.canonical_repository import (
    CanonicalRepository
)


def test_canonical_service():

    repository = CanonicalRepository(
        "data/test_canonical_service.json"
    )

    repository.clear()

    service = CanonicalService(
        repository
    )

    # ------------------------------------------
    # Duplicate threshold tests
    # ------------------------------------------

    assert (
        service.is_duplicate(0.43)
        is True
    )

    assert (
        service.is_duplicate(0.75)
        is False
    )

    # ------------------------------------------
    # Create canonical
    # ------------------------------------------

    result = service.create_canonical(
        question=
            "Define communication",
        subject=
            "Communication Skills"
    )

    assert (
        result["canonical_id"]
        == "CQ-00001"
    )

    assert (
        result["canonical_question"]
        == "Define communication"
    )

    # ------------------------------------------
    # Get canonical
    # ------------------------------------------

    canonical = service.get_canonical(
        "CQ-00001"
    )

    assert canonical is not None

    assert (
        canonical["subject"]
        == "Communication Skills"
    )

    # ------------------------------------------
    # Count
    # ------------------------------------------

    assert (
        service.count_canonicals()
        == 1
    )