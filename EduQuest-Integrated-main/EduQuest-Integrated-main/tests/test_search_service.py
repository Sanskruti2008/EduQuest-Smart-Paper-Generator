from src.services.search_service import SearchService
from src.services.chroma_service import ChromaService
from src.services.embedding_service import EmbeddingService


def test_search_service():

    chroma_service = ChromaService()

    search_service = SearchService(
        chroma_service
    )

    embedding_service = EmbeddingService()

    embedding = (
        embedding_service
        .generate_embedding(
            "What is communication?"
        )
    )

    results = (
        search_service
        .find_similar_questions(
            embedding=embedding,
            subject="Communication Skills",
            top_k=5
        )
    )

    # --------------------------------------
    # Validate result structure
    # --------------------------------------

    assert "ids" in results
    assert "documents" in results
    assert "distances" in results

    assert isinstance(
        results["ids"],
        list
    )

    assert isinstance(
        results["documents"],
        list
    )

    assert isinstance(
        results["distances"],
        list
    )