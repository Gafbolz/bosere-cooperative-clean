# Bosere Cooperative - Changelog

## [1.0.0] - March 24, 2026 - Production Ready

### Added
- Production deployment configuration
- `APP_ENV` environment variable to control dev endpoints
- Comprehensive `DEPLOYMENT.md` guide
- `.env.example` files for frontend and backend
- Minimal `requirements.prod.txt` for production

### Changed
- Dev endpoints (`/api/dev/*`) now conditionally loaded based on `APP_ENV`
- Updated `README.md` with production notes
- Updated `PRD.md` with current feature status

### Security
- Seed admin endpoint disabled in production mode
- Test mode endpoints disabled in production mode

---

## [0.9.0] - March 24, 2026 - Bug Fixes & Guarantor Feature

### Fixed
- Registration "body stream already read" error
- Contribution approval PostgreSQL ENUM type issues
- Admin pending contributions filter
- Guarantor selection now uses proper dropdown (not free-text)

### Added
- Test Mode for loan eligibility (admin-toggleable)
- `/api/guarantor/available` endpoint for dropdown selection
- Raw SQL queries for ENUM column updates

---

## [0.8.0] - March 2026 - Phase 3 & 4: Frontend Complete

### Added
- Member Profile & KYC page
- Enhanced Dashboard with eligibility display
- Loan application with guarantor selection
- Admin KYC verification interface
- Admin enhanced loan management

---

## [0.7.0] - March 2026 - Phase 1 & 2: Backend Services

### Added
- Database schema for all enhanced tables
- SettingsService for configurable settings
- LoanEligibilityService with tier-based rules
- GuarantorService with validation logic
- CollateralService for loan collateral
- CreditScoreService (0-100 scale)
- LiquidityService for cooperative health
- DefaultRecoveryService for overdue loans
- LoanCalculationService (2% reducing balance)
- MeetingService for monthly meetings

### Database Tables
- system_settings
- share_transactions
- withdrawal_requests
- guarantors
- meetings
- meeting_attendance
- meeting_topics
- dividend_records
- member_dividends

---

## [0.1.0] - Initial Release

### Added
- Basic cooperative app structure
- User registration and authentication
- Contribution submission and tracking
- Loan application system
- Admin approval workflows
- Supabase integration (PostgreSQL + Auth)
