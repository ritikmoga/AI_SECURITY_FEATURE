-- ScamShield AI user data schema
-- Target database: PostgreSQL 13+
-- Run with: psql "$DATABASE_URL" -f database/users_schema.sql

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(80) UNIQUE,
    password_hash TEXT NOT NULL,
    display_name VARCHAR(120),
    role VARCHAR(30) NOT NULL DEFAULT 'user',
    status VARCHAR(30) NOT NULL DEFAULT 'active',
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    mfa_secret_hash TEXT,
    failed_login_count INTEGER NOT NULL DEFAULT 0,
    locked_until TIMESTAMPTZ,
    last_login_at TIMESTAMPTZ,
    last_login_ip INET,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    CONSTRAINT users_role_check CHECK (role IN ('user', 'analyst', 'admin')),
    CONSTRAINT users_status_check CHECK (status IN ('active', 'pending', 'suspended', 'deleted')),
    CONSTRAINT users_email_lowercase_check CHECK (email = LOWER(email)),
    CONSTRAINT users_failed_login_count_check CHECK (failed_login_count >= 0)
);

CREATE TABLE IF NOT EXISTS user_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    full_name VARCHAR(160),
    phone VARCHAR(40),
    company VARCHAR(160),
    country VARCHAR(80),
    timezone VARCHAR(80) NOT NULL DEFAULT 'UTC',
    avatar_url TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    theme VARCHAR(40) NOT NULL DEFAULT 'infinity-shield',
    default_scanner VARCHAR(30) NOT NULL DEFAULT 'url',
    email_alerts_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    high_risk_alerts_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    report_retention_days INTEGER NOT NULL DEFAULT 90,
    settings JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT user_preferences_default_scanner_check CHECK (default_scanner IN ('url', 'message', 'file', 'qr')),
    CONSTRAINT user_preferences_retention_check CHECK (report_retention_days BETWEEN 1 AND 3650)
);

CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token_hash TEXT NOT NULL UNIQUE,
    refresh_token_hash TEXT UNIQUE,
    ip_address INET,
    user_agent TEXT,
    device_label VARCHAR(120),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    CONSTRAINT user_sessions_expiry_check CHECK (expires_at > created_at)
);

CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE,
    requested_ip INET,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    CONSTRAINT password_reset_tokens_expiry_check CHECK (expires_at > created_at)
);

CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    verified_at TIMESTAMPTZ,
    CONSTRAINT email_verification_tokens_expiry_check CHECK (expires_at > created_at)
);

CREATE TABLE IF NOT EXISTS user_api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(120) NOT NULL,
    key_prefix VARCHAR(16) NOT NULL,
    key_hash TEXT NOT NULL UNIQUE,
    scopes TEXT[] NOT NULL DEFAULT ARRAY['scan:read', 'scan:write'],
    last_used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_scan_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    scan_id VARCHAR(80) NOT NULL UNIQUE,
    scan_type VARCHAR(30) NOT NULL,
    target TEXT NOT NULL,
    risk_score INTEGER NOT NULL DEFAULT 0,
    risk_level VARCHAR(40) NOT NULL,
    report JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT user_scan_reports_scan_type_check CHECK (scan_type IN ('url', 'message', 'file', 'qr')),
    CONSTRAINT user_scan_reports_risk_score_check CHECK (risk_score BETWEEN 0 AND 100)
);

CREATE TABLE IF NOT EXISTS user_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    event_type VARCHAR(80) NOT NULL,
    event_status VARCHAR(30) NOT NULL DEFAULT 'success',
    ip_address INET,
    user_agent TEXT,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT user_audit_logs_status_check CHECK (event_status IN ('success', 'failure', 'blocked'))
);

CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_users_deleted_at ON users(deleted_at) WHERE deleted_at IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON user_sessions(user_id, expires_at)
    WHERE revoked_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_user_id ON password_reset_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_active ON password_reset_tokens(user_id, expires_at)
    WHERE used_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_user_id ON email_verification_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_active ON email_verification_tokens(user_id, expires_at)
    WHERE verified_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_user_api_keys_user_id ON user_api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_user_api_keys_active ON user_api_keys(user_id)
    WHERE revoked_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_user_scan_reports_user_id ON user_scan_reports(user_id);
CREATE INDEX IF NOT EXISTS idx_user_scan_reports_scan_type ON user_scan_reports(scan_type);
CREATE INDEX IF NOT EXISTS idx_user_scan_reports_risk_level ON user_scan_reports(risk_level);
CREATE INDEX IF NOT EXISTS idx_user_scan_reports_created_at ON user_scan_reports(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_scan_reports_report_gin ON user_scan_reports USING GIN (report);

CREATE INDEX IF NOT EXISTS idx_user_audit_logs_user_id ON user_audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_user_audit_logs_event_type ON user_audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_user_audit_logs_created_at ON user_audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_audit_logs_details_gin ON user_audit_logs USING GIN (details);

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_users_updated_at ON users;
CREATE TRIGGER trg_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_user_profiles_updated_at ON user_profiles;
CREATE TRIGGER trg_user_profiles_updated_at
BEFORE UPDATE ON user_profiles
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_user_preferences_updated_at ON user_preferences;
CREATE TRIGGER trg_user_preferences_updated_at
BEFORE UPDATE ON user_preferences
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

COMMENT ON TABLE users IS 'Core ScamShield AI user accounts. Store password hashes only, never raw passwords.';
COMMENT ON TABLE user_profiles IS 'Optional profile data linked one-to-one with users.';
COMMENT ON TABLE user_preferences IS 'Per-user ScamShield UI, alert, and retention preferences.';
COMMENT ON TABLE user_sessions IS 'Server-side login sessions stored as token hashes.';
COMMENT ON TABLE password_reset_tokens IS 'Password reset tokens stored as hashes with expiry.';
COMMENT ON TABLE email_verification_tokens IS 'Email verification tokens stored as hashes with expiry.';
COMMENT ON TABLE user_api_keys IS 'Optional API keys for programmatic ScamShield access, stored as hashes.';
COMMENT ON TABLE user_scan_reports IS 'User-linked scan reports compatible with the existing ScamShield report shape.';
COMMENT ON TABLE user_audit_logs IS 'Security audit trail for auth, account, and scanner actions.';

COMMIT;
