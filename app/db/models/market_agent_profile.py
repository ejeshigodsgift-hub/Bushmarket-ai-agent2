CREATE TABLE market_agent_profiles (
    id UUID PRIMARY KEY,
    user_id UUID UNIQUE REFERENCES users(id),

    approval_status VARCHAR(20) DEFAULT 'active',

    rating NUMERIC(3,2) DEFAULT 0.0,
    total_tasks INTEGER DEFAULT 0,

    region TEXT,

    created_at TIMESTAMP DEFAULT NOW()
);