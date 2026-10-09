ALTER TABLE public."User"
    ADD COLUMN IF NOT EXISTS auth_user_id UUID,
    ADD COLUMN IF NOT EXISTS employee_id TEXT,
    ADD COLUMN IF NOT EXISTS department TEXT,
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;

UPDATE public."User" SET is_active = TRUE WHERE is_active IS NULL;
ALTER TABLE public."User" ALTER COLUMN is_active SET DEFAULT TRUE;
ALTER TABLE public."User" ALTER COLUMN is_active SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_user_auth_user_id
    ON public."User"(auth_user_id)
    WHERE auth_user_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_user_email_lower
    ON public."User"(LOWER(email))
    WHERE email IS NOT NULL AND email <> '';

CREATE UNIQUE INDEX IF NOT EXISTS uq_user_employee_id_lower
    ON public."User"(LOWER(employee_id))
    WHERE employee_id IS NOT NULL AND employee_id <> '';

CREATE TABLE IF NOT EXISTS public.faculty_subject_assignment (
    faculty_id BIGINT NOT NULL REFERENCES public."User"(user_id) ON DELETE RESTRICT,
    subject_id BIGINT NOT NULL REFERENCES public.subject(subject_id) ON DELETE RESTRICT,
    assigned_by BIGINT NOT NULL REFERENCES public."User"(user_id) ON DELETE RESTRICT,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

ALTER TABLE public.faculty_subject_assignment
    ADD COLUMN IF NOT EXISTS assigned_by BIGINT REFERENCES public."User"(user_id) ON DELETE RESTRICT,
    ADD COLUMN IF NOT EXISTS assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;

UPDATE public.faculty_subject_assignment
SET assigned_at = NOW()
WHERE assigned_at IS NULL;
UPDATE public.faculty_subject_assignment
SET is_active = TRUE
WHERE is_active IS NULL;
ALTER TABLE public.faculty_subject_assignment
    ALTER COLUMN assigned_at SET DEFAULT NOW(),
    ALTER COLUMN assigned_at SET NOT NULL,
    ALTER COLUMN is_active SET DEFAULT TRUE,
    ALTER COLUMN is_active SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_faculty_subject_assignment
    ON public.faculty_subject_assignment(faculty_id, subject_id);

CREATE INDEX IF NOT EXISTS idx_faculty_assignment_active
    ON public.faculty_subject_assignment(faculty_id, is_active);

ALTER TABLE public.faculty_subject_assignment ENABLE ROW LEVEL SECURITY;

DO $$
DECLARE
    policy_name TEXT;
BEGIN
    FOR policy_name IN
        SELECT policyname
        FROM pg_policies
        WHERE schemaname = 'public' AND tablename = 'User'
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON public."User"', policy_name);
    END LOOP;
END
$$;
