CREATE TABLE IF NOT EXISTS schema_migrations (
    version text PRIMARY KEY,
    applied_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS app_users (
    id text PRIMARY KEY,
    display_name text NOT NULL,
    email text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_preferences (
    user_id text PRIMARY KEY REFERENCES app_users(id) ON DELETE CASCADE,
    target_role_keywords text[] NOT NULL DEFAULT '{}',
    preferred_locations text[] NOT NULL DEFAULT '{}',
    excluded_keywords text[] NOT NULL DEFAULT '{}',
    source_queries jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ingestion_runs (
    id bigserial PRIMARY KEY,
    selected_user_id text,
    mode text NOT NULL,
    started_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    fetched_count integer NOT NULL DEFAULT 0,
    parsed_count integer NOT NULL DEFAULT 0,
    new_count integer NOT NULL DEFAULT 0,
    duplicate_count integer NOT NULL DEFAULT 0,
    filtered_count integer NOT NULL DEFAULT 0,
    status text NOT NULL DEFAULT 'started',
    output_markdown_path text,
    output_json_path text,
    error_message text
);

CREATE TABLE IF NOT EXISTS email_messages (
    id bigserial PRIMARY KEY,
    user_id text NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
    gmail_message_id text NOT NULL,
    gmail_thread_id text,
    source text,
    sender text,
    subject text,
    received_at timestamptz,
    snippet text,
    body_hash text,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (user_id, gmail_message_id)
);

CREATE TABLE IF NOT EXISTS jobs (
    id bigserial PRIMARY KEY,
    source text NOT NULL,
    title text NOT NULL,
    company text,
    location text,
    url text,
    normalized_url text,
    normalized_url_hash text,
    normalized_title text NOT NULL,
    normalized_company text,
    normalized_location text,
    short_description text,
    first_seen_at timestamptz NOT NULL DEFAULT now(),
    last_seen_at timestamptz NOT NULL DEFAULT now(),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS jobs_source_url_hash_unique
    ON jobs (source, normalized_url_hash)
    WHERE normalized_url_hash IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS jobs_source_fallback_unique
    ON jobs (
        source,
        normalized_title,
        COALESCE(normalized_company, ''),
        COALESCE(normalized_location, '')
    )
    WHERE normalized_url_hash IS NULL;

CREATE TABLE IF NOT EXISTS user_jobs (
    user_id text NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
    job_id bigint NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    status text NOT NULL DEFAULT 'new',
    likely_relevant boolean,
    matched_keywords text[] NOT NULL DEFAULT '{}',
    matched_locations text[] NOT NULL DEFAULT '{}',
    exclusion_matches text[] NOT NULL DEFAULT '{}',
    relevance_reason text,
    first_seen_at timestamptz NOT NULL DEFAULT now(),
    last_seen_at timestamptz NOT NULL DEFAULT now(),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, job_id)
);

INSERT INTO app_users (id, display_name, email)
VALUES
    ('minjian', 'Minjian', 'minjian@example.invalid'),
    ('partner', 'Partner', 'partner@example.invalid')
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
        'minjian',
        ARRAY[
            'werkstudent ai',
            'werkstudent ki',
            'werkstudent softwareentwicklung',
            'working student software engineering',
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
    ),
    (
        'partner',
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
    )
ON CONFLICT (user_id) DO UPDATE
SET target_role_keywords = EXCLUDED.target_role_keywords,
    preferred_locations = EXCLUDED.preferred_locations,
    excluded_keywords = EXCLUDED.excluded_keywords,
    source_queries = EXCLUDED.source_queries,
    updated_at = now();
