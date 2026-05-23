CREATE TABLE agent_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- applicant (required)
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    motivation TEXT,
    experience TEXT,

    -- strict lifecycle status
    status VARCHAR(20) NOT NULL DEFAULT 'pending',

    -- admin review tracking
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW(),

    -- =========================
    -- CONSTRAINTS (BUSINESS RULE)
    -- =========================
    CONSTRAINT chk_agent_application_status
        CHECK (status IN ('pending', 'approved', 'rejected'))
);


-- =========================
-- INDEXES (PERFORMANCE CRITICAL)
-- =========================
CREATE INDEX idx_agent_applications_user_id
    ON agent_applications(user_id);

CREATE INDEX idx_agent_applications_status
    ON agent_applications(status);