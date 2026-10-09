"""
Database module - works with the existing Supabase schema without any ALTER TABLE.
Extra metadata is packed into raw_json (questionpaper) and question_hash (question).
"""
import os
import json
import re
import time
import hashlib
from datetime import datetime
from typing import List, Dict, Optional
from supabase import create_client, Client
from dotenv import load_dotenv
from groq import Groq
import requests

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=True)

# ---------------------------------------------------------------------------
# Smart deduplication helpers
# ---------------------------------------------------------------------------
_PUNCT_RE = re.compile(r"[^\w\s]")   # remove all punctuation
_WS_RE    = re.compile(r"\s+")        # collapse whitespace


# ---------------------------------------------------------------------------
# Question text cleaning / optional grammar correction
# ---------------------------------------------------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("GRAMMAR_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("GROQ_TOKEN")
GROK_API_KEY = os.getenv("GROK_API_KEY") or os.getenv("XAI_API_KEY")
GRAMMAR_BATCH_LIMIT = int(os.getenv("GRAMMAR_BATCH_LIMIT", "8"))


def _pick_grammar_api_key() -> tuple[Optional[str], str]:
    """Return the configured grammar API key and provider name.
    Prefers OpenAI-compatible keys, then Groq, then xAI/Grok.
    """
    if OPENAI_API_KEY:
        return OPENAI_API_KEY, "openai"
    if GROQ_API_KEY:
        return GROQ_API_KEY, "groq"
    if GROK_API_KEY:
        return GROK_API_KEY, "grok"
    return None, ""


def _basic_cleanup_text(text: str) -> str:
    """Lightweight, fast cleanup to fix common OCR artefacts and normalize spacing.
    This is intentionally conservative so we don't change meaning.
    """
    if not text or not isinstance(text, str):
        return ""
    t = text
    # Common ligatures and punctuation fixes
    replacements = {
        "ﬁ": "fi",
        "ﬂ": "fl",
        "—": "-",
        "–": "-",
        "•": "-",
        "\u200b": "",
        "\u00ad": "",  # soft hyphen
    }
    for k, v in replacements.items():
        t = t.replace(k, v)

    # Replace multiple hyphens / equals with single dash
    t = re.sub(r"[-=]{2,}", "-", t)

    # Fix common OCR mistakes: 0/O at word edges, 1/l and | confusion in words
    t = re.sub(r"\b0([A-Za-z])", r"O\1", t)
    t = re.sub(r"([A-Za-z])0\b", r"\1O", t)
    t = re.sub(r"\b1([a-z])", r"l\1", t)

    # Collapse whitespace and trim
    t = _WS_RE.sub(" ", t).strip()

    # Ensure sentence starts with capital letter where appropriate (keep acronyms intact)
    if t and t[0].islower():
        t = t[0].upper() + t[1:]

    return t


def _needs_remote_correction(text: str) -> bool:
    """Heuristic to decide whether to invoke a remote grammar/spell correction.
    Keep it conservative, but broaden enough to catch realistic OCR mistakes in
    exam questions such as "select ate" or "ERPlection".
    """
    if not text or len(text) < 20:
        return False
    # If there are unusual non-alphanumeric characters, likely OCR noise
    if re.search(r"[^A-Za-z0-9\s\.,;:\-()'\"\?/&%]", text):
        return True
    words = text.split()
    if len(words) == 0:
        return False
    # If lots of very long tokens (likely glue errors), flag it
    long_tokens = sum(1 for w in words if len(w) > 25)
    if long_tokens / max(1, len(words)) > 0.1:
        return True
    # If many tokens contain both digits and letters (ocr blends), flag it
    mixed = sum(1 for w in words if re.search(r"(?=.*[A-Za-z])(?=.*[0-9])", w))
    if mixed > 0:
        return True
    # OCR often creates single-word errors that do not include punctuation, so
    # also trigger on common exam-question length patterns when a likely typo is
    # present. This catches phrases like "select ate" and "ERPlection".
    if len(words) >= 6:
        typo_like = any(
            re.search(r"\b(?:select\s+ate|ERPlection|recuitment|spellng|slect|defin\w+|methode|procedur\w+)\b", text, re.IGNORECASE)
            or re.search(r"\b[A-Z]{2,}[a-z]+[A-Z][a-z]+\b", text)
            for _ in [0]
        )
        if typo_like:
            return True
    return False


def _is_likely_heading(text: str) -> bool:
    """Return True for texts that look like headers/footers or noise that should not
    be stored as questions. This is conservative — prefer skipping obvious non-questions.
    """
    if not text:
        return True
    t = text.strip()
    if len(t) < 10:
        return True
    low = t.lower()
    # common non-question prefixes found in papers
    if re.match(r'^(page|subject|time|total|maximum|marks|question paper|university|college)\b', low):
        return True
    # lines that are mostly numeric or short enumerations
    if re.fullmatch(r'[\d\s\-:\./()]+', t):
        return True
    return False


def _correct_texts_with_llm(texts: List[str], api_key: str, provider: str = "openai") -> List[str]:
    """Batch-correct texts using OpenAI-compatible, Groq, or Grok/xAI APIs.
    Returns corrected texts in same order. On failure, returns original texts.
    """
    if not api_key or not texts:
        return texts

    try:
        batch = texts[:GRAMMAR_BATCH_LIMIT]
        numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(batch))
        prompt = (
            "You are a concise and reliable proofreader for exam questions. "
            "For each numbered item below, correct grammar and spelling while preserving meaning, numbering, and any math or code snippets. "
            "Be terse and return a JSON array of corrected question strings only, in the same order. No extra text.\n\n"
            f"Questions:\n{numbered}"
        )

        if provider == "groq":
            client = Groq(api_key=api_key)
            resp = client.chat.completions.create(
                model=os.getenv("GROQ_GRAMMAR_MODEL", "openai/gpt-oss-20b"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=512,
            )
            raw = resp.choices[0].message.content.strip()
        elif provider == "grok":
            url = "https://api.x.ai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            body = {
                "model": os.getenv("GROK_MODEL", "grok-2-latest"),
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0,
                "max_tokens": 512,
            }
            resp = requests.post(url, headers=headers, json=body, timeout=20)
            if resp.status_code != 200:
                print(f"[GRAMMAR] {provider.upper()} API error {resp.status_code}: {resp.text}")
                return texts
            raw = resp.json()["choices"][0]["message"]["content"].strip()
        else:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            body = {
                "model": os.getenv("OPENAI_GRAMMAR_MODEL", "gpt-4o-mini"),
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0,
                "max_tokens": 512,
            }
            resp = requests.post(url, headers=headers, json=body, timeout=20)
            if resp.status_code != 200:
                print(f"[GRAMMAR] {provider.upper()} API error {resp.status_code}: {resp.text}")
                return texts
            raw = resp.json()["choices"][0]["message"]["content"].strip()

        m = re.search(r"\[.*\]", raw, re.DOTALL)
        corrected = json.loads(m.group(0)) if m else json.loads(raw)
        if isinstance(corrected, list) and len(corrected) == len(batch):
            return corrected + texts[len(batch):]
    except Exception as e:
        print(f"[GRAMMAR] {provider.upper()} correction failed: {e}")
    return texts


def _correct_texts_with_openai(texts: List[str], api_key: str) -> List[str]:
    """Backward-compatible wrapper for OpenAI grammar correction."""
    return _correct_texts_with_llm(texts, api_key, provider="openai")


