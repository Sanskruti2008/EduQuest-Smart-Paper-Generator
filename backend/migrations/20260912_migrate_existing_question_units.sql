-- Map existing questions to numeric unit names from their course outcomes.
-- CO1 -> Unit 1, CO2 -> Unit 2, CO3 -> Unit 3, CO4 -> Unit 4, CO5 -> Unit 5.
-- Run after the subject/unit tables exist.
-- The generated unit_id values remain unchanged; only question references move.

BEGIN;

DO $$
DECLARE
    question_row RECORD;
    target_unit_id BIGINT;
    target_unit_name TEXT;
    co_number INTEGER;
BEGIN
    FOR question_row IN
        SELECT question_id, subject_id, course_outcome
        FROM question
        WHERE course_outcome ~* '^CO\s*[1-5]$'
    LOOP
        co_number := substring(question_row.course_outcome FROM '[1-5]')::INTEGER;
        target_unit_name := format('Unit %s', co_number);

        SELECT unit_id
        INTO target_unit_id
        FROM unit
        WHERE subject_id = question_row.subject_id
          AND lower(btrim(unit_name)) = lower(target_unit_name)
        ORDER BY unit_id
        LIMIT 1;

        IF target_unit_id IS NULL THEN
            INSERT INTO unit (unit_name, subject_id)
            VALUES (target_unit_name, question_row.subject_id)
            RETURNING unit_id INTO target_unit_id;
        END IF;

        UPDATE question
        SET unit_id = target_unit_id
        WHERE question_id = question_row.question_id;
    END LOOP;
END $$;

COMMIT;
