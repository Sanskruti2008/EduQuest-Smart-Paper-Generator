from typing import List, Tuple
import database as db

def clean_and_maybe_correct(papers_data: list) -> list:
    """
    Run local cleanup on all questions and optionally call remote correction
    when configured. Mutates and returns papers_data.
    """
    flat = []
    for p_idx, paper in enumerate(papers_data):
        for q_idx, question in enumerate(paper.get('questions', [])):
            raw = (question.get('question_text') or '').strip()
            cleaned = db._basic_cleanup_text(raw)
            flat.append((p_idx, q_idx, cleaned))

    cleaned_texts = [t for (_p, _q, t) in flat]
    flagged = [i for i, txt in enumerate(cleaned_texts) if db._needs_remote_correction(txt)]
    grammar_api_key, grammar_provider = db._pick_grammar_api_key()
    if grammar_api_key and cleaned_texts:
        fallback = []
        if not flagged:
            fallback = [
                i for i, txt in enumerate(cleaned_texts)
                if len(txt) >= 24 and len(txt.split()) >= 5
            ][: db.GRAMMAR_BATCH_LIMIT if hasattr(db, 'GRAMMAR_BATCH_LIMIT') else len(cleaned_texts)]

        candidate_indices = (flagged + fallback)[: db.GRAMMAR_BATCH_LIMIT if hasattr(db, 'GRAMMAR_BATCH_LIMIT') else len(cleaned_texts)]
        if candidate_indices:
            to_send = []
            seen = set()
            for idx in candidate_indices:
                text = cleaned_texts[idx]
                key = text.lower().strip()
                if key and key not in seen:
                    to_send.append(text)
                    seen.add(key)
            if to_send:
                if grammar_provider == 'grok':
                    corrected = db._correct_texts_with_grok(to_send, grammar_api_key)
                elif grammar_provider == 'groq':
                    corrected = db._correct_texts_with_groq(to_send, grammar_api_key)
                else:
                    corrected = db._correct_texts_with_openai(to_send, grammar_api_key)
                for dst_idx, src_idx in enumerate(candidate_indices[:len(corrected)]):
                    cleaned_texts[src_idx] = corrected[dst_idx]

    for idx, (_p, _q, _old) in enumerate(flat):
        new_text = cleaned_texts[idx] if idx < len(cleaned_texts) else _old
        try:
            question = papers_data[_p]['questions'][_q]
            original_text = str(question.get('original_question_text') or question.get('question_text') or _old).strip()
            if not original_text:
                original_text = _old.strip()
            if question.get('question_text') is None:
                question['question_text'] = _old

            question['original_question_text'] = original_text
            question['question_text'] = new_text

            if new_text and new_text != original_text:
                question['grammar_suggestion'] = new_text
                question['had_grammar_correction'] = True
            else:
                question['grammar_suggestion'] = ''
                question['had_grammar_correction'] = False
        except Exception:
            pass

    return papers_data
