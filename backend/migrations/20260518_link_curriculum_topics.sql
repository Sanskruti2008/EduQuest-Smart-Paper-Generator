-- Link curriculum topics and subtopics in the topic table.
-- Run this once in Supabase SQL Editor for existing databases.

ALTER TABLE topic
    ADD COLUMN IF NOT EXISTS parent_topic_id BIGINT REFERENCES topic(topic_id) ON DELETE SET NULL;

ALTER TABLE topic
    DROP CONSTRAINT IF EXISTS topic_unit_id_topic_name_key;

DROP INDEX IF EXISTS uq_topic_root;
DROP INDEX IF EXISTS uq_topic_child;

CREATE UNIQUE INDEX IF NOT EXISTS uq_topic_root
    ON topic(unit_id, topic_name)
    WHERE parent_topic_id IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_topic_child
    ON topic(unit_id, parent_topic_id, topic_name)
    WHERE parent_topic_id IS NOT NULL;