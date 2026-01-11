// Web Atlas UI - Minimal POC

// API base path
// Indexes are in web/indexes/ which is served at /indexes/ in production
// For local dev (serving from web/ directory), use relative path
// For production, use absolute path
const isLocal = window.location.hostname === 'localhost' || 
                window.location.hostname === '127.0.0.1' ||
                window.location.hostname === '0.0.0.0';
const API_BASE = isLocal ? './indexes' : '/indexes';
let categoriesData = null;
let sitesData = null;
let currentCategory = null;

// State management
const state = {
  view: 'categories', // 'categories' | 'sites'
  category: null
};

// Load data
async function loadData() {
  const loadingEl = document.getElementById('loading');
  const errorEl = document.getElementById('error');
  
  try {
    loadingEl.style.display = 'block';
    
    // Load categories
    const categoriesResponse = await fetch(`${API_BASE}/categories.json`);
    if (!categoriesResponse.ok) throw new Error('Failed to load categories');
    categoriesData = await categoriesResponse.json();
    
    // Load sites
    const sitesResponse = await fetch(`${API_BASE}/sites-en.json`);
    if (!sitesResponse.ok) throw new Error('Failed to load sites');
    sitesData = await sitesResponse.json();
    
    loadingEl.style.display = 'none';
    renderCategories();
  } catch (error) {
    loadingEl.style.display = 'none';
    errorEl.textContent = `Error loading data: ${error.message}`;
    errorEl.style.display = 'block';
    console.error('Error loading data:', error);
  }
}

// Render categories view
function renderCategories() {
  const categoriesView = document.getElementById('categories-view');
  const sitesView = document.getElementById('sites-view');
  
  categoriesView.style.display = 'grid';
  sitesView.style.display = 'none';
  state.view = 'categories';
  state.category = null;
  
  categoriesView.innerHTML = categoriesData.categories.map(cat => `
    <div class="category-card" data-category="${cat.name}">
      <h3>${escapeHtml(cat.name)}</h3>
      <div class="count">${cat.count} site${cat.count !== 1 ? 's' : ''}</div>
    </div>
  `).join('');
  
  // Add click handlers
  categoriesView.querySelectorAll('.category-card').forEach(card => {
    card.addEventListener('click', () => {
      const category = card.dataset.category;
      showCategory(category);
    });
  });
}

// Show sites for a category
function showCategory(categoryName) {
  const categoriesView = document.getElementById('categories-view');
  const sitesView = document.getElementById('sites-view');
  const categoryTitle = document.getElementById('category-title');
  const sitesList = document.getElementById('sites-list');
  
  categoriesView.style.display = 'none';
  sitesView.style.display = 'block';
  state.view = 'sites';
  state.category = categoryName;
  
  categoryTitle.textContent = categoryName;
  
  const categorySites = sitesData.filter(site => site.category === categoryName);
  
  sitesList.innerHTML = categorySites.map(site => `
    <div class="site-card">
      <h3><a href="${escapeHtml(site.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(site.title)}</a></h3>
      <a href="${escapeHtml(site.url)}" target="_blank" rel="noopener noreferrer" class="url">${escapeHtml(site.url)}</a>
      <p class="description">${escapeHtml(site.description)}</p>
      <div class="meta">
        <span class="quality-badge quality-${escapeHtml(site.quality)}">${escapeHtml(site.quality)}</span>
        ${site.lenses.length > 0 ? `
          <div class="lenses">
            ${site.lenses.map(lens => `<span class="lens-tag">${escapeHtml(lens)}</span>`).join('')}
          </div>
        ` : ''}
      </div>
    </div>
  `).join('');
}

// Back button handler
document.getElementById('back-button').addEventListener('click', () => {
  renderCategories();
});

// Utility: escape HTML to prevent XSS
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Initialize app
loadData();

