CREATE TABLE shopper_profiles (
    id UUID PRIMARY KEY,
    user_id UUID UNIQUE REFERENCES users(id),

    preferred_categories JSONB,
    location TEXT,

    created_at TIMESTAMP DEFAULT NOW()
);