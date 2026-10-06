import os
import re

from dotenv import load_dotenv
from supabase import create_client

from paper_generation.data.sample_questions import sample_questions


class SupabaseQuestionRepository:

    def __init__(self):

        load_dotenv()

        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")

        self.client = None
        self._offline = False
        self._last_error = None

        try:
            if not url or not key:
                raise ValueError(
                    "SUPABASE_URL or SUPABASE_KEY is missing"
                )

            self.client = create_client(
                url,
                key
            )
        except Exception as exc:  # pragma: no cover - network/env fallback
            self._offline = True
            self._last_error = exc
            self.client = None
            print(
                "Supabase unavailable; continuing in offline fallback mode. "
                f"Reason: {exc}"
            )

    def _offline_id(self, *parts):
        """Generate a stable numeric pseudo-ID for offline-only records."""
        seed = "|".join(str(part) for part in parts if part is not None)
        return abs(hash(seed)) % 10**9

    def _normalize_fallback_questions(self, records):
        """Normalize in-memory sample questions to the paper-generation contract."""

        normalized = []
        for record in records:
            question = dict(record)
            question.setdefault("question_text", question.get("canonical_question") or question.get("question"))
            question.setdefault("canonical_id", f"OFFLINE_{self._offline_id(question.get('question_text', 'unknown'))}")
            question.setdefault("canonical_question", question.get("question_text"))
            question.setdefault("question", question.get("question_text"))
            question.setdefault("subject", "Unknown")
            question.setdefault("unit", record.get("unit") or record.get("unit_id"))
            question.setdefault("course_outcome", record.get("course_outcome") or "CO1")
            question.setdefault("difficulty", record.get("difficulty") or "Medium")
            question.setdefault("marks", record.get("marks") or 5)
            question.setdefault("rua", record.get("rua") or "U")
            question.setdefault("bloom_level", record.get("bloom_level") or record.get("bloom") or "Understand")
            question.setdefault("question_type", record.get("question_type") or "Short Answer")
            question.setdefault("chapter", record.get("chapter") or record.get("unit"))
            question.setdefault("question_number", record.get("question_number") or "")
            question.setdefault("question_id", self._offline_id(question.get("canonical_id"), question.get("question_text")))
            normalized.append(question)

        return normalized

    def _fallback_records(
        self,
        subject=None,
        unit_id=None,
        marks=None,
        rua=None,
        difficulty=None,
        bloom_level=None,
        course_outcome=None,
        question_type=None,
    ):
        """Return a local, read-only question pool when Supabase cannot be reached."""

        records = list(sample_questions)

        filters = {
            "subject": subject,
            "unit_id": unit_id,
            "marks": marks,
            "rua": rua,
            "difficulty": difficulty,
            "bloom_level": bloom_level,
            "course_outcome": course_outcome,
            "question_type": question_type,
        }

        for key, value in filters.items():
            if value is None:
                continue

            if key == "subject":
                requested_subject = self._normalize_subject_name(value)
                matches = []
                for record in records:
                    candidate_subject = record.get("subject") or ""
                    normalized_candidate = self._normalize_subject_name(candidate_subject)
                    if normalized_candidate == requested_subject:
                        matches.append(record)
                if matches:
                    records = matches
                continue

            if key == "unit_id":
                unit_matches = []
                for record in records:
                    unit_value = record.get("unit_id")
                    if unit_value is None:
                        unit_value = record.get("unit")
                    if str(unit_value or "") == str(value):
                        unit_matches.append(record)
                records = unit_matches
                continue

            records = [
                record for record in records
                if record.get(key) == value
            ]

        return records

    @staticmethod
    def _normalize_subject_name(subject_name):
        """Normalize harmless naming variations used by the UI and database."""
        value = str(subject_name or "").strip().casefold()
        value = re.sub(r"[^a-z0-9]+", " ", value)
        value = re.sub(r"\s+", " ", value).strip()
        aliases = {
            "advanced java": "advance java",
        }
        return aliases.get(value, value)

    # ==================================================
    # SUBJECT
    # ==================================================

    def get_or_create_subject(
        self,
        subject_name
    ):

        if self.client is None:
            return self._offline_id("subject", subject_name)

        result = (
            self.client
            .table("subject")
            .select("subject_id")
            .eq(
                "subject_name",
                subject_name
            )
            .execute()
        )

        if result.data:
            return result.data[0]["subject_id"]

        result = (
            self.client
            .table("subject")
            .insert({
                "subject_name": subject_name
            })
            .execute()
        )

        return result.data[0]["subject_id"]

    # ==================================================
    # QUESTION
    # ==================================================

    @staticmethod
    def _normalize_unit_id(unit):
        if unit is None or isinstance(unit, int):
            return unit
        if not isinstance(unit, str):
            raise ValueError(f"Invalid unit_id: {unit}")

        value = unit.strip()
        if value.isdigit():
            return int(value)

        numeric_match = re.fullmatch(r"Unit[- ](\d+)", value, re.IGNORECASE)
        if numeric_match:
            return int(numeric_match.group(1))

        match = re.fullmatch(r"Unit[- ]([IVXLCDM]+)", value, re.IGNORECASE)
        if not match:
            raise ValueError(f"Invalid unit_id: {unit}")

        roman_values = {
            "I": 1,
            "V": 5,
            "X": 10,
            "L": 50,
            "C": 100,
            "D": 500,
            "M": 1000,
        }
        total = 0
        previous = 0
        for symbol in reversed(match.group(1).upper()):
            current = roman_values[symbol]
            if current < previous:
                total -= current
            else:
                total += current
                previous = current
        return total

    def _resolve_unit_id(self, unit, subject_id, course_outcome=None):
        """
        Resolve different unit formats to the existing database unit.

        Examples:
            Unit-I  -> Unit 1
            Unit I  -> Unit 1
            Unit-1  -> Unit 1
            Unit 1  -> Unit 1
            1       -> unit_id 1 only when integer is supplied
        """

        if unit is None or isinstance(unit, int):
            return unit

        if not isinstance(unit, str):
            raise ValueError(f"Invalid unit_id: {unit}")

        value = unit.strip()

        if value.isdigit():
            return int(value)

        # ----------------------------------------------
        # Normalize unit name
        # ----------------------------------------------

        normalized = (
            value.upper()
            .replace("-", " ")
            .replace("_", " ")
            .strip()
        )

        parts = normalized.split()

        if len(parts) == 2 and parts[0] == "UNIT":
            unit_value = parts[1]

            roman_to_number = {
                "I": "1",
                "II": "2",
                "III": "3",
                "IV": "4",
                "V": "5",
            }

            if unit_value in roman_to_number:
                unit_value = roman_to_number[unit_value]

            if unit_value.isdigit():
                value = f"Unit {int(unit_value)}"

        # ----------------------------------------------
        # Find existing normalized unit
        # ----------------------------------------------

        unit_result = (
            self.client
            .table("unit")
            .select("unit_id")
            .eq("unit_name", value)
            .eq("subject_id", subject_id)
            .limit(1)
            .execute()
        )

        if unit_result.data:
            return unit_result.data[0]["unit_id"]

        # ----------------------------------------------
        # Create only if genuinely new unit
        # ----------------------------------------------

        created_unit = (
            self.client
            .table("unit")
            .insert(
                {
                    "unit_name": value,
                    "subject_id": subject_id,
                    "course_outcome": course_outcome,
                }
            )
            .execute()
        )

        return created_unit.data[0]["unit_id"]
    def save_question(
        self,
        question,
        subject_id
    ):
        """
        Save one original/historical question.

        Supabase stores the complete metadata required
        by the Paper Generation Engine.
        """

        if self.client is None:
            return self._offline_id("question", question.get("question_text"), subject_id)

        question_text = question["question_text"]

        # --------------------------------------------------
        # Prevent duplicate storage of the same question
        # within the same subject.
        # --------------------------------------------------

        result = (
            self.client
            .table("question")
            .select("question_id")
            .eq(
                "question_text",
                question_text
            )
            .eq(
                "subject_id",
                subject_id
            )
            .execute()
        )

        if result.data:
            question_id = result.data[0]["question_id"]
            metadata_updates = {}

            if question.get("question_type") or question.get("type"):
                metadata_updates["question_type"] = (
                    question.get("question_type")
                    or question.get("type")
                )

            if question.get("difficulty") or question.get("difficulty_level"):
                metadata_updates["difficulty_level"] = (
                    question.get("difficulty")
                    or question.get("difficulty_level")
                )

            for field in (
                "marks",
                "course_outcome",
                "co",
                "unit_id",
                "bloom_level",
                "bloom",
                "rua",
                "rua_level",
                "question_number",
                "chapter",
                "unit",
            ):
                if question.get(field) is not None:
                    metadata_updates[field] = question[field]

            if "course_outcome" not in metadata_updates and question.get("co"):
                metadata_updates["course_outcome"] = question["co"]

            if "unit_id" not in metadata_updates and question.get("unit") is not None:
                metadata_updates["unit_id"] = question["unit"]

            if "bloom_level" not in metadata_updates and question.get("bloom"):
                metadata_updates["bloom_level"] = question["bloom"]

            if "rua" not in metadata_updates and question.get("rua_level"):
                metadata_updates["rua"] = question["rua_level"]

            if "question_number" in metadata_updates:
                metadata_updates["question_number"] = str(
                    metadata_updates["question_number"]
                )

            if "co" in metadata_updates:
                metadata_updates["course_outcome"] = metadata_updates.pop("co")

            if "bloom" in metadata_updates:
                metadata_updates["bloom_level"] = metadata_updates.pop("bloom")

            if "rua_level" in metadata_updates:
                metadata_updates["rua"] = metadata_updates.pop("rua_level")

            if "unit" in metadata_updates:
                metadata_updates["unit_id"] = metadata_updates.pop("unit")

            if "unit_id" in metadata_updates:
                metadata_updates["unit_id"] = self._resolve_unit_id(
                    metadata_updates["unit_id"],
                    subject_id,
                    metadata_updates.get("course_outcome"),
                )

            if metadata_updates:
                self.client.table("question").update(
                    metadata_updates
                ).eq(
                    "question_id",
                    question_id
                ).execute()

            return question_id

        # --------------------------------------------------
        # Metadata normalization
        #
        # Accept multiple possible input field names so
        # different dataset formats remain compatible.
        # --------------------------------------------------

        question_type = (
            question.get("question_type")
            or question.get("type")
            or "Short Answer"
        )

        difficulty = (
            question.get("difficulty")
            or question.get("difficulty_level")
            or "Medium"
        )

        marks = question.get("marks")

        if marks is None:
            marks = 5

        course_outcome = (
            question.get("course_outcome")
            or question.get("co")
        )

        unit_id = (
            question.get("unit_id")
            or question.get("unit")
        )
        unit_id = self._resolve_unit_id(
            unit_id,
            subject_id,
            course_outcome,
        )

        bloom_level = (
            question.get("bloom_level")
            or question.get("bloom")
            or "Understand"
        )

        rua = (
            question.get("rua")
            or question.get("rua_level")
            or "U"
        )

        question_number = (
            question.get("question_number")
        )

        if question_number is None:
            question_number = ""

        chapter = (
            question.get("chapter")
            or question.get("unit")
        )

        # --------------------------------------------------
        # Prepare database record
        # --------------------------------------------------

        data = {

            "question_text":
                question_text,

            "question_type":
                question_type,

            "difficulty_level":
                difficulty,

            "subject_id":
                subject_id,

            "marks":
                marks,

            "course_outcome":
                course_outcome,

            "unit_id":
                unit_id,

            "bloom_level":
                bloom_level,

            "rua":
                rua,

            "question_number":
                str(question_number),

            "chapter":
                chapter,

            "status":
                "active"
        }

        # --------------------------------------------------
        # Insert
        # --------------------------------------------------

        result = (
            self.client
            .table("question")
            .insert(data)
            .execute()
        )

        return result.data[0]["question_id"]

    # ==================================================
    # CANONICAL QUESTION
    # ==================================================

    def save_canonical(
        self,
        canonical_question,
        concept_name=None
    ):
        """
        Save a canonical/unique question.
        """

        if self.client is None:
            return self._offline_id("canonical", canonical_question, concept_name)

        result = (
            self.client
            .table("canonical_question")
            .select(
                "canonical_id"
            )
            .eq(
                "canonical_question",
                canonical_question
            )
            .execute()
        )

        if result.data:
            return result.data[0]["canonical_id"]

        result = (
            self.client
            .table("canonical_question")
            .insert({
                "canonical_question":
                    canonical_question,

                "concept_name":
                    concept_name
            })
            .execute()
        )

        return result.data[0]["canonical_id"]

    # ==================================================
    # QUESTION → CANONICAL MAPPING
    # ==================================================

    def save_mapping(
        self,
        canonical_id,
        question_id,
        similarity_score=None
    ):
        """
        Create the relationship:

        original question
                ↓
        canonical question
        """

        if self.client is None:
            return self._offline_id("mapping", canonical_id, question_id, similarity_score)

        result = (
            self.client
            .table(
                "canonical_question_mapping"
            )
            .select(
                "mapping_id"
            )
            .eq(
                "question_id",
                question_id
            )
            .execute()
        )

        if result.data:
            return result.data[0]["mapping_id"]

        result = (
            self.client
            .table(
                "canonical_question_mapping"
            )
            .insert({

                "canonical_id":
                    canonical_id,

                "question_id":
                    question_id,

                "similarity_score":
                    similarity_score,

                "assignment_method":
                    "automatic"
            })
            .execute()
        )

        return result.data[0]["mapping_id"]

    # ==================================================
    # RETRIEVAL FOR PAPER GENERATION
    # ==================================================

    def get_questions_for_generation(
        self,
        subject=None,
        unit_id=None,
        marks=None,
        rua=None,
        difficulty=None,
        bloom_level=None,
        course_outcome=None,
        question_type=None
    ):
        """
        Public retrieval layer for Paper Generation.

        All filters are optional.

        Examples:

        get_questions_for_generation(
            subject="Communication Skills"
        )

        get_questions_for_generation(
            subject="Communication Skills",
            unit_id=1,
            marks=5,
            rua="U"
        )

        Supabase is the source of truth.
        ChromaDB is NOT accessed here.
        """

        if self._offline or self.client is None:
            return self._normalize_fallback_questions(
                self._fallback_records(
                    subject=subject,
                    unit_id=unit_id,
                    marks=marks,
                    rua=rua,
                    difficulty=difficulty,
                    bloom_level=bloom_level,
                    course_outcome=course_outcome,
                    question_type=question_type,
                )
            )

        # ==================================================
        # 1. GET SUBJECT INFORMATION
        # ==================================================

        subject_result = (
            self.client
            .table("subject")
            .select(
                "subject_id,"
                "subject_name"
            )
            .execute()
        )

        subject_map = {}

        for item in subject_result.data:

            subject_map[
                item["subject_id"]
            ] = item["subject_name"]

        unit_result = (
            self.client
            .table("unit")
            .select("unit_id,unit_name,subject_id")
            .execute()
        )

        unit_map = {
            item["unit_id"]: item
            for item in unit_result.data
        }

        # ==================================================
        # 2. RESOLVE SUBJECT
        # ==================================================

        subject_id = None

        if subject is not None:

            matching_subject = None

            requested_subject = self._normalize_subject_name(subject)
            for item in subject_result.data:
                if self._normalize_subject_name(item["subject_name"]) == requested_subject:
                    matching_subject = item
                    break

            if matching_subject is None:
                return []

            subject_id = (
                matching_subject[
                    "subject_id"
                ]
            )

        # ==================================================
        # 3. GET ACTIVE QUESTIONS
        # ==================================================

        question_query = (
            self.client
            .table("question")
            .select(
                "question_id,"
                "question_text,"
                "question_type,"
                "difficulty_level,"
                "subject_id,"
                "marks,"
                "course_outcome,"
                "unit_id,"
                "bloom_level,"
                "rua,"
                "question_number,"
                "chapter"
            )
            .eq(
                "status",
                "active"
            )
        )

        # --------------------------------------------------
        # Subject filter
        # --------------------------------------------------

        if subject_id is not None:

            question_query = (
                question_query
                .eq(
                    "subject_id",
                    subject_id
                )
            )

        # --------------------------------------------------
        # Metadata filters
        # --------------------------------------------------

        if unit_id is not None:

            if isinstance(unit_id, str) and not unit_id.strip().isdigit():
                matching_unit = (
                    self.client
                    .table("unit")
                    .select("unit_id")
                    .eq("unit_name", unit_id.strip())
                    .eq("subject_id", subject_id)
                    .limit(1)
                    .execute()
                )
                if not matching_unit.data:
                    return []
                unit_id = matching_unit.data[0]["unit_id"]

            question_query = (
                question_query
                .eq(
                    "unit_id",
                    unit_id
                )
            )

        if marks is not None:

            question_query = (
                question_query
                .eq(
                    "marks",
                    marks
                )
            )

        if rua is not None:

            question_query = (
                question_query
                .eq(
                    "rua",
                    rua
                )
            )

        if difficulty is not None:

            question_query = (
                question_query
                .eq(
                    "difficulty_level",
                    difficulty
                )
            )

        if bloom_level is not None:

            question_query = (
                question_query
                .eq(
                    "bloom_level",
                    bloom_level
                )
            )

        if course_outcome is not None:

            question_query = (
                question_query
                .eq(
                    "course_outcome",
                    course_outcome
                )
            )

        if question_type is not None:

            question_query = (
                question_query
                .eq(
                    "question_type",
                    question_type
                )
            )

        question_result = (
            question_query.execute()
        )

        if not question_result.data:
            return []

        # ==================================================
        # 4. QUESTION LOOKUP
        # ==================================================

        question_map = {}

        for question in question_result.data:

            question_map[
                question["question_id"]
            ] = question

        question_ids = list(
            question_map.keys()
        )

        # ==================================================
        # 5. GET CANONICAL MAPPINGS
        # ==================================================

        mapping_result = (
            self.client
            .table(
                "canonical_question_mapping"
            )
            .select(
                "mapping_id,"
                "canonical_id,"
                "question_id,"
                "similarity_score,"
                "assignment_method"
            )
            .in_(
                "question_id",
                question_ids
            )
            .execute()
        )

        if not mapping_result.data:
            return []

        # ==================================================
        # 6. GET CANONICAL QUESTIONS
        # ==================================================

        canonical_ids = list({
            item["canonical_id"]
            for item in mapping_result.data
        })

        canonical_result = (
            self.client
            .table(
                "canonical_question"
            )
            .select(
                "canonical_id,"
                "canonical_question,"
                "concept_name"
            )
            .in_(
                "canonical_id",
                canonical_ids
            )
            .execute()
        )

        if not canonical_result.data:
            return []

        # ==================================================
        # 7. CANONICAL LOOKUP
        # ==================================================

        canonical_map = {}

        for canonical in canonical_result.data:

            canonical_map[
                canonical["canonical_id"]
            ] = canonical

        # ==================================================
        # 8. BUILD UNIQUE QUESTION BANK
        # ==================================================

        results_by_canonical = {}

        for mapping in mapping_result.data:

            canonical_id = (
                mapping["canonical_id"]
            )

            question_id = (
                mapping["question_id"]
            )

            canonical = (
                canonical_map.get(
                    canonical_id
                )
            )

            question = (
                question_map.get(
                    question_id
                )
            )

            if not canonical or not question:
                continue

            # --------------------------------------------------
            # If multiple historical questions belong to the
            # same canonical question, use the lowest question
            # ID as the stable representative.
            # --------------------------------------------------

            existing = results_by_canonical.get(canonical_id)

            if existing is not None:
                current_metadata_score = sum(
                    existing.get(field) is not None
                    for field in ("unit_id", "course_outcome")
                )
                candidate_metadata_score = sum(
                    question.get(field) is not None
                    for field in ("unit_id", "course_outcome")
                )

                if candidate_metadata_score < current_metadata_score:
                    continue

                if (
                    candidate_metadata_score == current_metadata_score
                    and question_id >= existing["_question_id"]
                ):
                    continue

            question_subject = (
                subject_map.get(
                    question["subject_id"]
                )
            )

            results_by_canonical[
                canonical_id
            ] = {

                "_question_id":
                    question_id,

                "canonical_id":
                    canonical[
                        "canonical_id"
                    ],

                "canonical_question":
                    canonical[
                        "canonical_question"
                    ],

                # --------------------------------------------------
                # Compatibility fields
                # --------------------------------------------------

                "question_text":
                    canonical[
                        "canonical_question"
                    ],

                "question":
                    canonical[
                        "canonical_question"
                    ],

                "concept_name":
                    canonical.get(
                        "concept_name"
                    ),

                # --------------------------------------------------
                # Metadata
                # --------------------------------------------------

                "subject":
                    question_subject,

                "question_type":
                    question.get(
                        "question_type"
                    ),

                "difficulty":
                    question.get(
                        "difficulty_level"
                    ),

                "marks":
                    question.get(
                        "marks"
                    ),

                "course_outcome":
                    question.get(
                        "course_outcome"
                    ),

                "unit_id":
                    question.get(
                        "unit_id"
                    ),

                "unit":
                    (
                        unit_map.get(question.get("unit_id"), {})
                        .get("unit_name")
                    ),

                "bloom_level":
                    question.get(
                        "bloom_level"
                    ),

                "rua":
                    question.get(
                        "rua"
                    ),

                "question_number":
                    question.get(
                        "question_number"
                    ),

                "chapter":
                    question.get(
                        "chapter"
                    )
            }

        # ==================================================
        # 9. REMOVE INTERNAL FIELDS
        # ==================================================

        results = []

        results = []

        for item in results_by_canonical.values():

            item["question_id"] = item.pop(
                "_question_id",
                None
            )

            results.append(item)
        # ==================================================
        # 10. STABLE ORDER
        # ==================================================

        results.sort(
            key=lambda item:
                item["canonical_id"]
        )

        return results