"""Bridge the OCR question-bank save flow to the integrated similarity engine."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from threading import Lock
from typing import Any

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

_APP_ROOT = Path(__file__).resolve().parents[2]
_ENGINE_ROOT = (
    _APP_ROOT
    / "EduQuest-Integrated-main"
    / "EduQuest-Integrated-main"
)
_engine = None
_engine_lock = Lock()


def _get_engine():
    global _engine
    if _engine is None:
        if not _ENGINE_ROOT.is_dir():
            raise RuntimeError(
                f"Integrated similarity engine directory not found: {_ENGINE_ROOT}"
            )
        engine_root = str(_ENGINE_ROOT)
        if engine_root not in sys.path:
            sys.path.insert(0, engine_root)
        load_dotenv(_APP_ROOT / "backend" / ".env", override=False)
        from src.engine.similarity_engine import SimilarityEngine

        with _engine_lock:
            if _engine is None:
                _engine = SimilarityEngine()
    return _engine


def _update_canonical_metadata(
    results: list[dict[str, Any]],
    *,
    subject: str,
    supabase_records: list[dict[str, Any]] | None = None,
) -> None:
    """Attach upload and Supabase metadata to local canonical records."""
    engine_root = str(_ENGINE_ROOT)
    if engine_root not in sys.path:
        sys.path.insert(0, engine_root)
    from src.services.canonical_repository import CanonicalRepository

    repository = CanonicalRepository(
        file_path=str(_ENGINE_ROOT / "data" / "canonical_questions.json")
    )
    changed = False
    records = repository.get_all()
    by_id = {record.get("canonical_id"): record for record in records}
    by_question = {
        str(record.get("canonical_question") or "").strip().casefold(): record
        for record in records
    }

    metadata_fields = (
        "branch",
        "semester",
        "unit",
        "unit_id",
        "marks",
        "rua",
        "difficulty",
        "course_outcome",
        "bloom_level",
        "question_type",
    )

    def update_record(record: dict[str, Any], source: dict[str, Any]) -> None:
        nonlocal changed
        for key in metadata_fields:
            value = source.get(key)
            if value is not None and value != "":
                if record.get(key) != value:
                    record[key] = value
                    changed = True

    for result in results:
        question = result.get("question") or {}
        canonical_id = result.get("canonical_id")
        record = by_id.get(canonical_id)
        if not record:
            continue
        update_record(record, question)
        if subject and record.get("subject") != subject:
            record["subject"] = subject
            changed = True

    for source in supabase_records or []:
        text = str(
            source.get("canonical_question")
            or source.get("question_text")
            or source.get("question")
            or ""
        ).strip().casefold()
        record = by_question.get(text)
        if record:
            update_record(record, source)

    if changed:
        repository.save_all(records)


def get_unique_question_bank(
    *,
    branch: str | None = None,
    semester: str | None = None,
    subject: str | None = None,
    subject_id: int | None = None,
) -> list[dict[str, Any]]:
    """Read canonical questions from Supabase, where mappings are authoritative."""
    from database import get_unique_question_bank as get_unique_from_database

    return get_unique_from_database(
        branch=branch,
        semester=semester,
        subject=subject,
        subject_id=subject_id,
    )


def _flatten_questions(papers_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    questions: list[dict[str, Any]] = []
    for paper in papers_data:
        for question in paper.get("questions", []) or []:
            if not isinstance(question, dict):
                continue
            question_text = str(
                question.get("question_text") or question.get("question") or ""
            ).strip()
            if not question_text:
                continue
            normalized = dict(question)
            normalized["question_text"] = question_text
            questions.append(normalized)
    return questions


def process_saved_questions(
    *,
    papers_data: list[dict[str, Any]],
    subject: str,
    exam_info: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run saved OCR questions through the integrated similarity pipeline."""
    questions = _flatten_questions(papers_data)
    if not questions:
        return {
            "status": "skipped",
            "reason": "No non-empty questions were available for similarity processing.",
            "processed": 0,
            "duplicates": 0,
            "new_questions": 0,
            "failed": 0,
            "results": [],
        }

    metadata = exam_info or {}
    branch = str(metadata.get("branch") or "").strip()
    semester = str(metadata.get("semester") or "").strip()
    for question in questions:
        question["branch"] = branch
        question["semester"] = semester
    dataset = {
        "subject": str(subject).strip(),
        "questions": questions,
    }
    engine = _get_engine()
    report = engine.process_dataset(dataset)
    report_results = report.get("results", [])
    supabase_records = engine.supabase_repository.get_questions_for_generation(
        subject=dataset["subject"]
    )
    _update_canonical_metadata(
        report_results,
        subject=dataset["subject"],
        supabase_records=supabase_records,
    )

    compact_results = []
    for result in report_results:
        question = result.get("question", {})
        compact_results.append(
            {
                "question_number": question.get("question_number"),
                "question_text": question.get("question_text"),
                "similarity_score": result.get("similarity_score", 0.0),
                "is_duplicate": bool(result.get("is_duplicate")),
                "canonical_id": result.get("canonical_id"),
                "canonical_question": result.get("canonical_question"),
            }
        )

    return {
        "status": "completed",
        "subject": dataset["subject"],
        "branch": metadata.get("branch"),
        "semester": metadata.get("semester"),
        "processed": report.get("processed", 0),
        "duplicates": report.get("duplicates", 0),
        "new_questions": report.get("new_questions", 0),
        "failed": report.get("failed", 0),
        "results": compact_results,
    }


def process_saved_questions_safely(
    *,
    papers_data: list[dict[str, Any]],
    subject: str,
    exam_info: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Preserve the successful DB save while reporting engine failures explicitly."""
    try:
        return process_saved_questions(
            papers_data=papers_data,
            subject=subject,
            exam_info=exam_info,
        )
    except Exception as error:
        logger.exception("Similarity processing failed after question-paper save")
        return {
            "status": "failed",
            "error": str(error),
            "processed": 0,
            "duplicates": 0,
            "new_questions": 0,
            "failed": len(_flatten_questions(papers_data)),
            "results": [],
        }
