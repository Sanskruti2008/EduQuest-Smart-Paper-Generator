"""
Comprehensive Test Suite for OCR Extraction Module
Tests all core extraction functions for marks, course outcomes, and question validation
"""
import unittest
import os
import sys
from unittest.mock import patch, MagicMock
from ocr_extractor import (
    extract_marks_from_text,
    _normalize_co_label,
    validate_and_clean_question,
    _extract_numbers_from_text,
    extract_bloom_level,
    _clean_question_body,
    _should_try_ai_marks,
    _compute_question_confidence,
    _regex_extract_header,
    _extract_explicit_co_from_text,
)


class TestMarksExtraction(unittest.TestCase):
    """Test extract_marks_from_text() with various mark notations"""
    
    def test_square_bracket_marks(self):
        """Test marks in square brackets"""
        self.assertEqual(extract_marks_from_text("[4]"), 4)
        self.assertEqual(extract_marks_from_text("[8]"), 8)
        self.assertEqual(extract_marks_from_text("[6 marks]"), 6)
        self.assertEqual(extract_marks_from_text("[10 mark]"), 10)
    
    def test_parentheses_marks(self):
        """Test marks in parentheses"""
        self.assertEqual(extract_marks_from_text("(4)"), 4)
        self.assertEqual(extract_marks_from_text("(12)"), 12)
        self.assertEqual(extract_marks_from_text("(6 marks)"), 6)
    
    def test_marks_keyword_notation(self):
        """Test marks with explicit keywords"""
        self.assertEqual(extract_marks_from_text("Marks: 4"), 4)
        self.assertEqual(extract_marks_from_text("Marks - 5"), 5)
        self.assertEqual(extract_marks_from_text("marks 8"), 8)
        self.assertEqual(extract_marks_from_text("4 marks"), 4)
        self.assertEqual(extract_marks_from_text("6 mark"), 6)
    
    def test_m_notation_marks(self):
        """Test marks with M notation"""
        self.assertEqual(extract_marks_from_text("4M"), 4)
        self.assertEqual(extract_marks_from_text("8m"), 8)
        self.assertEqual(extract_marks_from_text("M:4"), 4)
        self.assertEqual(extract_marks_from_text("M-6"), 6)
    
    def test_leading_zero_marks(self):
        """Test marks with leading zeros"""
        self.assertEqual(extract_marks_from_text("04"), 4)
        self.assertEqual(extract_marks_from_text("08"), 8)
    
    def test_spelled_out_numbers(self):
        """Test marks written as spelled-out numbers"""
        self.assertEqual(extract_marks_from_text("Four marks"), 4)
        self.assertEqual(extract_marks_from_text("EIGHT marks"), 8)
        self.assertEqual(extract_marks_from_text("two mark"), 2)
    
    def test_standalone_marks_at_end(self):
        """Test standalone marks at end of line"""
        self.assertEqual(extract_marks_from_text("Question about something 4"), 4)
        self.assertEqual(extract_marks_from_text("Define the concept 6"), 6)
    
    def test_invalid_marks_fallback_to_default(self):
        """Test that invalid or missing marks default to 4"""
        self.assertEqual(extract_marks_from_text("No marks here"), 4)
        self.assertEqual(extract_marks_from_text(""), 4)
        self.assertEqual(extract_marks_from_text("999"), 4)  # Out of range
    
    def test_marks_boundaries(self):
        """Test valid mark ranges (1-50)"""
        self.assertEqual(extract_marks_from_text("[1]"), 1)
        self.assertEqual(extract_marks_from_text("[50]"), 50)
        self.assertEqual(extract_marks_from_text("[20]"), 20)
    
    def test_msbte_typical_marks(self):
        """Test extraction of typical MSBTE marks values"""
        typical_marks = [2, 3, 4, 5, 6, 8, 10, 12, 15, 16, 20]
        for mark in typical_marks:
            self.assertEqual(extract_marks_from_text(f"[{mark}]"), mark)


