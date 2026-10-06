from flask import Blueprint, current_app, request, jsonify
import json
import os
import tempfile
import time
import database as db
from utils.auth import require_admin
from services.grammar_service import clean_and_maybe_correct
from services.db_service import save_paper
from services.similarity_ingestion_service import process_saved_questions_safely

save_bp = Blueprint('save_bp', __name__)


def _sync_extracted_json(json_filename, exam_info, papers_data):
    """Persist the reviewed payload beside the source extracted JSON."""
    folder = current_app.config.get('EXTRACTED_JSON_FOLDER')
    if not folder:
        raise RuntimeError('Extracted JSON folder is not configured')

    filename = os.path.basename(str(json_filename or '')).strip()
    if not filename.lower().endswith('.json'):
        raise ValueError('Invalid extracted JSON filename')

    path = os.path.join(folder, filename)
    payload = {}
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as source:
            loaded = json.load(source)
            if isinstance(loaded, dict):
                payload = loaded

    payload['total_papers'] = len(papers_data)
    payload['exam_info'] = dict(exam_info)
    payload['papers'] = papers_data

    os.makedirs(folder, exist_ok=True)
    fd, temporary_path = tempfile.mkstemp(prefix='.reviewed-', suffix='.json', dir=folder)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as destination:
            json.dump(payload, destination, ensure_ascii=False, indent=2)
            destination.write('\n')
        os.replace(temporary_path, path)
    except Exception:
        if os.path.exists(temporary_path):
            os.unlink(temporary_path)
        raise


@save_bp.route('/api/save-extracted-paper', methods=['POST'])
@require_admin
def save_extracted_paper():
    try:
        body = request.get_json(force=True)
        if not body:
            return jsonify({'error': 'Empty request body'}), 400

        json_file = body.get('json_file') or body.get('filename')
        papers_data = body.get('papers_data') or body.get('papers') or []
        exam_info = body.get('exam_info', {}) or {}

        if not papers_data:
            return jsonify({'error': 'No questions provided to save'}), 400

        extracted_subject_name = str(exam_info.get('subject_name') or exam_info.get('subject') or body.get('subject') or 'Unknown').strip() or 'Unknown'
        extracted_subject_code = str(exam_info.get('subject_code') or body.get('subject_code') or '').strip()
        effective_branch = str(exam_info.get('branch') or body.get('branch') or 'Unknown').strip() or 'Unknown'
        effective_semester = str(exam_info.get('semester') or body.get('semester') or 'Unknown').strip() or 'Unknown'

        branch = effective_branch
        semester = effective_semester
        subject = extracted_subject_name
        exam_info['subject'] = extracted_subject_name
        exam_info['subject_name'] = extracted_subject_name
        exam_info['subject_code'] = extracted_subject_code if extracted_subject_code else exam_info.get('subject_code', '')
        exam_info['branch'] = effective_branch
        exam_info['semester'] = effective_semester

        db_filename = json_file or f"manual_{int(time.time())}.json"
        exam_info['original_filename'] = exam_info.get('original_filename') or db_filename

        # Cleanup and optional correction via grammar service
        try:
            papers_data = clean_and_maybe_correct(papers_data)
        except Exception as gerr:
            print(f"[SAVE-blueprint] Grammar correction pass failed: {gerr}")

        pid = save_paper(
            filename=db_filename,
            branch=branch,
            semester=semester,
            subject=subject,
            papers_data=papers_data,
            exam_info=exam_info
        )

        _sync_extracted_json(db_filename, exam_info, papers_data)
        similarity = process_saved_questions_safely(
            papers_data=papers_data,
            subject=subject,
            exam_info=exam_info,
        )

        return jsonify({
            'success': True,
            'paper_id': pid,
            'json_file': db_filename,
            'similarity': similarity,
        }), 200
    except Exception as e:
        print(f"Error in save_extracted_paper (blueprint): {e}")
        return jsonify({'error': str(e)}), 500
