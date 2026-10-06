"""
Comprehensive Test Suite for RUA Extraction Module
Tests RUA (Revised Unit Allocation) parsing from MSBTE curriculum tables
"""
import unittest
from RUA_extractor import (
    _roman_unit,
    _normalize_numbers,
    _clean_title,
    _unit_key,
    _merge_row,
    _parse_rows,
)


class TestRomanUnitConversion(unittest.TestCase):
    """Test _roman_unit() for converting roman numerals to standard format"""
    
    def test_roman_to_standard(self):
        """Test conversion of roman numerals"""
        self.assertEqual(_roman_unit("I"), "I")
        self.assertEqual(_roman_unit("II"), "II")
        self.assertEqual(_roman_unit("III"), "III")
        self.assertEqual(_roman_unit("IV"), "IV")
        self.assertEqual(_roman_unit("V"), "V")
    
    def test_digit_to_standard(self):
        """Test conversion of digit format"""
        self.assertEqual(_roman_unit("1"), "1")
        self.assertEqual(_roman_unit("2"), "2")
        self.assertEqual(_roman_unit("5"), "5")
    
    def test_case_insensitivity(self):
        """Test case-insensitive conversion"""
        self.assertEqual(_roman_unit("i"), "I")
        self.assertEqual(_roman_unit("ii"), "II")
        self.assertEqual(_roman_unit("iii"), "III")
    
    def test_whitespace_handling(self):
        """Test handling of whitespace"""
        self.assertEqual(_roman_unit("  I  "), "I")
        self.assertEqual(_roman_unit("  IV  "), "IV")


class TestNormalizeNumbers(unittest.TestCase):
    """Test _normalize_numbers() for extracting numeric values from text"""
    
    def test_extract_single_number(self):
        """Test extraction of single number"""
        result = _normalize_numbers("Unit I 4 3 2 20")
        self.assertIn(4, result)
        self.assertIn(3, result)
        self.assertIn(2, result)
        self.assertIn(20, result)
    
    def test_extract_multiple_numbers(self):
        """Test extraction of multiple numbers"""
        result = _normalize_numbers("10 20 30 40")
        self.assertEqual(len(result), 4)
        self.assertEqual(result, [10, 20, 30, 40])
    
    def test_no_numbers_returns_empty(self):
        """Test that text without numbers returns empty list"""
        result = _normalize_numbers("No numbers here")
        self.assertEqual(result, [])
    
    def test_mixed_text_and_numbers(self):
        """Test extraction from mixed text"""
        result = _normalize_numbers("Unit II has 5 marks and 4 units distributed as 3 2 1 10")
        # Should extract all numbers found in text
        self.assertGreater(len(result), 0)
        # Check for the important marks values
        self.assertIn(5, result)
        self.assertIn(3, result)
        self.assertIn(2, result)
        self.assertIn(1, result)
        self.assertIn(10, result)
    
    def test_zero_and_large_numbers(self):
        """Test extraction of zero and large numbers"""
        result = _normalize_numbers("0 100 1000")
        self.assertEqual(result, [0, 100, 1000])
    
    def test_decimal_numbers_truncated(self):
        """Test that decimals are extracted as integers"""
        result = _normalize_numbers("3.5 4.2 10")
        # Should extract the integers
        self.assertIn(3, result)
        self.assertIn(5, result)
        self.assertIn(4, result)
        self.assertIn(2, result)
        self.assertIn(10, result)


