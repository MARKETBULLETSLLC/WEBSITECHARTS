# PHASE 1 IMPLEMENTATION GUIDE - WEEK 1-2 (Gabe)

**Timeline:** April 15-26, 2026  
**Goal:** Verify & deploy Phase 1 API to Vercel  
**Responsibility:** Gabe (CTO)  
**Expected Hours:** 20+ hours spread over two weeks  

---

## ✅ PRE-REQS (Completed Before You Start)

- [x] Node.js installed (v18+)
- [x] npm install complete - `node_modules/` folder exists
- [x] .env.local created with Google Sheets credentials
- [x] All 4 source code files in `/pages/api/` 
- [x] Google Sheets integration library in `/lib/google-sheets.js`
- [x] Configuration complete (next.config.js, vercel.json)

---

## PART 1: Environment Verification (Monday, 15 min)

**Goal:** Confirm dev environment works

```bash
# Terminal 1 - Start dev server
npm run dev

# Terminal 2 - Test endpoints (while dev server runs)
# Option A: Manual test
curl http://localhost:3000/api/health
curl http://localhost:3000/api/charts
curl http://localhost:3000/api/quotes
curl http://localhost:3000/api/bor-status

# Option B: Automated test (recommended)
node test-api.js http://localhost:3000
```

**Expected Outcome (Manual Test):**
- All four endpoints return JSON
- No red error pages
- Terminal shows "compiled successfully"

**Expected Outcome (Automated Test):**
```
✅ PASS: Health Endpoint
✅ PASS: Charts Endpoint
✅ PASS: Quotes Endpoint
✅ PASS: BoR Status Endpoint

Results: Passed 4/4
```

**If it fails:**
- Check .env.local has all 4 variables
- Verify Google Sheets credentials are valid
- Stop dev server: Ctrl+C
- Delete .next folder: `rm -r .next`
- Restart: `npm run dev`

**Success Criteria:**
- ✅ All 4 endpoints respond with JSON
- ✅ No authentication errors
- ✅ Response time < 2 seconds

**Timeline:** Monday 15 min - confirm working

---

## PART 2: API Response Validation (Mon-Wed)

**Goal:** Verify each endpoint returns correct data structure

### 2.1 Health Endpoint Validation

```bash
# Request
curl http://localhost:3000/api/health

# Expected Response Pattern
{
  "status": "healthy",
  "timestamp": "2026-04-15T12:34:56Z",
  "service": "MarketBullets API Phase 1",
  "version": "1.0.0",
  "uptime": 45.234,
  "memory": {
    "used": 125,
    "total": 512
  }
}
```

**Validation Checklist:**
- [ ] Returns HTTP 200
- [ ] `status` === "healthy"
- [ ] Has `timestamp` (ISO format)
- [ ] Has `version`
- [ ] Memory fields are numbers

**Troubleshoot if:**
- Returns 500 error - check console for JS syntax issues
- Memory always 0 - check Node.js version (needs 18+)

---

### 2.2 Charts Endpoint Validation

```bash
# Request
curl http://localhost:3000/api/charts

# Expected Response Pattern
{
  "success": true,
  "timestamp": "2026-04-15T12:34:56Z",
  "count": 55,
  "data": {
    "Wheat Futures": [
      {
        "id": "WHEAT_SRW_D",
        "name": "SRW Wheat Daily",
        "category": "Wheat Futures",
        "url": "https://tradingnavigator.example.com/...",
        "lastUpdated": "2026-04-15T08:30:00Z",
        "description": "CBOT Soft Red Winter..."
      }
    ],
    "Spreads & Ratios": [ ... ],
    "Currencies": [ ... ]
  }
}
```

**Validation Checklist:**
- [ ] Returns HTTP 200
- [ ] `success` === true
- [ ] `count` > 50 (should be 55+ in live data)
- [ ] Charts grouped by `category`
- [ ] Each chart has: `id`, `name`, `url`, `lastUpdated`
- [ ] URLs are valid (start with http/https)

