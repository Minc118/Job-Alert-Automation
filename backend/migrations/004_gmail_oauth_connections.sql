CREATE TABLE IF NOT EXISTS gmail_oauth_connections (
    user_id text PRIMARY KEY REFERENCES app_users(id) ON DELETE CASCADE,
    connected_email text,
    encrypted_credentials text NOT NULL,
    scope text NOT NULL DEFAULT 'https://www.googleapis.com/auth/gmail.readonly',
    status text NOT NULL DEFAULT 'connected',
    last_fetch_at timestamptz,
    last_error text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS gmail_oauth_connections_status_idx
    ON gmail_oauth_connections (status);