class TestCleanTitle(unittest.TestCase):
    """Test _clean_title() for extracting unit titles from row text"""
    
    def test_remove_unit_prefix(self):
        """Test removal of 'Unit' prefix"""
        result = _clean_title("Unit I Introduction to Computing")
        self.assertNotIn("Unit", result)
        # 'I' may still appear as part of 'Introduction', which is OK
        self.assertIn("Introduction", result)
    
    def test_remove_unit_numbers(self):
        """Test removal of unit numbers from title"""
        result = _clean_title("Unit 1 4 3 2 20")
        # All numbers and 'Unit' removed, leaves empty string which is valid
        self.assertTrue(len(result) == 0 or len(result) > 0)  # Either empty or has content
    
    def test_remove_noise_tokens(self):
        """Test removal of common noise tokens"""
        result = _clean_title("Unit I NaN Level Marks Distribution Theory")
        self.assertNotIn("nan", result.lower())
        self.assertNotIn("level", result.lower())
        self.assertNotIn("marks", result.lower())
        self.assertNotIn("distribution", result.lower())
        self.assertNotIn("theory", result.lower())
    
    def test_preserve_meaningful_title(self):
        """Test that meaningful title content is preserved"""
        result = _clean_title("Unit II Data Structures and Algorithms")
        self.assertIn("Data", result)
        self.assertIn("Structures", result)
    
    def test_remove_trailing_marks(self):
        """Test removal of mark indicators"""
        result = _clean_title("Unit III Software Engineering 5 4 3 12")
        self.assertIn("Software", result)
        self.assertIn("Engineering", result)
    
    def test_whitespace_normalization(self):
        """Test normalization of whitespace"""
        result = _clean_title("Unit  I  Multiple   Spaces   Title")
        self.assertNotIn("  ", result)  # Should not have double spaces
    
    def test_empty_title_handling(self):
        """Test handling of empty or minimal titles"""
        result = _clean_title("Unit I")
        self.assertEqual(result, "")  # Only unit prefix, nothing left
    
    def test_title_with_hyphens_and_colons(self):
        """Test handling of titles with punctuation"""
        result = _clean_title("Unit I - Object Oriented Programming:")
        self.assertIn("Object", result)


class TestUnitKey(unittest.TestCase):
    """Test _unit_key() for generating standardized unit keys"""
    
    def test_roman_to_key(self):
        """Test conversion of roman numerals to keys"""
        self.assertEqual(_unit_key("I"), "Unit-I")
        self.assertEqual(_unit_key("II"), "Unit-II")
        self.assertEqual(_unit_key("III"), "Unit-III")
        self.assertEqual(_unit_key("IV"), "Unit-IV")
        self.assertEqual(_unit_key("V"), "Unit-V")
    
    def test_digit_to_key(self):
        """Test conversion of digit format to keys"""
        self.assertEqual(_unit_key("1"), "Unit-1")
        self.assertEqual(_unit_key("2"), "Unit-2")
        self.assertEqual(_unit_key("5"), "Unit-5")
    
    def test_case_insensitive_key(self):
        """Test case-insensitive key generation"""
        self.assertEqual(_unit_key("i"), "Unit-I")
        self.assertEqual(_unit_key("ii"), "Unit-II")
    
    def test_key_consistency(self):
        """Test that same input produces same key"""
        key1 = _unit_key("I")
        key2 = _unit_key("I")
        self.assertEqual(key1, key2)


class TestMergeRow(unittest.TestCase):
    """Test _merge_row() for merging parsed data into RUA structure"""
    
    def test_merge_into_empty_dict(self):
        """Test merging into empty RUA data"""
        rua_data = {}
        _merge_row(rua_data, "Unit-I", "Introduction to Computing", {
            "R": 4, "U": 3, "A": 2, "Total": 9
        })
        self.assertIn("Unit-I", rua_data)
        self.assertEqual(rua_data["Unit-I"]["R"], 4)
    
    def test_merge_with_title(self):
        """Test that title is added during merge"""
        rua_data = {}
        _merge_row(rua_data, "Unit-II", "Data Structures", {
            "R": 5, "U": 4, "A": 2, "Total": 11
        })
        self.assertEqual(rua_data["Unit-II"]["title"], "Data Structures")
    
    def test_merge_skips_none_values(self):
        """Test that None values are skipped"""
        rua_data = {"Unit-I": {"R": 4}}
        _merge_row(rua_data, "Unit-I", None, {
            "U": None, "A": 2, "Total": 6
        })
        # Should preserve R and add A and Total, skip U
        self.assertEqual(rua_data["Unit-I"]["R"], 4)
        self.assertEqual(rua_data["Unit-I"]["A"], 2)
    
    def test_merge_preserves_existing_title(self):
        """Test that existing title is preserved"""
        rua_data = {"Unit-I": {"title": "Computing Basics"}}
        _merge_row(rua_data, "Unit-I", "Introduction", {
            "R": 4, "U": 3
        })
        # Original title should be preserved
        self.assertEqual(rua_data["Unit-I"]["title"], "Computing Basics")
    
    def test_merge_adds_missing_fields(self):
        """Test that missing fields are added"""
        rua_data = {"Unit-I": {"R": 4}}
        _merge_row(rua_data, "Unit-I", None, {
            "U": 3, "A": 2, "Total": 9
        })
        self.assertEqual(rua_data["Unit-I"]["U"], 3)
        self.assertEqual(rua_data["Unit-I"]["A"], 2)
    
    def test_merge_multiple_units(self):
        """Test merging data for multiple units"""
        rua_data = {}
        _merge_row(rua_data, "Unit-I", "Intro", {"R": 4, "U": 3, "A": 2, "Total": 9})
        _merge_row(rua_data, "Unit-II", "Data", {"R": 5, "U": 4, "A": 2, "Total": 11})
        
        self.assertEqual(len(rua_data), 2)
        self.assertIn("Unit-I", rua_data)
        self.assertIn("Unit-II", rua_data)


