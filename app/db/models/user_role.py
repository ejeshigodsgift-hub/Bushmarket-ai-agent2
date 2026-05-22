CREATE TABLE user_roles (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),

    role VARCHAR(50) NOT NULL,
    -- roles: shopper | cooperative_creator | member | market_agent | admin

    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(user_id, role)
);