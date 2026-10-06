from src.services.embedding_service import (
    EmbeddingService
)

from src.services.similarity_service import (
    SimilarityService
)

from src.services.verb_extraction_service import (
    VerbExtractionService
)

from src.services.question_feature_service import (
    QuestionFeatureService
)


class DuplicateDetectionService:

    def __init__(
        self,
        embedding_service=None,
        feature_service=None
    ):

        self.embedding_service = (
            embedding_service
            if embedding_service
            else EmbeddingService()
        )

        self.feature_service = (
            feature_service
            if feature_service
            else QuestionFeatureService()
        )

    def compare(
        self,
        question1,
        question2,
        similarity_score,
        threshold=0.85
    ):

        features1 = (
            self.feature_service.extract(
                question1
            )
        )

        features2 = (
            self.feature_service.extract(
                question2
            )
        )

        same_verb = (
            features1["verb"]
            ==
            features2["verb"]
        )

        same_question_type = (
            features1["question_type"]
            ==
            features2["question_type"]
        )

        is_duplicate = (

            similarity_score >= threshold

            and

            same_verb

            and

            same_question_type
        )

        return {

            "similarity_score":
                similarity_score,

            "threshold":
                threshold,

            "question1_features":
                features1,

            "question2_features":
                features2,

            "same_verb":
                same_verb,

            "same_question_type":
                same_question_type,

            "is_duplicate":
                is_duplicate
        }

    def is_duplicate(
        self,
        question1,
        question2,
        threshold=0.85
    ):

        embedding1 = (
            self.embedding_service
            .generate_embedding(
                question1
            )
        )

        embedding2 = (
            self.embedding_service
            .generate_embedding(
                question2
            )
        )

        similarity_score = (
            SimilarityService.calculate_similarity(
                embedding1,
                embedding2
            )
        )

        return self.compare(
            question1=question1,
            question2=question2,
            similarity_score=similarity_score,
            threshold=threshold
        )