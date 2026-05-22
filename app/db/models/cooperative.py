CREATE TABLE cooperatives (
    id UUID PRIMARY KEY,

    creator_id UUID NOT NULL REFERENCES users(id),

    title VARCHAR(255) NOT NULL,
    description TEXT,

    product_name VARCHAR(255),
    product_category VARCHAR(255),

    target_quantity INTEGER NOT NULL,
    member_target INTEGER NOT NULL,

    contribution_per_member NUMERIC(18,2) NOT NULL,
    target_amount NUMERIC(18,2) NOT NULL,

    lifespan_days INTEGER NOT NULL CHECK (lifespan_days <= 60),

    status VARCHAR(30) NOT NULL DEFAULT 'draft',

    current_members INTEGER DEFAULT 0,
    current_amount NUMERIC(18,2) DEFAULT 0.00,

    starts_at TIMESTAMP,
    ends_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT unique_creator_product UNIQUE (creator_id, product_name)
);