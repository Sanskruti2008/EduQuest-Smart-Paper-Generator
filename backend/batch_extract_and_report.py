"""
Batch run extractor for all PDFs in backend/uploads and save normalized JSON outputs.
Saves per-file JSON into backend/extracted_json/<basename>_aggressive.json
Also writes a summary report to backend/extracted_json/batch_summary.json
"""
import os
import json
from pathlib import Path
from ocr_extractor import extract_questions_from_pdf, _normalize_extracted_result

BASE = Path(__file__).resolve().parent
UPLOADS = BASE / 'uploads'
OUTDIR = BASE / 'extracted_json'
OUTDIR.mkdir(parents=True, exist_ok=True)

summary = []

files = [p for p in UPLOADS.iterdir() if p.suffix.lower() == '.pdf']
if not files:
    print('No PDF files found in uploads/')

for pdf in files:
    print(f'Processing: {pdf.name}')
    try:
        # Fast pass first
        res = extract_questions_from_pdf(str(pdf), extract_images=False, subject_context=None, fast_mode=True)
        # Normalize result to apply aggressive fallback/merging
        norm = _normalize_extracted_result(res, extracted_images=[])
        qcount = sum(len(p.get('questions', [])) for p in norm.get('papers', []))
        needs = sum(1 for p in norm.get('papers', []) for q in p.get('questions', []) if q.get('status') == 'needs_review')
        # If still low, retry with higher quality
        if qcount < 18:
            print(f'Low question count ({qcount}) — retrying with higher OCR quality')
            res2 = extract_questions_from_pdf(str(pdf), extract_images=False, subject_context=None, fast_mode=False)
            norm2 = _normalize_extracted_result(res2, extracted_images=[])
            qcount2 = sum(len(p.get('questions', [])) for p in norm2.get('papers', []))
            if qcount2 > qcount:
                norm = norm2
                qcount = qcount2
                needs = sum(1 for p in norm.get('papers', []) for q in p.get('questions', []) if q.get('status') == 'needs_review')

        out_name = OUTDIR / f"{pdf.stem}_aggressive.json"
        with open(out_name, 'w', encoding='utf-8') as f:
            json.dump(norm, f, ensure_ascii=False, indent=2)

        summary.append({
            'file': pdf.name,
            'questions': qcount,
            'needs_review': needs,
            'out': str(out_name.name)
        })
        print(f' -> {qcount} questions ({needs} needs_review) saved to {out_name.name}')
    except Exception as e:
        print(f'Error processing {pdf.name}: {e}')
        summary.append({'file': pdf.name, 'error': str(e)})

with open(OUTDIR / 'batch_summary.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print('Batch complete. Summary written to extracted_json/batch_summary.json')
