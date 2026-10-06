import hashlib
import re

import chromadb


class ChromaService:

    def __init__(
        self,
        db_path="./chroma_db"
    ):

        # --------------------------------------------------
        # Store database path
        # --------------------------------------------------

        self.db_path = db_path

        # --------------------------------------------------
        # Persistent ChromaDB client
        # --------------------------------------------------

        self.client = (
            chromadb.PersistentClient(
                path=self.db_path
            )
        )

    # ======================================================
    # GET OR CREATE COLLECTION
    # ======================================================

    def get_collection(
        self,
        subject=None
    ):

        # --------------------------------------------------
        # Backward compatibility
        #
        # Older tests/code may call:
        #
        #     get_collection()
        #
        # New architecture calls:
        #
        #     get_collection("Communication Skills")
        # --------------------------------------------------

        if subject is None:

            subject = "Communication Skills"

        collection_name = (
            self._create_collection_name(
                subject
            )
        )

        return (
            self.client
            .get_or_create_collection(
                name=collection_name
            )
        )

    # ======================================================
    # COUNT QUESTIONS
    # ======================================================

    def count_questions(
        self,
        subject=None
    ):

        collection = (
            self.get_collection(
                subject
            )
        )

        return collection.count()

    # ======================================================
    # SEARCH SIMILAR QUESTIONS
    # ======================================================

    def search_similar(
        self,
        embedding,
        subject=None,
        top_k=5
    ):

        collection = (
            self.get_collection(
                subject
            )
        )

        # --------------------------------------------------
        # No questions stored yet
        # --------------------------------------------------

        if collection.count() == 0:

            return {
                "ids": [[]],
                "documents": [[]],
                "distances": [[]],
                "metadatas": [[]]
            }

        # --------------------------------------------------
        # Search
        # --------------------------------------------------

        return collection.query(

            query_embeddings=[
                embedding
            ],

            n_results=min(
                top_k,
                collection.count()
            )
        )

    # ======================================================
    # CREATE COLLECTION NAME
    # ======================================================

    def _create_collection_name(
        self,
        subject
    ):

        raw_subject = str(subject or "").strip().lower()
        clean_subject = re.sub(r"[^a-z0-9._-]+", "_", raw_subject)
        clean_subject = re.sub(r"_+", "_", clean_subject).strip("._-")

        if not clean_subject:
            clean_subject = "unknown"

        collection_name = f"questions_{clean_subject}"
        if len(collection_name) > 512:
            suffix = hashlib.sha1(raw_subject.encode("utf-8")).hexdigest()[:12]
            collection_name = f"questions_{clean_subject[:489]}_{suffix}"

        # Chroma requires names to start and end with an alphanumeric character.
        return collection_name.rstrip("._-") or "questions_unknown"
