# Bosere Cooperative - Production Deployment Guide

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│    Backend      │────▶│    Supabase     │
│   (Vercel)      │     │  (Railway/      │     │   (PostgreSQL   │
│   React SPA     │     │   Render/Fly)   │     │    + Auth)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

- **Frontend**: React SPA deployed on Vercel (or any static host)
- **Backend**: FastAPI Python API deployed on Railway, Render, or Fly.io
- **Database**: Supabase PostgreSQL with Row-Level Security
- **Authentication**: Supabase Auth (JWT-based)

---

## Prerequisites

1. **Supabase Account**: https://supabase.com (free tier available)
2. **Vercel Account**: https://vercel.com (free tier available)
3. **Backend Host Account**: Choose one:
   - Railway: https://railway.app
   - Render: https://render.com
   - Fly.io: https://fly.io

---

## Step 1: Supabase Setup

### 1.1 Create Project
1. Go to https://supabase.com and create a new project
2. Wait for the project to initialize (~2 minutes)
3. Note down these values from **Settings > API**:
   - **Project URL**: `https://[project-ref].supabase.co`
   - **Anon Public Key**: `eyJhbGci...`

### 1.2 Get Database Connection String
From **Settings > Database > Connection String > URI**:
```
postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
```

**Important**: Use the **pooler** connection (port 6543), NOT direct connection (port 5432).

### 1.3 Configure Authentication
1. Go to **Authentication > URL Configuration**
2. Set **Site URL** to your frontend domain (e.g., `https://your-app.vercel.app`)
3. Add your frontend domain to **Redirect URLs**
4. In **Authentication > Settings**:
   - Disable "Confirm email" for easier testing (enable in production)
   - Set "Minimum password length" to 6+

### 1.4 Database Tables
Tables are created automatically by the backend on first run. No manual SQL needed.

---

## Step 2: Backend Deployment

### Option A: Deploy to Railway (Recommended)

1. **Push code to GitHub** (or connect existing repo)

2. **Create Railway Project**
   - Go to https://railway.app
   - Click "New Project" > "Deploy from GitHub Repo"
   - Select your repository

3. **Configure Service**
   - Railway auto-detects Python
   - Set root directory to `backend` if monorepo

4. **Set Environment Variables**
   ```
   DATABASE_URL=postgresql://postgres.xxx:password@aws-0-region.pooler.supabase.com:6543/postgres
   SUPABASE_URL=https://xxx.supabase.co
   SUPABASE_ANON_KEY=eyJhbGci...
   CORS_ORIGINS=*
   APP_ENV=production
   ```

5. **Deploy**
   - Railway will build and deploy automatically
   - Note your service URL (e.g., `https://your-app.railway.app`)

### Option B: Deploy to Render

1. **Create Web Service**
   - Go to https://render.com
   - Click "New" > "Web Service"
   - Connect your GitHub repository

2. **Configure Build**
   ```
   Root Directory: backend
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn server:app --host 0.0.0.0 --port $PORT
   ```

3. **Set Environment Variables** (same as Railway)

4. **Deploy**

### Option C: Deploy to Fly.io

1. **Install flyctl**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Initialize and Deploy**
   ```bash
   cd backend
   fly launch
   fly secrets set DATABASE_URL="..." SUPABASE_URL="..." SUPABASE_ANON_KEY="..." APP_ENV="production"
   fly deploy
   ```

### Option D: Docker Deployment

The backend includes a Dockerfile:

```bash
cd backend
docker build -t bosere-backend .
docker run -p 8001:8001 \
  -e DATABASE_URL="..." \
  -e SUPABASE_URL="..." \
  -e SUPABASE_ANON_KEY="..." \
  -e APP_ENV="production" \
  bosere-backend
```

---

## Step 3: Frontend Deployment (Vercel)

### 3.1 Deploy to Vercel

1. **Import Project**
   - Go to https://vercel.com
   - Click "Import Project" > "Import Git Repository"
   - Select your repository

2. **Configure Build**
   - Framework Preset: Create React App
   - Root Directory: `frontend`
   - Build Command: `yarn build`
   - Output Directory: `build`

3. **Set Environment Variables**
   ```
   REACT_APP_BACKEND_URL=https://your-backend.railway.app
   REACT_APP_SUPABASE_URL=https://xxx.supabase.co
   REACT_APP_SUPABASE_ANON_KEY=eyJhbGci...
   ```

4. **Deploy**
   - Vercel will build and deploy
   - Note your frontend URL

### 3.2 Alternative: Static Hosting

Build locally and upload to any static host:
```bash
cd frontend
yarn install
yarn build
# Upload 'build' folder to Netlify, AWS S3, CloudFlare Pages, etc.
```

