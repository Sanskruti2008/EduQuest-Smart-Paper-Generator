from src.services.embedding_service import (
    EmbeddingService
)

from src.services.chroma_service import (
    ChromaService
)

from src.services.canonical_service import (
    CanonicalService
)

from src.services.canonical_repository import (
    CanonicalRepository
)


class QuestionIngestionPipeline:

    def __init__(
        self,
        db_path="./chroma_db",
        canonical_file_path="data/canonical_questions.json"
    ):

        self.embedding_service = (
            EmbeddingService()
        )

        self.chroma_service = (
            ChromaService(
                db_path=db_path
            )
        )

        self.canonical_repository = (
            CanonicalRepository(
                file_path=canonical_file_path
            )
        )

        self.canonical_service = (
            CanonicalService(
                self.canonical_repository
            )
        )

    def process_question(
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
            self.chroma_service
            .search_similar(
                embedding=embedding,
                subject=subject,
                top_k=5
            )
        )

        return {
            "question": question_text,
            "embedding_length": len(embedding),
            "search_results": results
        }