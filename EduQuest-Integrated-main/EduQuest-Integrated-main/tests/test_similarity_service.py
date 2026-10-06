from src.services.similarity_service import (
    SimilarityService
)

from src.services.embedding_service import (
    EmbeddingService
)


def test_similarity_calculation():

    embedding_service = (
        EmbeddingService()
    )

    text1 = "Define communication."

    text2 = "What is communication?"

    embedding1 = (
        embedding_service
        .generate_embedding(text1)
    )

    embedding2 = (
        embedding_service
        .generate_embedding(text2)
    )

    score = (
        SimilarityService
        .calculate_similarity(
            embedding1,
            embedding2
        )
    )

    # Similarity score should exist
    assert score is not None

    # Cosine similarity should be between 0 and 1
    assert 0.0 <= score <= 1.0

    # These questions are semantically related
    assert score > 0.50