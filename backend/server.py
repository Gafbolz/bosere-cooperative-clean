from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Header
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text, cast, String
from sqlalchemy.orm import selectinload
import os
import logging
import uuid
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta, date

import httpx

from database import get_db, AsyncSessionLocal
from models import (
    User, Contribution, Loan, Repayment, Notification, Guarantor, 
    ShareTransaction, WithdrawalRequest, Meeting, MeetingAttendance, MeetingTopic,
    SystemSettings, DividendRecord, MemberDividend,
    UserRole, ContributionStatus, LoanStatus, MemberStatus, KYCStatus,
    GuarantorStatus, RecoveryStatus
)
from services import (
    SettingsService, LoanEligibilityService, GuarantorService, 
    CollateralService, CreditScoreService, LiquidityService,
    DefaultRecoveryService, LoanCalculationService, MeetingService,
    ContributionService, SharesService
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Supabase Configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY')

# Cooperative Configuration
UNIT_VALUE = 10000  # ₦10,000 per unit
LOAN_MULTIPLIER = 3  # Loan eligibility = 3x contributions
DEFAULT_INTEREST_RATE = 5.0  # 5% annual interest

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

# Create the main app
app = FastAPI(title="Bosere Cooperative API", version="2.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ============ Pydantic Models ============

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    phone: str
    supabase_user_id: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    full_name: str
    phone: Optional[str]
    role: str
    is_approved: bool
    created_at: datetime
    # Enhanced fields
    status: Optional[str] = None
    business_name: Optional[str] = None
    cac_registration_number: Optional[str] = None
    kyc_status: Optional[str] = None
    credit_score: Optional[int] = 50
    savings_balance: Optional[float] = 0
    shares_balance: Optional[float] = 0

class ContributionCreate(BaseModel):
    amount: float
    description: Optional[str] = ""

class ContributionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    amount: float
    description: Optional[str]
    status: str
    created_at: datetime
    approved_at: Optional[datetime]
    user_name: Optional[str] = None

class LoanCreate(BaseModel):
    amount: float
    duration_months: int
    purpose: str

class RepaymentCreate(BaseModel):
    amount: float
    notes: Optional[str] = ""

class RepaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    loan_id: str
    amount: float
    payment_date: datetime
    notes: Optional[str]

class LoanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    amount: float
    duration_months: int
    interest_rate: float
    monthly_payment: float
    total_repayment: float
    purpose: Optional[str]
    status: str
    created_at: datetime
    approved_at: Optional[datetime]
    user_name: Optional[str] = None
    total_repaid: float = 0
    repayments: List[RepaymentResponse] = []
    # Enhanced fields
    remaining_balance: Optional[float] = 0
    guarantor_id: Optional[str] = None
    guarantor_name: Optional[str] = None
    collateral_locked: Optional[float] = 0
    days_overdue: Optional[int] = 0

class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    title: str
    message: str
    type: str
    is_read: bool
    created_at: datetime

class DashboardStats(BaseModel):
    total_contributions: float
    confirmed_contributions: float
    pending_contributions: float
    total_units: float
    unit_value: float
    total_share_value: float
    loan_eligibility: float
    active_loan_amount: float
    active_loan_remaining: float
    # Enhanced fields
    locked_collateral: float = 0
    available_savings: float = 0
    credit_score: int = 50

class AdminStats(BaseModel):
    total_members: int
    approved_members: int
    pending_members: int
    total_contributions: float
    pending_contributions_count: int
    total_loans_disbursed: float
    pending_loans_count: int
    active_loans_count: int
    # New fields
    total_shares: float = 0
    liquidity_ratio: float = 0
    liquidity_healthy: bool = True
    next_meeting_date: Optional[str] = None
    risky_loans_count: int = 0

# ============ New Pydantic Models for Enhanced Features ============

class KYCUpdate(BaseModel):
    business_name: Optional[str] = None
    residential_address: Optional[str] = None
    business_address: Optional[str] = None
    business_type: Optional[str] = None
    years_in_operation: Optional[int] = None
    cac_registration_number: Optional[str] = None
    cac_certificate_url: Optional[str] = None
    government_id_url: Optional[str] = None

class LoanEligibilityResponse(BaseModel):
    eligible: bool
    loan_limit: float
    reasons: List[str]
    tier: int
    multiplier: int
    membership_months: int
    approved_contributions: int
    savings_balance: float
    kyc_status: str
    has_active_loan: bool

class GuarantorValidationResponse(BaseModel):
    valid: bool
    reasons: List[str]
    guarantor: Optional[Dict[str, Any]] = None

class LoanApplicationCreate(BaseModel):
    amount: float
    duration_months: int
    purpose: str
    guarantor_id: str
    relationship_to_guarantor: Optional[str] = None

class LiquidityStatusResponse(BaseModel):
    total_funds: float
    total_active_loans: float
    available_funds: float
    liquidity_ratio: float
    threshold: float
    is_healthy: bool

class MeetingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    meeting_date: date
    meeting_time: str
    location: Optional[str]
    agenda: Optional[str]
    notes: Optional[str]
    status: str

class MeetingCreate(BaseModel):
    title: str
    meeting_date: date
    meeting_time: str = "10:00 AM"
    location: Optional[str] = None
    agenda: Optional[str] = None

class SystemSettingResponse(BaseModel):
    key: str
    value: str
    description: Optional[str] = None

class SharePurchaseCreate(BaseModel):
    amount: float

class WithdrawalRequestCreate(BaseModel):
    amount: float
    withdrawal_type: str  # savings, shares, emergency

class EnhancedUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    full_name: str
    phone: Optional[str]
    role: str
    status: str
    is_approved: bool
    # KYC fields
    business_name: Optional[str]
    business_type: Optional[str]
    cac_registration_number: Optional[str]
    kyc_status: str
    # Financial fields
    savings_balance: float
    shares_balance: float
    locked_collateral: float
    available_savings: float
    credit_score: int
    # Stats
    total_contributions: float
    total_loans_taken: float
    total_loans_repaid: float
    membership_months: int
    has_active_loan: bool
    created_at: datetime

class EnhancedLoanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    amount: float
    duration_months: int
    interest_rate: float
    monthly_payment: float
    total_repayment: float
    remaining_balance: float
    purpose: Optional[str]
    status: str
    created_at: datetime
    approved_at: Optional[datetime]
    # New fields
    collateral_locked: float
    days_overdue: int
    overdue_penalty: float
    recovery_status: str
    guarantor_name: Optional[str] = None
    user_name: Optional[str] = None
    total_repaid: float = 0
    repayments: List[RepaymentResponse] = []

# ============ Auth Helper Functions ============

async def verify_supabase_token(authorization: str = Header(None)) -> dict:
    """Verify Supabase JWT token and return user info"""
    if os.getenv("TEST_MODE", "false").lower() == "true":
       return {"id": "3e5502c1-cc21-4182-b7ab-7060d51e52ff" ,"role": "ADMIN"}
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    token = authorization.replace("Bearer ", "")
    
    # Verify token with Supabase
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SUPABASE_URL}/auth/v1/user",
            headers={
                "Authorization": f"Bearer {token}",
                "apikey": SUPABASE_ANON_KEY
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        return response.json()

async def get_current_user(
    supabase_user: dict = Depends(verify_supabase_token),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get the current user from database based on Supabase user ID"""
    result = await db.execute(
        select(User).where(User.supabase_user_id == supabase_user["id"])
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User profile not found. Please complete registration.")
    
    return user

async def get_admin_user(user: User = Depends(get_current_user)) -> User:
    """Ensure the current user is an admin"""
    if user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

def calculate_loan_payment(principal: float, months: int, annual_rate: float = DEFAULT_INTEREST_RATE) -> dict:
    """Calculate monthly payment and total repayment for a loan"""
    monthly_rate = annual_rate / 100 / 12
    if monthly_rate == 0:
        monthly_payment = principal / months
    else:
        monthly_payment = principal * (monthly_rate * (1 + monthly_rate)**months) / ((1 + monthly_rate)**months - 1)
    total_repayment = monthly_payment * months
    return {
        "monthly_payment": round(monthly_payment, 2),
        "total_repayment": round(total_repayment, 2),
        "total_interest": round(total_repayment - principal, 2)
    }

async def create_notification(db: AsyncSession, user_id: str, title: str, message: str, notif_type: str):
    """Create a notification for a user"""
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=notif_type
    )
    db.add(notification)

# ============ Auth Routes ============

@api_router.post("/auth/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user profile after Supabase signup"""
    import uuid
    
    # Check if user already exists using raw SQL for safety
    check_result = await db.execute(
        text("SELECT id FROM users WHERE supabase_user_id = :sid OR email = :email LIMIT 1"),
        {"sid": user_data.supabase_user_id, "email": user_data.email}
    )
    if check_result.fetchone():
        raise HTTPException(status_code=400, detail="User already registered")
    
    # Generate user ID
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    
    # Insert using raw SQL with only columns that exist in the base schema
    # This ensures compatibility even if enhanced columns haven't been migrated yet
    try:
        await db.execute(
            text("""
                INSERT INTO users (id, supabase_user_id, email, full_name, phone, role, is_approved, created_at, updated_at)
                VALUES (:id, :supabase_user_id, :email, :full_name, :phone, :role, :is_approved, :created_at, :updated_at)
            """),
            {
                "id": user_id,
                "supabase_user_id": user_data.supabase_user_id,
                "email": user_data.email,
                "full_name": user_data.full_name,
                "phone": user_data.phone,
                "role": "MEMBER",
                "is_approved": False,
                "created_at": now,
                "updated_at": now
            }
        )
        await db.commit()
    except Exception as e:
        await db.rollback()
        logging.error(f"Registration insert failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create user profile: {str(e)}")
    
    # Fetch the created user
    result = await db.execute(
        text("SELECT id, supabase_user_id, email, full_name, phone, role, is_approved, created_at FROM users WHERE id = :id"),
        {"id": user_id}
    )
    row = result.fetchone()
    
    if not row:
        raise HTTPException(status_code=500, detail="User created but could not be retrieved")
    
    # Create welcome notification
    try:
        notif_id = str(uuid.uuid4())
        await db.execute(
            text("""
                INSERT INTO notifications (id, user_id, title, message, type, is_read, created_at)
                VALUES (:id, :user_id, :title, :message, :type, :is_read, :created_at)
            """),
            {
                "id": notif_id,
                "user_id": user_id,
                "title": "Welcome to Bosere Cooperative!",
                "message": "Your account is pending approval. You'll be notified once approved.",
                "type": "welcome",
                "is_read": False,
                "created_at": now
            }
        )
        await db.commit()
    except Exception as e:
        # Non-critical - log but don't fail
        logging.warning(f"Could not create welcome notification: {e}")
    
    # Return user response with defaults for optional fields
    return UserResponse(
        id=row.id,
        email=row.email,
        full_name=row.full_name,
        phone=row.phone,
        role=row.role,
        is_approved=row.is_approved,
        created_at=row.created_at,
        status="PENDING",
        kyc_status="PENDING",
        credit_score=50,
        savings_balance=0,
        shares_balance=0
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    """Get current user profile"""
    return user

@api_router.get("/auth/check-user")
async def check_user(
    supabase_user: dict = Depends(verify_supabase_token),
    db: AsyncSession = Depends(get_db)
):
    """Check if user profile exists for Supabase user"""
    
    # Use raw SQL to avoid model column mismatches
    result = await db.execute(
        text("SELECT id, email, full_name, phone, role, is_approved FROM users WHERE supabase_user_id = :sid LIMIT 1"),
        {"sid": supabase_user["id"]}
    )
    row = result.fetchone()
    
    if row:
        # Handle role - could be string or enum depending on DB state
        role_value = row.role
        if hasattr(role_value, 'value'):
            role_value = role_value.value
        
        return {
            "exists": True,
            "user": {
                "id": row.id,
                "email": row.email,
                "full_name": row.full_name,
                "phone": row.phone,
                "role": str(role_value),
                "is_approved": row.is_approved
            }
        }
    return {"exists": False}

# ============ Contribution Routes ============

@api_router.post("/contributions", response_model=ContributionResponse)
async def create_contribution(
    data: ContributionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not user.is_approved:
        raise HTTPException(status_code=403, detail="Account not yet approved")
    
    import uuid
    contribution_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    
    # Use raw SQL to avoid model column mismatches with database schema
    try:
        await db.execute(
            text("""
                INSERT INTO contributions (id, user_id, amount, description, status, created_at)
                VALUES (:id, :user_id, :amount, :description, :status, :created_at)
            """),
            {
                "id": contribution_id,
                "user_id": user.id,
                "amount": data.amount,
                "description": data.description or "",
                "status": "PENDING",
                "created_at": now
            }
        )
        await db.commit()
    except Exception as e:
        await db.rollback()
        logging.error(f"Contribution insert failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create contribution: {str(e)}")
    
    return ContributionResponse(
        id=contribution_id,
        user_id=user.id,
        amount=data.amount,
        description=data.description or "",
        status="PENDING",
        created_at=now,
        approved_at=None,
        user_name=user.full_name
    )

@api_router.get("/contributions", response_model=List[ContributionResponse])
async def get_contributions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Contribution)
        .where(Contribution.user_id == user.id)
        .order_by(Contribution.created_at.desc())
        .limit(100)
    )
    contributions = result.scalars().all()
    
    return [
        ContributionResponse(
            id=c.id,
            user_id=c.user_id,
            amount=c.amount,
            description=c.description,
            status=get_status_value(c.status),
            created_at=c.created_at,
            approved_at=c.approved_at,
            user_name=user.full_name
        )
        for c in contributions
    ]

# ============ Loan Routes ============

@api_router.post("/loans", response_model=LoanResponse)
async def apply_for_loan(
    data: LoanCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not user.is_approved:
        raise HTTPException(status_code=403, detail="Account not yet approved")
    
    # Check for existing active loan
    result = await db.execute(
        select(Loan).where(
            and_(
                Loan.user_id == user.id,
                enum_text(Loan.status).in_(["PENDING", "APPROVED", "ACTIVE"])
            )
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="You already have an active or pending loan")
    
    # Calculate loan eligibility
    result = await db.execute(
        select(func.coalesce(func.sum(Contribution.amount), 0))
        .where(
            and_(
                Contribution.user_id == user.id,
                enum_text(Contribution.status) == "APPROVED"
            )
        )
    )
    total_confirmed = result.scalar() or 0
    max_loan = total_confirmed * LOAN_MULTIPLIER
    
    if data.amount > max_loan:
        raise HTTPException(
            status_code=400,
            detail=f"Loan amount exceeds eligibility. Max: ₦{max_loan:,.2f}"
        )
    
    payment_info = calculate_loan_payment(data.amount, data.duration_months)
    
    loan = Loan(
        user_id=user.id,
        amount=data.amount,
        duration_months=data.duration_months,
        interest_rate=DEFAULT_INTEREST_RATE,
        monthly_payment=payment_info["monthly_payment"],
        total_repayment=payment_info["total_repayment"],
        purpose=data.purpose,
        status="PENDING"
    )
    
    db.add(loan)
    await db.commit()
    await db.refresh(loan)
    
    return LoanResponse(
        id=loan.id,
        user_id=loan.user_id,
        amount=loan.amount,
        duration_months=loan.duration_months,
        interest_rate=loan.interest_rate,
        monthly_payment=loan.monthly_payment,
        total_repayment=loan.total_repayment,
        purpose=loan.purpose,
        status=get_status_value(loan.status),
        created_at=loan.created_at,
        approved_at=loan.approved_at,
        user_name=user.full_name,
        total_repaid=0,
        repayments=[]
    )

@api_router.get("/loans", response_model=List[LoanResponse])
async def get_loans(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Loan)
        .options(selectinload(Loan.repayments))
        .where(Loan.user_id == user.id)
        .order_by(Loan.created_at.desc())
    )
    loans = result.scalars().all()
    
    return [
        LoanResponse(
            id=l.id,
            user_id=l.user_id,
            amount=l.amount,
            duration_months=l.duration_months,
            interest_rate=l.interest_rate,
            monthly_payment=l.monthly_payment,
            total_repayment=l.total_repayment,
            purpose=l.purpose,
            status=get_status_value(l.status),
            created_at=l.created_at,
            approved_at=l.approved_at,
            user_name=user.full_name,
            total_repaid=sum(r.amount for r in l.repayments),
            repayments=[RepaymentResponse(
                id=r.id,
                loan_id=r.loan_id,
                amount=r.amount,
                payment_date=r.payment_date,
                notes=r.notes
            ) for r in l.repayments]
        )
        for l in loans
    ]

@api_router.post("/loans/{loan_id}/repayments", response_model=RepaymentResponse)
async def add_repayment(
    loan_id: str,
    data: RepaymentCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a repayment to an active loan"""
    result = await db.execute(
        select(Loan)
        .options(selectinload(Loan.repayments))
        .where(and_(Loan.id == loan_id, Loan.user_id == user.id))
    )
    loan = result.scalar_one_or_none()
    
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    
    if loan.status not in ["APPROVED", "ACTIVE"]:
        raise HTTPException(status_code=400, detail="Loan is not active")
    
    repayment = Repayment(
        loan_id=loan_id,
        amount=data.amount,
        notes=data.notes
    )
    
    db.add(repayment)
    
    # Check if loan is fully repaid
    total_repaid = sum(r.amount for r in loan.repayments) + data.amount
    if total_repaid >= loan.total_repayment:
        loan.status = "COMPLETED"
        loan.completed_at = datetime.now(timezone.utc)
        await create_notification(
            db, user.id,
            "Loan Fully Repaid!",
            f"Congratulations! Your loan of ₦{loan.amount:,.2f} has been fully repaid.",
            "loan_completed"
        )
    
    await db.commit()
    await db.refresh(repayment)
    
    return RepaymentResponse(
        id=repayment.id,
        loan_id=repayment.loan_id,
        amount=repayment.amount,
        payment_date=repayment.payment_date,
        notes=repayment.notes
    )

@api_router.get("/loans/calculator")
async def loan_calculator(amount: float, duration_months: int, contribution_total: float):
    max_loan = contribution_total * LOAN_MULTIPLIER
    eligible = amount <= max_loan
    payment_info = calculate_loan_payment(amount, duration_months)
    
    return {
        "amount": amount,
        "duration_months": duration_months,
        "contribution_total": contribution_total,
        "max_eligible_loan": max_loan,
        "is_eligible": eligible,
        "interest_rate": DEFAULT_INTEREST_RATE,
        **payment_info
    }

# ============ Dashboard Routes ============

@api_router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    
    # Get contributions using raw SQL to avoid enum type issues
    result = await db.execute(
        text("SELECT id, amount, status FROM contributions WHERE user_id = :uid"),
        {"uid": user.id}
    )
    contributions = result.fetchall()
    
    total_contributions = sum(c.amount for c in contributions)
    confirmed_contributions = sum(c.amount for c in contributions if str(c.status) == "APPROVED")
    pending_contributions = sum(c.amount for c in contributions if str(c.status) == "PENDING")
    
    # Calculate shares/units
    total_units = confirmed_contributions / UNIT_VALUE
    
    # Loan eligibility
    loan_eligibility = confirmed_contributions * LOAN_MULTIPLIER
    
    # Active loan using raw SQL to avoid enum type issues
    result = await db.execute(
        text("""
            SELECT id, amount, total_repayment, status 
            FROM loans 
            WHERE user_id = :uid AND status::text IN ('APPROVED', 'ACTIVE')
            LIMIT 1
        """),
        {"uid": user.id}
    )
    active_loan_row = result.fetchone()
    
    active_loan_amount = 0
    active_loan_remaining = 0
    
    if active_loan_row:
        active_loan_amount = active_loan_row.amount
        # Get repayments for this loan
        repay_result = await db.execute(
            text("SELECT COALESCE(SUM(amount), 0) as total FROM repayments WHERE loan_id = :lid"),
            {"lid": active_loan_row.id}
        )
        total_repaid = repay_result.scalar() or 0
        active_loan_remaining = active_loan_row.total_repayment - total_repaid
    
    # Get locked collateral - safely handle if column doesn't exist
    locked_collateral = 0
    credit_score = 50
    try:
        result = await db.execute(
            text("SELECT locked_collateral, credit_score FROM users WHERE id = :uid"),
            {"uid": user.id}
        )
        user_row = result.fetchone()
        if user_row:
            locked_collateral = user_row.locked_collateral or 0
            credit_score = user_row.credit_score or 50
    except Exception:
        # Columns may not exist in database - use defaults
        pass
    
    available_savings = confirmed_contributions - locked_collateral
    
    return DashboardStats(
        total_contributions=total_contributions,
        confirmed_contributions=confirmed_contributions,
        pending_contributions=pending_contributions,
        total_units=round(total_units, 2),
        unit_value=UNIT_VALUE,
        total_share_value=confirmed_contributions,
        loan_eligibility=loan_eligibility,
        active_loan_amount=active_loan_amount,
        active_loan_remaining=max(0, active_loan_remaining),
        locked_collateral=locked_collateral,
        available_savings=max(0, available_savings),
        credit_score=credit_score
    )

@api_router.get("/dashboard/chart-data")
async def get_chart_data(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    
    # Get approved contributions using raw SQL
    result = await db.execute(
        text("""
            SELECT amount, created_at 
            FROM contributions 
            WHERE user_id = :uid AND status::text = 'APPROVED'
            ORDER BY created_at
        """),
        {"uid": user.id}
    )
    contributions = result.fetchall()
    
    # Group by month
    monthly_data = {}
    for c in contributions:
        month = c.created_at.strftime("%Y-%m")
        if month not in monthly_data:
            monthly_data[month] = 0
        monthly_data[month] += c.amount
    
    return {
        "labels": list(monthly_data.keys()),
        "contributions": list(monthly_data.values())
    }

# ============ Notification Routes ============

@api_router.get("/notifications", response_model=List[NotificationResponse])
async def get_notifications(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .limit(100)
    )
    notifications = result.scalars().all()
    return notifications

@api_router.patch("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Notification).where(
            and_(Notification.id == notification_id, Notification.user_id == user.id)
        )
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = True
    await db.commit()
    return {"success": True}

@api_router.patch("/notifications/read-all")
async def mark_all_notifications_read(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy import update as sql_update
    await db.execute(
        sql_update(Notification)
        .where(Notification.user_id == user.id)
        .values(is_read=True)
    )
    await db.commit()
    return {"success": True}

# ============ Admin Routes ============

@api_router.get("/admin/stats", response_model=AdminStats)
async def get_admin_stats(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    total_members = await db.scalar(select(func.count()).select_from(User).where(enum_text(User.role) == "MEMBER"))
    approved_members = await db.scalar(select(func.count()).select_from(User).where(and_(enum_text(User.role) == "MEMBER", User.is_approved == True)))
    pending_members = await db.scalar(select(func.count()).select_from(User).where(and_(enum_text(User.role) == "MEMBER", User.is_approved == False)))
    
    total_contributions = await db.scalar(
        select(func.coalesce(func.sum(Contribution.amount), 0))
        .where(enum_text(Contribution.status) == "APPROVED")
    ) or 0
    pending_contributions_count = await db.scalar(
        select(func.count()).select_from(Contribution).where(enum_text(Contribution.status) == "PENDING")
    )
    
    total_loans_disbursed = await db.scalar(
        select(func.coalesce(func.sum(Loan.amount), 0))
        .where(enum_text(Loan.status).in_(["APPROVED", "ACTIVE", "COMPLETED"]))
    ) or 0
    pending_loans_count = await db.scalar(
        select(func.count()).select_from(Loan).where(enum_text(Loan.status) == "PENDING")
    )
    active_loans_count = await db.scalar(
        select(func.count()).select_from(Loan).where(enum_text(Loan.status).in_(["APPROVED", "ACTIVE"]))
    )
    
    return AdminStats(
        total_members=total_members,
        approved_members=approved_members,
        pending_members=pending_members,
        total_contributions=total_contributions,
        pending_contributions_count=pending_contributions_count,
        total_loans_disbursed=total_loans_disbursed,
        pending_loans_count=pending_loans_count,
        active_loans_count=active_loans_count
    )

@api_router.get("/admin/users", response_model=List[UserResponse])
async def get_all_users(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(enum_text(User.role) == "MEMBER").order_by(User.created_at.desc()).limit(500)
    )
    return result.scalars().all()

@api_router.patch("/admin/users/{user_id}/approve")
async def approve_user(
    user_id: str,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_approved = True
    await create_notification(
        db, user_id,
        "Account Approved!",
        "Your membership has been approved. You can now make contributions and apply for loans.",
        "account_approved"
    )
    await db.commit()
    return {"success": True}

@api_router.get("/admin/contributions")
async def get_all_contributions(
    status: Optional[str] = None,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Contribution).options(selectinload(Contribution.user))
    if status:
        query = query.where(enum_text(Contribution.status) == status.upper())
    query = query.order_by(Contribution.created_at.desc()).limit(500)
    
    result = await db.execute(query)
    contributions = result.scalars().all()
    
    return [
        {
            "id": c.id,
            "user_id": c.user_id,
            "user_name": c.user.full_name if c.user else "Unknown",
            "amount": c.amount,
            "description": c.description,
            "status": get_status_value(c.status),
            "created_at": c.created_at.isoformat(),
            "approved_at": c.approved_at.isoformat() if c.approved_at else None
        }
        for c in contributions
    ]

@api_router.patch("/admin/contributions/{contribution_id}/approve")
async def approve_contribution(
    contribution_id: str,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    logging.info(f"[APPROVE] Admin {admin.id} approving contribution {contribution_id}")
    
    # First check if contribution exists
    result = await db.execute(
    select(Contribution).where(Contribution.id == contribution_id)
)
contribution = result.scalar_one_or_none()
    
    if not contribution:
        logging.error(f"[APPROVE] Contribution {contribution_id} not found")
        raise HTTPException(status_code=404, detail="Contribution not found")
    
    logging.info(f"[APPROVE] Found contribution: amount={contribution.amount}, current_status={contribution.status}")
    
    now = datetime.now(timezone.utc)
    
    try:
        # Update contribution status using raw SQL with enum cast
         await db.execute(
           text("""
UPDATE contributions
SET status =
 'APPROVED'::contributionstatus,
    approved_at = :approved_at,
    approved_by = :approved_by
WHERE id = :cid
"""),
    {
        "cid": contribution_id,
        "approved_at": now,
        "approved_by": admin.id
    }
       )
       logging.info(f"[APPROVE] Contribution status updated to APPROVED")
        
        # Create notification
        notif_id = str(uuid.uuid4())
        await db.execute(
            text("""
                INSERT INTO notifications (id, user_id, title, message, type, is_read, created_at)
                VALUES (:id, :user_id, :title, :message, :type, :is_read, :created_at)
            """),
            {
                "id": notif_id,
                "user_id": contribution.user_id,
                "title": "Contribution Approved!",
                "message": f"Your contribution of ₦{contribution.amount:,.2f} has been approved and added to your share capital.",
                "type": "contribution_approved",
                "is_read": False,
                "created_at": now
            }
        )
        logging.info(f"[APPROVE] Notification created")
        
        await db.commit()
        logging.info(f"[APPROVE] Transaction committed successfully")
        return {"success": True}
        
    except Exception as e:
        await db.rollback()
        logging.error(f"[APPROVE] Failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to approve contribution: {str(e)}")

@api_router.patch("/admin/contributions/{contribution_id}/reject")
async def reject_contribution(
    contribution_id: str,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    logging.info(f"[REJECT] Admin {admin.id} rejecting contribution {contribution_id}")
    
    # First check if contribution exists
    result = await db.execute(
        text("SELECT id, user_id, amount FROM contributions WHERE id = :cid"),
        {"cid": contribution_id}
    )
    contribution = result.fetchone()
    
    if not contribution:
        logging.error(f"[REJECT] Contribution {contribution_id} not found")
        raise HTTPException(status_code=404, detail="Contribution not found")
    
    now = datetime.now(timezone.utc)
    
    try:
        # Update contribution status using raw SQL with enum cast
        await db.execute(
            text("""
                UPDATE contributions 
                SET status = 'REJECTED'::contributionstatus
                WHERE id = :cid
            """),
            {"cid": contribution_id}
        )
        logging.info(f"[REJECT] Contribution status updated to REJECTED")
        
        # Create notification
        notif_id = str(uuid.uuid4())
        await db.execute(
            text("""
                INSERT INTO notifications (id, user_id, title, message, type, is_read, created_at)
                VALUES (:id, :user_id, :title, :message, :type, :is_read, :created_at)
            """),
            {
                "id": notif_id,
                "user_id": contribution.user_id,
                "title": "Contribution Rejected",
                "message": f"Your contribution of ₦{contribution.amount:,.2f} was not approved. Please contact support.",
                "type": "contribution_rejected",
                "is_read": False,
                "created_at": now
            }
        )
        logging.info(f"[REJECT] Notification created")
        
        await db.commit()
        logging.info(f"[REJECT] Transaction committed successfully")
        return {"success": True}
        
    except Exception as e:
        await db.rollback()
        logging.error(f"[REJECT] Failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to reject contribution: {str(e)}")

@api_router.get("/admin/loans")
async def get_all_loans(
    status: Optional[str] = None,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Loan).options(selectinload(Loan.user), selectinload(Loan.repayments), selectinload(Loan.guarantor))
    if status:
        query = query.where(enum_text(Loan.status) == status.upper())
    query = query.order_by(Loan.created_at.desc()).limit(500)
    
    result = await db.execute(query)
    loans = result.scalars().all()
    
    loan_list = []
    for l in loans:
        # Get guarantor name if exists
        guarantor_name = None
        if l.guarantor_id:
            guarantor_result = await db.execute(select(User).where(User.id == l.guarantor_id))
            guarantor = guarantor_result.scalar_one_or_none()
            if guarantor:
                guarantor_name = guarantor.full_name
        
        loan_list.append({
            "id": l.id,
            "user_id": l.user_id,
            "user_name": l.user.full_name if l.user else "Unknown",
            "amount": l.amount,
            "duration_months": l.duration_months,
            "interest_rate": l.interest_rate,
            "monthly_payment": l.monthly_payment,
            "total_repayment": l.total_repayment,
            "remaining_balance": l.remaining_balance or l.total_repayment,
            "purpose": l.purpose,
            "status": get_status_value(l.status),
            "created_at": l.created_at.isoformat(),
            "approved_at": l.approved_at.isoformat() if l.approved_at else None,
            "total_repaid": sum(r.amount for r in l.repayments),
            "guarantor_id": l.guarantor_id,
            "guarantor_name": guarantor_name,
            "collateral_locked": l.collateral_locked or 0,
            "days_overdue": l.days_overdue or 0
        })
    
    return loan_list

@api_router.patch("/admin/loans/{loan_id}/approve")
async def approve_loan(
    loan_id: str,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    logging.info(f"[LOAN APPROVE] Admin {admin.id} approving loan {loan_id}")
    
    # Check if loan exists
    result = await db.execute(
        text("SELECT id, user_id, amount, status FROM loans WHERE id = :lid"),
        {"lid": loan_id}
    )
    loan = result.fetchone()
    
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    
    now = datetime.now(timezone.utc)
    
    try:
        # Update loan status using raw SQL with enum cast
        await db.execute(
            text("""
                UPDATE loans 
                SET status = 'ACTIVE'::loanstatus, 
                    approved_at = :approved_at, 
                    approved_by = :approved_by 
                WHERE id = :lid
            """),
            {"lid": loan_id, "approved_at": now, "approved_by": admin.id}
        )
        logging.info(f"[LOAN APPROVE] Loan status updated to ACTIVE")
        
        # Update user's active loan reference
        await db.execute(
            text("UPDATE users SET active_loan_id = :lid WHERE id = :uid"),
            {"lid": loan_id, "uid": loan.user_id}
        )
        
        # Create notification
        notif_id = str(uuid.uuid4())
        await db.execute(
            text("""
                INSERT INTO notifications (id, user_id, title, message, type, is_read, created_at)
                VALUES (:id, :user_id, :title, :message, :type, :is_read, :created_at)
            """),
            {
                "id": notif_id,
                "user_id": loan.user_id,
                "title": "Loan Approved!",
                "message": f"Your loan application of ₦{loan.amount:,.2f} has been approved. Funds will be disbursed shortly.",
                "type": "loan_approved",
                "is_read": False,
                "created_at": now
            }
        )
        
        await db.commit()
        logging.info(f"[LOAN APPROVE] Transaction committed successfully")
        return {"success": True}
        
    except Exception as e:
        await db.rollback()
        logging.error(f"[LOAN APPROVE] Failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to approve loan: {str(e)}")

@api_router.patch("/admin/loans/{loan_id}/reject")
async def reject_loan(
    loan_id: str,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    logging.info(f"[LOAN REJECT] Admin {admin.id} rejecting loan {loan_id}")
    
    # Check if loan exists
    result = await db.execute(
        text("SELECT id, user_id, amount FROM loans WHERE id = :lid"),
        {"lid": loan_id}
    )
    loan = result.fetchone()
    
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    
    now = datetime.now(timezone.utc)
    
    try:
        # Update loan status using raw SQL with enum cast
        await db.execute(
            text("""
                UPDATE loans 
                SET status = 'REJECTED'::loanstatus
                WHERE id = :lid
            """),
            {"lid": loan_id}
        )
        logging.info(f"[LOAN REJECT] Loan status updated to REJECTED")
        
        # Create notification
        notif_id = str(uuid.uuid4())
        await db.execute(
            text("""
                INSERT INTO notifications (id, user_id, title, message, type, is_read, created_at)
                VALUES (:id, :user_id, :title, :message, :type, :is_read, :created_at)
            """),
            {
                "id": notif_id,
                "user_id": loan.user_id,
                "title": "Loan Application Rejected",
                "message": f"Your loan application of ₦{loan.amount:,.2f} was not approved. Please contact support for more details.",
                "type": "loan_rejected",
                "is_read": False,
                "created_at": now
            }
        )
        
        await db.commit()
        logging.info(f"[LOAN REJECT] Transaction committed successfully")
        return {"success": True}
        
    except Exception as e:
        await db.rollback()
        logging.error(f"[LOAN REJECT] Failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to reject loan: {str(e)}")

# ============ Seed Admin (Production-Safe) ============
# This endpoint requires admin authentication in production

@api_router.post("/seed/admin")
async def seed_admin(db: AsyncSession = Depends(get_db)):
    """
    Seed the admin account - this creates a local admin without Supabase auth.
    NOTE: In production, prefer creating admin via Supabase + SQL UPDATE.
    """
    # Check if running in production
    app_env = os.environ.get('APP_ENV', 'development')
    if app_env == 'production':
        raise HTTPException(
            status_code=403, 
            detail="Admin seeding disabled in production. Use Supabase Auth + SQL UPDATE instead."
        )
    
    result = await db.execute(select(User).where(User.email == "admin@bosere.com"))
    existing = result.scalar_one_or_none()
    
    if existing:
        return {"message": "Admin already exists", "email": "admin@bosere.com"}
    
    admin = User(
        email="admin@bosere.com",
        full_name="Bosere Admin",
        phone="+2348000000000",
        role="ADMIN",
        is_approved=True,
        supabase_user_id="admin-local"
    )
    
    db.add(admin)
    await db.commit()
    
    return {"message": "Admin created. Create this user in Supabase Auth separately.", "email": "admin@bosere.com"}

# ============ Enhanced Business Logic Endpoints ============

@api_router.get("/eligibility", response_model=LoanEligibilityResponse)
async def check_loan_eligibility(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Check the current user's loan eligibility"""
    eligibility = await LoanEligibilityService.check_eligibility(db, user)
    return eligibility

@api_router.get("/guarantor/validate/{guarantor_id}", response_model=GuarantorValidationResponse)
async def validate_guarantor(
    guarantor_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Validate if a member can act as guarantor for the current user's loan"""
    validation = await GuarantorService.validate_guarantor(db, guarantor_id, user.id)
    return validation

@api_router.get("/guarantor/search")
async def search_guarantors(
    query: str = "",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Search for potential guarantors (active members who can guarantee loans)"""
    # Check if test mode is enabled
    test_mode = await SettingsService.get_bool(db, 'test_mode')
    
    if test_mode:
        # TEST MODE: Return all users except current user (bypass status checks)
        logging.info(f"[TEST MODE] Guarantor search - returning all users for query: {query}")
        result = await db.execute(
            text("""
                SELECT id, full_name, email, credit_score, role 
                FROM users 
                WHERE id != :user_id
                AND (full_name ILIKE :query OR email ILIKE :query OR :query = '')
                LIMIT 20
            """),
            {"user_id": user.id, "query": f"%{query}%"}
        )
        members = result.fetchall()
        
        return [
            {
                'id': m.id,
                'full_name': m.full_name,
                'email': m.email,
                'credit_score': m.credit_score or 50,
                'is_valid_guarantor': True,  # All valid in test mode
                'validation_issues': [],
                'test_mode': True
            }
            for m in members
        ]
    
    # PRODUCTION MODE: Only active members
    result = await db.execute(
        select(User)
        .filter(
            User.id != user.id,
            enum_text(User.status) == "ACTIVE",
            enum_text(User.role) == "MEMBER"
        )
        .filter(
            or_(
                User.full_name.ilike(f"%{query}%"),
                User.email.ilike(f"%{query}%")
            ) if query else True
        )
        .limit(10)
    )
    members = result.scalars().all()
    
    # Validate each as potential guarantor
    potential_guarantors = []
    for member in members:
        validation = await GuarantorService.validate_guarantor(db, member.id, user.id)
        potential_guarantors.append({
            'id': member.id,
            'full_name': member.full_name,
            'email': member.email,
            'credit_score': member.credit_score,
            'is_valid_guarantor': validation['valid'],
            'validation_issues': validation['reasons'] if not validation['valid'] else []
        })
    
    return potential_guarantors

@api_router.get("/guarantor/available")
async def get_available_guarantors(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all available guarantors for dropdown selection"""
    # Check if test mode is enabled
    test_mode = await SettingsService.get_bool(db, 'test_mode')
    
    if test_mode:
        # TEST MODE: Return all users except current user
        logging.info(f"[TEST MODE] Getting all available guarantors for user {user.id}")
        result = await db.execute(
            text("""
                SELECT id, full_name, email, credit_score 
                FROM users 
                WHERE id != :user_id
                ORDER BY full_name
                LIMIT 50
            """),
            {"user_id": user.id}
        )
        members = result.fetchall()
        
        return {
            'guarantors': [
                {
                    'id': m.id,
                    'full_name': m.full_name,
                    'email': m.email,
                    'credit_score': m.credit_score or 50,
                    'is_valid_guarantor': True,
                    'display_name': f"{m.full_name} ({m.email})"
                }
                for m in members
            ],
            'test_mode': True
        }
    
    # PRODUCTION MODE: Only return valid guarantors
    result = await db.execute(
        select(User)
        .filter(
            User.id != user.id,
            enum_text(User.status) == "ACTIVE",
            enum_text(User.role) == "MEMBER"
        )
        .order_by(User.full_name)
        .limit(50)
    )
    members = result.scalars().all()
    
    valid_guarantors = []
    for member in members:
        validation = await GuarantorService.validate_guarantor(db, member.id, user.id)
        if validation['valid']:
            valid_guarantors.append({
                'id': member.id,
                'full_name': member.full_name,
                'email': member.email,
                'credit_score': member.credit_score,
                'is_valid_guarantor': True,
                'display_name': f"{member.full_name} ({member.email})"
            })
    
    return {
        'guarantors': valid_guarantors,
        'test_mode': False
    }

@api_router.get("/liquidity", response_model=LiquidityStatusResponse)
async def get_liquidity_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the cooperative's current liquidity status"""
    status = await LiquidityService.get_liquidity_status(db)
    return status

@api_router.post("/loans/apply")
async def apply_for_loan(
    loan_data: LoanApplicationCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Apply for a loan with guarantor validation"""
    # Validate the loan request (respects test mode)
    validation = await LoanEligibilityService.validate_loan_request(
        db, user, loan_data.amount, loan_data.guarantor_id
    )
    
    is_test_mode = validation.get('test_mode', False)
    
    if not validation['valid']:
        raise HTTPException(
            status_code=400,
            detail={
                'message': 'Loan application rejected',
                'reasons': validation['reasons']
            }
        )
    
    # Calculate loan details using reducing balance
    interest_rate = await SettingsService.get_float(db, 'loan_interest_rate')
    loan_calc = LoanCalculationService.calculate_reducing_balance(
        loan_data.amount, interest_rate, loan_data.duration_months
    )
    
    loan_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    
    try:
        # Create the loan using raw SQL to handle enum type
        await db.execute(
            text("""
                INSERT INTO loans (id, user_id, amount, duration_months, interest_rate, 
                    monthly_payment, total_repayment, remaining_balance, purpose, 
                    guarantor_id, status, created_at)
                VALUES (:id, :user_id, :amount, :duration_months, :interest_rate,
                    :monthly_payment, :total_repayment, :remaining_balance, :purpose,
                    :guarantor_id, 'PENDING'::loanstatus, :created_at)
            """),
            {
                "id": loan_id,
                "user_id": user.id,
                "amount": loan_data.amount,
                "duration_months": loan_data.duration_months,
                "interest_rate": interest_rate,
                "monthly_payment": loan_calc['monthly_payment'],
                "total_repayment": loan_calc['total_repayment'],
                "remaining_balance": loan_calc['total_repayment'],
                "purpose": loan_data.purpose,
                "guarantor_id": loan_data.guarantor_id if not is_test_mode else None,
                "created_at": now
            }
        )
        
        # Create guarantor record if not in test mode
        if loan_data.guarantor_id and not is_test_mode:
            await GuarantorService.create_guarantor_record(
                db, loan_id, loan_data.guarantor_id, loan_data.relationship_to_guarantor
            )
        
        # Create notification
        notif_id = str(uuid.uuid4())
        await db.execute(
            text("""
                INSERT INTO notifications (id, user_id, title, message, type, is_read, created_at)
                VALUES (:id, :user_id, :title, :message, :type, :is_read, :created_at)
            """),
            {
                "id": notif_id,
                "user_id": user.id,
                "title": "Loan Application Submitted",
                "message": f"Your loan application for ₦{loan_data.amount:,.2f} has been submitted for review." + (" [TEST MODE]" if is_test_mode else ""),
                "type": "loan_applied",
                "is_read": False,
                "created_at": now
            }
        )
        
        await db.commit()
        
        logging.info(f"[LOAN APPLY] User {user.id} applied for loan {loan_id}, amount: {loan_data.amount}, test_mode: {is_test_mode}")
        
        return {
            'message': 'Loan application submitted successfully' + (' [TEST MODE]' if is_test_mode else ''),
            'loan_id': loan_id,
            'amount': loan_data.amount,
            'monthly_payment': loan_calc['monthly_payment'],
            'total_repayment': loan_calc['total_repayment'],
            'test_mode': is_test_mode
        }
        
    except Exception as e:
        await db.rollback()
        logging.error(f"[LOAN APPLY] Failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create loan application: {str(e)}")

@api_router.put("/profile/kyc")
async def update_kyc_info(
    kyc_data: KYCUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user's CAC/KYC information"""
    update_data = kyc_data.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(user, key, value)
    
    # If any KYC field is updated, set status to pending for re-verification
    if update_data:
        user.kyc_status = "PENDING"
    
    await db.commit()
    await db.refresh(user)
    
    return {'message': 'KYC information updated', 'kyc_status': user.kyc_status.value}

@api_router.get("/profile/enhanced", response_model=EnhancedUserResponse)
async def get_enhanced_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get enhanced user profile with all financial information"""
    return EnhancedUserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        role=get_status_value(user.role),
        status=user.status or 'pending',
        is_approved=user.is_approved,
        business_name=user.business_name,
        business_type=user.business_type,
        cac_registration_number=user.cac_registration_number,
        kyc_status=user.kyc_status or 'pending',
        savings_balance=user.savings_balance or 0,
        shares_balance=user.shares_balance or 0,
        locked_collateral=user.locked_collateral or 0,
        available_savings=(user.savings_balance or 0) - (user.locked_collateral or 0),
        credit_score=user.credit_score or 50,
        total_contributions=user.total_contributions or 0,
        total_loans_taken=user.total_loans_taken or 0,
        total_loans_repaid=user.total_loans_repaid or 0,
        membership_months=user.membership_duration_months if hasattr(user, 'membership_duration_months') else 0,
        has_active_loan=bool(user.active_loan_id),
        created_at=user.created_at
    )

# ============ Meetings Endpoints ============

@api_router.get("/meetings/next")
async def get_next_meeting(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the next scheduled meeting"""
    meeting = await MeetingService.get_or_create_next_meeting(db)
    return {
        'id': meeting.id,
        'title': meeting.title,
        'meeting_date': meeting.meeting_date.isoformat(),
        'meeting_time': meeting.meeting_time,
        'location': meeting.location,
        'agenda': meeting.agenda,
        'status': meeting.status
    }

@api_router.get("/meetings/upcoming")
async def get_upcoming_meetings(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get upcoming meetings"""
    meetings = await MeetingService.get_upcoming_meetings(db, limit=5)
    return [
        {
            'id': m.id,
            'title': m.title,
            'meeting_date': m.meeting_date.isoformat(),
            'meeting_time': m.meeting_time,
            'status': m.status
        }
        for m in meetings
    ]

@api_router.post("/meetings/{meeting_id}/topics")
async def submit_meeting_topic(
    meeting_id: str,
    topic_type: str,
    title: str,
    description: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Submit a topic/enquiry for a meeting"""
    topic = MeetingTopic(
        meeting_id=meeting_id,
        submitted_by=user.id,
        topic_type=topic_type,
        title=title,
        description=description
    )
    db.add(topic)
    await db.commit()
    
    return {'message': 'Topic submitted successfully', 'topic_id': topic.id}

# ============ Shares Endpoints ============

@api_router.post("/shares/purchase")
async def purchase_shares(
    purchase: SharePurchaseCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Request to purchase shares"""
    result = await SharesService.purchase_shares(db, user.id, purchase.amount)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['reason'])
    
    return result

@api_router.get("/shares/balance")
async def get_shares_balance(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's share balance and history"""
    share_unit = await SettingsService.get_float(db, 'share_unit')
    
    result = await db.execute(
        select(ShareTransaction)
        .filter(ShareTransaction.user_id == user.id)
        .order_by(ShareTransaction.created_at.desc())
        .limit(10)
    )
    transactions = result.scalars().all()
    
    return {
        'shares_balance': user.shares_balance or 0,
        'share_unit_price': share_unit,
        'total_value': (user.shares_balance or 0) * share_unit,
        'recent_transactions': [
            {
                'id': t.id,
                'type': t.transaction_type,
                'shares': t.shares_count,
                'amount': t.amount,
                'status': t.status,
                'date': t.created_at.isoformat()
            }
            for t in transactions
        ]
    }

# ============ Withdrawal Endpoints ============

@api_router.post("/withdrawals/request")
async def request_withdrawal(
    request: WithdrawalRequestCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Request a withdrawal (savings or shares)"""
    # Check if user has active loan
    if user.active_loan_id and request.withdrawal_type != 'emergency':
        raise HTTPException(
            status_code=400,
            detail="Cannot withdraw while you have an active loan. Contact admin for emergency withdrawal."
        )
    
    # Check available balance
    available = (user.savings_balance or 0) - (user.locked_collateral or 0)
    if request.withdrawal_type == 'savings' and request.amount > available:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient available savings. Available: ₦{available:,.2f}"
        )
    
    # Calculate eligible date based on notice period
    notice_days = await SettingsService.get_int(db, 'withdrawal_notice_days')
    if request.withdrawal_type == 'shares':
        notice_days = await SettingsService.get_int(db, 'share_exit_notice_days')
    
    eligible_date = datetime.now(timezone.utc) + timedelta(days=notice_days)
    
    withdrawal = WithdrawalRequest(
        user_id=user.id,
        amount=request.amount,
        withdrawal_type=request.withdrawal_type,
        eligible_date=eligible_date
    )
    db.add(withdrawal)
    await db.commit()
    
    return {
        'message': f'Withdrawal request submitted. Eligible date: {eligible_date.date()}',
        'request_id': withdrawal.id,
        'notice_days': notice_days,
        'eligible_date': eligible_date.isoformat()
    }

# ============ Admin Enhanced Endpoints ============

@api_router.get("/admin/liquidity", response_model=LiquidityStatusResponse)
async def admin_get_liquidity(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: Get detailed liquidity status"""
    return await LiquidityService.get_liquidity_status(db)

@api_router.patch("/admin/users/{user_id}/kyc")
async def admin_verify_kyc(
    user_id: str,
    status: str,  # 'verified' or 'rejected'
    note: Optional[str] = None,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: Verify or reject a user's KYC"""
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.kyc_status = "VERIFIED" if status == 'verified' else "REJECTED"
    user.kyc_verified_at = datetime.now(timezone.utc)
    user.kyc_verified_by = admin.id
    user.admin_note = note
    
    # If verified, also activate the member
    if status == 'verified':
        user.status = "ACTIVE"
        user.is_approved = True
    
    await db.commit()
    
    # Create notification
    await create_notification(
        db, user.id,
        f"KYC {status.capitalize()}",
        f"Your CAC/KYC verification has been {status}." + (f" Note: {note}" if note else ""),
        f"kyc_{status}"
    )
    await db.commit()
    
    return {'message': f'KYC {status}', 'user_id': user_id}

@api_router.patch("/admin/loans/{loan_id}/approve-enhanced")
async def admin_approve_loan_enhanced(
    loan_id: str,
    note: Optional[str] = None,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: Approve a loan with collateral locking"""
    result = await db.execute(select(Loan).filter(Loan.id == loan_id))
    loan = result.scalar_one_or_none()
    
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    
    if loan.status != "PENDING":
        raise HTTPException(status_code=400, detail="Loan is not pending")
    
    # Check liquidity
    liquidity_check = await LiquidityService.check_loan_approval(db, loan.amount)
    if not liquidity_check['can_approve']:
        raise HTTPException(status_code=400, detail=liquidity_check['reason'])
    
    # Lock collateral (use a portion of borrower's savings)
    collateral_amount = min(loan.amount * 0.5, (await db.get(User, loan.user_id)).savings_balance or 0)
    if collateral_amount > 0:
        await CollateralService.lock_collateral(db, loan.user_id, loan_id, collateral_amount)
    
    # Update loan
    loan.status = "APPROVED"
    loan.approved_at = datetime.now(timezone.utc)
    loan.approved_by = admin.id
    loan.approval_note = note
    loan.due_date = datetime.now(timezone.utc) + timedelta(days=30)  # First payment due in 30 days
    
    # Update user's active loan
    user = await db.get(User, loan.user_id)
    if user:
        user.active_loan_id = loan.id
        user.total_loans_taken = (user.total_loans_taken or 0) + loan.amount
    
    await db.commit()
    
    # Create notification
    await create_notification(
        db, loan.user_id,
        "Loan Approved!",
        f"Your loan of ₦{loan.amount:,.2f} has been approved. First payment due: {loan.due_date.date()}",
        "loan_approved"
    )
    await db.commit()
    
    return {'message': 'Loan approved', 'loan_id': loan_id, 'collateral_locked': collateral_amount}

@api_router.get("/admin/settings")
async def admin_get_settings(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: Get all system settings"""
    result = await db.execute(select(SystemSettings))
    settings = result.scalars().all()
    
    return [
        {
            'key': s.key,
            'value': s.value,
            'description': s.description
        }
        for s in settings
    ]

@api_router.put("/admin/settings/{key}")
async def admin_update_setting(
    key: str,
    value: str,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: Update a system setting"""
    await SettingsService.set_setting(db, key, value, admin.id)
    return {'message': f'Setting {key} updated', 'value': value}

@api_router.post("/admin/test-mode/toggle")
async def toggle_test_mode(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: Toggle test mode on/off"""
    current = await SettingsService.get_bool(db, 'test_mode')
    new_value = 'false' if current else 'true'
    await SettingsService.set_setting(db, 'test_mode', new_value, admin.id)
    
    import logging
    logging.info(f"[TEST MODE] Toggled by admin {admin.id}: {current} -> {new_value == 'true'}")
    
    return {
        'test_mode': new_value == 'true',
        'message': f"Test mode {'enabled' if new_value == 'true' else 'disabled'}",
        'warning': 'TEST MODE ACTIVE - Loan eligibility rules are bypassed!' if new_value == 'true' else None
    }

@api_router.get("/admin/test-mode/status")
async def get_test_mode_status(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: Get current test mode status"""
    test_mode = await SettingsService.get_bool(db, 'test_mode')
    override_user = await SettingsService.get_setting(db, 'test_user_override')
    
    return {
        'test_mode': test_mode,
        'test_user_override': override_user or None,
        'description': {
            'test_mode': 'When enabled, ALL users bypass loan eligibility rules',
            'test_user_override': 'Specific user ID that bypasses rules even when test_mode is false'
        }
    }

@api_router.put("/admin/test-mode/user-override")
async def set_test_user_override(
    user_id: str = None,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: Set a specific user to bypass eligibility rules"""
    await SettingsService.set_setting(db, 'test_user_override', user_id or '', admin.id)
    
    import logging
    if user_id:
        logging.info(f"[TEST MODE] User override set by admin {admin.id}: {user_id}")
    else:
        logging.info(f"[TEST MODE] User override cleared by admin {admin.id}")
    
    return {
        'test_user_override': user_id or None,
        'message': f"Test user override {'set to ' + user_id if user_id else 'cleared'}"
    }

@api_router.get("/admin/meetings")
async def admin_get_meetings(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: Get all meetings"""
    result = await db.execute(
        select(Meeting).order_by(Meeting.meeting_date.desc()).limit(20)
    )
    meetings = result.scalars().all()
    
    return [
        {
            'id': m.id,
            'title': m.title,
            'meeting_date': m.meeting_date.isoformat(),
            'meeting_time': m.meeting_time,
            'location': m.location,
            'status': m.status,
            'agenda': m.agenda,
            'notes': m.notes
        }
        for m in meetings
    ]

@api_router.post("/admin/meetings")
async def admin_create_meeting(
    meeting_data: MeetingCreate,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: Create a new meeting"""
    meeting = Meeting(
        title=meeting_data.title,
        meeting_date=meeting_data.meeting_date,
        meeting_time=meeting_data.meeting_time,
        location=meeting_data.location,
        agenda=meeting_data.agenda,
        created_by=admin.id
    )
    db.add(meeting)
    await db.commit()
    
    return {'message': 'Meeting created', 'meeting_id': meeting.id}

@api_router.put("/admin/meetings/{meeting_id}")
async def admin_update_meeting(
    meeting_id: str,
    notes: Optional[str] = None,
    agenda: Optional[str] = None,
    status: Optional[str] = None,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: Update meeting details"""
    result = await db.execute(select(Meeting).filter(Meeting.id == meeting_id))
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if notes is not None:
        meeting.notes = notes
    if agenda is not None:
        meeting.agenda = agenda
    if status is not None:
        meeting.status = status
        if status == 'completed':
            meeting.completed_at = datetime.now(timezone.utc)
    
    await db.commit()
    return {'message': 'Meeting updated'}

@api_router.post("/admin/meetings/{meeting_id}/attendance")
async def admin_mark_attendance(
    meeting_id: str,
    user_id: str,
    attended: bool = True,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: Mark attendance for a meeting"""
    # Check if record exists
    result = await db.execute(
        select(MeetingAttendance).filter(
            MeetingAttendance.meeting_id == meeting_id,
            MeetingAttendance.user_id == user_id
        )
    )
    record = result.scalar_one_or_none()
    
    if record:
        record.attended = attended
        record.marked_by = admin.id
        record.marked_at = datetime.now(timezone.utc)
    else:
        record = MeetingAttendance(
            meeting_id=meeting_id,
            user_id=user_id,
            attended=attended,
            marked_by=admin.id
        )
        db.add(record)
    
    await db.commit()
    return {'message': 'Attendance marked'}

@api_router.patch("/admin/loans/{loan_id}/recover")
async def admin_trigger_recovery(
    loan_id: str,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: Trigger recovery process for an overdue loan"""
    result = await DefaultRecoveryService.process_overdue_loan(db, loan_id)
    return result

@api_router.get("/admin/stats-enhanced")
async def admin_get_enhanced_stats(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: Get enhanced dashboard statistics"""
    # Basic stats
    total_members = await db.execute(
        select(func.count(User.id)).filter(enum_text(User.role) == "MEMBER")
    )
    approved_members = await db.execute(
        select(func.count(User.id)).filter(enum_text(User.role) == "MEMBER", User.is_approved == True)
    )
    pending_members = await db.execute(
        select(func.count(User.id)).filter(enum_text(User.role) == "MEMBER", User.is_approved == False)
    )
    
    # Financial stats
    total_savings = await db.execute(
        select(func.coalesce(func.sum(User.savings_balance), 0)).filter(enum_text(User.role) == "MEMBER")
    )
    total_shares = await db.execute(
        select(func.coalesce(func.sum(User.shares_balance), 0)).filter(enum_text(User.role) == "MEMBER")
    )
    
    # Loan stats
    pending_loans = await db.execute(
        select(func.count(Loan.id)).filter(enum_text(Loan.status) == "PENDING")
    )
    active_loans = await db.execute(
        select(func.count(Loan.id)).filter(enum_text(Loan.status).in_(["APPROVED", "ACTIVE"]))
    )
    total_disbursed = await db.execute(
        select(func.coalesce(func.sum(Loan.amount), 0)).filter(enum_text(Loan.status).in_(["APPROVED", "ACTIVE", "COMPLETED"]))
    )
    
    # Risky loans (overdue)
    risky_loans = await db.execute(
        select(func.count(Loan.id)).filter(Loan.days_overdue > 7)
    )
    
    # Contribution stats
    pending_contributions = await db.execute(
        select(func.count(Contribution.id)).filter(enum_text(Contribution.status) == "PENDING")
    )
    total_contributions = await db.execute(
        select(func.coalesce(func.sum(Contribution.amount), 0)).filter(enum_text(Contribution.status) == "APPROVED")
    )
    
    # Liquidity
    liquidity = await LiquidityService.get_liquidity_status(db)
    
    # Next meeting
    next_meeting = await MeetingService.get_or_create_next_meeting(db)
    
    return {
        'total_members': total_members.scalar() or 0,
        'approved_members': approved_members.scalar() or 0,
        'pending_members': pending_members.scalar() or 0,
        'total_savings': total_savings.scalar() or 0,
        'total_shares': total_shares.scalar() or 0,
        'total_contributions': total_contributions.scalar() or 0,
        'pending_contributions_count': pending_contributions.scalar() or 0,
        'total_loans_disbursed': total_disbursed.scalar() or 0,
        'pending_loans_count': pending_loans.scalar() or 0,
        'active_loans_count': active_loans.scalar() or 0,
        'risky_loans_count': risky_loans.scalar() or 0,
        'liquidity_ratio': liquidity['liquidity_ratio'],
        'liquidity_healthy': liquidity['is_healthy'],
        'next_meeting_date': next_meeting.meeting_date.isoformat() if next_meeting else None
    }

# ============ Health Check ============

@api_router.get("/")
async def root():
    return {"message": "Bosere Cooperative API v2.0 - Supabase Edition", "status": "healthy"}

@api_router.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat(), "database": "PostgreSQL via Supabase"}

# ============ Development-Only Endpoints ============
# These endpoints are ONLY available when APP_ENV != "production"

APP_ENV = os.environ.get('APP_ENV', 'development')

if APP_ENV != 'production':
    @api_router.post("/dev/test-mode/enable")
    async def dev_enable_test_mode(db: AsyncSession = Depends(get_db)):
        """DEV ONLY: Enable test mode for loan eligibility testing"""
        await SettingsService.set_setting(db, 'test_mode', 'true', 'dev')
        logging.info("[TEST MODE] Enabled via dev endpoint")
        return {'test_mode': True, 'message': 'Test mode enabled'}

    @api_router.post("/dev/test-mode/disable")
    async def dev_disable_test_mode(db: AsyncSession = Depends(get_db)):
        """DEV ONLY: Disable test mode"""
        await SettingsService.set_setting(db, 'test_mode', 'false', 'dev')
        logging.info("[TEST MODE] Disabled via dev endpoint")
        return {'test_mode': False, 'message': 'Test mode disabled'}

    @api_router.get("/dev/test-mode/status")
    async def dev_get_test_mode(db: AsyncSession = Depends(get_db)):
        """DEV ONLY: Check test mode status"""
        test_mode = await SettingsService.get_bool(db, 'test_mode')
        override_user = await SettingsService.get_setting(db, 'test_user_override')
        return {'test_mode': test_mode, 'test_user_override': override_user or None}
    
    @api_router.post("/dev/seed/admin")
    async def dev_seed_admin(db: AsyncSession = Depends(get_db)):
        """DEV ONLY: Seed a local admin account (redirect from /seed/admin)"""
        result = await db.execute(select(User).where(User.email == "admin@bosere.com"))
        existing = result.scalar_one_or_none()
        
        if existing:
            return {"message": "Admin already exists", "email": "admin@bosere.com"}
        
        admin = User(
            email="admin@bosere.com",
            full_name="Bosere Admin",
            phone="+2348000000000",
            role="ADMIN",
            is_approved=True,
            supabase_user_id="admin-local"
        )
        
        db.add(admin)
        await db.commit()
        
        return {"message": "Admin created. Create this user in Supabase Auth separately.", "email": "admin@bosere.com"}

    logging.info("[SERVER] Development mode - DEV endpoints enabled")
else:
    logging.info("[SERVER] Production mode - DEV endpoints disabled")

# Include the router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
