from sqlalchemy import Column, String, Float, Boolean, DateTime, Integer, ForeignKey, Text, Enum as SQLEnum, Date, JSON
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timezone, date
import uuid
import enum

def generate_uuid():
    return str(uuid.uuid4())

# ============================================
# ENUMS
# ============================================

class UserRole(str, enum.Enum):
    MEMBER = "MEMBER"
    ADMIN = "ADMIN"

class MemberStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"

class KYCStatus(str, enum.Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"

class ContributionStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class LoanStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    DEFAULTED = "DEFAULTED"

class GuarantorStatus(str, enum.Enum):
    PENDING = "pending"
    VALIDATED = "validated"
    REJECTED = "rejected"

class ShareTransactionType(str, enum.Enum):
    PURCHASE = "purchase"
    SALE = "sale"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    DIVIDEND = "dividend"

class WithdrawalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"

class RecoveryStatus(str, enum.Enum):
    NONE = "none"
    COLLATERAL_APPLIED = "collateral_applied"
    GUARANTOR_NOTIFIED = "guarantor_notified"
    RECOVERED = "recovered"
    WRITTEN_OFF = "written_off"

# ============================================
# SYSTEM SETTINGS
# ============================================

class SystemSettings(Base):
    __tablename__ = 'system_settings'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    updated_by = Column(String(36), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

# Default settings to be seeded:
# - minimum_monthly_contribution: 10000
# - minimum_contribution_period: 3 (months)
# - share_unit: 1000
# - loan_interest_rate: 2 (% monthly)
# - liquidity_threshold: 70 (%)
# - withdrawal_notice_days: 30
# - share_exit_notice_days: 60

# ============================================
# USER / MEMBER MODEL (Enhanced)
# ============================================

class User(Base):
    __tablename__ = 'users'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    supabase_user_id = Column(String(255), unique=True, nullable=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    # Use String instead of Enum for PostgreSQL compatibility (Supabase)
    role = Column(String(20), default="MEMBER", nullable=False)
    
    # Member Status - use String for portability
    status = Column(String(20), default="PENDING", index=True)
    is_approved = Column(Boolean, default=False, index=True)  # Keep for backward compatibility
    
    # Business/CAC Information
    business_name = Column(String(255), nullable=True)
    residential_address = Column(Text, nullable=True)
    business_address = Column(Text, nullable=True)
    business_type = Column(String(100), nullable=True)
    years_in_operation = Column(Integer, nullable=True)
    cac_registration_number = Column(String(100), nullable=True)
    cac_certificate_url = Column(String(500), nullable=True)
    government_id_url = Column(String(500), nullable=True)
    
    # KYC Status - use String for portability
    kyc_status = Column(String(20), default="PENDING", index=True)
    kyc_verified_at = Column(DateTime(timezone=True), nullable=True)
    kyc_verified_by = Column(String(36), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    admin_note = Column(Text, nullable=True)
    
    # Financial Balances
    savings_balance = Column(Float, default=0.0)  # Total approved contributions
    shares_balance = Column(Float, default=0.0)  # Number of shares owned
    locked_collateral = Column(Float, default=0.0)  # Amount locked for active loans
    
    # Aggregated Stats
    total_contributions = Column(Float, default=0.0)  # All-time approved contributions
    total_loans_taken = Column(Float, default=0.0)  # All-time loan amounts
    total_loans_repaid = Column(Float, default=0.0)  # All-time repayments
    
    # Credit Score (0-100, default 50)
    credit_score = Column(Integer, default=50)
    
    # Active Loan Reference
    active_loan_id = Column(String(36), nullable=True)  # Currently active loan
    
    # Timestamps
    join_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    contributions = relationship('Contribution', back_populates='user', foreign_keys='Contribution.user_id', cascade='all, delete-orphan')
    loans = relationship('Loan', back_populates='user', foreign_keys='Loan.user_id', cascade='all, delete-orphan')
    notifications = relationship('Notification', back_populates='user', cascade='all, delete-orphan')
    share_transactions = relationship('ShareTransaction', back_populates='user', foreign_keys='ShareTransaction.user_id', cascade='all, delete-orphan')
    withdrawal_requests = relationship('WithdrawalRequest', back_populates='user', foreign_keys='WithdrawalRequest.user_id', cascade='all, delete-orphan')
    
    # Helper property for membership duration
    @property
    def membership_duration_months(self):
        if not self.join_date:
            return 0
        delta = datetime.now(timezone.utc) - self.join_date
        return max(0, delta.days // 30)
    
    @property
    def available_savings(self):
        """Savings minus locked collateral"""
        return max(0, self.savings_balance - self.locked_collateral)

# ============================================
# CONTRIBUTION MODEL (Enhanced)
# ============================================

class Contribution(Base):
    __tablename__ = 'contributions'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default="PENDING", index=True)
    
    # Meeting reference (if contribution made during meeting)
    meeting_id = Column(String(36), ForeignKey('meetings.id', ondelete='SET NULL'), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(String(36), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Relationships
    user = relationship('User', back_populates='contributions', foreign_keys=[user_id])
    approver = relationship('User', foreign_keys=[approved_by])
    meeting = relationship('Meeting', back_populates='contributions')

# ============================================
# SHARES MODEL
# ============================================

class ShareTransaction(Base):
    __tablename__ = 'share_transactions'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    transaction_type = Column(String(20), nullable=False)
    shares_count = Column(Float, nullable=False)  # Number of shares
    amount = Column(Float, nullable=False)  # Monetary value
    share_unit_price = Column(Float, nullable=False)  # Price per share at time of transaction
    
    # For transfers
    counterparty_id = Column(String(36), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    # Status and approval
    status = Column(String(20), default='pending', index=True)  # pending, approved, rejected, completed
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(String(36), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    notes = Column(Text, nullable=True)
    
    # Relationships
    user = relationship('User', back_populates='share_transactions', foreign_keys=[user_id])
    counterparty = relationship('User', foreign_keys=[counterparty_id])

# ============================================
# WITHDRAWAL REQUEST MODEL
# ============================================

class WithdrawalRequest(Base):
    __tablename__ = 'withdrawal_requests'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    withdrawal_type = Column(String(20), nullable=False)  # savings, shares, emergency
    status = Column(String(20), default="pending", index=True)
    
    # Notice period
    notice_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    eligible_date = Column(DateTime(timezone=True), nullable=True)  # When withdrawal becomes eligible
    
    # Processing
    processed_at = Column(DateTime(timezone=True), nullable=True)
    processed_by = Column(String(36), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship('User', back_populates='withdrawal_requests', foreign_keys=[user_id])

# ============================================
# LOAN MODEL (Enhanced)
# ============================================

class Loan(Base):
    __tablename__ = 'loans'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Loan Details
    amount = Column(Float, nullable=False)
    duration_months = Column(Integer, nullable=False)
    interest_rate = Column(Float, default=2.0)  # Monthly interest rate (2% default)
    monthly_payment = Column(Float, nullable=False)
    total_repayment = Column(Float, nullable=False)
    remaining_balance = Column(Float, nullable=False)  # Current outstanding balance
    purpose = Column(Text, nullable=True)
    
    # Status
    status = Column(String(20), default="PENDING", index=True)
    
    # Guarantor
    guarantor_id = Column(String(36), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    # Collateral
    collateral_locked = Column(Float, default=0.0)  # Amount locked from borrower's savings
    collateral_released = Column(Boolean, default=False)
    collateral_used_for_recovery = Column(Float, default=0.0)
    
    # Default tracking
    due_date = Column(DateTime(timezone=True), nullable=True)  # Next payment due
    last_payment_date = Column(DateTime(timezone=True), nullable=True)
    days_overdue = Column(Integer, default=0)
    overdue_penalty = Column(Float, default=0.0)
    recovery_status = Column(String(30), default="none")
    
    # Meeting reference
    meeting_id = Column(String(36), ForeignKey('meetings.id', ondelete='SET NULL'), nullable=True)
    
    # Timestamps and approval
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(String(36), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    defaulted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Admin notes
    approval_note = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Relationships
    user = relationship('User', back_populates='loans', foreign_keys=[user_id])
    guarantor = relationship('User', foreign_keys=[guarantor_id])
    approver = relationship('User', foreign_keys=[approved_by])
    repayments = relationship('Repayment', back_populates='loan', cascade='all, delete-orphan')
    guarantor_record = relationship('Guarantor', back_populates='loan', uselist=False)
    meeting = relationship('Meeting', back_populates='loans')

# ============================================
# GUARANTOR MODEL
# ============================================

class Guarantor(Base):
    __tablename__ = 'guarantors'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    loan_id = Column(String(36), ForeignKey('loans.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    
    # Guarantor member reference
    guarantor_member_id = Column(String(36), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Details captured at time of guarantee
    guarantor_full_name = Column(String(255), nullable=False)
    guarantor_phone = Column(String(50), nullable=True)
    guarantor_email = Column(String(255), nullable=True)
    relationship_to_applicant = Column(String(100), nullable=True)
    
    # Validation
    status = Column(String(20), default="pending", index=True)
    validation_reason = Column(Text, nullable=True)  # Why valid or invalid
    validated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Guarantor's stats at time of guarantee (snapshot)
    guarantor_credit_score = Column(Integer, nullable=True)
    guarantor_membership_months = Column(Integer, nullable=True)
    guarantor_shares_balance = Column(Float, nullable=True)
    guarantor_has_completed_loan = Column(Boolean, nullable=True)
    
    # Recovery tracking
    liability_amount = Column(Float, default=0.0)  # Amount guarantor is liable for
    liability_paid = Column(Float, default=0.0)  # Amount guarantor has paid
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    loan = relationship('Loan', back_populates='guarantor_record')
    guarantor_member = relationship('User', foreign_keys=[guarantor_member_id])

# ============================================
# REPAYMENT MODEL (Enhanced)
# ============================================

class Repayment(Base):
    __tablename__ = 'repayments'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    loan_id = Column(String(36), ForeignKey('loans.id', ondelete='CASCADE'), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    
    # Payment details
    principal_paid = Column(Float, default=0.0)
    interest_paid = Column(Float, default=0.0)
    penalty_paid = Column(Float, default=0.0)
    
    # Balance after this payment
    remaining_balance_after = Column(Float, nullable=True)
    
    # Meeting reference
    meeting_id = Column(String(36), ForeignKey('meetings.id', ondelete='SET NULL'), nullable=True)
    
    # Source of payment
    payment_source = Column(String(50), default='direct')  # direct, collateral, guarantor
    
    # Timestamps
    payment_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    notes = Column(Text, nullable=True)
    recorded_by = Column(String(36), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    # Relationships
    loan = relationship('Loan', back_populates='repayments')
    meeting = relationship('Meeting', back_populates='repayments')

# ============================================
# MEETING MODEL
# ============================================

class Meeting(Base):
    __tablename__ = 'meetings'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    meeting_date = Column(Date, nullable=False, index=True)
    meeting_time = Column(String(20), default='10:00 AM')
    location = Column(String(255), nullable=True)
    
    # Agenda and notes
    agenda = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Status
    status = Column(String(20), default='scheduled')  # scheduled, in_progress, completed, cancelled
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_by = Column(String(36), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    attendance = relationship('MeetingAttendance', back_populates='meeting', cascade='all, delete-orphan')
    topics = relationship('MeetingTopic', back_populates='meeting', cascade='all, delete-orphan')
    contributions = relationship('Contribution', back_populates='meeting')
    loans = relationship('Loan', back_populates='meeting')
    repayments = relationship('Repayment', back_populates='meeting')

class MeetingAttendance(Base):
    __tablename__ = 'meeting_attendance'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    meeting_id = Column(String(36), ForeignKey('meetings.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    attended = Column(Boolean, default=False)
    arrival_time = Column(String(20), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    marked_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    marked_by = Column(String(36), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    # Relationships
    meeting = relationship('Meeting', back_populates='attendance')
    user = relationship('User', foreign_keys=[user_id])

class MeetingTopic(Base):
    __tablename__ = 'meeting_topics'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    meeting_id = Column(String(36), ForeignKey('meetings.id', ondelete='CASCADE'), nullable=False, index=True)
    submitted_by = Column(String(36), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    topic_type = Column(String(50), nullable=False)  # enquiry, loan_request, complaint, suggestion, other
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Status
    status = Column(String(20), default='pending')  # pending, discussed, resolved, deferred
    resolution = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    meeting = relationship('Meeting', back_populates='topics')
    submitter = relationship('User', foreign_keys=[submitted_by])

# ============================================
# NOTIFICATION MODEL (Unchanged)
# ============================================

class Notification(Base):
    __tablename__ = 'notifications'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), nullable=False)
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship('User', back_populates='notifications')

# ============================================
# DIVIDEND RECORD (For future use)
# ============================================

class DividendRecord(Base):
    __tablename__ = 'dividend_records'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    year = Column(Integer, nullable=False, index=True)
    
    # Financial summary
    total_system_profit = Column(Float, default=0.0)
    retained_profit = Column(Float, default=0.0)
    distributable_profit = Column(Float, default=0.0)
    total_shares_in_system = Column(Float, default=0.0)
    dividend_per_share = Column(Float, default=0.0)
    
    # Status
    status = Column(String(20), default='draft')  # draft, approved, distributed
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    approved_at = Column(DateTime(timezone=True), nullable=True)
    distributed_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(String(36), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

class MemberDividend(Base):
    __tablename__ = 'member_dividends'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    dividend_record_id = Column(String(36), ForeignKey('dividend_records.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    shares_held = Column(Float, nullable=False)
    share_ratio = Column(Float, nullable=False)  # Member's shares / total shares
    dividend_amount = Column(Float, nullable=False)
    
    # Status
    paid = Column(Boolean, default=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
