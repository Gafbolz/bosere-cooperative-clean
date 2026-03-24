"""
Bosere Cooperative - Business Logic Services

This module contains all the core business logic for:
- Loan eligibility calculation
- Guarantor validation
- Collateral management
- Credit score system
- Liquidity control
- Default/recovery flow
- Meeting scheduling
"""

from datetime import datetime, timezone, timedelta, date
from sqlalchemy import select, func, and_, or_, cast, String
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, List, Tuple
import calendar

from models import (
    User, Contribution, Loan, Repayment, Guarantor, ShareTransaction,
    WithdrawalRequest, Meeting, MeetingAttendance, Notification, SystemSettings,
    UserRole, MemberStatus, KYCStatus, ContributionStatus, LoanStatus,
    GuarantorStatus, RecoveryStatus
)

# Helper to cast enum column to text for comparisons
def enum_text(column):
    """Cast an enum column to text for comparison with strings"""
    return cast(column, String)

def get_status_value(status):
    """Safely get string value from status (handles both enum and string), normalized to uppercase"""
    if status is None:
        return None
    if hasattr(status, 'value'):
        return str(status.value).upper()
    return str(status).upper()


# ============================================
# SYSTEM SETTINGS SERVICE
# ============================================

class SettingsService:
    """Manage system-wide configurable settings"""
    
    # Default values
    DEFAULTS = {
        'minimum_monthly_contribution': '10000',
        'minimum_contribution_period': '3',  # months
        'share_unit': '1000',  # ₦1,000 per share
        'loan_interest_rate': '2',  # % monthly
        'liquidity_threshold': '70',  # %
        'withdrawal_notice_days': '30',
        'share_exit_notice_days': '60',
        'min_guarantor_membership_months': '6',
        'min_guarantor_shares': '10',  # minimum shares
        'min_guarantor_credit_score': '40',
        # TEST MODE settings
        'test_mode': 'false',  # Enable to bypass eligibility rules for testing
        'test_user_override': '',  # User ID that can bypass rules even when test_mode is false
    }
    
    @classmethod
    async def get_setting(cls, db: AsyncSession, key: str) -> str:
        """Get a setting value, returning default if not found"""
        result = await db.execute(
            select(SystemSettings).filter(SystemSettings.key == key)
        )
        setting = result.scalar_one_or_none()
        if setting:
            return setting.value
        return cls.DEFAULTS.get(key, '')
    
    @classmethod
    async def get_bool(cls, db: AsyncSession, key: str) -> bool:
        """Get a setting as boolean"""
        value = await cls.get_setting(db, key)
        return value.lower() in ('true', '1', 'yes', 'on')
    
    @classmethod
    async def get_float(cls, db: AsyncSession, key: str) -> float:
        """Get a setting as float"""
        value = await cls.get_setting(db, key)
        try:
            return float(value)
        except (ValueError, TypeError):
            return float(cls.DEFAULTS.get(key, 0))
    
    @classmethod
    async def get_int(cls, db: AsyncSession, key: str) -> int:
        """Get a setting as int"""
        value = await cls.get_setting(db, key)
        try:
            return int(value)
        except (ValueError, TypeError):
            return int(cls.DEFAULTS.get(key, 0))
    
    @classmethod
    async def set_setting(cls, db: AsyncSession, key: str, value: str, admin_id: str = None):
        """Set a setting value"""
        from sqlalchemy import text
        
        result = await db.execute(
            select(SystemSettings).filter(SystemSettings.key == key)
        )
        setting = result.scalar_one_or_none()
        
        # If admin_id is 'dev' or None, don't set updated_by (avoid FK violation)
        use_admin_id = admin_id if admin_id and admin_id != 'dev' else None
        
        if setting:
            setting.value = value
            if use_admin_id:
                setting.updated_by = use_admin_id
        else:
            # Use raw SQL to avoid ORM FK validation issues
            import uuid
            setting_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            await db.execute(
                text("""
                    INSERT INTO system_settings (id, key, value, description, updated_at, updated_by)
                    VALUES (:id, :key, :value, :description, :updated_at, :updated_by)
                    ON CONFLICT (key) DO UPDATE SET value = :value, updated_at = :updated_at
                """),
                {
                    "id": setting_id,
                    "key": key,
                    "value": value,
                    "description": f"Setting: {key}",
                    "updated_at": now,
                    "updated_by": use_admin_id
                }
            )
        
        await db.commit()
        return {'key': key, 'value': value}
    
    @classmethod
    async def seed_defaults(cls, db: AsyncSession):
        """Seed default settings if they don't exist"""
        for key, value in cls.DEFAULTS.items():
            result = await db.execute(
                select(SystemSettings).filter(SystemSettings.key == key)
            )
            if not result.scalar_one_or_none():
                setting = SystemSettings(key=key, value=value, description=f"Default: {value}")
                db.add(setting)
        await db.commit()


