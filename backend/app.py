import os
from importlib import import_module
from flask import Flask
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=True)

def create_app(test_config=None):
    app = Flask(__name__)

    # Configure folders
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    EXTRACTED_JSON_FOLDER = os.path.join(os.path.dirname(__file__), 'extracted_json')
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['EXTRACTED_JSON_FOLDER'] = EXTRACTED_JSON_FOLDER

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(EXTRACTED_JSON_FOLDER, exist_ok=True)

    # Enable CORS
    CORS(app)

    def register_blueprint(module_path, blueprint_name, label):
        try:
            module = import_module(module_path)
            app.register_blueprint(getattr(module, blueprint_name))
        except Exception as e:
            print(f"[APP] Warning: could not register {label} blueprint: {e}")

    # Register blueprints independently so optional dependencies do not block
    # core routes such as admin auth.
    register_blueprint('routes.core', 'core_bp', 'core')
    register_blueprint('routes.upload', 'upload_bp', 'upload')
    register_blueprint('routes.save', 'save_bp', 'save')
    register_blueprint('routes.questions', 'questions_bp', 'questions')
    register_blueprint('routes.papers', 'papers_bp', 'papers')
    register_blueprint('routes.faculty', 'faculty_bp', 'faculty')
    register_blueprint('routes.stats', 'stats_bp', 'stats')
    register_blueprint('routes.syllabus', 'syllabus_bp', 'syllabus')
    register_blueprint('routes.rua', 'rua_bp', 'rua')
    register_blueprint('routes.paper_generation', 'generation_bp', 'paper generation')

    # Additional blueprints may be registered elsewhere as refactor progresses

    return app
