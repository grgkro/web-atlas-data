# Fix Cloudflare Pages Build - Can't Find package.json

## Problem
Build fails with: `Could not read package.json: Error: ENOENT: no such file or directory`

Even with root directory set to `/`, Cloudflare can't find your `package.json`.

## Solution: Use Diagnostic Build Command

Try this **Build command** instead to see what's happening:

```bash
pwd && ls -la && if [ -f package.json ]; then echo "✅ package.json found"; npm install && npm run build; else echo "❌ package.json NOT found"; find . -name "package.json" 2>/dev/null; exit 1; fi
```

This will:
1. Show current directory
2. List all files
3. Check if package.json exists
4. If found, proceed with build
5. If not found, search for it and show where it might be

## Alternative Solution: Use Build Script

1. **Create `build.sh`** in your repository root (already created for you)

2. **Make it executable** (Cloudflare will handle this, but verify in git):
   ```bash
   git add build.sh
   git commit -m "Add Cloudflare Pages build script"
   git push
   ```

3. **In Cloudflare Pages settings, use:**
   - **Build command**: `bash build.sh`
   - **Deploy command**: `echo "Deploy complete"` (or leave empty if possible)

## Quick Fix: Verify package.json is Committed

Run this locally to verify:
```bash
git ls-files package.json
git show HEAD:package.json | head -5
```

If these commands work, `package.json` IS in your repository.

## Common Causes & Fixes

### 1. Wrong Branch
- Make sure Cloudflare is deploying from `main` (or whatever branch has `package.json`)
- In Cloudflare Pages → Settings → Builds & deployments → Check "Production branch"

### 2. Repository Not Cloned Correctly
- Try deleting and recreating the Cloudflare Pages project
- Make sure you're connecting to the correct GitHub repository

### 3. Root Directory Still Wrong
- Double-check: Root directory = `/` (just a forward slash, nothing else)
- Not `/web`, not `./`, not empty string - literally `/`

### 4. Deploy Command Issue
⚠️ **IMPORTANT**: The "Deploy command" field:
- ✅ **Good**: `echo "done"` or `true` (harmless commands)
- ❌ **Wrong**: `npx wrangler deploy` (that's for Cloudflare Workers!)
- ❌ **Wrong**: `npx wrangler pages deploy` (doesn't work in this context)

**For Cloudflare Pages, the deploy happens automatically after build. The deploy command field is rarely needed.**

## Recommended Settings

```
Root directory: /
Build command: npm install && npm run build
Deploy command: echo "Deploy complete"  (if field is required)
Build output directory: web
Framework preset: None
Production branch: main (or master)
```

## Test Locally First

Before deploying, verify the build works locally:
```bash
# Clone repo fresh (simulate Cloudflare)
git clone <your-repo-url> test-build
cd test-build
npm install
npm run build
# Should create web/indexes/ with JSON files
```

## Still Not Working?

### Option 1: Switch to Netlify (Easier)
Netlify has better auto-detection. See `DEPLOY_NETLIFY.md`.

### Option 2: Use GitHub Actions + Cloudflare Pages
Instead of direct Git integration, use GitHub Actions to build, then deploy:
1. Build in GitHub Actions
2. Upload artifacts
3. Deploy to Cloudflare Pages via Wrangler CLI

### Option 3: Manual Diagnostic
Add this to your build command to see exactly what Cloudflare sees:
```bash
echo "=== DEBUG INFO ===" && pwd && ls -la && echo "=== Looking for package.json ===" && find . -name "package.json" 2>/dev/null && echo "=== Proceeding with build ===" && npm install && npm run build
```

---

**Most likely fix**: Use the diagnostic build command above to see what Cloudflare actually sees! 🔍


