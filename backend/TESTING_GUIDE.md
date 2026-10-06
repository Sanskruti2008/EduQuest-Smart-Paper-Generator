# Extraction Module Test Quick Reference

## 📊 Test Results Summary
- **OCR Extraction Tests**: 55/55 ✅ PASSED
- **RUA Extraction Tests**: 44/44 ✅ PASSED
- **Total**: 99/99 PASSED (100%)

## 🚀 Quick Start

### Run All Tests
```bash
cd backend
python -m unittest test_ocr_extraction test_rua_extraction -v
```

### Run OCR Tests Only
```bash
cd backend
python -m unittest test_ocr_extraction -v
```

### Run RUA Tests Only
```bash
cd backend
python -m unittest test_rua_extraction -v
```

## 📋 Test Categories

### OCR Extraction (`test_ocr_extraction.py`)
| Category | Tests | Focus |
|----------|-------|-------|
| Marks Extraction | 10 | Multiple notation formats |
| Course Outcome | 5 | CO label normalization |
| Numbers | 5 | Number extraction & cleanup |
| Question Cleaning | 5 | Text preprocessing |
| Bloom Levels | 3 | Cognitive level extraction |
| **Question Validation** | **11** | **Core validation logic** |
| AI Fallback | 3 | Groq API integration |
| Confidence | 3 | Quality scoring |
| Edge Cases | 5 | Error handling |
| Integration | 4 | Real-world scenarios |

### RUA Extraction (`test_rua_extraction.py`)
| Category | Tests | Focus |
|----------|-------|-------|
| Roman Numerals | 4 | Unit conversion |
| Numbers | 6 | Number normalization |
| Titles | 8 | Title cleaning & extraction |
| Unit Keys | 4 | Key generation |
| Merge | 6 | Row merging logic |
| **Parsing** | **8** | **Core parsing logic** |
| Structure | 2 | Data validation |
| Edge Cases | 5 | Error handling |
| Integration | 2 | Full workflow |

## 🔍 Running Specific Tests

### Single Test Class
```bash
python -m unittest test_ocr_extraction.TestMarksExtraction -v
python -m unittest test_rua_extraction.TestParseRows -v
```

### Single Test Method
```bash
python -m unittest test_ocr_extraction.TestMarksExtraction.test_square_bracket_marks
python -m unittest test_rua_extraction.TestParseRows.test_parse_multiple_unit_rows
```

## 📊 Test Statistics

### Execution Time
- OCR Tests: ~22 seconds (with OCR processing)
- RUA Tests: ~0.008 seconds (lightweight parsing)

### Coverage
- **Functions Tested**: 20+ core extraction functions
- **Edge Cases**: 10+ edge case scenarios
- **Integration Tests**: 6 realistic workflows
- **Error Scenarios**: Null, empty, invalid data handling

## ✨ Key Improvements

### OCR Module
✅ 55 tests covering all mark formats
✅ Course outcome OCR corruption handling
✅ Question validation with 11 test scenarios
✅ Confidence scoring implementation
✅ Edge case and error handling

### RUA Module  
✅ 44 tests for curriculum parsing
✅ Roman numeral and digit handling
✅ Title extraction and cleaning
✅ Data structure validation
✅ NaN and malformed data handling

## 🐛 Known Behaviors

1. **Groq API Messages**: Tests may show API unavailable warnings - this is normal and expected
2. **OCR Processing**: Tests include realistic OCR noise/corruption scenarios
3. **Default Values**: Invalid inputs use sensible defaults (marks=4, CO='CO1', etc.)
4. **Validation**: Strict validation for question text (requires action verbs or clear noun phrases)

## 📝 Test Documentation

Detailed test documentation available in:
- [TEST_RESULTS.md](TEST_RESULTS.md) - Full test report
- Code comments in test files for individual test purposes

## 🎯 Next Steps

1. ✅ Core extraction functions tested
2. ✅ Edge cases handled
3. Next: Integration tests with database layer
4. Next: Performance benchmarking
5. Next: PDF sample testing with real exam papers

## ⚙️ Paper Generation Resource Limits

Paper generation uses the embedding model and ChromaDB, so the API executes
one generation at a time. Requests wait for a bounded period and receive
`429` when the worker remains busy. A running generation that exceeds its
timeout receives `504`; its worker slot remains occupied until the underlying
operation finishes, preventing overlapping model-heavy work.

Configure these environment variables for the deployment:

```text
PAPER_GENERATION_QUEUE_TIMEOUT_SECONDS=10
PAPER_GENERATION_TIMEOUT_SECONDS=180
```

The generation response includes `X-EduQuest-Generation-Milliseconds` on
successful requests. Use this value, server logs, CPU/memory metrics, and
request volume to establish a baseline before changing the limits.

---

**Last Updated**: 2026-09-05  
**Framework**: Python unittest  
**Dependencies**: None (standard library only)
