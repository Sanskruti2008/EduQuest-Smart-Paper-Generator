"""
Test suite for extraction enhancements module
Tests spelling correction, grammar validation, and enhanced marks extraction
"""
import unittest
from extraction_enhancements import (
    correct_spelling,
    GrammarValidator,
    extract_marks_enhanced,
    validate_marks_extraction,
    enhance_extracted_question,
)


class TestSpellingCorrection(unittest.TestCase):
    """Test spelling correction functionality"""
    
    def test_common_misspellings(self):
        """Test correction of common OCR misspellings"""
        test_cases = [
            ("teh concept", "the concept"),
            ("recieve the data", "receive the data"),
            ("algoritm implementation", "algorithm implementation"),
            ("datastructure design", "data structure design"),
        ]
        for misspelled, expected in test_cases:
            result = correct_spelling(misspelled)
            self.assertIn(expected.split()[0].lower(), result.lower())
    
    def test_multiple_errors(self):
        """Test correction of multiple errors"""
        text = "teh algoritm for datastructure implementaton"
        corrected = correct_spelling(text)
        # Should contain corrections
        self.assertIsNotNone(corrected)
        self.assertGreater(len(corrected), 0)
    
    def test_no_errors(self):
        """Test that correctly spelled text is unchanged"""
        text = "Explain the algorithm implementation"
        corrected = correct_spelling(text)
        self.assertEqual(corrected, text)
    
    def test_empty_input(self):
        """Test handling of empty input"""
        self.assertEqual(correct_spelling(""), "")
        self.assertEqual(correct_spelling(None), None)
    
    def test_technical_terms(self):
        """Test that technical terms are recognized"""
        text = "The database uses polymorphism"
        corrected = correct_spelling(text)
        self.assertIn("database", corrected.lower())
        self.assertIn("polymorphism", corrected.lower())


class TestGrammarValidation(unittest.TestCase):
    """Test grammar validation functionality"""
    
    def test_capitalization(self):
        """Test capitalization correction"""
        text = "explain the concept"
        corrected, issues = GrammarValidator.validate_question_grammar(text)
        self.assertTrue(corrected[0].isupper())
    
    def test_ending_punctuation(self):
        """Test addition of ending punctuation"""
        text = "Explain the concept"
        corrected, issues = GrammarValidator.validate_question_grammar(text)
        self.assertTrue(corrected.endswith(('.', '?', '!')))
    
    def test_grammar_issues_detection(self):
        """Test detection of grammar issues"""
        text = "explain the algorithm"
        corrected, issues = GrammarValidator.validate_question_grammar(text)
        self.assertIsInstance(issues, list)
        self.assertGreater(len(issues), 0)
    
    def test_well_formed_question(self):
        """Test that well-formed questions are recognized"""
        text = "Explain the concept of recursion in detail."
        corrected, issues = GrammarValidator.validate_question_grammar(text)
        # Should have minimal issues
        self.assertIsInstance(issues, list)
    
    def test_incomplete_sentence(self):
        """Test detection of incomplete sentences"""
        text = "The concept"
        corrected, issues = GrammarValidator.validate_question_grammar(text)
        # Should detect incomplete structure
        self.assertGreater(len(issues), 0)
    
    def test_subject_verb_agreement(self):
        """Test subject-verb agreement validation"""
        text = "Data are stored in database."
        corrected, issues = GrammarValidator.validate_question_grammar(text)
        # Validate returns tuple
        self.assertIsInstance(corrected, str)
        self.assertIsInstance(issues, list)


class TestEnhancedMarksExtraction(unittest.TestCase):
    """Test enhanced marks extraction"""
    
    def test_bracket_notation(self):
        """Test extraction from bracket notation"""
        test_cases = [
            ("Explain the concept [4]", 4),
            ("Define the term [6]", 6),
            ("Describe [12]", 12),
        ]
        for text, expected_marks in test_cases:
            marks = extract_marks_enhanced(text)
            self.assertEqual(marks, expected_marks)
    
    def test_parentheses_notation(self):
        """Test extraction from parentheses"""
        test_cases = [
            ("Question (4)", 4),
            ("Item (8 marks)", 8),
        ]
        for text, expected_marks in test_cases:
            marks = extract_marks_enhanced(text)
            self.assertEqual(marks, expected_marks)
    
    def test_keyword_notation(self):
        """Test extraction with keywords"""
        test_cases = [
            ("Marks: 4", 4),
            ("4 marks", 4),
            ("M:6", 6),
        ]
        for text, expected_marks in test_cases:
            marks = extract_marks_enhanced(text)
            self.assertEqual(marks, expected_marks)
    
    def test_section_header_notation(self):
        """Test extraction from section headers like 'Q1: Attempt any 3 (12 marks)'."""
        text = "Q1: Attempt any 3 (12 marks)"
        marks = extract_marks_enhanced(text)
        self.assertEqual(marks, 12)  # Explicit 12 marks takes precedence
    
    def test_spelled_out_numbers(self):
        """Test extraction of spelled-out marks"""
        test_cases = [
            ("Four marks", 4),
            ("Six marks", 6),
            ("Twelve marks", 12),
        ]
        for text, expected_marks in test_cases:
            marks = extract_marks_enhanced(text)
            self.assertEqual(marks, expected_marks)
    
    def test_msbte_typical_values(self):
        """Test extraction of MSBTE typical marks"""
        typical_marks = [2, 3, 4, 5, 6, 8, 10, 12, 15, 16, 20]
        for mark in typical_marks:
            text = f"Question [{mark}]"
            extracted = extract_marks_enhanced(text)
            self.assertEqual(extracted, mark)
    
    def test_default_fallback(self):
        """Test default fallback to 4"""
        text = "No marks specified anywhere"
        marks = extract_marks_enhanced(text)
        self.assertEqual(marks, 4)


