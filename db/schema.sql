CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS habits (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT    NOT NULL,
    type        TEXT    NOT NULL CHECK (type IN ('ternary', 'boolean')),
    is_active   BOOLEAN NOT NULL DEFAULT true,
    created_at  DATE    NOT NULL DEFAULT CURRENT_DATE,
    archived_at DATE
);

CREATE TABLE IF NOT EXISTS habit_logs (
    id         UUID      PRIMARY KEY DEFAULT gen_random_uuid(),
    habit_id   UUID      NOT NULL REFERENCES habits(id),
    date       DATE      NOT NULL,
    value      SMALLINT  NOT NULL CHECK (value >= 0 AND value <= 2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_habit_date UNIQUE (habit_id, date)
);

CREATE INDEX IF NOT EXISTS idx_logs_date     ON habit_logs(date);
CREATE INDEX IF NOT EXISTS idx_logs_habit_id ON habit_logs(habit_id);
