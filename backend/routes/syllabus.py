import json
import os

from flask import Blueprint, jsonify, request

from syllabus_analyzer import SyllabusAnalyzer


syllabus_bp = Blueprint('syllabus', __name__)


def _syllabus_file_path() -> str:
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'syllabus_data.json')


@syllabus_bp.route('/api/syllabus', methods=['GET'])
def get_syllabus_data():
    try:
        syllabus_file = _syllabus_file_path()

        if not os.path.exists(syllabus_file):
            return jsonify({'error': 'Syllabus data not found'}), 404

        with open(syllabus_file, 'r', encoding='utf-8') as f:
            syllabus_data = json.load(f)

        return jsonify(syllabus_data), 200
    except Exception as e:
        print(f"Error in get_syllabus_data: {str(e)}")
        return jsonify({'error': str(e)}), 500


@syllabus_bp.route('/api/syllabus/subjects', methods=['GET'])
def get_subjects():
    try:
        analyzer = SyllabusAnalyzer(_syllabus_file_path())
        subjects = analyzer.get_all_subjects()
        return jsonify({'success': True, 'subjects': subjects}), 200
    except Exception as e:
        print(f"Error in get_subjects: {str(e)}")
        return jsonify({'error': str(e)}), 500


@syllabus_bp.route('/api/syllabus/<subject_id>', methods=['GET'])
def get_subject_details(subject_id):
    try:
        analyzer = SyllabusAnalyzer(_syllabus_file_path())
        subject = analyzer.get_subject_by_id(subject_id)

        if not subject:
            return jsonify({'error': 'Subject not found'}), 404

        return jsonify({'success': True, 'subject': subject}), 200
    except Exception as e:
        print(f"Error in get_subject_details: {str(e)}")
        return jsonify({'error': str(e)}), 500


@syllabus_bp.route('/api/syllabus/<subject_id>/chapter/<int:chapter_number>', methods=['GET'])
def get_chapter_details(subject_id, chapter_number):
    try:
        analyzer = SyllabusAnalyzer(_syllabus_file_path())
        chapter = analyzer.get_chapter_details(subject_id, chapter_number)

        if not chapter:
            return jsonify({'error': 'Chapter not found'}), 404

        return jsonify({'success': True, 'chapter': chapter}), 200
    except Exception as e:
        print(f"Error in get_chapter_details: {str(e)}")
        return jsonify({'error': str(e)}), 500


@syllabus_bp.route('/api/syllabus/<subject_id>/analysis', methods=['GET'])
def get_rua_analysis(subject_id):
    try:
        analyzer = SyllabusAnalyzer(_syllabus_file_path())
        analysis = analyzer.analyze_rua_compliance(subject_id)
        return jsonify({'success': True, 'analysis': analysis}), 200
    except Exception as e:
        print(f"Error in get_rua_analysis: {str(e)}")
        return jsonify({'error': str(e)}), 500


@syllabus_bp.route('/api/syllabus/<subject_id>/preparation-guide', methods=['GET'])
def get_preparation_guide(subject_id):
    try:
        analyzer = SyllabusAnalyzer(_syllabus_file_path())
        guide = analyzer.get_exam_preparation_guide(subject_id)
        return jsonify({'success': True, 'guide': guide}), 200
    except Exception as e:
        print(f"Error in get_preparation_guide: {str(e)}")
        return jsonify({'error': str(e)}), 500


@syllabus_bp.route('/api/syllabus/<subject_id>/weightage', methods=['GET'])
def get_weightage_distribution(subject_id):
    try:
        analyzer = SyllabusAnalyzer(_syllabus_file_path())
        distribution = analyzer.get_weightage_distribution(subject_id)
        return jsonify({'success': True, 'distribution': distribution}), 200
    except Exception as e:
        print(f"Error in get_weightage_distribution: {str(e)}")
        return jsonify({'error': str(e)}), 500


@syllabus_bp.route('/api/syllabus/<subject_id>/chapter/<int:chapter_number>/study-plan', methods=['GET'])
def get_chapter_study_plan(subject_id, chapter_number):
    try:
        analyzer = SyllabusAnalyzer(_syllabus_file_path())
        study_plan = analyzer.generate_chapter_study_plan(subject_id, chapter_number)
        return jsonify({'success': True, 'study_plan': study_plan}), 200
    except Exception as e:
        print(f"Error in get_chapter_study_plan: {str(e)}")
        return jsonify({'error': str(e)}), 500


@syllabus_bp.route('/api/syllabus/<subject_id>/missing-ruas', methods=['GET'])
def get_missing_ruas(subject_id):
    try:
        analyzer = SyllabusAnalyzer(_syllabus_file_path())
        missing = analyzer.find_missing_ruas(subject_id)
        return jsonify({'success': True, 'missing_analysis': missing}), 200
    except Exception as e:
        print(f"Error in get_missing_ruas: {str(e)}")
        return jsonify({'error': str(e)}), 500


@syllabus_bp.route('/api/syllabus/<subject_id>/compare', methods=['GET'])
def compare_chapters(subject_id):
    try:
        chapter1 = request.args.get('chapter1', type=int)
        chapter2 = request.args.get('chapter2', type=int)

        if not chapter1 or not chapter2:
            return jsonify({'error': 'Both chapter1 and chapter2 parameters are required'}), 400

        analyzer = SyllabusAnalyzer(_syllabus_file_path())
        comparison = analyzer.compare_chapters(subject_id, chapter1, chapter2)
        return jsonify({'success': True, 'comparison': comparison}), 200
    except Exception as e:
        print(f"Error in compare_chapters: {str(e)}")
        return jsonify({'error': str(e)}), 500