class TestMarksValidation(unittest.TestCase):
    """Test marks validation and confidence scoring"""
    
    def test_valid_marks_high_confidence(self):
        """Test validation of valid marks"""
        text = "Explain [4]"
        marks, confidence = validate_marks_extraction(text, 4)
        self.assertEqual(marks, 4)
        self.assertGreater(confidence, 0.5)
    
    def test_invalid_marks_correction(self):
        """Test correction of invalid marks"""
        text = "Explain the concept"
        marks, confidence = validate_marks_extraction(text, 7)
        # Should return closest MSBTE value
        self.assertIn(marks, [6, 8])
    
    def test_confidence_score_range(self):
        """Test confidence scores are in valid range"""
        text = "Question [5]"
        marks, confidence = validate_marks_extraction(text, 5)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
    
    def test_msbte_marks_higher_confidence(self):
        """Test that MSBTE marks get higher confidence"""
        text = "Explain [4]"
        marks1, conf1 = validate_marks_extraction(text, 4)
        marks2, conf2 = validate_marks_extraction(text, 7)
        # MSBTE marks should have higher confidence
        self.assertGreaterEqual(conf1, conf2)


class TestEnhancementIntegration(unittest.TestCase):
    """Test integrated enhancement of questions"""
    
    def test_enhance_complete_question(self):
        """Test enhancement of a complete question"""
        question = {
            'question_text': 'teh algoritm for datastructure explain the concept',
            'marks': '6',
            'course_outcome': 'CO1',
        }
        enhanced = enhance_extracted_question(question)
        
        # Check enhancements were applied
        self.assertTrue(enhanced.get('enhancements_applied', False))
        # Check spelling was corrected
        self.assertNotIn('teh', enhanced['question_text'])
        self.assertNotIn('algoritm', enhanced['question_text'])
    
    def test_enhance_marks_extraction(self):
        """Test marks extraction during enhancement"""
        question = {
            'question_text': 'Explain the concept [4]',
            'course_outcome': 'CO1',
        }
        enhanced = enhance_extracted_question(question)
        
        self.assertEqual(enhanced['marks'], 4)
        self.assertTrue(enhanced.get('enhancements_applied', False))
    
    def test_enhance_grammar_validation(self):
        """Test grammar validation during enhancement"""
        question = {
            'question_text': 'explain the algorithm',
            'marks': 4,
            'course_outcome': 'CO1',
        }
        enhanced = enhance_extracted_question(question)
        
        # Grammar should be checked
        self.assertTrue(enhanced.get('grammar_checked', False))
        # Should be capitalized
        self.assertTrue(enhanced['question_text'][0].isupper())
    
    def test_enhance_with_metadata(self):
        """Test that enhancement adds metadata"""
        question = {
            'question_text': 'Define the algorithm [4]',
            'marks': 4,
            'course_outcome': 'CO1',
        }
        enhanced = enhance_extracted_question(question)
        
        # Check metadata
        self.assertIn('enhancements_applied', enhanced)
        self.assertIn('enhancement_timestamp', enhanced)
    
    def test_error_handling_in_enhancement(self):
        """Test graceful error handling"""
        question = {
            'question_text': 'Explain',  # Very short, might cause issues
            'marks': 'invalid',
            'course_outcome': 'CO1',
        }
        # Should not crash
        try:
            enhanced = enhance_extracted_question(question)
            self.assertIsNotNone(enhanced)
        except Exception as e:
            self.fail(f"Enhancement raised unexpected exception: {e}")


class TestRealWorldScenarios(unittest.TestCase):
    """Test real-world OCR extraction scenarios"""
    
    def test_ocr_damaged_question(self):
        """Test extraction from OCR-damaged text"""
        question = {
            'question_text': 'Exp1a1n th€ c0nc€pt 0f m@ch1n3 l€@rn1ng [4]',
            'course_outcome': 'CO1',
        }
        enhanced = enhance_extracted_question(question)
        # Should attempt to improve
        self.assertIsNotNone(enhanced)
        self.assertTrue(enhanced.get('enhancements_applied', False))
    
    def test_multi_part_question_enhancement(self):
        """Test enhancement of multi-part questions"""
        question = {
            'question_text': 'Define algoritm and explain complexity analisis (8)',
            'course_outcome': 'CO2',
        }
        enhanced = enhance_extracted_question(question)
        
        # Spelling should be corrected
        self.assertNotIn('algoritm', enhanced['question_text'])
        self.assertNotIn('analisis', enhanced['question_text'])
        # Marks should be extracted
        self.assertEqual(enhanced['marks'], 8)
    
    def test_question_with_unusual_marks_notation(self):
        """Test questions with unusual mark notations"""
        question = {
            'question_text': 'Explain the concept - Marks: Five',
            'course_outcome': 'CO1',
        }
        enhanced = enhance_extracted_question(question)
        
        # Should extract "five" as 5
        self.assertEqual(enhanced['marks'], 5)
    
    def test_long_complex_question(self):
        """Test enhancement of long complex questions"""
        question = {
            'question_text': 'Describe in detail teh algoritm for implementing datastructure with proper explaination of all components [12]',
            'course_outcome': 'CO2',
        }
        enhanced = enhance_extracted_question(question)
        
        # Spelling should be corrected
        self.assertNotIn('teh', enhanced['question_text'])
        self.assertNotIn('algoritm', enhanced['question_text'])
        self.assertNotIn('datastructure', enhanced['question_text'])
        self.assertNotIn('explaination', enhanced['question_text'])
        # Marks should be 12
        self.assertEqual(enhanced['marks'], 12)


if __name__ == '__main__':
    unittest.main(verbosity=2)