def _correct_texts_with_groq(texts: List[str], api_key: str) -> List[str]:
    """Wrapper for Groq grammar correction."""
    return _correct_texts_with_llm(texts, api_key, provider="groq")


def _correct_texts_with_grok(texts: List[str], api_key: str) -> List[str]:
    """Wrapper for Grok/xAI grammar correction."""
    return _correct_texts_with_llm(texts, api_key, provider="grok")


def _canonical(text: str) -> str:
    """Aggressively normalise question text for fingerprinting.
    Lowercases, strips punctuation, collapses whitespace.
    Two OCR-variant copies of the same question will produce the same canonical form.
    """
    t = text.lower()
    t = _PUNCT_RE.sub(" ", t)          # replace punctuation with space
    t = _WS_RE.sub(" ", t).strip()     # collapse runs of whitespace
    return t

def _content_hash(text: str) -> str:
    """SHA-256 of the canonical text — used as a stable unique key in question_hash."""
    return hashlib.sha256(_canonical(text).encode("utf-8")).hexdigest()
    
def _extract_numbers_from_text(text: str) -> List[str]:
    """Return numeric tokens found in text, preserving appearance order."""
    if not text:
        return []

    numbers: List[str] = []
    seen = set()
    covered_spans = []
    text_str = str(text)

    for pattern in (r'\d+\/\d+', r'\d+\.\d+', r'\d+(?:st|nd|rd|th)'):
        for match in re.finditer(pattern, text_str, re.IGNORECASE):
            value = match.group(0)
            if value not in seen:
                seen.add(value)
                numbers.append(value)
            covered_spans.append(match.span())

    def _overlaps(span):
        for start, end in covered_spans:
            if span[0] < end and span[1] > start:
                return True
        return False

    for match in re.finditer(r'\d+', text_str):
        if _overlaps(match.span()):
            continue
        value = match.group(0)
        if value not in seen:
            seen.add(value)
            numbers.append(value)
    return numbers

# ---------------------------------------------------------------------------

_sb: Client = None
_sb_admin: Client = None


