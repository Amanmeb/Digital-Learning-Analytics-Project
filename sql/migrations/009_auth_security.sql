-- ============================================================
-- Migration 009
-- Authentication Security Tables
-- CDLAID Analytics Platform
-- ============================================================

BEGIN;

-- ============================================================
-- Extend auth.users
-- ============================================================

ALTER TABLE auth.users
ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER NOT NULL DEFAULT 0;

ALTER TABLE auth.users
ADD COLUMN IF NOT EXISTS last_failed_login TIMESTAMPTZ;

ALTER TABLE auth.users
ADD COLUMN IF NOT EXISTS locked_until TIMESTAMPTZ;

ALTER TABLE auth.users
ADD COLUMN IF NOT EXISTS last_login TIMESTAMPTZ;

ALTER TABLE auth.users
ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMPTZ DEFAULT NOW();

-- ============================================================
-- Refresh Tokens
-- ============================================================

CREATE TABLE IF NOT EXISTS auth.refresh_tokens (

    id UUID PRIMARY KEY,

    user_id UUID NOT NULL
        REFERENCES auth.users(user_id)
        ON DELETE CASCADE,

    token_hash TEXT NOT NULL UNIQUE,

    expires_at TIMESTAMPTZ NOT NULL,

    revoked BOOLEAN NOT NULL DEFAULT FALSE,

    revoked_at TIMESTAMPTZ,

    device_id TEXT,

    device_name TEXT,

    user_agent TEXT,

    ip_address INET,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user
ON auth.refresh_tokens(user_id);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_hash
ON auth.refresh_tokens(token_hash);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expiry
ON auth.refresh_tokens(expires_at);

-- ============================================================
-- Password Reset Tokens
-- ============================================================

CREATE TABLE IF NOT EXISTS auth.password_reset_tokens (

    id UUID PRIMARY KEY,

    user_id UUID NOT NULL
        REFERENCES auth.users(user_id)
        ON DELETE CASCADE,

    token_hash TEXT NOT NULL UNIQUE,

    expires_at TIMESTAMPTZ NOT NULL,

    used BOOLEAN NOT NULL DEFAULT FALSE,

    used_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_password_reset_user
ON auth.password_reset_tokens(user_id);

CREATE INDEX IF NOT EXISTS idx_password_reset_hash
ON auth.password_reset_tokens(token_hash);

CREATE INDEX IF NOT EXISTS idx_password_reset_expiry
ON auth.password_reset_tokens(expires_at);

-- ============================================================
-- Audit Logs
-- ============================================================

CREATE TABLE IF NOT EXISTS auth.audit_logs (

    id UUID PRIMARY KEY,

    user_id UUID
        REFERENCES auth.users(user_id)
        ON DELETE SET NULL,

    event VARCHAR(100) NOT NULL,

    ip_address INET,

    user_agent TEXT,

    device_id TEXT,

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user
ON auth.audit_logs(user_id);

CREATE INDEX IF NOT EXISTS idx_audit_logs_event
ON auth.audit_logs(event);

CREATE INDEX IF NOT EXISTS idx_audit_logs_created
ON auth.audit_logs(created_at DESC);

-- ============================================================
-- Permissions
-- ============================================================

GRANT SELECT, INSERT, UPDATE, DELETE
ON ALL TABLES IN SCHEMA auth
TO cdlaid_user;

COMMIT;