# ============================================
# LOAN ELIGIBILITY SERVICE
# ============================================

class LoanEligibilityService:
    """Calculate loan eligibility based on cooperative rules"""
    
    @classmethod
    async def is_test_mode_enabled(cls, db: AsyncSession, user_id: str = None) -> bool:
        """
        Check if test mode is enabled for loan eligibility bypass.
        Returns True if:
        - test_mode setting is 'true', OR
        - user_id matches test_user_override setting
        """
        # Check global test mode
        test_mode = await SettingsService.get_bool(db, 'test_mode')
        if test_mode:
            return True
        
        # Check user-specific override
        if user_id:
            override_user = await SettingsService.get_setting(db, 'test_user_override')
            if override_user and override_user == user_id:
                return True
        
        return False
    
    @classmethod
    async def check_eligibility(cls, db: AsyncSession, user: User) -> Dict:
        """
        Check if a member is eligible for a loan and calculate their limit.
        
        Returns a dict with:
        - eligible: bool
        - loan_limit: float
        - reasons: list of reasons if not eligible
        - tier: the eligibility tier (1x, 2x, 3x)
        - test_mode: whether test mode is active
        """
        reasons = []
        
        # Check if test mode is enabled for this user
        test_mode_active = await cls.is_test_mode_enabled(db, user.id)
        
        if test_mode_active:
            # TEST MODE: Bypass all eligibility checks
            import logging
            logging.info(f"[TEST MODE] Bypassing eligibility checks for user {user.id}")
            
            return {
                'eligible': True,
                'loan_limit': 1000000,  # ₦1M test limit
                'reasons': [],
                'tier': 3,
                'multiplier': 3,
                'membership_months': 12,
                'approved_contributions': 10,
                'savings_balance': user.savings_balance or 100000,
                'kyc_status': 'VERIFIED',
                'has_active_loan': bool(user.active_loan_id),
                'test_mode': True,
                'test_mode_note': 'Eligibility bypassed - TEST MODE active'
            }
        
        # PRODUCTION MODE: Enforce all rules strictly
        
        # 1. Check if member is active
        if get_status_value(user.status) != "ACTIVE":
            reasons.append("Member account is not active")
        
        # 2. Check KYC status
        if get_status_value(user.kyc_status) != "VERIFIED":
            reasons.append("CAC/KYC verification is not complete")
        
        # 3. Check for active loan
        if user.active_loan_id:
            reasons.append("Member already has an active loan")
        
        # 4. Check contribution count (minimum 3 approved)
        contrib_result = await db.execute(
            select(func.count(Contribution.id))
            .filter(
                Contribution.user_id == user.id,
                enum_text(Contribution.status) == "APPROVED"
            )
        )
        approved_contributions = contrib_result.scalar() or 0
        
        min_contributions = await SettingsService.get_int(db, 'minimum_contribution_period')
        if approved_contributions < min_contributions:
            reasons.append(f"Insufficient contribution history (need at least {min_contributions} approved contributions)")
        
        # 5. Check membership duration
        membership_months = user.membership_duration_months
        
        if membership_months < 3:
            reasons.append("Membership duration is less than 3 months")
            tier = 0
            multiplier = 0
        elif membership_months < 6:
            tier = 1
            multiplier = 1
        elif membership_months < 12:
            tier = 2
            multiplier = 2
        else:
            tier = 3
            multiplier = 3
        
        # Calculate loan limit based on savings
        loan_limit = user.savings_balance * multiplier if multiplier > 0 else 0
        
        # Check if eligible
        eligible = len(reasons) == 0 and loan_limit > 0
        
        return {
            'eligible': eligible,
            'loan_limit': loan_limit,
            'reasons': reasons,
            'tier': tier,
            'multiplier': multiplier,
            'membership_months': membership_months,
            'approved_contributions': approved_contributions,
            'savings_balance': user.savings_balance,
            'kyc_status': get_status_value(user.kyc_status) if user.kyc_status else 'PENDING',
            'has_active_loan': bool(user.active_loan_id),
            'test_mode': False
        }
    
    @classmethod
    async def validate_loan_request(cls, db: AsyncSession, user: User, amount: float, guarantor_id: str = None) -> Dict:
        """
        Validate a loan request including amount, guarantor, and liquidity checks.
        In TEST MODE, bypasses all validation.
        """
        # Check if test mode is enabled
        test_mode_active = await cls.is_test_mode_enabled(db, user.id)
        
        if test_mode_active:
            import logging
            logging.info(f"[TEST MODE] Bypassing loan validation for user {user.id}, amount: {amount}")
            
            return {
                'valid': True,
                'reasons': [],
                'eligibility': {
                    'eligible': True,
                    'loan_limit': 1000000,
                    'tier': 3,
                    'test_mode': True
                },
                'liquidity': {'can_approve': True, 'test_mode': True},
                'test_mode': True,
                'test_mode_note': 'Validation bypassed - TEST MODE active'
            }
        
        # PRODUCTION MODE: Full validation
        eligibility = await cls.check_eligibility(db, user)
        
        if not eligibility['eligible']:
            return {
                'valid': False,
                'reasons': eligibility['reasons'],
                'eligibility': eligibility,
                'test_mode': False
            }
        
        validation_issues = []
        
        # Check if amount exceeds limit
        if amount > eligibility['loan_limit']:
            validation_issues.append(f"Requested amount (₦{amount:,.2f}) exceeds loan limit (₦{eligibility['loan_limit']:,.2f})")
        
        # Check liquidity
        liquidity_check = await LiquidityService.check_loan_approval(db, amount)
        if not liquidity_check['can_approve']:
            validation_issues.append(liquidity_check['reason'])
        
        # Validate guarantor if provided
        if guarantor_id:
            guarantor_validation = await GuarantorService.validate_guarantor(db, guarantor_id, user.id)
            if not guarantor_validation['valid']:
                validation_issues.extend(guarantor_validation['reasons'])
        else:
            validation_issues.append("Guarantor is required for loan application")
        
        return {
            'valid': len(validation_issues) == 0,
            'reasons': validation_issues,
            'eligibility': eligibility,
            'liquidity': liquidity_check,
            'test_mode': False
        }


