CREATE TABLE cooperative_memberships (
    id UUID PRIMARY KEY,

    cooperative_id UUID NOT NULL REFERENCES cooperatives(id),
    user_id UUID NOT NULL REFERENCES users(id),

    status VARCHAR(20) DEFAULT 'pending',

    contribution_amount NUMERIC(18,2) NOT NULL,

    payment_reference VARCHAR(255), -- Paystack/Stripe reference

    joined_at TIMESTAMP DEFAULT NOW(),

    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT unique_membership UNIQUE (cooperative_id, user_id)
);