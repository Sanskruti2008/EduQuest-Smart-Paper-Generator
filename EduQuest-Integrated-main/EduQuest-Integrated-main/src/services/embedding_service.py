from sentence_transformers import SentenceTransformer


class EmbeddingService:

    _model = None

    MODEL_NAME = "all-MiniLM-L6-v2"

    def __init__(self):

        # --------------------------------------------------
        # Reuse already loaded model
        # --------------------------------------------------

        if EmbeddingService._model is not None:

            return

        print(
            "Loading Embedding Model..."
        )

        # --------------------------------------------------
        # Load model
        #
        # local_files_only=False allows the first download.
        # After the model is cached, it can be reused.
        # --------------------------------------------------

        EmbeddingService._model = (
            SentenceTransformer(
                self.MODEL_NAME
            )
        )

    # ======================================================
    # GENERATE SINGLE EMBEDDING
    # ======================================================

    def generate_embedding(
        self,
        text: str
    ):

        if not text:

            raise ValueError(
                "Text cannot be empty."
            )

        embedding = (
            EmbeddingService._model.encode(
                text
            )
        )

        return embedding.tolist()

    # ======================================================
    # GENERATE MULTIPLE EMBEDDINGS
    # ======================================================

    def generate_embeddings(
        self,
        texts: list
    ):

        if not texts:

            return []

        embeddings = (
            EmbeddingService._model.encode(
                texts
            )
        )

        return embeddings.tolist()