# ============================================
# GUARANTOR SERVICE
# ============================================

class GuarantorService:
    """Validate and manage loan guarantors"""
    
    @classmethod
    async def validate_guarantor(cls, db: AsyncSession, guarantor_id: str, applicant_id: str) -> Dict:
        """
        Validate if a member can act as guarantor.
        
        Requirements:
        - Active member with 6+ months membership
        - Good credit score (40+)
        - Minimum shares balance
        - Has completed at least one loan
        - Not suspended
        - Not in default
        - Not the applicant themselves
        """
        reasons = []
        
        # Get guarantor
        result = await db.execute(
            select(User).filter(User.id == guarantor_id)
        )
        guarantor = result.scalar_one_or_none()
        
        if not guarantor:
            return {'valid': False, 'reasons': ['Guarantor not found'], 'guarantor': None}
        
        # Can't guarantee own loan
        if guarantor_id == applicant_id:
            reasons.append("Cannot be your own guarantor")
        
        # Must be active
        if guarantor.status != "ACTIVE":
            reasons.append("Guarantor is not an active member")
        
        # Check membership duration
        min_months = await SettingsService.get_int(db, 'min_guarantor_membership_months')
        if guarantor.membership_duration_months < min_months:
            reasons.append(f"Guarantor must have at least {min_months} months membership")
        
        # Check credit score
        min_score = await SettingsService.get_int(db, 'min_guarantor_credit_score')
        if guarantor.credit_score < min_score:
            reasons.append(f"Guarantor credit score ({guarantor.credit_score}) is below minimum ({min_score})")
        
        # Check shares balance
        min_shares = await SettingsService.get_float(db, 'min_guarantor_shares')
        if guarantor.shares_balance < min_shares:
            reasons.append(f"Guarantor must have at least {min_shares} shares")
        
        # Check if guarantor has completed at least one loan
        completed_loans = await db.execute(
            select(func.count(Loan.id))
            .filter(
                Loan.user_id == guarantor_id,
                enum_text(Loan.status) == "COMPLETED"
            )
        )
        if (completed_loans.scalar() or 0) == 0:
            reasons.append("Guarantor must have successfully repaid at least one loan")
        
        # Check for default
        defaulted_loans = await db.execute(
            select(func.count(Loan.id))
            .filter(
                Loan.user_id == guarantor_id,
                enum_text(Loan.status) == "DEFAULTED"
            )
        )
        if (defaulted_loans.scalar() or 0) > 0:
            reasons.append("Guarantor has a history of loan default")
        
        # Check if already guaranteeing another active loan
        active_guarantees = await db.execute(
            select(func.count(Guarantor.id))
            .join(Loan, Guarantor.loan_id == Loan.id)
            .filter(
                Guarantor.guarantor_member_id == guarantor_id,
                enum_text(Loan.status).in_(["PENDING", "APPROVED", "ACTIVE"])
            )
        )
        if (active_guarantees.scalar() or 0) > 0:
            reasons.append("Guarantor is already guaranteeing another active loan")
        
        return {
            'valid': len(reasons) == 0,
            'reasons': reasons,
            'guarantor': {
                'id': guarantor.id,
                'full_name': guarantor.full_name,
                'phone': guarantor.phone,
                'email': guarantor.email,
                'credit_score': guarantor.credit_score,
                'membership_months': guarantor.membership_duration_months,
                'shares_balance': guarantor.shares_balance
            } if guarantor else None
        }
    
    @classmethod
    async def create_guarantor_record(cls, db: AsyncSession, loan_id: str, guarantor_id: str, 
                                      relationship: str = None) -> Guarantor:
        """Create a guarantor record for a loan"""
        result = await db.execute(select(User).filter(User.id == guarantor_id))
        guarantor = result.scalar_one_or_none()
        
        if not guarantor:
            raise ValueError("Guarantor not found")
        
        # Check completed loans
        completed_result = await db.execute(
            select(func.count(Loan.id))
            .filter(Loan.user_id == guarantor_id, enum_text(Loan.status) == "COMPLETED")
        )
        
        record = Guarantor(
            loan_id=loan_id,
            guarantor_member_id=guarantor_id,
            guarantor_full_name=guarantor.full_name,
            guarantor_phone=guarantor.phone,
            guarantor_email=guarantor.email,
            relationship_to_applicant=relationship,
            status="validated",
            guarantor_credit_score=guarantor.credit_score,
            guarantor_membership_months=guarantor.membership_duration_months,
            guarantor_shares_balance=guarantor.shares_balance,
            guarantor_has_completed_loan=(completed_result.scalar() or 0) > 0,
            validated_at=datetime.now(timezone.utc)
        )
        
        db.add(record)
        return record


