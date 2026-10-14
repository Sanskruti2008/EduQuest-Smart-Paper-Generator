from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import time, os, json
from services.ocr_service import extract_and_clean
from services.db_service import save_paper
import database as db
from utils.auth import require_roles
from utils.file_utils import allowed_file
from services.similarity_ingestion_service import process_saved_questions_safely

upload_bp = Blueprint('upload_bp', __name__)


def _prepare_review_questions(extracted_data):
    """Expose OCR candidates in review responses without changing clean-bank data."""
    if not isinstance(extracted_data, dict):
        return extracted_data

    candidates = extracted_data.get('review_candidates') or []
    papers = extracted_data.get('papers') or []
    if not papers:
        papers = [{'paper_number': 1, 'questions': []}]
        extracted_data['papers'] = papers
    if not candidates:
        return extracted_data

    existing = {
        ' '.join(str(question.get('question_text', '')).casefold().split())
        for paper in papers
        for question in (paper.get('questions') or [])
    }
    review_questions = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        key = ' '.join(str(candidate.get('question_text', '')).casefold().split())
        if key and key not in existing:
            review_questions.append(dict(candidate))
            existing.add(key)

    if review_questions:
        papers[0] = {
            **papers[0],
            'questions': [*(papers[0].get('questions') or []), *review_questions],
        }
        extracted_data['papers'] = papers
    return extracted_data


@upload_bp.route('/api/upload-question-paper', methods=['POST'])
@require_roles("admin", "faculty")
def upload_question_paper():
    try:
        review_mode = str(request.form.get('review', 'false')).lower() == 'true'
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only PDF files are allowed'}), 400

        branch = request.form.get('branch', 'Unknown')
        semester = request.form.get('semester', 'Unknown')
        subject = request.form.get('subject', 'Unknown')

        filename = secure_filename(file.filename)
        timestamp = int(time.time())
        unique_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)

        extracted_data, json_filename = extract_and_clean(
            filepath,
            subject_context={'subject': subject, 'branch': branch, 'semester': semester},
            extract_images=False,
            # Review uploads prioritize OCR accuracy over the fast 150-DPI pass.
            fast_mode=False,
            extracted_json_folder=current_app.config.get('EXTRACTED_JSON_FOLDER')
        )

        questions_count = 0
        papers_data = []
        if extracted_data and isinstance(extracted_data, dict):
            papers_data = extracted_data.get('papers', [])
            questions_count = sum(len(paper.get('questions', [])) for paper in papers_data)
            exam_info = extracted_data.setdefault('exam_info', {})
            exam_info['branch'] = str(exam_info.get('branch') or branch or 'Unknown').strip() or 'Unknown'
            exam_info['semester'] = str(exam_info.get('semester') or semester or 'Unknown').strip() or 'Unknown'
            exam_info['subject'] = str(
                exam_info.get('subject') or exam_info.get('subject_name') or subject or 'Unknown'
            ).strip() or 'Unknown'
            extracted_data['json_file'] = json_filename
            if review_mode:
                extracted_data = _prepare_review_questions(extracted_data)

        # Auto-save unless review
        paper_id = None
        db_error = None
        similarity = None
        if questions_count > 0 and not review_mode:
            try:
                exam_info = extracted_data.get('exam_info', {}) if extracted_data else {}
                exam_info['original_filename'] = filename
                extracted_subject_name = str(exam_info.get('subject_name') or exam_info.get('subject') or '').strip()
                extracted_subject_code = str(exam_info.get('subject_code') or '').strip()
                effective_subject = extracted_subject_name or subject
                effective_branch = str(exam_info.get('branch') or branch or 'Unknown').strip() or 'Unknown'
                effective_semester = str(exam_info.get('semester') or semester or 'Unknown').strip() or 'Unknown'

                exam_info['subject'] = effective_subject
                exam_info['subject_name'] = effective_subject
                if extracted_subject_code:
                    exam_info['subject_code'] = extracted_subject_code
                if effective_branch:
                    exam_info['branch'] = effective_branch
                if effective_semester:
                    exam_info['semester'] = effective_semester

                paper_id = save_paper(
                    filename=unique_filename,
                    branch=effective_branch,
                    semester=effective_semester,
                    subject=effective_subject,
                    papers_data=papers_data,
                    exam_info=exam_info
                )
                similarity = process_saved_questions_safely(
                    papers_data=papers_data,
                    subject=effective_subject,
                    exam_info=exam_info,
                )
            except Exception as dbe:
                db_error = str(dbe)

        extraction_source = extracted_data.get('extraction_source', 'OCR Fallback') if extracted_data else 'OCR Fallback'
        minimum_questions_met = questions_count >= 26
        success_message = (
            f'Question paper uploaded and processed successfully. {questions_count} questions extracted. '
            f'Extraction source: {extraction_source}.'
        )
        if not minimum_questions_met:
            success_message = (
                f'Question paper processed with {questions_count} valid questions. '
                'The paper has fewer than the required 26 questions and needs review.'
            )
        if questions_count == 0:
            success_message = 'PDF uploaded but no questions extracted. Try a different PDF or check OCR settings.'
        if db_error:
            success_message += f' (DB save warning: {db_error})'

        return jsonify({
            'success': True,
            'message': success_message,
            'filename': filename,
            'json_file': json_filename,
            'extracted_data': extracted_data,
            'questions_extracted': questions_count > 0,
            'questions_count': questions_count,
            'minimum_questions_met': minimum_questions_met,
            'extraction_source': extraction_source,
            'paper_id': paper_id,
            'saved_to_db': paper_id is not None,
            'similarity': similarity,
            'detected_subject': extracted_data.get('exam_info', {}).get('subject_name', '') if extracted_data else '',
            'detected_subject_code': extracted_data.get('exam_info', {}).get('subject_code', '') if extracted_data else '',
            'detected_course_name': extracted_data.get('exam_info', {}).get('course_name', '') if extracted_data else '',
            'detected_course_code': extracted_data.get('exam_info', {}).get('course_code', '') if extracted_data else '',
        }), 200

    except Exception as e:
        print(f"Error in upload_question_paper (blueprint): {e}")
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': str(e)}), 500
