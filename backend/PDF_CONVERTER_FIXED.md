# PDF to JSON Converter - Fixed!

## 🎯 What's Been Fixed

### 1. **Improved OCR Text Cleaning**
- Removes OCR artifacts like underscores (`_`), tildes (`~`), and em dashes (`—`)
- Cleans up special characters at the beginning of questions
- Better handling of smart quotes and special punctuation
- Example: `_b) State any two points` → `State any two points`

### 2. **Enhanced Question Pattern Matching**
- Better regex patterns for detecting sub-questions (a), b), c), etc.)
- Handles OCR artifacts in question labels
- More robust CO (Course Outcome) extraction
- Improved Bloom's level detection

### 3. **Question Validation & Cleanup**
- Automatic validation of extracted questions
- Ensures marks are in valid range (1-20)
- Validates course outcomes (CO1, CO2, etc.)
- Validates Bloom's levels (K1-K6)
- Capitalizes first letter of questions
- Removes trailing/leading special characters

### 4. **Better Error Messages**
- Clear installation instructions for Tesseract OCR
- Detailed Poppler installation guidance
- Helpful debugging output during extraction
- Better error handling and logging

### 5. **OCR Improvements**
- Fixed common misreadings (e.g., | → I)
- Removes extra spaces before punctuation
- Better preservation of mathematical symbols
- Enhanced post-processing of extracted text

## 🚀 How to Use

### Prerequisites

1. **Install Tesseract OCR**
   - Windows: [Download from GitHub](https://github.com/tesseract-ocr/tesseract)
   - Linux: `sudo apt-get install tesseract-ocr`
   - macOS: `brew install tesseract`

2. **Install Poppler** (for PDF processing)
   - Windows: [Download from GitHub](https://github.com/oschwartz10612/poppler-windows/releases/)
   - Linux: `sudo apt-get install poppler-utils`
   - macOS: `brew install poppler`

3. **Install Python Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

### Testing the Converter

```bash
# Test all PDFs in uploads folder
python test_pdf_converter.py

# Test a specific PDF
python test_pdf_converter.py path/to/your/file.pdf
```

### Using in Your Application

```python
from ocr_extractor import extract_questions_from_pdf

# Extract questions from PDF
result = extract_questions_from_pdf('path/to/paper.pdf', extract_images=True)

# Access extracted data
papers = result['papers']
for paper in papers:
    questions = paper['questions']
    for q in questions:
        print(f"Q{q['question_number']}: {q['question_text']}")
        print(f"Marks: {q['marks']}, CO: {q['course_outcome']}, Bloom: {q['bloom_level']}")
```

## 📋 Output Format

The converter returns JSON in the following format:

```json
{
  "total_papers": 1,
  "exam_info": {},
  "papers": [
    {
      "paper_number": 1,
      "paper_name": "Question Paper",
      "questions": [
        {
          "question_number": "1",
          "question_text": "State any two points of difference between encoding and decoding.",
          "marks": 4,
          "course_outcome": "CO1",
          "bloom_level": "K1",
          "has_math": false,
          "has_diagram": false,
          "images": []
        }
      ]
    }
  ],
  "total_images_detected": 0,
  "extraction_metadata": {
    "total_characters": 12345,
    "total_lines": 234,
    "tesseract_version": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
    "images_extracted": 0
  }
}
```

## 🔍 Validation Rules

Questions are automatically validated and cleaned:

1. **Minimum length**: Question text must be at least 10 characters
2. **Marks validation**: Must be between 1-20 (defaults to 4 if invalid)
3. **Course Outcome**: Must match pattern CO\d+ (defaults to CO1)
4. **Bloom's Level**: Must be K1-K6 (defaults to K2)
5. **Auto-capitalization**: First letter is capitalized
6. **Artifact removal**: Leading/trailing special characters removed

## 🐛 Troubleshooting

### No questions extracted?

1. Check if PDF has text or is image-based (OCR works on both)
2. Verify Tesseract is installed and in PATH
3. Ensure PDF is not password-protected
4. Check the debug output for parsing issues

### Tesseract not found error?

- Make sure Tesseract is installed
- On Windows, add to PATH or it will auto-detect common install locations
- The script will print the detected Tesseract path

### Poppler error when converting PDF?

- Install Poppler for your operating system (see Prerequisites)
- On Windows, add Poppler bin folder to PATH

### OCR extracting garbage text?

- Increase DPI in `extract_text_from_pdf()` (default is 300)
- Ensure PDF is not too low quality
- Some handwritten papers may not work well

## 📊 What Gets Extracted

- ✅ Question text (cleaned and validated)
- ✅ Marks (1-20 range)
- ✅ Course Outcomes (CO1, CO2, etc.)
- ✅ Bloom's Taxonomy Level (K1-K6)
- ✅ Mathematical content detection
- ✅ Diagram/figure references
- ✅ Images (uploaded to Cloudinary if configured)

## 🔧 Configuration

### Cloudinary Setup (Optional - for image upload)

Create a `.env` file in the backend directory:

```env
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

If Cloudinary is not configured, images won't be uploaded but extraction will still work.

### OCR Configuration

You can adjust OCR settings in `extract_text_from_pdf()`:

```python
# Change DPI for better quality (higher = slower but better quality)
images = convert_from_path(pdf_path, dpi=300)  # Try 400 or 600

# Adjust Tesseract config
custom_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'
```

## ✨ Example Output

**Before (with OCR artifacts):**
```
_b) State any two points of difference between encoding and decoding.
— e) Illustrate through a neat diagram the elements of communication process.
~ g) State any two examples of negative and positive haptics.
```

**After (cleaned):**
```
State any two points of difference between encoding and decoding.
Illustrate through a neat diagram the elements of communication process.
State any two examples of negative and positive haptics.
```

## 📝 Notes

- The converter works best with well-formatted MSBTE question papers
- Scanned PDFs work via OCR (quality depends on scan quality)
- Digital PDFs (text-based) also work via OCR
- Image detection and upload requires Cloudinary configuration
- Questions are automatically numbered sequentially

## 🎓 Support

If you encounter issues:

1. Run the test script: `python test_pdf_converter.py`
2. Check the console output for detailed error messages
3. Verify all prerequisites are installed
4. Ensure PDF is not corrupted or password-protected
