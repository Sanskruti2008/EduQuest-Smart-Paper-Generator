-- Store unit-level RUA markings alongside each unit name.
-- Apply once for existing databases.

ALTER TABLE unit
    ADD COLUMN IF NOT EXISTS rua_json JSONB DEFAULT '{}'::jsonb;