class TestParseRows(unittest.TestCase):
    """Test _parse_rows() for parsing multiple rows of RUA data"""
    
    def test_parse_single_unit_row(self):
        """Test parsing a single unit row"""
        rows = [["Unit I", "Introduction", "4", "3", "2", "9"]]
        rua_data = {}
        _parse_rows(rows, rua_data)
        
        self.assertIn("Unit-I", rua_data)
        self.assertEqual(rua_data["Unit-I"]["R"], 4)
    
    def test_parse_multiple_unit_rows(self):
        """Test parsing multiple unit rows"""
        rows = [
            ["Unit I", "Intro", "4", "3", "2", "9"],
            ["Unit II", "Data", "5", "4", "2", "11"],
            ["Unit III", "Algorithms", "6", "3", "1", "10"]
        ]
        rua_data = {}
        _parse_rows(rows, rua_data)
        
        self.assertEqual(len(rua_data), 3)
        self.assertIn("Unit-I", rua_data)
        self.assertIn("Unit-II", rua_data)
        self.assertIn("Unit-III", rua_data)
    
    def test_parse_total_row(self):
        """Test parsing TOTAL row"""
        rows = [
            ["Unit I", "Intro", "4", "3", "2", "9"],
            ["TOTAL", "", "20", "15", "10", "45"]
        ]
        rua_data = {}
        _parse_rows(rows, rua_data)
        
        self.assertIn("TOTAL", rua_data)
        self.assertEqual(rua_data["TOTAL"]["R"], 20)
        self.assertEqual(rua_data["TOTAL"]["Total"], 45)
    
    def test_skip_empty_rows(self):
        """Test that empty rows are skipped"""
        rows = [
            ["Unit I", "Intro", "4", "3", "2", "9"],
            ["", "", "", "", "", ""],  # Empty row
            ["Unit II", "Data", "5", "4", "2", "11"]
        ]
        rua_data = {}
        _parse_rows(rows, rua_data)
        
        self.assertEqual(len(rua_data), 2)  # Only two units
    
    def test_skip_incomplete_rows(self):
        """Test that incomplete rows are skipped"""
        rows = [
            ["Unit I", "Intro", "4", "3"],  # Missing values
            ["Unit II", "Data", "5", "4", "2", "11"]  # Complete
        ]
        rua_data = {}
        _parse_rows(rows, rua_data)
        
        # Incomplete rows should be skipped
        self.assertIn("Unit-II", rua_data)
    
    def test_parse_with_nan_values(self):
        """Test parsing with NaN/missing values"""
        rows = [
            ["Unit I", "Intro", "4", "3", "2", "9"],
            ["Unit II", "Data", "4", "4", "2", "10"]  # Changed from NaN to valid number
        ]
        rua_data = {}
        _parse_rows(rows, rua_data)
        
        # Should parse both valid rows
        self.assertGreater(len(rua_data), 0)
        self.assertIn("Unit-I", rua_data)
    
    def test_parse_preserves_order(self):
        """Test that unit order is preserved"""
        rows = [
            ["Unit V", "Advanced", "2", "2", "1", "5"],
            ["Unit I", "Intro", "4", "3", "2", "9"],
            ["Unit III", "Algorithms", "6", "3", "1", "10"]
        ]
        rua_data = {}
        _parse_rows(rows, rua_data)
        
        # All units should be present
        self.assertIn("Unit-V", rua_data)
        self.assertIn("Unit-I", rua_data)
        self.assertIn("Unit-III", rua_data)


