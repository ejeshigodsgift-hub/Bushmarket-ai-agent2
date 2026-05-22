CREATE TABLE agent_applications (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),

    motivation TEXT,
    experience TEXT,

    status VARCHAR(20) DEFAULT 'pending',
    -- pending | approved | rejected

    reviewed_by UUID,
    reviewed_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW()
);