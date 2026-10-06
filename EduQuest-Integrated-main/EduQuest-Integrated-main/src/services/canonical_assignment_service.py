from src.services.search_service import SearchService
from src.services.chroma_service import ChromaService
from src.services.embedding_service import EmbeddingService


class CanonicalAssignmentService:

    def __init__(
        self,
        search_service=None,
        embedding_service=None
    ):

        if embedding_service is None:
            embedding_service = EmbeddingService()

        if search_service is None:
            chroma_service = ChromaService()

            search_service = SearchService(
                chroma_service
            )

        self.embedding_service = embedding_service
        self.search_service = search_service

    def assign(
        self,
        question_text,
        subject
    ):

        embedding = (
            self.embedding_service
            .generate_embedding(
                question_text
            )
        )

        results = (
            self.search_service
            .find_similar_questions(
                embedding=embedding,
                subject=subject,
                top_k=1
            )
        )

        documents = (
            results
            .get("documents", [[]])[0]
        )

        distances = (
            results
            .get("distances", [[]])[0]
        )

        if not documents:

            return {
                "is_duplicate": False,
                "matched_question": None,
                "distance": None,
                "canonical_id": None
            }

        best_match = documents[0]
        distance = distances[0]

        if distance <= 0.45:

            return {
                "is_duplicate": True,
                "matched_question": best_match,
                "distance": distance,
                "canonical_id": None
            }

        return {
            "is_duplicate": False,
            "matched_question": None,
            "distance": distance,
            "canonical_id": None
        }