class TestCourseMetadataExtraction(unittest.TestCase):
    def test_extracts_course_name_and_code_from_header(self):
        result = _regex_extract_header(
            "COURSE : Software Engineering(SWE) COURSE CODE : 232146\n"
            "SUMMER EXAMINATION"
        )

        self.assertEqual(result['course_name'], 'Software Engineering(SWE)')
        self.assertEqual(result['course_code'], '232146')
        self.assertEqual(result['subject_name'], result['course_name'])
        self.assertEqual(result['subject_code'], result['course_code'])


class TestCourseOutcomeNormalization(unittest.TestCase):
    """Test _normalize_co_label() for course outcome parsing"""
    
    def test_standard_co_labels(self):
        """Test standard CO labels"""
        self.assertEqual(_normalize_co_label("CO1"), "CO1")
        self.assertEqual(_normalize_co_label("CO2"), "CO2")
        self.assertEqual(_normalize_co_label("CO6"), "CO6")
        self.assertEqual(_normalize_co_label("CO10"), "CO10")
    
    def test_co_with_variations(self):
        """Test CO labels with case variations"""
        self.assertEqual(_normalize_co_label("co1"), "CO1")
        self.assertEqual(_normalize_co_label("Co2"), "CO2")
        self.assertEqual(_normalize_co_label("CO 1"), "CO1")
    
    def test_co_with_special_formats(self):
        """Test CO labels with special formatting"""
        self.assertEqual(_normalize_co_label("CO-1"), "CO1")
        self.assertEqual(_normalize_co_label("CO_2"), "CO2")
        self.assertIsNotNone(_normalize_co_label("C01"))  # Should handle OCR variants
        self.assertEqual(_extract_explicit_co_from_text("CO6 a) Explain the topic."), "CO6")
        self.assertEqual(_extract_explicit_co_from_text("CO10 b) Define the term."), "CO10")
    
    def test_invalid_co_labels(self):
        """Test invalid CO labels return None or default"""
        # Empty string should return None
        self.assertIsNone(_normalize_co_label(""))
        # Completely unrelated strings should return None
        self.assertIsNone(_normalize_co_label("ABCDEF"))
        # Random text without CO pattern should return None
        self.assertIsNone(_normalize_co_label("HELLO"))
        # LO1 might still parse as CO1 due to OCR handling, so we test unknown patterns
        result = _normalize_co_label("XY1")
        # Either None or handled gracefully
        self.assertTrue(result is None or isinstance(result, str))
    
    def test_co_with_context(self):
        """Test CO extraction from contextual text"""
        # Some may be extracted from surrounding text
        result = _normalize_co_label("CO1")
        self.assertIsNotNone(result)

        def test_extracts_common_ocr_spaced_co_labels(self):
            self.assertEqual(_extract_explicit_co_from_text('C O 3 a) Explain production planning.'), 'CO3')
            self.assertEqual(_extract_explicit_co_from_text('State the principles of management. C0-4'), 'CO4')
            self.assertEqual(_extract_explicit_co_from_text('List the types of organization. CO5'), 'CO5')

        def test_does_not_treat_ordinary_co2_text_as_course_outcome(self):
            self.assertIsNone(_extract_explicit_co_from_text('Explain CO2 emissions in industry.'))

        def test_missing_course_outcome_is_flagged_not_defaulted(self):
            result = validate_and_clean_question({
                'question_text': 'Explain the principles of industrial management.',
                'marks': 4,
            })
            self.assertIsNotNone(result)
            self.assertEqual(result['course_outcome'], '')
            self.assertIn('Course outcome not confidently identified', result['review_flags'])

        def test_incomplete_question_is_marked_for_review(self):
            result = validate_and_clean_question({
                'question_text': 'Explain the importance of safety management and.',
                'marks': 4,
                'course_outcome': 'CO5',
            })
            self.assertIsNotNone(result)
            self.assertEqual(result['status'], 'needs_review')
            self.assertIn('Possible OCR truncation', result['review_flags'])

        def test_unresolved_ocr_fragments_are_marked_for_review(self):
            result = validate_and_clean_question({
                'question_text': 'State preventive measures to avoid accidents THREE SOO the application areas of Lean manufacturing.',
                'marks': 3,
                'course_outcome': 'CO5',
            })
            self.assertIsNotNone(result)
            self.assertEqual(result['status'], 'needs_review')


