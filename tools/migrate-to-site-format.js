#!/usr/bin/env node

/**
 * Migration script to convert category YAML files to individual site files
 * Run: node tools/migrate-to-site-format.js
 */

const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

// Helper to generate slug from name
function generateSlug(name) {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

// Map primary_category to category (normalize)
const categoryMap = {
  'Search': 'Search',
  'Knowledge': 'Knowledge',
  'Tools': 'Tools',
  'News': 'News',
  'Buy': 'Buy',
  'Build': 'Build',
  'Play': 'Play',
  'Explore': 'Explore'
};

const categoriesDir = path.join(__dirname, '..', 'categories');
const sitesDir = path.join(__dirname, '..', 'sites');
const categoryFiles = fs.readdirSync(categoriesDir).filter(f => f.endsWith('.yml'));

// Create sites directory
if (!fs.existsSync(sitesDir)) {
  fs.mkdirSync(sitesDir, { recursive: true });
}

const allSites = [];

categoryFiles.forEach(categoryFile => {
  const filePath = path.join(categoriesDir, categoryFile);
  const content = fs.readFileSync(filePath, 'utf8');
  const sites = yaml.load(content);
  
  if (!Array.isArray(sites)) {
    console.error(`Skipping ${categoryFile}: not an array`);
    return;
  }
  
  sites.forEach(site => {
    if (!site.name || !site.url) {
      console.error(`Skipping invalid site in ${categoryFile}:`, site);
      return;
    }
    
    const id = generateSlug(site.name);
    const siteDir = path.join(sitesDir, id);
    
    // Create site directory
    if (!fs.existsSync(siteDir)) {
      fs.mkdirSync(siteDir, { recursive: true });
    }
    
    // Create site.yml
    const siteData = {
      id: id,
      url: site.url,
      category: categoryMap[site.primary_category] || site.primary_category,
      lenses: site.lenses || [],
      quality: site.quality || 'solid',
      title: {
        en: site.name
      },
      description: {
        en: site.description
      }
    };
    
    const yamlContent = yaml.dump(siteData, {
      lineWidth: -1,
      noRefs: true,
      sortKeys: false
    });
    
    fs.writeFileSync(path.join(siteDir, 'site.yml'), yamlContent);
    allSites.push({ id, name: site.name });
    console.log(`Created: sites/${id}/site.yml`);
  });
});

console.log(`\nMigration complete! Created ${allSites.length} site files.`);


