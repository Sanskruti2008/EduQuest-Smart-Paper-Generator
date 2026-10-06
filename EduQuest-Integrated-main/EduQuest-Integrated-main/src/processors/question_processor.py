from src.repositories.supabase_question_repository import (
    SupabaseQuestionRepository
)


class QuestionProcessor:

    def __init__(
        self,
        embedding_service,
        search_service,
        duplicate_service,
        chroma_service,
        canonical_service,
        supabase_repository=None
    ):

        self.embedding_service = embedding_service
        self.search_service = search_service
        self.duplicate_service = duplicate_service
        self.chroma_service = chroma_service
        self.canonical_service = canonical_service

        # Supabase is optional so existing tests and
        # existing pipeline behaviour remain compatible.
        self.supabase_repository = (
            supabase_repository
        )

    # ==================================================
    # PROCESS ONE QUESTION
    # ==================================================

    def process(
        self,
        question,
        subject
    ):

        question_text = (
            question["question_text"]
        )

        print(
            f"\nProcessing: {question_text}"
        )

        # ==================================================
        # 1. GENERATE EMBEDDING
        # ==================================================

        embedding = (
            self.embedding_service
            .generate_embedding(
                question_text
            )
        )

        print(
            f"Embedding Generated: "
            f"{len(embedding)} dimensions"
        )

        # ==================================================
        # 2. SEARCH SIMILAR QUESTIONS
        # ==================================================

        search_results = (
            self.search_service
            .find_similar_questions(
                embedding=embedding,
                subject=subject,
                top_k=5
            )
        )

        ids = (
            search_results
            .get("ids", [[]])[0]
        )

        distances = (
            search_results
            .get("distances", [[]])[0]
        )

        documents = (
            search_results
            .get("documents", [[]])[0]
        )

        print(
            f"Similar Questions Found: "
            f"{len(ids)}"
        )

        # ==================================================
        # 3. NO EXISTING QUESTIONS
        # ==================================================

        if not ids:

            canonical = (
                self.canonical_service
                .create_canonical(
                    question=question_text,
                    subject=subject,
                    branch=question.get("branch"),
                    semester=question.get("semester"),
                    question_type=question.get("question_type"),
                    unit=question.get("unit"),
                    unit_id=question.get("unit_id"),
                    marks=question.get("marks"),
                    rua=question.get("rua"),
                    difficulty=question.get("difficulty"),
                    course_outcome=question.get("course_outcome"),
                    bloom_level=question.get("bloom_level"),
                )
            )

            canonical_id = (
                canonical["canonical_id"]
            )

            self._store_question(
                question=question,
                embedding=embedding,
                subject=subject,
                canonical_id=canonical_id
            )

            # Save to Supabase
            self._save_to_supabase(
                question=question,
                subject=subject,
                canonical=canonical,
                similarity_score=0.0
            )

            print(
                "New canonical question created."
            )

            return {
                "question": question,
                "embedding": embedding,
                "similarity_score": 0.0,
                "is_duplicate": False,
                "canonical_id": canonical_id,
                "canonical_question":
                    canonical["canonical_question"]
            }

        # ==================================================
        # 4. GET BEST MATCH
        # ==================================================

        best_distance = distances[0]

        search_similarity = (
            self._distance_to_similarity(
                best_distance
            )
        )

        existing_question = (
            documents[0]
            if documents
            else ""
        )

        # ==================================================
        # 5. DUPLICATE DETECTION
        # ==================================================

        duplicate_result = (
            self.duplicate_service
            .is_duplicate(
                question1=question_text,
                question2=existing_question,
                threshold=0.85
            )
        )

        final_similarity = (
            duplicate_result.get(
                "similarity_score",
                search_similarity
            )
        )

        print(
            f"Best Similarity: "
            f"{search_similarity:.4f}"
        )

        print(
            "Duplicate Check:"
        )

        print(
            f"  Similarity : "
            f"{final_similarity:.4f}"
        )

        print(
            "  Threshold  : 0.8500"
        )

        print(
            f"  Same Verb  : "
            f"{duplicate_result.get('same_verb', False)}"
        )

        # ==================================================
        # 6. DUPLICATE QUESTION
        # ==================================================

        if duplicate_result["is_duplicate"]:

            canonical_id = (
                self._get_canonical_id(
                    question_id=ids[0],
                    subject=subject
                )
            )

            self.canonical_service.repository.update_metadata(
                canonical_id,
                {
                    "branch": question.get("branch"),
                    "semester": question.get("semester"),
                    "question_type": question.get("question_type"),
                    "unit": question.get("unit"),
                    "unit_id": question.get("unit_id"),
                    "marks": question.get("marks"),
                    "rua": question.get("rua"),
                    "difficulty": question.get("difficulty"),
                    "course_outcome": question.get("course_outcome"),
                    "bloom_level": question.get("bloom_level"),
                }
            )

            print(
                "Duplicate detected."
            )

            # ----------------------------------------------
            # Save duplicate question to Supabase.
            #
            # It will be linked to the existing canonical
            # question instead of creating a new canonical.
            # ----------------------------------------------

            self._save_duplicate_to_supabase(
                question=question,
                subject=subject,
                canonical_id=canonical_id,
                canonical_question=existing_question,
                similarity_score=final_similarity
            )

            return {
                "question": question,
                "embedding": embedding,
                "similarity_score":
                    final_similarity,
                "is_duplicate": True,
                "canonical_id":
                    canonical_id,
                "canonical_question":
                    existing_question
            }

        # ==================================================
        # 7. NEW UNIQUE QUESTION
        # ==================================================

        canonical = (
            self.canonical_service
            .create_canonical(
                question=question_text,
                subject=subject,
                branch=question.get("branch"),
                semester=question.get("semester"),
            )
        )

        canonical_id = (
            canonical["canonical_id"]
        )

        self._store_question(
            question=question,
            embedding=embedding,
            subject=subject,
            canonical_id=canonical_id
        )

        # Save unique question to Supabase
        self._save_to_supabase(
            question=question,
            subject=subject,
            canonical=canonical,
            similarity_score=final_similarity
        )

        print(
            "New canonical question created."
        )

        return {
            "question": question,
            "embedding": embedding,
            "similarity_score":
                final_similarity,
            "is_duplicate": False,
            "canonical_id":
                canonical_id,
            "canonical_question":
                canonical["canonical_question"]
        }

    # ==================================================
    # SAVE UNIQUE QUESTION TO SUPABASE
    # ==================================================

    def _save_to_supabase(
        self,
        question,
        subject,
        canonical,
        similarity_score=None
    ):

        if self.supabase_repository is None:
            return

        print(
            "Saving question to Supabase..."
        )

        # ----------------------------------------------
        # 1. Get/create subject
        # ----------------------------------------------

        subject_id = (
            self.supabase_repository
            .get_or_create_subject(
                subject
            )
        )

        # ----------------------------------------------
        # 2. Save original question
        # ----------------------------------------------

        question_id = (
            self.supabase_repository
            .save_question(
                question=question,
                subject_id=subject_id
            )
        )

        # ----------------------------------------------
        # 3. Save canonical question
        #
        # Supabase generates its own BIGINT canonical_id.
        # This is intentionally separate from the engine's
        # CQ-00001 style canonical ID.
        # ----------------------------------------------

        supabase_canonical_id = (
            self.supabase_repository
            .save_canonical(
                canonical_question=
                    canonical["canonical_question"]
            )
        )

        # ----------------------------------------------
        # 4. Save question → canonical mapping
        # ----------------------------------------------

        self.supabase_repository.save_mapping(
            canonical_id=
                supabase_canonical_id,

            question_id=
                question_id,

            similarity_score=
                similarity_score
        )

        print(
            "Question saved to Supabase."
        )

        print(
            f"  Question ID      : {question_id}"
        )

        print(
            f"  Engine Canonical : "
            f"{canonical['canonical_id']}"
        )

        print(
            f"  Supabase Canonical: "
            f"{supabase_canonical_id}"
        )

    # ==================================================
    # SAVE DUPLICATE QUESTION TO SUPABASE
    # ==================================================

    def _save_duplicate_to_supabase(
        self,
        question,
        subject,
        canonical_id,
        canonical_question,
        similarity_score=None
    ):

        if self.supabase_repository is None:
            return

        print(
            "Saving duplicate question to Supabase..."
        )

        # ----------------------------------------------
        # 1. Get/create subject
        # ----------------------------------------------

        subject_id = (
            self.supabase_repository
            .get_or_create_subject(
                subject
            )
        )

        # ----------------------------------------------
        # 2. Save duplicate question
        # ----------------------------------------------

        question_id = (
            self.supabase_repository
            .save_question(
                question=question,
                subject_id=subject_id
            )
        )

        # ----------------------------------------------
        # 3. Find/create corresponding canonical
        #
        # We use canonical QUESTION TEXT rather than
        # the engine's CQ-xxxxx ID because Supabase has
        # a BIGINT canonical_id.
        # ----------------------------------------------

        supabase_canonical_id = (
            self.supabase_repository
            .save_canonical(
                canonical_question=
                    canonical_question
            )
        )

        # ----------------------------------------------
        # 4. Map duplicate question to canonical
        # ----------------------------------------------

        self.supabase_repository.save_mapping(
            canonical_id=
                supabase_canonical_id,

            question_id=
                question_id,

            similarity_score=
                similarity_score
        )

        print(
            "Duplicate question saved to Supabase."
        )

        print(
            f"  Question ID      : {question_id}"
        )

        print(
            f"  Engine Canonical : {canonical_id}"
        )

        print(
            f"  Supabase Canonical: "
            f"{supabase_canonical_id}"
        )

    # ==================================================
    # DISTANCE → SIMILARITY
    # ==================================================

    def _distance_to_similarity(
        self,
        distance
    ):

        if distance is None:
            return 0.0

        return max(
            0.0,
            1.0 - distance
        )

    # ==================================================
    # STORE QUESTION IN CHROMADB
    # ==================================================

    def _store_question(
        self,
        question,
        embedding,
        subject,
        canonical_id
    ):

        collection = (
            self.chroma_service
            .get_collection(
                subject
            )
        )

        # ----------------------------------------------
        # Generate stable question ID
        # ----------------------------------------------

        question_id = (
            f"{subject}_"
            f"{collection.count() + 1}"
        )

        collection.add(
            ids=[
                question_id
            ],
            embeddings=[
                embedding
            ],
            documents=[
                question[
                    "question_text"
                ]
            ],
            metadatas=[
                {
                    "subject": subject,
                    "canonical_id":
                        canonical_id
                }
            ]
        )

        print(
            "Question stored in ChromaDB."
        )

    # ==================================================
    # GET CANONICAL ID FROM CHROMADB RECORD
    # ==================================================

    def _get_canonical_id(
        self,
        question_id,
        subject
    ):

        collection = (
            self.chroma_service
            .get_collection(
                subject
            )
        )

        result = (
            collection.get(
                ids=[
                    question_id
                ]
            )
        )

        if not result:
            return None

        # ==================================================
        # 1. TRY METADATA
        # ==================================================

        metadatas = (
            result.get(
                "metadatas"
            )
        )

        if metadatas:

            metadata = metadatas[0]

            if metadata:

                canonical_id = (
                    metadata.get(
                        "canonical_id"
                    )
                )

                if canonical_id:
                    return canonical_id

        # ==================================================
        # 2. LEGACY RECORD RECOVERY
        # ==================================================

        documents = (
            result.get(
                "documents"
            )
        )

        if not documents:
            return None

        existing_question = (
            documents[0]
        )

        # ==================================================
        # 3. SEARCH CANONICAL REPOSITORY
        # ==================================================

        canonical = (
            self.canonical_service
            .repository
            .find_by_question(
                existing_question
            )
        )

        if canonical:

            canonical_id = (
                canonical[
                    "canonical_id"
                ]
            )

            # Repair old ChromaDB record
            collection.update(
                ids=[
                    question_id
                ],
                metadatas=[
                    {
                        "subject": subject,
                        "canonical_id":
                            canonical_id
                    }
                ]
            )

            return canonical_id

        # ==================================================
        # 4. CREATE CANONICAL IF MISSING
        # ==================================================

        canonical = (
            self.canonical_service
            .create_canonical(
                question=existing_question,
                subject=subject,
                branch=None,
                semester=None,
            )
        )

        canonical_id = (
            canonical[
                "canonical_id"
            ]
        )

        # Repair ChromaDB metadata
        collection.update(
            ids=[
                question_id
            ],
            metadatas=[
                {
                    "subject": subject,
                    "canonical_id":
                        canonical_id
                }
            ]
        )

        return canonical_id