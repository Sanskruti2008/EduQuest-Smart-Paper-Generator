from typing import List, Dict, Any
import database as db

def save_paper(filename: str, branch: str, semester: str, subject: str, papers_data: List[Dict], exam_info: Dict) -> int:
    """Thin wrapper for database.save_paper_with_questions"""
    return db.save_paper_with_questions(
        filename=filename,
        branch=branch,
        semester=semester,
        subject=subject,
        papers_data=papers_data,
        exam_info=exam_info
    )

def get_paper_by_id(pid: int):
    return db.get_paper_by_id(pid)

def get_all_questions(branch=None, semester=None, subject=None, limit=100):
    return db.get_all_questions(branch, semester, subject, limit)

def search_questions(term: str, branch=None, semester=None, subject=None, limit=50):
    return db.search_questions(term, branch, semester, subject, limit)

def get_all_uploaded_papers(limit: int = 100, offset: int = 0):
    return db.get_all_uploaded_papers(limit=limit, offset=offset)
