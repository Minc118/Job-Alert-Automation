ALTER TABLE user_jobs
    ADD COLUMN IF NOT EXISTS first_seen_run_id bigint REFERENCES ingestion_runs(id),
    ADD COLUMN IF NOT EXISTS last_seen_run_id bigint REFERENCES ingestion_runs(id);

CREATE TABLE IF NOT EXISTS job_run_occurrences (
    ingestion_run_id bigint NOT NULL REFERENCES ingestion_runs(id) ON DELETE CASCADE,
    user_id text NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
    job_id bigint NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    seen_as_new boolean NOT NULL DEFAULT false,
    seen_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (ingestion_run_id, user_id, job_id)
);

CREATE INDEX IF NOT EXISTS job_run_occurrences_user_job_idx
    ON job_run_occurrences (user_id, job_id);

CREATE INDEX IF NOT EXISTS job_run_occurrences_run_user_idx
    ON job_run_occurrences (ingestion_run_id, user_id);

CREATE TABLE IF NOT EXISTS analysis_batches (
    id bigserial PRIMARY KEY,
    user_id text NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
    status text NOT NULL DEFAULT 'prepared',
    request_markdown_path text,
    request_json_path text,
    result_json_path text,
    job_count integer NOT NULL DEFAULT 0,
    created_at timestamptz NOT NULL DEFAULT now(),
    imported_at timestamptz,
    error_message text
);

CREATE INDEX IF NOT EXISTS analysis_batches_user_created_idx
    ON analysis_batches (user_id, created_at);

CREATE TABLE IF NOT EXISTS codex_job_analyses (
    id bigserial PRIMARY KEY,
    user_id text NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
    job_id bigint NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    analysis_batch_id bigint REFERENCES analysis_batches(id) ON DELETE SET NULL,
    score numeric,
    priority text NOT NULL,
    reason text,
    concern text,
    suggested_status text,
    source_file text,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS codex_job_analyses_user_job_idx
    ON codex_job_analyses (user_id, job_id);

CREATE INDEX IF NOT EXISTS codex_job_analyses_priority_idx
    ON codex_job_analyses (priority);

INSERT INTO app_users (id, display_name, email)
VALUES ('chang', 'Chang', 'chang@example.invalid')
ON CONFLICT (id) DO UPDATE
SET display_name = EXCLUDED.display_name,
    email = EXCLUDED.email,
    updated_at = now();

INSERT INTO user_preferences (
    user_id,
    target_role_keywords,
    preferred_locations,
    excluded_keywords,
    source_queries
)
VALUES
    (
        'chang',
        ARRAY[
            'project management',
            'junior project manager',
            'project coordinator',
            'marketing',
            'communications',
            'public relations',
            'pr',
            'business development',
            'operations',
            'digital transformation',
            'team assistant'
        ],
        ARRAY['berlin', 'potsdam', 'remote', 'hybrid berlin', 'hybrid potsdam'],
        ARRAY[
            'senior',
            'lead',
            'director',
            'native german required',
            'muttersprachlich deutsch',
            'internship unpaid',
            'praktikum unbezahlt'
        ],
        '{
            "linkedin": "from:(jobs-noreply@linkedin.com) newer_than:7d",
            "stepstone": "from:(stepstone) newer_than:7d",
            "indeed": "from:(indeed) newer_than:7d"
        }'::jsonb
    ),
    (
        'minjian',
        ARRAY[
            'werkstudent ai',
            'werkstudent ki',
            'werkstudent softwareentwicklung',
            'working student software engineering',
            'working student automation',
            'working student data',
            'werkstudent it projektmanagement',
            'werkstudent product management',
            'werkstudent data',
            'werkstudent automation',
            'werkstudent digitalisierung',
            'junior software developer',
            'student assistant it'
        ],
        ARRAY['berlin', 'potsdam', 'remote', 'hybrid berlin', 'hybrid potsdam'],
        ARRAY['senior', 'lead', 'principal', 'internship unpaid', 'praktikum unbezahlt'],
        '{
            "linkedin": "from:(jobs-noreply@linkedin.com) newer_than:7d",
            "stepstone": "from:(stepstone) newer_than:7d",
            "indeed": "from:(indeed) newer_than:7d"
        }'::jsonb
    )
ON CONFLICT (user_id) DO UPDATE
SET target_role_keywords = EXCLUDED.target_role_keywords,
    preferred_locations = EXCLUDED.preferred_locations,
    excluded_keywords = EXCLUDED.excluded_keywords,
    source_queries = EXCLUDED.source_queries,
    updated_at = now();
