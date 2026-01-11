#!/bin/bash
# Build script for Cloudflare Pages
npm install
npm run build
# Copy web files to output directory (Cloudflare Pages expects output in current dir)
cp -r web/* dist/
# Copy indexes to the correct location
mkdir -p dist/indexes
cp dist/indexes/*.json dist/indexes/ 2>/dev/null || true


