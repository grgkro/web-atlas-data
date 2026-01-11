#!/usr/bin/env node

/**
 * Build indexes from site files
 * Generates:
 * - dist/indexes/categories.json (category list + counts)
 * - dist/indexes/sites-en.json (flat list for English UI)
 */

const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

const sitesDir = path.join(__dirname, '..', 'sites');
const distDir = path.join(__dirname, '..', 'dist');
const indexesDir = path.join(distDir, 'indexes');

// Ensure directories exist
if (!fs.existsSync(indexesDir)) {
  fs.mkdirSync(indexesDir, { recursive: true });
}

// Get all site directories
const siteDirs = fs.readdirSync(sitesDir).filter(dir => {
  const dirPath = path.join(sitesDir, dir);
  return fs.statSync(dirPath).isDirectory();
});

const sites = [];
const categories = new Map();

// Load all site files
siteDirs.forEach(siteId => {
  const siteFilePath = path.join(sitesDir, siteId, 'site.yml');
  
  if (!fs.existsSync(siteFilePath)) {
    console.warn(`Warning: No site.yml found for ${siteId}`);
    return;
  }
  
  try {
    const content = fs.readFileSync(siteFilePath, 'utf8');
    const siteData = yaml.load(content);
    
    // Validate required fields
    if (!siteData.id || !siteData.url || !siteData.category) {
      console.warn(`Warning: Invalid site data for ${siteId}`);
      return;
    }
    
    // Build site entry for index
    const siteEntry = {
      id: siteData.id,
      url: siteData.url,
      title: siteData.title?.en || siteData.id,
      description: siteData.description?.en || '',
      category: siteData.category,
      lenses: siteData.lenses || [],
      quality: siteData.quality || 'solid'
    };
    
    // Add tags if present
    if (siteData.tags) {
      siteEntry.tags = siteData.tags;
    }
    
    sites.push(siteEntry);
    
    // Track category counts
    const categoryName = siteData.category;
    if (!categories.has(categoryName)) {
      categories.set(categoryName, 0);
    }
    categories.set(categoryName, categories.get(categoryName) + 1);
  } catch (error) {
    console.error(`Error processing ${siteId}:`, error.message);
  }
});

// Sort sites by category, then by quality (exceptional first), then by title
sites.sort((a, b) => {
  if (a.category !== b.category) {
    return a.category.localeCompare(b.category);
  }
  const qualityOrder = { exceptional: 0, solid: 1, niche: 2 };
  const qualityDiff = (qualityOrder[a.quality] || 1) - (qualityOrder[b.quality] || 1);
  if (qualityDiff !== 0) return qualityDiff;
  return a.title.localeCompare(b.title);
});

// Build categories.json
const categoriesList = Array.from(categories.entries())
  .map(([name, count]) => ({ name, count }))
  .sort((a, b) => a.name.localeCompare(b.name));

const categoriesData = {
  categories: categoriesList,
  totalSites: sites.length
};

// Write categories.json
fs.writeFileSync(
  path.join(indexesDir, 'categories.json'),
  JSON.stringify(categoriesData, null, 2)
);

// Write sites-en.json
fs.writeFileSync(
  path.join(indexesDir, 'sites-en.json'),
  JSON.stringify(sites, null, 2)
);

console.log(`✅ Built indexes:`);
console.log(`   - ${categoriesList.length} categories`);
console.log(`   - ${sites.length} sites`);
console.log(`   - Generated: dist/indexes/categories.json`);
console.log(`   - Generated: dist/indexes/sites-en.json`);