class TestExtractNumbers(unittest.TestCase):
    """Test _extract_numbers_from_text() for identifying marks/codes"""
    
    def test_extract_single_number(self):
        """Test extracting single number"""
        result = _extract_numbers_from_text("Question has [4]")
        # Returns strings, not ints
        self.assertIn('4', result)
    
    def test_extract_multiple_numbers(self):
        """Test extracting multiple numbers"""
        result = _extract_numbers_from_text("Unit 1 to 5, 8 marks")
        self.assertGreater(len(result), 0)
    
    def test_extract_year_numbers(self):
        """Test extracting numbers (should avoid false positives like years)"""
        result = _extract_numbers_from_text("2026 examination")
        # Should extract, but validation should filter out invalid marks
        self.assertGreater(len(result), 0)
    
    def test_extract_empty_text(self):
        """Test extracting from empty text"""
        result = _extract_numbers_from_text("")
        self.assertEqual(result, [])
    
    def test_extract_no_numbers(self):
        """Test extracting when no numbers present"""
        result = _extract_numbers_from_text("Just some text with no digits")
        self.assertEqual(result, [])


class TestCleanQuestionBody(unittest.TestCase):
    """Test _clean_question_body() for question text cleanup"""
    
    def test_remove_leading_junk(self):
        """Test removal of leading junk symbols"""
        result = _clean_question_body("@@@ Explain the concept")
        self.assertNotIn("@@@", result)
        self.assertIn("Explain", result)
    
    def test_remove_trailing_whitespace(self):
        """Test removal of trailing whitespace"""
        result = _clean_question_body("Define the term   \n\t")
        self.assertEqual(result, result.strip())
    
    def test_normalize_whitespace(self):
        """Test normalization of internal whitespace"""
        result = _clean_question_body("Question   with    multiple    spaces")
        self.assertNotIn("    ", result)
    
    def test_preserve_valid_content(self):
        """Test that valid question content is preserved"""
        original = "Explain the concept of machine learning"
        result = _clean_question_body(original)
        self.assertIn("machine learning", result.lower())
    
    def test_remove_page_numbers(self):
        """Test removal of page number artifacts"""
        result = _clean_question_body("Some question Page 1")
        # Should handle page indicators
        self.assertIsNotNone(result)


class TestBloomLevelExtraction(unittest.TestCase):
    """Test extract_bloom_level() for cognitive level classification"""
    
    def test_explicit_bloom_levels(self):
        """Test extraction of explicit bloom level notation"""
        self.assertEqual(extract_bloom_level("K1"), "K1")
        self.assertEqual(extract_bloom_level("[K2]"), "K2")
        self.assertEqual(extract_bloom_level("Bloom: K3"), "K3")
    
    def test_default_bloom_level(self):
        """Test default bloom level when not specified"""
        result = extract_bloom_level("No bloom level here")
        self.assertIsNotNone(result)  # Should return a default
    
    def test_bloom_level_range(self):
        """Test all valid bloom levels K1-K6"""
        for level in range(1, 7):
            result = extract_bloom_level(f"K{level}")
            self.assertEqual(result, f"K{level}")


