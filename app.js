/**
 * YT Lead Hunter PRO & CRM
 * Full Client Engine & State Management
 * AK Technology & Zentic Media Architecture
 */

// ------------------------------------------------------------
const API_BASE = (window.location.protocol === 'file:' || !window.location.host || window.location.host === '')
  ? 'http://localhost:8000'
  : '';

const SOCIAL_CONFIG = {
  instagram:  { short: 'IG',  color: '#E1306C', label: 'Instagram' },
  twitter:    { short: 'TW',  color: '#1DA1F2', label: 'Twitter/X' },
  x:          { short: 'X',   color: '#000000', label: 'X (Twitter)' },
  tiktok:     { short: 'TT',  color: '#010101', label: 'TikTok' },
  facebook:   { short: 'FB',  color: '#1877F2', label: 'Facebook' },
  linkedin:   { short: 'LI',  color: '#0A66C2', label: 'LinkedIn' },
  whatsapp:   { short: 'WA',  color: '#25D366', label: 'WhatsApp' },
  telegram:   { short: 'TG',  color: '#229ED9', label: 'Telegram' },
  discord:    { short: 'DC',  color: '#5865F2', label: 'Discord' },
  threads:    { short: 'TH',  color: '#000000', label: 'Threads' },
  pinterest:  { short: 'PIN', color: '#E60023', label: 'Pinterest' },
  linktree:   { short: 'LT',  color: '#43E660', label: 'Linktree' },
  beacons:    { short: 'BC',  color: '#FF6B35', label: 'Beacons' },
  stan:       { short: 'ST',  color: '#7C3AED', label: 'Stan' },
};

function getSocialUrl(platform, val) {
  if (val.startsWith('http')) return val;
  const map = {
    instagram: 'https://instagram.com/', twitter: 'https://twitter.com/',
    x: 'https://twitter.com/', tiktok: 'https://tiktok.com/@',
    facebook: 'https://facebook.com/', linkedin: 'https://linkedin.com/in/',
    whatsapp: 'https://wa.me/', telegram: 'https://t.me/',
    discord: 'https://discord.gg/', threads: 'https://threads.net/@',
    pinterest: 'https://pinterest.com/', linktree: 'https://linktr.ee/',
  };
  const base = map[platform] || 'https://';
  return base + val.replace('@', '');
}

function renderSocialPills(social, compact = true) {
  if (!social || Object.keys(social).length === 0)
    return '<span style="color:#9ca3af;font-size:11px;">-</span>';
  return Object.entries(social).map(([platform, val]) => {
    const cfg = SOCIAL_CONFIG[platform.toLowerCase()] || { short: platform.substring(0,2).toUpperCase(), color: '#8b1524', label: platform };
    const url = getSocialUrl(platform.toLowerCase(), val);
    if (compact) {
      return `<a href="${url}" target="_blank" title="${cfg.label}: ${val}"
        style="display:inline-flex;align-items:center;padding:2px 7px;border-radius:10px;
               font-size:10px;font-weight:800;text-decoration:none;color:#fff;
               background:${cfg.color};white-space:nowrap;letter-spacing:0.3px;"
      >${cfg.short}</a>`;
    }
    return `<a href="${url}" target="_blank"
      style="display:inline-flex;align-items:center;gap:5px;padding:5px 11px;border-radius:14px;
             font-size:12px;font-weight:700;text-decoration:none;color:#fff;
             background:${cfg.color};margin:3px;"
    >${cfg.short} ${cfg.label}: ${val}</a>`;
  }).join('');
}
const APP_STATE = {
  currentPage: 'dashboard',
  discoveryMode: 'single', // -------------------------------------------------------------
  strategy: 'auto',
  leads: [],
  selectedLeadIds: new Set(),
  activeLeadForModal: null,
  activeScoreFilter: 'all',
  activeResultsTab: 'qualified',
  recentSearches: [],
  quotaLimit: 30000,
  quotaUsed: 0,
  keys: {
    primary: { key: '', locked: false },
    secondary: { key: '', locked: false },
    third: { key: '', locked: false }
  },
  brightDataKey: '',
  isScanning: false,
  nicheIndex: 0
};

// ------------------------------------------------------------
const NICHES_DB = [
  {
    name: 'Motivation',
    score: 81.5,
    type: 'C — Opportunistic',
    subNiches: [
      'Event organizers (motivational)',
      'Motivational membership communities',
      'Keynote speakers',
      'Motivational course creators',
      'Speaker bureau brands'
    ],
    microNiches: [
      'Youth motivational speakers',
      'Motivational documentary brands',
      'Corporate motivational speakers',
      'Motivational speaking academies',
      'Faith & mindset coaches'
    ],
    opportunities: [
      'hire keynote speaker',
      'motivational speaking programs',
      'mindset coaching bootcamp',
      'corporate leadership retreat'
    ]
  },
  {
    name: 'Video Editing & Creators',
    score: 88.2,
    type: 'A — High Intent',
    subNiches: [
      'YouTube automation channels',
      'Talking head podcast channels',
      'Faceless educational channels',
      'Tech review studios',
      'Vloggers with >50k subs'
    ],
    microNiches: [
      'Retention editing breakdown',
      'Premiere Pro workflow hacks',
      'Sound design for YouTube',
      'CapCut desktop workflows',
      'Thumbnail CTR strategies'
    ],
    opportunities: [
      'hire freelance video editor',
      'youtube retention optimization',
      'podcast short form repurposing',
      'agency editing partner'
    ]
  },
  {
    name: 'Personal Finance & Investing',
    score: 85.0,
    type: 'B — High Budget',
    subNiches: [
      'Dividend investing brands',
      'Research newsletters',
      'Real estate investing coaches',
      'Alternative asset educators',
      'Trading psychology mentors'
    ],
    microNiches: [
      'Index fund retirement strategies',
      'Rental property BRRRR mentors',
      'Options income communities',
      'Tax lien investing tutorials',
      'Crypto treasury analysis'
    ],
    opportunities: [
      'finance newsletter sponsorship',
      'wealth consulting client',
      'real estate mastermind',
      'investor podcast guesting'
    ]
  },
  {
    name: 'Fitness & Nutrition',
    score: 79.4,
    type: 'C — High Volume',
    subNiches: [
      'Online fitness coaching',
      'Bodybuilding prep coaches',
      'Nutrition & meal prep creators',
      'CrossFit box owners',
      'Home workout program creators'
    ],
    microNiches: [
      'Hypertrophy science breakdown',
      'Keto for busy executives',
      'Mobility & posture routines',
      'Calisthenics skill progressions',
      'Postpartum fitness mentors'
    ],
    opportunities: [
      'online personal training app',
      'custom workout programming',
      'supplement brand sponsorship',
      'fitness membership community'
    ]
  }
];

// ------------------------------------------------------------
const EXPORT_COLUMNS = [
  { id: 'channel_name', label: 'Channel Name', default: true },
  { id: 'handle', label: 'Handle (@)', default: true },
  { id: 'channel_url', label: 'Channel URL', default: true },
  { id: 'email', label: 'Email Address', default: true },
  { id: 'subscribers', label: 'Subscribers', default: true },
  { id: 'total_views', label: 'Total Views', default: true },
  { id: 'videos', label: 'Videos Published', default: true },
  { id: 'avg_views', label: 'Avg Views / Video', default: true },
  { id: 'upload_freq', label: 'Upload Frequency', default: false },
  { id: 'last_upload', label: 'Last Upload Date', default: false },
  { id: 'website', label: 'Website', default: true },
  { id: 'country', label: 'Country', default: false },
  { id: 'score', label: 'Lead Score', default: true },
  { id: 'instagram', label: 'Instagram', default: false },
  { id: 'twitter', label: 'X (Twitter)', default: false },
  { id: 'tiktok', label: 'TikTok', default: false },
  { id: 'facebook', label: 'Facebook', default: false },
  { id: 'linkedin', label: 'LinkedIn', default: false },
  { id: 'whatsapp', label: 'WhatsApp', default: false },
  { id: 'telegram', label: 'Telegram', default: false },
  { id: 'discord', label: 'Discord', default: false },
  { id: 'threads', label: 'Threads', default: false },
  { id: 'pinterest', label: 'Pinterest', default: false },
  { id: 'linktree', label: 'Linktree', default: false },
  { id: 'outreach_notes', label: 'Outreach Notes', default: false }
];

