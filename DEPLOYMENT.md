# Deployment Guide

This guide covers deploying the Web Atlas UI to various hosting platforms.

## Quick Start

1. Build the indexes: `npm run build`
2. The UI files are in `web/` directory
3. The indexes are in `dist/indexes/` (and copied to `web/indexes/` for local dev)

## Cloudflare Pages

1. Connect your GitHub repository to Cloudflare Pages
2. Configure build settings:
   - **Build command**: `npm install && npm run build`
   - **Output directory**: `web`
   - **Root directory**: `/` (leave empty)
   - **Deploy command**: ⚠️ **LEAVE EMPTY** - Pages deploys automatically after build
3. Deploy!
   - Cloudflare will build and deploy automatically
   - Your site will be live at `https://your-project.pages.dev`

**See `DEPLOY_CLOUDFLARE.md` for detailed step-by-step instructions.**

### Cloudflare Pages via CLI (Optional)

If you prefer command line instead of GitHub integration:

```bash
npm install -g wrangler
npx wrangler login
npx wrangler pages deploy web --project-name=web-atlas
```

**Note**: GitHub integration is recommended for automatic deployments on every push.

## Vercel

1. Import your GitHub repository into Vercel
2. Vercel will auto-detect `vercel.json`
3. The build and routing are configured automatically
4. Deploy!

### Manual Vercel Deployment

```bash
vercel --prod
```

## GitHub Pages

GitHub Pages can serve static files from a branch or directory.

1. Enable GitHub Pages in repository settings
2. Set source to `/web` directory (or a branch with built files)
3. For GitHub Actions build:
   - The `.github/workflows/build-indexes.yml` workflow builds indexes
   - You'll need an additional workflow to deploy to `gh-pages` branch
   - Example: Use `peaceiris/actions-gh-pages@v3` action

### GitHub Pages Workflow Example

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
      - run: npm ci && npm run build
      - uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./web
```

## Netlify

1. Connect your GitHub repository to Netlify
2. Configure build:
   - **Build command**: `npm install && npm run build`
   - **Publish directory**: `web`
3. Add redirect rule in `netlify.toml` or dashboard:
   ```toml
   [[redirects]]
     from = "/indexes/*"
     to = "/dist/indexes/:splat"
     status = 200
   ```
4. Deploy!

## Local Development

For local testing, you can use any static file server:

```bash
# Using Python
cd web && python -m http.server 8000

# Using Node.js (npx)
npm run dev  # Uses serve package

# Using PHP
cd web && php -S localhost:8000
```

The app will load indexes from `web/indexes/` in local development mode.

## Custom Domain Setup

Once deployed:

1. Point your domain DNS to your hosting provider:
   - **Cloudflare Pages**: Add a CNAME record pointing to `*.pages.dev`
   - **Vercel**: Add a CNAME record pointing to `cname.vercel-dns.com`
   - **GitHub Pages**: Add A/CNAME records per GitHub's instructions

2. Configure SSL (usually automatic with modern hosts)

3. Update DNS for `web-atlas.org` to point to your host

## Environment Variables

No environment variables are needed for the basic deployment. The UI loads data from static JSON files.

## Caching

The indexes are static JSON files that should be cached:
- Recommended: Cache-Control: `public, max-age=3600, s-maxage=3600`
- Indexes are regenerated on every merge to `main` via CI

