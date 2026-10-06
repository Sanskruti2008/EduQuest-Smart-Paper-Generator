import os

from src.services.canonical_repository import (
    CanonicalRepository
)


def test_canonical_repository():

    test_file = (
        "data/test_canonical_questions.json"
    )

    # ------------------------------------------
    # Create repository
    # ------------------------------------------

    repo = CanonicalRepository(
        test_file
    )

    # ------------------------------------------
    # Start with clean repository
    # ------------------------------------------

    repo.clear()

    # ------------------------------------------
    # Add canonical question
    # ------------------------------------------

    result = repo.add_canonical(
        canonical_question=
            "Define communication",
        subject=
            "Communication Skills"
    )

    # ------------------------------------------
    # Verify canonical ID
    # ------------------------------------------

    assert (
        result["canonical_id"]
        == "CQ-00001"
    )

    # ------------------------------------------
    # Verify question
    # ------------------------------------------

    assert (
        result["canonical_question"]
        == "Define communication"
    )

    # ------------------------------------------
    # Verify subject
    # ------------------------------------------

    assert (
        result["subject"]
        == "Communication Skills"
    )

    # ------------------------------------------
    # Retrieve all
    # ------------------------------------------

    data = repo.get_all()

    assert len(data) == 1

    # ------------------------------------------
    # Retrieve by ID
    # ------------------------------------------

    found = repo.get_by_id(
        "CQ-00001"
    )

    assert found is not None

    assert (
        found["canonical_question"]
        == "Define communication"
    )

    # ------------------------------------------
    # Find by question
    # ------------------------------------------

    found = repo.find_by_question(
        "Define communication."
    )

    assert found is not None

    assert (
        found["canonical_id"]
        == "CQ-00001"
    )

    # ------------------------------------------
    # Count
    # ------------------------------------------

    assert repo.count() == 1

    # ------------------------------------------
    # Cleanup
    # ------------------------------------------

    if os.path.exists(test_file):

        os.remove(test_file)