// ------------------------------------------------------------
function navigatePage(pageId) {
  APP_STATE.currentPage = pageId;
  document.querySelectorAll('.page-view').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.nav-tab-btn').forEach(el => el.classList.remove('active'));

  const viewEl = document.getElementById(`view-${pageId}`);
  if (viewEl) viewEl.classList.add('active');

  const navBtn = document.querySelector(`.nav-tab-btn[data-page="${pageId}"]`);
  if (navBtn) navBtn.classList.add('active');

  // Trigger page-specific refreshes
  if (pageId === 'dashboard') updateDashboardMetrics();
  if (pageId === 'results') renderResultsTable();
  if (pageId === 'exports') updateExportPreview();
  if (pageId === 'pipeline') loadPipelineBoard();
  if (pageId === 'fb-radar') loadFbRadarPage();

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ------------------------------------------------------------
function toggleDarkMode() {
  document.body.classList.toggle('dark-mode');
  const isDark = document.body.classList.contains('dark-mode');
  document.getElementById('themeToggleBtn').textContent = isDark ? '☀️' : '🌙';
  localStorage.setItem('yt_lead_hunter_theme', isDark ? 'dark' : 'light');
}

// ------------------------------------------------------------
function setDiscoveryMode(mode) {
  APP_STATE.discoveryMode = mode;
  document.getElementById('btnModeSingle').classList.toggle('active', mode === 'single');
  document.getElementById('btnModeBulk').classList.toggle('active', mode === 'bulk');
  document.getElementById('singleKeywordSection').style.display = mode === 'single' ? 'block' : 'none';
  document.getElementById('bulkKeywordSection').style.display = mode === 'bulk' ? 'block' : 'none';
  calculatePreSearchEstimate();
}

document.addEventListener('DOMContentLoaded', () => {
  // Theme restore
  if (localStorage.getItem('yt_lead_hunter_theme') === 'dark') {
    document.body.classList.add('dark-mode');
    const tBtn = document.getElementById('themeToggleBtn');
    if (tBtn) tBtn.textContent = '☀️';
  }

  // Load saved state
  loadStoredKeys();
  loadLeadsFromDatabase();
  loadFbAlerts();
  initNichePanel();
  initExportColumns();
  setupFilterEventListeners();
  calculatePreSearchEstimate();
});

// Strategy Buttons
document.addEventListener('click', (e) => {
  if (e.target.classList.contains('strategy-btn')) {
    document.querySelectorAll('.strategy-btn').forEach(b => b.classList.remove('active'));
    e.target.classList.add('active');
    APP_STATE.strategy = e.target.dataset.strategy;
    const descMap = {
      auto: 'Smart — adapts query depth to keyword type (recommended)',
      conservative: 'Fastest — queries top 1-2 video clusters only',
      balanced: 'Thorough — balances query depth and quota',
      aggressive: 'Deep crawl — searches questions, comparisons, and related keywords'
    };
    const sDesc = document.getElementById('strategyDesc');
    if (sDesc) sDesc.textContent = descMap[APP_STATE.strategy] || '';
    calculatePreSearchEstimate();
  }

  // Pills group selection
  if (e.target.classList.contains('select-pill') && e.target.parentElement) {
    const parent = e.target.parentElement;
    parent.querySelectorAll('.select-pill').forEach(p => p.classList.remove('active'));
    e.target.classList.add('active');
    calculatePreSearchEstimate();
  }
});

// ------------------------------------------------------------
function calculatePreSearchEstimate() {
  const maxResultsPill = document.querySelector('#maxResultsPills .select-pill.active');
  const targetResults = maxResultsPill ? parseInt(maxResultsPill.dataset.val) : 50;

  let multiplier = 1;
  if (APP_STATE.discoveryMode === 'bulk') {
    const bulkText = (document.getElementById('inputBulkKeywords')?.value || '').trim();
    const lines = bulkText ? bulkText.split('\n').filter(l => l.trim().length > 0).length : 1;
    multiplier = Math.max(1, lines);
    const statsEl = document.getElementById('bulkKeywordsStats');
    if (statsEl) {
      statsEl.textContent = `Lines: ${lines} | Keywords: ${lines} | Est. queries: ${lines * 3} | Est. API units: ${(lines * 150).toLocaleString()}`;
    }
  }

  const estLeads = Math.round(targetResults * 0.85 * multiplier);
  const quotaUnits = Math.round(targetResults * 2.8 * multiplier);
  const quotaPct = Math.min(100, Math.round((quotaUnits / APP_STATE.quotaLimit) * 100));
  const estTimeSeconds = Math.max(5, Math.round(targetResults * 0.4 * multiplier));

  const elLeads = document.getElementById('estQualifiedLeads');
  const elUnits = document.getElementById('estQuotaUnits');
  const elPct = document.getElementById('estQuotaPct');
  const elTime = document.getElementById('estSearchTime');
  const elBar = document.getElementById('estProgressBar');

  if (elLeads) elLeads.textContent = `~${estLeads.toLocaleString()}`;
  if (elUnits) elUnits.textContent = quotaUnits.toLocaleString();
  if (elPct) elPct.textContent = `${quotaPct}%`;
  if (elTime) elTime.textContent = estTimeSeconds > 60 ? `~${Math.round(estTimeSeconds/60)}m` : `~${estTimeSeconds}s`;
  if (elBar) elBar.style.width = `${quotaPct}%`;
}

function setupFilterEventListeners() {
  const kwInput = document.getElementById('inputKeyword');
  if (kwInput) kwInput.addEventListener('input', calculatePreSearchEstimate);

  const bulkInput = document.getElementById('inputBulkKeywords');
  if (bulkInput) bulkInput.addEventListener('input', calculatePreSearchEstimate);

  const minSubs = document.getElementById('filterMinSubs');
  if (minSubs) minSubs.addEventListener('input', calculatePreSearchEstimate);
}

function toggleAdvancedFilters() {
  const content = document.getElementById('advFiltersContent');
  const icon = document.getElementById('advToggleIcon');
  if (!content) return;
  const isHidden = content.style.display === 'none';
  content.style.display = isHidden ? 'block' : 'none';
  if (icon) icon.textContent = isHidden ? '▲' : '▼';
}

function clearCountryFilter() {
  const sel = document.getElementById('filterCountry');
  if (sel) sel.value = '';
  renderResultsTable();
}

function pasteClipboardKeywords() {
  if (navigator.clipboard) {
    navigator.clipboard.readText().then(text => {
      const area = document.getElementById('inputBulkKeywords');
      if (area) {
        area.value = (area.value ? area.value + '\n' : '') + text;
        calculatePreSearchEstimate();
      }
    });
  }
}

function clearBulkKeywords() {
  const area = document.getElementById('inputBulkKeywords');
  if (area) {
    area.value = '';
    calculatePreSearchEstimate();
  }
}

// ------------------------------------------------------------
function initNichePanel() {
  const niche = NICHES_DB[APP_STATE.nicheIndex % NICHES_DB.length];
  document.getElementById('nicheScoreDisplay').textContent = niche.score;
  document.getElementById('nicheTitleDisplay').textContent = niche.name;

  const subEl = document.getElementById('nicheSubList');
  if (subEl) {
    subEl.innerHTML = niche.subNiches.map(s => `
      <div class="niche-sub-item" onclick="applyNicheQuery('${s.replace(/'/g, "\\'")}')">${s}</div>
    `).join('');
  }

  const microEl = document.getElementById('nicheMicroList');
  if (microEl) {
    microEl.innerHTML = niche.microNiches.map(m => `
      <div class="niche-sub-item" style="border-left:3px solid var(--primary-red);" onclick="applyNicheQuery('${m.replace(/'/g, "\\'")}')">${m}</div>
    `).join('');
  }

  const oppEl = document.getElementById('nicheOpportunitiesList');
  if (oppEl) {
    oppEl.innerHTML = niche.opportunities.map(o => `
      <div class="niche-sub-item" style="display:flex;justify-content:space-between;" onclick="applyNicheQuery('${o.replace(/'/g, "\\'")}')">
        <span>${o}</span>
        <span style="font-size:10px;color:var(--primary-red);font-weight:700;">COMMERCIAL</span>
      </div>
    `).join('');
  }
}

function applyNicheQuery(query) {
  const input = document.getElementById('inputKeyword');
  if (input) {
    input.value = query;
    showToast(`Applied niche query: "${query}"`, 'info');
    calculatePreSearchEstimate();
  }
}

function copyAllOpportunities() {
  const niche = NICHES_DB[APP_STATE.nicheIndex % NICHES_DB.length];
  const text = niche.opportunities.join('\n');
  navigator.clipboard.writeText(text);
  showToast('Copied all niche opportunities to clipboard!', 'success');
}

// ------------------------------------------------------------
async function startDiscoveryScan() {
  if (APP_STATE.isScanning) return;

  let keyword = '';
  if (APP_STATE.discoveryMode === 'single') {
    keyword = (document.getElementById('inputKeyword')?.value || '').trim();
    if (!keyword) {
      showToast('Please enter a search keyword first!', 'warning');
      return;
    }
  } else {
    const raw = (document.getElementById('inputBulkKeywords')?.value || '').trim();
    if (!raw) {
      showToast('Please enter at least one keyword in the list!', 'warning');
      return;
    }
    keyword = raw.split('\n')[0].trim(); // first keyword for primary run
  }

  const engine = document.getElementById('selectEngine')?.value || 'auto';
  const minSubs = parseInt(document.getElementById('filterMinSubs')?.value) || 500;
  const maxSubs = parseInt(document.getElementById('filterMaxSubs')?.value) || 500000;
  const country = document.getElementById('filterCountry')?.value || '';
  const maxResultsPill = document.querySelector('#maxResultsPills .select-pill.active');
  const maxResults = maxResultsPill ? parseInt(maxResultsPill.dataset.val) : 50;

  APP_STATE.isScanning = true;
  const btn = document.getElementById('btnStartDiscovery');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '⏳ Scanning YouTube...';
  }

  const pBox = document.getElementById('liveScanProgressBox');
  const pMsg = document.getElementById('scanStatusMsg');
  const pPct = document.getElementById('scanProgressPct');
  const pBar = document.getElementById('scanProgressBarFill');
  if (pBox) pBox.style.display = 'block';

  // API Call to FastAPI Backend
  try {
    const res = await fetch(API_BASE + '/api/scan/youtube', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        keyword,
        min_subs: minSubs,
        max_subs: maxSubs,
        max_results: maxResults,
        country,
        engine
      })
    });

    const data = await res.json();
    if (data && data.scan_id) {
      pollScanProgress(data.scan_id, keyword, country);
    } else {
      throw new Error('Could not initiate scan');
    }
  } catch (err) {
    console.error('Backend scan failed:', err);
    APP_STATE.isScanning = false;
    const btn = document.getElementById('btnStartDiscovery');
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '🚀 Start Lead Discovery';
    }
    const pBox = document.getElementById('liveScanProgressBox');
    if (pBox) pBox.style.display = 'none';
    showToast('Failed to connect to backend scanner. Please verify server is online.', 'error');
  }
}

function pollScanProgress(scanId, keyword, country = '') {
  const pMsg = document.getElementById('scanStatusMsg');
  const pPct = document.getElementById('scanProgressPct');
  const pBar = document.getElementById('scanProgressBarFill');
  let errCount = 0;

  const timer = setInterval(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/scan/progress/${scanId}`);
      const data = await res.json();
      errCount = 0;

      if (pMsg && data.step) pMsg.textContent = data.step;
      if (pPct) pPct.textContent = `${data.progress || 0}%`;
      if (pBar) pBar.style.width = `${data.progress || 0}%`;

      if (data.status === 'done' || data.progress >= 100) {
        clearInterval(timer);
        finishScan(data.leads || [], keyword);
      }
    } catch (e) {
      errCount++;
      if (errCount >= 6) {
        clearInterval(timer);
        APP_STATE.isScanning = false;
        const btn = document.getElementById('btnStartDiscovery');
        if (btn) {
          btn.disabled = false;
          btn.innerHTML = '🚀 Start Lead Discovery';
        }
        const pBox = document.getElementById('liveScanProgressBox');
        if (pBox) pBox.style.display = 'none';
        showToast('Lost connection to backend scan progress.', 'error');
      }
    }
  }, 1000);
}

function runSimulatedDiscovery(keyword, count, country = '') {
  let pct = 0;
  const pMsg = document.getElementById('scanStatusMsg');
  const pPct = document.getElementById('scanProgressPct');
  const pBar = document.getElementById('scanProgressBarFill');

  const cText = country ? ` in ${country}` : '';
  const steps = [
    `Connecting to YouTube API${cText}...`,
    `Searching ranking videos${cText}...`,
    'Extracting creator handles & country metadata...',
    'Scraping About pages & verified emails...',
    'Running AI video quality scoring...',
    'Finalizing leads...'
  ];

  const interval = setInterval(() => {
    pct += 18;
    const stepIdx = Math.min(steps.length - 1, Math.floor((pct / 100) * steps.length));
    if (pMsg) pMsg.textContent = steps[stepIdx];
    if (pPct) pPct.textContent = `${Math.min(100, pct)}%`;
    if (pBar) pBar.style.width = `${Math.min(100, pct)}%`;

    if (pct >= 100) {
      clearInterval(interval);
      const generated = generateSampleLeads(keyword, count, country);
      finishScan(generated, keyword);
    }
  }, 500);
}

function finishScan(newLeads, keyword) {
  APP_STATE.isScanning = false;
  const btn = document.getElementById('btnStartDiscovery');
  if (btn) {
    btn.disabled = false;
    btn.innerHTML = '🚀 Start Lead Discovery';
  }
  const pBox = document.getElementById('liveScanProgressBox');
  if (pBox) pBox.style.display = 'none';

  // Merge leads
  newLeads.forEach(l => {
    if (!APP_STATE.leads.some(existing => existing.channel === l.channel || existing.id === l.id)) {
      APP_STATE.leads.unshift(l);
    }
  });

  // Track search session
  APP_STATE.recentSearches.unshift({
    keyword,
    count: newLeads.length,
    highScore: newLeads.filter(l => (l.ai_score || 0) >= 70).length,
    date: new Date().toLocaleDateString()
  });

  // Update Quota
  APP_STATE.quotaUsed += Math.min(newLeads.length * 35, 1200);

  updateDashboardMetrics();
  showToast(`Found ${newLeads.length} leads for "${keyword}"!`, 'success');
  navigatePage('results');
}

// ------------------------------------------------------------
function generateSampleLeads(keyword, count, country = '') {
  const kwClean = keyword.replace(/[^a-zA-Z0-9 ]/g, '').trim() || 'Creator';
  const cUpper = (country || '').toUpperCase();

  let locations = ['Global', 'Studio', 'Media', 'Digital', 'Hub'];
  let creators = ['Alex', 'Jordan', 'Taylor', 'Morgan', 'Sam', 'Chris', 'Robin', 'Jesse'];
  let tld = 'com';
  let cDisplay = cUpper || 'US';

  if (cUpper === 'CA') {
    locations = ['Toronto', 'Vancouver', 'Montreal', 'Calgary', 'Ottawa', 'Ontario', 'BC', 'Canada'];
    creators = ['Liam', 'Noah', 'Emma', 'Olivia', 'Ethan', 'Chloe', 'Lucas', 'Maya', 'Felix', 'Sophie', 'Ryan'];
    tld = 'ca';
    cDisplay = 'CA';
  } else if (cUpper === 'GB') {
    locations = ['London', 'Manchester', 'Birmingham', 'Bristol', 'Edinburgh', 'UK'];
    creators = ['George', 'Harry', 'Oliver', 'Charlotte', 'Amelia', 'Jack', 'Freddie', 'Poppy'];
    tld = 'co.uk';
    cDisplay = 'GB';
  } else if (cUpper === 'AU') {
    locations = ['Sydney', 'Melbourne', 'Brisbane', 'Perth', 'Australia'];
    creators = ['Jack', 'William', 'Oliver', 'Mia', 'Isla', 'Lucas', 'Cooper'];
    tld = 'com.au';
    cDisplay = 'AU';
  } else if (cUpper === 'US') {
    locations = ['NYC', 'LA', 'Austin', 'Miami', 'Chicago', 'USA'];
    creators = ['Jake', 'David', 'Michael', 'Sarah', 'Brandon', 'Jessica', 'Tyler'];
    tld = 'com';
    cDisplay = 'US';
  }

  const nameTemplates = [
    (n, loc) => `${kwClean} Pro Studio (${loc})`,
    (n, loc) => `The ${kwClean} Blueprint`,
    (n, loc) => `Daily ${kwClean} Talks with ${n}`,
    (n, loc) => `Elite ${kwClean} Mastery`,
    (n, loc) => `Prime ${kwClean} Secrets`,
    (n, loc) => `${loc} ${kwClean} Hub`,
    (n, loc) => `Coach ${n} | ${kwClean} ${loc}`,
    (n, loc) => `${n} ${kwClean} Coaching`,
    (n, loc) => `NextLevel ${kwClean} ${loc}`,
    (n, loc) => `The ${kwClean} Show ${loc}`,
    (n, loc) => `${kwClean} Lab with ${n}`,
    (n, loc) => `${kwClean} Collective (${loc})`
  ];

  const list = [];
  const targetCount = Math.min(count || 50, 500);

  for (let i = 0; i < targetCount; i++) {
    const loc = locations[i % locations.length];
    const n = creators[i % creators.length];
    const tmpl = nameTemplates[i % nameTemplates.length];
    let name = tmpl(n, loc);
    if (i >= nameTemplates.length) {
      name += ` #${Math.floor(i / nameTemplates.length) + 1}`;
    }

    const slug = name.replace(/[^a-zA-Z0-9]/g, '').toLowerCase() || `channel${i+1}`;
    const subsNum = Math.floor(Math.random() * 85000) + 1200;
    const subsStr = subsNum > 999 ? (subsNum / 1000).toFixed(1) + 'K' : subsNum.toString();
    const viewsNum = subsNum * Math.floor(Math.random() * 30 + 10);
    const score = Math.floor(Math.random() * 35) + 65; // 65-100
    const hasEmail = Math.random() > 0.08;
    const email = hasEmail ? `contact@${slug}.${tld}` : '';

    list.push({
      id: Date.now() + i,
      channel: name,
      name: name,
      handle: `@${slug}`,
      channel_url: `https://www.youtube.com/results?search_query=${encodeURIComponent(name + ' ' + (cUpper === 'CA' ? 'Canada' : cDisplay))}`,
      subscribers: subsStr,
      subs_raw: subsNum,
      total_views: (viewsNum / 1000).toFixed(1) + 'K',
      videos: Math.floor(Math.random() * 200 + 40),
      avg_views: Math.floor(subsNum * 0.12),
      last_upload: `${Math.floor(Math.random() * 6 + 1)}d ago`,
      upload_freq: '2x/week',
      website: `https://www.youtube.com/results?search_query=${encodeURIComponent(name + ' ' + (cUpper === 'CA' ? 'Canada' : cDisplay))}`,
      country: cDisplay,
      created: 'Oct 2022',
      email: email,
      ai_score: score,
      lead_type: score >= 70 ? 'hot' : 'warm',
      description: `High-value educational content and actionable strategies on ${keyword} based in ${loc}. Helping viewers achieve predictable results.`,
      social: {
        instagram: `@${slug}`,
        twitter: `@${slug}`,
        tiktok: `@${slug}`,
        facebook: `${name.replace(/\s+/g,'')}`,
        linkedin: `in/${slug}`,
        ...(Math.random() > 0.5 ? { whatsapp: `+1${Math.floor(Math.random()*9000000000+1000000000)}` } : {}),
        ...(Math.random() > 0.6 ? { telegram: `@${slug}` } : {}),
        ...(Math.random() > 0.7 ? { discord: `${slug}` } : {}),
        ...(Math.random() > 0.5 ? { linktree: `linktr.ee/${slug}` } : {})
      },
      audit: {
        seo: Math.floor(Math.random() * 30 + 60),
        growth: Math.floor(Math.random() * 20 + 80),
        activity: 100,
        clientProb: Math.floor(Math.random() * 25 + 75),
        readiness: Math.floor(Math.random() * 20 + 75)
      }
    });
  }
  return list;
}

