#!/usr/bin/env node

/**
 * Copy generated indexes to web directory for local development
 */

const fs = require('fs');
const path = require('path');

const distIndexes = path.join(__dirname, '..', 'dist', 'indexes');
const webIndexes = path.join(__dirname, '..', 'web', 'indexes');

// Ensure web/indexes directory exists
if (!fs.existsSync(webIndexes)) {
  fs.mkdirSync(webIndexes, { recursive: true });
}

// Copy each index file
const files = ['categories.json', 'sites-en.json'];
let copiedCount = 0;

files.forEach(file => {
  const src = path.join(distIndexes, file);
  const dest = path.join(webIndexes, file);
  
  if (fs.existsSync(src)) {
    fs.copyFileSync(src, dest);
    console.log(`Copied: ${file} → web/indexes/`);
    copiedCount++;
    
    // Verify file was copied successfully
    if (!fs.existsSync(dest)) {
      throw new Error(`Failed to copy ${file} - destination file does not exist`);
    }
    
    // Verify file content is JSON
    try {
      const content = fs.readFileSync(dest, 'utf8');
      JSON.parse(content); // Validate it's valid JSON
    } catch (e) {
      throw new Error(`Invalid JSON in ${file}: ${e.message}`);
    }
  } else {
    throw new Error(`Error: ${file} not found in dist/indexes/ - build failed`);
  }
});

if (copiedCount === 0) {
  throw new Error('Error: No index files were copied - check build process');
}

console.log(`✅ Successfully copied ${copiedCount} index files to web/indexes/`);

