ALTER TABLE users ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'PENDING';
CREATE INDEX IF NOT EXISTS ix_users_status ON users(status);
ALTER TABLE users ADD COLUMN IF NOT EXISTS business_name VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS residential_address TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS business_address TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS business_type VARCHAR(100);
ALTER TABLE users ADD COLUMN IF NOT EXISTS years_in_operation INTEGER;
ALTER TABLE users ADD COLUMN IF NOT EXISTS cac_registration_number VARCHAR(100);
ALTER TABLE users ADD COLUMN IF NOT EXISTS cac_certificate_url VARCHAR(500);
ALTER TABLE users ADD COLUMN IF NOT EXISTS government_id_url VARCHAR(500);
ALTER TABLE users ADD COLUMN IF NOT EXISTS kyc_status VARCHAR(20) DEFAULT 'PENDING';
ALTER TABLE users ADD COLUMN IF NOT EXISTS kyc_verified_at TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN IF NOT EXISTS kyc_verified_by VARCHAR(36);
ALTER TABLE users ADD COLUMN IF NOT EXISTS admin_note TEXT;
CREATE INDEX IF NOT EXISTS ix_users_kyc_status ON users(kyc_status);
ALTER TABLE users ADD COLUMN IF NOT EXISTS savings_balance DOUBLE PRECISION DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS shares_balance DOUBLE PRECISION DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_collateral DOUBLE PRECISION DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS total_contributions DOUBLE PRECISION DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS total_loans_taken DOUBLE PRECISION DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS total_loans_repaid DOUBLE PRECISION DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS credit_score INTEGER DEFAULT 50;
ALTER TABLE users ADD COLUMN IF NOT EXISTS active_loan_id VARCHAR(36);
ALTER TABLE users ADD COLUMN IF NOT EXISTS join_date TIMESTAMPTZ DEFAULT NOW();

ALTER TABLE loans ADD COLUMN IF NOT EXISTS remaining_balance DOUBLE PRECISION DEFAULT 0;
ALTER TABLE loans ADD COLUMN IF NOT EXISTS guarantor_id VARCHAR(36);
ALTER TABLE loans ADD COLUMN IF NOT EXISTS collateral_locked DOUBLE PRECISION DEFAULT 0;
ALTER TABLE loans ADD COLUMN IF NOT EXISTS collateral_released BOOLEAN DEFAULT FALSE;
ALTER TABLE loans ADD COLUMN IF NOT EXISTS collateral_used_for_recovery DOUBLE PRECISION DEFAULT 0;
ALTER TABLE loans ADD COLUMN IF NOT EXISTS due_date TIMESTAMPTZ;
ALTER TABLE loans ADD COLUMN IF NOT EXISTS last_payment_date TIMESTAMPTZ;
ALTER TABLE loans ADD COLUMN IF NOT EXISTS days_overdue INTEGER DEFAULT 0;
ALTER TABLE loans ADD COLUMN IF NOT EXISTS overdue_penalty DOUBLE PRECISION DEFAULT 0;
ALTER TABLE loans ADD COLUMN IF NOT EXISTS recovery_status VARCHAR(30) DEFAULT 'none';
ALTER TABLE loans ADD COLUMN IF NOT EXISTS meeting_id VARCHAR(36);
ALTER TABLE loans ADD COLUMN IF NOT EXISTS defaulted_at TIMESTAMPTZ;
ALTER TABLE loans ADD COLUMN IF NOT EXISTS approval_note TEXT;
ALTER TABLE loans ADD COLUMN IF NOT EXISTS rejection_reason TEXT;

ALTER TABLE contributions ADD COLUMN IF NOT EXISTS meeting_id VARCHAR(36);
ALTER TABLE contributions ADD COLUMN IF NOT EXISTS rejection_reason TEXT;

CREATE TABLE IF NOT EXISTS system_settings (
    id VARCHAR(36) PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value VARCHAR(255) NOT NULL,
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by VARCHAR(36)
);
CREATE INDEX IF NOT EXISTS ix_system_settings_key ON system_settings(key);

