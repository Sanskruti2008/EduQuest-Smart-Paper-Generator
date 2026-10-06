from io import BytesIO
from zipfile import ZipFile

from app import create_app
from routes import stats as stats_route
from utils.auth import _generate_role_token


def test_stats_require_admin_authentication(monkeypatch):
    app = create_app()
    app.config['TESTING'] = True
    client = app.test_client()
    get_stats = stats_route.db.get_stats
    monkeypatch.setattr(stats_route.db, 'get_stats', lambda: {
        'total_papers': 7,
        'total_questions': 42,
        'papers_by_branch': {'CSE': 7},
        'papers_by_semester': [{'branch': 'CSE', 'semester': '1', 'count': 7}],
    })

    assert client.get('/api/stats').status_code == 401
    for endpoint in ('/api/admin/faculty', '/api/uploaded-papers', '/api/papers/1'):
        assert client.get(endpoint).status_code == 401

    faculty_token = _generate_role_token('faculty@example.test', 'faculty')
    faculty_response = client.get(
        '/api/stats',
        headers={'Authorization': f'Bearer {faculty_token}'},
    )
    assert faculty_response.status_code == 403

    admin_token = _generate_role_token('admin@example.test', 'admin')
    admin_response = client.get(
        '/api/stats',
        headers={'Authorization': f'Bearer {admin_token}'},
    )
    assert admin_response.status_code == 200
    assert admin_response.get_json()['stats']['total_papers'] == 7

    def fail_to_connect():
        raise RuntimeError('database unavailable')

    monkeypatch.setattr(stats_route.db, 'get_stats', get_stats)
    monkeypatch.setattr(stats_route.db, 'get_supabase_client', fail_to_connect)
    failed_response = client.get(
        '/api/stats',
        headers={'Authorization': f'Bearer {admin_token}'},
    )
    assert failed_response.status_code == 500
    assert 'stats' not in failed_response.get_json()


def test_reviewed_paper_download_uses_edited_question_text(monkeypatch):
    app = create_app()
    app.config['TESTING'] = True
    client = app.test_client()
    token = _generate_role_token('faculty@example.test', 'faculty')
    reviewed_paper = {
        'paper_information': {
            'branch': 'CSE',
            'semester': 4,
            'subject': 'Data Structures',
            'subject_code': 'DS',
            'exam_type': 'University',
            'paper_total_marks': 2,
        },
        'sections': {
            'Q1': {
                'questions_to_attempt': 1,
                'questions': [{
                    'canonical_id': 'question-1',
                    'question_text': 'Explain a balanced binary search tree.',
                    'unit': 'Unit-I',
                    'marks': 2,
                    'rua': 'U',
                    'difficulty': 'Easy',
                    'course_outcome': 'CO1',
                }],
            },
        },
    }

    assert client.post('/api/download-reviewed-paper', json=reviewed_paper).status_code == 401
    response = client.post(
        '/api/download-reviewed-paper',
        json=reviewed_paper,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 200
    assert response.mimetype == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    with ZipFile(BytesIO(response.data)) as document:
        document_xml = document.read('word/document.xml')
    assert b'Explain a balanced binary search tree.' in document_xml
