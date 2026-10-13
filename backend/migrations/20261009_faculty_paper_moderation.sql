ALTER TABLE public.faculty_subject_assignment
    ADD COLUMN IF NOT EXISTS can_generate BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS can_moderate BOOLEAN NOT NULL DEFAULT FALSE;

UPDATE public.faculty_subject_assignment
SET can_generate = TRUE
WHERE can_generate IS NULL;

UPDATE public.faculty_subject_assignment
SET can_moderate = FALSE
WHERE can_moderate IS NULL;

ALTER TABLE public.questionpaper
    ADD COLUMN IF NOT EXISTS generated_by BIGINT
        REFERENCES public."User"(user_id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS moderated_by BIGINT
        REFERENCES public."User"(user_id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS moderated_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS moderation_comments TEXT,
    ADD COLUMN IF NOT EXISTS reviewed_by BIGINT
        REFERENCES public."User"(user_id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS review_comments TEXT,
    ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'FINALIZED';

CREATE INDEX IF NOT EXISTS idx_questionpaper_generated_by
    ON public.questionpaper(generated_by);
CREATE INDEX IF NOT EXISTS idx_questionpaper_status_subject
    ON public.questionpaper(status, subject_id);

CREATE OR REPLACE FUNCTION public.persist_generated_question_paper(
    p_subject_id BIGINT,
    p_exam_type TEXT,
    p_exam_year INTEGER,
    p_raw_json JSONB,
    p_question_ids BIGINT[],
    p_generation_log JSONB
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = public
AS $$
DECLARE
    v_paper_id BIGINT;
    v_generation_id BIGINT;
    v_mapping_count INTEGER;
    v_usage_count INTEGER;
    v_log papergenerationlog%ROWTYPE;
BEGIN
    IF COALESCE(cardinality(p_question_ids), 0)
        <> COALESCE((p_generation_log->>'total_questions')::INTEGER, -1) THEN
        RAISE EXCEPTION 'PERSISTENCE_ERROR: question ID count does not match generation log';
    END IF;

    IF (
        SELECT count(DISTINCT question_id)
        FROM unnest(p_question_ids) AS ids(question_id)
    ) <> cardinality(p_question_ids) THEN
        RAISE EXCEPTION 'PERSISTENCE_ERROR: duplicate question IDs';
    END IF;

    INSERT INTO public.questionpaper (
        subject_id,
        exam_type,
        exam_year,
        raw_json,
        generated_by,
        status
    )
    VALUES (
        p_subject_id,
        p_exam_type,
        p_exam_year,
        p_raw_json,
        NULLIF(p_generation_log->>'generated_by', '')::BIGINT,
        COALESCE(NULLIF(p_generation_log->>'initial_status', ''), 'SUBMITTED_FOR_MODERATION')
    )
    RETURNING paper_id INTO v_paper_id;

    INSERT INTO public.questionpapermapping (paper_id, question_id)
    SELECT v_paper_id, question_id
    FROM unnest(p_question_ids) AS ids(question_id);
    GET DIAGNOSTICS v_mapping_count = ROW_COUNT;

    IF v_mapping_count <> cardinality(p_question_ids) THEN
        RAISE EXCEPTION 'PERSISTENCE_ERROR: expected % mapping rows, inserted %',
            cardinality(p_question_ids), v_mapping_count;
    END IF;

    INSERT INTO public.questionusagehistory (paper_id, question_id)
    SELECT v_paper_id, question_id
    FROM unnest(p_question_ids) AS ids(question_id);
    GET DIAGNOSTICS v_usage_count = ROW_COUNT;

    IF v_usage_count <> cardinality(p_question_ids) THEN
        RAISE EXCEPTION 'PERSISTENCE_ERROR: expected % usage rows, inserted %',
            cardinality(p_question_ids), v_usage_count;
    END IF;

    v_log := jsonb_populate_record(
        NULL::public.papergenerationlog,
        p_generation_log || jsonb_build_object('paper_id', v_paper_id)
    );

    INSERT INTO public.papergenerationlog (
        paper_id,
        blueprint_id,
        generated_by,
        total_questions,
        total_marks,
        generated_at
    )
    VALUES (
        v_log.paper_id,
        v_log.blueprint_id,
        v_log.generated_by,
        v_log.total_questions,
        v_log.total_marks,
        v_log.generated_at
    )
    RETURNING generation_id INTO v_generation_id;

    IF v_generation_id IS NULL THEN
        RAISE EXCEPTION 'PERSISTENCE_ERROR: generation log insert returned no ID';
    END IF;

    RETURN jsonb_build_object(
        'paper_id', v_paper_id,
        'generation_id', v_generation_id,
        'paper_records', 1,
        'mapped_questions', v_mapping_count,
        'usage_records', v_usage_count,
        'generation_log_records', 1
    );
END;
$$;

REVOKE ALL ON FUNCTION public.persist_generated_question_paper(
    BIGINT, TEXT, INTEGER, JSONB, BIGINT[], JSONB
) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION public.persist_generated_question_paper(
    BIGINT, TEXT, INTEGER, JSONB, BIGINT[], JSONB
) TO service_role;
