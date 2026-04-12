# QUICK REFERENCE - GABE'S WEEK 1-2

Keep this open Mon-Fri. Everything you need is here.

---

## Monday (4/15) - Setup

```bash
# Step 1: Navigate
cd c:\Users\hofer\OneDrive\Documents\GitHub\ClonerMarketbulletsllc\WEBSITECHARTS

# Step 2: Check Node.js (should show v18+)
node --version

# Step 3: Install
npm install

# Step 4: Create .env.local
copy .env.local.template .env.local
# Edit .env.local with Gary's credentials
```

Done? Text: "Setup complete"

---

## Mon-Wed (4/15-4/17) - Test Endpoints

**Start dev server:**
```bash
npm run dev
```

**Test all 4 endpoints (in new terminal):**
```bash
node test-api.js http://localhost:3000
```

Expected output:
```
✅ PASS: Health Endpoint
✅ PASS: Charts Endpoint
✅ PASS: Quotes Endpoint
✅ PASS: BoR Status Endpoint

Results: Passed 4/4
```

**Issues?** Check [README_PHASE1.md](README_PHASE1.md) Part 2 troubleshooting

---

## Thursday (4/18) - Production Build

```bash
# Stop dev server: Ctrl+C

# Build
npm run build

# Start production server
npm start

# Test (same as before)
node test-api.js http://localhost:3000
```

If all 4 tests pass, you're good for Friday.

---

## Friday (4/19) - Deploy

```bash
# Commit & push
git add .
git commit -m "Phase 1 API ready for production"
git push origin main

# Then:
# 1. Go to https://vercel.com/dashboard
# 2. Import GitHub repo: ClonerMarketbulletsllc
# 3. Add these environment variables:
#    - GOOGLE_SHEETS_PROJECT_ID
#    - GOOGLE_SHEETS_PRIVATE_KEY
#    - GOOGLE_SHEETS_CLIENT_EMAIL
#    - GOOGLE_SHEETS_ID
# 4. Deploy
# 5. Wait for green checkmark
# 6. Get your URL (like https://marketbullets-api-xyz.vercel.app)
```

**Verify live:**
```bash
node test-api.js https://YOUR-VERCEL-URL
```

**Success?** Text Gary: "Phase 1 live at [URL]"

---

## Documentation Quick Links

| Question | Answer |
|----------|--------|
| What does each endpoint do? | [API_SPECIFICATION.md](API_SPECIFICATION.md) |
| My endpoint returned an error | [README_PHASE1.md](README_PHASE1.md) Part 2 |
| How do I test my changes? | `node test-api.js http://localhost:3000` |
| Port 3000 is already in use | `npm run dev -- -p 3001` |
| npm install failed | Check Node.js v18+, try again |
| What's my deployment URL? | Vercel dashboard under "Deployments" |
| Can I update charts without redeploying? | Yes! Gary edits Google Sheet, changes live in 30-60s |

---

## Files You'll Actually Use

- `package.json` — Defines npm scripts
- `next.config.js` — Build settings (don't need to edit)
- `vercel.json` — Deployment settings (don't need to edit)
- `.env.local` — Your credentials (KEEP SECRET)
- `/pages/api/` — The 4 endpoints (read-only)
- `/lib/google-sheets.js` — Data integration (read-only)
- `test-api.js` — Your testing tool

---

## Success Checklist

- [ ] Monday: 4 setup steps complete
- [ ] Tue: `npm run dev` works
- [ ] Tue: `node test-api.js ...` shows 4/4 passed
- [ ] Wed: Caching headers present (check README_PHASE1 Part 3)
- [ ] Thu: `npm run build` && `npm start` works
- [ ] Fri: Git push successful
- [ ] Fri: Vercel deployment successful
- [ ] Fri: `node test-api.js https://...` shows 4/4 passed
- [ ] Fri: Gary notified with URL

**All 8 ✅? You're done. Phase 1 complete.**

---

## Emergency: Something Broke

**First:** Stop everything (Ctrl+C), take a breath.

**Check this order:**

1. **npm install failed?**
   - Delete folder: `rm -r node_modules .next`
   - Run again: `npm install`

2. **Endpoint returns error?**
   - Check .env.local has all 4 variables (no typos)
   - Check Google Sheet credentials from Gary are correct
   - See troubleshooting in [README_PHASE1.md](README_PHASE1.md) Part 2

3. **Port 3000 already in use?**
   - `npm run dev -- -p 3001`

4. **Vercel deployment failed?**
   - Check env vars are spelled EXACTLY (case-sensitive)
   - See [README_PHASE1.md](README_PHASE1.md) Part 5

5. **Still stuck?**
   - Stop everything
   - Delete .next folder
   - Run `npm run dev` fresh
   - Test again

---

## You Have 20+ Hours Over 5 Days

- Monday: 2 hours (setup + initial tests)
- Tuesday: 4 hours (endpoint validation)
- Wednesday: 3 hours (caching + performance)
- Thursday: 3 hours (production build testing)
- Friday: 4 hours (deployment + verification)
- **Buffer:** 4 hours for unexpected issues

Don't rush. Follow the steps exactly as written.

---

**Last thing:** After Friday deployment, take a screenshot of the test results and send to Gary. 

You're done with Phase 1. Good work.
