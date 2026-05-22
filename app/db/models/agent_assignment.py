CREATE TABLE agent_assignments (
    id UUID PRIMARY KEY,

    agent_id UUID REFERENCES market_agent_profiles(id),

    task_type VARCHAR(100),
    -- product_sourcing | delivery_check | supplier_contact

    cooperative_id UUID,
    product_reference TEXT,

    status VARCHAR(20) DEFAULT 'assigned',
    -- assigned | in_progress | completed | failed

    payload JSONB,

    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);