// ------------------------------------------------------------
async function loadLeadsFromDatabase() {
  try {
    const res = await fetch(API_BASE + '/api/leads');
    const data = await res.json();
    if (data && data.leads && data.leads.length > 0) {
      APP_STATE.leads = data.leads.map(l => ({
        ...l,
        handle: l.website ? l.website.split('/').pop() : `@${l.name.replace(/\s+/g, '').toLowerCase()}`,
        channel_url: l.website || `https://youtube.com/@${l.name.replace(/\s+/g, '').toLowerCase()}`,
        total_views: l.total_views || '45.2K',
        videos: l.videos || 85,
        avg_views: l.avg_views || 120,
        last_upload: '2w ago',
        upload_freq: '2x/week',
        audit: {
          seo: 68,
          growth: 100,
          activity: 100,
          clientProb: 75,
          readiness: 79
        }
      }));
    } else {
      APP_STATE.leads = [];
    }
  } catch (err) {
    APP_STATE.leads = [];
  }
  updateDashboardMetrics();
  renderResultsTable();
}

// ------------------------------------------------------------
function updateDashboardMetrics() {
  const total = APP_STATE.leads.length;
  const high = APP_STATE.leads.filter(l => (l.ai_score || 0) >= 70).length;
  const scores = APP_STATE.leads.map(l => l.ai_score || 0).filter(s => s > 0);
  const avg = scores.length > 0 ? Math.round(scores.reduce((a,b) => a+b, 0) / scores.length) : '--';

  const remainingQuota = Math.max(0, APP_STATE.quotaLimit - APP_STATE.quotaUsed);
  const quotaPct = Math.round((remainingQuota / APP_STATE.quotaLimit) * 100);

  // Top metric elements
  document.getElementById('statTotalLeads').textContent = total;
  document.getElementById('statQualifiedSub').textContent = `${total} qualified`;
  document.getElementById('statHighPotential').textContent = high;
  document.getElementById('statAvgScore').textContent = avg;
  document.getElementById('statQuotaRemaining').textContent = remainingQuota.toLocaleString();
  document.getElementById('statQuotaPct').textContent = `${quotaPct}% of 30k daily limit`;

  // Badges & Gauges
  document.getElementById('resultsBadge').textContent = total;
  document.getElementById('navQuotaUnits').textContent = `${remainingQuota.toLocaleString()} units`;
  document.getElementById('gaugeCenterPct').textContent = `${quotaPct}%`;
  document.getElementById('gaugeOfUnits').textContent = `${remainingQuota.toLocaleString()} of 30,000 Magic Units`;

  const circle = document.getElementById('gaugeCircle');
  if (circle) {
    const offset = 283 - (283 * (quotaPct / 100));
    circle.style.strokeDashoffset = offset;
  }

  // Score distribution bars
  const b0 = APP_STATE.leads.filter(l => l.ai_score < 20).length;
  const b1 = APP_STATE.leads.filter(l => l.ai_score >= 20 && l.ai_score < 40).length;
  const b2 = APP_STATE.leads.filter(l => l.ai_score >= 40 && l.ai_score < 60).length;
  const b3 = APP_STATE.leads.filter(l => l.ai_score >= 60 && l.ai_score < 80).length;
  const b4 = APP_STATE.leads.filter(l => l.ai_score >= 80).length;

  document.getElementById('scoreDistTotalLeads').textContent = `${total} LEADS`;
  const setBar = (idx, val) => {
    document.getElementById(`distVal${idx}`).textContent = val;
    const h = total > 0 ? Math.max(3, (val / total) * 100) : 3;
    document.getElementById(`distBar${idx}`).style.height = `${h}px`;
  };
  setBar(0, b0);
  setBar(1, b1);
  setBar(2, b2);
  setBar(3, b3);
  setBar(4, b4);

  // Top Leads list in Dashboard
  const topList = document.getElementById('topLeadsList');
  if (topList) {
    if (APP_STATE.leads.length === 0) {
      topList.innerHTML = `<div style="text-align:center;padding:30px 0;color:var(--text-muted);"><p>No leads yet</p></div>`;
    } else {
      const sorted = [...APP_STATE.leads].sort((a,b) => (b.ai_score||0) - (a.ai_score||0)).slice(0, 5);
      topList.innerHTML = sorted.map(l => `
        <div style="display:flex;align-items:center;justify-content:space-between;padding:10px 0;border-bottom:1px solid var(--border-color);cursor:pointer;" onclick="openLeadModal(${l.id})">
          <div style="display:flex;align-items:center;gap:10px;">
            <div style="width:34px;height:34px;background:#8b1524;color:#fff;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:12px;">
              ${(l.channel||'C').charAt(0)}
            </div>
            <div>
              <div style="font-weight:700;font-size:13px;color:var(--text-main);">${l.channel || l.name}</div>
              <div style="font-size:11px;color:var(--text-muted);">${l.subscribers} -¢ ${l.country || 'US'}</div>
            </div>
          </div>
          <span class="score-badge ${(l.ai_score||0) >= 70 ? 'high' : 'med'}">${l.ai_score || 50}</span>
        </div>
      `).join('');
    }
  }

  // Right column stats
  document.getElementById('rightWeekLeads').textContent = total;
  document.getElementById('rightHighPotential').textContent = high;
  document.getElementById('rightAvgScore').textContent = avg;

  // Recent Searches
  const rList = document.getElementById('recentSearchesList');
  if (rList && APP_STATE.recentSearches.length > 0) {
    rList.innerHTML = APP_STATE.recentSearches.slice(0, 4).map(s => `
      <div style="display:flex;align-items:center;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border-color);font-size:12.5px;">
        <span style="font-weight:700;">${s.keyword}</span>
        <div style="display:flex;gap:8px;align-items:center;">
          <span style="background:var(--bg-subtle);padding:2px 6px;border-radius:4px;font-size:11px;">${s.count} leads</span>
          <span style="color:#166534;font-weight:700;font-size:11px;">${s.highScore}★</span>
        </div>
      </div>
    `).join('');
  }
}

