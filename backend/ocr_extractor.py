"""
MSBTE OCR Extractor - Integrated Module
Extract exam questions from scanned PDFs with image detection
"""
import json
import re
from copy import deepcopy
from pdf2image import convert_from_path
import pytesseract
from PIL import Image, ImageOps, ImageDraw, ImageFilter, ImageEnhance
import os
import platform
import shutil
import numpy as np
from io import BytesIO
import base64
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
from groq import Groq

# Import enhancement utilities
try:
    from extraction_enhancements import (
        correct_spelling,
        GrammarValidator,
        extract_marks_enhanced,
        validate_marks_extraction,
        enhance_extracted_question,
    )
    ENHANCEMENTS_AVAILABLE = True
except ImportError:
    ENHANCEMENTS_AVAILABLE = False
    print("WARNING: extraction_enhancements module not available. Some features disabled.")

# Load environment variables
load_dotenv()

# Cross-platform Tesseract path detection
def find_tesseract():
    """Find Tesseract executable across different platforms"""
    # Check if tesseract is in PATH
    tesseract_cmd = shutil.which('tesseract')
    if tesseract_cmd:
        return tesseract_cmd
    
    # Platform-specific default paths
    if platform.system() == 'Windows':
        possible_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            r'C:\Users\{}\AppData\Local\Tesseract-OCR\tesseract.exe'.format(os.getenv('USERNAME', ''))
        ]
    elif platform.system() == 'Darwin':  # macOS
        possible_paths = [
            '/usr/local/bin/tesseract',
            '/opt/homebrew/bin/tesseract'
        ]
    else:  # Linux
        possible_paths = [
            '/usr/bin/tesseract',
            '/usr/local/bin/tesseract'
        ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None

# Set Tesseract path
tesseract_path = find_tesseract()
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
else:
    print("WARNING: Tesseract not found. OCR functionality may not work.")

def detect_images_in_page(image, min_size=100):
    """
    Detect image regions in a PDF page
    Returns list of bounding boxes for detected images/diagrams
    """
    try:
        # Convert to numpy array
        img_array = np.array(image.convert('L'))  # Grayscale
        
        # Detect large white or blank regions (likely images/diagrams)
        # Use edge detection to find image boundaries
        from scipy import ndimage
        
        # Simple threshold to find non-text regions
        # Text regions have lots of small variations, images are more uniform
        # This is a simplified approach - could be enhanced with ML
        
        # For now, detect regions with low text density
        # OCR the entire page to get text box coordinates
        ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        
        # Get image dimensions
        width, height = image.size
        
        # Create a mask of text regions
        text_mask = np.zeros((height, width), dtype=np.uint8)
        
        for i, conf in enumerate(ocr_data['conf']):
            if int(conf) > 0:  # Valid text detection
                x, y, w, h = ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i]
                if w > 0 and h > 0:
                    text_mask[y:y+h, x:x+w] = 255
        
        # Invert to get non-text regions
        non_text_mask = 255 - text_mask
        
        # Find contiguous regions (potential images)
        from scipy.ndimage import label, find_objects
        labeled_array, num_features = label(non_text_mask > 128)
        
        image_regions = []
        for i, slice_obj in enumerate(find_objects(labeled_array)):
            if slice_obj is not None:
                y_slice, x_slice = slice_obj
                bbox_height = y_slice.stop - y_slice.start
                bbox_width = x_slice.stop - x_slice.start
                
                # Filter by size - only keep reasonably sized regions
                if bbox_width >= min_size and bbox_height >= min_size:
                    # Discard giant regions that span most of the page (whitespace artifacts)
                    if bbox_width >= width * 0.90:
                        continue
                    # Check if region has enough content (not just white space)
                    region_arr = img_array[y_slice, x_slice]
                    mean_val = float(region_arr.mean())
                    # Skip near-white regions (mean > 240 = mostly blank whitespace)
                    if mean_val > 240:
                        continue
                    # Require higher pixel variance AND sufficient area
                    if (region_arr.std() > 40 and
                            bbox_width * bbox_height > min_size * min_size * 4):
                        image_regions.append({
                            'bbox': (x_slice.start, y_slice.start, x_slice.stop, y_slice.stop),
                            'width': bbox_width,
                            'height': bbox_height
                        })
        
        return image_regions
        
    except ImportError:
        # scipy not available, use simpler detection
        return detect_images_simple(image, min_size)
    except Exception as e:
        print(f"Image detection error: {e}")
        return []

def detect_images_simple(image, min_size=50):
    """Simplified image detection without scipy"""
    try:
        # Get OCR bounding boxes
        ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        
        width, height = image.size
        
        # Find large gaps between text regions (likely images)
        text_boxes = []
        for i, conf in enumerate(ocr_data['conf']):
            if int(conf) > 0:
                x, y, w, h = ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i]
                if w > 0 and h > 0:
                    text_boxes.append((x, y, x+w, y+h))
        
        # Look for large empty regions
        image_regions = []
        
        # Simple heuristic: if there's a large vertical gap, likely an image
        if len(text_boxes) > 1:
            sorted_boxes = sorted(text_boxes, key=lambda b: b[1])  # Sort by y
            
            for i in range(len(sorted_boxes) - 1):
                gap_start = sorted_boxes[i][3]  # Bottom of current box
                gap_end = sorted_boxes[i+1][1]  # Top of next box
                gap_height = gap_end - gap_start
                
                if gap_height > min_size:
                    # Found a gap - might be an image
                    image_regions.append({
                        'bbox': (0, gap_start, width, gap_end),
                        'width': width,
                        'height': gap_height
                    })
        
        return image_regions
        
    except Exception as e:
        print(f"Simple image detection error: {e}")
        return []

def extract_and_save_images(image, image_regions, page_num, cloudinary_folder):
    """Extract image regions and upload directly to Cloudinary cloud storage"""
    # Configure Cloudinary
    cloudinary.config(
        cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
        api_key=os.getenv('CLOUDINARY_API_KEY'),
        api_secret=os.getenv('CLOUDINARY_API_SECRET')
    )
    
    extracted_images = []
    
    for idx, region in enumerate(image_regions):
        try:
            bbox = region['bbox']
            # Crop the image
            cropped = image.crop(bbox)
            
            # Generate filename
            image_filename = f"page_{page_num}_image_{idx+1}.png"
            
            # Convert to bytes for upload
            buffered = BytesIO()
            cropped.save(buffered, format="PNG")
            buffered.seek(0)
            
            # Upload to Cloudinary
            try:
                upload_result = cloudinary.uploader.upload(
                    buffered,
                    folder=cloudinary_folder,
                    public_id=f'page_{page_num}_image_{idx+1}',
                    resource_type='image',
                    overwrite=True
                )
                
                extracted_images.append({
                    'filename': image_filename,
                    'url': upload_result['secure_url'],
                    'public_id': upload_result['public_id'],
                    'cloudinary_url': upload_result['secure_url'],
                    'width': region['width'],
                    'height': region['height'],
                    'bbox': bbox,
                    'page': page_num
                })
                
                print(f"✓ Uploaded image to Cloudinary: {upload_result['secure_url']}")
                
            except Exception as cloudinary_error:
                # Log error but don't store locally
                print(f"✗ Cloudinary upload failed for page {page_num} image {idx+1}: {cloudinary_error}")
                print("  Make sure CLOUDINARY credentials are set in .env file")
                continue
            
        except Exception as e:
            print(f"Error extracting image {idx+1} from page {page_num}: {e}")
            continue
    
    return extracted_images

# ─────────────────────────────────────────────────────────────────────────────
# OCR Pre-processing helpers
# ─────────────────────────────────────────────────────────────────────────────

def preprocess_image_for_ocr(pil_image):
    """
    Multi-step preprocessing pipeline that dramatically improves Tesseract
    accuracy on scanned / photocopied exam papers.

    Steps
    -----
    1. Convert to grayscale
    2. Upscale small pages so effective width >= 2200 px (≈ 300 DPI for A4)
    3. Otsu adaptive binarisation (crisps text to pure black/white)
    4. Light sharpening pass
    5. Contrast enhancement (makes faint print legible)
    """
    img = pil_image.convert('L')                          # 1. Grayscale

    # 2. Upscale if too small
    w, h = img.size
    if w < 2200:
        scale = 2200 / w
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    # 3. Otsu binarisation via numpy
    arr = np.array(img)
    hist, _ = np.histogram(arr.ravel(), bins=256, range=(0, 256))
    total = arr.size
    sum_total = int(np.dot(np.arange(256), hist))
    sum_b, w_b, var_max, threshold = 0, 0, 0.0, 128
    for t in range(256):
        w_b += hist[t]
        if w_b == 0:
            continue
        w_f = total - w_b
        if w_f == 0:
            break
        sum_b += t * hist[t]
        m_b = sum_b / w_b
        m_f = (sum_total - sum_b) / w_f
        var_between = w_b * w_f * (m_b - m_f) ** 2
        if var_between > var_max:
            var_max = var_between
            threshold = t
    binary = np.where(arr > threshold, 255, 0).astype(np.uint8)
    img = Image.fromarray(binary)

    # 4. Sharpen slightly
    img = img.filter(ImageFilter.SHARPEN)

    # 5. Contrast boost
    img = ImageEnhance.Contrast(img).enhance(1.4)

    return img


def _ocr_with_config(pil_image, psm):
    """Run Tesseract with a given PSM mode and return extracted text."""
    config = (
        f'--oem 3 --psm {psm} '
        '-c preserve_interword_spaces=1 '
        '-c textord_heavy_nr=1 '
        '-c tessedit_do_invert=0'
    )
    return pytesseract.image_to_string(pil_image, config=config, lang='eng')


# ─────────────────────────────────────────────────────────────────────────────

def extract_text_from_pdf(pdf_path, dpi=150, extract_images=False, fast_mode=True):
    """
    Convert PDF to text using OCR with preprocessing.
    
    Args:
        pdf_path: Path to PDF file
        dpi: DPI for image conversion (default 150, lower is faster)
        extract_images: Whether to extract images (slow, default False)
        fast_mode: Skip image detection, use single OCR pass (default True for speed)
    """
    try:
        print(f"Converting PDF to images at {dpi} DPI (fast_mode={fast_mode})...")
        images = convert_from_path(pdf_path, dpi=dpi)
        print(f"Successfully converted {len(images)} pages to images")
    except Exception as e:
        print(f"ERROR converting PDF to images: {str(e)}")
        print("HINT: Make sure Poppler is installed.")
        print("  - Windows: Download from https://github.com/oschwartz10612/poppler-windows/releases/")
        print("  - Linux: sudo apt-get install poppler-utils")
        print("  - macOS: brew install poppler")
        raise Exception(f"PDF conversion failed. Poppler may not be installed: {str(e)}")

    full_text = []
    all_images = []

    pdf_basename = os.path.splitext(os.path.basename(pdf_path))[0]
    cloudinary_folder = f"eduquest/{pdf_basename}"

    for i, image in enumerate(images, 1):
        try:
            # ── Image extraction (skip in fast_mode) ────
            if extract_images and not fast_mode:
                image_regions = detect_images_in_page(image)
                if image_regions:
                    extracted = extract_and_save_images(image, image_regions, i, cloudinary_folder)
                    all_images.extend(extracted)

            # ── Pre-process for OCR ──────────────────────────────────────────
            processed = preprocess_image_for_ocr(image)

            # ── Layout-aware OCR ────────────────────────────────────────────
            # PSM 4 preserves columns and separated question blocks better than
            # PSM 6, which treats a full exam page as one uniform text block.
            # Keep the retry for sparse pages where PSM 4 may under-segment text.
            if fast_mode:
                text = _ocr_with_config(processed, psm=4)
                meaningful = [ln for ln in text.split('\n') if ln.strip()]
                if len(meaningful) < 5:
                    text_psm6 = _ocr_with_config(processed, psm=6)
                    if len([ln for ln in text_psm6.split('\n') if ln.strip()]) > len(meaningful):
                        text = text_psm6
            else:
                text = _ocr_with_config(processed, psm=4)
                # If PSM 4 produced very little text, retry with PSM 6
                meaningful = [ln for ln in text.split('\n') if ln.strip()]
                if len(meaningful) < 5:
                    text_psm6 = _ocr_with_config(processed, psm=6)
                    if len([ln for ln in text_psm6.split('\n') if ln.strip()]) > len(meaningful):
                        text = text_psm6

            # ── Post-processing ─────────────────────────────────────────────
            text = text.replace('|', 'I')
            text = re.sub(r'\s+([.,;:?!])', r'\1', text)
            text = text.replace('\x0c', '\n')   # strip form-feed chars

            page_text = f"\n--- PAGE {i} ---\n"
            if extract_images and not fast_mode and all_images:
                page_text += f"[IMAGES DETECTED: {len([x for x in all_images if x.get('page') == i])} on this page]\n"
            page_text += text
            full_text.append(page_text)

        except Exception as e:
            print(f"ERROR processing page {i}: {str(e)}")
            continue

    if not full_text:
        raise Exception("No text could be extracted from any page")

    result_text = '\n'.join(full_text)

    if extract_images and not fast_mode:
        return result_text, all_images
    else:
        return result_text, []

