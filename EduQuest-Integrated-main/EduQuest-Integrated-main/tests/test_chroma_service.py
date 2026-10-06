from src.services.chroma_service import (
    ChromaService
)

from src.services.embedding_service import (
    EmbeddingService
)


def test_chroma_service():

    chroma = ChromaService(
        db_path="./test_chroma_service_db"
    )

    embedding_service = (
        EmbeddingService()
    )

    subject = "Communication Skills"

    # ------------------------------------------
    # Count questions
    # ------------------------------------------

    initial_count = (
        chroma.count_questions(
            subject
        )
    )

    assert initial_count >= 0

    # ------------------------------------------
    # Generate embedding
    # ------------------------------------------

    query = "Define communication."

    embedding = (
        embedding_service
        .generate_embedding(
            query
        )
    )

    assert embedding is not None

    assert len(embedding) == 384

    # ------------------------------------------
    # Search similar questions
    # ------------------------------------------

    results = (
        chroma.search_similar(
            embedding=embedding,
            subject=subject,
            top_k=5
        )
    )

    assert "ids" in results

    assert "documents" in results

    assert "distances" in results