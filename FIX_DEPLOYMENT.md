# Fix: JSON Files Returning HTML Instead of JSON

## Problem
The deployed site at https://web-atlas-data.pages.dev returns HTML instead of JSON when accessing `/indexes/categories.json`, causing the error:
```
Error loading data: Unexpected token '<', "<!DOCTYPE "... is not valid JSON
```

## Solution: Commit and Redeploy

The fix has been made - you need to commit and push the changes:

```bash
git add web/_headers web/_redirects tools/copy-indexes.js
git commit -m "Fix: Ensure JSON files are served correctly in Cloudflare Pages"
git push
```

After pushing, Cloudflare Pages will automatically rebuild and redeploy.

## What Was Fixed

1. **Created `web/_headers`** - Cloudflare Pages configuration to serve JSON files with correct Content-Type
2. **Fixed `web/_redirects`** - Removed incorrect redirect that was causing issues  
3. **Enhanced `tools/copy-indexes.js`** - Added validation to ensure files are copied correctly

## Alternative: If Issue Persists

If after redeploying the JSON files still return HTML, check:

### 1. Verify Files Are Deployed
- Go to Cloudflare Pages dashboard → Your deployment
- Check build logs to confirm `npm run copy-indexes` ran successfully
- Verify `web/indexes/` directory exists in the build output

### 2. Check Cloudflare Pages Settings
- Go to Settings → Functions → Check if there's a catch-all route
- Disable any "SPA mode" or "Catch-all routing" settings
- Cloudflare Pages should serve static files directly

### 3. Test Direct Access
Try accessing the JSON files directly:
- https://web-atlas-data.pages.dev/indexes/categories.json
- https://web-atlas-data.pages.dev/indexes/sites-en.json

If these still return HTML, the files aren't being deployed correctly.

### 4. Manual Fix in Cloudflare Dashboard
If needed, you can configure headers manually:
- Go to Settings → Functions and Pages
- Add a Function or Middleware to handle `/indexes/*` routes
- But this shouldn't be necessary with `_headers` file

## Expected Behavior After Fix

After redeploying:
- ✅ `/indexes/categories.json` returns valid JSON
- ✅ `/indexes/sites-en.json` returns valid JSON
- ✅ Content-Type header is `application/json`
- ✅ UI loads and displays categories and sites correctly

---

**Next step**: Commit and push the changes, then wait for Cloudflare Pages to rebuild! 🚀


