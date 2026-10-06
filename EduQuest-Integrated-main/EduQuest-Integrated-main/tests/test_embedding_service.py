from src.services.embedding_service import (
    EmbeddingService
)


def test_embedding_generation():

    service = EmbeddingService()

    embedding = (
        service.generate_embedding(
            "Define communication"
        )
    )

    # Embedding should be generated
    assert embedding is not None

    # all-MiniLM-L6-v2 produces 384 dimensions
    assert len(embedding) == 384

    # Every value should be numeric
    assert all(
        isinstance(value, (int, float))
        for value in embedding
    )