def clean_text(text):
    """Remove OCR artifacts and clean up text; preserve mathematical symbols."""
    if not text:
        return text

    # Collapse runs of whitespace (preserve newlines separately)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n', text)

    # ── Character-level substitutions ───────────────────────────────────────
    replacements = {
        # UTF-8 mis-reading artefacts
        'â€"'   : '-',
        'â€™'   : "'",
        'â€\x9c': '"',
        'â€\x9d': '"',
        'â€œ'   : '"',
        'â€'    : '"',
        'Â©'    : '',
        'Â®'    : '',
        'â€¢'   : '-',
        # Unicode punctuation → ASCII
        '\u2014': '-',    # Em dash
        '\u2013': '-',    # En dash
        '\u2018': "'",    # Left single quote
        '\u2019': "'",    # Right single quote
        '\u201c': '"',    # Left double quote
        '\u201d': '"',    # Right double quote
        '\u00a0': ' ',    # Non-breaking space
        '\u200b': '',     # Zero-width space
        '\ufffd': '',     # Replacement character
        '\x00'  : '',     # Null byte
        '\x0c'  : '\n',   # Form-feed
        # Common Tesseract mis-reads on MSBTE papers
        '—'     : '-',
        '–'     : '-',
        '\u2022': '-',    # Bullet
        '\u00b7': '.',    # Middle dot
    }
    for wrong, correct in replacements.items():
        text = text.replace(wrong, correct)

    # Common whole-word OCR corrections seen in MSBTE papers.
    word_fixes = {
        'en list': 'enlist',
        'expiain': 'explain',
        'fiate': 'differentiate',
        'jot stock': 'joint stock',
        'liha the help': 'with the help',
        'henry fayo': 'Henry Fayol',
        'workman compensation': 'Workmen\'s Compensation',
        'supemetting': 'supernetting',
        'subneting': 'subnetting',
        'comunication': 'communication',
        'interrnet': 'internet',
        'systemate': 'system and',
        'erp election': 'ERP selection',
        'erpelection': 'ERP selection',
        'select ate': 'selection and',
        'nob per in duction': 'minimum wages',
        'nob per in duction wages act': 'Minimum Wages Act',
        'stat production': 'State production',
        'systemsco': 'systems',
        'skilis': 'skills',
        'aorganization': 'of organization',
        'markebng': 'marketing',
        'managemen': 'management',
        'vanous': 'various',
        'avoaccidents': 'avoid accidents',
    }
    for wrong, correct in word_fixes.items():
        text = re.sub(rf'\b{re.escape(wrong)}\b', correct, text, flags=re.IGNORECASE)

    text = re.sub(r'\b([Nn])ob\s+per\s+in\s+duction\b', 'minimum wages', text)
    text = re.sub(r'\bERP\s*election\b', 'ERP selection', text, flags=re.IGNORECASE)
    text = re.sub(r'\bselect\s+ate\b', 'selection and', text, flags=re.IGNORECASE)
    text = re.sub(r'\bsystemate\b', 'system and', text, flags=re.IGNORECASE)
    text = re.sub(r"\bdisciptine\s*['’`]n\b", 'discipline in', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+C{1,3}o\s+O\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\bExplain\s+the\s+in\s+brief\b', 'Explain in brief', text, flags=re.IGNORECASE)
    text = re.sub(r'\bExplain\s+-S\b', 'Explain 5-S', text, flags=re.IGNORECASE)
    text = re.sub(r'\.{2,}', '.', text)
    text = re.sub(r'\bStat\s+production\b', 'State production', text, flags=re.IGNORECASE)
    text = re.sub(r'\bAct(?:co|c0|cos)\b', 'Act', text, flags=re.IGNORECASE)
    text = re.sub(r'\bC[O0Q]\s*\d+\s*[,;]?(?:\s*\d+)?\b', '', text, flags=re.IGNORECASE)

    # Common OCR gluing patterns seen in scanned diploma papers.
    text = re.sub(r'\b(Explain|Define|State|List|Write|Differentiate|Compare|Discuss|Describe)\s+(?:the\s+)?([A-Za-z])([a-z]+)\s+([A-Z][a-z]+)',
                  r'\1 \2\3 \4', text)

    # ── Regex-level clean-up ─────────────────────────────────────────────────
    # Remove stray underscores/tildes/dashes at line start
    text = re.sub(r'(?m)^[_~\-\s]+', '', text)
    # Remove stray underscores/tildes before sub-question labels: _b) → b)
    text = re.sub(r'[_~]+\s*([a-z]\))', r'\1', text)
    # Fix OCR run-on: lowercase letter directly followed by uppercase → insert space
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    # Remove lone pipe/backslash characters (scanning noise)
    text = re.sub(r'(?<!\S)[|\\](?!\S)', '', text)
    # Remove a few known trailing junk tokens that OCR appends to questions.
    text = re.sub(r'\bCOS\b(?=\s*$)', '', text)
    text = re.sub(r'\bC0S\b(?=\s*$)', '', text)
    # Collapse multiple spaces that may have appeared after substitutions
    text = re.sub(r' {2,}', ' ', text)

    return text.strip()


def _split_compound_question_lines(text: str) -> str:
    """Expand OCR lines that accidentally contain multiple question starts.

    This is intentionally conservative: it only inserts line breaks when a
    clear new question / sub-question marker appears inside the same OCR line.
    That makes downstream parsing much more likely to treat items as separate
    questions instead of one merged block.
    """
    if not text:
        return text

    # Break obvious glued-together sub-question markers before the more general
    # splitter runs. These patterns are intentionally narrow: only label-like
    # tokens followed by a question verb are affected.
    text = re.sub(
        r'(?<=\S)\s*=\s+(?=[A-Za-z]{1,3}[\)\}\]:]\s*[_~\-]*\s*[A-Za-z])',
        '\n',
        text,
    )
    text = re.sub(
        r'(?<=\S)\s+(?=[A-Za-z]{1,3}[\)\}\]:]\s*[_~\-]*\s*[A-Za-z])',
        '\n',
        text,
    )

    split_markers = [
        # Main question headers often arrive as Q1, Q.1, or Question 1 on a
        # single OCR line. Treat any of those as a new question boundary.
        r'(?=\b(?:Q|Que(?:stion)?)\.?\s*\d+\b)',
        r'(?=\b\d+\s*\.)',
        r'(?=\b\d+\s*\))',
        r'(?=\b\d+\s*[.)]\s+[A-Za-z])',
        r'(?=\b(?:CO\s*\d+|CO[Ss0]|C0S)\s+[A-Za-z]{1,3}[\)\}\]:]\s*[_~\-]*\s*[A-Za-z])',
        r'(?<=CO\d)\s+(?=[A-Za-z]{1,3}[\)\}\]:]\s*[_~\-]*\s*[A-Za-z])',
        r'(?=\b\([a-hA-H]\))',
        r'(?=\b[a-hA-H]{1,3}[\)\}\]:]\s*[_~\-]*\s*[A-Za-z])',
        r'(?=\b(?:i{1,3}|iv|v|vi{0,3}|ix|x)[\)\}\]:]\s*[_~\-]*\s*[A-Za-z])',
        r'(?=\bCO\s*\d+\b)',
        # API/OCR text can glue multiple verb-led questions onto one line.
        r'(?=(?:Explain|Define|Describe|Write|Differentiate|Compare|State|List|Discuss|'
        r'Illustrate|Prepare|Calculate|Solve|What\s+is|What\s+are|Why\s+is|Why\s+are|'
        r'How\s+does|How\s+do)\b)',
    ]

    # First normalise whitespace so the lookaheads work reliably.
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    for marker in split_markers:
        # Break compound OCR lines only when the marker appears after some text.
        text = re.sub(rf'(?<!\n)\s+{marker}', '\n', text)

    # OR separators frequently split alternatives/questions in polytechnic papers.
    text = re.sub(r'(?<=\S)\s+\bOR\b\s+(?=\S)', '\nOR\n', text, flags=re.IGNORECASE)

    # Clean up accidental blank lines introduced by splitting.
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _preprocess_ocr_text(text: str) -> str:
    """Clean noisy OCR text without changing overall document structure."""
    if not text:
        return text

    t = str(text).replace('\r\n', '\n').replace('\r', '\n')

    # Merge words split across line breaks, but preserve a new question after
    # sentence punctuation: "structure.\nExplain ..." must stay separate.
    t = re.sub(r'(?<![.!?:;])([A-Za-z])\n([a-z])', r'\1\2', t)

    # Split common merged boundary: "importance2 Define" -> newline before
    # the next numbered/verb-led question start.
    t = re.sub(
        r'([a-z])\s*(\d+\s*[.)]\s*)?(?=(?:Explain|Define|Describe|Write|Differentiate|Compare|State|List|Discuss|Illustrate)\b)',
        r'\1\n\2',
        t,
        flags=re.IGNORECASE,
    )

    cleaned_lines = []
    for raw in t.split('\n'):
        line = raw.strip()
        if not line:
            cleaned_lines.append('')
            continue

        # Drop garbage-only fragments.
        if not re.search(r'[A-Za-z0-9]', line):
            continue

        # Remove leading OCR junk symbols.
        line = re.sub(r'^\s*[=+\-"\':;\[\]{}()<>`~|\\]+\s*', '', line)

        # Normalize internal whitespace.
        line = re.sub(r'\s{2,}', ' ', line).strip()

        # Remove tiny non-meaningful fragments.
        if len(line) <= 2 and not re.search(r'\d', line):
            continue

        cleaned_lines.append(line)

    out = '\n'.join(cleaned_lines)
    out = re.sub(r'\n{3,}', '\n\n', out)
    return out.strip()


def _split_into_paper_blocks(content: str) -> list[str]:
    """Heuristically split OCR text into multiple paper blocks when present."""
    if not content:
        return []

    lines = content.split('\n')
    if len(lines) < 30:
        return [content]

    starts = [0]
    q1_seen_positions = []

    for i, line in enumerate(lines):
        s = line.strip()
        if not s:
            continue

        if re.match(r'^\s*Q\.?\s*1\b.*(?:Attempt|attempt)?', s):
            q1_seen_positions.append(i)
            # If Q1 appears again far away, treat as a new paper boundary.
            if len(q1_seen_positions) >= 2 and i - q1_seen_positions[-2] > 25:
                starts.append(i)
                continue

        # Repeated full paper headers likely indicate a new paper in the same PDF.
        if re.search(r'(?:QUESTION\s*PAPER|SUMMER\s+EXAMINATION|WINTER\s+EXAMINATION|SUBJECT\s*CODE\s*[:\-]?\s*\d{5})', s, re.IGNORECASE):
            if i > 20 and (i - starts[-1]) > 40:
                starts.append(i)

        # Explicit page separators can indicate a new paper when followed by Q1.
        if re.match(r'^---\s*PAGE\s*\d+\s*---$', s, re.IGNORECASE):
            lookahead = ' '.join(lines[i + 1:i + 8])
            if re.search(r'\bQ\.?\s*1\b', lookahead, re.IGNORECASE) and (i - starts[-1]) > 35:
                starts.append(i + 1)

    starts = sorted(set(idx for idx in starts if 0 <= idx < len(lines)))
    if len(starts) == 1:
        return [content]

    blocks = []
    for idx, st in enumerate(starts):
        en = starts[idx + 1] if idx + 1 < len(starts) else len(lines)
        block = '\n'.join(lines[st:en]).strip()
        if block:
            blocks.append(block)

    return blocks or [content]


def _extract_questions_from_noisy_lines(content: str) -> list[dict]:
    """Fallback extractor for heavily noisy OCR where structured parsing misses lines.

    This pass treats each clear CO/label/verb line as an individual question,
    tuned for diploma/polytechnic paper formatting.
    """
    if not content:
        return []

    text = _preprocess_ocr_text(content)
    lines = [ln.strip() for ln in text.split('\n') if ln.strip()]

    questions = []
    current_marks_each = 4
    # Only carry forward a CO that was actually observed in the source.
    current_co = ''

    # Verb gate for valid question starters.
    verb_re = re.compile(
        r'\b(?:Explain|Define|Describe|Write|Differentiate|Compare|State|List|Discuss|Illustrate|Draw|Prepare|Analyze|Apply|Enlist|Identify|'
        r'Choose|Fill|Do|Transform|Compose|Draft|Formulate|Elaborate|Summari[sz]e|Read|Make|Answer|Calculate|Solve|Comment|Justify|Prove|'
        r'What\s*is|What\s*are|Why\s*is|Why\s*are|How\s*does|How\s*do|How\s*can|Give|Show|Outline|Trace|Name|Mention)\b',
        re.IGNORECASE,
    )

    for line in lines:
        s = line.strip()
        if not s:
            continue

        # Section header for marks-per-question estimation.
        if re.match(r'^\s*Q\.?\s*\d+\b', s, re.IGNORECASE):
            attempt_count, total_marks = None, None
            m1 = re.search(r'Attempt\s+any\s+([A-Za-z0-9]+)', s, re.IGNORECASE)
            if m1:
                token = m1.group(1).upper()
                word_map = {
                    'ONE': 1, 'TWO': 2, 'THREE': 3, 'FOUR': 4, 'FIVE': 5,
                    'SIX': 6, 'SEVEN': 7, 'EIGHT': 8, 'NINE': 9, 'TEN': 10,
                }
                attempt_count = int(token) if token.isdigit() else word_map.get(token)
            m2 = re.search(r'\((\d{1,3})\)|\[(\d{1,3})\]', s)
            if m2:
                total_marks = int(next(g for g in m2.groups() if g))
            if attempt_count and total_marks and attempt_count > 0:
                current_marks_each = max(1, round(total_marks / attempt_count))
            continue

        # Skip obvious header/instruction lines.
        if re.search(r'(?:GOVERNMENT|POLYTECHNIC|EXAMINATION|INSTRUCTIONS|COURSE:|DURATION:|MARKS:|FIGURES TO THE RIGHT|COMMUNICATION INSTRUMENTS)', s, re.IGNORECASE):
            continue

        # Parse CO token when present.
        co_match = re.match(r'^\s*(C{1,3}[O0Q][0-9OQILTSIVXLCDM]{0,6})\b', s, re.IGNORECASE)
        body = s
        if co_match:
            parsed_co = _normalize_co_label(co_match.group(1))
            if parsed_co:
                current_co = parsed_co
            body = s[co_match.end():].strip()

        # Remove noisy leading label fragments like "sc)", "-.d}", "\by~", "<<)".
        body = re.sub(r'^[_~\-\./\\\"\']*\s*[A-Za-z0-9]{1,3}[\)\}\]:.]\s*', '', body)
        body = re.sub(r'^[_~\-\./\\\"\'\s]+', '', body)
        body = clean_text(body)

        # Keep only lines that look like actual question statements.
        if not body or len(re.findall(r'[A-Za-z]{2,}', body)) < 4:
            continue
        if not verb_re.search(body):
            continue

        q_obj = {
            'question_number': str(len(questions) + 1),
            'question_text': body,
            'marks': current_marks_each,
            'course_outcome': current_co,
            'bloom_level': extract_bloom_level(body),
            'has_math': detect_math_content(body),
            'identified_numbers': _extract_numbers_from_text(body),
            'has_diagram': bool(re.search(r'\b(diagram|draw|figure|graph|chart|sketch)\b', body, re.IGNORECASE)),
            'images': [],
            'sub_questions': [],
        }
        validated = validate_and_clean_question(q_obj)
        if validated:
            questions.append(validated)

    # De-duplicate near-identical lines that OCR can emit repeatedly.
    deduped = []
    seen = set()
    for q in questions:
        key = re.sub(r'\W+', ' ', q.get('question_text', '').lower()).strip()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(q)

    for i, q in enumerate(deduped, start=1):
        q['question_number'] = str(i)
    return deduped


def _aggressive_fallback_split(text: str) -> str:
    """More aggressive splitter used as a fallback when too few questions
    are extracted. Inserts line breaks before common question-start markers
    even when noisy OCR has mangled spacing or punctuation.
    """
    if not text:
        return text

    # Normalize common OCR damage before looking for boundaries. These fixes
    # are limited to question stems and established exam terminology.
    t = clean_text(text)
    t = re.sub(r'\bEn\s+list\b', 'Enlist', t, flags=re.IGNORECASE)
    t = re.sub(r'\bExpiain\b', 'Explain', t, flags=re.IGNORECASE)
    t = re.sub(r'\bfiate\b', 'Differentiate', t, flags=re.IGNORECASE)
    t = re.sub(r'\bjolt\s+stock\b', 'joint stock', t, flags=re.IGNORECASE)
    t = re.sub(
        r'\b(?:ny\s+)?referring\s+any\s+four\s+provisions\b',
        'Explain any four provisions',
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r'detail\s*the\s+different\s+provisions',
        'detail. Enlist the different provisions',
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(r'\bthe\s+brief\s+classification\b', 'State the brief classification', t, flags=re.IGNORECASE)
    t = re.sub(r'\b(?:t|ny)\s+any\s+eight\b', 'List any eight', t, flags=re.IGNORECASE)
    t = re.sub(r'\bny\s+THREE\s+in\s+mass\s+production\b', 'Attempt any THREE in mass production', t, flags=re.IGNORECASE)
    t = re.sub(r'\b(?:ine|ine)\s+inventory\b', 'Define inventory', t, flags=re.IGNORECASE)
    t = re.sub(r'\bTHREE\s+four\s+merits\s+and\s+applications\b', 'List four merits and applications', t, flags=re.IGNORECASE)
    t = re.sub(r"\bAP['’]?s?\.\s+of\s+marketing\b", 'Principles of marketing', t, flags=re.IGNORECASE)

    # Normalize whitespace first
    t = re.sub(r'[ \t]+', ' ', t)

    # Aggressive markers: dotted Q headers, numbered items, alpha labels, CO labels
    markers = [
        r'(?<=\S)\s+(?=(?:Q\.?\s*\d+))',
        r'(?<=\S)\s+(?=(?:\d+\s*[.)]))',
        r'(?<=\S)\s+(?=(?:[a-hA-H][\)\}\]:]))',
        r'(?<=\S)\s+(?=(?:C[O0Q][\s\-\.:]*\d))',
        # Recover boundaries when OCR drops the sub-question label.
        r'(?<=\S)\s+(?=(?:Enlist|Explain|Define|Describe|Differentiate|'
        r'List|State|Classify|Attempt|Prepare|Discuss|Compare|Justify)\b)',
    ]

    for m in markers:
        t = re.sub(m, '\n', t, flags=re.IGNORECASE)

    # Split long runs of punctuation/garbage left at line starts
    t = re.sub(r'\n[\W_]{2,}', '\n', t)
    # Keep recovered boundaries intact: _preprocess_ocr_text intentionally
    # joins a newline followed by lowercase text as a word-wrap repair.
    stem_start = r'(enlist|explain|define|describe|differentiate|list|state|classify|attempt|prepare|discuss|compare|justify)'
    t = re.sub(
        rf'(?im)^(\s*){stem_start}\b',
        lambda match: f'{match.group(1)}{match.group(2).capitalize()}',
        t,
    )
    t = re.sub(r'\n{3,}', '\n\n', t)
    return t.strip()


def _normalize_inline_label(label: str) -> str:
    """Collapse OCR-noisy sub-question labels down to a single lower-case letter.

    Examples:
    - 'sc' -> 'c'
    - 'Cd' -> 'd'
    - 'g'  -> 'g'
    """
    if not label:
        return ''
    letters = re.sub(r'[^A-Za-z]', '', label)
    if not letters:
        return ''
    return letters[-1].lower()


_QUESTION_NOISE_PATTERNS = [
    r'GOVERNMENT\s+POLYTECHNIC[^\n]*',
    r'POLYTECHNIC[^\n]*',
    r'ACADEMICALLY\s+AUTONOMOUS[^\n]*',
    r'INSTITUTE\s+OF\s+GOVERNMENT[^\n]*',
    r'QUESTION\s+PAPER[^\n]*',
    r'SUMMER\s+EXAMINATION[^\n]*',
    r'WINTER\s+EXAMINATION[^\n]*',
    r'DIPLOMA\s+PROGRAM(?:ME|M)E[^\n]*',
    r'BRANCH[^\n]*',
    r'SEMESTER[^\n]*',
    r'DURATION[^\n]*',
    r'MARKS[^\n]*',
    r'TIME[^\n]*',
    r'SUBJECT[^\n]*',
    r'ROLL\s*NO[^\n]*',
    r'SEAT\s*NO[^\n]*',
]


def _clean_question_body(text: str) -> str:
    """Remove obvious paper-header noise and leftover OCR junk from a question body."""
    if not text:
        return ''

    t = clean_text(text)

    # Repair common API/Tesseract word joins before grammar validation.
    glued_token_repairs = {
        r'\bmarkeling\b': 'marketing',
        r'\bwilh\b': 'with',
        r'\bdepariment\b': 'department',
        r'\bEsplain\b': 'Explain',
        r'\bExpain\b': 'Explain',
        r'\bStale\b': 'State',
        r'\bWhatis\b': 'What is',
        r'\bExplainany\b': 'Explain any',
        r'\bEsplainany\b': 'Explain any',
        r'\bfourterms\b': 'four terms',
        r'\bplanningany\b': 'planning any',
        r'\bExpainrocrultment\b': 'Explain recruitment',
        r'\bp\s+Janning\b': 'planning',
    }
    for pattern, replacement in glued_token_repairs.items():
        t = re.sub(pattern, replacement, t, flags=re.IGNORECASE)

    # Strip header/footer noise wherever it appears in the line.
    for pattern in _QUESTION_NOISE_PATTERNS:
        t = re.sub(pattern, ' ', t, flags=re.IGNORECASE)

    # Remove stray separator runs and OCR crumbs that commonly appear between labels.
    t = re.sub(r'(?i)\b(?:co\s*\d+|q\s*\d+|ques?\.?\s*\d+)\b', ' ', t)
    t = re.sub(r'[=]{2,}', ' ', t)
    t = re.sub(r'[_~]{2,}', ' ', t)
    t = re.sub(r'\b(?:COS|C0S)\b(?=\s*$)', ' ', t)
    t = re.sub(r'\s*\)\s*$', '', t)
    # OCR often prefixes lines with junk symbols (=, +, quotes, bullets, etc.).
    # Keep stripping these so valid questions are not dropped by strict starters.
    t = re.sub(r'^\s*[\W_]+\s*', '', t)
    # Also remove stray single-letter list markers left at start after cleanup.
    t = re.sub(r'^\s*[a-zA-Z][\)\}\]:]\s*', '', t)
    # Tesseract sometimes repeats a short function word when a scan has bleed-
    # through. Collapse only a conservative list so technical repetition is
    # not altered (for example, "very very" or repeated variable names).
    repeated_words = r'(?:the|a|an|of|in|to|and|is|are|any|with|for|on|by)'
    t = re.sub(
        rf'\b({repeated_words})(?:\s+\1){{1,}}\b',
        r'\1',
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(r'\s{2,}', ' ', t).strip()

    # Recover a common OCR fragment such as
    # "The importance management ... Stale ..." as a standard question.
    importance_match = re.search(
        r'\bthe\s+importance\s+(?:of\s+)?([A-Za-z][A-Za-z-]*)\b',
        t,
        re.IGNORECASE,
    )
    has_action = re.search(
        r'\b(?:state|explain|define|describe|discuss|list|write|compare|differentiate)\b',
        t,
        re.IGNORECASE,
    )
    if importance_match and (
        not has_action
        or not re.search(r'\bthe\s+importance\s+of\b', t, re.IGNORECASE)
    ):
        subject = importance_match.group(1)
        t = f'State the importance of {subject}.'

    return t


def _normalize_co_label(co_str: str) -> str | None:
    """Normalize a CO label from various OCR forms to canonical 'CO{n}'.

    Handles digits, ordinals, Roman numerals and spelled-out numbers.
    Returns e.g. 'CO1' or None when no sensible value found.
    """
    if not co_str:
        return None
    s = str(co_str).upper().strip()
    # tolerate spaced or punctuated OCR like 'C O 2', 'CO-2', 'C.O.2'
    s_nospace = re.sub(r'[^A-Z0-9IVXLCDM]', '', s)
    # Common OCR corruption duplicates the leading C: 'CCO5' -> 'CO5'.
    s_nospace = re.sub(r'^C{2,}(?=[O0Q])', 'C', s_nospace)

    # OCR-fuzzy branch: accept common CO lookalikes such as COT, COI, C02,
    # COQ3, C0S, etc., but avoid normal words like COURSE.
    if re.match(r'^C[O0Q]', s_nospace) and re.fullmatch(r'[0-9OQILTSIVXLCDM]{1,6}', s_nospace[2:]):
        fuzzy = re.sub(r'^C[O0Q]', 'CO', s_nospace)
        fuzzy = fuzzy.translate(str.maketrans({'I': '1', 'L': '1', 'T': '1', 'S': '5'}))
        m = re.search(r'\d+', fuzzy)
        if m and int(m.group(0)) > 0:
            return f"CO{int(m.group(0))}"
        m = re.search(r'\b([IVXLCDM]{1,4})\b', fuzzy)
        if m:
            r = m.group(1)
            roman_map = {
                'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5,
                'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10
            }
            val = roman_map.get(r)
            if val:
                return f"CO{val}"

    # Common OCR corruption of CO5 as COS / C0S.
    if s_nospace in {'COS', 'C0S'}:
        return 'CO5'

    # Direct digits or ordinals: CO1, CO 1, CO-1, CO 1st.
    m = re.search(r'(?:CO\s*[-: ]*|\b)?(\d{1,2})(?:ST|ND|RD|TH)?\b', s)
    if m:
        value = int(m.group(1))
        return f"CO{value}" if value > 0 else None

    # Roman numerals mapping
    roman_map = {
        'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5,
        'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10
    }
    m = re.search(r'\b(?:CO\s*[-: ]*)?([IVXLCDM]{1,4})\b', s)
    if m:
        r = m.group(1)
        val = roman_map.get(r)
        if val:
            return f"CO{val}"

    # Spelled-out numbers
    words = {
        'ONE': 1, 'TWO': 2, 'THREE': 3, 'FOUR': 4, 'FIVE': 5,
        'SIX': 6, 'SEVEN': 7, 'EIGHT': 8, 'NINE': 9, 'TEN': 10
    }
    for w, v in words.items():
        if re.search(rf'\b{w}\b', s):
            return f"CO{v}"

    # Last-resort: isolated token
    m = re.search(r'\b(\d{1,2}|[IVXLCDM]{1,4})\b', s_nospace)
    if m:
        token = m.group(1)
        if token.isdigit() and int(token) > 0:
            return f"CO{int(token)}"
        token = token.upper()
        if token in roman_map:
            return f"CO{roman_map[token]}"

    return None


def _is_valid_co_label(value: str) -> bool:
    """Return whether a normalized value is a positive, structural CO label."""
    return bool(re.fullmatch(r'CO[1-9]\d{0,2}', str(value or '').strip(), re.IGNORECASE))


def _extract_explicit_co_from_text(text: str) -> str | None:
    """Find a confident CO label embedded in OCR text.

    CO labels are accepted at a line boundary or immediately before a
    sub-question marker/punctuation. This avoids treating chemistry text such
    as ``CO2 emissions`` as a course outcome.
    """
    if not text:
        return None

    token_re = re.compile(
        r'(?<![A-Za-z])C{1,3}\s*[O0Q]\s*[-_.:]?\s*'
        r'([0-9OQILTSIVXLCDM]{1,4})',
        re.IGNORECASE,
    )
    for match in token_re.finditer(str(text)):
        following = str(text)[match.end():]
        at_boundary = (
            match.start() <= 2
            or re.match(r'\s*(?:[:.,;)]|[a-hA-H]\))', following)
            or not following.strip()
        )
        if not at_boundary:
            continue
        normalized = _normalize_co_label(match.group(0))
        if _is_valid_co_label(normalized):
            return normalized
    return None

def detect_math_content(text):
    """Detect if text contains mathematical expressions"""
    math_patterns = [
        r'[x-z]\^[\d]+',  # Variables with exponents: x^2, y^3
        r'\\?[a-z]+\([^)]+\)',  # Functions: sin(x), log(x), sqrt(x)
        r'[+\-*/=]\s*\d',  # Math operations with numbers
        r'\d+\s*[+\-*/=]\s*\d+',  # Numeric expressions: 2+3, 5*4
        r'\\?frac\{[^}]+\}\{[^}]+\}',  # LaTeX fractions
        r'\d+/\d+',  # Simple fractions: 1/2, 3/4
        r'lim|sin|cos|tan|log|ln|exp|sqrt',  # Math functions
        r'\b[a-z]\s*[=<>]\s*\d',  # Equations: x = 5, y > 3
        r'\d+[a-z]\s*[+\-]',  # Algebraic: 2x + 3y
        r'[∫∑∏√π]',  # Math symbols (if OCR captures them)
        r'\^2|\^3',  # Common exponents
    ]
    
    for pattern in math_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def _extract_numbers_from_text(text):
    """Return numeric tokens found in text, preserving appearance order."""
    if not text:
        return []

    numbers = []
    seen = set()
    covered_spans = []
    text_str = str(text)

    for pattern in (r'\d+\/\d+', r'\d+\.\d+', r'\d+(?:st|nd|rd|th)'):
        for match in re.finditer(pattern, text_str, re.IGNORECASE):
            value = match.group(0)
            if value not in seen:
                seen.add(value)
                numbers.append(value)
            covered_spans.append(match.span())

    def _overlaps(span):
        for start, end in covered_spans:
            if span[0] < end and span[1] > start:
                return True
        return False

    for match in re.finditer(r'\d+', text_str):
        if _overlaps(match.span()):
            continue
        value = match.group(0)
        if value not in seen:
            seen.add(value)
            numbers.append(value)

    return numbers

def extract_marks_from_text(text):
    """
    Extract marks from question text with enhanced extraction if available.
    Handles: '[4]', '(4)', '4 marks', '4M', '4m', 'M:4', 'M-4',
    leading zero like '04', standalone digit at end of line.
    
    Uses enhanced extraction if available, otherwise falls back to basic extraction.
    """
    # Use enhanced extraction if available
    if ENHANCEMENTS_AVAILABLE:
        try:
            return extract_marks_enhanced(text)
        except Exception as e:
            print(f"[OCR] Enhanced marks extraction failed: {e}")
            # Fall through to basic extraction
    
    # FALLBACK: Basic extraction patterns
    patterns = [
        r'\bMarks?\b\s*[:\-]?\s*(\d{1,2})\b',   # Marks: 4   Marks - 4
        r'\[(\d{1,2})\s*(?:marks?|M)?\]',         # [4], [6 marks]
        r'\((\d{1,2})\s*(?:marks?|M)?\)',         # (4), (6 marks)
        r'\b(\d{1,2})\s*(?:marks?|M)\b',          # 4 marks, 4M
        r'\b[Mm]\s*[:\-]?\s*(\d{1,2})\b',       # M:4, M-6
        r'(?:^|\s)(0?[1-9]|1[0-9]|20)(?:\s*$)',     # standalone 1-20 at end (incl 04)
    ]

    t = str(text or '').strip()
    # Try each pattern
    for pattern in patterns:
        match = re.search(pattern, t, re.IGNORECASE | re.MULTILINE)
        if match:
            # take the last non-None group
            val = next((g for g in reversed(match.groups()) if g is not None), None)
            if val is not None:
                try:
                    marks = int(str(val).lstrip('0') or '0')
                except Exception:
                    continue
                if 1 <= marks <= 50:
                    return marks

    # Try spelled numbers (one two three)
    words_map = {
        'ONE': 1, 'TWO': 2, 'THREE': 3, 'FOUR': 4, 'FIVE': 5,
        'SIX': 6, 'SEVEN': 7, 'EIGHT': 8, 'NINE': 9, 'TEN': 10,
        'TWELVE': 12, 'FOURTEEN': 14
    }
    for w, v in words_map.items():
        if re.search(rf'\b{w}\b\s*(?:marks?)?', t, re.IGNORECASE):
            return v

    return 4  # Default fallback


def _should_try_ai_marks(raw_text: str, resolved_marks: int | None) -> bool:
    """Return True when a model fallback is worth trying for marks."""
    if resolved_marks not in (None, 4):
        return False
    if not raw_text:
        return False

    t = str(raw_text)
    return bool(re.search(
        r'\b(?:marks?|mark\s*:?|m\s*:?|attempt\s+any|total\s*marks?)\b|[\[\(]\s*\d{1,3}\s*[\]\)]|\d{1,3}\s*(?:marks?|m)\b',
        t,
        re.IGNORECASE,
    ))


def _extract_marks_with_ai(raw_text: str, question_text: str = '') -> int | None:
    """Use Groq to infer marks only when the OCR text is ambiguous."""
    api_key = os.getenv('GROQ_API_KEY', '').strip()
    if not api_key or not raw_text:
        return None

    prompt = (
        "Extract the marks for this single exam question from OCR text. "
        "Use only explicit marks notation, section totals, or obvious marks clues. "
        "If the question belongs to a section like 'Attempt any 3 [12]', infer 4 marks each when appropriate. "
        "If no reliable marks can be determined, return 4. "
        "Return ONLY one integer between 1 and 50.\n\n"
        f"OCR text:\n{raw_text}\n\n"
    )
    if question_text and question_text != raw_text:
        prompt += f"Cleaned question text:\n{question_text}\n"

    try:
        client = Groq(api_key=api_key)
        models = [
            os.getenv('GROQ_PARSER_MODEL', 'llama-3.1-8b-instant'),
            'llama-3.3-70b-versatile',
        ]
        last_err = None
        for model_name in models:
            try:
                resp = client.chat.completions.create(
                    messages=[
                        {
                            'role': 'system',
                            'content': 'You extract only the marks value from OCR exam text and return a single integer.',
                        },
                        {'role': 'user', 'content': prompt},
                    ],
                    model=model_name,
                    temperature=0.0,
                    max_tokens=8,
                )
                content = (resp.choices[0].message.content or '').strip()
                match = re.search(r'\b(\d{1,2})\b', content)
                if match:
                    marks = int(match.group(1))
                    if 1 <= marks <= 50:
                        return marks
                return None
            except Exception as e:
                last_err = e
                continue
        if last_err:
            print(f"[OCR] AI marks fallback failed: {last_err}")
    except Exception as e:
        print(f"[OCR] AI marks fallback init failed: {e}")
    return None

def extract_bloom_level(text):
    """Extract Bloom's taxonomy level from question text"""
    bloom_keywords = {
        'K1': ['define', 'list', 'name', 'identify', 'state', 'what is', 'who is', 'when', 'where'],
        'K2': ['explain', 'describe', 'discuss', 'outline', 'summarize', 'interpret', 'compare'],
        'K3': ['apply', 'demonstrate', 'solve', 'calculate', 'use', 'illustrate', 'implement'],
        'K4': ['analyze', 'examine', 'investigate', 'categorize', 'differentiate', 'distinguish'],
        'K5': ['evaluate', 'assess', 'critique', 'justify', 'argue', 'defend', 'judge'],
        'K6': ['create', 'design', 'develop', 'construct', 'formulate', 'propose', 'synthesize']
    }
    
    text_lower = text.lower()
    
    # Check for explicit Bloom level notation (K1, K2, etc.)
    bloom_match = re.search(r'\bK[1-6]\b', text, re.IGNORECASE)
    if bloom_match:
        return bloom_match.group(0).upper()
    
    # Infer from keywords
    for level, keywords in bloom_keywords.items():
        for keyword in keywords:
            if keyword in text_lower:
                return level
    
    return 'K2'  # Default to K2 (Understanding)


def _compute_question_confidence(question: dict, raw_text: str = '') -> float:
    """Compute parser confidence score in [0,1] for extracted questions."""
    qn = str(question.get('question_number', '')).strip()
    text = str(question.get('question_text', '')).strip()
    words = re.findall(r'[A-Za-z]{2,}', text)
    has_verb = bool(re.search(
        r'\b(?:Explain|Define|Describe|Write|Differentiate|Compare|State|List|Discuss|Illustrate)\b',
        text,
        re.IGNORECASE,
    ))

    numbering_score = 1.0 if re.fullmatch(r'\d+', qn) else 0.5
    completeness_score = min(1.0, len(words) / 10.0)
    clean_chars = len(re.findall(r'[A-Za-z0-9\s,.;:()\-\[\]/]', text))
    cleanliness_score = (clean_chars / max(1, len(text))) if text else 0.0
    certainty_score = 1.0 if has_verb else 0.25

    # Penalize OCR-junk starts from original line.
    if raw_text and re.match(r'^\s*[=+\-"\':;\[\]{}()<>`~|\\]', raw_text):
        cleanliness_score *= 0.6

    score = (0.25 * numbering_score +
             0.30 * completeness_score +
             0.20 * cleanliness_score +
             0.25 * certainty_score)
    return round(max(0.0, min(1.0, score)), 2)


def _looks_truncated_question(text: str) -> bool:
    """Detect OCR fragments that should not be presented as accepted questions."""
    if not text:
        return True

    normalized = re.sub(r'\s+', ' ', str(text)).strip()
    if re.search(r'\b(?:and|or|of|to|the|a|an)\.?$', normalized, re.IGNORECASE):
        return True
    if re.search(r'\b[A-Za-z]\.?$', normalized):
        return True
    if re.search(r'\b(?:stom|necose|emerits|cosd)\b|\bc\s+o\b', normalized, re.IGNORECASE):
        return True
    if re.search(r'\b(?:THREE\s+S[O0]O|ane\s+woe|avoaccidents)\b', normalized, re.IGNORECASE):
        return True
    return bool(re.search(
        r'\b(?:minimum|management|organizational|organization|production|'
        r'industrial|marketing|inventory|resource|procedure|department)\s+[A-Za-z]{1,2}\.?$',
        normalized,
        re.IGNORECASE,
    ))


def _contains_ocr_noise(text: str) -> bool:
    """Detect artifacts that make a question unsafe to accept automatically."""
    if not text:
        return True
    if re.search(r'(^|\s)\d{3,}\s*[&@#)]', text):
        return True
    if re.search(r'[©®�%}]', text):
        return True
    if text.count('"') % 2 or text.count("'") % 2:
        return True
    if re.search(r'\b(?:THREE|FOUR|FIVE)\s+[A-Za-z]?[\'"`]', text, re.IGNORECASE):
        return True
    return False

def validate_and_clean_question(question):
    """
    Validate and clean extracted question data with enhancements.
    Applies spell checking, grammar validation, and improved marks extraction if available.
    Returns cleaned question dict or None if invalid
    """
    if not question or not isinstance(question, dict):
        return None

    # Validation adds derived fields and review flags. Work on an isolated
    # copy so retry/fallback passes see the original parser output unchanged.
    question = deepcopy(question)
    
    # Get question text and clean it before applying strict validation.
    raw_q_text = str(question.get('question_text', '')).strip()
    q_text = clean_text(_clean_question_body(raw_q_text))
    
    # Apply spelling correction if enhancements available
    if ENHANCEMENTS_AVAILABLE:
        try:
            q_text = correct_spelling(q_text)
            question['spelling_checked'] = True
        except Exception as e:
            print(f"[OCR] Spell checking failed: {e}")

    if not q_text or len(q_text) < 10:  # Too short to be a valid question
        return None

    # Apply grammar validation if enhancements available
    if ENHANCEMENTS_AVAILABLE:
        try:
            q_text, grammar_issues = GrammarValidator.validate_question_grammar(q_text)
            # Grammar fixes can add an article after OCR cleanup. Normalize
            # repeated function words once more before persisting the record.
            q_text = clean_text(_clean_question_body(q_text))
            if grammar_issues:
                question['grammar_issues'] = grammar_issues
                question['grammar_checked'] = True
        except Exception as e:
            print(f"[OCR] Grammar checking failed: {e}")

    # Drop if what remains still looks like a paper header rather than a question.
    if not q_text or len(q_text) < 10:
        return None
    if re.match(r'^(?:government|polytechnic|institute|college|university|academically|question paper|summer examination|winter examination)\b', q_text, re.IGNORECASE):
        return None
    if not re.match(r'^(?:state|explain|describe|discuss|define|list|write|draw|draft|prepare|compare|differentiate|enumerate|solve|answer|identify|justify|comment|illustrate|sketch|prove|calculate|name|mention|choose|fill|do|transform|compose|formulate|elaborate|summari[sz]e|read|make|what\s*is|what\s*are|why\s*is|why\s*are|how\s*does|how\s*do|how\s*can|give|show|outline|trace|difference|advantages|disadvantages|features|classification|types|importance|purpose|meaning|concept|principle|function|procedure|methods|role|objective|application|applications|comparison|relationship|criteria|steps|summary|\d+\s*[.)]|[a-h][\)\}\]:]|(?:i{1,3}|iv|v|vi{0,3}|ix|x)[\)\}\]:])', q_text, re.IGNORECASE):
        # Keep only if it clearly reads like a question and not metadata.
        # Some valid questions begin with noun phrases instead of imperative verbs.
        # The stronger content checks below still reject non-questions.
        if not re.search(r'\b(?:difference|advantages|disadvantages|features|classification|types|importance|purpose|meaning|concept|principle|function|procedure|methods|role|objective|application|applications|comparison|relationship|criteria|steps|summary)\b', q_text, re.IGNORECASE):
            return None

    # Require at least four meaningful words.
    meaningful_words = re.findall(r'[A-Za-z]{2,}', q_text)
    if len(meaningful_words) < 4:
        return None

    # Require at least one academic action verb or a clear noun-led question pattern.
    if not (
        re.search(r'\b(?:Explain|Define|Describe|Write|Differentiate|Compare|State|List|Discuss|Illustrate|Choose|Fill|Do|Transform|Compose|Draft|Formulate|Elaborate|Summari[sz]e|Read|Make|Answer|Calculate|Solve|Comment|Justify|Prove|What\s*is|What\s*are|Why\s*is|Why\s*are|How\s*does|How\s*do|How\s*can|Give|Show|Outline|Trace|Name|Mention)\b', q_text, re.IGNORECASE)
        or re.search(r'\b(?:difference|advantages|disadvantages|features|classification|types|importance|purpose|meaning|concept|principle|function|procedure|methods|role|objective|application|applications|comparison|relationship|criteria|steps|summary)\b', q_text, re.IGNORECASE)
    ):
        return None
    
    # Update question with cleaned and enhanced text
    question['question_text'] = q_text
    question['identified_numbers'] = _extract_numbers_from_text(raw_q_text or q_text)
    
    # Ensure marks is valid: coerce strings, fallback to extraction from text
    marks = question.get('marks', None)
    resolved_marks = None
    if isinstance(marks, int) and not isinstance(marks, bool):
        resolved_marks = marks
    elif isinstance(marks, str):
        # Try direct integer parse
        mstr = re.sub(r'[^0-9]', '', marks.strip())
        if mstr:
            try:
                resolved_marks = int(mstr)
            except Exception:
                resolved_marks = None
        else:
            # Try to extract from the string content
            resolved_marks = extract_marks_from_text(marks)
    else:
        # Try to extract from the question text
        resolved_marks = extract_marks_from_text(q_text)

    if not isinstance(resolved_marks, int) or resolved_marks < 1 or resolved_marks > 50:
        resolved_marks = 4

    if _should_try_ai_marks(raw_q_text, resolved_marks):
        ai_marks = _extract_marks_with_ai(raw_q_text, q_text)
        if isinstance(ai_marks, int) and 1 <= ai_marks <= 50:
            resolved_marks = ai_marks
    
    # Validate marks with enhanced validation if available
    if ENHANCEMENTS_AVAILABLE:
        try:
            resolved_marks, marks_confidence = validate_marks_extraction(q_text, resolved_marks)
            question['marks_confidence'] = marks_confidence
            question['marks_validated'] = True
        except Exception as e:
            print(f"[OCR] Marks validation failed: {e}")
    
    question['marks'] = resolved_marks
    
    # Ensure course outcome is valid without inventing CO1 when OCR missed it.
    co = str(question.get('course_outcome') or question.get('co') or '')
    parsed_co = _normalize_co_label(co) or _extract_explicit_co_from_text(raw_q_text)
    if parsed_co and parsed_co not in {f'CO{i}' for i in range(1, 6)}:
        parsed_co = None
    question['course_outcome'] = parsed_co or ''
    if not parsed_co:
        question.setdefault('review_flags', []).append('Course outcome not confidently identified')
    if _contains_ocr_noise(q_text):
        question.setdefault('review_flags', []).append('OCR noise requires review')
    question['review_flags'] = list(dict.fromkeys(question.get('review_flags', [])))
    
    # Ensure bloom level is valid
    bloom = str(question.get('bloom_level') or 'K2').upper()
    if not re.fullmatch(r'K[1-6]', bloom):
        question['bloom_level'] = 'K2'
    else:
        question['bloom_level'] = bloom

    # Preserve sub_questions array if present (smart-extractor feature)
    if 'sub_questions' not in question:
        question['sub_questions'] = []

    # Preserve sub_label if present (a, b, c …)
    # (no validation needed – it's just a string label)

    # Confidence and review status.
    confidence = _compute_question_confidence(question, raw_text=raw_q_text)
    if _looks_truncated_question(q_text):
        confidence = min(confidence, 0.45)
        question.setdefault('review_flags', []).append('Possible OCR truncation')
    question['confidence_score'] = confidence
    question['status'] = (
        'needs_review'
        if confidence < 0.75 or question.get('review_flags')
        else 'accepted'
    )
    
    # Mark that enhancements were applied
    if ENHANCEMENTS_AVAILABLE:
        question['enhancements_applied'] = True

    return question


def validate_and_clean_question_loose(question):
    """
    Relaxed validator that accepts shorter/noisier candidates for
    "aggressive recall". Returns a cleaned question dict with
    status 'needs_review' or None if clearly invalid.
    """
    # First try strict validator
    strict = validate_and_clean_question(question)
    if strict:
        # force needs_review when confidence is low
        if strict.get('confidence_score', 1.0) < 0.6:
            strict['status'] = 'needs_review'
        return strict

    # Build a minimal relaxed candidate
    if not question or not isinstance(question, dict):
        return None

    raw = str(question.get('question_text', '')).strip()
    if not raw:
        return None

    # Require at least 2 words of length>=2 to avoid pure garbage
    meaningful = re.findall(r'[A-Za-z]{2,}', raw)
    if len(meaningful) < 2:
        return None

    q = dict(question)
    q['question_text'] = _clean_question_body(raw)
    q['marks'] = int(question.get('marks') or extract_marks_from_text(raw) or 4)
    q['course_outcome'] = _normalize_co_label(question.get('course_outcome') or '') or ''
    if not q['course_outcome']:
        q.setdefault('review_flags', []).append('Course outcome not confidently identified')
    q['bloom_level'] = question.get('bloom_level') or extract_bloom_level(q['question_text'])
    q['has_math'] = detect_math_content(q['question_text'])
    q['identified_numbers'] = _extract_numbers_from_text(raw)
    q['has_diagram'] = bool(re.search(r'\b(diagram|draw|figure|sketch|graph|chart)\b', q['question_text'], re.IGNORECASE))
    q.setdefault('sub_questions', question.get('sub_questions', []))

    q['confidence_score'] = _compute_question_confidence(q, raw_text=raw)
    q['status'] = 'needs_review'
    return q


def _normalize_extracted_result(result: dict, extracted_images=None) -> dict:
    """Split merged question_text entries in any parsed result before storage.

    This runs on both AI-parsed and regex-parsed outputs so uploads behave the
    same way regardless of which parser produced the first pass.
    """
    if not result or not isinstance(result, dict):
        return result

    normalized = {
        **result,
        'papers': [],
    }

    total_before = 0
    total_after = 0

    for paper in result.get('papers', []):
        total_before += len(paper.get('questions', []))
        rebuilt_questions = []
        for question in paper.get('questions', []):
            text = str(question.get('question_text', '')).strip()
            if not text:
                continue

            split_text = _split_compound_question_lines(text)
            # Question counts can look plausible even when one record contains
            # many merged stems and other records are duplicates. Apply the
            # stem-aware splitter to suspicious compound records before using
            # the count-based fallback below.
            stem_count = len(re.findall(
                r'\b(?:enlist|explain|define|describe|differentiate|list|state|'
                r'classify|attempt|prepare|discuss|compare|justify)\b',
                text,
                re.IGNORECASE,
            ))
            if stem_count >= 2:
                split_text = _aggressive_fallback_split(split_text)
            split_lines = [ln.strip() for ln in split_text.splitlines() if ln.strip()]

            if len(split_lines) > 1:
                parsed = parse_papers_and_extract_questions(split_text, extracted_images or [], _allow_block_split=False)
                parsed_questions = parsed.get('papers', [{}])[0].get('questions', []) if parsed.get('papers') else []
                if len(parsed_questions) > 1:
                    for parsed_question in parsed_questions:
                        validated = validate_and_clean_question(dict(parsed_question))
                        if validated:
                            rebuilt_questions.append(validated)
                    continue

            validated = validate_and_clean_question(dict(question))
            if validated:
                rebuilt_questions.append(validated)

        unique_questions = []
        seen_question_keys = set()
        for question in rebuilt_questions:
            question_key = re.sub(
                r'\W+',
                ' ',
                str(question.get('question_text', '')).casefold(),
            ).strip()
            if not question_key or question_key in seen_question_keys:
                continue
            seen_question_keys.add(question_key)
            unique_questions.append(question)
        rebuilt_questions = unique_questions

        for idx, question in enumerate(rebuilt_questions, start=1):
            question['question_number'] = str(idx)
        total_after += len(rebuilt_questions)

        new_paper = dict(paper)
        new_paper['questions'] = rebuilt_questions
        normalized['papers'].append(new_paper)

    normalized['total_papers'] = len(normalized['papers'])
    if 'total_images_detected' in result:
        normalized['total_images_detected'] = result.get('total_images_detected', 0)
    if 'images_folder' in result:
        normalized['images_folder'] = result.get('images_folder', {})

    # Fallback: if extraction produced far fewer questions than expected,
    # run an aggressive splitter on original question blocks to try and
    # recover missed boundaries. This helps for heavily-noisy OCR where
    # labels are mangled and initial parsing undercounts questions.
    EXPECTED_MIN = 20
    if total_after < EXPECTED_MIN:
        print(f"DEBUG: Too few questions ({total_after}) — running aggressive fallback split")
        repaired_papers = []
        for paper in result.get('papers', []):
            new_qs = []
            for q in paper.get('questions', []):
                q_text = str(q.get('question_text', '')).strip()
                if not q_text:
                    continue

                # If parser grouped list items under one parent, expand each item
                # into a candidate question to improve individual question recall.
                sub_items = q.get('sub_questions') or []
                if isinstance(sub_items, list) and sub_items:
                    for item in sub_items:
                        sub_text = str((item or {}).get('text', '')).strip()
                        if not sub_text:
                            continue
                        candidate = {
                            'question_text': clean_text(f"{q_text} {sub_text}"),
                            'marks': q.get('marks'),
                            'course_outcome': q.get('course_outcome'),
                            'bloom_level': q.get('bloom_level'),
                            'has_math': bool(q.get('has_math', False)),
                            'has_diagram': bool(q.get('has_diagram', False)),
                            'images': q.get('images', []),
                            'sub_questions': [],
                            'sub_label': q.get('sub_label', ''),
                        }
                        v = validate_and_clean_question_loose(candidate)
                        if v:
                            new_qs.append(v)

                ag = _aggressive_fallback_split(q_text)
                parts = [ln.strip() for ln in ag.split('\n') if ln.strip()]
                if len(parts) > 1:
                    for part in parts:
                        candidate = {
                            'question_text': clean_text(part),
                            'marks': q.get('marks'),
                            'course_outcome': None,
                            'bloom_level': None,
                            'has_math': False,
                            'has_diagram': False,
                            'images': [],
                            'sub_questions': []
                        }
                        # Try to recover CO label from the split part
                        m = re.search(r'\bC[O0Q][\s\-\.:]*\d+', part, re.IGNORECASE)
                        if m:
                            parsed = _normalize_co_label(m.group(0))
                            if parsed:
                                candidate['course_outcome'] = parsed

                        v = validate_and_clean_question_loose(candidate)
                        if v:
                            new_qs.append(v)
                else:
                    v = validate_and_clean_question(dict(q))
                    if v:
                        new_qs.append(v)

            for idx, question in enumerate(new_qs, start=1):
                question['question_number'] = str(idx)

            new_paper = dict(paper)
            new_paper['questions'] = new_qs
            repaired_papers.append(new_paper)

        normalized['papers'] = repaired_papers
        total_after = sum(len(p.get('questions', [])) for p in normalized['papers'])
        # If aggressive fallback still undercounts, try a noisy-line extractor
        # that treats many short lines as candidate questions and merge them
        # as `needs_review` so manual verification can recover missed items.
        if total_after < EXPECTED_MIN:
            print(f"DEBUG: Aggressive fallback ({total_after}) insufficient — running noisy-line extractor")
            # build seen keyset from current normalized questions
            seen = set()
            for p in normalized.get('papers', []):
                for q in p.get('questions', []):
                    k = re.sub(r'\W+', ' ', str(q.get('question_text','')).lower()).strip()
                    if k:
                        seen.add(k)

            # Concatenate original question_text blocks as input for noisy extractor
            raw_concat = ' '.join(
                [str(q.get('question_text','')) for p in result.get('papers', []) for q in p.get('questions', [])]
            )
            noisy = _extract_questions_from_noisy_lines(raw_concat)
            added = 0
            for cand in noisy:
                v = validate_and_clean_question_loose(cand)
                if not v:
                    continue
                k = re.sub(r'\W+', ' ', v.get('question_text','').lower()).strip()
                if not k or k in seen:
                    continue
                seen.add(k)
                v['status'] = 'needs_review'
                v['confidence_score'] = round(v.get('confidence_score', 0.0), 2)
                # append to first paper
                if normalized.get('papers'):
                    normalized['papers'][0]['questions'].append(v)
                else:
                    normalized['papers'] = [{
                        'paper_number': 1,
                        'paper_name': 'Question Paper',
                        'questions': [v]
                    }]
                added += 1

            if added:
                total_after = sum(len(p.get('questions', [])) for p in normalized['papers'])
                print(f"Noisy-line merge added {added} questions: now {total_after}")

    print(f"DEBUG: Normalized extracted result {total_before} -> {total_after} questions")
    return normalized


def parse_papers_and_extract_questions(content, extracted_images=[], _allow_block_split=True):
    """
    Smart hierarchical question parser for MSBTE-style papers.

    Understands the three-level structure:
      Level 1 – Main section header  : Q.1, Q.2 … (Attempt any N)
      Level 2 – Sub-question         : CO1 a) … / a) … / b) …
      Level 3 – List items inside SQ : i) … / ii) … / 1) … / 2) …

    Sub-question list items are collected into a `sub_questions` array and
    also appended to the full question_text so the flat question list remains
    backwards-compatible with the existing front-end.
    """

    # Pre-clean OCR noise first, then split glued question markers.
    content = _preprocess_ocr_text(content)
    content = _split_compound_question_lines(content)

    # Split multi-paper PDFs into separate blocks when clear boundaries exist.
    if _allow_block_split:
        blocks = _split_into_paper_blocks(content)
        if len(blocks) > 1:
            merged_papers = []
            total_images = 0
            images_folder = {}
            for idx, block in enumerate(blocks, start=1):
                parsed = parse_papers_and_extract_questions(block, extracted_images, _allow_block_split=False)
                for paper in parsed.get('papers', []):
                    paper_obj = dict(paper)
                    paper_obj['paper_number'] = len(merged_papers) + 1
                    merged_papers.append(paper_obj)
                total_images += int(parsed.get('total_images_detected', 0) or 0)
                if isinstance(parsed.get('images_folder'), dict):
                    images_folder.update(parsed.get('images_folder'))

            return {
                'total_papers': len(merged_papers),
                'exam_info': {},
                'papers': merged_papers,
                'total_images_detected': total_images,
                'images_folder': images_folder,
            }

    # ── Compiled patterns ────────────────────────────────────────────────────
    # Main question header: Q.1  Q. 2  Q 3  Que.1  Q1.
    MAIN_Q_RE = re.compile(
        r'^\s*Q(?:ue?)?\.?\s*(\d+)\b', re.IGNORECASE
    )
    co_token = r'C{1,3}\s*[O0Q]\s*[-_.:]?\s*[0-9OQILTSIVXLCDM]{1,6}'
    # Sub-question line: [OCR artifacts] [CO<n>] [a-e])  rest-of-text
    # Handles: "CO1 a) …", "CO2: b) …", "a) …", "_ b) …", "~ c) …"
    SUB_Q_RE = re.compile(
        rf'^[_~—–\-\s]*(?:({co_token})[:\s]*)?[_~—–\-\s]*([A-Za-z]{{1,3}})[\)\}}\]:]\s*(.*)',
        re.IGNORECASE
    )
    CO_START_RE = re.compile(
        rf'^\s*{co_token}\b.*[A-Za-z]',
        re.IGNORECASE,
    )
    # Roman-numeral / simple-digit list items: i) ii) iii) iv) v) / 1) 2) …
    # Strict roman pattern to avoid matching words ('in', 'is', 'iv' as prefix)
    ROMAN_RE = re.compile(
        r'^[_~—–\-\s]*'
        r'(i{1,3}|iv|vi{0,3}|ix|xi{0,3}|xiv|xv|'   # small romans up to xv
        r'[1-9]|[1-9][0-9])'                          # or digits 1-99
        r'\)\s+(.+)',
        re.IGNORECASE
    )
    # Lines we never want to process
    SKIP_RE = re.compile(
        r'^(?:GOVERNMENT|POLYTECHNIC|(?:Mid|End)\s*Sem|Examination|'
        r'Instructions|--- PAGE|IMAGES DETECTED|Marks\s*:|'
        r'Total\s*Marks|Subject\s*:|Branch\s*:|Semester\s*:|'
        r'Time\s*:|Roll\s*No|Seat\s*No)',
        re.IGNORECASE
    )
    # Lines that signal the start of a new main-section (we skip for content)
    SECTION_HDR_RE = re.compile(
        r'Attempt\s+any|All\s+questions\s+are\s+compulsory',
        re.IGNORECASE
    )
    QUESTION_START_RE = re.compile(
        r'^(?:'
        r'(?:state|states|explain|describe|discuss|define|enlist|list|write|draw|draft|prepare|compare|differentiate|enumerate|solve|answer|identify|justify|comment|illustrate|sketch|prove|calculate|name|mention|what|why|how|give|show|outline|trace)\b'
        r'|\d+\s*[.)]\s*'
        r'|[a-hA-H][\)\}\]:]\s*'
        r'|(?:i{1,3}|iv|v|vi{0,3}|ix|x)[\)\}\]:]\s*'
        r')',
        re.IGNORECASE
    )
    HEADER_NOISE_RE = re.compile(
        r'^(?:'
        r'GOVERNMENT|POLYTECHNIC|INSTITUTE|COLLEGE|UNIVERSITY|ACADEM|'
        r'QUESTION\s*PAPER|SUMMER\s*EXAMINATION|WINTER\s*EXAMINATION|'
        r'PROGRAMME|DIPLOMA|BRANCH|SEMESTER|DURATION|MAXIMUM\s*MARKS|'
        r'TIME\s*:?|SUBJECT\s*:?|MARKS\s*:?|PAGE\s*\d+|ROLL\s*NO|SEAT\s*NO'
        r')\b',
        re.IGNORECASE
    )
    INSTRUCTION_NOISE_RE = re.compile(
        r'(?:illustrate\s+your\s+answers|answers\s+with\s+neat\s+sketches|'
        r'use\s+of\s+mathematical\s+tables|figures\s+to\s+the\s+right\s+indicate\s+full\s+marks|'
        r'assume.*additional\s+data|assume.*necessary|communication\s+instruments\s+such\s+as|'
        r'all\s+questions\s+are\s+compulsory)'
        r'|(?:instruction|instructions)\s*[:.]?$',
        re.IGNORECASE
    )
    STANDALONE_CO_RE = re.compile(rf'^\s*({co_token})\s*[:\-\.]?\s*$', re.IGNORECASE)

    # ── State ─────────────────────────────────────────────────────────────────
    questions       = []
    page_images     = {}
    assigned_images = set()
    current_page    = 1
    current_co      = ''           # last explicit CO, carried forward
    current_sub     = None         # dict holding the open sub-question
    pending_subs    = []           # sub-questions waiting for section flush
    started_questions = False      # set once real question content begins
    current_section_attempt_count = None
    current_section_total_marks    = None
    current_section_marks_each     = None

    # Group images by page
    for img in extracted_images:
        pg = img.get('page', 1)
        page_images.setdefault(pg, []).append(img)

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _assign_image(page_num, has_diagram):
        """Return a Cloudinary image entry if one is available for this page."""
        if not has_diagram:
            return []
        for img in page_images.get(page_num, []):
            img_id = f"{img['page']}_{img['filename']}"
            if img_id not in assigned_images:
                assigned_images.add(img_id)
                return [{
                    'filename': img['filename'],
                    'url': img.get('cloudinary_url', img.get('url', '')),
                    'width': img['width'],
                    'height': img['height']
                }]
        return []

    def _build_question_text(header, list_items, continuations):
        """
        Assemble the question_text from header + continuations ONLY.
        list_items are stored in sub_questions[], never inlined into question_text.
        continuations – plain extra lines that are part of the question instruction.
        """
        parts = [header.strip()] if header.strip() else []

        # Append plain continuation lines that are part of the instruction
        for c in continuations:
            c = c.strip()
            if c:
                parts.append(c)

        # NOTE: list_items are NOT appended here — they live in sub_questions[]
        return ' '.join(parts)

    def _word_to_int(token):
        token = str(token or '').strip().upper()
        if token.isdigit():
            return int(token)
        word_map = {
            'ONE': 1, 'TWO': 2, 'THREE': 3, 'FOUR': 4, 'FIVE': 5,
            'SIX': 6, 'SEVEN': 7, 'EIGHT': 8, 'NINE': 9, 'TEN': 10,
            'ELEVEN': 11, 'TWELVE': 12, 'THIRTEEN': 13, 'FOURTEEN': 14,
            'FIFTEEN': 15, 'SIXTEEN': 16, 'SEVENTEEN': 17, 'EIGHTEEN': 18,
            'NINETEEN': 19, 'TWENTY': 20,
        }
        return word_map.get(token)

    def _parse_section_mark_info(text):
        """Return (attempt_count, total_marks) from a section header-like line."""
        attempt_count = None
        total_marks = None

        attempt_match = re.search(r'Attempt\s+any\s+([A-Za-z0-9]+)', text, re.IGNORECASE)
        if attempt_match:
            attempt_count = _word_to_int(attempt_match.group(1))

        total_match = re.search(r'\b(?:Marks?|Total\s*Marks?)\b\s*[:\-]?\s*(\d{1,3})\b', text, re.IGNORECASE)
        if not total_match:
            total_match = re.search(r'\[(\d{1,3})\]', text)
        if not total_match:
            total_match = re.search(r'\((\d{1,3})\)', text)
        if total_match:
            try:
                total_marks = int(total_match.group(1))
            except Exception:
                total_marks = None

        return attempt_count, total_marks

    def _resolve_section_marks(attempt_count, total_marks):
        if not attempt_count or not total_marks:
            return None
        if attempt_count <= 0 or total_marks <= 0:
            return None
        # OCR commonly misreads section totals like "(12)" as "(42)".
        # If the total is implausibly large for an Attempt any 3/5 section and
        # ends with 2, normalize it back to the standard 12-mark section.
        if attempt_count in (3, 5) and total_marks > 20 and total_marks % 10 == 2:
            total_marks = 12
        return max(1, round(total_marks / attempt_count))

    def _finalize_sub():
        """Close the currently open sub-question and push it to pending_subs."""
        nonlocal current_sub
        if current_sub is None:
            return

        s           = current_sub
        list_items  = s['list_items']
        full_text   = _build_question_text(s['header'], list_items, s['cont'])
        full_text   = _clean_question_body(full_text)

        # Strip stray mark notations added by OCR
        full_text = re.sub(r'\[?\(?\d+\s*(?:marks?|M)?\)?\]?', '', full_text).strip()
        full_text = _clean_question_body(full_text)

        if len(full_text) >= 10:
            # Prefer marks inferred from the section header, then explicit marks on
            # the sub-question itself, then fallback to marks in the text.
            marks = s.get('marks')
            if not isinstance(marks, int) or marks < 1:
                marks = extract_marks_from_text(full_text) or extract_marks_from_text(s.get('raw', ''))
            has_diagram = bool(re.search(
                r'\b(diagram|figure|graph|chart|image|illustration|draw|sketch)\b',
                full_text, re.IGNORECASE))
            has_math    = detect_math_content(full_text)
            bloom       = extract_bloom_level(full_text)

            # Build sub_questions array for any list items (even just one)
            subs_arr = [{'text': li} for li in list_items] if list_items else []

            pending_subs.append({
                'sub_label'      : s['label'],
                'question_text'  : full_text,
                'marks'          : marks,
                'course_outcome' : s['co'],
                'bloom_level'    : bloom,
                'has_math'       : has_math,
                'has_diagram'    : has_diagram,
                'images'         : _assign_image(s['page'], has_diagram),
                'sub_questions'  : subs_arr,
            })
            print(f"DEBUG  sub-q [{s['co']} {s['label']})]: {full_text[:60]}…")

        current_sub = None

    def _flush_pending():
        """Push all pending sub-questions into the main questions list."""
        for sq in pending_subs:
            obj = {
                'question_number': str(len(questions) + 1),
                **sq
            }
            v = validate_and_clean_question(obj)
            if v:
                questions.append(v)
        pending_subs.clear()

    # ── Main parse loop ───────────────────────────────────────────────────────
    for raw_line in content.split('\n'):
        stripped = raw_line.strip()

        # Normalize spaced or OCR-corrupted CO prefixes before sub-question
        # matching so labels such as "C O 3 a)" retain their outcome.
        co_prefix = re.match(rf'^({co_token})\s+(?=[A-Za-z]{{1,3}}[\)\}}\]:])', stripped, re.IGNORECASE)
        if co_prefix:
            parsed_prefix = _normalize_co_label(co_prefix.group(1))
            if parsed_prefix:
                stripped = f'{parsed_prefix} {stripped[co_prefix.end():].lstrip()}'

        # ① Track page marker
        pm = re.search(r'--- PAGE (\d+) ---', stripped)
        if pm:
            current_page = int(pm.group(1))
            continue

        # ② Ignore blank / noise lines
        if not stripped or len(stripped) < 3:
            continue
        if SKIP_RE.match(stripped) or HEADER_NOISE_RE.match(stripped):
            continue
        if INSTRUCTION_NOISE_RE.search(stripped):
            continue

        standalone_co = STANDALONE_CO_RE.match(stripped)
        if standalone_co:
            parsed = _normalize_co_label(standalone_co.group(1))
            if parsed:
                current_co = parsed
            continue

        # ③ Main question header  (Q.1, Q.2, …)
        if MAIN_Q_RE.match(stripped):
            _finalize_sub()
            _flush_pending()
            started_questions = True
            current_section_attempt_count = None
            current_section_total_marks = None
            current_section_marks_each = None
            # Optionally capture exam-level mark info from the header line
            # e.g. "Q.1 Attempt any FIVE of the following:  [10]"
            attempt_count, total_marks = _parse_section_mark_info(stripped)
            if attempt_count:
                current_section_attempt_count = attempt_count
            if total_marks:
                current_section_total_marks = total_marks
            current_section_marks_each = _resolve_section_marks(
                current_section_attempt_count,
                current_section_total_marks,
            )
            continue

        # ④ Also skip the "Attempt any …" sub-line that follows a Q. header
        if SECTION_HDR_RE.search(stripped):
            attempt_count, total_marks = _parse_section_mark_info(stripped)
            if attempt_count:
                current_section_attempt_count = attempt_count
            if total_marks:
                current_section_total_marks = total_marks
            current_section_marks_each = _resolve_section_marks(
                current_section_attempt_count,
                current_section_total_marks,
            )
            continue

        # Standalone section mark line, often emitted by OCR as "(12)" or "[20]".
        if started_questions and not current_sub:
            if re.fullmatch(r'\s*[\(\[]\s*\d{1,3}\s*[\)\]]\s*', stripped):
                _, total_marks = _parse_section_mark_info(stripped)
                if total_marks:
                    current_section_total_marks = total_marks
                    current_section_marks_each = _resolve_section_marks(
                        current_section_attempt_count,
                        current_section_total_marks,
                    )
                continue

        # ⑤ Sub-question line  (CO1 a) … / a) … / _ b) …)
        sm = SUB_Q_RE.match(stripped)
        if sm:
            _finalize_sub()                              # close previous SQ
            started_questions = True
            co_raw  = sm.group(1)
            label   = _normalize_inline_label(sm.group(2))
            rest    = sm.group(3).strip()

            if not label:
                continue

            # Update current CO if explicitly stated on this line
            if co_raw:
                parsed = _normalize_co_label(co_raw)
                if parsed:
                    current_co = parsed

            # Remove marks notation from rest text
            rest = re.sub(r'\[?\(?\d+\s*(?:marks?|M)?\)?\]?', '', rest).strip()

            current_sub = {
                'co'    : current_co,
                'label' : label,
                'header': rest,
                'marks' : current_section_marks_each,
                'list_items': [],
                'cont'  : [],
                'raw'   : stripped,
                'page'  : current_page,
            }
            continue

        # ⑥ List item inside an open sub-question  (i) ii) 1) 2) …)
        rm = ROMAN_RE.match(stripped)
        if rm and current_sub is not None:
            started_questions = True
            item_text = rm.group(2).strip()
            # Strip trailing mark notation from list item text
            item_text = re.sub(r'\[?\(?\d+\s*(?:marks?|M)?\)?\]?', '', item_text).strip()
            item_text = clean_text(item_text)
            if item_text and len(item_text) >= 3:
                current_sub['list_items'].append(item_text)
            continue

        # Some OCR lines contain both the CO label and the next sub-question,
        # e.g. "COS b) Draw and explain ...". Split them here so the new item
        # is not merged into the previous sub-question.
        co_compound = re.match(
            r'^((?:C[O0Q][0-9OQILTSIVXLCDM]{0,6}))\s*[_~—–\-\s]*([A-Za-z]{1,3}[\)\}\]:])\s*(.*)',
            stripped,
            re.IGNORECASE,
        )
        if co_compound:
            _finalize_sub()
            started_questions = True
            parsed = _normalize_co_label(co_compound.group(1))
            if parsed:
                current_co = parsed
            label = _normalize_inline_label(co_compound.group(2))
            rest = co_compound.group(3).strip()
            if label:
                current_sub = {
                    'co'    : current_co,
                    'label' : label,
                    'header': re.sub(r'\[?\(?\d+\s*(?:marks?|M)?\)?\]?','', rest).strip(),
                    'marks' : current_section_marks_each,
                    'list_items': [],
                    'cont'  : [],
                    'raw'   : stripped,
                    'page'  : current_page,
                }
            continue

        # If an open question is followed by a new CO-labeled line with real
        # text, close the current question first so the new line is parsed as a
        # separate question instead of being appended as continuation text.
        if current_sub is not None and (SUB_Q_RE.match(stripped) or MAIN_Q_RE.match(stripped) or CO_START_RE.match(stripped)):
            _finalize_sub()
            current_sub = None

        # A recovered stem without a label starts a new question. Close the
        # current item first instead of treating the line as continuation.
        if current_sub is not None and QUESTION_START_RE.match(stripped):
            _finalize_sub()
            current_sub = None

        # ⑦ Continuation / inline CO-only line
        if current_sub is not None:
            # Continuation: don't absorb a new sub-question or main header
            if (not SUB_Q_RE.match(stripped) and
                    not MAIN_Q_RE.match(stripped) and
                    len(stripped) >= 5):
                # CO-only prefix (e.g. "CO2  rest of text for current SQ")
                co_inline = re.match(r'^((?:C[O0Q][0-9OQILTSIVXLCDM]{0,6}))[:\s]+(.+)', stripped, re.IGNORECASE)
                if co_inline:
                    parsed = _normalize_co_label(co_inline.group(1))
                    if parsed:
                        current_sub['co'] = parsed
                    cont_text = co_inline.group(2).strip()
                    if cont_text:
                        current_sub['cont'].append(cont_text)
                else:
                    current_sub['cont'].append(stripped)
            continue

        # ⑧ Orphan line: CO + text without a sub-question letter
        #    e.g. "CO3  Give the meaning of the following words"
        co_only = re.match(r'^[_~—–\-\s]*((?:C[O0Q][0-9OQILTSIVXLCDM]{0,6}))[:\s]+(.+)', stripped, re.IGNORECASE)
        if co_only:
            _finalize_sub()
            started_questions = True
            parsed = _normalize_co_label(co_only.group(1))
            if parsed:
                current_co = parsed
            rest = co_only.group(2).strip()
            rest = re.sub(r'^[\W_]+', '', rest)
            rest_tokens = rest.split()
            if (len(rest_tokens) >= 2
                    and 1 <= len(re.sub(r'[^A-Za-z]', '', rest_tokens[0])) <= 3
                    and rest_tokens[1][:1].isupper()):
                rest = ' '.join(rest_tokens[1:])
            rest = re.sub(r'\[?\(?\d+\s*(?:marks?|M)?\)?\]?', '', rest).strip()
            if len(rest) >= 10:
                current_sub = {
                    'co'    : current_co,
                    'label' : str(len(pending_subs) + 1),
                    'header': rest,
                    'marks' : current_section_marks_each,
                    'list_items': [],
                    'cont'  : [],
                    'raw'   : stripped,
                    'page'  : current_page,
                }
            continue

        # ⑨ Plain line with no recognisable prefix and no open sub-question
        #    Treat as a standalone question if it looks long enough
        if len(stripped) >= 20 and (started_questions or QUESTION_START_RE.match(stripped)):
            if HEADER_NOISE_RE.match(stripped):
                continue
            _finalize_sub()
            started_questions = True
            current_sub = {
                'co'    : current_co,
                'label' : str(len(pending_subs) + 1),
                'header': stripped,
                'list_items': [],
                'cont'  : [],
                'raw'   : stripped,
                'page'  : current_page,
            }

    # ── End of document: flush remaining state ────────────────────────────────
    _finalize_sub()
    _flush_pending()

    print(f"DEBUG: Extracted {len(questions)} total questions")
    print(f"DEBUG: Detected {len(extracted_images)} images")

    if questions:
        return {
            'total_papers': 1,
            'exam_info': {},
            'papers': [{
                'paper_number': 1,
                'paper_name'  : 'Question Paper',
                'questions'   : questions
            }],
            'total_images_detected': len(extracted_images),
            'images_folder'        : page_images
        }
    else:
        print("WARNING: No questions extracted. Check PDF format and patterns.")
        print("First 500 chars of content:", content[:500])
        return {
            'total_papers': 0,
            'exam_info': {},
            'papers': [],
            'total_images_detected'  : len(extracted_images),
            'images_folder'          : page_images,
            'debug_content_sample'   : content[:1000]
        }

def ai_parse_questions(raw_text, extracted_images=[], groq_api_key=None, subject_context=None):
    """
    Use Groq LLM to parse raw OCR text from MSBTE question papers (optimized for speed).
    
    Returns dict matching standard extractor schema, or None on failure (falls back to regex).
    """
    api_key = groq_api_key or os.getenv(
        'GROQ_API_KEY',
        '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'
    )
    if not api_key:
        return None

    try:
        client = Groq(api_key=api_key)

        # Optimized, concise system prompt (fewer tokens = faster response)
        system_prompt = """Parse MSBTE question papers. Return ONLY a JSON array of questions:

[{
  "question_number": "1",
  "question_text": "Main instruction only (no list items)",
  "marks": 4,
    "course_outcome": "",
  "bloom_level": "K1",
  "has_math": false,
  "has_diagram": false,
  "sub_questions": [{"text": "item1"}, {"text": "item2"}],
  "sub_label": "a",
  "images": []
}]

RULES:
- question_text = parent instruction ONLY, never include list items
- sub_questions = array of {text: "..."} for numbered items (i, ii, iii or 1, 2, 3)
- marks: default 4
- bloom_level: infer from verb (list/define=K1, explain=K2, apply=K3, analyze=K4, evaluate=K5, create=K6)
- has_diagram: true if mentions figure/diagram/draw/sketch
- has_math: true if has equations/fractions/symbols
- course_outcome: normalize an explicit CO label from the OCR; use an empty string when absent
- sub_label: a/b/c/d/e/f/g of this question
- Ignore: Q.1, Q.2 headers, "Attempt any..." text, page numbers
- Handle OCR trash: _b)→b), ~g)→g), leading/trailing junk"""

        if subject_context:
            subj = subject_context.get('subject', '')
            system_prompt += f"\n\nSubject context: {subj}"

        # Optimized chunking: use only first 10k chars for speed, regex can handle rest
        MAX_CHAR = 10_000
        text_to_send = raw_text[:MAX_CHAR]

        user_prompt = f"""Parse this MSBTE OCR text to JSON array:

{text_to_send}

Return ONLY JSON array, no markdown or explanation."""

        def _call_groq(prompt_text, temperature=0.2):
            """Call Groq API (optimized temperature for accuracy + speed)."""
            models = [
                os.getenv('GROQ_PARSER_MODEL', 'llama-3.1-8b-instant'),
                'llama-3.3-70b-versatile',
            ]
            last_err = None
            for model_name in models:
                try:
                    cc = client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user",   "content": prompt_text},
                        ],
                        model=model_name,
                        temperature=temperature,
                        max_tokens=4096,
                    )
                    resp = cc.choices[0].message.content.strip()
                    resp = re.sub(r'^```(?:json)?\s*', '', resp, flags=re.MULTILINE)
                    resp = re.sub(r'```\s*$', '', resp, flags=re.MULTILINE)
                    resp = re.sub(r',\s*([\]}])', r'\1', resp.strip())
                    return resp
                except Exception as e:
                    last_err = e
                    continue
            raise last_err if last_err else RuntimeError('Groq call failed')

        def _parse_response(resp_text):
            """Parse JSON response."""
            try:
                return json.loads(resp_text)
            except json.JSONDecodeError as e:
                print(f"AI parse error: {e}")
                # Attempt lightweight recovery for truncated arrays.
                repaired = resp_text.strip()
                if repaired.startswith('['):
                    open_curly = repaired.count('{')
                    close_curly = repaired.count('}')
                    if close_curly < open_curly:
                        repaired += '}' * (open_curly - close_curly)
                    if not repaired.endswith(']'):
                        repaired += ']'
                    repaired = re.sub(r',\s*\]', ']', repaired)
                    try:
                        return json.loads(repaired)
                    except Exception:
                        pass
                # Retry once at temperature 0 for deterministic output
                try:
                    resp2 = _call_groq(user_prompt, temperature=0.0)
                    return json.loads(resp2)
                except:
                    raise

        print(f"AI: Parsing OCR text ({len(text_to_send)} chars)…")
        response_text = _call_groq(user_prompt)

        raw_questions = _parse_response(response_text)
        if not isinstance(raw_questions, list):
            raise ValueError("AI did not return a list")

        # ── Build page→images map ──────────────────────────────────────────
        page_images     = {}
        assigned_images = set()
        for img in extracted_images:
            pg = img.get('page', 1)
            page_images.setdefault(pg, []).append(img)

        def _assign_image(has_diagram):
            for pg_imgs in page_images.values():
                for img in pg_imgs:
                    img_id = f"{img['page']}_{img['filename']}"
                    if img_id not in assigned_images:
                        assigned_images.add(img_id)
                        return [{'filename': img['filename'],
                                 'url': img.get('cloudinary_url', img.get('url', '')),
                                 'width': img['width'], 'height': img['height']}]
            return []

        # ── Validate and normalize questions ────────────────────────────────
        questions = []
        for idx, q in enumerate(raw_questions):
            text = str(q.get('question_text', '')).strip()
            if not text or len(text) < 8:
                continue

            has_diagram = bool(q.get('has_diagram', False))
            obj = {
                'question_number' : str(idx + 1),
                'question_text'   : text,
                'marks'           : int(q.get('marks', 4)),
                'course_outcome'  : str(q.get('course_outcome', '')),
                'bloom_level'     : str(q.get('bloom_level', 'K2')),
                'has_math'        : bool(q.get('has_math', False)),
                'has_diagram'     : has_diagram,
                'images'          : _assign_image(has_diagram) if has_diagram else [],
                'sub_questions'   : q.get('sub_questions', []),
                'sub_label'       : q.get('sub_label', ''),
            }
            validated = validate_and_clean_question(obj)
            if validated:
                questions.append(validated)

        # Re-number sequentially
        for i, q in enumerate(questions):
            q['question_number'] = str(i + 1)

        print(f"AI: Successfully extracted {len(questions)} questions")
        return {
            'total_papers': 1,
            'exam_info'   : {},
            'papers'      : [{'paper_number': 1,
                               'paper_name'  : 'Question Paper',
                               'questions'   : questions}],
            'total_images_detected': len(extracted_images),
            'images_folder'        : page_images,
            'parsed_by'            : 'ai',
        }

    except json.JSONDecodeError as e:
        print(f"AI parse: JSON decode error – {e}")
        print(f"AI parse: raw response was: {response_text[:300] if 'response_text' in locals() else 'N/A'}")
        return None
    except Exception as e:
        print(f"AI parse failed ({type(e).__name__}): {e}")
        return None


# ---------------------------------------------------------------------------
# MSBTE known subject code map (code is the 5-digit MSBTE course number)
# Used as authoritative fallback when OCR garbles the printed code.
# ---------------------------------------------------------------------------
_MSBTE_SUBJECT_CODES: dict = {
    'communication skills':                     '22101',
    'communication skills (cms)':               '22101',
    'engineering mathematics':                  '22103',
    'applied mathematics':                      '22201',
    'basic mathematics':                        '22103',
    'fundamentals of ict':                      '22104',
    'programming in c':                         '22316',
    'engineering drawing':                      '22102',
    'basic electrical engineering':             '22215',
    'electrical machines':                      '22314',
    'digital electronics':                      '22318',
    'data structures':                          '22317',
    'database management':                      '22412',
    'database management systems':              '22412',
    'operating systems':                        '22516',
    'software engineering':                     '22617',
    'computer networks':                        '22415',
    'web development':                          '22519',
    'python programming':                       '22616',
    'machine learning':                         '22618',
    'java programming':                         '22412',
    'microprocessors':                          '22429',
    'fluid mechanics':                          '22402',
    'strength of materials':                    '22306',
    'engineering thermodynamics':               '22302',
}


def _is_known_subject_code(code: str) -> bool:
    c = str(code or '').strip()
    return bool(re.fullmatch(r'\d{5}', c) and c in set(_MSBTE_SUBJECT_CODES.values()))


def _regex_extract_header(text: str) -> dict:
    """
    Regex-based MSBTE paper header extractor.
    Scans the first 100 lines (header area) for known field patterns.
    Handles partially corrupted / word-split OCR output.
    """
    info: dict = {}
    lines = text.split('\n')

    # ── Pre-process header: collapse word splits caused by OCR line breaks ────
    # OCR frequently breaks a single word across lines, e.g.:
    #   "Cour\n   se: Com\nmunication Skills"
    # We join lines where a line ends with letters and the next begins with
    # letters (after stripping whitespace), so the word is reassembled.
    joined_lines = []
    raw_header_lines = lines[:100]
    i = 0
    while i < len(raw_header_lines):
        line = raw_header_lines[i]
        # Merge with next line when current line ends mid-word (no punctuation/space at end)
        while (i + 1 < len(raw_header_lines)
               and re.search(r'[A-Za-z]$', line.rstrip())
               and re.match(r'\s*[a-z]', raw_header_lines[i + 1])):
            i += 1
            line = line.rstrip() + raw_header_lines[i].lstrip()
        joined_lines.append(line)
        i += 1

    header = '\n'.join(joined_lines)
    # Also try the raw (unjoined) header for patterns that don't need word joining
    header_raw = '\n'.join(raw_header_lines)

    # ── Subject name ──────────────────────────────────────────────────────────
    # Pattern 1: explicit course label. Stop before a following course-code
    # label so OCR text such as "COURSE: Software Engineering COURSE CODE:"
    # does not become part of the course name.
    m = re.search(
        r'Course\s*[:\-]\s*([A-Za-z][A-Za-z0-9 &()\-/]*?)(?=\s+Course\s+Code\b|\s+Code\b|[\r\n]|$)',
        header, re.IGNORECASE
    )
    if m:
        name = m.group(1).strip().rstrip('.,')
        if len(name) >= 4:
            info['subject_name'] = name

    # Pattern 2: explicit label "Subject:", "Sub:" etc.
    if not info.get('subject_name'):
        m = re.search(
            r'(?:Subject|Sub|Programme|Program|Prog)\s*[:\-]\s*([A-Za-z][A-Za-z0-9 &()\-/]+)',
            header, re.IGNORECASE
        )
    if m and not info.get('subject_name'):
        name = m.group(1).strip().rstrip('.,')
        name = re.sub(r'\s{2,}.*$', '', name).strip()   # strip trailing OCR junk
        if len(name) >= 4:
            info['subject_name'] = name

    # Pattern 3: fallback — check known subject names directly in the header text
    if not info.get('subject_name'):
        header_lower = header.lower()
        for known_name in sorted(_MSBTE_SUBJECT_CODES.keys(), key=len, reverse=True):
            if known_name in header_lower:
                # Title-case the match text from the header
                idx = header_lower.index(known_name)
                info['subject_name'] = header[idx: idx + len(known_name)].strip()
                break

    # ── Course code / subject code ────────────────────────────────────────────
    # Try 1: explicit "Code: 22101" label
    m = re.search(r'\b(?:Course\s+)?Code\b[^a-zA-Z0-9]{0,20}(\d{4,6})', header, re.IGNORECASE)
    if m:
        info['course_code'] = m.group(1)
        info['subject_code'] = m.group(1)

    # Try 2: standalone 5-digit number that looks like an MSBTE code (starts with 2)
    # Exclude current years (2020-2029) to avoid false positives
    if not info.get('subject_code'):
        nums = re.findall(r'\b(2\d{4})\b', header_raw)
        valid = [n for n in nums if not re.match(r'^202\d$', n)]  # exclude 202x years
        if valid:
            info['subject_code'] = valid[0]

    # Try 3: scan the ENTIRE first page text for a known 5-digit code
    if not info.get('subject_code'):
        first_page = '\n'.join(lines[:150])
        nums = re.findall(r'\b(2\d{4})\b', first_page)
        valid = [n for n in nums if not re.match(r'^202\d$', n)
                 and n in _MSBTE_SUBJECT_CODES.values()]
        if valid:
            info['subject_code'] = valid[0]

    # Try 4 (most reliable): map known subject name → code
    if not info.get('subject_code') and info.get('subject_name'):
        key = info['subject_name'].lower().strip()
        code = _MSBTE_SUBJECT_CODES.get(key)
        if not code:
            for k, v in _MSBTE_SUBJECT_CODES.items():
                if k in key or key in k:
                    code = v
                    break
        if code:
            info['subject_code'] = code

    if not info.get('course_code'):
        info['course_code'] = info.get('subject_code', '')

    if info.get('subject_name'):
        info['course_name'] = info['subject_name']

    # ── Exam type ─────────────────────────────────────────────────────────────
    if re.search(r'summer', header, re.IGNORECASE):
        info['exam_type'] = 'Summer Examination'
    elif re.search(r'winter', header, re.IGNORECASE):
        info['exam_type'] = 'Winter Examination'
    elif re.search(r'mid.?semester|mid.?term', header, re.IGNORECASE):
        info['exam_type'] = 'Mid Semester'
    elif re.search(r'unit.?test', header, re.IGNORECASE):
        info['exam_type'] = 'Unit Test'
    elif re.search(r'end.?semester', header, re.IGNORECASE):
        info['exam_type'] = 'End Semester'

    # ── Exam year ─────────────────────────────────────────────────────────────
    m = re.search(r'\b(20\d{2})\b', header)
    if m:
        info['exam_year'] = m.group(1)

    # ── Total marks ───────────────────────────────────────────────────────────
    m = re.search(r'(?:Total\s+)?Marks?\s*[:\-]?\s*(\d{2,3})', header, re.IGNORECASE)
    if m:
        info['total_marks'] = m.group(1)

    # ── Duration ──────────────────────────────────────────────────────────────
    m = re.search(r'Duration\s*[:\-]?\s*([\d.]+\s*(?:Hr|Hours?|Hrs))', header, re.IGNORECASE)
    if m:
        info['duration'] = m.group(1).strip()

    return info


def ai_extract_exam_info(header_text: str, subject_context: dict = None,
                         groq_api_key: str = None) -> dict:
    """
    Use Groq LLM to extract paper header metadata from the first portion of OCR text.
    Receives an optional subject_context dict (subject, branch, semester) to help
    the AI recover garbled OCR codes.
    Returns a dict with: course_name, course_code, subject_name, subject_code, exam_type, exam_year,
    total_marks, duration, branch.  Missing fields are empty strings.
    """
    api_key = groq_api_key or os.getenv(
        'GROQ_API_KEY',
        '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'
    )
    if not api_key:
        return {}
    try:
        from groq import Groq as _Groq
        client = _Groq(api_key=api_key)

        ctx_line = ''
        if subject_context:
            ctx_line = (
                f"\nKnown context (from user selection): "
                f"subject='{subject_context.get('subject','')}', "
                f"branch='{subject_context.get('branch','')}', "
                f"semester='{subject_context.get('semester','')}'. "
                f"Use this to help reconstruct garbled OCR fields.\n"
            )

        # Also embed the known-code map hint so AI can recover garbled codes
        code_hints = ', '.join(f"'{k}' → {v}"
                               for k, v in list(_MSBTE_SUBJECT_CODES.items())[:15])

        system = (
            "You are a precise OCR metadata extractor for MSBTE (Maharashtra State Board of "
            "Technical Education) question papers. Extract only paper-header information and "
            "return a single JSON object (no markdown, no explanation). "
            "Use empty string '' for any field not found. "
            "IMPORTANT: MSBTE subject codes are 5-digit numbers (e.g. 22101, 22316). "
            "If the OCR has garbled the code (e.g. '4  a' instead of '22101'), "
            "reconstruct it using the subject name and the known-code hints provided."
        )
        user = f"""Extract the exam header metadata from this OCR text.{ctx_line}

Known MSBTE subject codes (use for garbled-code recovery): {code_hints}

Return ONLY this JSON object:
{{
  "subject_name": "<full subject name>",
  "subject_code": "<5-digit MSBTE code, e.g. 22101>",
    "course_name": "<full course name>",
    "course_code": "<printed course code>",
  "exam_type": "<Summer Examination | Winter Examination | Mid Semester | Unit Test>",
  "exam_year": "<4-digit year>",
  "total_marks": "<numeric total marks>",
  "duration": "<e.g. 3 Hours>",
  "branch": "<branch/programme if visible>"
}}

OCR TEXT (first portion of paper):
---
{header_text[:3000]}
---
Return ONLY the JSON object."""
        models = [
            os.getenv('GROQ_HEADER_MODEL', 'llama-3.1-8b-instant'),
            'llama-3.3-70b-versatile',
        ]
        cc = None
        last_err = None
        for model_name in models:
            try:
                cc = client.chat.completions.create(
                    messages=[{"role": "system", "content": system},
                              {"role": "user",   "content": user}],
                    model=model_name,
                    temperature=0.0,
                    max_tokens=300,
                )
                break
            except Exception as e:
                last_err = e
                continue
        if cc is None:
            raise last_err if last_err else RuntimeError('Groq header parse failed')
        raw = cc.choices[0].message.content.strip()
        raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE)
        raw = re.sub(r'```\s*$', '',          raw, flags=re.MULTILINE)
        raw = re.sub(r',\s*([\]}])', r'\1',   raw.strip())
        info = json.loads(raw)

        # Accept either naming convention from the model and expose both.
        if not info.get('subject_name'):
            info['subject_name'] = info.get('course_name', '')
        if not info.get('subject_code'):
            info['subject_code'] = info.get('course_code', '')
        if not info.get('course_name'):
            info['course_name'] = info.get('subject_name', '')
        if not info.get('course_code'):
            info['course_code'] = info.get('subject_code', '')

        # Validate: if code looks garbled (not all digits or wrong length), try map
        code = str(info.get('subject_code', '')).strip()
        if code and (not _is_known_subject_code(code)):
            name_key = str(info.get('subject_name', '')).lower().strip()
            code = _MSBTE_SUBJECT_CODES.get(name_key, '')
            if not code:
                for k, v in _MSBTE_SUBJECT_CODES.items():
                    if k in name_key or name_key in k:
                        code = v
                        break
            info['subject_code'] = code

        print(f"AI exam info: subject='{info.get('subject_name','')}' "
              f"code='{info.get('subject_code','')}' year='{info.get('exam_year','')}'")
        return info
    except Exception as e:
        print(f"ai_extract_exam_info warning (non-fatal): {e}")
        return {}


