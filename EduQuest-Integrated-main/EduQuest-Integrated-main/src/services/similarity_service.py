from sentence_transformers import util


class SimilarityService:

    @staticmethod
    def calculate_similarity(
        embedding1,
        embedding2
    ):

        score = util.cos_sim(
            embedding1,
            embedding2
        )

        return float(score)