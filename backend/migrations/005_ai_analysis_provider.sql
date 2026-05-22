ALTER TABLE codex_job_analyses
    ADD COLUMN IF NOT EXISTS provider text NOT NULL DEFAULT 'codex';

CREATE INDEX IF NOT EXISTS codex_job_analyses_provider_idx
    ON codex_job_analyses (provider);
