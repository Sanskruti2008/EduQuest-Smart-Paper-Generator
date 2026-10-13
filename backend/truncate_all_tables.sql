-- EduQuest Smart Paper generation System - Empty all application tables without changing the schema.
-- Run this in the Supabase SQL Editor.
-- This is destructive and cannot be undone after COMMIT.

BEGIN;

TRUNCATE TABLE
    questionpapermapping,
    questionpaper,
    question,
    question_bank,
    topic,
    unit,
    subject,
    "User"
RESTART IDENTITY CASCADE;

COMMIT;