def _read_supabase_config() -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Read Supabase config from env, ignoring placeholder values."""
    url = os.getenv("SUPABASE_URL", "").strip()
    service_key = os.getenv("SUPABASE_SERVICE_KEY", "").strip()
    anon_key = os.getenv("SUPABASE_ANON_KEY", "").strip() or os.getenv("SUPABASE_KEY", "").strip()

    def _is_placeholder(value: str) -> bool:
        upper = value.upper()
        return not value or upper.startswith("REPLACE") or "YOUR-" in upper or "YOUR_" in upper

    if _is_placeholder(service_key):
        service_key = ""
    if _is_placeholder(anon_key):
        anon_key = ""

    if service_key:
        return url or None, service_key, "service"
    if anon_key:
        return url or None, anon_key, "anon"
    return url or None, None, None

def get_supabase_client() -> Client:
    global _sb
    if _sb is None:
        supabase_url, supabase_key, key_type = _read_supabase_config()
        if not supabase_url or not supabase_key:
            raise Exception(
                "Supabase is not configured. Set SUPABASE_URL and either SUPABASE_SERVICE_KEY or SUPABASE_ANON_KEY in backend/.env."
            )
        _sb = create_client(supabase_url, supabase_key)
        print(f"[DB] Supabase client initialized using {key_type} key")
    return _sb


def get_supabase_admin_client() -> Client:
    """Return the backend-only client that can use Supabase Auth admin APIs."""
    global _sb_admin
    if _sb_admin is None:
        supabase_url = os.getenv("SUPABASE_URL", "").strip()
        service_key = os.getenv("SUPABASE_SERVICE_KEY", "").strip()
        if (
            not supabase_url
            or not service_key
            or service_key.upper().startswith("REPLACE")
            or "YOUR-" in service_key.upper()
            or "YOUR_" in service_key.upper()
        ):
            raise RuntimeError("Supabase Auth administration is not configured.")
        _sb_admin = create_client(supabase_url, service_key)
    return _sb_admin


def create_supabase_auth_client() -> Client:
    """Create an isolated public-key client for a single password sign-in."""
    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    anon_key = (
        os.getenv("SUPABASE_ANON_KEY", "").strip()
        or os.getenv("SUPABASE_KEY", "").strip()
    )
    if (
        not supabase_url
        or not anon_key
        or anon_key.upper().startswith("REPLACE")
        or "YOUR-" in anon_key.upper()
        or "YOUR_" in anon_key.upper()
    ):
        raise RuntimeError("Supabase Auth sign-in is not configured.")
    return create_client(supabase_url, anon_key)


def init_database():
    """No-op – schema already exists. Optional ALTER TABLE SQL for full columns:
    ALTER TABLE questionpaper ADD COLUMN IF NOT EXISTS filename TEXT;
    ALTER TABLE questionpaper ADD COLUMN IF NOT EXISTS branch TEXT;
    ALTER TABLE questionpaper ADD COLUMN IF NOT EXISTS semester TEXT;
    ALTER TABLE questionpaper ADD COLUMN IF NOT EXISTS total_questions INTEGER DEFAULT 0;
    ALTER TABLE question ADD COLUMN IF NOT EXISTS question_number TEXT;
    ALTER TABLE question ADD COLUMN IF NOT EXISTS bloom_level TEXT;
    ALTER TABLE question ADD COLUMN IF NOT EXISTS course_outcome TEXT;
    ALTER TABLE question ADD COLUMN IF NOT EXISTS sub_label TEXT;
    ALTER TABLE question ADD COLUMN IF NOT EXISTS sub_questions JSONB DEFAULT '[]';
    ALTER TABLE question ADD COLUMN IF NOT EXISTS has_diagram BOOLEAN DEFAULT FALSE;
    ALTER TABLE question ADD COLUMN IF NOT EXISTS has_math BOOLEAN DEFAULT FALSE;
    ALTER TABLE question ADD COLUMN IF NOT EXISTS images JSONB DEFAULT '[]';
    ALTER TABLE question ADD COLUMN IF NOT EXISTS answer TEXT;
    ALTER TABLE question ADD COLUMN IF NOT EXISTS chapter TEXT;
    ALTER TABLE question ADD COLUMN IF NOT EXISTS topic_text TEXT;
    """
    return True


def get_admin_user(username: str) -> Optional[Dict]:
    """Fetch an admin user record by username."""
    sb = get_supabase_client()
    result = sb.table("admin_users").select("*").eq("username", username).limit(1).execute()
    return result.data[0] if result.data else None


def create_admin_user(username: str, password_hash: str) -> Dict:
    """Create an admin user with a pre-hashed password (bcrypt)."""
    sb = get_supabase_client()
    result = (
        sb.table("admin_users")
        .insert({"username": username, "password_hash": password_hash})
        .execute()
    )
    return result.data[0] if result.data else {}

# ---------------------------------------------------------------------------
# RUA classifier via Groq
# ---------------------------------------------------------------------------
_GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def _keyword_rua(text: str) -> str:
    """Fast keyword fallback: R / U / A."""
    t = text.lower()
    if any(k in t for k in ["define", "list", "name", "state", "recall", "identify", "what is", "who", "when"]):
        return "R"
    if any(k in t for k in ["apply", "demonstrate", "calculate", "solve", "use", "implement",
                             "design", "develop", "construct", "write a program", "code"]):
        return "A"
    return "U"

def classify_rua_batch(question_texts: List[str]) -> List[str]:
    """
    Classify a batch of questions as R / U / A using Groq.
    Falls back to keyword heuristics if Groq is unavailable or raises.
    Returns a list of 'R', 'U', or 'A' strings in the same order.
    """
    if not _GROQ_API_KEY or not question_texts:
        return [_keyword_rua(t) for t in question_texts]

    numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(question_texts))
    prompt = (
        "You are an expert in Bloom's Taxonomy applied to engineering exam questions.\n"
        "Classify each question below as exactly ONE of:\n"
        "  R  – Remember  (recall facts, definitions, list, state, name, identify)\n"
        "  U  – Understand (explain, describe, discuss, compare, summarize, differentiate)\n"
        "  A  – Apply     (solve, calculate, design, implement, write code, demonstrate)\n\n"
        "Rules:\n"
        "- Reply with ONLY a JSON array of single letters, e.g. [\"R\",\"U\",\"A\",\"U\"]\n"
        "- The array length MUST equal the number of questions.\n"
        "- No explanation, no extra text.\n\n"
        f"Questions:\n{numbered}"
    )
    try:
        client = Groq(api_key=_GROQ_API_KEY)
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=256,
        )
        raw = resp.choices[0].message.content.strip()
        # Extract the JSON array even if surrounded by markdown fences
        m = re.search(r'\[.*\]', raw, re.DOTALL)
        labels = json.loads(m.group(0)) if m else json.loads(raw)
        if isinstance(labels, list) and len(labels) == len(question_texts):
            return [str(l).strip().upper()[0] if str(l).strip().upper()[0] in ('R','U','A') else 'U'
                    for l in labels]
    except Exception as e:
        print(f"[DB] Groq RUA classification failed, using keyword fallback: {e}")
    return [_keyword_rua(t) for t in question_texts]

# ---------------------------------------------------------------------------
# Bloom helpers
# ---------------------------------------------------------------------------
def auto_assign_bloom_level(question: Dict) -> str:
    text  = (question.get("question_text") or "").lower()
    marks = question.get("marks", 0)
    if any(k in text for k in ["define","list","name","state","recall"]):        return "Remember"
    if any(k in text for k in ["explain","describe","discuss","compare","summarize"]): return "Understand"
    if any(k in text for k in ["apply","demonstrate","calculate","solve","use"]): return "Apply"
    if any(k in text for k in ["analyze","examine","differentiate","investigate"]): return "Analyze"
    if any(k in text for k in ["evaluate","assess","judge","justify","critique"]): return "Evaluate"
    if any(k in text for k in ["create","design","develop","construct","formulate"]): return "Create"
    if marks <= 2:   return "Remember"
    elif marks <= 4: return "Understand"
    elif marks <= 6: return "Apply"
    elif marks <= 8: return "Analyze"
    elif marks <= 9: return "Evaluate"
    return "Create"

# ---------------------------------------------------------------------------
# CO / chapter helpers
# ---------------------------------------------------------------------------
_ROMAN = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6}

def _co_from_chapter(chapter: str, existing_co: str) -> str:
    """
    Derive an MSBTE course outcome label (CO1–CO6) from a chapter/unit string.
    MSBTE convention: Unit I → CO1, Unit II → CO2, … Unit V → CO5.
    Returns existing_co unchanged when no unit number can be found.
    """
    if existing_co and re.match(r'^CO\d$', existing_co.strip(), re.IGNORECASE):
        return existing_co.strip().upper()
    # "Unit I", "Unit-II", "Unit 3" etc.
    m = re.search(r'\bUnit[-\s]*(I{1,3}V?|VI?|IV|V?I{0,3})\b', chapter, re.IGNORECASE)
    if m:
        roman = m.group(1).upper()
        if roman in _ROMAN:
            return f"CO{_ROMAN[roman]}"
    # Arabic digit: "Chapter 2", "Unit 3"
    m = re.search(r'\b(?:Unit|Chapter|Ch)[-\s]*(\d)\b', chapter, re.IGNORECASE)
    if m:
        return f"CO{m.group(1)}"
    return existing_co or ""


def _unit_name_from_co(course_outcome: str, chapter: str) -> str:
    """Resolve CO1/CO2-style labels to a stable subject-scoped unit name."""
    co_match = re.fullmatch(r"CO\s*([1-5])", str(course_outcome or "").strip(), re.IGNORECASE)
    if co_match:
        return f"Unit {int(co_match.group(1))}"
    return chapter.strip() or "General"


def _get_or_create_unit(sb, subject_id: int, unit_name: str, _cache: Dict) -> int:
    """Look up or insert a unit row; cache results to avoid repeated DB hits."""
    key = f"{subject_id}:{unit_name}"
    if key in _cache:
        return _cache[key]
    r = sb.table("unit").select("unit_id") \
        .eq("subject_id", subject_id).eq("unit_name", unit_name).limit(1).execute()
    uid = r.data[0]["unit_id"] if r.data else \
        sb.table("unit").insert({"unit_name": unit_name, "subject_id": subject_id}).execute().data[0]["unit_id"]
    _cache[key] = uid
    return uid


def _get_or_create_topic(sb, unit_id: int, topic_name: str, _cache: Dict) -> int:
    """Look up or insert a topic row; cache results to avoid repeated DB hits."""
    key = f"{unit_id}:{topic_name}"
    if key in _cache:
        return _cache[key]
    r = sb.table("topic").select("topic_id") \
        .eq("unit_id", unit_id).eq("topic_name", topic_name).limit(1).execute()
    tid = r.data[0]["topic_id"] if r.data else \
        sb.table("topic").insert({"topic_name": topic_name, "unit_id": unit_id}).execute().data[0]["topic_id"]
    _cache[key] = tid
    return tid


def _get_or_create_question_bank(sb, subject_id: int, subject_name: str, _cache: Dict) -> Optional[int]:
    """Look up or insert the question bank for a subject."""
    key = f"{subject_id}:{subject_name}"
    if key in _cache:
        return _cache[key]

    try:
        r = sb.table("question_bank").select("question_bank_id") \
            .eq("subject_id", subject_id).limit(1).execute()
        if r.data:
            bank_id = r.data[0]["question_bank_id"]
            sb.table("question_bank").update({"bank_name": subject_name}).eq("question_bank_id", bank_id).execute()
        else:
            bank_id = sb.table("question_bank").insert({
                "subject_id": subject_id,
                "bank_name": subject_name,
            }).execute().data[0]["question_bank_id"]
    except Exception as e:
        print(f"[DB] question bank unavailable, continuing without bank link: {e}")
        bank_id = None

    _cache[key] = bank_id
    return bank_id

# ---------------------------------------------------------------------------
# Normalise a DB row back to our standard shape
# ---------------------------------------------------------------------------
def _norm_sem(s: str) -> str:
    """Normalise semester to bare digit(s): '1st Semester' -> '1', '1' -> '1'."""
    return ''.join(filter(str.isdigit, str(s or '')))


def _row_to_question(row: Dict, paper_meta: Optional[Dict] = None) -> Dict:
    # Extra fields: prefer dedicated columns (when they exist) over the JSON
    # payload inside question_hash.  The JSON fallback supports rows that were
    # written before the optional columns were added.
    extra: Dict = {}
    try:
        raw_hash = row.get("question_hash") or "{}"
        extra = json.loads(raw_hash) if raw_hash.strip().startswith("{") else {}
    except Exception:
        pass

    def _col(col_name: str, fallback):
        """Return dedicated-column value if present, else JSON fallback."""
        v = row.get(col_name)
        if v is not None and v != "" and v != []:
            return v
        return extra.get(col_name, fallback)

    q = {
        "id"             : row.get("question_id"),
        "question_id"    : row.get("question_id"),
        "text"           : row.get("question_text", ""),
        "question_number": _col("question_number", ""),
        "question_text"  : row.get("question_text", ""),
        "marks"          : row.get("marks") or 5,
        "course_outcome" : row.get("course_outcome") or extra.get("course_outcome"),
        "bloom_level"    : _col("bloom_level", "Understand"),
        "difficulty"     : row.get("difficulty_level") or "Medium",
        "chapter"        : _col("chapter", extra.get("chapter", "General")),
        "topic"          : extra.get("topic_text", "General"),
        "question_bank_id": _col("question_bank_id", extra.get("question_bank_id", "")),
        "subject_code"   : extra.get("subject_code", ""),
        "type"           : row.get("question_type") or "Short Answer",
        "answer"         : _col("answer", ""),
        "sub_label"      : _col("sub_label", ""),
        "sub_questions"  : _col("sub_questions", []),
        "has_diagram"    : _col("has_diagram", False),
        "has_math"       : _col("has_math", False),
        "identified_numbers": _col("identified_numbers", _extract_numbers_from_text(row.get("question_text", ""))),
        "images"         : _col("images", []),
        "created_at"     : row.get("created_at"),
        "source"         : row.get("source_type") or "OCR Extracted",
    }
    if paper_meta:
        pj = paper_meta.get("raw_json") or {}
        q["grade"]        = pj.get("semester", "Unknown")
        q["subject"]      = extra.get("subject") or pj.get("subject", "Unknown")
        q["subject_code"] = extra.get("subject_code") or pj.get("subject_code", "")
        q["paper"]   = {
            "id"           : paper_meta.get("paper_id"),
            "filename"     : pj.get("filename", ""),
            "upload_date"  : paper_meta.get("created_at"),
            "branch"       : extra.get("branch") or pj.get("branch", ""),
            "semester"     : extra.get("semester") or pj.get("semester", ""),
            "subject"      : extra.get("subject") or pj.get("subject", ""),
            "subject_code" : extra.get("subject_code") or pj.get("subject_code", ""),
            "exam_info"    : pj,
        }
    else:
        # Fallback: read from per-question extra_meta (stored since v2 uploads)
        if extra.get("subject"):
            q["subject"] = extra["subject"]
        if extra.get("subject_code"):
            q["subject_code"] = extra["subject_code"]
        if extra.get("semester"):
            q["grade"] = extra["semester"]
    return q

# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------
def save_paper_with_questions(filename: str, branch: str, semester: str,
                              subject: str, papers_data: List[Dict],
                              exam_info: Optional[Dict] = None) -> int:
    # --- Resolve all required FK IDs ---
    sb = get_supabase_client()
    meta = dict(exam_info or {})
    subject_name = (meta.get("subject_name") or meta.get("course_name") or meta.get("subject") or subject or "Unknown").strip() or "Unknown"
    subject_code = str(meta.get("subject_code") or meta.get("course_code") or "").strip().casefold()

    _sem_str  = str(meta.get("semester") or semester or "").strip().casefold()
    _branch_str = str(meta.get("branch") or branch or "").strip().casefold()

    # Subject identity is course code/name plus academic context. The same
    # course title can exist under different branches or semesters and must
    # not share units or question IDs across those contexts.
    if subject_code:
        sr = (sb.table("subject").select("subject_id")
              .ilike("subject_code", subject_code)
              .ilike("branch", _branch_str)
              .ilike("semester", _sem_str)
              .limit(1).execute())
        # OCR can change the code while preserving the course name. Reuse the
        # subject when its name and academic context still match.
        if not sr.data:
            sr = (sb.table("subject").select("subject_id")
                  .ilike("subject_name", subject_name)
                  .ilike("branch", _branch_str)
                  .ilike("semester", _sem_str)
                  .limit(1).execute())
    else:
        sr = (sb.table("subject").select("subject_id")
              .ilike("subject_name", subject_name)
              .ilike("branch", _branch_str)
              .ilike("semester", _sem_str)
              .limit(1).execute())
    if sr.data:
        subject_id = sr.data[0]["subject_id"]
        # Always write all metadata — no conditional guards that silently skip values
        update_fields: dict = {
            "subject_name": subject_name,   # normalise casing in case it drifted
        }
        if subject_code:
            update_fields["subject_code"] = subject_code
        if _sem_str:
            update_fields["semester"] = _sem_str
        if _branch_str:
            update_fields["branch"] = _branch_str
        sb.table("subject").update(update_fields).eq("subject_id", subject_id).execute()
        print(f"[DB] subject updated: id={subject_id} name='{subject_name}' sem='{_sem_str}' branch='{_branch_str}' code='{subject_code}'")
    else:
        ins = sb.table("subject").insert({
            "subject_name": subject_name,
            "subject_code": subject_code,
            "semester"    : _sem_str,
            "branch"      : _branch_str,
        }).execute()
        subject_id = ins.data[0]["subject_id"]
        print(f"[DB] subject inserted: id={subject_id} name='{subject_name}' sem='{_sem_str}' branch='{_branch_str}' code='{subject_code}'")

    # unit / topic are now resolved per-question (cached to minimise DB round trips)
    _unit_cache: Dict  = {}
    _topic_cache: Dict = {}
    _bank_cache: Dict  = {}

    question_bank_id = _get_or_create_question_bank(sb, subject_id, subject_name, _bank_cache)

    # created_by — use first available user, or create a system user
    cr = sb.table("User").select("user_id").limit(1).execute()
    if cr.data:
        created_by = cr.data[0]["user_id"]
    else:
        nr = sb.table("User").insert({"name": "System", "role": "admin"}).execute()
        created_by = nr.data[0]["user_id"]
    # ----------------------------------------

    # Count will be tracked accurately during the loop (blanks are skipped)
    saved_q = 0

    meta.update({
        "filename"       : filename,
        "branch"         : branch,
        "semester"       : semester,
        "subject"        : subject_name,
        "subject_code"   : subject_code,
        "course_name"    : meta.get("course_name") or subject_name,
        "course_code"    : meta.get("course_code") or subject_code,
    })

    paper_row = {
        "subject_id": subject_id,
        "exam_type" : meta.get("exam_type", "University"),
        "exam_year" : int(meta.get("year", datetime.now().year)),
        "exam_date" : meta.get("exam_date", datetime.now().strftime("%Y-%m-%d")),
        "raw_json"  : meta,
    }

    # ------------------------------------------------------------------
    # Paper-level dedup: if this exact filename was already processed,
    # return the existing paper_id without re-inserting anything.
    # ------------------------------------------------------------------
    existing_paper = (
        sb.table("questionpaper")
        .select("paper_id")
        .eq("subject_id", subject_id)
        .eq("exam_type", paper_row["exam_type"])
        .eq("exam_year", paper_row["exam_year"])
        .execute()
    )
    # Match by filename stored inside raw_json
    pid = None
    for row in (existing_paper.data or []):
        candidate_pid = row["paper_id"]
        # Fetch raw_json of this candidate to check filename
        detail = sb.table("questionpaper").select("raw_json").eq("paper_id", candidate_pid).limit(1).execute()
        if detail.data and detail.data[0].get("raw_json", {}).get("filename") == filename:
            pid = candidate_pid
            break

    if pid is not None:
        print(f"[DB] Paper '{filename}' already in DB (paper_id={pid}), replacing reviewed questions.")
        sb.table("questionpapermapping").delete().eq("paper_id", pid).execute()
        sb.table("questionpaper").update({
            "subject_id": subject_id,
            "exam_type": paper_row["exam_type"],
            "exam_year": paper_row["exam_year"],
            "exam_date": paper_row["exam_date"],
            "raw_json": paper_row["raw_json"],
        }).eq("paper_id", pid).execute()
    else:
        pr  = sb.table("questionpaper").insert(paper_row).execute()
        pid = pr.data[0]["paper_id"]

    # ------------------------------------------------------------------
    # Ensure questions are numbered sequentially per paper starting at 1.
    # This enforces a deterministic `question_number` for DB consumers.
    # Skip blank question texts when assigning numbers so numbering matches
    # the persisted (non-empty) questions order.
    # ------------------------------------------------------------------
    for paper in papers_data:
        seq = 1
        for question in paper.get("questions", []):
            txt = " ".join((question.get("question_text") or "").split()).strip()
            if not txt:
                # preserve existing empty/placeholder numbers but do not increment
                continue
            # store as string to match DB column semantics
            question["question_number"] = str(seq)
            seq += 1

    # ------------------------------------------------------------------
    # Pre-pass: collect all non-blank question texts, perform fast local
    # cleanup and (optionally) a small batched grammar correction call
    # before the insert loop. Classification (R/U/A) is performed on the
    # cleaned texts so downstream metadata is consistent.
    # ------------------------------------------------------------------
    _orig_texts: List[str] = []
    _cleaned_texts: List[str] = []
    for paper in papers_data:
        for question in paper.get("questions", []):
            t = " ".join((question.get("question_text") or "").split()).strip()
            if not t:
                continue
            cleaned = _basic_cleanup_text(t)
            if cleaned:
                _orig_texts.append(t)
                _cleaned_texts.append(cleaned)

    # Conservative remote grammar correction: use whichever configured API key is
    # present. This enables Grok/xAI correction when OpenAI is not configured.
    grammar_api_key, grammar_provider = _pick_grammar_api_key()
    if grammar_api_key and _cleaned_texts:
        flagged_indices = [i for i, txt in enumerate(_cleaned_texts) if _needs_remote_correction(txt)]
        fallback_indices = []
        if not flagged_indices:
            # Some valid OCR mistakes do not trigger the heuristic, especially on
            # slightly noisy but otherwise normal-looking question lines.
            fallback_indices = [
                i for i, txt in enumerate(_cleaned_texts)
                if len(txt) >= 24 and len(txt.split()) >= 5
            ][:GRAMMAR_BATCH_LIMIT]

        if flagged_indices or fallback_indices:
            to_send = [
                _cleaned_texts[i]
                for i in (flagged_indices + fallback_indices)[:GRAMMAR_BATCH_LIMIT]
            ]
            unique_send = []
            seen = set()
            for text in to_send:
                key = text.lower().strip()
                if key and key not in seen:
                    unique_send.append(text)
                    seen.add(key)

            if unique_send:
                if grammar_provider == "grok":
                    corrected = _correct_texts_with_grok(unique_send, grammar_api_key)
                elif grammar_provider == "groq":
                    corrected = _correct_texts_with_groq(unique_send, grammar_api_key)
                else:
                    corrected = _correct_texts_with_openai(unique_send, grammar_api_key)

                target_indices = (flagged_indices + fallback_indices)[:min(len(unique_send), len(corrected))]
                for dst_idx, new_text in zip(target_indices, corrected[:len(target_indices)]):
                    _cleaned_texts[dst_idx] = new_text
                print(f"[GRAMMAR] Corrected {len(target_indices)} questions via {grammar_provider.upper()} API.")

    # Map originals -> cleaned (post-correction) so we can look up per-question later
    _orig_to_cleaned: Dict[str, str] = dict(zip(_orig_texts, _cleaned_texts))

    _rua_labels = classify_rua_batch(_cleaned_texts)
    _rua_map: Dict[str, str] = dict(zip(_cleaned_texts, _rua_labels))
    print(f"[DB] Groq RUA classification done for {len(_cleaned_texts)} questions (post-cleanup).")
    # ------------------------------------------------------------------

    for paper in papers_data:
        for question in paper.get("questions", []):
            # Normalize marks to integer (coerce strings like '4', '[4]', 'Marks:4')
            raw_marks = question.get("marks", 0)
            marks = 0
            try:
                marks = int(raw_marks)
            except Exception:
                m = re.search(r"(\d{1,2})", str(raw_marks or ""))
                if m:
                    marks = int(m.group(1))
                else:
                    # fallback to 0 (will be classified as Easy/Medium/Hard accordingly)
                    marks = 0
            bloom = question.get("bloom_level") or auto_assign_bloom_level(question)
            diff  = "Easy" if marks <= 3 else "Medium" if marks <= 6 else "Hard"
            qt    = question.get("question_text", "").lower()
            if any(w in qt for w in ["explain","describe","discuss"]):   qtype = "Long Answer"
            elif any(w in qt for w in ["solve","calculate","design","write"]): qtype = "Problem Solving"
            else: qtype = "Short Answer"

            # Pack all extra metadata into question_hash as JSON
            chapter_name = question.get("chapter", "General").strip() or "General"
            topic_text   = question.get("topic",   "General").strip() or "General"

            # Prefer the CO parsed from the question text. Only infer from the
            # chapter/unit when extraction did not produce a usable label.
            parsed_co = str(question.get("course_outcome") or question.get("co") or "").strip().upper()
            co_match = re.fullmatch(r"CO\s*([1-5])", parsed_co)
            co = f"CO{co_match.group(1)}" if co_match else _co_from_chapter(chapter_name, "")
            if not co:
                co = ""

            # Resolve per-question unit (cached per paper upload)
            unit_name = _unit_name_from_co(co, chapter_name)
            q_unit_id  = _get_or_create_unit(sb, subject_id, unit_name, _unit_cache)

            extra_meta = {
                "question_number": question.get("question_number", ""),
                "course_outcome" : co,
                "bloom_level"    : bloom,
                "chapter"        : chapter_name,
                "topic_text"     : topic_text,
                "answer"         : question.get("answer", ""),
                "sub_label"      : question.get("sub_label", ""),
                "sub_questions"  : question.get("sub_questions", []),
                "has_diagram"    : question.get("has_diagram", False),
                "has_math"       : question.get("has_math", False),
                "identified_numbers": question.get("identified_numbers", []),
                "question_bank_id": question_bank_id,
                "images"         : question.get("images", []),
                # Subject / branch / semester stored per-question for easy retrieval
                "subject"        : subject_name,
                "subject_code"   : subject_code,
                "branch"         : branch,
                "semester"       : semester,
            }

            # Normalize question text: strip whitespace, collapse internal spaces
            raw_text  = question.get("question_text", "")
            norm_text = " ".join(raw_text.split()).strip()

            # Skip blank questions entirely
            if not norm_text:
                continue

            # Use the cleaned (and possibly externally corrected) text when available
            cleaned_text = _orig_to_cleaned.get(norm_text) if '_orig_to_cleaned' in locals() else None
            # safe fallback: use basic cleanup
            if cleaned_text is None:
                cleaned_text = _basic_cleanup_text(norm_text)

            # Skip obvious headers/footers/noise
            if _is_likely_heading(cleaned_text):
                continue

            # Look up the Groq-classified RUA label (falls back to 'U' if missing)
            rua_label = _rua_map.get(cleaned_text, _keyword_rua(cleaned_text))

            # Stable content fingerprint — same question from different OCR runs
            # will always produce the same hash (lowercase + no punctuation + SHA-256)
            c_hash = _content_hash(cleaned_text)

            # Encode question-intrinsic metadata as JSON stored in question_hash.
            # IMPORTANT: do NOT include paper-varying fields (branch/semester/subject)
            # here — those live in the paper's raw_json.  Including them would make
            # two uploads of the same question produce different JSON strings and
            # break the unique-constraint-based dedup.
            #
            # Layout: {"_h":"<sha256>", "question_number":…, "bloom_level":…, …}
            # The "_h" key embeds the content hash so the dedup ilike query can
            # find it, while the full JSON payload preserves all extra fields.
            stable_meta = {
                "_h"             : c_hash,
                "question_number": extra_meta.get("question_number", ""),
                "bloom_level"    : extra_meta.get("bloom_level", ""),
                "course_outcome" : extra_meta.get("course_outcome", ""),
                "chapter"        : extra_meta.get("chapter", ""),
                "topic_text"     : extra_meta.get("topic_text", ""),
                "answer"         : extra_meta.get("answer", ""),
                "sub_label"      : extra_meta.get("sub_label", ""),
                "sub_questions"  : extra_meta.get("sub_questions", []),
                "has_diagram"    : extra_meta.get("has_diagram", False),
                "has_math"       : extra_meta.get("has_math", False),
                "identified_numbers": extra_meta.get("identified_numbers", []),
                "question_bank_id": extra_meta.get("question_bank_id", question_bank_id),
                "images"         : extra_meta.get("images", []),
            }
            question_hash_value = json.dumps(stable_meta, ensure_ascii=False)

            q_row = {
                "question_text"   : cleaned_text,
                "marks"           : marks,
                "difficulty_level": diff,
                "question_type"   : qtype,
                "source_type"     : "OCR Extracted",
                "status"          : "active",
                "rua"             : rua_label,
                "subject_id"      : subject_id,
                "unit_id"         : q_unit_id,
                "course_outcome"  : co or "",
                "bloom_level"     : bloom,
                "question_number" : extra_meta.get("question_number", ""),
                "sub_label"       : extra_meta.get("sub_label", ""),
                "sub_questions"   : extra_meta.get("sub_questions", []),
                "has_diagram"     : extra_meta.get("has_diagram", False),
                "has_math"        : extra_meta.get("has_math", False),
                "images"          : extra_meta.get("images", []),
                "answer"          : extra_meta.get("answer", ""),
                "chapter"         : chapter_name,
                "created_by"      : created_by,
                "question_hash"   : question_hash_value,
            }

            if question_bank_id is not None:
                q_row["question_bank_id"] = question_bank_id

            # Smart dedup: attempt multiple lookup strategies to avoid inserting
            # duplicate questions. We prefer matching the embedded JSON _h key,
            # but also handle old-style bare-hash rows and finally fall back to
            # a content-based local hash comparison of likely candidates.
            qid = None

            # 1) JSON _h with typical spacing
            existing = sb.table("question").select("question_id") \
                .ilike("question_hash", f'%"_h": "{c_hash}"%').limit(1).execute()
            # 2) JSON _h without space after colon
            if not (existing.data):
                existing = sb.table("question").select("question_id") \
                    .ilike("question_hash", f'%"_h":"{c_hash}"%').limit(1).execute()
            # 3) Old-style bare-hash rows
            if not (existing.data):
                existing = sb.table("question").select("question_id") \
                    .eq("question_hash", c_hash).limit(1).execute()

            if existing.data:
                qid = existing.data[0]["question_id"]
            else:
                # 4) Candidate scan by a short snippet of the cleaned text. Fetch a
                # handful of potential matches and compare their canonical hashes
                # locally to avoid false negatives due to JSON formatting differences.
                snippet = cleaned_text[:120]
                try:
                    candidates = sb.table("question").select("question_id, question_text, question_hash") \
                        .ilike("question_text", f"%{snippet}%").limit(5).execute()
                except Exception:
                    candidates = None

                if candidates and candidates.data:
                    for cand in candidates.data:
                        cand_text = cand.get("question_text", "")
                        if cand_text and _content_hash(cand_text) == c_hash:
                            qid = cand["question_id"]
                            break

                # If still not found, insert and handle race conditions gracefully
                if qid is None:
                    try:
                        qr  = sb.table("question").insert(q_row).execute()
                        qid = qr.data[0]["question_id"]
                    except Exception as dup:
                        # Unique-violation or other race: attempt the same lookups again
                        if "23505" in str(dup) or "unique" in str(dup).lower():
                            fallback = sb.table("question").select("question_id") \
                                .ilike("question_hash", f'%"_h": "{c_hash}"%').limit(1).execute()
                            if not fallback.data:
                                fallback = sb.table("question").select("question_id") \
                                    .ilike("question_hash", f'%"_h":"{c_hash}"%').limit(1).execute()
                            if not fallback.data:
                                fallback = sb.table("question").select("question_id") \
                                    .eq("question_hash", c_hash).limit(1).execute()
                            if not fallback.data and candidates and candidates.data:
                                for cand in candidates.data:
                                    if _content_hash(cand.get("question_text", "")) == c_hash:
                                        fallback = {"data": [{"question_id": cand["question_id"]}]}
                                        break
                            if fallback and fallback.data:
                                qid = fallback.data[0]["question_id"]
                            else:
                                raise
                        else:
                            raise

            # add to mapping — pre-check so the same (paper, question) pair is never inserted twice
            map_exists = (
                sb.table("questionpapermapping")
                .select("mapping_id")
                .eq("paper_id", pid)
                .eq("question_id", qid)
                .limit(1)
                .execute()
            )
            if not map_exists.data:
                try:
                    sb.table("questionpapermapping").insert({"paper_id": pid, "question_id": qid}).execute()
                except Exception:
                    pass  # race-condition guard

            saved_q += 1

    print(f"[DB] Saved {saved_q} questions for paper_id={pid}")
    # Keep the count in raw_json because deployed schemas may not include the
    # optional total_questions column.
    paper_meta = dict(paper_row["raw_json"])
    paper_meta["total_questions"] = saved_q
    sb.table("questionpaper").update({"raw_json": paper_meta}).eq("paper_id", pid).execute()
    return pid

# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------
def get_all_questions(branch=None, semester=None, subject=None, limit=100, offset=0):
    try:
        sb = get_supabase_client()
        mq = sb.table("questionpapermapping").select(
            "question_id, questionpaper!fk_mapping_paper!inner(paper_id, created_at, raw_json, exam_year, exam_type)"
        )
        if branch or semester:
            # filter later in Python since raw_json isn't queryable by column
            pass
        mq = mq.range(offset, offset + limit - 1)
        mr = mq.execute()
        if not mr.data:
            return []

        paper_by_qid = {m["question_id"]: m.get("questionpaper", {}) for m in mr.data}
        q_ids = list(paper_by_qid.keys())
        qr    = sb.table("question").select("*").in_("question_id", q_ids).execute()

        results = []
        for row in qr.data:
            pi  = paper_by_qid.get(row["question_id"], {})
            pj  = pi.get("raw_json") or {}
            if branch   and pj.get("branch",   "").lower().strip() != branch.lower().strip():   continue
            if semester and _norm_sem(pj.get("semester")) != _norm_sem(semester):                continue
            if subject  and pj.get("subject",  "").lower() != subject.lower():  continue
            results.append(_row_to_question(row, pi))
        return results
    except Exception as e:
        print(f"[DB] get_all_questions error: {e}")
        return []

def search_questions(search_term, branch=None, semester=None, subject=None, limit=50):
    try:
        sb = get_supabase_client()
        qr = sb.table("question").select("*").ilike("question_text", f"%{search_term}%").limit(limit).execute()
        if not qr.data:
            return []

        q_ids = [r["question_id"] for r in qr.data]
        mr    = sb.table("questionpapermapping").select(
            "question_id, questionpaper!fk_mapping_paper(paper_id, created_at, raw_json)"
        ).in_("question_id", q_ids).execute()

        paper_by_qid = {m["question_id"]: m.get("questionpaper") or {} for m in mr.data}

        results = []
        for row in qr.data:
            pi  = paper_by_qid.get(row["question_id"], {})
            pj  = pi.get("raw_json") or {}
            if branch   and pj.get("branch",   "").lower().strip() != branch.lower().strip():   continue
            if semester and _norm_sem(pj.get("semester")) != _norm_sem(semester):                continue
            if subject  and pj.get("subject",  "").lower() != subject.lower():  continue
            results.append(_row_to_question(row, pi))
        return results
    except Exception as e:
        print(f"[DB] search_questions error: {e}")
        return []

def get_paper_by_id(paper_id: int):
    try:
        sb  = get_supabase_client()
        pr  = sb.table("questionpaper").select("*").eq("paper_id", paper_id).execute()
        if not pr.data:
            return None

        paper_row = pr.data[0]
        pj        = paper_row.get("raw_json") or {}

        mr    = sb.table("questionpapermapping").select("question_id").eq("paper_id", paper_id).execute()
        q_ids = [m["question_id"] for m in mr.data]

        questions = []
        if q_ids:
            qr = sb.table("question").select("*").in_("question_id", q_ids).execute()
            for row in qr.data:
                questions.append(_row_to_question(row, paper_row))

        return {
            "id"             : paper_row["paper_id"],
            "paper_id"       : paper_row["paper_id"],
            "filename"       : pj.get("filename", ""),
            "upload_date"    : paper_row.get("created_at"),
            "branch"         : pj.get("branch", ""),
            "semester"       : pj.get("semester", ""),
            "subject"        : pj.get("subject", ""),
            "exam_info"      : pj,
            "total_questions": pj.get("total_questions", len(questions)),
            "questions"      : questions,
        }
    except Exception as e:
        print(f"[DB] get_paper_by_id error: {e}")
        return None

def get_all_uploaded_papers(limit: int = 100, offset: int = 0) -> List[Dict]:
    """
    Get all uploaded question papers from the database with pagination.
    Returns a list of papers with basic info (without full question details).
    """
    try:
        sb = get_supabase_client()
        result = (
            sb.table("questionpaper")
            .select("paper_id, exam_type, exam_year, exam_date, created_at, raw_json")
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        
        papers = []
        for row in result.data:
            pj = row.get("raw_json") or {}
            # Count questions for this paper
            qm = sb.table("questionpapermapping").select("question_id").eq("paper_id", row["paper_id"]).execute()
            questions_count = len(qm.data) if qm.data else 0
            
            papers.append({
                "paper_id": row["paper_id"],
                "filename": pj.get("filename", ""),
                "subject": pj.get("subject", "Unknown"),
                "subject_code": pj.get("subject_code", ""),
                "branch": pj.get("branch", ""),
                "semester": pj.get("semester", ""),
                "exam_type": row.get("exam_type", ""),
                "exam_year": row.get("exam_year"),
                "exam_date": row.get("exam_date"),
                "upload_date": row.get("created_at"),
                "total_questions": questions_count,
            })
        
        return papers
    except Exception as e:
        print(f"[DB] get_all_uploaded_papers error: {e}")
        return []

def save_curriculum(curriculum: Dict) -> Dict:
    """
    Persist extracted curriculum into subject → unit → topic tables.

    Parameters
    ----------
    curriculum : dict  – output of a curriculum extraction pipeline

    Returns
    -------
    dict with keys: subject_id, units_saved, topics_saved, subject_name, subject_code
    """
    try:
        # Input validation
        if not isinstance(curriculum, dict):
            raise TypeError(f"curriculum must be dict, got {type(curriculum).__name__}")
        if "units" not in curriculum or not isinstance(curriculum.get("units"), list):
            print("[DB] WARNING: curriculum has no 'units' key or units is not a list")
            curriculum["units"] = []
        
        sb = get_supabase_client()

        subject_name = (curriculum.get("subject_name") or "Unknown Subject").strip()
        subject_code = (curriculum.get("subject_code") or "").strip().casefold()
        branch       = (curriculum.get("branch") or "").strip().casefold()
        semester_raw = curriculum.get("semester")
        semester_str = _norm_sem(semester_raw).strip().casefold() if semester_raw else ""

        # ── Upsert subject ──────────────────────────────────────────────────────
        subject_query = sb.table("subject").select("subject_id")
        if subject_code:
            subject_query = subject_query.ilike("subject_code", subject_code)
        else:
            subject_query = subject_query.ilike("subject_name", subject_name)
        if branch:
            subject_query = subject_query.ilike("branch", branch)
        if semester_str:
            subject_query = subject_query.ilike("semester", semester_str)
        sr = subject_query.limit(1).execute()
        if sr.data:
            subject_id = sr.data[0]["subject_id"]
            update_fields: Dict = {"subject_name": subject_name}
            if subject_code:
                update_fields["subject_code"] = subject_code
            if semester_str:
                update_fields["semester"] = semester_str
            if branch:
                update_fields["branch"] = branch
            sb.table("subject").update(update_fields).eq("subject_id", subject_id).execute()
            print(f"[DB] curriculum: subject updated id={subject_id} name='{subject_name}'")
        else:
            ins = sb.table("subject").insert({
                "subject_name": subject_name,
                "subject_code": subject_code,
                "semester": semester_str,
                "branch": branch,
            }).execute()
            subject_id = ins.data[0]["subject_id"]
            print(f"[DB] curriculum: subject inserted id={subject_id} name='{subject_name}'")

        units_saved  = 0
        topics_saved = 0

        def _clean_name(value) -> str:
            if value is None:
                return ""
            return str(value).strip().rstrip(".")

        def _topic_label(topic_data) -> str:
            if isinstance(topic_data, dict):
                return _clean_name(topic_data.get("topic_name") or topic_data.get("name"))
            return _clean_name(topic_data)

        def _topic_children(topic_data) -> list:
            if isinstance(topic_data, dict):
                children = topic_data.get("subtopics") or topic_data.get("topics") or []
                return children if isinstance(children, list) else []
            return []

        _topic_has_parent_link = None

        def _supports_parent_topic_id() -> bool:
            nonlocal _topic_has_parent_link
            if _topic_has_parent_link is not None:
                return _topic_has_parent_link
            try:
                sb.table("topic").select("topic_id, parent_topic_id").limit(1).execute()
                _topic_has_parent_link = True
            except Exception as e:
                if 'parent_topic_id' in str(e):
                    _topic_has_parent_link = False
                else:
                    raise
            return _topic_has_parent_link

        _unit_rua_json_supported = None

        def _supports_unit_rua_json() -> bool:
            nonlocal _unit_rua_json_supported
            if _unit_rua_json_supported is not None:
                return _unit_rua_json_supported
            try:
                sb.table("unit").select("unit_id, rua_json").limit(1).execute()
                _unit_rua_json_supported = True
            except Exception as e:
                if 'rua_json' in str(e):
                    _unit_rua_json_supported = False
                else:
                    raise
            return _unit_rua_json_supported

        def _unit_rua_payload(unit_data, resolved_unit_name: str) -> dict:
            existing = unit_data.get("rua_markings") if isinstance(unit_data, dict) else None
            if isinstance(existing, dict) and existing:
                existing = dict(existing)
                existing["unit_name"] = resolved_unit_name
                return existing

            topic_markings = []
            for topic in (unit_data.get("topics") or []) if isinstance(unit_data, dict) else []:
                if not isinstance(topic, dict):
                    continue
                topic_name = _clean_name(topic.get("topic_name") or topic.get("name"))
                rua_mapping = topic.get("rua_mapping")
                if not topic_name or not isinstance(rua_mapping, dict):
                    continue
                topic_markings.append({
                    "topic_name": topic_name,
                    "rua_mapping": rua_mapping,
                })

            return {
                "unit_name": resolved_unit_name,
                "topics": topic_markings,
            }

        def _find_topic_id(unit_id: int, topic_name: str, parent_topic_id: Optional[int] = None) -> Optional[int]:
            query = (
                sb.table("topic")
                .select("topic_id")
                .eq("unit_id", unit_id)
                .ilike("topic_name", topic_name)
            )
            if _supports_parent_topic_id():
                if parent_topic_id is None:
                    query = query.is_("parent_topic_id", None)
                else:
                    query = query.eq("parent_topic_id", parent_topic_id)
            result = query.limit(1).execute()
            return result.data[0]["topic_id"] if result.data else None

        def _insert_topic(unit_id: int, topic_name: str, parent_topic_id: Optional[int] = None) -> int:
            payload = {
                "topic_name": topic_name,
                "unit_id": unit_id,
            }
            if _supports_parent_topic_id() and parent_topic_id is not None:
                payload["parent_topic_id"] = parent_topic_id
            result = sb.table("topic").insert(payload).execute()
            return result.data[0]["topic_id"]

        def _save_topic_tree(unit_id: int, topic_data, parent_topic_id: Optional[int] = None) -> None:
            nonlocal topics_saved

            topic_name = _topic_label(topic_data)
            if not topic_name:
                return

            parent_links_supported = _supports_parent_topic_id()
            effective_parent_id = parent_topic_id if parent_links_supported else None
            topic_id = _find_topic_id(unit_id, topic_name, effective_parent_id)
            if topic_id is None:
                topic_id = _insert_topic(unit_id, topic_name, effective_parent_id)
                topics_saved += 1

            for child in _topic_children(topic_data):
                child_name = _topic_label(child)
                if not child_name or child_name.lower() == topic_name.lower():
                    continue
                if parent_links_supported:
                    _save_topic_tree(unit_id, child, topic_id)
                else:
                    # Parent links not supported in DB: store subtopics as
                    # distinct path-labeled topic rows so they are not lost or
                    # collapsed across different parent topics.
                    child_path_name = f"{topic_name} > {child_name}"
                    existing_child_id = _find_topic_id(unit_id, child_path_name, None)
                    if existing_child_id is None:
                        _insert_topic(unit_id, child_path_name, None)
                        topics_saved += 1

        for unit_idx, unit in enumerate(curriculum.get("units") or [], start=1):
            # Generate unit name: prioritize provided name, else use unit_number, else use index
            unit_name = (unit.get("unit_name") or "").strip()
            unit_number = unit.get("unit_number")
            
            if not unit_name:
                # Generate a default name if none provided
                # Check if unit_number is not None (handles 0 as valid unit number)
                if unit_number is not None:
                    unit_name = f"Unit {unit_number}"
                else:
                    unit_name = f"Unit {unit_idx}"
            
            # Handle edge case where unit_name is just "Unit" (no number) - use index
            elif unit_name.lower() == "unit":
                unit_name = f"Unit {unit_idx}"

            unit_rua_json = _unit_rua_payload(unit, unit_name)

            # ── Upsert unit ─────────────────────────────────────────────────────
            ur = (
                sb.table("unit")
                .select("unit_id")
                .eq("subject_id", subject_id)
                .ilike("unit_name", unit_name)
                .limit(1)
                .execute()
            )
            if ur.data:
                unit_id = ur.data[0]["unit_id"]
                print(f"[DB] curriculum: unit found id={unit_id} name='{unit_name}'")
                update_payload = {"unit_name": unit_name}
                if _supports_unit_rua_json():
                    update_payload["rua_json"] = unit_rua_json
                sb.table("unit").update(update_payload).eq("unit_id", unit_id).execute()
            else:
                insert_payload = {
                    "unit_name" : unit_name,
                    "subject_id": subject_id,
                }
                if _supports_unit_rua_json():
                    insert_payload["rua_json"] = unit_rua_json
                ui = sb.table("unit").insert(insert_payload).execute()
                unit_id = ui.data[0]["unit_id"]
                units_saved += 1
                print(f"[DB] curriculum: unit inserted id={unit_id} name='{unit_name}'")

            # ── Upsert topics + subtopics ────────────────────────────────────────
            for topic in (unit.get("topics") or []):
                _save_topic_tree(unit_id, topic)

        subtopics_total = sum(
            len(t.get("subtopics") or [])
            for unit in (curriculum.get("units") or [])
            for t in (unit.get("topics") or [])
        )
        print(
            f"[DB] curriculum saved: subject_id={subject_id} "
            f"units={units_saved} topics(incl subtopics)={topics_saved} "
            f"subtopics_in_json={subtopics_total}"
        )
        return {
            "subject_id"       : subject_id,
            "subject_name"     : subject_name,
            "subject_code"     : subject_code,
            "units_saved"      : units_saved,
            "topics_saved"     : topics_saved,
            "subtopics_in_json": subtopics_total,
        }
    except Exception as e:
        print(f"[DB] ERROR in save_curriculum: {type(e).__name__}: {str(e)}")
        print(f"[DB] curriculum keys: {list(curriculum.keys()) if isinstance(curriculum, dict) else 'NOT A DICT'}")
        raise


def get_stats() -> Dict:
    try:
        sb = get_supabase_client()
        pr = sb.table("questionpaper").select("paper_id", count="exact").execute()
        qr = sb.table("question").select("question_id", count="exact").execute()
        br = sb.table("questionpaper").select("raw_json").execute()

        papers_by_branch  = {}
        semester_counts   = {}
        for row in br.data:
            pj = row.get("raw_json") or {}
            b  = pj.get("branch", "Unknown")
            s  = pj.get("semester", "Unknown")
            papers_by_branch[b] = papers_by_branch.get(b, 0) + 1
            k  = f"{b}_{s}"
            semester_counts[k]  = semester_counts.get(k, 0) + 1

        return {
            "total_papers"      : pr.count or 0,
            "total_questions"   : qr.count or 0,
            "papers_by_branch"  : papers_by_branch,
            "papers_by_semester": [
                {"branch": k.split("_")[0], "semester": k.split("_")[1], "count": v}
                for k, v in semester_counts.items()
            ],
        }
    except Exception as e:
        print(f"[DB] get_stats error: {e}")
        raise