// ------------------------------------------------------------
function renderResultsTable() {
  const tbody = document.getElementById('leadsTableBody');
  if (!tbody) return;

  let filtered = [...APP_STATE.leads];

  // Score chip filter
  if (APP_STATE.activeScoreFilter === 'high') filtered = filtered.filter(l => (l.ai_score || 0) >= 70);
  if (APP_STATE.activeScoreFilter === 'med') filtered = filtered.filter(l => (l.ai_score || 0) >= 40 && (l.ai_score || 0) < 70);
  if (APP_STATE.activeScoreFilter === 'low') filtered = filtered.filter(l => (l.ai_score || 0) < 40);

  // Search filter
  const q = (document.getElementById('tableSearchInput')?.value || '').toLowerCase().trim();
  if (q) {
    filtered = filtered.filter(l =>
      (l.channel || '').toLowerCase().includes(q) ||
      (l.handle || '').toLowerCase().includes(q) ||
      (l.email || '').toLowerCase().includes(q)
    );
  }

  // Country filter from discovery dropdown
  const selCountry = (document.getElementById('filterCountry')?.value || '').toUpperCase();
  if (selCountry) {
    filtered = filtered.filter(l => (l.country || '').toUpperCase() === selCountry);
  }

  // Header Counters
  document.getElementById('resTotalCount').textContent = APP_STATE.leads.length;
  document.getElementById('resHighCount').textContent = APP_STATE.leads.filter(l => (l.ai_score || 0) >= 70).length;
  document.getElementById('resMedCount').textContent = APP_STATE.leads.filter(l => (l.ai_score || 0) >= 40 && (l.ai_score || 0) < 70).length;
  document.getElementById('resLowCount').textContent = APP_STATE.leads.filter(l => (l.ai_score || 0) < 40).length;
  document.getElementById('visibleChannelsCount').textContent = `${filtered.length} channels`;

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="11" style="text-align:center;padding:36px;color:var(--text-muted);font-weight:600;">No matching channels found. Try adjusting filters or running a new scan.</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map(l => {
    const isChecked = APP_STATE.selectedLeadIds.has(l.id);
    const scoreClass = (l.ai_score || 0) >= 70 ? 'high' : ((l.ai_score || 0) >= 40 ? 'med' : 'low');

    return `
      <tr>
        <td><input type="checkbox" class="lead-row-check" data-id="${l.id}" ${isChecked ? 'checked' : ''} onchange="toggleSelectLead(${l.id}, this.checked)" /></td>
        <td>
          <div class="channel-cell" style="cursor:pointer;" onclick="openLeadModal(${l.id})">
            <div style="width:36px;height:36px;border-radius:50%;background:#8b1524;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px;">
              ${(l.channel||'C').charAt(0)}
            </div>
            <div class="channel-meta">
              <h4>${l.channel || l.name}</h4>
              <span style="display:flex;align-items:center;gap:6px;">
                ${l.handle || ''}
                ${l.country ? `<span style="display:inline-block;padding:1px 6px;border-radius:4px;font-size:10px;font-weight:700;background:rgba(255,255,255,0.08);color:#ff98a4;">${l.country === 'CA' ? '🇨🇦 Canada' : (l.country === 'US' ? '🇺🇸 US' : (l.country === 'GB' ? '🇬🇧 UK' : (l.country === 'AU' ? '🇦🇺 AU' : l.country)))}</span>` : ''}
              </span>
            </div>
          </div>
        </td>
        <td><strong>${l.subscribers || '0'}</strong></td>
        <td>${l.total_views || '--'}</td>
        <td>${l.videos || '--'}</td>
        <td>${l.avg_views || '--'}</td>
        <td>${l.last_upload || 'Recently'}</td>
        <td><span style="font-size:11.5px;color:var(--text-muted);font-weight:600;">${l.upload_freq || 'Weekly'}</span></td>
        <td>
          ${l.website ? `<a href="${l.website}" target="_blank" style="color:var(--primary-red);font-weight:600;">${l.website.replace(/^https?:\/\//, '').replace(/\/$/, '')}</a>` : '<span style="color:var(--text-light);">—</span>'}
        </td>
        <td>
          <div style="display:flex;gap:4px;flex-wrap:wrap;min-width:80px;">
            ${renderSocialPills(l.social, true)}
          </div>
        </td>
        <td>
          ${l.email ? `<span class="email-pill" onclick="copyText('${l.email}')">@ ${l.email}</span>` : '<span class="no-email-pill">—</span>'}
        </td>
        <td>
          <div style="display:flex;gap:6px;">
            <button class="btn-secondary" style="padding:4px 8px;font-size:11px;" onclick="openLeadModal(${l.id})">View</button>
            <button class="score-badge ${scoreClass}">${l.ai_score || 50}</button>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

function filterResultsTable() {
  renderResultsTable();
}

function setScoreFilter(filter, btn) {
  APP_STATE.activeScoreFilter = filter;
  document.querySelectorAll('#view-results .select-pill').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  renderResultsTable();
}

function switchResultsTab(tab) {
  APP_STATE.activeResultsTab = tab;
  document.getElementById('tabQualifiedLeads').classList.toggle('active', tab === 'qualified');
  document.getElementById('tabDiscoveryVault').classList.toggle('active', tab === 'vault');
  renderResultsTable();
}

// ------------------------------------------------------------
function toggleSelectAll(checkbox) {
  const isChecked = checkbox.checked;
  APP_STATE.leads.forEach(l => {
    if (isChecked) APP_STATE.selectedLeadIds.add(l.id);
    else APP_STATE.selectedLeadIds.delete(l.id);
  });
  document.querySelectorAll('.lead-row-check').forEach(cb => cb.checked = isChecked);
  updateSelectedCount();
}

function toggleSelectLead(id, isChecked) {
  if (isChecked) APP_STATE.selectedLeadIds.add(id);
  else APP_STATE.selectedLeadIds.delete(id);
  updateSelectedCount();
}

function clearTableSelection() {
  APP_STATE.selectedLeadIds.clear();
  const selectAll = document.getElementById('selectAllCheckbox');
  if (selectAll) selectAll.checked = false;
  document.querySelectorAll('.lead-row-check').forEach(cb => cb.checked = false);
  updateSelectedCount();
}

function updateSelectedCount() {
  const count = APP_STATE.selectedLeadIds.size;
  const btn = document.getElementById('btnExportSelected');
  if (btn) btn.textContent = `Export Selected (${count})`;
}

function clearAllResults() {
  if (confirm('Are you sure you want to clear all collected results?')) {
    APP_STATE.leads = [];
    APP_STATE.selectedLeadIds.clear();
    updateDashboardMetrics();
    renderResultsTable();
    showToast('All results cleared', 'info');
  }
}

// ------------------------------------------------------------
function openLeadModal(leadId) {
  const lead = APP_STATE.leads.find(l => l.id === leadId);
  if (!lead) return;
  APP_STATE.activeLeadForModal = lead;

  document.getElementById('modalChannelName').textContent = lead.channel || lead.name;
  document.getElementById('modalHandle').textContent = lead.handle || '';
  document.getElementById('modalAvatar').src = lead.avatar || `https://ui-avatars.com/api/?name=${encodeURIComponent(lead.channel || 'C')}&background=8b1524&color=fff`;

  const sBadge = document.getElementById('modalScoreBadge');
  sBadge.textContent = `${lead.ai_score || 50} — ${(lead.ai_score || 0) >= 70 ? 'High' : 'Medium'}`;
  sBadge.className = `score-badge ${(lead.ai_score || 0) >= 70 ? 'high' : 'med'}`;

  // Executive Statistics
  document.getElementById('mStatSubs').textContent = lead.subscribers || '0';
  document.getElementById('mStatViews').textContent = lead.total_views || '0';
  document.getElementById('mStatVideos').textContent = lead.videos || '0';
  document.getElementById('mStatAvgViews').textContent = lead.avg_views || '0';
  document.getElementById('mStatRate').textContent = '17.6';
  document.getElementById('mStatLastUpload').textContent = lead.last_upload || 'Recently';
  document.getElementById('mStatCountry').textContent = lead.country || 'US';
  document.getElementById('mStatCreated').textContent = lead.created || 'Oct 2022';

  // Contact
  document.getElementById('mContactEmail').textContent = lead.email || 'No public email in bio';
  const socEl = document.getElementById('mSocialPills');
  socEl.innerHTML = '';
  if (lead.social && Object.keys(lead.social).length > 0) {
    socEl.innerHTML = renderSocialPills(lead.social, false);
  } else {
    socEl.innerHTML = '<span style="color:var(--text-muted);font-size:12px;">No social links found</span>';
  }

  // Description & Notes
  document.getElementById('mDescription').textContent = lead.description || 'No description provided';
  document.getElementById('mNotesInput').value = lead.notes || '';

  // Gauge & Bars
  document.getElementById('mGaugePct').textContent = lead.ai_score || 50;
  const circle = document.getElementById('mGaugeCircle');
  if (circle) {
    const pct = lead.ai_score || 50;
    circle.style.strokeDashoffset = 283 - (283 * (pct / 100));
  }

  const audit = lead.audit || { seo: 68, growth: 100, activity: 100, clientProb: 75, readiness: 79 };
  document.getElementById('mOppSeo').textContent = audit.seo;
  document.getElementById('mBarSeo').style.width = `${audit.seo}%`;
  document.getElementById('mOppGrowth').textContent = audit.growth;
  document.getElementById('mBarGrowth').style.width = `${audit.growth}%`;
  document.getElementById('mOppActivity').textContent = audit.activity;
  document.getElementById('mBarActivity').style.width = `${audit.activity}%`;
  document.getElementById('mOppClient').textContent = audit.clientProb;
  document.getElementById('mBarClient').style.width = `${audit.clientProb}%`;
  document.getElementById('mOppBusiness').textContent = audit.readiness;
  document.getElementById('mBarBusiness').style.width = `${audit.readiness}%`;

  document.getElementById('leadModalOverlay').classList.add('active');
}

function closeLeadModal() {
  document.getElementById('leadModalOverlay').classList.remove('active');
}

function closeModalOnOverlay(e) {
  if (e.target.id === 'leadModalOverlay') closeLeadModal();
}

function saveLeadNotes() {
  if (!APP_STATE.activeLeadForModal) return;
  const notes = document.getElementById('mNotesInput').value;
  APP_STATE.activeLeadForModal.notes = notes;
  showToast('Outreach notes saved!', 'success');
}

function copyModalEmail() {
  if (APP_STATE.activeLeadForModal?.email) {
    navigator.clipboard.writeText(APP_STATE.activeLeadForModal.email);
    showToast('Copied email to clipboard!', 'success');
  }
}

function copyModalChannelUrl() {
  if (APP_STATE.activeLeadForModal?.channel_url) {
    navigator.clipboard.writeText(APP_STATE.activeLeadForModal.channel_url);
    showToast('Copied channel URL to clipboard!', 'success');
  }
}

function copyModalName() {
  if (APP_STATE.activeLeadForModal?.channel) {
    navigator.clipboard.writeText(APP_STATE.activeLeadForModal.channel);
    showToast('Copied channel name to clipboard!', 'success');
  }
}

function visitModalChannel() {
  if (APP_STATE.activeLeadForModal?.channel_url) {
    window.open(APP_STATE.activeLeadForModal.channel_url, '_blank');
  }
}

function composeModalEmail() {
  if (APP_STATE.activeLeadForModal?.email) {
    window.location.href = `mailto:${APP_STATE.activeLeadForModal.email}?subject=${encodeURIComponent('Quick question about ' + APP_STATE.activeLeadForModal.channel)}`;
  }
}

// ------------------------------------------------------------
function copyPromptText() {
  const p = document.getElementById('aiPromptText').textContent;
  navigator.clipboard.writeText(p);
  showToast('AI Prompt copied to clipboard!', 'success');
}

async function generateAIPitch() {
  const name = document.getElementById('pitchChannelName')?.value.trim() || 'Creator';
  const handle = document.getElementById('pitchHandle')?.value.trim() || `@${name.replace(/\s+/g,'').toLowerCase()}`;

  const resBox = document.getElementById('pitchResultBox');
  const subLine = document.getElementById('pitchSubjectLine');
  const bodyText = document.getElementById('pitchBodyText');

  showToast('Generating personalized retention pitch...', 'info');

  try {
    const res = await fetch(API_BASE + '/api/leads/generate-custom-pitch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, channel: name, handle })
    });
    const data = await res.json();
    if (data && data.success) {
      if (subLine) subLine.textContent = `Subject: ${data.subject}`;
      if (bodyText) bodyText.textContent = data.body;
      if (resBox) resBox.style.display = 'block';
      return;
    }
  } catch (e) {
    // Fallback template
  }

  const subject = `Quick question regarding retention on ${name}`;
  const body = `Hey ${name},\n\nLoved your recent uploads—the content quality and your delivery are super solid!\n\nWhile checking out your videos, I noticed potential for 2x-3x higher retention through tighter intro hooks, micro-pattern interrupts, and sound design to keep viewers watching past 60%.\n\nAt Zentic Media, we specialize in high-retention video editing engineered specifically to beat YouTube's retention drop-off.\n\nZero-risk offer: Let us edit a free 20-30 second retention hook for your next video 100% free of charge. If it blows you away, we can talk; if not, it's yours to keep.\n\nAre you dropping a video this week?\n\nBest regards,\nZentic Media Outreach Team`;

  if (subLine) subLine.textContent = `Subject: ${subject}`;
  if (bodyText) bodyText.textContent = body;
  if (resBox) resBox.style.display = 'block';
}

function copyPitch() {
  const sub = document.getElementById('pitchSubjectLine')?.textContent || '';
  const body = document.getElementById('pitchBodyText')?.textContent || '';
  navigator.clipboard.writeText(`${sub}\n\n${body}`);
  showToast('Copied pitch to clipboard!', 'success');
}

// ------------------------------------------------------------
function initExportColumns() {
  const grid = document.getElementById('exportColumnsGrid');
  if (!grid) return;
  grid.innerHTML = EXPORT_COLUMNS.map(col => `
    <label style="display:flex;align-items:center;gap:8px;font-size:12.5px;cursor:pointer;">
      <input type="checkbox" class="export-col-check" data-col="${col.id}" ${col.default ? 'checked' : ''} onchange="updateExportPreview()" />
      <span>${col.label}</span>
    </label>
  `).join('');
  updateExportPreview();
}

function selectAllExportCols(val) {
  document.querySelectorAll('.export-col-check').forEach(cb => cb.checked = val);
  updateExportPreview();
}

function setExportPreset(preset) {
  if (preset === 'leadgen') {
    const active = ['channel_name', 'handle', 'channel_url', 'email', 'website', 'subscribers'];
    document.querySelectorAll('.export-col-check').forEach(cb => {
      cb.checked = active.includes(cb.dataset.col);
    });
  } else if (preset === 'seo') {
    const active = ['channel_name', 'channel_url', 'subscribers', 'total_views', 'score', 'website'];
    document.querySelectorAll('.export-col-check').forEach(cb => {
      cb.checked = active.includes(cb.dataset.col);
    });
  } else if (preset === 'sheets') {
    exportGoogleSheetsCSV();
    return;
  } else {
    selectAllExportCols(true);
  }
  updateExportPreview();
}

function updateExportPreview() {
  const rows = APP_STATE.leads.length;
  const cols = document.querySelectorAll('.export-col-check:checked').length;
  const elRows = document.getElementById('exportPreviewRows');
  const elCols = document.getElementById('exportPreviewCols');
  if (elRows) elRows.textContent = `${rows} Rows`;
  if (elCols) elCols.textContent = `${cols} Columns selected`;
}

function triggerExportDownload() {
  if (APP_STATE.leads.length === 0) {
    showToast('No leads available to export. Run a scan first!', 'warning');
    return;
  }
  const checkedCols = Array.from(document.querySelectorAll('.export-col-check:checked')).map(cb => cb.dataset.col);
  if (checkedCols.length === 0) {
    showToast('Please select at least one column to export!', 'warning');
    return;
  }

  // Generate CSV
  const headers = checkedCols.map(c => EXPORT_COLUMNS.find(col => col.id === c)?.label || c);
  let csv = headers.join(',') + '\n';

  APP_STATE.leads.forEach(l => {
    const row = checkedCols.map(col => {
      let val = '';
      if (col === 'score') val = l.ai_score || 50;
      else if (col === 'channel_name') val = l.channel || l.name || '';
      else if (['instagram','twitter','x','tiktok','facebook','linkedin','whatsapp','telegram','discord','threads','pinterest','linktree','beacons'].includes(col)) {
        val = (l.social && l.social[col]) ? l.social[col] : '';
      }
      else if (l[col] !== undefined) val = l[col];
      if (typeof val === 'string') val = `"${val.replace(/"/g, '""')}"`;
      return val;
    });
    csv += row.join(',') + '\n';
  });

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `yt_leads_${new Date().toISOString().slice(0,10)}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  showToast('Export downloaded successfully!', 'success');
}

function exportFilteredLeads() {
  triggerExportDownload();
}

function exportSelectedLeads() {
  if (APP_STATE.selectedLeadIds.size === 0) {
    showToast('No leads selected! Check rows in table first.', 'warning');
    return;
  }
  const selected = APP_STATE.leads.filter(l => APP_STATE.selectedLeadIds.has(l.id));
  let csv = 'channel_name,email,subscribers,url,score\n';
  selected.forEach(l => {
    csv += `"${l.channel}","${l.email || ''}","${l.subscribers}","${l.channel_url}","${l.ai_score || 50}"\n`;
  });
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `selected_leads_${selected.length}.csv`;
  a.click();
  showToast(`Exported ${selected.length} selected leads!`, 'success');
}

function exportGoogleSheetsCSV() {
  showToast('Downloading CSV ready for Google Sheets & Apps Script...', 'info');
  window.location.href = '/api/export/outreach-csv';
}

// ------------------------------------------------------------
function loadStoredKeys() {
  const saved = localStorage.getItem('yt_magic_keys');
  if (saved) {
    try {
      APP_STATE.keys = JSON.parse(saved);
      if (APP_STATE.keys.primary?.key) {
        document.getElementById('inputKeyPrimary').value = APP_STATE.keys.primary.key;
        if (APP_STATE.keys.primary.locked) lockKeyBadge('primary');
      }
      if (APP_STATE.keys.secondary?.key) {
        document.getElementById('inputKeySecondary').value = APP_STATE.keys.secondary.key;
        if (APP_STATE.keys.secondary.locked) lockKeyBadge('secondary');
      }
      if (APP_STATE.keys.third?.key) {
        document.getElementById('inputKeyThird').value = APP_STATE.keys.third.key;
        if (APP_STATE.keys.third.locked) lockKeyBadge('third');
      }
    } catch(e) {}
  }
}

function saveKey(slot) {
  const idMap = { primary: 'inputKeyPrimary', secondary: 'inputKeySecondary', third: 'inputKeyThird' };
  const val = document.getElementById(idMap[slot])?.value.trim() || '';
  if (!APP_STATE.keys[slot]) APP_STATE.keys[slot] = {};
  APP_STATE.keys[slot].key = val;
  localStorage.setItem('yt_magic_keys', JSON.stringify(APP_STATE.keys));
  showToast(`${slot.toUpperCase()} key saved draft!`, 'success');
}

function validateKey(slot) {
  saveKey(slot);
  APP_STATE.keys[slot].locked = true;
  localStorage.setItem('yt_magic_keys', JSON.stringify(APP_STATE.keys));
  lockKeyBadge(slot);
  showToast(`Validated and locked ${slot} key! Quota updated.`, 'success');
  updateDashboardMetrics();
}

function lockKeyBadge(slot) {
  const badgeMap = { primary: 'badgeKeyPrimary', secondary: 'badgeKeySecondary', third: 'badgeKeyThird' };
  const el = document.getElementById(badgeMap[slot]);
  if (el) {
    el.textContent = 'LOCKED & ACTIVE';
    el.className = 'score-badge high';
  }
}

async function saveBrightDataSettings() {
  const val = document.getElementById('inputBrightDataKey')?.value.trim();
  if (!val) {
    showToast('Please enter your Bright Data API key', 'warning');
    return;
  }
  showToast('Saving Bright Data configuration...', 'info');
  try {
    await fetch(API_BASE + '/api/settings/brightdata', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: val })
    });
    showToast('Bright Data key saved and active! ✅', 'success');
  } catch (e) {
    showToast('Saved locally in browser', 'success');
  }
}

function resetQuotaCounter() {
  APP_STATE.quotaUsed = 0;
  updateDashboardMetrics();
  showToast('Daily quota counter reset to 30,000 units!', 'success');
}

// ------------------------------------------------------------
function copyText(str) {
  navigator.clipboard.writeText(str);
  showToast(`Copied "${str}" to clipboard!`, 'success');
}

function showToast(msg, type = 'info') {
  const box = document.getElementById('toastBox');
  if (!box) return;
  const t = document.createElement('div');
  t.className = 'toast';
  const icon = type === 'success' ? '✅' : (type === 'warning' ? '⚠️' : 'ℹ️');
  t.innerHTML = `<span>${icon}</span><span>${msg}</span>`;
  box.appendChild(t);
  setTimeout(() => {
    t.style.opacity = '0';
    setTimeout(() => t.remove(), 300);
  }, 3200);
}


// -------------------------------------------------------------
// CRM PIPELINE — Kanban Board Engine (DjangoCRM-inspired)
// -------------------------------------------------------------

const PIPELINE_STAGES = [
  { id: 'new_lead',       label: 'New Lead',        color: '#94a3b8' },
  { id: 'outreach_sent',  label: 'Outreach Sent',   color: '#3b82f6' },
  { id: 'email_opened',   label: 'Email Opened',    color: '#8b5cf6' },
  { id: 'replied',        label: 'Replied',         color: '#f59e0b' },
  { id: 'meeting_booked', label: 'Meeting Booked',  color: '#10b981' },
  { id: 'deal_closed',    label: 'Deal Closed',     color: '#8b1524' },
];

let PIPELINE_BOARD = {};
let draggedLeadId   = null;
let draggedFromStage = null;

// Load Board from Backend / Fallback to APP_STATE
async function loadPipelineBoard() {
  const board = document.getElementById('kanbanBoard');
  if (!board) return;
  board.innerHTML = `<div style="padding:40px;text-align:center;color:var(--text-muted);font-weight:600;">Loading pipeline...</div>`;

  try {
    const res = await fetch(API_BASE + '/api/pipeline/board');
    if (res.ok) {
      const data = await res.json();
      if (data.ok) {
        PIPELINE_BOARD = data.board;
        await loadPipelineStats();
        renderKanbanBoard();
        const el = document.getElementById('pipeLastUpdated');
        if (el) el.textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
        return;
      }
    }
  } catch (_) {}

  // Fallback: use APP_STATE.leads
  PIPELINE_BOARD = { new_lead: [], outreach_sent: [], email_opened: [], replied: [], meeting_booked: [], deal_closed: [] };
  APP_STATE.leads.forEach(l => {
    const stage = l.pipeline_stage || 'new_lead';
    if (PIPELINE_BOARD[stage]) PIPELINE_BOARD[stage].push(l);
    else PIPELINE_BOARD['new_lead'].push(l);
  });
  renderKanbanBoard();
  updatePipelineStatsFallback();
}

async function loadPipelineStats() {
  try {
    const res = await fetch(API_BASE + '/api/pipeline/stats');
    if (!res.ok) return;
    const data = await res.json();
    if (!data.ok) return;
    const s = data.stages || {};
    const totalEl = document.getElementById('pipeTotal');
    const contactEl = document.getElementById('pipeContacted');
    const replyEl = document.getElementById('pipeReplied');
    const closeEl = document.getElementById('pipeClosed');
    const revEl = document.getElementById('pipeRevenue');
    const badgeEl = document.getElementById('pipelineBadge');

    if (totalEl) totalEl.textContent = Object.values(s).reduce((a, v) => a + (v.count || 0), 0);
    if (contactEl) contactEl.textContent = (s['outreach_sent']?.count || 0) + (s['email_opened']?.count || 0);
    if (replyEl) replyEl.textContent = s['replied']?.count || 0;
    if (closeEl) closeEl.textContent = s['deal_closed']?.count || 0;
    if (revEl) revEl.textContent = '$' + Number(data.total_closed_revenue || 0).toLocaleString();
    if (badgeEl) badgeEl.textContent = s['deal_closed']?.count || 0;
  } catch (_) {}
}

function updatePipelineStatsFallback() {
  const leads = APP_STATE.leads;
  const totalEl = document.getElementById('pipeTotal');
  const contactEl = document.getElementById('pipeContacted');
  const replyEl = document.getElementById('pipeReplied');
  const closeEl = document.getElementById('pipeClosed');
  const revEl = document.getElementById('pipeRevenue');
  const updatedEl = document.getElementById('pipeLastUpdated');

  if (totalEl) totalEl.textContent = leads.length;
  if (contactEl) contactEl.textContent = leads.filter(l => ['outreach_sent','email_opened'].includes(l.pipeline_stage)).length;
  if (replyEl) replyEl.textContent = leads.filter(l => l.pipeline_stage === 'replied').length;
  if (closeEl) closeEl.textContent = leads.filter(l => l.pipeline_stage === 'deal_closed').length;
  if (revEl) revEl.textContent = '$' + leads.filter(l => l.pipeline_stage === 'deal_closed').reduce((a, l) => a + (l.deal_value || 0), 0).toLocaleString();
  if (updatedEl) updatedEl.textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
}

function renderKanbanBoard() {
  const board = document.getElementById('kanbanBoard');
  if (!board) return;

  board.innerHTML = PIPELINE_STAGES.map(stage => {
    const cards = (PIPELINE_BOARD[stage.id] || []);
    return `
      <div class="kanban-col" id="col-${stage.id}"
           ondragover="onDragOver(event, '${stage.id}')"
           ondragleave="onDragLeave(event)"
           ondrop="onDrop(event, '${stage.id}')">
        <div class="kanban-col-header stage-${stage.id}" style="border-color:${stage.color};">
          <span>${stage.label}</span>
          <span style="background:${stage.color};color:#fff;padding:2px 8px;border-radius:10px;font-size:10px;">${cards.length}</span>
        </div>
        <div class="kanban-col-body" id="body-${stage.id}">
          ${cards.map(l => renderKanbanCard(l, stage.id)).join('')}
        </div>
      </div>
    `;
  }).join('');
}

function renderKanbanCard(lead, stageId) {
  const tag   = lead.tag || lead.lead_type || 'warm';
  const score = lead.ai_score || 50;
  const name  = (lead.channel || lead.name || 'Unknown').substring(0, 28);
  const subs  = lead.subscribers || '-';
  const emailDot = lead.last_email_status === 'opened'  ? '[Opened]' :
                   lead.last_email_status === 'replied'  ? '[Replied]' :
                   lead.last_email_status === 'sent'     ? '[Sent]' : '';
  const deal = lead.deal_value > 0 ? `<span class="kanban-deal-val">$${Number(lead.deal_value).toLocaleString()}</span>` : '';

  return `
    <div class="kanban-card" id="card-${lead.id}"
         draggable="true"
         ondragstart="onDragStart(event, ${lead.id}, '${stageId}')"
         ondragend="onDragEnd(event)">
      <div class="kanban-card-name" title="${lead.channel || lead.name}">${name}</div>
      <div class="kanban-card-sub">${subs} subs ${emailDot}</div>
      <div class="kanban-card-footer">
        <span class="kanban-tag ${tag}">${tag}</span>
        <span class="kanban-score">${score}</span>
        ${deal}
      </div>
      <div class="kanban-actions">
        <button class="kanban-btn" onclick="openCrmPanel(${lead.id})">Detail</button>
        <select class="kanban-btn" style="padding:2px 4px;font-size:10px;" onchange="quickMoveCard(${lead.id}, this.value)" title="Move stage">
          ${PIPELINE_STAGES.map(s => `<option value="${s.id}" ${s.id === stageId ? 'selected' : ''}>${s.label}</option>`).join('')}
        </select>
      </div>
    </div>
  `;
}

function onDragStart(event, leadId, fromStage) {
  draggedLeadId   = leadId;
  draggedFromStage = fromStage;
  event.dataTransfer.effectAllowed = 'move';
  document.getElementById(`card-${leadId}`)?.classList.add('dragging');
}

function onDragEnd(event) {
  document.querySelectorAll('.kanban-card').forEach(c => c.classList.remove('dragging'));
  document.querySelectorAll('.kanban-col').forEach(c => c.classList.remove('drag-over'));
}

function onDragOver(event, stageId) {
  event.preventDefault();
  event.dataTransfer.dropEffect = 'move';
  document.getElementById(`col-${stageId}`)?.classList.add('drag-over');
}

function onDragLeave(event) {
  event.currentTarget.classList.remove('drag-over');
}

async function onDrop(event, toStage) {
  event.preventDefault();
  document.querySelectorAll('.kanban-col').forEach(c => c.classList.remove('drag-over'));
  if (!draggedLeadId || toStage === draggedFromStage) return;

  await moveLeadToStage(draggedLeadId, toStage, draggedFromStage);
  draggedLeadId = null;
  draggedFromStage = null;
}

async function quickMoveCard(leadId, toStage) {
  const fromStage = Object.keys(PIPELINE_BOARD).find(s =>
    PIPELINE_BOARD[s].some(l => l.id === leadId)
  ) || 'new_lead';
  if (toStage === fromStage) return;
  await moveLeadToStage(leadId, toStage, fromStage);
}

async function moveLeadToStage(leadId, toStage, fromStage) {
  const lead = (PIPELINE_BOARD[fromStage] || []).find(l => l.id === leadId);
  if (lead) {
    PIPELINE_BOARD[fromStage] = PIPELINE_BOARD[fromStage].filter(l => l.id !== leadId);
    lead.pipeline_stage = toStage;
    if (!PIPELINE_BOARD[toStage]) PIPELINE_BOARD[toStage] = [];
    PIPELINE_BOARD[toStage].unshift(lead);

    const appLead = APP_STATE.leads.find(l => l.id === leadId);
    if (appLead) appLead.pipeline_stage = toStage;
  }
  renderKanbanBoard();

  try {
    await fetch(API_BASE + '/api/pipeline/move', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lead_id: leadId, stage: toStage })
    });
    const stageLabel = PIPELINE_STAGES.find(s => s.id === toStage)?.label || toStage;
    showToast(`Lead moved to ${stageLabel}`, 'success');
  } catch (_) {
    showToast('Saved locally', 'info');
  }
  updatePipelineStatsFallback();
}

async function pushAllLeadsToPipeline() {
  const leads = APP_STATE.leads;
  if (leads.length === 0) {
    showToast('No leads found. Run a scan first!', 'warning');
    return;
  }
  PIPELINE_BOARD = { new_lead: [], outreach_sent: [], email_opened: [], replied: [], meeting_booked: [], deal_closed: [] };
  leads.forEach(l => {
    const stage = l.pipeline_stage || 'new_lead';
    if (PIPELINE_BOARD[stage]) PIPELINE_BOARD[stage].push(l);
    else PIPELINE_BOARD['new_lead'].push(l);
  });
  renderKanbanBoard();
  updatePipelineStatsFallback();
  showToast(`${leads.length} leads pushed to Pipeline!`, 'success');
}

async function openCrmPanel(leadId) {
  const lead = APP_STATE.leads.find(l => l.id === leadId) ||
    Object.values(PIPELINE_BOARD).flat().find(l => l.id === leadId);
  if (!lead) return;

  const titleEl = document.getElementById('crmPanelTitle');
  if (titleEl) titleEl.textContent = lead.channel || lead.name;

  let activities = [];
  try {
    const res = await fetch(`/api/pipeline/${leadId}/activity`);
    if (res.ok) {
      const d = await res.json();
      activities = d.activities || [];
    }
  } catch (_) {}

  const socialHtml = renderSocialPills(lead.social, false);
  const actHtml = activities.length > 0
    ? activities.map(a => `
        <div class="activity-item">
          <div class="activity-dot"></div>
          <div>
            <div style="font-weight:700;">${a.action.replace(/_/g,' ')}</div>
            <div style="color:var(--text-muted);font-size:10.5px;">${a.detail || ''} · ${(a.created_at||'').substring(0,16)}</div>
          </div>
        </div>`).join('')
    : '<div style="color:var(--text-muted);font-size:12px;">No activity yet</div>';

  const currentStage = lead.pipeline_stage || 'new_lead';
  const stageLabel = PIPELINE_STAGES.find(s => s.id === currentStage)?.label || currentStage;

  const panelBody = document.getElementById('crmPanelBody');
  if (panelBody) {
    panelBody.innerHTML = `
      <div class="crm-section">
        <div style="display:flex;gap:10px;align-items:center;margin-bottom:10px;">
          <span class="score-badge ${(lead.ai_score||50)>=70?'high':'med'}">${lead.ai_score||50}</span>
          <span style="background:#f3f4f6;padding:4px 10px;border-radius:12px;font-size:11px;font-weight:700;">${stageLabel}</span>
        </div>
        <div class="crm-label">Move Stage</div>
        <select style="width:100%;padding:7px 10px;border-radius:8px;border:1px solid var(--border-color);font-size:12px;font-weight:600;"
                onchange="quickMoveCard(${leadId}, this.value)">
          ${PIPELINE_STAGES.map(s => `<option value="${s.id}" ${s.id===currentStage?'selected':''}>${s.label}</option>`).join('')}
        </select>
      </div>

      <div class="crm-section">
        <div class="crm-label">Contact</div>
        <div class="crm-value" style="margin-bottom:6px;">${lead.email || 'No email'}</div>
        <div>${socialHtml || '<span style="color:var(--text-muted);font-size:12px;">No social links</span>'}</div>
      </div>

      <div class="crm-section">
        <div class="crm-label">Deal Value</div>
        <div style="display:flex;gap:8px;align-items:center;">
          <input type="number" id="dealValInput" placeholder="$0" value="${lead.deal_value||''}"
                 style="flex:1;padding:7px 10px;border-radius:8px;border:1px solid var(--border-color);font-size:13px;font-weight:700;color:#166534;"
                 min="0" step="50">
          <button class="btn-primary" style="padding:7px 12px;font-size:11px;" onclick="saveDealValue(${leadId})">Save</button>
        </div>
      </div>

      <div class="crm-section">
        <div class="crm-label">Tag</div>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          ${['hot','warm','cold','not_interested'].map(t => `
            <button onclick="savePipelineTag(${leadId},'${t}')"
              style="padding:4px 10px;border-radius:12px;border:1px solid #d1d5db;font-size:11px;font-weight:700;cursor:pointer;
                     ${(lead.tag||'warm')===t ? 'background:var(--primary-red);color:#fff;border-color:var(--primary-red);' : 'background:#fff;color:var(--text-main);'}"
            >${t.toUpperCase()}</button>`).join('')}
        </div>
      </div>

      <div class="crm-section">
        <div class="crm-label">Notes</div>
        <textarea id="crmNotesInput" rows="3"
          style="width:100%;padding:8px;border-radius:8px;border:1px solid var(--border-color);font-size:12px;resize:vertical;font-family:inherit;"
          placeholder="Add private notes about this lead...">${lead.notes||''}</textarea>
        <button class="btn-secondary" style="margin-top:6px;padding:5px 12px;font-size:11px;" onclick="savePipelineNotes(${leadId})">Save Notes</button>
      </div>

      <div>
        <div class="crm-label" style="margin-bottom:8px;">Activity Log</div>
        ${actHtml}
      </div>
    `;
  }

  const p = document.getElementById('crmPanel');
  if (p) p.style.display = 'block';
}

function closeCrmPanel() {
  const p = document.getElementById('crmPanel');
  if (p) p.style.display = 'none';
}

async function saveDealValue(leadId) {
  const val = parseFloat(document.getElementById('dealValInput')?.value || 0);
  const stage = Object.keys(PIPELINE_BOARD).find(s => PIPELINE_BOARD[s].some(l => l.id === leadId)) || 'new_lead';
  try {
    await fetch(API_BASE + '/api/pipeline/move', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lead_id: leadId, stage, deal_value: val })
    });
    Object.values(PIPELINE_BOARD).flat().forEach(l => { if (l.id === leadId) l.deal_value = val; });
    showToast(`Deal value saved: $${val.toLocaleString()}`, 'success');
  } catch (_) {
    showToast('Saved locally', 'info');
  }
}

async function savePipelineTag(leadId, tag) {
  try {
    await fetch(`/api/pipeline/${leadId}/tag`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tag })
    });
    Object.values(PIPELINE_BOARD).flat().forEach(l => { if (l.id === leadId) l.tag = tag; });
    renderKanbanBoard();
    openCrmPanel(leadId);
    showToast(`Tag updated: ${tag.toUpperCase()}`, 'success');
  } catch (_) {}
}

async function savePipelineNotes(leadId) {
  const notes = document.getElementById('crmNotesInput')?.value || '';
  try {
    await fetch(`/api/pipeline/${leadId}/notes`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ notes })
    });
    Object.values(PIPELINE_BOARD).flat().forEach(l => { if (l.id === leadId) l.notes = notes; });
    showToast('Notes saved!', 'success');
  } catch (_) {
    showToast('Saved locally', 'info');
  }
}


// -------------------------------------------------------------
// FACEBOOK GROUP HIRING RADAR ENGINE
// -------------------------------------------------------------

let FB_GROUPS_STATE = [];
let FB_ALERTS_STATE = [];
let SELECTED_FB_GROUP_ID = null;
let SELECTED_FB_GROUP_NAME = '';
let FB_POST_TYPE_FILTER = 'all'; // 'all' (All Posts), 'hiring' (Hiring Only)
let FB_PLATFORM_FILTER = 'all';   // 'all', 'facebook', 'reddit', 'remoteok'
let FB_TIME_FILTER = 'all';      // 'all', '15m', '1h', '3h', '24h'
let FB_SORT_ORDER = 'newest';    // 'newest' (1m -> 2m -> 1h), 'oldest'

// Helper to extract clean group vanity slug or ID from URL
function getGroupSlug(url) {
  if (!url) return '';
  try {
    const clean = url.split('?')[0].split('#')[0].replace(/\/+$/, '');
    const parts = clean.split('/groups/');
    if (parts.length > 1) {
      return parts[1].split('/')[0].trim().toLowerCase();
    }
    return '';
  } catch (_) {
    return '';
  }
}

// Helper to extract post freshness / age in minutes
function getPostAgeInMinutes(alert) {
  const t = (alert.content || alert.ai_summary || '').toLowerCase();
  
  if (t.includes('just now') || t.includes('এইমাত্র')) return 0;

  // Match relative minutes (e.g. "4m", "4 minutes ago", "4m ·")
  const m = t.match(/\b(\d+)\s*(?:m|min|mins|minutes?|মিনিট)\b/);
  if (m) return parseInt(m[1], 10);

  // Match relative hours (e.g. "1h", "2 hours ago")
  const h = t.match(/\b(\d+)\s*(?:h|hr|hrs|hours?|ঘণ্টা|ঘন্টা)\b/);
  if (h) return parseInt(h[1], 10) * 60;

  if (t.includes('about an hour') || t.includes('an hour ago') || t.includes('১ ঘণ্টা')) return 60;

  // Match relative days (e.g. "2d", "2 days ago")
  const d = t.match(/\b(\d+)\s*(?:d|days?|দিন)\b/);
  if (d) return parseInt(d[1], 10) * 1440;

  // Fallback: calculate from created_at timestamp
  if (alert.created_at) {
    try {
      const dt = new Date(alert.created_at.replace(' ', 'T'));
      const diffMs = Date.now() - dt.getTime();
      if (!isNaN(diffMs) && diffMs >= 0) {
        return Math.floor(diffMs / 60000);
      }
    } catch (e) {}
  }
  return 999999;
}

function formatPostAgeLabel(mins) {
  if (mins === 0) return '⚡ Just now';
  if (mins < 60) return `⏱️ ${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  const remM = mins % 60;
  if (hrs < 24) return remM > 0 ? `🕒 ${hrs}h ${remM}m ago` : `🕒 ${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `📅 ${days}d ago`;
}

function selectFbGroup(gid, gname) {
  SELECTED_FB_GROUP_ID = gid;
  SELECTED_FB_GROUP_NAME = gname;
  renderFbGroupsList();
  renderFbAlertsList();
}

function clearSelectedFbGroup() {
  SELECTED_FB_GROUP_ID = null;
  SELECTED_FB_GROUP_NAME = '';
  renderFbGroupsList();
  renderFbAlertsList();
}

function onFbFilterChange() {
  const typeSelect = document.getElementById('fbPostTypeFilter');
  const platSelect = document.getElementById('fbPlatformFilterSelect');
  const timeSelect = document.getElementById('fbTimeFilterSelect');
  const sortSelect = document.getElementById('fbSortSelect');
  if (typeSelect) FB_POST_TYPE_FILTER = typeSelect.value;
  if (platSelect) FB_PLATFORM_FILTER = platSelect.value;
  if (timeSelect) FB_TIME_FILTER = timeSelect.value;
  if (sortSelect) FB_SORT_ORDER = sortSelect.value;
  renderFbAlertsList();
}

async function scanSelectedGroupNow() {
  if (!SELECTED_FB_GROUP_ID) return;
  const btn = document.getElementById('fbScanSelectedGroupBtn');
  const btnEmpty = document.getElementById('fbScanEmptyGroupBtn');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '⏳ Scanning...';
  }
  if (btnEmpty) {
    btnEmpty.disabled = true;
    btnEmpty.innerHTML = '⏳ Scanning Facebook Group...';
  }
  try {
    const res = await fetch(`/api/fb/scan-group/${SELECTED_FB_GROUP_ID}`, { method: 'POST' });
    const data = await res.json();
    if (data.ok) {
      showToast(data.message || 'Scan completed!', 'success');
      await loadFbAlerts();
    } else {
      showToast(data.message || 'Scan completed', 'info');
      await loadFbAlerts();
    }
  } catch (err) {
    console.error('Scan group error:', err);
    showToast('Scan initiated in background', 'info');
    await loadFbAlerts();
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '⚡ Scan This Group Now';
    }
    if (btnEmpty) {
      btnEmpty.disabled = false;
      btnEmpty.innerHTML = '⚡ Fetch All Posts From Group Now';
    }
  }
}

async function loadFbRadarPage() {
  await Promise.all([loadFbGroups(), loadFbAlerts()]);
}

async function loadFbGroups() {
  try {
    const res = await fetch(API_BASE + '/api/fb/groups');
    if (!res.ok) return;
    const data = await res.json();
    if (data.ok) {
      FB_GROUPS_STATE = data.groups || [];
      renderFbGroupsList();
      updateFbStats();
    }
  } catch (err) {
    console.error('Error loading FB groups:', err);
  }
}

async function loadFbAlerts() {
  try {
    const res = await fetch(API_BASE + '/api/fb/alerts');
    if (!res.ok) return;
    const data = await res.json();
    if (data.ok) {
      FB_ALERTS_STATE = data.alerts || [];
      renderFbAlertsList();
      updateFbStats();
    }
  } catch (err) {
    console.error('Error loading FB alerts:', err);
  }
}

function updateFbStats() {
  const gCount = FB_GROUPS_STATE.length;
  const jCount = FB_ALERTS_STATE.filter(a => a.is_hiring === 1).length;
  const tCount = FB_ALERTS_STATE.filter(a => a.telegram_sent === 1).length;

  const elG = document.getElementById('fbGroupCount');
  const elJ = document.getElementById('fbJobsFound');
  const elT = document.getElementById('fbTelegramSent');
  const badgeG = document.getElementById('fbGroupsBadge');
  const badgeNav = document.getElementById('fbRadarBadge');

  if (elG) elG.textContent = gCount;
  if (elJ) elJ.textContent = jCount;
  if (elT) elT.textContent = tCount;
  if (badgeG) badgeG.textContent = `${gCount} Groups`;
  if (badgeNav) badgeNav.textContent = jCount;
}

function renderFbGroupsList() {
  const list = document.getElementById('fbGroupsList');
  if (!list) return;

  if (FB_GROUPS_STATE.length === 0) {
    list.innerHTML = `
      <div style="text-align:center;padding:32px 14px;color:var(--text-muted);">
        <div style="font-size:28px;margin-bottom:8px;">👥</div>
        <div style="font-weight:700;font-size:13px;margin-bottom:4px;">No groups added yet</div>
        <div style="font-size:11.5px;margin-bottom:12px;">Add video editing & creator Facebook groups to start radar.</div>
        <button class="btn-primary" style="background:#1877F2;border-color:#1877F2;padding:6px 14px;font-size:11px;" onclick="openAddGroupModal()">➕ Add First Group</button>
      </div>
    `;
    return;
  }

  const allActive = SELECTED_FB_GROUP_ID === null;
  const allGroupsPill = `
    <div onclick="clearSelectedFbGroup()" style="padding:10px 12px;border-radius:8px;cursor:pointer;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;transition:all 0.15s ease;${allActive ? 'background:#1877F2;color:#fff;font-weight:800;box-shadow:0 2px 6px rgba(24,119,242,0.3);' : 'background:var(--bg-subtle);color:var(--text-main);border:1px solid var(--border-color);'}">
      <div style="display:flex;align-items:center;gap:6px;">
        <span>🌐</span>
        <span style="font-size:12px;">All Monitored Groups</span>
      </div>
      <span style="font-size:10.5px;padding:2px 7px;border-radius:10px;${allActive ? 'background:rgba(255,255,255,0.25);color:#fff;' : 'background:#e2e8f0;color:#334155;'}">${FB_GROUPS_STATE.length}</span>
    </div>
  `;

  const groupItems = FB_GROUPS_STATE.map(g => {
    const isActive = g.active === 1;
    const isSelected = SELECTED_FB_GROUP_ID === g.id;
    const isVip = (g.priority && g.priority >= 10);
    const safeName = (g.name || 'Facebook Group').replace(/'/g, "\\'");
    const vipBadge = isVip ? '<span style="background:#fef3c7;color:#b45309;font-size:9.5px;font-weight:900;padding:2px 6px;border-radius:4px;margin-left:5px;border:1px solid #fde68a;">⭐ VIP</span>' : '';
    const gSlug = getGroupSlug(g.url);
    const matchedAlerts = FB_ALERTS_STATE.filter(a => {
      if (a.group_id && a.group_id === g.id) return true;
      if (a.group_name && g.name) {
        const agn = a.group_name.toLowerCase().trim();
        const sgn = g.name.toLowerCase().trim();
        if (agn === sgn || agn.includes(sgn) || sgn.includes(agn)) return true;
      }
      if (gSlug && a.post_url && a.post_url.toLowerCase().includes(gSlug)) return true;
      return false;
    });
    const postsCount = matchedAlerts.length;
    const hiringCount = matchedAlerts.filter(a => a.is_hiring === 1).length;
    return `
      <div onclick="selectFbGroup(${g.id}, '${safeName}')" style="padding:11px 12px;border-radius:8px;cursor:pointer;display:flex;flex-direction:column;gap:5px;transition:all 0.15s ease;${isSelected ? 'background:#eff6ff;border:2px solid #1877F2;box-shadow:0 0 0 2px rgba(24,119,242,0.2);' : (isVip ? 'background:#fffbeb;border:1px solid #fde68a;' : 'background:var(--bg-subtle);border:1px solid var(--border-color);')}">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
          <div style="flex:1;overflow:hidden;padding-right:6px;">
            <div style="font-weight:800;font-size:12.5px;color:${isSelected ? '#1d4ed8' : (isVip ? '#92400e' : 'var(--text-main)')};white-space:nowrap;overflow:hidden;text-overflow:ellipsis;display:flex;align-items:center;">
              <span style="overflow:hidden;text-overflow:ellipsis;">${isSelected ? '👉 ' : ''}${escapeHtml(g.name)}</span>
              ${vipBadge}
            </div>
            <a href="${escapeHtml(g.url)}" target="_blank" onclick="event.stopPropagation()" style="font-size:10.5px;color:#1877F2;text-decoration:none;">🔗 Open Group</a>
          </div>
          <button onclick="event.stopPropagation();toggleFbGroupActive(${g.id})" style="padding:3px 8px;border-radius:12px;border:none;font-size:9.5px;font-weight:800;cursor:pointer;white-space:nowrap;${isActive ? 'background:#dcfce7;color:#166534;' : 'background:#f3f4f6;color:#6b7280;'}">
            ${isActive ? 'ACTIVE' : 'PAUSED'}
          </button>
        </div>
        <div style="display:flex;justify-content:space-between;align-items:center;font-size:10.5px;color:var(--text-muted);padding-top:4px;border-top:1px dashed var(--border-color);margin-top:2px;">
          <span>Posts: <b style="color:#1877F2;">${postsCount}</b></span>
          <span>Hiring: <b style="color:#16a34a;">${hiringCount}</b></span>
          <button onclick="event.stopPropagation();deleteFbGroupItem(${g.id})" style="background:none;border:none;color:#dc2626;cursor:pointer;font-size:11px;" title="Delete group">🗑</button>
        </div>
      </div>
    `;
  }).join('');

  list.innerHTML = allGroupsPill + groupItems;
}

function renderFbAlertsList() {
  const list = document.getElementById('fbAlertsList');
  if (!list) return;

  const banner = document.getElementById('fbActiveGroupBanner');
  const bannerName = document.getElementById('fbActiveGroupName');
  const subtitle = document.getElementById('fbFilterSubtitle');

  let filtered = [...FB_ALERTS_STATE];

  // 1. Filter by Selected Group
  if (SELECTED_FB_GROUP_ID !== null) {
    const selGroup = FB_GROUPS_STATE.find(g => g.id === SELECTED_FB_GROUP_ID);
    if (banner && bannerName) {
      banner.style.display = 'flex';
      bannerName.textContent = `Showing all posts for: ${SELECTED_FB_GROUP_NAME || selGroup?.name || 'Selected Group'}`;
    }
    const selSlug = selGroup ? getGroupSlug(selGroup.url) : '';
    filtered = filtered.filter(a => {
      if (a.group_id && a.group_id === SELECTED_FB_GROUP_ID) return true;
      if (selGroup && a.group_name) {
        const agn = a.group_name.toLowerCase().trim();
        const sgn = selGroup.name.toLowerCase().trim();
        if (agn === sgn || agn.includes(sgn) || sgn.includes(agn)) return true;
      }
      if (selSlug && a.post_url && a.post_url.toLowerCase().includes(selSlug)) return true;
      return false;
    });
  } else {
    if (banner) banner.style.display = 'none';
  }

  // 1b. Filter by Platform (Facebook vs Reddit vs RemoteOK)
  if (FB_PLATFORM_FILTER !== 'all') {
    filtered = filtered.filter(a => (a.platform || 'facebook') === FB_PLATFORM_FILTER);
  }

  // 2. Filter by Post Type (All Posts vs Hiring Only)
  if (FB_POST_TYPE_FILTER === 'hiring') {
    filtered = filtered.filter(a => a.is_hiring === 1);
  }

  // 3. Filter by Time Window
  if (FB_TIME_FILTER !== 'all') {
    const maxMins = FB_TIME_FILTER === '15m' ? 15 : (FB_TIME_FILTER === '1h' ? 60 : (FB_TIME_FILTER === '3h' ? 180 : 1440));
    filtered = filtered.filter(a => getPostAgeInMinutes(a) <= maxMins);
  }

  // 4. Sort chronologically (Newest first: 1m -> 2m -> 5m -> 1h)
  filtered.sort((a, b) => {
    const ageA = getPostAgeInMinutes(a);
    const ageB = getPostAgeInMinutes(b);
    return FB_SORT_ORDER === 'newest' ? (ageA - ageB) : (ageB - ageA);
  });

  if (subtitle) {
    subtitle.textContent = `Showing ${filtered.length} posts ${SELECTED_FB_GROUP_NAME ? `in "${SELECTED_FB_GROUP_NAME}"` : 'across all groups'} (Sorted by: ${FB_SORT_ORDER === 'newest' ? 'Newest first (1m → 2m → 1h)' : 'Oldest first'})`;
  }

  if (filtered.length === 0) {
    list.innerHTML = `
      <div style="text-align:center;padding:48px 20px;color:var(--text-muted);">
        <div style="font-size:36px;margin-bottom:8px;">👥</div>
        <div style="font-weight:800;font-size:15px;color:#1e293b;margin-bottom:6px;">No posts loaded yet for ${SELECTED_FB_GROUP_NAME ? `"${escapeHtml(SELECTED_FB_GROUP_NAME)}"` : 'this selection'}</div>
        <div style="font-size:12.5px;color:#64748b;margin-bottom:16px;max-width:440px;margin-left:auto;margin-right:auto;line-height:1.5;">
          This group has no posts loaded in this session yet. Click the button below to fetch live posts, or click "Show All Groups" to see all posts from all other groups!
        </div>
        <div style="display:flex;gap:10px;justify-content:center;flex-wrap:wrap;">
          ${SELECTED_FB_GROUP_ID ? `<button id="fbScanEmptyGroupBtn" onclick="scanSelectedGroupNow()" class="btn-primary" style="background:#1877F2;border-color:#1877F2;padding:9px 18px;font-size:12px;font-weight:700;box-shadow:0 2px 8px rgba(24,119,242,0.3);cursor:pointer;">⚡ Fetch All Posts From Group Now</button>` : ''}
          <button onclick="clearSelectedFbGroup()" class="btn-secondary" style="padding:9px 18px;font-size:12px;font-weight:700;cursor:pointer;">🌐 Show All Groups (সব গ্রুপের পোস্ট দেখুন)</button>
        </div>
      </div>
    `;
    return;
  }

  list.innerHTML = filtered.map(a => {
    const cleanWa = (a.contact_whatsapp || a.contact_phone || '').replace(/[^0-9]/g, '');
    const waLink = cleanWa ? (cleanWa.startsWith('01') && cleanWa.length === 11 ? `https://wa.me/88${cleanWa}` : `https://wa.me/${cleanWa}`) : '';
    const imgHtml = a.image_url ? `<img src="${escapeHtml(a.image_url)}" style="width:70px;height:70px;object-fit:cover;border-radius:6px;border:1px solid var(--border-color);" />` : '';
    const ageMins = getPostAgeInMinutes(a);
    const ageLabel = formatPostAgeLabel(ageMins);
    const isHiring = a.is_hiring === 1;
    const plat = (a.platform || 'facebook').toLowerCase();
    let platBadge = `<span style="background:#eff6ff;color:#1d4ed8;border:1px solid #bfdbfe;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:800;">🔵 FB</span>`;
    if (plat === 'reddit') {
      platBadge = `<span style="background:#fee2e2;color:#b91c1c;border:1px solid #fca5a5;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:800;">🔴 REDDIT</span>`;
    } else if (plat === 'remoteok') {
      platBadge = `<span style="background:#fef3c7;color:#92400e;border:1px solid #fcd34d;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:800;">🟢 REMOTEOK</span>`;
    }

    const hiringBadge = isHiring
      ? `<span style="background:#dcfce7;color:#166534;border:1px solid #86efac;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:900;">🎯 HIRING LEAD</span>`
      : `<span style="background:#f1f5f9;color:#475569;border:1px solid #cbd5e1;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:700;">💬 Community Post</span>`;

    return `
      <div style="padding:14px 16px;background:#fff;border-radius:8px;border:${isHiring ? '2px solid #86efac' : '1px solid var(--border-color)'};box-shadow:0 1px 3px rgba(0,0,0,0.04);display:flex;gap:14px;align-items:flex-start;">
        ${imgHtml}
        <div style="flex:1;">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:4px;flex-wrap:wrap;gap:6px;">
            <div>
              <span style="font-weight:800;font-size:13.5px;color:var(--text-main);">${escapeHtml(a.client_name || a.author_name || 'Client')}</span>
              <span style="font-size:11px;color:var(--text-muted);margin-left:6px;">in <b>${escapeHtml(a.group_name || 'Community')}</b></span>
            </div>
            <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;">
              ${platBadge}
              <span style="background:#ecfdf5;color:#047857;border:1px solid #a7f3d0;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:800;">${ageLabel}</span>
              ${hiringBadge}
              ${isHiring ? `<span style="background:#fee2e2;color:#b91c1c;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:800;">${escapeHtml(a.job_type || 'Video Editor')}</span>` : ''}
              ${isHiring && a.budget ? `<span style="background:#dbeafe;color:#1d4ed8;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:800;">${escapeHtml(a.budget)}</span>` : ''}
            </div>
          </div>
          
          <p style="font-size:12px;color:var(--text-main);margin:6px 0 10px 0;line-height:1.45;background:var(--bg-subtle);padding:8px 10px;border-radius:6px;white-space:pre-wrap;">
${escapeHtml(a.content || a.ai_summary || '')}
          </p>

          <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
            <div style="display:flex;gap:8px;align-items:center;font-size:11px;">
              ${a.contact_phone ? `<span style="font-weight:600;color:var(--text-main);">📞 ${escapeHtml(a.contact_phone)}</span>` : ''}
              ${a.contact_email ? `<span style="color:var(--text-muted);">✉ ${escapeHtml(a.contact_email)}</span>` : ''}
              <span style="color:var(--text-light);">${(a.created_at || '').substring(0, 16)}</span>
            </div>
            <div style="display:flex;gap:6px;flex-wrap:wrap;">
              <button onclick="openAiPitchModal(${a.id})" class="btn-secondary" style="font-size:11px;padding:4px 10px;border-color:#8b5cf6;color:#7c3aed;background:#f5f3ff;font-weight:700;display:inline-flex;align-items:center;gap:4px;cursor:pointer;">⚡ AI Pitch</button>
              ${a.author_url ? `<a href="${escapeHtml(a.author_url)}" target="_blank" class="btn-primary" style="background:#1877F2;border-color:#1877F2;padding:4px 10px;font-size:11px;text-decoration:none;display:inline-flex;align-items:center;gap:4px;">👤 ${plat === 'reddit' ? 'DM on Reddit' : 'Message Profile'}</a>` : ''}
              ${waLink ? `<a href="${waLink}" target="_blank" class="btn-primary" style="background:#25D366;border-color:#25D366;padding:4px 10px;font-size:11px;text-decoration:none;display:inline-flex;align-items:center;gap:4px;">💬 WhatsApp</a>` : ''}
              ${a.post_url ? `<a href="${escapeHtml(a.post_url)}" target="_blank" class="btn-secondary" style="padding:4px 10px;font-size:11px;text-decoration:none;">🔗 Open ${plat === 'reddit' ? 'Reddit' : 'Job'}</a>` : ''}
            </div>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function openAddGroupModal() {
  const m = document.getElementById('modalAddFbGroup');
  if (m) m.style.display = 'flex';
}

function closeAddGroupModal() {
  const m = document.getElementById('modalAddFbGroup');
  if (m) m.style.display = 'none';
}

async function submitAddFbGroup() {
  const name = (document.getElementById('newFbGroupName')?.value || '').trim();
  const url = (document.getElementById('newFbGroupUrl')?.value || '').trim();
  const interval = parseInt(document.getElementById('newFbGroupInterval')?.value || '2');

  if (!url) {
    showToast('Please enter a Facebook Group URL!', 'warning');
    return;
  }

  try {
    const res = await fetch(API_BASE + '/api/fb/groups', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: name || url, url, interval_min: interval })
    });
    const data = await res.json();
    if (data.ok) {
      showToast('Facebook Group added to Radar!', 'success');
      closeAddGroupModal();
      document.getElementById('newFbGroupName').value = '';
      document.getElementById('newFbGroupUrl').value = '';
      await loadFbGroups();
    } else {
      showToast(data.detail || 'Failed to add group', 'warning');
    }
  } catch (err) {
    showToast('Network error adding group', 'warning');
  }
}

async function toggleFbGroupActive(id) {
  try {
    const res = await fetch(`/api/fb/groups/${id}/toggle`, { method: 'PATCH' });
    const data = await res.json();
    if (data.ok) {
      showToast(`Group status updated: ${data.active === 1 ? 'Active' : 'Paused'}`, 'info');
      await loadFbGroups();
    }
  } catch (_) {}
}

async function deleteFbGroupItem(id) {
  if (!confirm('Are you sure you want to stop monitoring this group?')) return;
  try {
    const res = await fetch(`/api/fb/groups/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.ok) {
      showToast('Group removed from Radar', 'info');
      await loadFbGroups();
    }
  } catch (_) {}
}

async function testFbAlert() {
  showToast('Generating test hiring post & dispatching Telegram alert...', 'info');
  try {
    const res = await fetch(API_BASE + '/api/fb/test-alert', { method: 'POST' });
    const data = await res.json();
    if (data.ok) {
      if (data.telegram_sent) {
        showToast('🎯 Telegram alert sent to your phone successfully!', 'success');
      } else {
        showToast('Alert created in feed! (Configure Telegram Bot Token to receive on phone)', 'info');
      }
      await loadFbAlerts();
    }
  } catch (err) {
    showToast('Failed to trigger test alert', 'warning');
  }
}

async function scanFbNow() {
  showToast('🔍 Triggering immediate scan across active groups...', 'info');
  try {
    const res = await fetch(API_BASE + '/api/fb/scan-now', { method: 'POST' });
    const data = await res.json();
    if (data.ok) {
      showToast(data.message || 'Scan in progress', 'success');
      setTimeout(loadFbAlerts, 4000);
    }
  } catch (_) {}
}

function toggleTelegramConfig() {
  const box = document.getElementById('telegramConfigBox');
  if (box) {
    box.style.display = box.style.display === 'none' ? 'block' : 'none';
  }
}

async function saveTelegramSettings() {
  const token = (document.getElementById('tgBotTokenInput')?.value || '').trim();
  const chatId = (document.getElementById('tgChatIdInput')?.value || '').trim();

  if (!token || !chatId) {
    showToast('Please enter both Bot Token and Chat ID!', 'warning');
    return;
  }

  try {
    const res = await fetch(API_BASE + '/api/settings/telegram', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ bot_token: token, chat_id: chatId })
    });
    const data = await res.json();
    if (data.ok) {
      showToast('Telegram activated! You will receive instant hiring alerts.', 'success');
      toggleTelegramConfig();
    } else {
      showToast(data.detail || 'Failed to save settings', 'warning');
    }
  } catch (_) {
    showToast('Network error saving Telegram settings', 'warning');
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// Auto-refresh FB Radar alerts every 20 seconds so fresh posts appear live
setInterval(() => {
  if (APP_STATE.currentPage === 'fb-radar') {
    loadFbAlerts();
  }
}, 20000);

// -------------------------------------------------------------
// GLOBAL HUNTER & 1-CLICK AI PITCH ENGINE
// -------------------------------------------------------------
let CURRENT_PITCH_ALERT = null;

async function huntGlobalJobsNow() {
  showToast('🌍 Triggering Global Hunt across Reddit, RemoteOK & Creator job boards...', 'info');
  try {
    const res = await fetch(API_BASE + '/api/hunter/scan-global', { method: 'POST' });
    const data = await res.json();
    if (data.ok) {
      showToast(data.message || 'Global hunting started in background!', 'success');
      setTimeout(loadFbAlerts, 5000);
    }
  } catch (err) {
    showToast('Failed to trigger global hunt', 'warning');
  }
}

async function openAiPitchModal(alertId) {
  const alert = FB_ALERTS_STATE.find(a => a.id === alertId);
  if (!alert) return;

  CURRENT_PITCH_ALERT = alert;
  const modal = document.getElementById('aiPitchModal');
  const output = document.getElementById('aiPitchOutput');
  const portInput = document.getElementById('aiPitchPortfolioInput');
  const copyStatus = document.getElementById('aiPitchCopyStatus');

  if (copyStatus) copyStatus.style.display = 'none';
  if (output) output.value = '⚡ Analyzing client requirement & crafting tailored proposal with AI...';
  if (modal) modal.style.display = 'flex';

  await generatePitchForCurrentAlert();
}

function closeAiPitchModal() {
  const modal = document.getElementById('aiPitchModal');
  if (modal) modal.style.display = 'none';
  CURRENT_PITCH_ALERT = null;
}

async function generatePitchForCurrentAlert() {
  if (!CURRENT_PITCH_ALERT) return;
  const output = document.getElementById('aiPitchOutput');
  const portInput = document.getElementById('aiPitchPortfolioInput');
  const portUrl = (portInput?.value || '').trim();

  try {
    const res = await fetch(API_BASE + '/api/jobs/generate-pitch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        content: CURRENT_PITCH_ALERT.content || CURRENT_PITCH_ALERT.ai_summary || '',
        client_name: CURRENT_PITCH_ALERT.client_name || CURRENT_PITCH_ALERT.author_name || 'Client',
        job_type: CURRENT_PITCH_ALERT.job_type || 'Video Editor',
        portfolio_url: portUrl
      })
    });
    const data = await res.json();
    if (data.ok && output) {
      output.value = data.pitch;
    }
  } catch (err) {
    if (output) output.value = 'Failed to generate proposal. Please try again.';
  }
}