CREATE TABLE IF NOT EXISTS meetings (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    meeting_date TIMESTAMPTZ NOT NULL,
    location VARCHAR(255),
    agenda TEXT,
    minutes TEXT,
    status VARCHAR(20) DEFAULT 'scheduled',
    created_by VARCHAR(36),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_meetings_meeting_date ON meetings(meeting_date);
CREATE INDEX IF NOT EXISTS ix_meetings_status ON meetings(status);

CREATE TABLE IF NOT EXISTS meeting_topics (
    id VARCHAR(36) PRIMARY KEY,
    meeting_id VARCHAR(36) NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    resolution TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS meeting_attendance (
    id VARCHAR(36) PRIMARY KEY,
    meeting_id VARCHAR(36) NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    attended BOOLEAN DEFAULT FALSE,
    checked_in_at TIMESTAMPTZ,
    excuse_reason TEXT
);

CREATE TABLE IF NOT EXISTS share_transactions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    transaction_type VARCHAR(20) NOT NULL,
    shares_count DOUBLE PRECISION NOT NULL,
    amount DOUBLE PRECISION NOT NULL,
    share_unit_price DOUBLE PRECISION NOT NULL,
    counterparty_id VARCHAR(36),
    status VARCHAR(20) DEFAULT 'pending',
    approved_at TIMESTAMPTZ,
    approved_by VARCHAR(36),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    notes TEXT
);
CREATE INDEX IF NOT EXISTS ix_share_transactions_user_id ON share_transactions(user_id);

CREATE TABLE IF NOT EXISTS withdrawal_requests (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount DOUBLE PRECISION NOT NULL,
    withdrawal_type VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    notice_date TIMESTAMPTZ DEFAULT NOW(),
    eligible_date TIMESTAMPTZ,
    processed_at TIMESTAMPTZ,
    processed_by VARCHAR(36),
    rejection_reason TEXT,
    bank_account VARCHAR(100),
    bank_name VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_withdrawal_requests_user_id ON withdrawal_requests(user_id);
CREATE INDEX IF NOT EXISTS ix_withdrawal_requests_status ON withdrawal_requests(status);

CREATE TABLE IF NOT EXISTS guarantors (
    id VARCHAR(36) PRIMARY KEY,
    loan_id VARCHAR(36) UNIQUE NOT NULL REFERENCES loans(id) ON DELETE CASCADE,
    guarantor_member_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    guarantor_full_name VARCHAR(255) NOT NULL,
    guarantor_phone VARCHAR(50),
    guarantor_email VARCHAR(255),
    relationship_to_applicant VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending',
    validation_reason TEXT,
    validated_at TIMESTAMPTZ,
    guarantor_credit_score INTEGER,
    guarantor_membership_months INTEGER,
    guarantor_shares_balance DOUBLE PRECISION,
    guarantor_has_completed_loan BOOLEAN,
    recovery_amount_requested DOUBLE PRECISION DEFAULT 0,
    recovery_amount_paid DOUBLE PRECISION DEFAULT 0,
    recovery_notified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_guarantors_loan_id ON guarantors(loan_id);
CREATE INDEX IF NOT EXISTS ix_guarantors_guarantor_member_id ON guarantors(guarantor_member_id);

CREATE TABLE IF NOT EXISTS dividend_records (
    id VARCHAR(36) PRIMARY KEY,
    year INTEGER UNIQUE NOT NULL,
    total_profit DOUBLE PRECISION NOT NULL,
    dividend_pool DOUBLE PRECISION NOT NULL,
    total_shares DOUBLE PRECISION NOT NULL,
    dividend_per_share DOUBLE PRECISION NOT NULL,
    status VARCHAR(20) DEFAULT 'calculated',
    approved_at TIMESTAMPTZ,
    approved_by VARCHAR(36),
    distributed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_dividend_records_year ON dividend_records(year);

CREATE TABLE IF NOT EXISTS member_dividends (
    id VARCHAR(36) PRIMARY KEY,
    dividend_record_id VARCHAR(36) NOT NULL REFERENCES dividend_records(id) ON DELETE CASCADE,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    shares_held DOUBLE PRECISION NOT NULL,
    dividend_amount DOUBLE PRECISION NOT NULL,
    payment_method VARCHAR(50),
    paid_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_member_dividends_user_id ON member_dividends(user_id);

INSERT INTO system_settings (id, key, value, description) VALUES
    (gen_random_uuid()::text, 'minimum_monthly_contribution', '10000', 'Minimum monthly contribution amount in Naira'),
    (gen_random_uuid()::text, 'minimum_contribution_period', '3', 'Minimum contribution period in months before loan eligibility'),
    (gen_random_uuid()::text, 'share_unit', '1000', 'Value of one share unit in Naira'),
    (gen_random_uuid()::text, 'loan_interest_rate', '2', 'Monthly interest rate percentage'),
    (gen_random_uuid()::text, 'liquidity_threshold', '70', 'Minimum liquidity threshold percentage'),
    (gen_random_uuid()::text, 'withdrawal_notice_days', '30', 'Notice period for withdrawal requests'),
    (gen_random_uuid()::text, 'share_exit_notice_days', '60', 'Notice period for share exit requests')
ON CONFLICT (key) DO NOTHING;

SELECT 'Migration completed successfully' AS result;