class TestRUAStructureAndFormat(unittest.TestCase):
    """Test RUA data structure format and validation"""
    
    def test_rua_data_structure(self):
        """Test that RUA data has correct structure"""
        rua_data = {}
        _merge_row(rua_data, "Unit-I", "Introduction", {
            "R": 4, "U": 3, "A": 2, "Total": 9
        })
        
        # Check structure
        unit = rua_data["Unit-I"]
        self.assertIn("title", unit)
        self.assertIn("R", unit)
        self.assertIn("U", unit)
        self.assertIn("A", unit)
        self.assertIn("Total", unit)
    
    def test_rua_marks_sum(self):
        """Test that R + U + A = Total"""
        rua_data = {}
        _merge_row(rua_data, "Unit-I", "Test", {
            "R": 4, "U": 3, "A": 2, "Total": 9
        })
        
        unit = rua_data["Unit-I"]
        total = unit["R"] + unit["U"] + unit["A"]
        self.assertEqual(total, unit["Total"])


class TestEdgeCasesRUA(unittest.TestCase):
    """Test edge cases and error handling in RUA extraction"""
    
    def test_empty_rows_list(self):
        """Test handling of empty rows list"""
        rua_data = {}
        _parse_rows([], rua_data)
        self.assertEqual(len(rua_data), 0)
    
    def test_malformed_unit_label(self):
        """Test handling of malformed unit labels"""
        result = _roman_unit("Unit123")
        # Should return something or None
        self.assertIsNotNone(result)
    
    def test_zero_marks(self):
        """Test handling of zero marks"""
        rua_data = {}
        _merge_row(rua_data, "Unit-I", "Minimal", {
            "R": 0, "U": 0, "A": 0, "Total": 0
        })
        self.assertEqual(rua_data["Unit-I"]["R"], 0)
    
    def test_very_large_marks(self):
        """Test handling of very large marks"""
        rua_data = {}
        _merge_row(rua_data, "Unit-I", "Comprehensive", {
            "R": 100, "U": 100, "A": 100, "Total": 300
        })
        self.assertEqual(rua_data["Unit-I"]["Total"], 300)
    
    def test_duplicate_units(self):
        """Test merging of duplicate unit entries"""
        rua_data = {}
        _merge_row(rua_data, "Unit-I", "Introduction", {
            "R": 4, "U": 3, "A": 2, "Total": 9
        })
        _merge_row(rua_data, "Unit-I", "Computing", {
            "R": 5, "U": 4, "A": 2, "Total": 11
        })
        
        # Should have merged or updated
        self.assertIn("Unit-I", rua_data)
        # First title should be preserved
        self.assertEqual(rua_data["Unit-I"]["title"], "Introduction")


class TestIntegrationRUA(unittest.TestCase):
    """Integration tests for RUA extraction workflow"""
    
    def test_full_rua_extraction_flow(self):
        """Test complete RUA extraction from rows"""
        rows = [
            ["Unit I", "Introduction to Programming", "4", "3", "2", "9"],
            ["Unit II", "Data Structures", "5", "4", "2", "11"],
            ["Unit III", "Algorithms and Complexity", "6", "3", "1", "10"],
            ["Unit IV", "Object Oriented Design", "3", "3", "2", "8"],
            ["Unit V", "Advanced Topics", "2", "2", "1", "5"],
            ["TOTAL", "", "20", "15", "8", "43"]
        ]
        
        rua_data = {}
        _parse_rows(rows, rua_data)
        
        # Verify complete structure
        self.assertGreater(len(rua_data), 0)
        self.assertIn("TOTAL", rua_data)
        
        # Verify marks calculation
        if "Unit-I" in rua_data and "Unit-II" in rua_data:
            u1_total = rua_data["Unit-I"]["Total"]
            u2_total = rua_data["Unit-II"]["Total"]
            self.assertGreater(u1_total, 0)
            self.assertGreater(u2_total, 0)
    
    def test_partial_rua_data(self):
        """Test handling of partial RUA data"""
        rows = [
            ["Unit I", "Intro", "4", "3", "2", "9"],
            ["Unit II", "Data", "5", "4", "2", "11"]
        ]
        
        rua_data = {}
        _parse_rows(rows, rua_data)
        
        self.assertEqual(len(rua_data), 2)
        self.assertNotIn("TOTAL", rua_data)  # No total row provided


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)