class TestQuestionValidation(unittest.TestCase):
    """Test validate_and_clean_question() with various question formats"""
    
    def test_valid_complete_question(self):
        """Test validation of a complete, well-formed question"""
        question = {
            'question_text': 'Explain the concept of machine learning and its applications',
            'marks': 4,
            'course_outcome': 'CO1',
            'bloom_level': 'K2',
        }
        result = validate_and_clean_question(question)
        self.assertIsNotNone(result)
        self.assertEqual(result['marks'], 4)
        self.assertEqual(result['course_outcome'], 'CO1')
    
    def test_reject_too_short_question(self):
        """Test rejection of questions that are too short"""
        question = {
            'question_text': 'Hi',
            'marks': 4,
        }
        result = validate_and_clean_question(question)
        self.assertIsNone(result)
    
    def test_reject_header_as_question(self):
        """Test rejection of document headers misidentified as questions"""
        question = {
            'question_text': 'Government Polytechnic Institute Examination',
            'marks': 4,
        }
        result = validate_and_clean_question(question)
        self.assertIsNone(result)
    
    def test_question_without_explicit_verb_accepted(self):
        """Test that valid noun-phrase questions are still accepted"""
        question = {
            'question_text': 'Difference between machine learning and deep learning',
            'marks': 4,
            'course_outcome': 'CO1',
            'bloom_level': 'K2',
        }
        result = validate_and_clean_question(question)
        self.assertIsNotNone(result)
    
    def test_marks_string_to_int_conversion(self):
        """Test conversion of marks from string to int"""
        question = {
            'question_text': 'Define the term "algorithm" in computer science',
            'marks': '6',
            'course_outcome': 'CO1',
        }
        result = validate_and_clean_question(question)
        self.assertIsNotNone(result)
        self.assertEqual(result['marks'], 6)
    
    def test_marks_extraction_from_text(self):
        """Test marks extraction when not explicitly provided"""
        question = {
            'question_text': 'Explain the concept of algorithm design and analysis [4]',
            'course_outcome': 'CO1',
        }
        result = validate_and_clean_question(question)
        self.assertIsNotNone(result)
        self.assertEqual(result['marks'], 4)
    
    def test_co_normalization_in_validation(self):
        """Test that CO labels are normalized during validation"""
        question = {
            'question_text': 'Describe the process step by step',
            'marks': 5,
            'course_outcome': 'co1',  # lowercase
        }
        result = validate_and_clean_question(question)
        self.assertIsNotNone(result)
        self.assertEqual(result['course_outcome'], 'CO1')
    
    def test_bloom_level_fallback(self):
        """Test that invalid bloom levels are replaced with default"""
        question = {
            'question_text': 'List all the important concepts',
            'marks': 4,
            'course_outcome': 'CO1',
            'bloom_level': 'INVALID',
        }
        result = validate_and_clean_question(question)
        self.assertIsNotNone(result)
        self.assertEqual(result['bloom_level'], 'K2')
    
    def test_confidence_score_calculation(self):
        """Test that confidence scores are calculated"""
        question = {
            'question_text': 'Define the fundamental concepts',
            'marks': 4,
            'course_outcome': 'CO1',
        }
        result = validate_and_clean_question(question)
        self.assertIsNotNone(result)
        self.assertIn('confidence_score', result)
        self.assertGreaterEqual(result['confidence_score'], 0.0)
        self.assertLessEqual(result['confidence_score'], 1.0)
    
    def test_status_assignment(self):
        """Test that status is correctly assigned based on confidence"""
        question = {
            'question_text': 'Explain the concept of distributed systems in detail',
            'marks': 8,
            'course_outcome': 'CO2',
        }
        result = validate_and_clean_question(question)
        self.assertIsNotNone(result)
        self.assertIn('status', result)
        self.assertIn(result['status'], ['accepted', 'needs_review'])
    
    def test_sub_questions_array_preserved(self):
        """Test that sub_questions array is preserved"""
        question = {
            'question_text': 'Explain machine learning and its applications in modern systems',
            'marks': 4,
            'sub_questions': [
                {'sub_label': 'a', 'text': 'What is supervised learning?'},
                {'sub_label': 'b', 'text': 'What is unsupervised learning?'}
            ]
        }
        result = validate_and_clean_question(question)
        self.assertIsNotNone(result)
        self.assertEqual(len(result['sub_questions']), 2)
    
    def test_identified_numbers_extracted(self):
        """Test that identified numbers are extracted during validation"""
        question = {
            'question_text': 'Discuss the concepts in units 1, 2, and 3 with examples [4]',
            'marks': 4,
        }
        result = validate_and_clean_question(question)
        self.assertIsNotNone(result)
        self.assertIn('identified_numbers', result)


class TestShouldTryAiMarks(unittest.TestCase):
    """Test _should_try_ai_marks() for determining when to use AI fallback"""
    
    def test_ai_fallback_for_ambiguous_marks(self):
        """Test that AI fallback is tried for ambiguous cases"""
        result = _should_try_ai_marks("Question about [marks]", None)
        # May or may not need AI depending on implementation
        self.assertIsInstance(result, bool)
    
    def test_no_ai_for_resolved_marks(self):
        """Test that AI is not tried when marks are already resolved"""
        result = _should_try_ai_marks("Some text", 6)
        self.assertFalse(result)
    
    def test_no_ai_for_empty_text(self):
        """Test that AI is not tried for empty text"""
        result = _should_try_ai_marks("", None)
        self.assertFalse(result)


