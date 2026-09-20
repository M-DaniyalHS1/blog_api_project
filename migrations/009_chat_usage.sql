CREATE TABLE IF NOT EXISTS chat_usage (
    key VARCHAR(100) PRIMARY KEY,
    count INTEGER NOT NULL DEFAULT 0,
    expires_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_chat_usage_expires_at ON chat_usage (expires_at);
