CREATE TABLE IF NOT EXISTS app_user_profiles (
    auth_subject text PRIMARY KEY,
    user_id text NOT NULL UNIQUE REFERENCES app_users(id) ON DELETE CASCADE,
    auth_provider text NOT NULL DEFAULT 'neon',
    display_name text,
    email text,
    onboarding_complete boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS app_user_profiles_user_id_idx
    ON app_user_profiles (user_id);