# ============================================
# COLLATERAL SERVICE
# ============================================

class CollateralService:
    """Manage loan collateral (locked savings)"""
    
    @classmethod
    async def lock_collateral(cls, db: AsyncSession, user_id: str, loan_id: str, amount: float) -> bool:
        """Lock a portion of user's savings as collateral for a loan"""
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            return False
        
        # Check if user has enough available savings
        available = user.savings_balance - user.locked_collateral
        if available < amount:
            return False
        
        # Lock the collateral
        user.locked_collateral += amount
        
        # Update loan
        loan_result = await db.execute(select(Loan).filter(Loan.id == loan_id))
        loan = loan_result.scalar_one_or_none()
        if loan:
            loan.collateral_locked = amount
        
        await db.commit()
        return True
    
    @classmethod
    async def release_collateral(cls, db: AsyncSession, loan_id: str) -> bool:
        """Release collateral when loan is fully repaid"""
        result = await db.execute(select(Loan).filter(Loan.id == loan_id))
        loan = result.scalar_one_or_none()
        
        if not loan or loan.collateral_released:
            return False
        
        # Get user and release their locked collateral
        user_result = await db.execute(select(User).filter(User.id == loan.user_id))
        user = user_result.scalar_one_or_none()
        
        if user:
            user.locked_collateral = max(0, user.locked_collateral - loan.collateral_locked)
        
        loan.collateral_released = True
        await db.commit()
        return True
    
    @classmethod
    async def apply_collateral_for_recovery(cls, db: AsyncSession, loan_id: str, amount: float) -> float:
        """Apply locked collateral to recover defaulted loan amount"""
        result = await db.execute(select(Loan).filter(Loan.id == loan_id))
        loan = result.scalar_one_or_none()
        
        if not loan:
            return 0
        
        # Calculate how much collateral can be applied
        available_collateral = loan.collateral_locked - loan.collateral_used_for_recovery
        amount_to_apply = min(amount, available_collateral)
        
        if amount_to_apply <= 0:
            return 0
        
        # Update loan
        loan.collateral_used_for_recovery += amount_to_apply
        loan.remaining_balance -= amount_to_apply
        loan.recovery_status = "collateral_applied"
        
        # Update user's balances
        user_result = await db.execute(select(User).filter(User.id == loan.user_id))
        user = user_result.scalar_one_or_none()
        
        if user:
            user.locked_collateral = max(0, user.locked_collateral - amount_to_apply)
            user.savings_balance = max(0, user.savings_balance - amount_to_apply)
        
        # Create a repayment record
        repayment = Repayment(
            loan_id=loan_id,
            amount=amount_to_apply,
            payment_source='collateral',
            remaining_balance_after=loan.remaining_balance,
            notes='Collateral applied for loan recovery'
        )
        db.add(repayment)
        
        await db.commit()
        return amount_to_apply


