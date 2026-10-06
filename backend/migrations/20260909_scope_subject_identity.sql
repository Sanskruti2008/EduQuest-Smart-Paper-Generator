-- Keep identical course names/codes separate by academic context.
-- Apply once to existing Supabase databases.

ALTER TABLE subject
    DROP CONSTRAINT IF EXISTS subject_subject_name_key;

CREATE UNIQUE INDEX IF NOT EXISTS uq_subject_code_context
    ON subject(subject_code, branch, semester)
    WHERE subject_code IS NOT NULL AND subject_code <> '';

CREATE UNIQUE INDEX IF NOT EXISTS uq_subject_name_context
    ON subject(subject_name, branch, semester)
    WHERE subject_code IS NULL OR subject_code = '';
