-- Day 4 migration: approval audit records and idempotency constraints.
-- Run once against the existing Neon database before using approval/redemption APIs.

CREATE TABLE IF NOT EXISTS reward_approvals (
    approval_id VARCHAR PRIMARY KEY,
    idempotency_key VARCHAR NOT NULL,
    request_hash VARCHAR NOT NULL,
    customer_id NUMERIC(12, 0) NOT NULL
        REFERENCES customer_loyalty_profiles(customer_id),
    reward_id VARCHAR NOT NULL
        REFERENCES reward_catalogue(reward_id),
    campaign_id VARCHAR NOT NULL
        REFERENCES campaign_budgets(campaign_id),
    purchase_value NUMERIC NOT NULL,
    evaluation_date DATE NOT NULL,
    points_required INTEGER NOT NULL,
    reward_cost NUMERIC NOT NULL,
    approval_status VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_reward_approvals_idempotency_key UNIQUE (idempotency_key)
);

ALTER TABLE reward_ledger
    ADD COLUMN IF NOT EXISTS approval_id VARCHAR
        REFERENCES reward_approvals(approval_id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_reward_ledger_idempotency_key
    ON reward_ledger(idempotency_key);
