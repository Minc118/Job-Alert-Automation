CREATE TABLE IF NOT EXISTS user_documents (
    id bigserial PRIMARY KEY,
    user_id text NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
    document_type text NOT NULL,
    original_filename text NOT NULL,
    stored_path text NOT NULL,
    mime_type text,
    file_size_bytes bigint,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT user_documents_type_check
        CHECK (document_type IN ('profile_markdown', 'resume_pdf', 'cover_letter_template'))
);

CREATE INDEX IF NOT EXISTS user_documents_user_created_idx
    ON user_documents (user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS user_documents_user_type_active_idx
    ON user_documents (user_id, document_type, is_active);