**If failing:**
- Verify Google Sheets has "Charts" sheet with headers
- Check GOOGLE_SHEETS_ID in .env.local is correct
- Run: `npm run dev` to reload

---

### 2.3 Quotes Endpoint Validation

```bash
# Request
curl http://localhost:3000/api/quotes

# Expected Response Pattern
{
  "success": true,
  "timestamp": "2026-04-15T12:34:56Z",
  "count": 8,
  "summary": {
    "totalVolume": 1245000,
    "maxChange": 3.5,
    "minPrice": 520.25,
    "maxPrice": 580.75
  },
  "data": [
    {
      "contract": "ZWK25",
      "month": "May 2025",
      "bid": 545.25,
      "ask": 545.75,
      "last": 545.50,
      "change": 2.25,
      "volume": 124500,
      "timestamp": "2026-04-15T08:30:00Z"
    }
  ]
}
```

**Validation Checklist:**
- [ ] Returns HTTP 200
- [ ] `success` === true
- [ ] `summary` has: totalVolume, maxChange, minPrice, maxPrice
- [ ] Each quote has: contract, month, bid, ask, last, change, volume
- [ ] All numeric fields are actual numbers (not strings)
- [ ] Count matches data array length

**If failing:**
- Verify Google Sheets has "Quotes" sheet
- Check bid/ask/last/change are numeric (not text)
- Check volume is numeric

---

### 2.4 Box-o-Rox Status Endpoint Validation

```bash
# Request
curl http://localhost:3000/api/bor-status

# Expected Response Pattern
{
  "success": true,
  "timestamp": "2026-04-15T12:34:56Z",
  "phase": "LOCKED & LOADED",
  "color": "#FF6B6B",
  "description": "Setup complete"
}
```

