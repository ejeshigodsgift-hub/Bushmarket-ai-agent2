CREATE TABLE cooperative_wallets (
    id UUID PRIMARY KEY,

    cooperative_id UUID UNIQUE NOT NULL REFERENCES cooperatives(id),

    currency VARCHAR(10) DEFAULT 'NGN',

    escrow_balance NUMERIC(18,2) DEFAULT 0.00,

    available_balance NUMERIC(18,2) DEFAULT 0.00,

    status VARCHAR(20) DEFAULT 'active',

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);