-- Run before deploying the new backend. Existing dates remain unknown.
BEGIN;
ALTER TABLE blogs ADD COLUMN IF NOT EXISTS source_url TEXT;
ALTER TABLE blogs ADD COLUMN IF NOT EXISTS published_at TIMESTAMPTZ;
ALTER TABLE blogs ALTER COLUMN published_at SET DEFAULT CURRENT_TIMESTAMP;
COMMIT;