**Validation Checklist:**
- [ ] Returns HTTP 200
- [ ] `success` === true
- [ ] `phase` is one of: LOADED, LOCKED & LOADED, AIM, FIRE
- [ ] `color` is valid hex color code (#RRGGBB)
- [ ] Has `description`

**Allowed phases & colors:**
- LOADED → #FFD700 (gold)
- LOCKED & LOADED → #FF6B6B (red)
- AIM → #4ECDC4 (cyan)
- FIRE → #FF0000 (red)

**Timeline:** Mon-Wed - 2-3 hours total validation

---

## PART 3: Caching & Performance Testing (Wed)

**Goal:** Verify caching headers work correctly

```bash
# Check cache headers
curl -i http://localhost:3000/api/health

# Expected headers
Cache-Control: public, max-age=60, s-maxage=60
```

**Cache Header Validation:**
- [ ] Health endpoint: max-age=60
- [ ] Charts endpoint: max-age=60, stale-while-revalidate=120
- [ ] Quotes endpoint: max-age=30, stale-while-revalidate=60
- [ ] BoR endpoint: max-age=60, stale-while-revalidate=120

**Why this matters:**
- Reduces API calls by 60x during peak usage
- Prevents Google Sheets rate limit hits
- Improves dashboard load time by 500-1000ms

**Timeline:** Wed - 30 min

---

## PART 4: Environment Setup for Deployment (Thu)

**Goal:** Prepare for Vercel deployment

### 4.1 Create Vercel Account

1. Go to https://vercel.com/login
2. Sign up with GitHub
3. Authorize access to your GitHub account
4. You're ready to deploy

### 4.2 Add Environment Variables to Vercel

**Via Vercel Dashboard:**
1. Create new project
2. Connect GitHub repo: `ClonerMarketbulletsllc`
3. Add environment variables (in Settings → Environment Variables):

```
GOOGLE_SHEETS_PROJECT_ID = [value from .env.local]
GOOGLE_SHEETS_PRIVATE_KEY = [value from .env.local]
GOOGLE_SHEETS_CLIENT_EMAIL = [value from .env.local]
GOOGLE_SHEETS_ID = [value from .env.local]
```

**Critical:** Use exact variable names - no typos

### 4.3 Test Production Build Locally

```bash
npm run build
npm start

# Test endpoints again
curl http://localhost:3000/api/health
```

**Expected Outcome:**
- Build completes with no errors
- "compiled successfully" message
- Endpoints respond same as dev mode

**If build fails:**
- Check for any `console.log` statements (remove them)
- Verify all imports are correct
- Check .env.local has all 4 variables

**Timeline:** Thu - 1 hour

---

## PART 5: Deploy to Vercel (Fri)

**Goal:** Push Phase 1 API live

### 5.1 Verify Git Setup

```bash
# Confirm you can push to GitHub
git status
git add .
git commit -m "Phase 1 API - Initial deployment"
git push origin main
```

### 5.2 Deploy via Vercel

**Option A: Via Dashboard (Recommended)**
1. Go to https://vercel.com/dashboard
2. Click "New Project"
3. Select GitHub repo
4. Configure environment variables (already done in Part 4.2)
5. Deploy

**Option B: Via Vercel CLI**
```bash
npm install -g vercel
vercel
# Follow prompts
```

### 5.3 Verify Deployment

Once deployed, Vercel gives you a URL like: `https://marketbullets-api.vercel.app`

```bash
# Test live endpoints with automated test script
node test-api.js https://YOUR-DEPLOYMENT-URL

# Or manually test individual endpoints
curl https://YOUR-DEPLOYMENT-URL/api/health
curl https://YOUR-DEPLOYMENT-URL/api/charts
```

**Expected Outcome:**
- All endpoints respond with 200
- Same JSON structure as local
- Response time < 1 second

---

## PART 6: Documentation & Handoff (Fri)

**Goal:** Prepare for Phase 2 (Frontend)

### 6.1 Create Deployment Summary

Create file: `PHASE1_DEPLOYED.md`

```markdown
# Phase 1 Deployment Summary

**Deployed:** Friday, April 26, 2026  
**URL:** https://YOUR-VERCEL-URL  
**Environment:** Production  

## Endpoints

- GET /api/health → Server status
- GET /api/charts → 55+ chart metadata
- GET /api/quotes → Current futures quotes
- GET /api/bor-status → Market phase (LOADED, LOCKED & LOADED, AIM, FIRE)

## Performance Metrics

- Health endpoint: 40ms avg response time
- Charts endpoint: 120ms avg (cached 60s)
- Quotes endpoint: 85ms avg (cached 30s)
- BoR endpoint: 50ms avg (cached 60s)

## Google Sheets Integration

- Status: ✅ Live
- Update frequency: Real-time on sheet edit
- Fallback data: Mock data if API fails
- Rate limit: 1,000 reads/min per project (no issues at current usage)

## Next Steps (Phase 2)

- Frontend: Astro-based dashboard
- Integration: Connect to these 4 endpoints
- Timeline: May 1 - June 15, 2026
```

### 6.2 Notify Gary

Send: "Phase 1 API live at [URL]. All 4 endpoints verified. Ready for frontend integration."

**Timeline:** Fri - 30 min

---

## SUCCESS CRITERIA - WEEK 1-2

- ✅ All 4 endpoints deployed to Vercel
- ✅ All endpoints return correct JSON structure
- ✅ Caching headers present
- ✅ Response times < 2 seconds local, < 1 second deployed
- ✅ No authentication errors in logs
- ✅ Phase 1 API URL documented
- ✅ Gary notified and ready for Phase 2

---

## Rollback Plan (If Deployment Fails)

1. In Vercel dashboard, click "Deployments"
2. Find previous successful deployment
3. Click "Promote to Production"
4. Immediate rollback - no downtime

---

## WEEK 1-2 DAILY CHECKLIST

| Date | Task | Status |
|------|------|--------|
| Mon 4/15 | Run MONDAY_FIRST_STEPS (Parts 1-4) | |
| Tue 4/16 | Validate Charts & Quotes endpoints | |
| Wed 4/17 | Validate BoR & Health endpoints + caching | |
| Thu 4/18 | Test production build locally | |
| Fri 4/19 | Deploy to Vercel + notify Gary | |

---

End of Phase 1. You're now ready for Phase 2 kickoff (May 1, 2026).
