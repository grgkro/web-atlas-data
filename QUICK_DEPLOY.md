# Quick Deploy Guide 🚀

**TL;DR**: Push to GitHub → Connect to Netlify → Done in 2 minutes!

## Step-by-Step: Deploy to Netlify (FREE)

### 1. Push Your Code to GitHub (if not already)

```bash
git add .
git commit -m "Add UI and deployment config"
git push
```

### 2. Deploy to Netlify (2 minutes)

**Option A: Via Web UI (Easiest)**
1. Go to https://app.netlify.com
2. Sign in with GitHub (free account)
3. Click "Add new site" → "Import an existing project"
4. Select your `web-atlas-data` repository
5. Netlify auto-detects settings from `netlify.toml`:
   - ✅ Build: `npm install && npm run build`
   - ✅ Publish: `web`
6. Click "Deploy site"
7. Wait ~1-2 minutes for build
8. ✅ **Your site is live!** (e.g., `https://amazing-site-12345.netlify.app`)

**Option B: Via CLI (If you prefer command line)**
```bash
npm install -g netlify-cli
netlify login
netlify deploy --prod
```

### 3. Connect Custom Domain (web-atlas.org)

1. In Netlify dashboard → Your site → "Domain settings"
2. Click "Add custom domain"
3. Enter: `web-atlas.org`
4. Follow Netlify's DNS instructions:
   - Add a CNAME record pointing to your Netlify URL, OR
   - Add A records (Netlify provides IPs)
5. Wait 5-10 minutes for DNS propagation
6. SSL is automatic and free! ✅

---

## Alternative: Cloudflare Pages (Also Free)

### Why Cloudflare Pages?
- ⚡ Fastest global CDN
- 🔒 Free SSL
- 🌍 Excellent performance
- 💰 Unlimited free builds

### Deploy Steps:
1. Go to https://pages.cloudflare.com
2. Sign in with GitHub
3. "Create a project" → Select your repo
4. Build settings:
   - Framework preset: None
   - Build command: `npm install && npm run build`
   - Build output directory: `web`
5. Click "Save and Deploy"
6. ✅ **Live in ~1 minute!**

### Connect Domain:
1. In Cloudflare Pages → Your site → "Custom domains"
2. Add `web-atlas.org`
3. Update DNS (Cloudflare will show you exactly what to add)

---

## Alternative: Vercel (Also Free)

### Why Vercel?
- ⚡ Very fast
- 🔧 Great developer experience
- 📊 Built-in analytics (free tier)

### Deploy Steps:
1. Go to https://vercel.com
2. Sign in with GitHub
3. "Import Project" → Select your repo
4. Vercel auto-detects `vercel.json` ✅
5. Click "Deploy"
6. ✅ **Live in ~30 seconds!**

---

## Comparison

| Feature | Netlify | Cloudflare Pages | Vercel |
|---------|---------|------------------|--------|
| **Free Tier** | ✅ Generous | ✅ Unlimited | ✅ Generous |
| **Build Time** | ~1-2 min | ~1 min | ~30 sec |
| **CDN Performance** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Ease of Setup** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Custom Domain** | ✅ Free | ✅ Free | ✅ Free |
| **SSL** | ✅ Auto | ✅ Auto | ✅ Auto |
| **Best For** | General use | Maximum speed | Developer UX |

**Recommendation**: All three are excellent! Netlify is the easiest to set up, Cloudflare Pages is fastest globally, and Vercel has great DX.

---

## Post-Deployment Checklist

- [ ] Site loads correctly
- [ ] Categories display properly
- [ ] Sites list works when clicking categories
- [ ] Indexes load (check browser console: `/indexes/categories.json` and `/indexes/sites-en.json`)
- [ ] Custom domain connected (if applicable)
- [ ] SSL certificate active (check HTTPS)
- [ ] Test on mobile device

---

## Troubleshooting

**Site loads but shows "Loading..." forever?**
- Check browser console (F12) for errors
- Verify `/indexes/categories.json` and `/indexes/sites-en.json` are accessible
- Check build logs in your hosting provider's dashboard

**Build fails?**
- Make sure Node.js 18+ is available
- Check `package.json` scripts are correct
- Review build logs for specific errors

**Indexes not found?**
- Verify `web/indexes/` directory exists after build
- Check redirect rules in `netlify.toml` (or equivalent)
- Ensure build script runs `npm run copy-indexes`

---

## Next Steps After Deployment

1. ✅ Share your site URL!
2. 🔧 Update README with live URL
3. 🔄 Set up auto-deploy (already done if connected to GitHub)
4. 📊 Add analytics (optional - Google Analytics, Plausible, etc.)
5. 🎨 Customize UI (add logo, colors, etc.)

---

**You're all set!** 🎉


