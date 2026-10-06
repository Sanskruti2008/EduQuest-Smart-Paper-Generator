import unittest
from unittest.mock import patch

from ocr_extractor import (
    _aggressive_fallback_split,
    _clean_question_body,
    extract_text_from_pdf,
    validate_and_clean_question,
)


class OcrCleanupAccuracyTest(unittest.TestCase):
    def test_collapses_repeated_ocr_function_words(self):
        cleaned = _clean_question_body(
            "Explain the the the role of management in a service industry."
        )
        self.assertEqual(
            cleaned,
            "Explain the role of management in a service industry.",
        )

    def test_preserves_repeated_meaningful_words(self):
        cleaned = _clean_question_body("Compare very very large data structures")
        self.assertIn("very very", cleaned)

    def test_repairs_garbled_importance_question(self):
        question = validate_and_clean_question({
            "question_text": "The importance management. o @ Stale s i &.",
            "marks": 4,
        })
        self.assertIsNotNone(question)
        self.assertEqual(question["question_text"], "State the importance of management.")
        self.assertEqual(question["status"], "needs_review")

    def test_repairs_common_glued_and_misspelled_words(self):
        cleaned = _clean_question_body(
            "Define the markeling management. Whatis meant by fourterms used in planningany."
        )
        self.assertEqual(
            cleaned,
            "Define the marketing management. What is meant by four terms used in planning any.",
        )

    def test_ocr_symbols_prevent_automatic_acceptance(self):
        question = validate_and_clean_question({
            "question_text": "Explain the material resource planning with ©.",
            "marks": 4,
            "course_outcome": "CO5",
        })
        self.assertIsNotNone(question)
        self.assertEqual(question["status"], "needs_review")
        self.assertIn("OCR noise requires review", question["review_flags"])

    def test_invalid_candidates_are_preserved_for_review(self):
        from reclean_extracted_json import _clean_payload

        cleaned, _ = _clean_payload({
            "papers": [{"questions": [{"question_text": "noise only"}]}]
        })
        self.assertEqual(cleaned["validation_summary"]["clean_questions"], 0)
        self.assertEqual(len(cleaned["review_candidates"]), 1)

    def test_review_questions_are_excluded_from_clean_bank(self):
        from reclean_extracted_json import _clean_payload

        cleaned, _ = _clean_payload({
            "papers": [{"questions": [{
                "question_text": "Explain the material resource planning with ©.",
                "marks": 4,
                "course_outcome": "CO5",
            }]}]
        })
        self.assertEqual(cleaned["papers"][0]["questions"], [])
        self.assertEqual(len(cleaned["review_candidates"]), 1)

    def test_preserves_question_boundary_after_punctuation(self):
        cleaned = _clean_question_body(
            "List different types of organization.\nExplain line and staff structure."
        )
        self.assertIn("organization.\nExplain", cleaned)

    def test_marks_truncated_ocr_as_needs_review(self):
        question = validate_and_clean_question({
            "question_text": "Explain the Job batch production s stom necose.",
            "marks": 4,
            "course_outcome": "CO1",
        })
        self.assertIsNotNone(question)
        self.assertEqual(question["status"], "needs_review")

    def test_grammar_stage_does_not_restore_duplicate_articles(self):
        question = validate_and_clean_question({
            "question_text": "Explain the the role of management.",
            "marks": 4,
            "course_outcome": "CO1",
        })
        self.assertIsNotNone(question)
        self.assertNotIn("the the", question["question_text"].lower())

    def test_validation_does_not_mutate_parser_input(self):
        question = {
            "question_text": "Explain the the role of management.",
            "marks": 4,
            "review_flags": [],
        }
        validate_and_clean_question(question)
        self.assertEqual(question["question_text"], "Explain the the role of management.")
        self.assertEqual(question["review_flags"], [])

    def test_validation_normalizes_malformed_metadata(self):
        question = validate_and_clean_question({
            "question_text": "Explain the role of management.",
            "marks": True,
            "bloom_level": None,
        })
        self.assertIsNotNone(question)
        self.assertEqual(question["marks"], 4)
        self.assertEqual(question["bloom_level"], "K2")

    def test_splits_damaged_question_stems(self):
        split = _aggressive_fallback_split(
            "En list any four advantages of jot stock companies. "
            "Expiain the functions of cooperative organizations. "
            "fiate between job and batch production."
        )
        parts = [part for part in split.splitlines() if part.strip()]
        self.assertEqual(len(parts), 3)
        self.assertIn("enlist", parts[0].lower())
        self.assertIn("explain", parts[1].lower())
        self.assertIn("differentiate", parts[2].lower())

    @patch("ocr_extractor._ocr_with_config", side_effect=["Q1\nDefine the term\nQ2\nList two types\n", ""])
    @patch("ocr_extractor.preprocess_image_for_ocr", return_value="processed")
    @patch("ocr_extractor.convert_from_path", return_value=["page"])
    def test_fast_ocr_prefers_layout_aware_psm4(self, _convert, _preprocess, ocr):
        extract_text_from_pdf("paper.pdf", fast_mode=True)
        self.assertEqual(ocr.call_args_list[0].kwargs["psm"], 4)


if __name__ == "__main__":
    unittest.main()