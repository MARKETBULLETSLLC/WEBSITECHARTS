# MONDAY MORNING, APRIL 15 - FIRST STEPS FOR GABE

**Time required:** 20-30 minutes

This is your exact entry point. Start here Monday morning. No decisions needed - just follow these 4 steps.

---

## Step 1: Navigate to Project Directory

```bash
cd c:\Users\hofer\OneDrive\Documents\GitHub\ClonerMarketbulletsllc\WEBSITECHARTS
```

Verify you see: `package.json`, `next.config.js`, folders: `pages/`, `lib/`, `public/`

---

## Step 2: Install Node.js (If Not Already Installed)

**Check if Node.js is installed:**
```bash
node --version
npm --version
```

If both return version numbers (e.g., v18.x.x), **skip to Step 3**.

**If not installed:**
1. Go to https://nodejs.org/
2. Download **LTS version** (currently 20.x)
3. Run the installer, accept defaults
4. Restart your terminal
5. Verify: `node --version` and `npm --version`

---

## Step 3: Install Dependencies

```bash
npm install
```

**Expected output:**
- "added X packages"
- No critical errors
- Folder `node_modules/` appears

**If it fails:**
- Check Node.js version (should be 18+)
- Delete `node_modules/` folder
- Try `npm install` again
- Contact Gary if still failing

---

## Step 4: Create Environment File

Copy the template:
```bash
copy .env.local.template .env.local
```

**Open .env.local** and add Google Sheets credentials (Gary provides these):
```
GOOGLE_SHEETS_PROJECT_ID=xxx
GOOGLE_SHEETS_PRIVATE_KEY="-----BEGIN..."
GOOGLE_SHEETS_CLIENT_EMAIL=xxx
GOOGLE_SHEETS_ID=xxx
```

---

## Done - Ready for Next Steps

When all 4 steps complete successfully:
1. Open `README_PHASE1.md` - your complete Week 1-2 guide
2. Start Part 1: "Verify API Endpoints Work" (use `node test-api.js`)
3. Text Gary: "Phase 1 setup complete, starting verification"

**Total time to this point:** 30 minutes

---

## Troubleshooting

| Error | Solution |
|-------|----------|
| "npm: command not found" | Node.js not installed - do Step 2 |
| "npm ERR! 404" | Check internet connection, try `npm install` again |
| ".env.local not found" | Copy didn't work - manually create file with content from .env.local.template |
| Port 3000 in use | `npm run dev -- -p 3001` |

That's it. Monday morning, execute steps 1-4, then open README_PHASE1.md.