# ============================================
# CREDIT SCORE SERVICE
# ============================================

class CreditScoreService:
    """Manage member credit scores"""
    
    BASE_SCORE = 50
    
    # Score adjustments
    FULL_REPAYMENT_BONUS = 10
    CONSISTENT_CONTRIBUTION_BONUS = 5
    LATE_PAYMENT_PENALTY = -10
    DEFAULT_PENALTY = -20
    
    @classmethod
    async def update_score(cls, db: AsyncSession, user_id: str, adjustment: int, reason: str) -> int:
        """Update a user's credit score"""
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            return 0
        
        old_score = user.credit_score
        new_score = max(0, min(100, old_score + adjustment))
        user.credit_score = new_score
        
        await db.commit()
        return new_score
    
    @classmethod
    async def on_loan_completed(cls, db: AsyncSession, user_id: str) -> int:
        """Credit score bonus for completing a loan"""
        return await cls.update_score(db, user_id, cls.FULL_REPAYMENT_BONUS, "Loan fully repaid")
    
    @classmethod
    async def on_late_payment(cls, db: AsyncSession, user_id: str) -> int:
        """Credit score penalty for late payment"""
        return await cls.update_score(db, user_id, cls.LATE_PAYMENT_PENALTY, "Late loan payment")
    
    @classmethod
    async def on_default(cls, db: AsyncSession, user_id: str) -> int:
        """Credit score penalty for loan default"""
        return await cls.update_score(db, user_id, cls.DEFAULT_PENALTY, "Loan default")
    
    @classmethod
    async def on_consistent_contribution(cls, db: AsyncSession, user_id: str) -> int:
        """Credit score bonus for consistent monthly contributions"""
        return await cls.update_score(db, user_id, cls.CONSISTENT_CONTRIBUTION_BONUS, "Consistent contribution")


# ============================================
# LIQUIDITY SERVICE
# ============================================

