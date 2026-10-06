from src.services.chroma_service import (
    ChromaService
)


def test_metadata():

    chroma = ChromaService()

    collection = chroma.get_collection(
        "Communication Skills"
    )

    results = collection.get(
        limit=1,
        include=[
            "metadatas",
            "documents"
        ]
    )

    # --------------------------------------------------
    # If collection is empty
    # --------------------------------------------------

    if len(results["ids"]) == 0:

        print(
            "No questions found in collection."
        )

        return

    print(
        "Question:"
    )

    print(
        results["documents"][0]
    )

    print(
        "\nMetadata:"
    )

    print(
        results["metadatas"][0]
    )

    assert (
        results["documents"][0]
        is not None
    )