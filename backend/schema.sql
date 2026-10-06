-- ============================================================
-- EduQuest.ai – Supabase Schema
-- Run this entire script in the Supabase SQL Editor
-- ============================================================

-- ── 1. User ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "User" (
    user_id   BIGSERIAL PRIMARY KEY,
    name      TEXT      NOT NULL,
    role      TEXT      NOT NULL DEFAULT 'teacher',   -- 'admin' | 'teacher' | 'student'
    email     TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── 2. subject ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS subject (
    subject_id   BIGSERIAL PRIMARY KEY,
    subject_name TEXT NOT NULL,
    subject_code TEXT,
    semester     TEXT,
    branch       TEXT,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_subject_code_context
    ON subject(subject_code, branch, semester)
    WHERE subject_code IS NOT NULL AND subject_code <> '';

CREATE UNIQUE INDEX IF NOT EXISTS uq_subject_name_context
    ON subject(subject_name, branch, semester)
    WHERE subject_code IS NULL OR subject_code = '';

-- ── 3. unit  (chapter inside a subject) ──────────────────────
CREATE TABLE IF NOT EXISTS unit (
    unit_id    BIGSERIAL PRIMARY KEY,
    unit_name  TEXT    NOT NULL,
    subject_id BIGINT  NOT NULL REFERENCES subject(subject_id) ON DELETE CASCADE,
    rua_json   JSONB   DEFAULT '{}'::jsonb,
    UNIQUE (subject_id, unit_name)
);

-- ── 4. topic (topic inside a unit, with optional parent topic) ───────────
CREATE TABLE IF NOT EXISTS topic (
    topic_id   BIGSERIAL PRIMARY KEY,
    topic_name TEXT   NOT NULL,
    unit_id    BIGINT NOT NULL REFERENCES unit(unit_id) ON DELETE CASCADE,
    parent_topic_id BIGINT REFERENCES topic(topic_id) ON DELETE SET NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_topic_root
    ON topic(unit_id, topic_name)
    WHERE parent_topic_id IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_topic_child
    ON topic(unit_id, parent_topic_id, topic_name)
    WHERE parent_topic_id IS NOT NULL;

-- ── 5. question_bank (one bank per subject) ───────────────────
CREATE TABLE IF NOT EXISTS question_bank (
    question_bank_id BIGSERIAL PRIMARY KEY,
    subject_id       BIGINT NOT NULL UNIQUE REFERENCES subject(subject_id) ON DELETE CASCADE,
    bank_name        TEXT   NOT NULL,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- ── 6. question ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS question (
    -- identity
    question_id      BIGSERIAL PRIMARY KEY,

    -- core content (what the user asked for)
    question_text    TEXT    NOT NULL,
    question_type    TEXT    NOT NULL DEFAULT 'Short Answer',
                     -- 'Short Answer' | 'Long Answer' | 'Problem Solving' | 'Comparative' | 'Diagram'
    difficulty_level TEXT    NOT NULL DEFAULT 'Medium',
                     -- 'Easy' | 'Medium' | 'Hard'
    subject_id       BIGINT  NOT NULL REFERENCES subject(subject_id) ON DELETE CASCADE,
    question_bank_id BIGINT  REFERENCES question_bank(question_bank_id) ON DELETE SET NULL,
    topic_id         BIGINT  REFERENCES topic(topic_id) ON DELETE SET NULL,
    marks            INTEGER NOT NULL DEFAULT 5,

    -- additional necessary columns used by database.py
    unit_id          BIGINT  REFERENCES unit(unit_id) ON DELETE SET NULL,
    course_outcome   TEXT,                              -- CO1 – CO6
    bloom_level      TEXT    DEFAULT 'Understand',      -- Remember/Understand/Apply/Analyze/Evaluate/Create
    rua              TEXT    DEFAULT 'U',               -- R | U | A (Remember-Understand-Apply)
    question_number  TEXT,                              -- e.g. "Q1a", "2(b)"
    sub_label        TEXT,                              -- e.g. "a)", "i)"
    sub_questions    JSONB   DEFAULT '[]',              -- nested sub-question objects
    has_diagram      BOOLEAN DEFAULT FALSE,
    has_math         BOOLEAN DEFAULT FALSE,
    images           JSONB   DEFAULT '[]',
    answer           TEXT,
    chapter          TEXT,
    source_type      TEXT    DEFAULT 'OCR Extracted',   -- 'OCR Extracted' | 'Manual'
    status           TEXT    DEFAULT 'active',          -- 'active' | 'archived'
    created_by       BIGINT  REFERENCES "User"(user_id) ON DELETE SET NULL,
    question_hash    TEXT    UNIQUE,                    -- SHA-256 fingerprint for deduplication

    created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- ── 7. questionpaper ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS questionpaper (
    paper_id    BIGSERIAL PRIMARY KEY,
    subject_id  BIGINT NOT NULL REFERENCES subject(subject_id) ON DELETE CASCADE,
    exam_type   TEXT   NOT NULL DEFAULT 'University',  -- 'University' | 'Internal' | 'Mock'
    exam_year   INTEGER,
    exam_date   DATE,
    raw_json    JSONB  DEFAULT '{}',   -- stores filename, branch, semester, subject_code, etc.
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ── 8. questionpapermapping (paper ↔ question, many-to-many) ─
CREATE TABLE IF NOT EXISTS questionpapermapping (
    mapping_id  BIGSERIAL PRIMARY KEY,
    paper_id    BIGINT NOT NULL REFERENCES questionpaper(paper_id) ON DELETE CASCADE,
    question_id BIGINT NOT NULL REFERENCES question(question_id) ON DELETE CASCADE,
    UNIQUE (paper_id, question_id)
);

-- ── Indexes ───────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_question_subject    ON question(subject_id);
CREATE INDEX IF NOT EXISTS idx_question_bank       ON question(question_bank_id);
CREATE INDEX IF NOT EXISTS idx_question_topic      ON question(topic_id);
CREATE INDEX IF NOT EXISTS idx_question_bloom      ON question(bloom_level);
CREATE INDEX IF NOT EXISTS idx_question_difficulty ON question(difficulty_level);
CREATE INDEX IF NOT EXISTS idx_question_hash       ON question(question_hash);
CREATE INDEX IF NOT EXISTS idx_qpm_paper           ON questionpapermapping(paper_id);
CREATE INDEX IF NOT EXISTS idx_qpm_question        ON questionpapermapping(question_id);
CREATE INDEX IF NOT EXISTS idx_qp_subject          ON questionpaper(subject_id);
CREATE INDEX IF NOT EXISTS idx_qbank_subject       ON question_bank(subject_id);
CREATE INDEX IF NOT EXISTS idx_unit_subject        ON unit(subject_id);
CREATE INDEX IF NOT EXISTS idx_topic_unit          ON topic(unit_id);

-- Full-text search on question text
CREATE INDEX IF NOT EXISTS idx_question_fts
    ON question USING gin(to_tsvector('english', question_text));

-- ── Row Level Security ────────────────────────────────────────
ALTER TABLE "User"               ENABLE ROW LEVEL SECURITY;
ALTER TABLE subject               ENABLE ROW LEVEL SECURITY;
ALTER TABLE unit                  ENABLE ROW LEVEL SECURITY;
ALTER TABLE topic                 ENABLE ROW LEVEL SECURITY;
ALTER TABLE question_bank         ENABLE ROW LEVEL SECURITY;
ALTER TABLE question              ENABLE ROW LEVEL SECURITY;
ALTER TABLE questionpaper         ENABLE ROW LEVEL SECURITY;
ALTER TABLE questionpapermapping  ENABLE ROW LEVEL SECURITY;

-- Allow full access for backend (service-role key bypasses RLS anyway,
-- but these policies cover anon/authenticated clients too)
DO $$ DECLARE t TEXT;
BEGIN
    FOREACH t IN ARRAY ARRAY['"User"','subject','unit','topic','question_bank','question','questionpaper','questionpapermapping']
  LOOP
    EXECUTE format('CREATE POLICY "allow_all_%s" ON %s FOR ALL USING (true) WITH CHECK (true)', t, t);
  END LOOP;
END $$;