class LiquidityService:
    """Monitor and control cooperative liquidity"""
    
    @classmethod
    async def get_liquidity_status(cls, db: AsyncSession) -> Dict:
        """Get current liquidity status of the cooperative"""
        
        # Total approved savings in system
        savings_result = await db.execute(
            select(func.coalesce(func.sum(User.savings_balance), 0))
            .filter(User.role == "MEMBER")
        )
        total_funds = savings_result.scalar() or 0
        
        # Total active loan amounts
        loans_result = await db.execute(
            select(func.coalesce(func.sum(Loan.remaining_balance), 0))
            .filter(enum_text(Loan.status).in_(["APPROVED", "ACTIVE"]))
        )
        total_active_loans = loans_result.scalar() or 0
        
        # Calculate ratio
        liquidity_ratio = (total_active_loans / total_funds * 100) if total_funds > 0 else 0
        
        # Get threshold
        threshold = await SettingsService.get_float(db, 'liquidity_threshold')
        
        return {
            'total_funds': total_funds,
            'total_active_loans': total_active_loans,
            'available_funds': total_funds - total_active_loans,
            'liquidity_ratio': round(liquidity_ratio, 2),
            'threshold': threshold,
            'is_healthy': liquidity_ratio < threshold
        }
    
    @classmethod
    async def check_loan_approval(cls, db: AsyncSession, loan_amount: float) -> Dict:
        """Check if a loan can be approved based on liquidity"""
        status = await cls.get_liquidity_status(db)
        
        # Calculate what ratio would be after this loan
        new_total_loans = status['total_active_loans'] + loan_amount
        new_ratio = (new_total_loans / status['total_funds'] * 100) if status['total_funds'] > 0 else 100
        
        can_approve = new_ratio < status['threshold']
        
        return {
            'can_approve': can_approve,
            'current_ratio': status['liquidity_ratio'],
            'projected_ratio': round(new_ratio, 2),
            'threshold': status['threshold'],
            'reason': None if can_approve else f"Liquidity limit would be exceeded ({new_ratio:.1f}% > {status['threshold']}%)"
        }


# ============================================
# DEFAULT & RECOVERY SERVICE
# ============================================

class DefaultRecoveryService:
    """Handle loan defaults and recovery process"""
    
    @classmethod
    async def check_overdue_loans(cls, db: AsyncSession) -> List[Dict]:
        """Check all active loans for overdue status"""
        result = await db.execute(
            select(Loan)
            .filter(enum_text(Loan.status).in_(["APPROVED", "ACTIVE"]))
        )
        loans = result.scalars().all()
        
        overdue_loans = []
        now = datetime.now(timezone.utc)
        
        for loan in loans:
            if loan.due_date and now > loan.due_date:
                days_overdue = (now - loan.due_date).days
                overdue_loans.append({
                    'loan_id': loan.id,
                    'user_id': loan.user_id,
                    'days_overdue': days_overdue,
                    'remaining_balance': loan.remaining_balance,
                    'status': get_status_value(loan.status)
                })
        
        return overdue_loans
    
    @classmethod
    async def process_overdue_loan(cls, db: AsyncSession, loan_id: str) -> Dict:
        """
        Process an overdue loan according to the recovery flow:
        - Day 1-7: Reminder
        - Day 7+: 1% penalty
        - Day 14+: Mark at risk
        - Day 30+: Trigger recovery
        """
        result = await db.execute(select(Loan).filter(Loan.id == loan_id))
        loan = result.scalar_one_or_none()
        
        if not loan or not loan.due_date:
            return {'processed': False, 'reason': 'Loan not found or no due date'}
        
        now = datetime.now(timezone.utc)
        if now <= loan.due_date:
            return {'processed': False, 'reason': 'Loan is not overdue'}
        
        days_overdue = (now - loan.due_date).days
        loan.days_overdue = days_overdue
        
        actions_taken = []
        
        # Day 7+: Apply 1% penalty
        if days_overdue >= 7 and loan.overdue_penalty == 0:
            penalty = loan.remaining_balance * 0.01
            loan.overdue_penalty = penalty
            loan.remaining_balance += penalty
            actions_taken.append(f"Applied 1% penalty: ₦{penalty:,.2f}")
        
        # Day 14+: Mark at risk (if not already)
        if days_overdue >= 14:
            actions_taken.append("Marked as at-risk")
        
        # Day 30+: Trigger recovery
        if days_overdue >= 30 and loan.recovery_status == "none":
            # Step 1: Apply collateral
            collateral_applied = await CollateralService.apply_collateral_for_recovery(
                db, loan_id, loan.remaining_balance
            )
            actions_taken.append(f"Applied collateral: ₦{collateral_applied:,.2f}")
            
            # Refresh loan
            await db.refresh(loan)
            
            # Step 2: If still has balance, notify guarantor
            if loan.remaining_balance > 0:
                loan.recovery_status = "guarantor_notified"
                
                # Update guarantor liability
                guarantor_result = await db.execute(
                    select(Guarantor).filter(Guarantor.loan_id == loan_id)
                )
                guarantor = guarantor_result.scalar_one_or_none()
                if guarantor:
                    guarantor.liability_amount = loan.remaining_balance
                    actions_taken.append(f"Guarantor notified of liability: ₦{loan.remaining_balance:,.2f}")
            
            # Step 3: If still unpaid after 60 days, mark as defaulted
            if days_overdue >= 60 and loan.remaining_balance > 0:
                loan.status = "DEFAULTED"
                loan.defaulted_at = now
                
                # Update user's credit score
                await CreditScoreService.on_default(db, loan.user_id)
                
                # Clear active loan reference
                user_result = await db.execute(select(User).filter(User.id == loan.user_id))
                user = user_result.scalar_one_or_none()
                if user:
                    user.active_loan_id = None
                
                actions_taken.append("Loan marked as DEFAULTED")
        
        await db.commit()
        
        return {
            'processed': True,
            'days_overdue': days_overdue,
            'actions_taken': actions_taken,
            'remaining_balance': loan.remaining_balance,
            'recovery_status': get_status_value(loan.recovery_status)
        }


