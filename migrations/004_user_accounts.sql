-- Additive migration: old app instances may still create unassigned posts.
-- The new app assigns those posts to the configured admin during startup.
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    token_version INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
ALTER TABLE blogs ADD COLUMN IF NOT EXISTS author_id INTEGER REFERENCES users(id);
CREATE INDEX IF NOT EXISTS ix_blogs_author_id ON blogs(author_id);