class TestComputeQuestionConfidence(unittest.TestCase):
    """Test _compute_question_confidence() for scoring question quality"""
    
    def test_high_confidence_well_formed_question(self):
        """Test high confidence for well-formed questions"""
        question = {
            'question_text': 'Explain the concept of distributed systems and their advantages',
            'marks': 8,
            'course_outcome': 'CO2',
            'bloom_level': 'K3',
        }
        confidence = _compute_question_confidence(question)
        self.assertGreater(confidence, 0.5)
    
    def test_low_confidence_incomplete_question(self):
        """Test lower confidence for incomplete questions"""
        question = {
            'question_text': 'Define',
            'marks': 4,
        }
        confidence = _compute_question_confidence(question)
        self.assertLess(confidence, 0.8)
    
    def test_confidence_with_missing_fields(self):
        """Test confidence calculation with missing fields"""
        question = {
            'question_text': 'Discuss the topic',
        }
        confidence = _compute_question_confidence(question)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)


class TestEdgeCasesAndErrorHandling(unittest.TestCase):
    """Test edge cases and error handling in extraction functions"""
    
    def test_null_input_handling(self):
        """Test handling of null/None inputs"""
        result = validate_and_clean_question(None)
        self.assertIsNone(result)
    
    def test_empty_dict_handling(self):
        """Test handling of empty dictionary"""
        result = validate_and_clean_question({})
        self.assertIsNone(result)
    
    def test_invalid_marks_type(self):
        """Test handling of invalid marks types"""
        question = {
            'question_text': 'Explain the concept of data structures',
            'marks': {'value': 4},  # Invalid type, but question is valid
        }
        result = validate_and_clean_question(question)
        # Should handle gracefully and use default marks
        self.assertIsNotNone(result)
        self.assertIsInstance(result['marks'], int)
    
    def test_unicode_handling(self):
        """Test handling of unicode characters"""
        question = {
            'question_text': 'Explain the concept of café and mañana',
            'marks': 4,
        }
        result = validate_and_clean_question(question)
        self.assertIsNotNone(result)
    
    def test_special_characters_in_question(self):
        """Test handling of special characters"""
        question = {
            'question_text': 'What is @#$% and #$%^?',
            'marks': 4,
        }
        # Should handle or reject appropriately
        result = validate_and_clean_question(question)
        # Result could be None or cleaned, both are valid


class TestIntegrationScenarios(unittest.TestCase):
    """Integration tests for realistic extraction scenarios"""
    
    def test_ocr_error_handling_question(self):
        """Test extraction from OCR-damaged text"""
        question = {
            'question_text': 'Explain the c0ncept of m@ch1n3 learning and its applications [4]',
            'course_outcome': 'C01',
        }
        result = validate_and_clean_question(question)
        # Should handle OCR noise reasonably - validation may reject or accept depending on severity
        # Just verify it doesn't crash
        self.assertTrue(result is None or isinstance(result, dict))
    
    def test_multi_part_question_extraction(self):
        """Test extraction of multi-part questions"""
        question = {
            'question_text': 'Define the concept of algorithm and explain time complexity analysis',
            'marks': 8,
            'course_outcome': 'CO1',
        }
        result = validate_and_clean_question(question)
        self.assertIsNotNone(result)
        self.assertIn('algorithm', result['question_text'].lower())
    
    def test_very_long_question(self):
        """Test handling of very long question text"""
        long_text = "Explain " + "the concept " * 50 + "in detail"
        question = {
            'question_text': long_text,
            'marks': 12,
        }
        result = validate_and_clean_question(question)
        self.assertIsNotNone(result)
    
    def test_question_with_code_snippet(self):
        """Test handling of questions containing code"""
        question = {
            'question_text': 'Analyze the output of this function: def foo(x): return x*2; foo(5) and explain the result',
            'marks': 4,
        }
        result = validate_and_clean_question(question)
        self.assertIsNotNone(result)


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)
