"""
Simple CLI reviewer for extracted question JSON files.
Usage:
  python review_extracted.py <extracted_json_path> [--interactive]

- Without --interactive: prints questions and basic metadata.
- With --interactive: steps through each question and lets you keep/edit/delete/mark.
Saves a reviewed file alongside the original with suffix `_reviewed.json`.
"""
import json
import sys
import os


def load_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_file(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def print_question(q, idx=None):
    if idx is not None:
        print(f"[{idx}] ({q.get('question_number','?')}) [{q.get('status','?')}] confidence={q.get('confidence_score',0)}")
    else:
        print(f"({q.get('question_number','?')}) [{q.get('status','?')}] confidence={q.get('confidence_score',0)}")
    print(f"  Marks: {q.get('marks')}")
    print(f"  CO: {q.get('course_outcome')}")
    print(f"  Bloom: {q.get('bloom_level')}")
    print(f"  Text: {q.get('question_text')}")
    if q.get('sub_questions'):
        print(f"  Sub-questions: {len(q.get('sub_questions'))}")


def interactive_review(data, out_path):
    papers = data.get('papers', [])
    if not papers:
        print("No papers/questions found.")
        return

    paper = papers[0]
    qs = paper.get('questions', [])
    i = 0
    changed = False
    while i < len(qs):
        q = qs[i]
        print('\n' + '-'*60)
        print_question(q, idx=i+1)
        print("Commands: [k]eep  [e]dit  [d]elete  [a]ccept  [r]needs_review  [n]ext  [q]quit")
        cmd = input("> ").strip().lower()
        if cmd in ('k','n',''):
            i += 1
            continue
        if cmd == 'q':
            break
        if cmd == 'd':
            confirm = input("Delete this question? (y/N): ").strip().lower()
            if confirm == 'y':
                qs.pop(i)
                changed = True
                continue
            else:
                continue
        if cmd == 'a':
            q['status'] = 'accepted'
            changed = True
            i += 1
            continue
        if cmd == 'r':
            q['status'] = 'needs_review'
            changed = True
            i += 1
            continue
        if cmd == 'e':
            print('Enter new question text (single line). Leave empty to keep')
            new = input('Text: ').rstrip()
            if new:
                q['question_text'] = new
            newm = input(f"Marks [{q.get('marks')}]: ").strip()
            if newm:
                try:
                    q['marks'] = int(newm)
                except:
                    print('Invalid marks, keeping original')
            newco = input(f"Course outcome [{q.get('course_outcome')}]: ").strip()
            if newco:
                q['course_outcome'] = newco
            q['status'] = 'needs_review'
            changed = True
            i += 1
            continue
        print('Unknown command')

    if changed:
        # renumber
        for idx, q in enumerate(qs, start=1):
            q['question_number'] = str(idx)
        save_file(out_path, data)
        print(f"Saved reviewed file: {out_path}")
    else:
        print('No changes made.')


def print_summary(data):
    print('--- Extraction Summary ---')
    print('Exam info:', data.get('exam_info', {}))
    papers = data.get('papers', [])
    total = 0
    needs = 0
    for p in papers:
        qs = p.get('questions', [])
        total += len(qs)
        needs += sum(1 for q in qs if q.get('status') == 'needs_review')
    print(f'Total questions: {total} (needs_review: {needs})')
    print('--- Questions ---')
    if papers:
        for idx, q in enumerate(papers[0].get('questions', []), start=1):
            st = q.get('status','')
            conf = q.get('confidence_score',0)
            print(f"[{idx}] ({q.get('marks')}) [{st}] conf={conf} -> {q.get('question_text')}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python review_extracted.py <extracted_json_path> [--interactive]')
        sys.exit(1)
    path = sys.argv[1]
    interactive = '--interactive' in sys.argv or '-i' in sys.argv
    if not os.path.exists(path):
        print('File not found:', path)
        sys.exit(2)
    data = load_file(path)
    print_summary(data)
    out_path = os.path.splitext(path)[0] + '_reviewed.json'
    if interactive:
        interactive_review(data, out_path)
    else:
        print('\nRun with --interactive to review and correct questions interactively.')
        print(f"To review interactively: python review_extracted.py {path} --interactive")
        print(f"A copy will be saved to: {out_path}")
