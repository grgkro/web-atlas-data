# Atlas of the Web

A human-curated, open-source map of useful websites.

This repository contains structured data and a minimal UI proof-of-concept.

## Data Structure

### Source of Truth: Individual Site Files

Each website is stored as an individual YAML file:

```
sites/
  mdn-web-docs/
    site.yml
  freecodecamp/
    site.yml
  ...
```

### Site File Format (`sites/<id>/site.yml`)

```yaml
id: mdn-web-docs
url: https://developer.mozilla.org
category: Build
lenses: [education, reference]
quality: solid
title:
  en: MDN Web Docs
  de: MDN Web Docs  # Future translations
description:
  en: Comprehensive documentation and learning resources for web developers.
  de: Umfassende Doku und Lernressourcen für Webentwicklung.
```

### Generated Indexes

The build process generates JSON indexes for fast UI loading:

- `dist/indexes/categories.json` - Category list with counts
- `dist/indexes/sites-en.json` - Flat list of all sites (English)

## Development

### Prerequisites

- Node.js 18+
- npm

### Setup

```bash
npm install
```

### Build Indexes

```bash
npm run build
```

This generates the JSON indexes in `dist/indexes/`.

### Local Development

For local development, you can serve the web directory:

```bash
# Using Python
cd web && python -m http.server 8000

# Using Node.js (npx)
npx serve web

# Using PHP
cd web && php -S localhost:8000
```

Then open `http://localhost:8000` in your browser.

**Note:** For local development, copy the `dist/indexes` folder to `web/indexes` or use a server that serves both directories.

## Deployment

### Cloudflare Pages

1. Connect your GitHub repository to Cloudflare Pages
2. Set build command: `npm install && npm run build`
3. Set output directory: `web`
4. Add redirect rule: `/indexes/*` → `/dist/indexes/:splat`
5. Deploy

### Vercel

1. Import your GitHub repository
2. Vercel will auto-detect `vercel.json`
3. Deploy

### GitHub Pages

GitHub Pages can serve static files. You'll need to:
1. Enable GitHub Pages in repository settings
2. Point to `/web` directory
3. Build indexes on each push (see `.github/workflows/build-indexes.yml`)

## What belongs here
- Useful websites
- Non-spammy
- Safe for work by default
- Things you would genuinely recommend to a friend

## What does NOT belong here
- SEO farms
- Affiliate spam
- NSFW / illegal content
- "My new AI tool" with no real value

## How to contribute

### Adding a new site

For security reasons, new site submissions must follow a URL-only format:

1. Create a new directory under `sites/` with a slug (lowercase, hyphens): `sites/my-site/`
2. Create `site.yml` containing **only the website URL** (one line, max 200 characters)
   - Example: `https://example.com`
   - The file must contain only the URL, nothing else
3. Open a pull request
4. An automated validation checks the format (script-based, prevents prompt injection)
5. AI automatically generates the complete site data (category, lenses, title, description, etc.)
6. The generated `site.yml` is committed to your PR branch
7. PR is approved and ready for merge

**Note:** For security, users cannot submit full YAML files directly. The AI generates all metadata from the URL to prevent prompt injection attacks.

### Editing an existing site

1. Edit the `sites/<id>/site.yml` file
2. Open a pull request
3. Automated review will check changes

**Note:** The old category files (`categories/*.yml`) are kept for reference but new additions should use the new format.

**Note:** The old category files (`categories/*.yml`) are kept for reference. New additions use the site-based format with URL-only submissions for security.

