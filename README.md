# Bosere Cooperative

A full-stack cooperative finance platform for managing member savings, contributions, loans, and shares.

## Features

### For Members
- **Dashboard**: View savings balance, loan eligibility, credit score
- **Contributions**: Submit and track monthly contributions
- **Loans**: Apply for loans (up to 3x savings based on membership tier)
- **Guarantor System**: Search and select loan guarantors
- **Profile & KYC**: Submit business documents for verification
- **Meetings**: View upcoming cooperative meetings

### For Administrators
- **Member Management**: Approve members, verify KYC documents
- **Contribution Processing**: Review and approve contributions
- **Loan Management**: Approve/reject loans, track repayments
- **System Settings**: Configure interest rates, share units, thresholds
- **Liquidity Monitoring**: Track cooperative financial health

### Business Rules
| Membership Duration | Loan Multiplier |
|---------------------|-----------------|
| < 3 months | Not eligible |
| 3-6 months | 1x savings |
| 6-12 months | 2x savings |
| 12+ months | 3x savings |

- **Interest Rate**: 2% monthly (reducing balance)
- **Guarantor Requirements**: 6+ months membership, credit score 40+, completed loan history
- **Liquidity Threshold**: 70% (prevents over-lending)

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React, Tailwind CSS, Shadcn UI |
| Backend | FastAPI, SQLAlchemy |
| Database | PostgreSQL (Supabase) |
| Authentication | Supabase Auth |

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- Supabase account (free tier works)

### 1. Clone & Setup

```bash
git clone <repository-url>
cd bosere-cooperative
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Supabase credentials

# Run server
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### 3. Frontend Setup

```bash
cd frontend
yarn install

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run development server
yarn start
```

### 4. Create Admin User

1. Register through the app
2. Run in Supabase SQL Editor:
```sql
UPDATE users 
SET role = 'ADMIN', is_approved = true, status = 'ACTIVE', kyc_status = 'VERIFIED'
WHERE email = 'your-email@example.com';
```

## Environment Variables

### Backend
```bash
# Supabase PostgreSQL (use pooler connection)
DATABASE_URL=postgresql://postgres.xxx:password@aws-0-region.pooler.supabase.com:6543/postgres

# Supabase API
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGci...

# Optional
CORS_ORIGINS=*
APP_ENV=development  # Set to "production" to disable dev endpoints
```

### Frontend
```bash
REACT_APP_BACKEND_URL=http://localhost:8001
REACT_APP_SUPABASE_URL=https://xxx.supabase.co
REACT_APP_SUPABASE_ANON_KEY=eyJhbGci...
```

## Project Structure

```
bosere-cooperative/
├── backend/
│   ├── server.py           # FastAPI routes & endpoints
│   ├── models.py           # SQLAlchemy database models
│   ├── services.py         # Business logic services
│   ├── database.py         # Database configuration
│   ├── requirements.txt    # Python dependencies
│   ├── Dockerfile          # Container deployment
│   └── .env.example        # Environment template
├── frontend/
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── contexts/       # React context (Auth, Theme)
│   │   ├── pages/          # Page components
│   │   │   ├── admin/      # Admin pages
│   │   │   └── dashboard/  # Member dashboard pages
│   │   └── lib/            # Utilities & Supabase client
│   ├── package.json        # Node dependencies
│   ├── vercel.json         # Vercel deployment config
│   └── .env.example        # Environment template
├── DEPLOYMENT.md           # Production deployment guide
└── README.md               # This file
```

## Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed deployment instructions:

- **Frontend**: Vercel (recommended), Netlify, or any static host
- **Backend**: Railway, Render, Fly.io, or Docker
- **Database**: Supabase (PostgreSQL)

## API Documentation

When running locally, visit: `http://localhost:8001/docs`

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/auth/register` | POST | Register new user |
| `/api/dashboard/stats` | GET | Dashboard statistics |
| `/api/contributions` | GET/POST | Contributions |
| `/api/loans/apply` | POST | Apply for loan |
| `/api/eligibility` | GET | Check loan eligibility |
| `/api/admin/users` | GET | List all members (admin) |

## Production Notes

- Set `APP_ENV=production` to disable development endpoints (`/api/dev/*`)
- Configure specific CORS origins in production
- Enable email confirmation in Supabase for production
- Use connection pooling (Supabase port 6543)

## License

MIT License