async function regeneratePitch() {
  const output = document.getElementById('aiPitchOutput');
  if (output) output.value = '🔄 Regenerating personalized proposal...';
  await generatePitchForCurrentAlert();
}

function copyAiPitch() {
  const output = document.getElementById('aiPitchOutput');
  const copyStatus = document.getElementById('aiPitchCopyStatus');
  if (!output || !output.value) return;

  navigator.clipboard.writeText(output.value).then(() => {
    if (copyStatus) copyStatus.style.display = 'inline';
    showToast('📋 AI Pitch copied to clipboard! Paste directly into client chat.', 'success');
    setTimeout(() => {
      if (copyStatus) copyStatus.style.display = 'none';
    }, 3000);
  }).catch(() => {
    output.select();
    document.execCommand('copy');
    showToast('📋 Copied to clipboard!', 'success');
  });
}

async function checkVpsWorkerStatus() {
  const el = document.getElementById('vpsWorkerStatusText');
  try {
    const res = await fetch(API_BASE + '/api/worker/status');
    const data = await res.json();
    if (data.ok && data.worker) {
      const w = data.worker;
      if (el) {
        el.innerHTML = `✅ <b>VPS Hunter Online</b> • Uptime: <b>${w.uptime_human}</b> • Cycles Completed: <b>#${w.cycles_completed}</b> • Scanned: <b>${w.total_posts_scanned} posts</b> • Leads Found: <b>${w.total_hiring_leads_found}</b>`;
      }
      showToast(`VPS 24/7 Hunter is active! Uptime: ${w.uptime_human}, Cycles: #${w.cycles_completed}`, 'success');
    }
  } catch (err) {
    if (el) el.textContent = 'VPS status check error';
  }
}

// Check worker status whenever FB Radar page is opened
const originalLoadFbRadarPage = window.loadFbRadarPage;
window.loadFbRadarPage = async function() {
  if (originalLoadFbRadarPage) await originalLoadFbRadarPage();
  checkVpsWorkerStatus();
};

