# Deploy to Netlify (Recommended - Free & Easy)

Netlify offers a generous free tier perfect for static sites like Web Atlas.

## Quick Deploy Steps

### Option 1: Deploy via Netlify UI (Easiest)

1. **Push your code to GitHub** (if not already done)
   ```bash
   git add .
   git commit -m "Prepare for deployment"
   git push
   ```

2. **Go to Netlify**
   - Visit https://app.netlify.com
   - Sign up/login (free with GitHub)

3. **Connect Repository**
   - Click "Add new site" → "Import an existing project"
   - Choose GitHub and authorize Netlify
   - Select your `web-atlas-data` repository

4. **Configure Build Settings**
   Netlify should auto-detect from `netlify.toml`, but verify:
   - **Build command**: `npm install && npm run build`
   - **Publish directory**: `web`
   - **Node version**: 18 (optional, but recommended)

5. **Deploy**
   - Click "Deploy site"
   - Wait for build to complete (~1-2 minutes)
   - Your site will be live at `https://random-name-12345.netlify.app`

### Option 2: Deploy via Netlify CLI

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Login
netlify login

# Deploy (from project root)
netlify deploy --prod
```

## Connect Custom Domain (web-atlas.org)

1. **In Netlify Dashboard**
   - Go to your site → "Domain settings"
   - Click "Add custom domain"
   - Enter `web-atlas.org`

2. **Update DNS**
   Netlify will show you the DNS records to add:
   - Add a CNAME record in your DNS provider:
     - Name: `@` (or root domain)
     - Value: `your-site-name.netlify.app`
   - Or add an A record (Netlify will provide IP addresses)

3. **SSL Certificate**
   - Netlify automatically provisions free SSL
   - Usually active within 1-2 minutes
   - Your site will be at `https://web-atlas.org`

## What Happens on Each Deploy

1. Netlify runs `npm install && npm run build`
2. Build script generates indexes in `dist/indexes/`
3. Indexes are copied to `web/indexes/`
4. Netlify serves everything from the `web/` directory
5. Your site is live!

## Free Tier Limits

- ✅ 100GB bandwidth/month (plenty for a directory site)
- ✅ 300 build minutes/month
- ✅ Unlimited sites
- ✅ Free SSL
- ✅ Custom domains
- ✅ Form handling (if needed later)

## Environment Variables

None needed! Everything is static.

## Troubleshooting

### Build fails
- Check Node version (should be 18+)
- Check build logs in Netlify dashboard
- Verify `package.json` has correct scripts

### Indexes not loading
- Verify `web/indexes/` exists after build
- Check browser console for 404 errors
- Ensure `netlify.toml` redirects are correct

### Custom domain not working
- Wait 5-10 minutes for DNS propagation
- Check DNS records are correct
- Verify SSL certificate is active in Netlify dashboard

## Continuous Deployment

By default, Netlify deploys on every push to `main` branch. You can:
- Set up branch previews for PRs
- Configure deploy contexts (production vs preview)
- Set up build hooks for manual deploys

---

**That's it!** Your Web Atlas should be live in ~2 minutes. 🚀