# ============================================
# LOAN CALCULATION SERVICE
# ============================================

class LoanCalculationService:
    """Calculate loan payments using reducing balance method"""
    
    @classmethod
    def calculate_reducing_balance(cls, principal: float, monthly_rate: float, duration_months: int) -> Dict:
        """
        Calculate loan with 2% monthly reducing balance interest.
        
        Returns schedule with monthly payment, total interest, total repayment.
        """
        rate = monthly_rate / 100  # Convert percentage to decimal
        
        # For reducing balance: EMI = P * r * (1+r)^n / ((1+r)^n - 1)
        if rate > 0:
            factor = (1 + rate) ** duration_months
            monthly_payment = principal * rate * factor / (factor - 1)
        else:
            monthly_payment = principal / duration_months
        
        # Generate amortization schedule
        schedule = []
        balance = principal
        total_interest = 0
        
        for month in range(1, duration_months + 1):
            interest = balance * rate
            principal_paid = monthly_payment - interest
            balance = max(0, balance - principal_paid)
            total_interest += interest
            
            schedule.append({
                'month': month,
                'payment': round(monthly_payment, 2),
                'principal': round(principal_paid, 2),
                'interest': round(interest, 2),
                'balance': round(balance, 2)
            })
        
        return {
            'principal': principal,
            'monthly_rate': monthly_rate,
            'duration_months': duration_months,
            'monthly_payment': round(monthly_payment, 2),
            'total_interest': round(total_interest, 2),
            'total_repayment': round(principal + total_interest, 2),
            'schedule': schedule
        }
    
    @classmethod
    async def recalculate_remaining_balance(cls, db: AsyncSession, loan_id: str) -> float:
        """Recalculate remaining balance based on payments made"""
        result = await db.execute(select(Loan).filter(Loan.id == loan_id))
        loan = result.scalar_one_or_none()
        
        if not loan:
            return 0
        
        # Sum all repayments
        repayments_result = await db.execute(
            select(func.coalesce(func.sum(Repayment.amount), 0))
            .filter(Repayment.loan_id == loan_id)
        )
        total_repaid = repayments_result.scalar() or 0
        
        # Calculate remaining
        remaining = loan.total_repayment - total_repaid + loan.overdue_penalty
        loan.remaining_balance = max(0, remaining)
        
        await db.commit()
        return loan.remaining_balance


# ============================================
# MEETING SERVICE
# ============================================

