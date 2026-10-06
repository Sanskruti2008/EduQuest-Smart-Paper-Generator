import os
import time

from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename

import database as db
from RUA_extractor import extract_rua
from utils.auth import require_admin

rua_bp = Blueprint('rua_bp', __name__)


def _normalize_rua_output(raw_rua: dict) -> tuple[list[dict], dict]:
    units = []
    totals = {'R': 0, 'U': 0, 'A': 0, 'Total': 0}

    if not isinstance(raw_rua, dict):
        return units, totals

    for key, value in raw_rua.items():
        if not isinstance(value, dict):
            continue

        if key == 'TOTAL':
            totals = {
                'R': int(value.get('R', 0) or 0),
                'U': int(value.get('U', 0) or 0),
                'A': int(value.get('A', 0) or 0),
                'Total': int(value.get('Total', 0) or 0),
            }
            continue

        units.append({
            'unit_key': key,
            'unit_name': (value.get('title') or key.replace('Unit-', 'Unit ')).strip(),
            'R': int(value.get('R', 0) or 0),
            'U': int(value.get('U', 0) or 0),
            'A': int(value.get('A', 0) or 0),
            'Total': int(value.get('Total', 0) or 0),
        })

    return units, totals


@rua_bp.route('/api/admin/rua/extract', methods=['POST'])
@require_admin
def extract_rua_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No PDF file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No PDF file selected'}), 400

        filename = secure_filename(file.filename)
        if not filename.lower().endswith('.pdf'):
            return jsonify({'error': 'Only PDF files are allowed'}), 400

        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)

        stored_filename = f"{int(time.time())}_{filename}"
        stored_path = os.path.join(upload_folder, stored_filename)
        file.save(stored_path)

        raw_rua = extract_rua(stored_path)
        units, total = _normalize_rua_output(raw_rua)

        return jsonify({
            'success': True,
            'filename': filename,
            'stored_filename': stored_filename,
            'units': units,
            'total': total,
        }), 200
    except Exception as e:
        print(f'Error in extract_rua_pdf: {e}')
        return jsonify({'error': str(e)}), 500


@rua_bp.route('/api/admin/rua/save', methods=['POST'])
@require_admin
def save_rua_values():
    try:
        body = request.get_json(force=True)
        if not body:
            return jsonify({'error': 'Empty request body'}), 400

        subject_name = (body.get('subject_name') or '').strip()
        if not subject_name:
          
            return jsonify({'error': 'Subject is required'}), 400

        units = body.get('units') or []
        if not units:
            return jsonify({'error': 'No RUA values provided'}), 400

        curriculum = {
            'subject_name': subject_name,
            'subject_code': (body.get('subject_code') or '').strip(),
            'branch': (body.get('branch') or '').strip(),
            'semester': body.get('semester'),
            'units': [],
        }

        for unit in units:
            unit_name = (unit.get('unit_name') or unit.get('unit_key') or '').strip()
            curriculum['units'].append({
                'unit_name': unit_name or 'Unit',
                'rua_markings': {
                    'unit_name': unit_name or 'Unit',
                    'R': int(unit.get('R', 0) or 0),
                    'U': int(unit.get('U', 0) or 0),
                    'A': int(unit.get('A', 0) or 0),
                    'Total': int(unit.get('Total', 0) or 0),
                },
            })

        saved = db.save_curriculum(curriculum)
        return jsonify({'success': True, 'saved': saved}), 200
    except Exception as e:
        print(f'Error in save_rua_values: {e}')
        return jsonify({'error': str(e)}), 500