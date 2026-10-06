import os, json, time
from typing import Tuple, Dict, Any
from ocr_extractor import extract_questions_from_pdf
from reclean_extracted_json import _clean_payload
from services.grammar_service import clean_and_maybe_correct


def extract_and_clean(pdf_path: str, subject_context: dict = None, extract_images: bool = False, fast_mode: bool = True, upload_folder: str = None, extracted_json_folder: str = None) -> Tuple[Dict[str, Any], str]:
    """
    Run native OCR extraction, then run the existing parser and cleanup.
    Returns (extracted_data, json_filename).
    """
    extraction_source = 'OCR'
    extracted = extract_questions_from_pdf(
        pdf_path,
        extract_images=extract_images,
        subject_context=subject_context,
        fast_mode=fast_mode,
        extracted_text=None,
        extraction_source=extraction_source,
    )

    json_filename = None
    if extracted and isinstance(extracted, dict):
        cleaned_data, clean_stats = _clean_payload(extracted)
        extracted = cleaned_data
        extracted['extraction_source'] = extraction_source

        try:
            papers = extracted.get('papers') or []
            if papers:
                extracted['papers'] = clean_and_maybe_correct(papers)
                # Grammar correction can change the text; run the validator again
                # so only the final standardized text receives its status.
                extracted, _ = _clean_payload(extracted)
                extracted['extraction_source'] = extraction_source
        except Exception as e:
            print(f"[OCR] Per-question grammar correction failed: {e}")

        # write JSON file if folder provided
        if extracted_json_folder:
            basename = os.path.basename(pdf_path)
            timestamp = int(time.time())
            json_filename = f"{timestamp}_{basename.rsplit('.',1)[0]}.json"
            json_path = os.path.join(extracted_json_folder, json_filename)
            with open(json_path, 'w', encoding='utf-8') as jf:
                json.dump(extracted, jf, indent=2, ensure_ascii=False)

    return extracted, json_filename