def extract_questions_from_pdf(pdf_path, extract_images=False, subject_context=None, fast_mode=True,
                               extracted_text=None, extraction_source='OCR Fallback'):
    """
    Main function to extract questions from a PDF file with optimized performance.
    
    Pipeline:
      1. OCR via Tesseract (150 DPI, fast single-pass)  → raw text
      2. AI parsing (Groq LLaMA)                        → structured questions
      3. Regex parser                                   → fallback if AI fails
    
    Args:
        pdf_path: Path to PDF file
        extract_images: Whether to extract images (default False for speed)
        subject_context: Subject/branch/semester info
        fast_mode: Use fast extraction settings (default True)
    
    Returns: dict with extracted questions and metadata
    """
    try:
        # Validate file exists
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Validate Tesseract only when the external provider did not supply text.
        if extracted_text is None and not tesseract_path:
            raise Exception(
                "Tesseract OCR is not installed or not found in PATH. "
                "Please install Tesseract OCR from https://github.com/tesseract-ocr/tesseract"
            )

        print(f"Starting PDF extraction (fast_mode={fast_mode}) from: {pdf_path}")
        print(f"Tesseract path: {tesseract_path}")

        # ── Step 1: obtain text ────────────────────────────────────────────────
        # External text is already extracted; the existing OCR path remains the fallback.
        if extracted_text is not None:
            text_content = extracted_text
            extracted_images = []
        else:
            dpi = 150 if fast_mode else 200
            text_content, extracted_images = extract_text_from_pdf(
                pdf_path, dpi=dpi, extract_images=extract_images, fast_mode=fast_mode
            )

        if not text_content or len(text_content.strip()) == 0:
            print("WARNING: No text extracted from PDF")
            return {
                'total_papers': 0,
                'exam_info': {},
                'papers': [],
                'error': 'No text could be extracted from the PDF',
                'total_images_detected': len(extracted_images)
            }

        # Clean OCR noise and expand merged OCR lines before AI/regex parsing.
        text_content = _preprocess_ocr_text(text_content)
        text_content = _split_compound_question_lines(text_content)

        # Save raw OCR text for debugging
        raw_debug_path = pdf_path.replace('.pdf', '_raw_ocr.txt')
        try:
            with open(raw_debug_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
            print(f"Raw OCR text saved to: {raw_debug_path}")
        except Exception:
            pass

        # ── Step 1b: Extract paper header metadata (subject, code, year…) ──────
        # Layer 1 – fast regex (no API call, handles structural patterns)
        regex_info = _regex_extract_header(text_content)
        # Layer 2 – AI (handles garbled text, can reconstruct codes)
        ai_info = ai_extract_exam_info(text_content,
                                       subject_context=subject_context)
        # Merge: start from AI result, then apply regex values where they are
        # more reliable (valid 5-digit codes, clean subject names, typed year).
        detected_exam_info: dict = {**ai_info}
        for key, val in regex_info.items():
            if not val:
                continue
            existing = detected_exam_info.get(key, '')
            # Always prefer a valid 5-digit subject code from regex
            if key == 'subject_code':
                if _is_known_subject_code(str(val)):
                    detected_exam_info[key] = val
            # Prefer regex subject_name when AI returned empty or "Unknown"
            elif key == 'subject_name':
                if not existing or existing.lower() in ('unknown', ''):
                    detected_exam_info[key] = val
            # For other fields take regex value when AI returned empty
            elif not existing:
                detected_exam_info[key] = val

        # Final safety: if subject_code is still garbled/empty, resolve from name map
        code = str(detected_exam_info.get('subject_code', '')).strip()
        if not _is_known_subject_code(code):
            # Try from detected subject_name first, then from subject_context
            name_key = str(
                detected_exam_info.get('subject_name') or
                detected_exam_info.get('subject') or
                (subject_context or {}).get('subject', '')
            ).lower().strip()
            resolved = _MSBTE_SUBJECT_CODES.get(name_key, '')
            if not resolved:
                for k, v in _MSBTE_SUBJECT_CODES.items():
                    if k in name_key or name_key in k:
                        resolved = v
                        break
            # Last resort: scan the entire OCR text for known MSBTE subject names.
            # Normalise first so OCR word-splits ("com\nmunication") don't block matching.
            if not resolved:
                text_normalised = re.sub(r'\s+', ' ', text_content).lower()
                for k, v in sorted(_MSBTE_SUBJECT_CODES.items(), key=lambda x: len(x[0]), reverse=True):
                    if k in text_normalised:
                        resolved = v
                        if not detected_exam_info.get('subject_name'):
                            detected_exam_info['subject_name'] = k.title()
                        break
            if resolved:
                detected_exam_info['subject_code'] = resolved

        if not detected_exam_info.get('subject_name') and subject_context:
            ctx_subject = str(subject_context.get('subject', '')).strip()
            if ctx_subject:
                detected_exam_info['subject_name'] = ctx_subject

        # Keep course terminology available while retaining existing subject keys.
        detected_exam_info['course_name'] = (
            detected_exam_info.get('course_name') or
            detected_exam_info.get('subject_name', '')
        )
        detected_exam_info['course_code'] = (
            detected_exam_info.get('course_code') or
            detected_exam_info.get('subject_code', '')
        )

        print(f"Final exam info → subject='{detected_exam_info.get('subject_name','')}' "
              f"code='{detected_exam_info.get('subject_code','')}' "
              f"year='{detected_exam_info.get('exam_year','')}'")

        # ── Step 2: Try AI parsing ─────────────────────────────────────────────
        result = None
        ai_result = ai_parse_questions(text_content, extracted_images, subject_context=subject_context)
        if ai_result:
            q_count = sum(len(p.get('questions', []))
                          for p in ai_result.get('papers', []))
            if q_count >= 12:         # accept AI only when count is plausible
                result = ai_result
                print(f"Using AI-parsed result: {q_count} questions")
            else:
                print(f"AI returned only {q_count} questions – falling back to regex")

        # ── Step 3: Regex parser fallback ─────────────────────────────────────
        if result is None:
            print("Using regex parser…")
            result = parse_papers_and_extract_questions(text_content, extracted_images)

        # Merge detected header info into result's exam_info
        existing_exam_info = result.get('exam_info') or {}
        existing_exam_info.update({k: v for k, v in detected_exam_info.items() if v})
        result['exam_info'] = existing_exam_info

        # Final normalization pass: split any merged AI/regex question blocks.
        result = _normalize_extracted_result(result, extracted_images)

        # If the extractor returned far fewer questions than expected, try a
        # more thorough OCR pass (higher DPI, two-pass OCR) and re-parse. This
        # helps when Tesseract missed many short lines due to low DPI.
        EXPECTED_MIN_QUESTIONS = 26
        q_count = sum(len(p.get('questions', [])) for p in result.get('papers', []))
        if q_count < EXPECTED_MIN_QUESTIONS and (fast_mode or extracted_text is None):
            try:
                print(f"Low question count ({q_count}) — retrying OCR at higher quality...")
                text_content2, extracted_images2 = extract_text_from_pdf(
                    pdf_path, dpi=200, extract_images=extract_images, fast_mode=False
                )

                # Re-run AI + regex parsing on higher-quality text
                text_content2 = _preprocess_ocr_text(text_content2)
                text_content2 = _split_compound_question_lines(text_content2)
                ai_result2 = ai_parse_questions(text_content2, extracted_images2, subject_context=subject_context)
                candidate = None
                if ai_result2:
                    qc2 = sum(len(p.get('questions', [])) for p in ai_result2.get('papers', []))
                    if qc2 > q_count:
                        candidate = ai_result2

                if candidate is None:
                    # Fallback to regex parse of higher-quality OCR
                    candidate = parse_papers_and_extract_questions(text_content2, extracted_images2)

                # Normalize and choose the best (more questions)
                candidate = _normalize_extracted_result(candidate, extracted_images2)
                qc_final = sum(len(p.get('questions', [])) for p in candidate.get('papers', []))
                if qc_final > q_count:
                    print(f"Retry improved question count: {q_count} -> {qc_final}")
                    candidate_exam_info = result.get('exam_info', {})
                    result = candidate
                    # Preserve exam metadata resolved earlier.
                    result['exam_info'] = candidate_exam_info
                else:
                    print(f"Retry did not improve question count: {q_count} -> {qc_final}")
            except Exception as e:
                print(f"Retry OCR pass failed: {e}")

        # Last-resort fallback for noisy scans: extract questions directly from
        # CO/label/verb lines when structured parsing still undercounts.
        q_count = sum(len(p.get('questions', [])) for p in result.get('papers', []))
        if q_count < EXPECTED_MIN_QUESTIONS:
            try:
                line_questions = _extract_questions_from_noisy_lines(text_content)
                if line_questions and result.get('papers'):
                    base_questions = result['papers'][0].get('questions', [])

                    def _norm_key(t: str) -> str:
                        return re.sub(r'\W+', ' ', str(t).lower()).strip()

                    existing = {_norm_key(q.get('question_text', '')) for q in base_questions}
                    added = 0
                    for cand in line_questions:
                        key = _norm_key(cand.get('question_text', ''))
                        if not key or key in existing:
                            continue
                        base_questions.append(cand)
                        existing.add(key)
                        added += 1

                    if added > 0:
                        for i, q in enumerate(base_questions, start=1):
                            q['question_number'] = str(i)
                        print(f"Noisy-line merge added {added} questions: {q_count} -> {len(base_questions)}")
            except Exception as e:
                print(f"Noisy-line fallback failed: {e}")

        # Add extraction metadata
        try:
            tess_ver = str(pytesseract.get_tesseract_version())
        except Exception:
            tess_ver = str(tesseract_path)
        result['extraction_metadata'] = {
            'total_characters' : len(text_content),
            'total_lines'      : len(text_content.split('\n')),
            'tesseract_version': tess_ver,
            'images_extracted' : len(extracted_images),
            'parser'           : result.get('parsed_by', 'regex'),
            'source'           : extraction_source,
        }
        result['extraction_source'] = extraction_source

        return result

    except FileNotFoundError as e:
        print(f"FILE ERROR: {str(e)}")
        return {'total_papers': 0, 'exam_info': {}, 'papers': [], 'error': str(e)}
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'total_papers': 0,
            'exam_info': {},
            'papers': [],
            'error': f'Extraction failed: {str(e)}'
        }

