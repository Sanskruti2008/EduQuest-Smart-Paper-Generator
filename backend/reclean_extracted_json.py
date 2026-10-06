"""Re-clean previously extracted question-paper JSON files.

This utility applies the current OCR question sanitizer and validator to an
existing extracted JSON file or every JSON file inside a directory.
It writes cleaned copies next to the originals by default.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Iterable

from ocr_extractor import (
    _split_compound_question_lines,
    _extract_explicit_co_from_text,
    _is_valid_co_label,
    _normalize_co_label,
    parse_papers_and_extract_questions,
    validate_and_clean_question,
)


def _iter_json_files(path: Path) -> Iterable[Path]:
    if path.is_file():
        yield path
        return
    yield from sorted(path.glob("*.json"))


def _clean_payload(payload: dict) -> tuple[dict, dict]:
    cleaned_payload = copy.deepcopy(payload)
    stats = {"kept": 0, "dropped": 0, "changed": 0}
    review_candidates = []

    def retain_for_review(question: dict, reason: str) -> None:
        candidate = copy.deepcopy(question or {})
        candidate["status"] = "needs_review"
        flags = candidate.setdefault("review_flags", [])
        if reason not in flags:
            flags.append(reason)
        review_candidates.append(candidate)

    for paper in cleaned_payload.get("papers", []):
        cleaned_questions = []
        for idx, question in enumerate(paper.get("questions", []), start=1):
            original_text = str(question.get("question_text", "")).strip()

            merged_text = _split_compound_question_lines(original_text)
            merged_lines = [line.strip() for line in merged_text.splitlines() if line.strip()]

            if len(merged_lines) > 1:
                parsed = parse_papers_and_extract_questions(merged_text)
                parsed_questions = parsed.get("papers", [{}])[0].get("questions", []) if parsed.get("papers") else []
                if len(parsed_questions) > 1:
                    for parsed_question in parsed_questions:
                        validated = validate_and_clean_question(copy.deepcopy(parsed_question))
                        if not validated:
                            stats["dropped"] += 1
                            retain_for_review(parsed_question, "Question could not be validated")
                            continue
                        validated["question_number"] = str(len(cleaned_questions) + 1)
                        if validated.get("question_text", "").strip() != original_text:
                            stats["changed"] += 1
                        cleaned_questions.append(validated)
                        stats["kept"] += 1
                    continue

            cleaned = validate_and_clean_question(copy.deepcopy(question))
            if not cleaned:
                stats["dropped"] += 1
                retain_for_review(question, "Question could not be validated")
                continue

            cleaned["question_number"] = str(len(cleaned_questions) + 1)
            if cleaned.get("question_text", "").strip() != original_text:
                stats["changed"] += 1
            cleaned_questions.append(cleaned)
            stats["kept"] += 1

        paper["questions"] = cleaned_questions

    # Standardize the final bank across all papers, not only within each parser pass.
    seen_questions = set()
    for paper in cleaned_payload.get("papers", []):
        standardized_questions = []
        for question in paper.get("questions", []):
            if question.get("status") != "accepted":
                retain_for_review(question, "Question requires human validation")
                continue
            question_text = str(question.get("question_text", "")).strip()
            question_key = " ".join(question_text.casefold().split())
            if not question_key or question_key in seen_questions:
                stats["dropped"] += 1
                if question_key:
                    retain_for_review(question, "Duplicate question removed from clean bank")
                continue

            course_outcome = _normalize_co_label(question.get("course_outcome") or "")
            course_outcome = course_outcome or _extract_explicit_co_from_text(question_text)
            if _is_valid_co_label(course_outcome):
                question["course_outcome"] = course_outcome
                question["review_flags"] = [
                    flag for flag in question.get("review_flags", [])
                    if flag != "Course outcome not confidently identified"
                ]
            else:
                question["course_outcome"] = ""
                flags = question.setdefault("review_flags", [])
                if "Course outcome not confidently identified" not in flags:
                    flags.append("Course outcome not confidently identified")
            question["review_flags"] = list(dict.fromkeys(question.get("review_flags", [])))

            seen_questions.add(question_key)
            standardized_questions.append(question)

        for index, question in enumerate(standardized_questions, start=1):
            question["question_number"] = str(index)
        paper["questions"] = standardized_questions

    if cleaned_payload.get("papers"):
        cleaned_payload["total_papers"] = len(cleaned_payload["papers"])
    cleaned_payload["review_candidates"] = review_candidates
    cleaned_payload["validation_summary"] = {
        "clean_questions": stats["kept"],
        "review_candidates": len(review_candidates),
        "accuracy_policy": "Only validated questions are eligible for generation; review candidates require human confirmation.",
    }
    return cleaned_payload, stats


def main() -> int:
    parser = argparse.ArgumentParser(description="Re-clean extracted question-paper JSON")
    parser.add_argument("path", help="JSON file or directory of JSON files to clean")
    parser.add_argument("--overwrite", action="store_true", help="Replace the original file")
    args = parser.parse_args()

    source = Path(args.path)
    if not source.exists():
        raise SystemExit(f"Path not found: {source}")

    for json_file in _iter_json_files(source):
        payload = json.loads(json_file.read_text(encoding="utf-8"))
        cleaned_payload, stats = _clean_payload(payload)

        if args.overwrite:
            output_file = json_file
        else:
            output_file = json_file.with_name(f"{json_file.stem}_recleaned.json")

        output_file.write_text(json.dumps(cleaned_payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(
            f"{json_file.name}: kept={stats['kept']} dropped={stats['dropped']} changed={stats['changed']} -> {output_file.name}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())