---

## Step 4: Post-Deployment Setup

### 4.1 Create Admin User

1. **Register** through your deployed frontend with your admin email

2. **Promote to Admin** via Supabase SQL Editor:
   ```sql
   UPDATE users 
   SET role = 'ADMIN', 
       is_approved = true, 
       status = 'ACTIVE', 
       kyc_status = 'VERIFIED'
   WHERE email = 'your-admin-email@example.com';
   ```

### 4.2 Verify Deployment

1. Visit `https://your-backend.railway.app/api/health`
   - Should return: `{"status": "healthy", ...}`

2. Visit your frontend URL
   - Should load the landing page

3. Test registration and login flow

### 4.3 Configure CORS (if needed)

If you get CORS errors, update `CORS_ORIGINS` in backend:
```
CORS_ORIGINS=https://your-frontend.vercel.app,https://custom-domain.com
```

---

## Environment Variables Reference

### Backend (.env)

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DATABASE_URL` | Yes | Supabase PostgreSQL connection string | `postgresql://postgres.xxx:pass@...` |
| `SUPABASE_URL` | Yes | Supabase project URL | `https://xxx.supabase.co` |
| `SUPABASE_ANON_KEY` | Yes | Supabase anonymous key | `eyJhbGci...` |
| `CORS_ORIGINS` | No | Allowed CORS origins | `*` or comma-separated URLs |
| `APP_ENV` | No | Environment mode | `development` or `production` |

### Frontend (.env)

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `REACT_APP_BACKEND_URL` | Yes | Backend API URL | `https://api.your-app.com` |
| `REACT_APP_SUPABASE_URL` | Yes | Supabase project URL | `https://xxx.supabase.co` |
| `REACT_APP_SUPABASE_ANON_KEY` | Yes | Supabase anonymous key | `eyJhbGci...` |

---

## Production Checklist

### Security
- [ ] Set `APP_ENV=production` (disables dev endpoints)
- [ ] Configure specific CORS origins (not `*`)
- [ ] Enable email confirmation in Supabase Auth
- [ ] Review Supabase RLS policies
- [ ] Use HTTPS for all URLs

### Performance
- [ ] Enable Supabase connection pooling (use port 6543)
- [ ] Configure database connection pool size
- [ ] Set up CDN for static assets (Vercel handles this)

### Monitoring
- [ ] Set up error tracking (Sentry, LogRocket)
- [ ] Configure backend logging
- [ ] Set up uptime monitoring

### Backup
- [ ] Enable Supabase Point-in-Time Recovery
- [ ] Document backup/restore procedures

---

## Troubleshooting

### "Connection refused" errors
- Verify DATABASE_URL uses pooler (port 6543)
- Check if backend service is running
- Verify environment variables are set

### CORS errors
- Set CORS_ORIGINS to include your frontend domain
- Verify REACT_APP_BACKEND_URL is correct (no trailing slash)

### Authentication failures
- Verify SUPABASE_URL and SUPABASE_ANON_KEY match in both frontend and backend
- Check Supabase Auth settings (Site URL, Redirect URLs)
- Clear browser storage and retry

### 500 Internal Server Error
- Check backend logs for detailed error message
- Verify database connection string is correct
- Ensure all required tables exist

### Admin access not working
- Verify user role is `ADMIN` (uppercase) in database
- Clear browser cache and re-login
- Check user's `is_approved` flag is `true`

---

## API Reference

### Public Endpoints
- `GET /api/health` - Health check
- `GET /api/` - API info

### Member Endpoints (Authenticated)
- `GET /api/auth/me` - Current user profile
- `GET /api/dashboard/stats` - Dashboard statistics
- `GET /api/contributions` - User's contributions
- `POST /api/contributions` - Submit contribution
- `GET /api/loans` - User's loans
- `POST /api/loans/apply` - Apply for loan
- `GET /api/eligibility` - Loan eligibility check
- `GET /api/guarantor/available` - Available guarantors

### Admin Endpoints
- `GET /api/admin/stats` - Admin dashboard
- `GET /api/admin/users` - All members
- `PATCH /api/admin/users/{id}/approve` - Approve member
- `GET /api/admin/contributions` - All contributions
- `PATCH /api/admin/contributions/{id}/approve` - Approve contribution
- `GET /api/admin/loans` - All loans
- `PATCH /api/admin/loans/{id}/approve` - Approve loan

---

## Support

For deployment issues:
1. Check backend logs for error details
2. Verify all environment variables
3. Test database connection separately
4. Review Supabase dashboard for auth/database issues
