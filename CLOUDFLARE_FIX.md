# Fix Cloudflare Pages Build Error

## Error: `Could not read package.json`

This error means Cloudflare Pages can't find your `package.json` file.

## Solution 1: Check Root Directory Setting (Most Common Fix)

In Cloudflare Pages dashboard:

1. Go to your project → **Settings** → **Builds & deployments**
2. Click **"Edit configuration"** on your production environment
3. **Find "Root directory"** field
4. **Make sure it's set to `/` or leave it EMPTY** ⚠️
   - ❌ **Wrong**: `/web` or `./` or any other path
   - ✅ **Correct**: `/` or **EMPTY**
5. Click **Save**

**Why?** Cloudflare needs to find `package.json` at the repository root. If root directory is set to a subdirectory, it won't find it.

## Solution 2: Verify Repository Structure

Make sure your repo structure is:
```
your-repo/
├── package.json       ← Must be at root
├── package-lock.json
├── tools/
├── sites/
├── web/
└── ...
```

## Solution 3: Recreate Project (If above doesn't work)

1. In Cloudflare Pages, go to **Settings** → **General**
2. Delete the project (or create a new one)
3. **Create new project** → Connect to Git
4. Select your repository
5. **Important settings:**
   - **Root directory**: ⚠️ **LEAVE EMPTY** (don't put `/web` here!)
   - **Build command**: `npm install && npm run build`
   - **Build output directory**: `web` (this is where the built files go)
   - **Framework preset**: `None`
6. Click **Save and Deploy**

## Solution 4: Check Git Branch

Make sure you're deploying from the correct branch:
- **Production branch**: Should be `main` (or `master` depending on your repo)
- Verify `package.json` exists in that branch

## Quick Checklist

Before deploying, verify:
- [ ] `package.json` exists in repository root
- [ ] `package.json` is committed to git
- [ ] Root directory is `/` or EMPTY in Cloudflare
- [ ] Build output directory is `web` (not `/web` or `./web`)
- [ ] Build command is `npm install && npm run build`

## If Still Not Working

Try this build command instead:
```bash
cd /opt/buildhome/repo && npm install && npm run build
```

But this should NOT be necessary if root directory is correct.

## Alternative: Use Netlify Instead

If Cloudflare Pages continues to have issues, Netlify is equally good and often easier:
- See `DEPLOY_NETLIFY.md` for instructions
- Netlify auto-detects `netlify.toml` settings

---

**Most likely fix**: Set "Root directory" to `/` or EMPTY in Cloudflare Pages settings! 🎯


