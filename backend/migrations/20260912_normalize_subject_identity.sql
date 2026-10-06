-- Normalize subject identity so NULL, empty, and casing differences cannot
-- create multiple rows for the same subject in the same academic context.
-- Apply once in the Supabase SQL Editor.

UPDATE subject
SET subject_name = btrim(subject_name),
    subject_code = btrim(coalesce(subject_code, '')),
    branch = btrim(coalesce(branch, '')),
    semester = btrim(coalesce(semester, ''));

-- Retain the oldest row for each normalized subject identity.
CREATE TEMP TABLE subject_id_merge (
    duplicate_id BIGINT PRIMARY KEY,
    keep_id BIGINT NOT NULL
);

INSERT INTO subject_id_merge (duplicate_id, keep_id)
SELECT duplicate.subject_id, keeper.subject_id
FROM subject AS duplicate
JOIN subject AS keeper
  ON lower(btrim(keeper.subject_name)) = lower(btrim(duplicate.subject_name))
 AND lower(coalesce(keeper.subject_code, '')) = lower(coalesce(duplicate.subject_code, ''))
 AND lower(coalesce(keeper.branch, '')) = lower(coalesce(duplicate.branch, ''))
 AND lower(coalesce(keeper.semester, '')) = lower(coalesce(duplicate.semester, ''))
 AND keeper.subject_id < duplicate.subject_id;

UPDATE unit AS target
SET subject_id = merge.keep_id
FROM subject_id_merge AS merge
WHERE target.subject_id = merge.duplicate_id;

UPDATE question_bank AS target
SET subject_id = merge.keep_id
FROM subject_id_merge AS merge
WHERE target.subject_id = merge.duplicate_id;

UPDATE questionpaper AS target
SET subject_id = merge.keep_id
FROM subject_id_merge AS merge
WHERE target.subject_id = merge.duplicate_id;

UPDATE question AS target
SET subject_id = merge.keep_id
FROM subject_id_merge AS merge
WHERE target.subject_id = merge.duplicate_id;

DELETE FROM subject
WHERE subject_id IN (SELECT duplicate_id FROM subject_id_merge);

DROP INDEX IF EXISTS uq_subject_code_context;
DROP INDEX IF EXISTS uq_subject_name_context;

CREATE UNIQUE INDEX IF NOT EXISTS uq_subject_code_context
    ON subject (
        lower(btrim(subject_code)),
        lower(btrim(branch)),
        lower(btrim(semester))
    )
    WHERE btrim(coalesce(subject_code, '')) <> '';

CREATE UNIQUE INDEX IF NOT EXISTS uq_subject_name_context
    ON subject (
        lower(btrim(subject_name)),
        lower(btrim(branch)),
        lower(btrim(semester))
    )
    WHERE btrim(coalesce(subject_code, '')) = '';

DROP TABLE subject_id_merge;