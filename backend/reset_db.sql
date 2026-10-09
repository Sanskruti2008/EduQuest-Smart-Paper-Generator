-- ============================================================
-- EduQuest.ai - Full Database Reset
-- Drops all tables and sequences, then recreates from scratch.
-- Run this in the Supabase SQL Editor.
-- ============================================================

-- Drop tables in reverse FK order to avoid dependency errors
DROP TABLE IF EXISTS questionpapermapping CASCADE;
DROP TABLE IF EXISTS questionpaper        CASCADE;
DROP TABLE IF EXISTS question             CASCADE;
DROP TABLE IF EXISTS question_bank        CASCADE;
DROP TABLE IF EXISTS topic                CASCADE;
DROP TABLE IF EXISTS unit                 CASCADE;
DROP TABLE IF EXISTS subject              CASCADE;
DROP TABLE IF EXISTS "User"               CASCADE;

-- 1. User
CREATE TABLE "User" (
    user_id    BIGSERIAL PRIMARY KEY,
    name       TEXT NOT NULL,
    role       TEXT NOT NULL DEFAULT 'faculty',
    email      TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. subject
CREATE TABLE subject (
    subject_id   BIGSERIAL PRIMARY KEY,
    subject_name TEXT NOT NULL UNIQUE,
    subject_code TEXT,
    semester     TEXT,
    branch       TEXT,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- 3. unit
CREATE TABLE unit (
    unit_id    BIGSERIAL PRIMARY KEY,
    unit_name  TEXT   NOT NULL,
    subject_id BIGINT NOT NULL REFERENCES subject(subject_id) ON DELETE CASCADE,
    UNIQUE (subject_id, unit_name)
);

-- 4. topic
CREATE TABLE topic (
    topic_id   BIGSERIAL PRIMARY KEY,
    topic_name TEXT   NOT NULL,
    unit_id    BIGINT NOT NULL REFERENCES unit(unit_id) ON DELETE CASCADE,
    UNIQUE (unit_id, topic_name)
);

-- 5. question_bank
CREATE TABLE question_bank (
    question_bank_id BIGSERIAL PRIMARY KEY,
    subject_id       BIGINT NOT NULL UNIQUE REFERENCES subject(subject_id) ON DELETE CASCADE,
    bank_name        TEXT   NOT NULL,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- 6. question
CREATE TABLE question (
    question_id      BIGSERIAL PRIMARY KEY,
    question_text    TEXT    NOT NULL,
    question_type    TEXT    NOT NULL DEFAULT 'Short Answer',
    difficulty_level TEXT    NOT NULL DEFAULT 'Medium',
    subject_id       BIGINT  NOT NULL REFERENCES subject(subject_id) ON DELETE CASCADE,
    question_bank_id BIGINT  REFERENCES question_bank(question_bank_id) ON DELETE SET NULL,
    marks            INTEGER NOT NULL DEFAULT 5,
    course_outcome   TEXT,

    unit_id          BIGINT  REFERENCES unit(unit_id) ON DELETE SET NULL,
    bloom_level      TEXT    DEFAULT 'Understand',
    rua              TEXT    DEFAULT 'U',
    question_number  TEXT,
    sub_label        TEXT,
    sub_questions    JSONB   DEFAULT '[]',
    has_diagram      BOOLEAN DEFAULT FALSE,
    has_math         BOOLEAN DEFAULT FALSE,
    images           JSONB   DEFAULT '[]',
    answer           TEXT,
    chapter          TEXT,
    source_type      TEXT    DEFAULT 'OCR Extracted',
    status           TEXT    DEFAULT 'active',
    created_by       BIGINT  REFERENCES "User"(user_id) ON DELETE SET NULL,
    question_hash    TEXT    UNIQUE,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- 7. questionpaper
CREATE TABLE questionpaper (
    paper_id   BIGSERIAL PRIMARY KEY,
    subject_id BIGINT NOT NULL REFERENCES subject(subject_id) ON DELETE CASCADE,
    exam_type  TEXT   NOT NULL DEFAULT 'University',
    exam_year  INTEGER,
    exam_date  DATE,
    raw_json   JSONB  DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. questionpapermapping
CREATE TABLE questionpapermapping (
    mapping_id  BIGSERIAL PRIMARY KEY,
    paper_id    BIGINT NOT NULL REFERENCES questionpaper(paper_id) ON DELETE CASCADE,
    question_id BIGINT NOT NULL REFERENCES question(question_id)  ON DELETE CASCADE,
    CONSTRAINT fk_mapping_paper FOREIGN KEY (paper_id) REFERENCES questionpaper(paper_id) ON DELETE CASCADE,
    UNIQUE (paper_id, question_id)
);

-- Indexes
CREATE INDEX idx_question_subject    ON question(subject_id);
CREATE INDEX idx_question_bank       ON question(question_bank_id);
CREATE INDEX idx_question_co         ON question(course_outcome);
CREATE INDEX idx_question_bloom      ON question(bloom_level);
CREATE INDEX idx_question_difficulty ON question(difficulty_level);
CREATE INDEX idx_question_hash       ON question(question_hash);
CREATE INDEX idx_qpm_paper           ON questionpapermapping(paper_id);
CREATE INDEX idx_qpm_question        ON questionpapermapping(question_id);
CREATE INDEX idx_qp_subject          ON questionpaper(subject_id);
CREATE INDEX idx_qbank_subject       ON question_bank(subject_id);
CREATE INDEX idx_unit_subject        ON unit(subject_id);
CREATE INDEX idx_topic_unit          ON topic(unit_id);
CREATE INDEX idx_subject_semester    ON subject(semester);
CREATE INDEX idx_subject_branch      ON subject(branch);
CREATE INDEX idx_question_fts        ON question USING gin(to_tsvector('english', question_text));

-- Row Level Security
ALTER TABLE "User"               ENABLE ROW LEVEL SECURITY;
ALTER TABLE subject              ENABLE ROW LEVEL SECURITY;
ALTER TABLE unit                 ENABLE ROW LEVEL SECURITY;
ALTER TABLE topic                ENABLE ROW LEVEL SECURITY;
ALTER TABLE question_bank        ENABLE ROW LEVEL SECURITY;
ALTER TABLE question             ENABLE ROW LEVEL SECURITY;
ALTER TABLE questionpaper        ENABLE ROW LEVEL SECURITY;
ALTER TABLE questionpapermapping ENABLE ROW LEVEL SECURITY;

CREATE POLICY "allow_all_User"                 ON "User"               FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_subject"              ON subject              FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_unit"                 ON unit                 FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_topic"                ON topic                FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_question_bank"        ON question_bank         FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_question"             ON question             FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_questionpaper"        ON questionpaper        FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_questionpapermapping" ON questionpapermapping FOR ALL USING (true) WITH CHECK (true);

-- Safe migration: add semester/branch to subject if running on an existing schema
ALTER TABLE subject ADD COLUMN IF NOT EXISTS semester TEXT;
ALTER TABLE subject ADD COLUMN IF NOT EXISTS branch   TEXT;
