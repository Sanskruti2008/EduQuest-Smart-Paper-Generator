from src.services.chroma_service import (
    ChromaService
)


class SearchService:

    def __init__(
        self,
        chroma_service: ChromaService
    ):

        self.chroma_service = (
            chroma_service
        )

    # ==================================================
    # FIND SIMILAR QUESTIONS
    # ==================================================

    def find_similar_questions(
        self,
        embedding,
        subject,
        top_k=5
    ):

        return (
            self.chroma_service
            .search_similar(
                embedding=embedding,
                subject=subject,
                top_k=top_k
            )
        )