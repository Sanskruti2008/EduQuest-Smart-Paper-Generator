import json
import os


class CanonicalRepository:

    def __init__(
        self,
        file_path="data/canonical_questions.json"
    ):

        self.file_path = file_path

        # Create data directory if required
        directory = os.path.dirname(
            self.file_path
        )

        if directory:
            os.makedirs(
                directory,
                exist_ok=True
            )

        # Create repository file
        if not os.path.exists(
            self.file_path
        ):

            with open(
                self.file_path,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    [],
                    file,
                    indent=4,
                    ensure_ascii=False
                )

    # ==================================================
    # GET ALL
    # ==================================================

    def get_all(self):

        with open(
            self.file_path,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if not isinstance(data, list):
            return []

        return data

    # ==================================================
    # SAVE ALL
    # ==================================================

    def save_all(
        self,
        data
    ):

        with open(
            self.file_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False
            )

    # ==================================================
    # ADD CANONICAL
    # ==================================================

    def add_canonical(
        self,
        canonical_question,
        subject=None,
        question_type=None,
        verb=None,
        **kwargs
    ):

        data = self.get_all()

        # ----------------------------------------------
        # Normalize question for exact duplicate check
        # ----------------------------------------------

        normalized_new = (
            canonical_question
            .strip()
            .lower()
            .rstrip("?")
            .rstrip(".")
        )

        # ----------------------------------------------
        # Check whether canonical already exists
        # ----------------------------------------------

        for item in data:

            existing_question = (
                item.get(
                    "canonical_question",
                    ""
                )
            )

            normalized_existing = (
                existing_question
                .strip()
                .lower()
                .rstrip("?")
                .rstrip(".")
            )

            if (
                normalized_existing
                == normalized_new
            ):

                return item

        # ----------------------------------------------
        # Generate ID
        # ----------------------------------------------

        canonical_id = (
            f"CQ-{len(data) + 1:05d}"
        )

        item = {

            "canonical_id":
                canonical_id,

            "canonical_question":
                canonical_question,

            "subject":
                subject,

            "question_type":
                question_type,

            "verb":
                verb
        }

        # Preserve any additional metadata
        # supplied by CanonicalService

        for key, value in kwargs.items():

            if key not in item:

                item[key] = value

        # ----------------------------------------------
        # Save
        # ----------------------------------------------

        data.append(item)

        self.save_all(data)

        return item

    # ==================================================
    # ADD
    # ==================================================
    #
    # Compatibility method.
    #
    # Some services may call add() while others call
    # add_canonical(). Both should use the same logic.
    #

    def add(
        self,
        canonical_question,
        subject=None,
        question_type=None,
        verb=None,
        **kwargs
    ):

        return self.add_canonical(

            canonical_question=
                canonical_question,

            subject=
                subject,

            question_type=
                question_type,

            verb=
                verb,

            **kwargs
        )

    # ==================================================
    # FIND BY ID
    # ==================================================

    def get_by_id(
        self,
        canonical_id
    ):

        data = self.get_all()

        for item in data:

            if (
                item.get(
                    "canonical_id"
                )
                == canonical_id
            ):

                return item

        return None

    def update_metadata(
        self,
        canonical_id,
        metadata
    ):
        """Merge non-empty metadata into an existing canonical record."""
        data = self.get_all()
        for item in data:
            if item.get("canonical_id") != canonical_id:
                continue
            changed = False
            for key, value in metadata.items():
                if value is not None and value != "" and item.get(key) != value:
                    item[key] = value
                    changed = True
            if changed:
                self.save_all(data)
            return item
        return None

    # ==================================================
    # FIND BY QUESTION
    # ==================================================

    def find_by_question(
        self,
        question
    ):

        normalized_question = (
            question
            .strip()
            .lower()
            .rstrip("?")
            .rstrip(".")
        )

        data = self.get_all()

        for item in data:

            existing_question = (
                item.get(
                    "canonical_question",
                    ""
                )
            )

            normalized_existing = (
                existing_question
                .strip()
                .lower()
                .rstrip("?")
                .rstrip(".")
            )

            if (
                normalized_existing
                == normalized_question
            ):

                return item

        return None

    # ==================================================
    # COUNT
    # ==================================================

    def count(self):

        return len(
            self.get_all()
        )

    # ==================================================
    # CLEAR
    # ==================================================

    def clear(self):

        self.save_all([])

    # ==================================================
    # FIRST CANONICAL
    # ==================================================

    def get_first_canonical(self):

        data = self.get_all()

        if data:
            return data[0]

        return None