class MeetingService:
    """Manage cooperative monthly meetings"""
    
    @classmethod
    def get_next_first_monday(cls, from_date: date = None) -> date:
        """Get the date of the next first Monday of the month"""
        if from_date is None:
            from_date = date.today()
        
        # Start from next month if we've passed the first Monday
        year = from_date.year
        month = from_date.month
        
        # Find first Monday of current month
        first_day = date(year, month, 1)
        days_until_monday = (7 - first_day.weekday()) % 7
        if first_day.weekday() == 0:  # Already Monday
            first_monday = first_day
        else:
            first_monday = first_day + timedelta(days=days_until_monday)
        
        # If we've passed it, get next month's
        if from_date > first_monday:
            if month == 12:
                year += 1
                month = 1
            else:
                month += 1
            
            first_day = date(year, month, 1)
            days_until_monday = (7 - first_day.weekday()) % 7
            if first_day.weekday() == 0:
                first_monday = first_day
            else:
                first_monday = first_day + timedelta(days=days_until_monday)
        
        return first_monday
    
    @classmethod
    async def get_or_create_next_meeting(cls, db: AsyncSession, admin_id: str = None) -> Meeting:
        """Get the next scheduled meeting or create one"""
        next_monday = cls.get_next_first_monday()
        
        # Check if meeting exists
        result = await db.execute(
            select(Meeting).filter(Meeting.meeting_date == next_monday)
        )
        meeting = result.scalar_one_or_none()
        
        if not meeting:
            # Create new meeting
            meeting = Meeting(
                title=f"Monthly Cooperative Meeting - {next_monday.strftime('%B %Y')}",
                meeting_date=next_monday,
                meeting_time="10:00 AM",
                agenda="1. Opening\n2. Review of previous meeting\n3. Financial report\n4. Loan applications\n5. Contributions update\n6. Any other business\n7. Closing",
                status='scheduled',
                created_by=admin_id
            )
            db.add(meeting)
            await db.commit()
            await db.refresh(meeting)
        
        return meeting
    
    @classmethod
    async def get_upcoming_meetings(cls, db: AsyncSession, limit: int = 3) -> List[Meeting]:
        """Get upcoming meetings"""
        today = date.today()
        result = await db.execute(
            select(Meeting)
            .filter(Meeting.meeting_date >= today)
            .order_by(Meeting.meeting_date.asc())
            .limit(limit)
        )
        return result.scalars().all()


# ============================================
# CONTRIBUTION PROCESSING SERVICE
# ============================================

class ContributionService:
    """Process contributions and update member balances"""
    
    @classmethod
    async def process_approved_contribution(cls, db: AsyncSession, contribution_id: str, admin_id: str) -> bool:
        """Process a contribution approval - update user balances"""
        result = await db.execute(
            select(Contribution).filter(Contribution.id == contribution_id)
        )
        contribution = result.scalar_one_or_none()
        
        if not contribution or contribution.status != "PENDING":
            return False
        
        # Update contribution status
        contribution.status = "APPROVED"
        contribution.approved_at = datetime.now(timezone.utc)
        contribution.approved_by = admin_id
        
        # Update user balances
        user_result = await db.execute(select(User).filter(User.id == contribution.user_id))
        user = user_result.scalar_one_or_none()
        
        if user:
            user.savings_balance += contribution.amount
            user.total_contributions += contribution.amount
        
        # Create notification
        notification = Notification(
            user_id=contribution.user_id,
            title="Contribution Approved",
            message=f"Your contribution of ₦{contribution.amount:,.2f} has been approved and added to your savings.",
            type="contribution_approved"
        )
        db.add(notification)
        
        await db.commit()
        return True


# ============================================
# SHARES SERVICE
# ============================================

class SharesService:
    """Manage member shares"""
    
    @classmethod
    async def purchase_shares(cls, db: AsyncSession, user_id: str, amount: float) -> Dict:
        """Purchase shares with a given amount"""
        share_unit = await SettingsService.get_float(db, 'share_unit')
        
        if amount < share_unit:
            return {'success': False, 'reason': f'Minimum purchase is ₦{share_unit:,.2f}'}
        
        shares_count = amount / share_unit
        
        # Create transaction
        transaction = ShareTransaction(
            user_id=user_id,
            transaction_type='purchase',
            shares_count=shares_count,
            amount=amount,
            share_unit_price=share_unit,
            status='pending'
        )
        db.add(transaction)
        
        await db.commit()
        
        return {
            'success': True,
            'transaction_id': transaction.id,
            'shares_count': shares_count,
            'amount': amount
        }
    
    @classmethod
    async def approve_share_purchase(cls, db: AsyncSession, transaction_id: str, admin_id: str) -> bool:
        """Approve a share purchase"""
        result = await db.execute(
            select(ShareTransaction).filter(ShareTransaction.id == transaction_id)
        )
        transaction = result.scalar_one_or_none()
        
        if not transaction or transaction.status != 'pending':
            return False
        
        transaction.status = 'completed'
        transaction.approved_at = datetime.now(timezone.utc)
        transaction.approved_by = admin_id
        
        # Update user's shares balance
        user_result = await db.execute(select(User).filter(User.id == transaction.user_id))
        user = user_result.scalar_one_or_none()
        
        if user:
            user.shares_balance += transaction.shares_count
        
        await db.commit()
        return True
