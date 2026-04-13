# WEEK 1 CHECKLIST - GABE

Copy & paste this into your task manager. Check off each day.

## MONDAY, APRIL 15 - ENVIRONMENT SETUP (60 min)

- [ ] 8:00 AM - Open MONDAY_FIRST_STEPS.md
- [ ] 8:05 AM - Navigate to project directory
- [ ] 8:10 AM - Check Node.js version (should be 18+)
- [ ] 8:15 AM - If missing, install Node.js LTS
- [ ] 8:30 AM - Run `npm install` (10-15 min wait)
- [ ] 8:50 AM - Copy `.env.local.template` → `.env.local`
- [ ] 9:00 AM - Fill in 4 Google Sheets credentials
- [ ] 9:05 AM - Save file
- [ ] **DONE** - Text Gary: "Phase 1 setup complete"

---

## TUESDAY, APRIL 16 - HEALTH CHECKS (90 min)

- [ ] Start development server: `npm run dev`
- [ ] Test Health endpoint: `curl http://localhost:3000/api/health`
- [ ] Test Charts endpoint: `curl http://localhost:3000/api/charts`
- [ ] Verify response includes all 55+ charts
- [ ] Verify charts grouped by category
- [ ] Test Quotes endpoint: `curl http://localhost:3000/api/quotes`
- [ ] Verify quote math (totalVolume, maxChange calculated correctly)
- [ ] **RED FLAG?** If any endpoint returns error - debug using README_PHASE1.md Part 2 troubleshooting
- [ ] **DONE** - Take screenshot of all 4 endpoints working

---

## WEDNESDAY, APRIL 17 - BoR & CACHING (60 min)

- [ ] Test BoR endpoint: `curl http://localhost:3000/api/bor-status`
- [ ] Verify phase is one of: LOADED, LOCKED & LOADED, AIM, FIRE
- [ ] Verify color is valid hex code
- [ ] Check cache headers: `curl -i http://localhost:3000/api/health`
- [ ] Record Cache-Control values for all 4 endpoints
- [ ] All should have `max-age=60` or `max-age=30`
- [ ] **DONE** - Prepare caching summary for Gary

---

## THURSDAY, APRIL 18 - PRODUCTION BUILD TEST (60 min)

- [ ] Stop dev server: `Ctrl+C`
- [ ] Run production build: `npm run build`
- [ ] Wait for "compiled successfully" message
- [ ] Start production server: `npm start`
- [ ] Test all 4 endpoints again
- [ ] Verify production response same as dev
- [ ] Record response times for each endpoint
- [ ] **DONE** - Green light for Vercel deployment

---

## FRIDAY, APRIL 19 - VERCEL DEPLOYMENT (90 min)

- [ ] Verify GitHub repository is up to date: `git status`
- [ ] If changes, commit: `git add . && git commit -m "Phase 1 API ready for production"`
- [ ] Push to GitHub: `git push origin main`
- [ ] Go to https://vercel.com/dashboard
- [ ] Create new project from GitHub repo
- [ ] Add 4 environment variables:
  - GOOGLE_SHEETS_PROJECT_ID
  - GOOGLE_SHEETS_PRIVATE_KEY
  - GOOGLE_SHEETS_CLIENT_EMAIL
  - GOOGLE_SHEETS_ID
- [ ] Deploy
- [ ] Wait for "Deployment Complete" message
- [ ] Get Vercel URL from dashboard
- [ ] Test live endpoints: `curl https://YOUR-VERCEL-URL/api/health`
- [ ] All 4 endpoints return 200 OK
- [ ] **DONE** - **Text Gary Phase 1 URL**: "MarketBullets Phase 1 API live: [URL]"

---

## ISSUES?

| Error | Checklist |
|-------|-----------|
| "npm: command not found" | Run Step 2 of MONDAY_FIRST_STEPS |
| Endpoint returns 500 | Check Google Sheets credentials in .env.local |
| Deployment fails on Vercel | Verify all 4 env vars spelled exactly (case-sensitive) |
| Port 3000 in use | `npm run dev -- -p 3001` |

---

**Total Hours:** ~20 hours spread over 5 days = 4 hours/day average

**End Result:** Phase 1 API live on Vercel, all endpoints verified, ready for Phase 2 frontend.
