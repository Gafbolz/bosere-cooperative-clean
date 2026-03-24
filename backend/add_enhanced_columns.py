"""Add enhanced columns for cooperative business logic

Revision ID: add_enhanced_columns
Revises: 0164410fa044
Create Date: 2026-03-24 18:00:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_enhanced_columns'
down_revision: Union[str, Sequence[str], None] = '0164410fa044'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add enhanced columns to existing tables."""
    
    # ============ USERS TABLE - Add new columns ============
    # Member Status
    op.add_column('users', sa.Column('status', sa.String(20), server_default='PENDING', nullable=True))
    op.create_index('ix_users_status', 'users', ['status'])
    
    # Business/CAC Information
    op.add_column('users', sa.Column('business_name', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('residential_address', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('business_address', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('business_type', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('years_in_operation', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('cac_registration_number', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('cac_certificate_url', sa.String(500), nullable=True))
    op.add_column('users', sa.Column('government_id_url', sa.String(500), nullable=True))
    
    # KYC Status
    op.add_column('users', sa.Column('kyc_status', sa.String(20), server_default='PENDING', nullable=True))
    op.add_column('users', sa.Column('kyc_verified_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('kyc_verified_by', sa.String(36), nullable=True))
    op.add_column('users', sa.Column('admin_note', sa.Text(), nullable=True))
    op.create_index('ix_users_kyc_status', 'users', ['kyc_status'])
    
    # Financial Balances
    op.add_column('users', sa.Column('savings_balance', sa.Float(), server_default='0', nullable=True))
    op.add_column('users', sa.Column('shares_balance', sa.Float(), server_default='0', nullable=True))
    op.add_column('users', sa.Column('locked_collateral', sa.Float(), server_default='0', nullable=True))
    
    # Aggregated Stats
    op.add_column('users', sa.Column('total_contributions', sa.Float(), server_default='0', nullable=True))
    op.add_column('users', sa.Column('total_loans_taken', sa.Float(), server_default='0', nullable=True))
    op.add_column('users', sa.Column('total_loans_repaid', sa.Float(), server_default='0', nullable=True))
    
    # Credit Score
    op.add_column('users', sa.Column('credit_score', sa.Integer(), server_default='50', nullable=True))
    
    # Active Loan Reference
    op.add_column('users', sa.Column('active_loan_id', sa.String(36), nullable=True))
    
    # Join date
    op.add_column('users', sa.Column('join_date', sa.DateTime(timezone=True), nullable=True))
    
    # ============ LOANS TABLE - Add new columns ============
    op.add_column('loans', sa.Column('remaining_balance', sa.Float(), server_default='0', nullable=True))
    op.add_column('loans', sa.Column('guarantor_id', sa.String(36), nullable=True))
    op.add_column('loans', sa.Column('collateral_locked', sa.Float(), server_default='0', nullable=True))
    op.add_column('loans', sa.Column('collateral_released', sa.Boolean(), server_default='false', nullable=True))
    op.add_column('loans', sa.Column('collateral_used_for_recovery', sa.Float(), server_default='0', nullable=True))
    op.add_column('loans', sa.Column('due_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('loans', sa.Column('last_payment_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('loans', sa.Column('days_overdue', sa.Integer(), server_default='0', nullable=True))
    op.add_column('loans', sa.Column('overdue_penalty', sa.Float(), server_default='0', nullable=True))
    op.add_column('loans', sa.Column('recovery_status', sa.String(30), server_default='none', nullable=True))
    op.add_column('loans', sa.Column('meeting_id', sa.String(36), nullable=True))
    op.add_column('loans', sa.Column('defaulted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('loans', sa.Column('approval_note', sa.Text(), nullable=True))
    op.add_column('loans', sa.Column('rejection_reason', sa.Text(), nullable=True))
    
    # ============ CONTRIBUTIONS TABLE - Add new columns ============
    op.add_column('contributions', sa.Column('meeting_id', sa.String(36), nullable=True))
    op.add_column('contributions', sa.Column('rejection_reason', sa.Text(), nullable=True))
    
    # ============ Create new tables ============
    
    # System Settings
    op.create_table('system_settings',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('key', sa.String(100), unique=True, nullable=False),
        sa.Column('value', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', sa.String(36), nullable=True),
    )
    op.create_index('ix_system_settings_key', 'system_settings', ['key'], unique=True)
    
    # Meetings
    op.create_table('meetings',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('meeting_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('agenda', sa.Text(), nullable=True),
        sa.Column('minutes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), server_default='scheduled', nullable=True),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_meetings_meeting_date', 'meetings', ['meeting_date'])
    op.create_index('ix_meetings_status', 'meetings', ['status'])
    
    # Meeting Topics
    op.create_table('meeting_topics',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('meeting_id', sa.String(36), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), server_default='pending', nullable=True),
        sa.Column('resolution', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key('fk_meeting_topics_meeting', 'meeting_topics', 'meetings', ['meeting_id'], ['id'], ondelete='CASCADE')
    
    # Meeting Attendance
    op.create_table('meeting_attendance',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('meeting_id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('attended', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('checked_in_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('excuse_reason', sa.Text(), nullable=True),
    )
    op.create_foreign_key('fk_meeting_attendance_meeting', 'meeting_attendance', 'meetings', ['meeting_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_meeting_attendance_user', 'meeting_attendance', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    
    # Share Transactions
    op.create_table('share_transactions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('transaction_type', sa.String(20), nullable=False),
        sa.Column('shares_count', sa.Float(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('share_unit_price', sa.Float(), nullable=False),
        sa.Column('counterparty_id', sa.String(36), nullable=True),
        sa.Column('status', sa.String(20), server_default='pending', nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_by', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
    )
    op.create_index('ix_share_transactions_user_id', 'share_transactions', ['user_id'])
    op.create_foreign_key('fk_share_transactions_user', 'share_transactions', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    
    # Withdrawal Requests
    op.create_table('withdrawal_requests',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('withdrawal_type', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), server_default='pending', nullable=True),
        sa.Column('notice_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('eligible_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processed_by', sa.String(36), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('bank_account', sa.String(100), nullable=True),
        sa.Column('bank_name', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_withdrawal_requests_user_id', 'withdrawal_requests', ['user_id'])
    op.create_index('ix_withdrawal_requests_status', 'withdrawal_requests', ['status'])
    op.create_foreign_key('fk_withdrawal_requests_user', 'withdrawal_requests', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    
    # Guarantors
    op.create_table('guarantors',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('loan_id', sa.String(36), nullable=False, unique=True),
        sa.Column('guarantor_member_id', sa.String(36), nullable=False),
        sa.Column('guarantor_full_name', sa.String(255), nullable=False),
        sa.Column('guarantor_phone', sa.String(50), nullable=True),
        sa.Column('guarantor_email', sa.String(255), nullable=True),
        sa.Column('relationship_to_applicant', sa.String(100), nullable=True),
        sa.Column('status', sa.String(20), server_default='pending', nullable=True),
        sa.Column('validation_reason', sa.Text(), nullable=True),
        sa.Column('validated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('guarantor_credit_score', sa.Integer(), nullable=True),
        sa.Column('guarantor_membership_months', sa.Integer(), nullable=True),
        sa.Column('guarantor_shares_balance', sa.Float(), nullable=True),
        sa.Column('guarantor_has_completed_loan', sa.Boolean(), nullable=True),
        sa.Column('recovery_amount_requested', sa.Float(), server_default='0', nullable=True),
        sa.Column('recovery_amount_paid', sa.Float(), server_default='0', nullable=True),
        sa.Column('recovery_notified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_guarantors_loan_id', 'guarantors', ['loan_id'])
    op.create_index('ix_guarantors_guarantor_member_id', 'guarantors', ['guarantor_member_id'])
    op.create_foreign_key('fk_guarantors_loan', 'guarantors', 'loans', ['loan_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_guarantors_member', 'guarantors', 'users', ['guarantor_member_id'], ['id'], ondelete='CASCADE')
    
    # Dividend Records
    op.create_table('dividend_records',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('total_profit', sa.Float(), nullable=False),
        sa.Column('dividend_pool', sa.Float(), nullable=False),
        sa.Column('total_shares', sa.Float(), nullable=False),
        sa.Column('dividend_per_share', sa.Float(), nullable=False),
        sa.Column('status', sa.String(20), server_default='calculated', nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_by', sa.String(36), nullable=True),
        sa.Column('distributed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_dividend_records_year', 'dividend_records', ['year'], unique=True)
    
    # Member Dividends
    op.create_table('member_dividends',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('dividend_record_id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('shares_held', sa.Float(), nullable=False),
        sa.Column('dividend_amount', sa.Float(), nullable=False),
        sa.Column('payment_method', sa.String(50), nullable=True),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_member_dividends_user_id', 'member_dividends', ['user_id'])
    op.create_foreign_key('fk_member_dividends_dividend', 'member_dividends', 'dividend_records', ['dividend_record_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_member_dividends_user', 'member_dividends', 'users', ['user_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    """Remove enhanced columns and tables."""
    
    # Drop new tables in reverse order
    op.drop_table('member_dividends')
    op.drop_table('dividend_records')
    op.drop_table('guarantors')
    op.drop_table('withdrawal_requests')
    op.drop_table('share_transactions')
    op.drop_table('meeting_attendance')
    op.drop_table('meeting_topics')
    op.drop_table('meetings')
    op.drop_table('system_settings')
    
    # Remove columns from contributions
    op.drop_column('contributions', 'rejection_reason')
    op.drop_column('contributions', 'meeting_id')
    
    # Remove columns from loans
    op.drop_column('loans', 'rejection_reason')
    op.drop_column('loans', 'approval_note')
    op.drop_column('loans', 'defaulted_at')
    op.drop_column('loans', 'meeting_id')
    op.drop_column('loans', 'recovery_status')
    op.drop_column('loans', 'overdue_penalty')
    op.drop_column('loans', 'days_overdue')
    op.drop_column('loans', 'last_payment_date')
    op.drop_column('loans', 'due_date')
    op.drop_column('loans', 'collateral_used_for_recovery')
    op.drop_column('loans', 'collateral_released')
    op.drop_column('loans', 'collateral_locked')
    op.drop_column('loans', 'guarantor_id')
    op.drop_column('loans', 'remaining_balance')
    
    # Remove columns from users
    op.drop_index('ix_users_kyc_status', 'users')
    op.drop_index('ix_users_status', 'users')
    op.drop_column('users', 'join_date')
    op.drop_column('users', 'active_loan_id')
    op.drop_column('users', 'credit_score')
    op.drop_column('users', 'total_loans_repaid')
    op.drop_column('users', 'total_loans_taken')
    op.drop_column('users', 'total_contributions')
    op.drop_column('users', 'locked_collateral')
    op.drop_column('users', 'shares_balance')
    op.drop_column('users', 'savings_balance')
    op.drop_column('users', 'admin_note')
    op.drop_column('users', 'kyc_verified_by')
    op.drop_column('users', 'kyc_verified_at')
    op.drop_column('users', 'kyc_status')
    op.drop_column('users', 'government_id_url')
    op.drop_column('users', 'cac_certificate_url')
    op.drop_column('users', 'cac_registration_number')
    op.drop_column('users', 'years_in_operation')
    op.drop_column('users', 'business_type')
    op.drop_column('users', 'business_address')
    op.drop_column('users', 'residential_address')
    op.drop_column('users', 'business_name')
    op.drop_column('users', 'status')
