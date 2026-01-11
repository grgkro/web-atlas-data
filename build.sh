#!/bin/bash
# Build script for Cloudflare Pages
# This script helps diagnose build issues

set -e  # Exit on error

echo "Current directory: $(pwd)"
echo "Listing files:"
ls -la

echo ""
echo "Checking for package.json:"
if [ -f "package.json" ]; then
    echo "✅ package.json found!"
    cat package.json | head -5
else
    echo "❌ package.json NOT found!"
    echo "Looking for package.json in parent directories:"
    find .. -name "package.json" -type f 2>/dev/null | head -5
    exit 1
fi

echo ""
echo "Installing dependencies..."
npm install

echo ""
echo "Building..."
npm run build

echo ""
echo "✅ Build complete!"
echo "Build output in web/ directory:"
ls -la web/ | head -10


