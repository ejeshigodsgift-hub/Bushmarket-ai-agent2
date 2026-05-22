CREATE TABLE event_logs (
    id UUID PRIMARY KEY,

    event_type VARCHAR(100) NOT NULL,
    aggregate_type VARCHAR(100), -- cooperative, wallet, membership

    aggregate_id UUID,

    payload JSONB NOT NULL,

    status VARCHAR(30) DEFAULT 'pending',

    retry_count INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT NOW()
);