"""EduQuest Paper Generation Engine public interface."""

__all__ = ["generate_question_paper"]


def generate_question_paper(*args, **kwargs):
    """Lazily import the heavy generation pipeline to avoid import-time crashes."""
    from paper_generation.generator import generate_question_paper as _generate_question_paper

    return _generate_question_paper(*args, **kwargs)