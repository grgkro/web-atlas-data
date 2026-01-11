# Deploy to Cloudflare Pages (FREE)

Cloudflare Pages is excellent for static sites with a generous free tier and fast global CDN.

## Quick Deploy Steps

### 1. Push Code to GitHub (if not already)

```bash
git add .
git commit -m "Prepare for Cloudflare Pages deployment"
git push
```

### 2. Deploy via Cloudflare Pages UI

1. **Go to Cloudflare Pages**
   - Visit https://pages.cloudflare.com
   - Sign in (or create free account with email/GitHub)

2. **Create a New Project**
   - Click "Create a project"
   - Choose "Connect to Git"
   - Authorize Cloudflare to access GitHub
   - Select your `web-atlas-data` repository

3. **Configure Build Settings** ⚠️ IMPORTANT
   
   You'll see these fields - fill them like this:
   
   - **Project name**: `web-atlas` (or whatever you want)
   
   - **Production branch**: `main` (or `master`)
   
   - **Framework preset**: `None` (or leave empty)
   
   - **Root directory**: ⚠️ **LEAVE EMPTY** (or `/`) - Must be root where package.json is located
   
   - **Build command**: 
     ```
     npm install && npm run build
     ```
   
   - **Build output directory**: 
     ```
     web
     ```
   
   - **Deploy command**: ⚠️ **MUST USE**: `echo "Deploy complete"` or `true`
     - ❌ **DO NOT use**: `npx wrangler deploy` (that's for Workers - will fail!)
     - ❌ **DO NOT use**: `npx wrangler pages deploy` (won't work in this context)
     - ✅ **USE**: `echo "Deploy complete"` or `true` (harmless no-op)
     - Pages deploys automatically after build completes - deploy command is ignored anyway
   
   - **Environment variables**: (none needed)
   
   **⚠️ CRITICAL**: Make sure "Root directory" is **EMPTY** or set to `/`. 
   Cloudflare must find `package.json` at the repository root.

4. **Click "Save and Deploy"**

5. **Wait for Build** (~1-2 minutes)
   - Watch the build logs in real-time
   - You'll see: `npm install` → `npm run build` → deployment
   - ✅ Build successful = your site is live!

6. **Your site URL** will be: `https://web-atlas.pages.dev` (or similar)

### 3. Connect Custom Domain (web-atlas.org)

1. **In Cloudflare Pages Dashboard**
   - Go to your project
   - Click "Custom domains" tab
   - Click "Set up a custom domain"
   - Enter: `web-atlas.org`

2. **DNS Configuration**
   - Cloudflare will show you the exact DNS records needed
   - **Option A**: If your domain is already on Cloudflare DNS:
     - Just click "Continue" - it's automatic!
   
   - **Option B**: If domain is elsewhere (GoDaddy, Namecheap, etc.):
     - Add a **CNAME** record:
       - Name: `@` (or root domain)
       - Value: `web-atlas.pages.dev` (your Pages URL)
     - Or add **A** records (Cloudflare will provide IPs)

3. **SSL Certificate**
   - Cloudflare automatically provisions free SSL
   - Usually active within 1-2 minutes
   - Your site will be at `https://web-atlas.org` ✅

## Alternative: Deploy via CLI (wrangler)

If you prefer command line:

```bash
# Install Wrangler CLI
npm install -g wrangler

# Login to Cloudflare
npx wrangler login

# Deploy (from project root)
npx wrangler pages deploy web --project-name=web-atlas
```

**Note**: This is a one-time deploy. For continuous deployment, use GitHub integration instead.

## What Happens on Each Deploy

1. ✅ Cloudflare runs `npm install && npm run build`
2. ✅ Build script generates indexes in `dist/indexes/`
3. ✅ Indexes are copied to `web/indexes/`
4. ✅ Cloudflare serves everything from the `web/` directory
5. ✅ Your site is live at your Pages URL!

## Free Tier Limits

- ✅ **Unlimited** builds per month
- ✅ **Unlimited** requests
- ✅ **Unlimited** bandwidth
- ✅ **500** builds per month (free tier) - more than enough
- ✅ Free SSL certificates
- ✅ Custom domains
- ✅ Preview deployments for PRs

## Troubleshooting

### Build fails
- Check build logs in Cloudflare dashboard
- Verify Node.js version (should auto-detect, but might need Node 18+)
- Ensure `package.json` scripts are correct
- Check that `web/indexes/` exists after build

### "Deploy command" field confusion
- **Leave it empty!** Cloudflare Pages deploys automatically after build
- If the field is required, you can put: `echo "Deploy complete"` (it won't be used)

### Indexes not loading (404 errors)
- Verify `web/indexes/` directory exists after build
- Check build logs to confirm `npm run copy-indexes` ran
- Try accessing `/indexes/categories.json` directly in browser
- Verify redirect rules aren't needed (Pages serves `web/` directory as root)

### Custom domain not working
- Wait 5-10 minutes for DNS propagation
- Verify DNS records are correct (use `dig` or `nslookup`)
- Check Cloudflare dashboard shows domain is active
- Verify SSL certificate is issued (should show in dashboard)

## Advanced: Branch Previews

Cloudflare Pages automatically creates preview deployments for every branch and PR:
- Each branch gets its own URL: `https://branch-name.pages.dev`
- PRs get preview URLs you can share
- Perfect for testing before merging!

## Why Cloudflare Pages?

- ⚡ **Fastest** global CDN (Cloudflare's network)
- 🔒 **Free SSL** (automatic)
- 💰 **Generous** free tier (unlimited bandwidth!)
- 🌍 **Global** performance
- 🔧 **Simple** setup
- 📊 **Built-in** analytics (optional upgrade)

---

**That's it!** Your site should be live in ~2 minutes. 🚀

