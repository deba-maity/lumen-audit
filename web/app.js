'use strict';

const $ = (selector, root = document) => root.querySelector(selector);
const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[c]));
const e = escapeHTML;
const icons = {
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.4 1.4m11.2 11.2L19 19M5 19l1.4-1.4M17.6 6.4 19 5"/>',
  grid: '<rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/>',
  folder: '<path d="M3 7a2 2 0 0 1 2-2h5l2 2h7a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z"/><path d="M3 11h18"/>',
  layers: '<path d="m12 3 10 5-10 5L2 8Zm-10 9 10 5 10-5M2 16l10 5 10-5"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  circlecheck: '<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',
  copy: '<rect x="8" y="8" width="13" height="13" rx="2"/><path d="M16 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h3"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  spark: '<path d="m12 3 2.4 6.6L21 12l-6.6 2.4L12 21l-2.4-6.6L3 12l6.6-2.4ZM20 2v4m-2-2h4"/>',
  shield: '<path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6Z"/><path d="m8 12 3 3 5-6"/>',
  arrow: '<path d="M5 12h14m-5-5 5 5-5 5"/>',
  chevron: '<path d="m9 5 7 7-7 7"/>',
  down: '<path d="m6 9 6 6 6-6"/>',
  search: '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>',
  download: '<path d="M12 3v12m-5-5 5 5 5-5M4 16v4h16v-4"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  close: '<path d="m6 6 12 12M6 18 18 6"/>',
  drive: '<rect x="3" y="4" width="18" height="16" rx="3"/><path d="M3 14h18M7 17h.01M11 17h.01"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10h.01"/>',
  external: '<path d="M14 3h7v7m0-7L10 14M10 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-5"/>',
  file: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Zm0 0v6h6M8 13h8M8 17h5"/>',
  image: '<rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="8" cy="8" r="1"/><path d="m3 16 5-5 5 5 3-3 5 5"/>',
  video: '<rect x="3" y="3" width="18" height="18" rx="3"/><path d="m10 8 6 4-6 4Z"/>',
  code: '<path d="m8 6-6 6 6 6m8-12 6 6-6 6M14 3l-4 18"/>',
  box: '<path d="m12 3 9 5v9l-9 5-9-5V8Zm0 9v10M3 8l9 4 9-4M7 5l9 5"/>',
  refresh: '<path d="M20 7v5h-5M4 17v-5h5"/><path d="M6 6a8 8 0 0 1 13 2l1 4M4 12l1 4a8 8 0 0 0 13 2"/>',
  send: '<path d="m22 2-7 20-4-9-9-4Zm0 0L11 13"/>',
  menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
  leaf: '<path d="M20 3c-9 0-16 3-16 10a7 7 0 0 0 7 7c7 0 9-8 9-17ZM4 20 16 8"/>',
  monitor: '<rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8m-4-4v4"/>',
};
function icon(name, cls = '') { return `<svg class="icon ${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${icons[name] || icons.file}</svg>`; }
function bytes(value, decimals = 1) {
  if (!Number.isFinite(value)) return '—';
  if (value === 0) return '0 B';
  const index = Math.min(4, Math.floor(Math.log(Math.abs(value)) / Math.log(1024)));
  return `${(value / 1024 ** index).toLocaleString(undefined, {maximumFractionDigits: index ? decimals : 0})} ${['B','KiB','MiB','GiB','TiB'][index]}`;
}
const number = value => Number(value || 0).toLocaleString();
const date = value => Number.isFinite(value) && Number.isFinite(new Date(value * 1000).getTime()) ? new Date(value * 1000).toLocaleDateString(undefined, {month:'short', day:'numeric', year:'numeric'}) : 'Unknown';
const dateTime = value => Number.isFinite(value) && Number.isFinite(new Date(value * 1000).getTime()) ? new Date(value * 1000).toLocaleString(undefined, {dateStyle:'medium', timeStyle:'short'}) : 'Unknown';
const categoryColors = {'Video & audio':'#779080', 'Archives & installers':'#d4a785', 'Development':'#a0b6a6', 'Images':'#d5c78e', 'Documents':'#99aab4', 'Other':'#c8cac0'};
const categoryIcons = {'Video & audio':'video', 'Archives & installers':'box', 'Development':'code', 'Images':'image', 'Documents':'file', 'Other':'file'};
const kindLabels = {duplicates:'Duplicate files', generated:'Project leftovers', installers:'Older installers', large:'Large files'};
const state = {
  config:null, report:null, history:[], page:'overview', query:'', category:'all', folder:'', reviewKind:'all', showKept:false, reviewPage:1, duplicatePage:1,
  sort:'size', pageNumber:1, model:'', models:[], messages:[], draft:'', asking:false, scan:null, comparison:null, beforeId:'', mobileNav:false, decisions:{},
};
let reportEpoch = 0;
let loadEpoch = 0;
const sortedInventories = new WeakMap();
function decisionKey() { return 'lumen-decisions-v2-' + state.report.id; }
function readDecisions() {
  try {
    const value = JSON.parse(localStorage.getItem(decisionKey()) || '{}');
    state.decisions = value && typeof value === 'object' && !Array.isArray(value) ? Object.fromEntries(Object.entries(value).filter(([key,value])=>/^[a-zA-Z0-9-]+$/.test(key) && ['keep','review'].includes(value))) : {};
  } catch { state.decisions = {}; }
}
function inventoryInOrder() {
  let cache = sortedInventories.get(state.report);
  if (!cache) { cache = new Map(); sortedInventories.set(state.report, cache); }
  if (!cache.has(state.sort)) cache.set(state.sort, [...state.report.files].sort((a,b)=>state.sort==='name'?a.name.localeCompare(b.name):state.sort==='modified'?b.modified-a.modified:state.sort==='oldest'?a.modified-b.modified:b.size-a.size));
  return cache.get(state.sort);
}
function pager(total, page, size, action) {
  const pages=Math.max(1,Math.ceil(total/size));
  return `<div class="pagination"><span>${number(total)} items · page ${page} of ${pages}</span><div><button class="button small secondary" data-action="${action}" data-direction="-1" ${page===1?'disabled':''}>Previous</button><button class="button small secondary" data-action="${action}" data-direction="1" ${page===pages?'disabled':''}>Next</button></div></div>`;
}

async function api(path, body, raw=false) {
  if (window.lumenPagesApi) return window.lumenPagesApi(path, body, raw);
  const controller = new AbortController();
  const timeout = setTimeout(()=>controller.abort(), 30000);
  try {
    const response = await fetch(path, {signal:controller.signal, method:body===undefined?'GET':'POST', headers:{'X-Lumen-Token':state.config?.token || '', ...(body===undefined?{}:{'Content-Type':'application/json'})}, ...(body===undefined?{}:{body:JSON.stringify(body)})});
    if(!response.ok) {
      let message='Request failed. Is Lumen still running?';
      try {message=(await response.json()).error || message;} catch(error) {if(error.name==='AbortError')throw error;}
      throw new Error(message);
    }
    return raw ? await response.blob() : await response.json();
  } catch(error) {
    if(error.name==='AbortError')throw new Error('The local server took too long to respond. Try again.');
    if(error instanceof TypeError)throw new Error('Could not reach Lumen. Check that the local server is running.');
    throw error;
  } finally { clearTimeout(timeout); }
}
let toastTimer;
function toast(message, error=false) { const node = $('#toast'); node.textContent = message; node.className = `visible ${error ? 'error' : ''}`; clearTimeout(toastTimer); toastTimer = setTimeout(() => node.className = '', 6500); }
function run(promise) { Promise.resolve(promise).catch(error => toast(error.message || 'Something went wrong.', true)); }

function navItem(page, name, glyph, count) { return `<button class="nav-item ${state.page === page ? 'active' : ''}" data-action="navigate" data-page="${page}" ${state.page === page ? 'aria-current="page"' : ''}>${icon(glyph)}<span>${name}</span>${count !== undefined ? `<span class="nav-count">${count}</span>` : ''}</button>`; }
function shell() {
  const r = state.report;
  const titles = {overview:'Overview', explorer:'Storage explorer', review:'Review queue', duplicates:'Duplicate files', history:'Snapshots & changes', apps:'Applications', assistant:'Ask Lumen'};
  $('#app').innerHTML = `
  <aside id="sidebar" class="sidebar ${state.mobileNav ? 'open' : ''}">
    <button class="brand" data-action="navigate" data-page="overview" aria-label="Lumen home"><span class="brand-symbol">${icon('sun')}</span><span>lumen<span class="brand-period">.</span></span></button>
    <div class="sidebar-label">YOUR WORKSPACE</div><nav aria-label="Main navigation">
      ${navItem('overview','Overview','grid')}${navItem('explorer','Storage explorer','folder')}${navItem('review','Review queue','circlecheck',r.findings.length)}${navItem('duplicates','Duplicates','copy')}${navItem('history','Snapshots','clock')}${navItem('apps','Applications','monitor')}
      <div class="nav-divider"></div>${navItem('assistant','Ask Lumen','spark')}<span class="nav-hint">A little help making sense of it.</span>
    </nav>
    <div class="sidebar-bottom"><div class="local-note"><span class="status-dot"></span><strong>Local by design</strong><p>Your files stay in your world.</p>${state.config.hosted_demo ? `<a class="text-link" href="./lumen-audit.zip" download>Download the local app ${icon("download")}</a>` : ""}<button class="text-link" data-action="privacy">How Lumen works ${icon('arrow')}</button></div><div class="device"><span class="device-icon">${icon('monitor')}</span><div><strong>${r.demo ? 'Demo workspace' : 'This computer'}</strong><span>${state.config.demo_only ? 'Scans disabled · read-only' : 'Read-only · localhost'}</span></div></div></div>
  </aside>
  <div class="workspace"><header class="topbar"><div class="breadcrumb"><button class="icon-button mobile-toggle" data-action="mobile-nav" aria-label="Toggle navigation" aria-controls="sidebar" aria-expanded="${state.mobileNav}">${icon('menu')}</button><span>Workspace</span>${icon('chevron')}<strong>${titles[state.page]}</strong></div><div class="topbar-actions"><button class="search-trigger" data-action="search">${icon('search')}<span>Find a file</span><kbd>/</kbd></button><span class="readonly">${icon('shield')} Read-only</span><button class="avatar" data-action="privacy" aria-label="About your local workspace">L</button></div></header>
    <main id="main" tabindex="-1"><div class="mode-banner ${r.demo ? '' : 'live'}"><span>${icon(r.demo ? 'leaf' : 'shield')} ${r.demo ? '<strong>A little look around.</strong> This view uses fictional data. Opening it does not scan your computer.' : `<strong>Local snapshot.</strong> ${e(dateTime(r.created))} · ${number(r.files.length)} files in the selected scope.`}</span><button data-action="scan" class="banner-link">${state.config.demo_only ? 'About demo mode' : 'Scan my folders'} ${icon('arrow')}</button></div>
    <div id="scan-progress"></div><div id="page-content">${pageContent()}</div>
    <footer class="page-footer"><span>${icon('leaf')} Made for a little more breathing room.</span><span>Nothing moved. Nothing deleted.</span></footer></main>
  </div>`;
  renderProgress();
}
function heading(eyebrow, title, subtitle, actions='') { return `<div class="page-heading"><div><div class="eyebrow">${eyebrow}</div><h1>${title}</h1><p>${subtitle}</p></div><div class="heading-actions">${actions}</div></div>`; }
function exportButton() { return `<button class="button secondary" data-action="export">${icon('download')} Export report</button>`; }
function scanButton() { return `<button class="button primary" data-action="scan">${icon('plus')} New scan</button>`; }
function pageContent() { return ({overview:overview, explorer:explorer, review:review, duplicates:duplicates, history:history, apps:apps, assistant:assistant})[state.page](); }
function updatePage() { $('#page-content').innerHTML = pageContent(); }
function empty(title, text, glyph='leaf', button='') { return `<div class="empty-state"><div>${icon(glyph)}</div><h3>${title}</h3><p>${text}</p>${button}</div>`; }

function overview() {
  const r = state.report, s = r.summary;
  const top = r.findings.slice(0,4);
  return `${heading('A FRESH PERSPECTIVE', 'A little clarity. A lighter laptop.', 'Understand what’s here, what it does, and what deserves a second look.', exportButton()+scanButton())}
  <section class="hero-card"><div class="hero-copy"><span class="pill hero-pill"><span class="status-dot"></span> ${r.demo ? 'FICTIONAL SNAPSHOT' : 'SNAPSHOT READY'}</span><h2>Make room for<br>what’s next<span>.</span></h2><p>Your storage has a story. Let’s untangle it.<br> Lumen found <strong>${number(s.findings)} things worth reviewing</strong>—<br>you decide what stays.</p><button class="button hero-button" data-action="navigate" data-page="review">Explore your review queue ${icon('arrow')}</button><span class="hero-footnote">${icon('shield')} An observer, never a cleaner.</span></div><div class="storage-orbit"><div class="orbit-label">THE BIG PICTURE <span>01 / STORAGE</span></div>${storageRing()}<div class="orbit-caption"><span class="tiny-dot"></span> Every byte has a place.</div></div></section>
  <div class="stats-grid"><article class="stat-card"><div class="stat-label">Storage in this snapshot ${icon('drive')}</div><strong>${bytes(s.bytes)}</strong><div><span class="small-dot green"></span>${number(s.files)} files · logical size</div></article><article class="stat-card"><div class="stat-label">Space worth reviewing ${icon('layers')}</div><strong>${bytes(s.review_bytes)}<span class="stat-tag">${s.findings} findings</span></strong><div>Potential candidates, not promised savings</div></article><article class="stat-card"><div class="stat-label">Matching extra copies ${icon('copy')}</div><strong>${r.coverage.hashing ? bytes(s.duplicate_bytes) : 'Not checked'}</strong><div>${r.coverage.hashing ? `${r.duplicates.length} content-matched groups · review locations` : 'Enable hashing when starting a scan'}</div></article></div>
  <div class="overview-grid"><section class="panel"><div class="panel-heading"><div><h2>A place for everything</h2><p>Where your selected storage lives.</p></div><button class="text-link" data-action="navigate" data-page="explorer">Explore ${icon('arrow')}</button></div>${storageMosaic()}<div class="category-legend">${s.categories.map(cat=>`<button data-action="category" data-category="${e(cat.name)}"><span style="--dot:${categoryColors[cat.name]}" class="legend-dot"></span>${e(cat.name)}<strong>${bytes(cat.bytes)}</strong></button>`).join('')}</div></section>
  <section class="panel gentle-panel"><div class="panel-heading"><div><h2>Clarity, with context.</h2><p>A finding is a starting point.</p></div>${icon('spark')}</div><div class="insight-illustration" aria-hidden="true"><span class="paper paper-back"></span><span class="paper paper-front">${icon('leaf')}<i></i><i></i><i></i></span><span class="illustration-check">${icon('check')}</span></div><h3>“Can I actually remove this?”</h3><p>Lumen explains what an item likely does and what removal could affect. You get the evidence, not a risky green light.</p><button class="button secondary" data-action="ask-prompt" data-question="What should I review first?">Ask about this snapshot ${icon('arrow')}</button></section></div>
  <section class="panel findings-preview"><div class="panel-heading"><div><h2>A few things worth a look <span class="count-badge">${r.findings.length}</span></h2><p>Biggest review candidates first. Nothing is selected for deletion.</p></div><button class="text-link" data-action="navigate" data-page="review">View all ${icon('arrow')}</button></div>${top.length ? `<div class="finding-list">${top.map(findingRow).join('')}</div>` : empty('Nothing to flag here', 'There are no review candidates within the scanned scope.')}</section>
  <button class="coverage-strip" data-action="coverage"><span>${icon('info')} <strong>Know the boundaries.</strong> ${number(r.coverage.skipped)} items skipped · Last-opened times are unknown${r.coverage.limited ? ' · Partial inventory' : ''}</span><span>View scan coverage ${icon('arrow')}</span></button>`;
}
function storageRing() {
  const s = state.report.summary;
  let offset=0;
  const segments = s.categories.map(cat=>{const fraction = s.bytes ? cat.bytes/s.bytes : 0; const length = Math.max(0,fraction*565.49-5); const result=`<circle cx="130" cy="130" r="90" fill="none" stroke="${categoryColors[cat.name]}" stroke-width="33" stroke-dasharray="${length} ${565.49-length}" stroke-dashoffset="${-offset}" transform="rotate(-90 130 130)"/>`; offset+=fraction*565.49; return result;}).join('');
  return `<div class="ring-wrap"><svg viewBox="0 0 260 260" role="img" aria-label="Storage by category: ${e(s.categories.map(c=>c.name+' '+bytes(c.bytes)).join(', '))}"><circle cx="130" cy="130" r="115" fill="none" stroke="#d6dfcf" stroke-width="1" stroke-dasharray="2 6"/><circle cx="130" cy="130" r="90" fill="none" stroke="#e4eadc" stroke-width="33"/>${segments}<circle cx="130" cy="130" r="65" fill="none" stroke="#dbe3d4" stroke-width="1"/></svg><div class="ring-center">${icon('folder')}<strong>${bytes(s.bytes)}</strong><span>in this snapshot</span></div><span class="orbit-dot dot-one"></span><span class="orbit-dot dot-two"></span></div>`;
}
function storageMosaic() {
  const categories = state.report.summary.categories.filter(item=>item.bytes>0);
  const rectangles=[];
  function split(items,x,y,width,height) {
    if(!items.length)return;
    if(items.length===1){rectangles.push({...items[0],x,y,width,height});return;}
    const total=items.reduce((sum,item)=>sum+item.bytes,0);
    let pivot=1,sum=items[0].bytes;
    while(pivot<items.length-1 && sum+items[pivot].bytes<total/2){sum+=items[pivot++].bytes;}
    const fraction=sum/total;
    if(width>=height){split(items.slice(0,pivot),x,y,width*fraction,height);split(items.slice(pivot),x+width*fraction,y,width*(1-fraction),height);}
    else {split(items.slice(0,pivot),x,y,width,height*fraction);split(items.slice(pivot),x,y+height*fraction,width,height*(1-fraction));}
  }
  split(categories,0,0,100,45);
  return `<div class="storage-mosaic proportional-map" aria-label="Storage category map, area proportional to logical size">${rectangles.map(cat=>`<button class="mosaic-tile ${cat.width<15||cat.height<10?'tiny-tile':''}" style="--tile:${categoryColors[cat.name]};left:${cat.x}%;top:${cat.y/45*100}%;width:calc(${cat.width}% - 4px);height:calc(${cat.height/45*100}% - 4px)" data-action="category" data-category="${e(cat.name)}" aria-label="${e(cat.name)}: ${bytes(cat.bytes)}" title="${e(cat.name)}: ${bytes(cat.bytes)}">${icon(categoryIcons[cat.name])}<span>${e(cat.name)}</span><strong>${bytes(cat.bytes)}</strong></button>`).join('') || '<span class="map-empty">No file bytes in this snapshot.</span>'}</div>`;
}
function findingRow(item) {
  const glyph = {duplicates:'copy',generated:'code',installers:'box',large:'file'}[item.kind];
  return `<button class="finding-row" data-action="finding" data-id="${e(item.id)}"><span class="item-icon ${item.kind}">${icon(glyph)}</span><span class="finding-main"><strong>${e(item.title)}</strong><span class="truncate">${e(item.path)}</span></span><span class="finding-label">${e(item.confidence)}</span><span class="finding-size">${bytes(item.bytes)}</span>${icon('chevron')}</button>`;
}

const folderSummaries = new WeakMap();
function folderSummary() {
  let result=folderSummaries.get(state.report);
  if(!result){const map=new Map();for(const file of state.report.files){const key=JSON.stringify([file.root,file.folder]);const item=map.get(key)||{key,root:file.root,name:file.folder,bytes:0,count:0};item.bytes+=file.size;item.count++;map.set(key,item);}result=[...map.values()].sort((a,b)=>b.bytes-a.bytes);folderSummaries.set(state.report,result);}
  return result;
}
function folderCards() {
  return `<div class="folder-cards">${folderSummary().slice(0,8).map(item=>`<button data-action="folder" data-folder="${e(item.key)}" title="${e(item.root)}"><span>${icon('folder')}<strong>${e(item.name)}</strong></span><small>${e(item.root)}</small><div><b>${bytes(item.bytes)}</b><span>${number(item.count)} files</span></div></button>`).join('')}</div>`;
}
function explorer() {
  const r = state.report;
  return `${heading('GET THE LAY OF THE LAND', 'Everything, in perspective.', 'Browse the inventory. File contents stay unopened unless you choose duplicate hashing.', exportButton())}
  <section class="panel storage-panel"><div class="panel-heading"><h2>Storage by category</h2><span class="muted">${bytes(r.summary.bytes)} inventoried</span></div>${storageMosaic()}<div class="panel-heading"><div><h2>Largest folders in this scope</h2><p>Click a folder to narrow the inventory. Showing up to eight.</p></div></div>${folderCards()}</section>
  <section class="panel"><div class="explorer-controls"><label class="input-search">${icon('search')}<input id="file-search" type="search" placeholder="Search filenames or paths…" value="${e(state.query)}" aria-label="Search inventory"></label><select id="category-select" aria-label="Filter category"><option value="all">All categories</option>${r.summary.categories.map(c=>`<option value="${e(c.name)}" ${state.category===c.name?'selected':''}>${e(c.name)}</option>`).join('')}</select><select id="file-sort" aria-label="Sort files"><option value="size" ${state.sort==='size'?'selected':''}>Largest first</option><option value="name" ${state.sort==='name'?'selected':''}>Name A–Z</option><option value="modified" ${state.sort==='modified'?'selected':''}>Recently modified</option><option value="oldest" ${state.sort==='oldest'?'selected':''}>Oldest modified</option></select></div>
  ${state.folder ? `<div class="active-filter">Folder: ${e(JSON.parse(state.folder).join(' / '))} <button class="text-link" data-action="clear-folder">Clear ${icon('close')}</button></div>` : ''}
  <div id="file-results">${fileResults()}</div></section><p class="help-text">${icon('info')} “Modified” describes a content change, not the last time you opened a file. Sizes are logical bytes, not allocated disk space.</p>`;
}
function fileResults() {
  const query = state.query.toLowerCase();
  const filtered = inventoryInOrder().filter(file=>(state.category==='all'||file.category===state.category)&&(!state.folder||JSON.stringify([file.root,file.folder])===state.folder)&&(!query||file.path.toLowerCase().includes(query)));
  const pages=Math.max(1,Math.ceil(filtered.length/40)); state.pageNumber=Math.min(state.pageNumber,pages);
  const files=filtered.slice((state.pageNumber-1)*40,state.pageNumber*40);
  if(!files.length) return empty('No files in this view', 'Try another search or clear the category filter.', 'search', '<button class="button secondary" data-action="reset-filters">Clear filters</button>');
  return `<div class="table-scroll"><table class="file-table"><thead><tr><th>FILE / LOCATION</th><th>CATEGORY</th><th>MODIFIED</th><th class="align-right">SIZE</th><th><span class="sr-only">Details</span></th></tr></thead><tbody>${files.map(file=>`<tr><td><button class="file-link" data-action="file" data-id="${file.id}"><span class="file-glyph" style="--tile:${categoryColors[file.category]}">${icon(categoryIcons[file.category])}</span><span><strong>${e(file.name)}</strong><small>${e(file.relative)}</small></span></button></td><td><span class="category-tag">${e(file.category)}</span></td><td class="date-cell">${date(file.modified)}</td><td class="align-right size-cell">${bytes(file.size)}</td><td><button class="icon-button" data-action="file" data-id="${file.id}" aria-label="Details for ${e(file.name)}">${icon('chevron')}</button></td></tr>`).join('')}</tbody></table></div><div class="pagination"><span>${number((state.pageNumber-1)*40+1)}–${number(Math.min(state.pageNumber*40,filtered.length))} of ${number(filtered.length)} files</span><div><button class="button small secondary" data-action="prev-files" ${state.pageNumber===1?'disabled':''}>Previous</button><span>${state.pageNumber} / ${pages}</span><button class="button small secondary" data-action="next-files" ${state.pageNumber===pages?'disabled':''}>Next</button></div></div>`;
}
function review() {
  const r=state.report;
  const filtered=r.findings.filter(item=>(state.reviewKind==='all'||item.kind===state.reviewKind)&&(state.showKept||state.decisions[item.id]!=='keep'));
  state.reviewPage=Math.min(state.reviewPage,Math.max(1,Math.ceil(filtered.length/24)));
  return `${heading('A SECOND LOOK, ON YOUR TERMS', 'A thoughtful review queue.', 'See the reason, understand the tradeoff, and decide what matters to you.', exportButton())}
  <div class="review-summary"><span class="review-summary-icon">${icon('layers')}</span><div><strong>${bytes(r.summary.review_bytes)} <span>worth reviewing</span></strong><p>Categories don’t double-count the same files. Actual savings depend on what you keep.</p></div><span class="pill">${r.findings.length} findings</span></div>
  <div class="filter-line"><div class="filter-chips">${[['all','All findings'],...Object.entries(kindLabels)].map(([key,label])=>`<button class="filter-chip ${state.reviewKind===key?'selected':''}" data-action="review-filter" data-kind="${key}">${label}<span>${key==='all'?r.findings.length:r.findings.filter(f=>f.kind===key).length}</span></button>`).join('')}</div><label class="check-label"><input type="checkbox" id="show-kept" ${state.showKept?'checked':''}> Show kept items</label></div>
  <div class="review-grid">${filtered.slice((state.reviewPage-1)*24,state.reviewPage*24).map(item=>`<article class="review-card"><div class="review-card-top"><span class="item-icon ${item.kind}">${icon({duplicates:'copy',generated:'code',installers:'box',large:'file'}[item.kind])}</span><span class="pill ${state.decisions[item.id]==='keep'?'kept':''}">${state.decisions[item.id]==='keep'?'Marked to keep':e(item.confidence)}</span></div><div class="review-card-size">${bytes(item.bytes)}</div><h2>${e(item.title)}</h2><p class="path-line" title="${e(item.path)}">${e(item.path)}</p><p class="review-description">${e(item.purpose)}</p><div class="review-card-bottom"><span>${item.risk==='conditional'?'Check before rebuilding':'Your review needed'}</span><button class="text-link" data-action="finding" data-id="${item.id}">See the evidence ${icon('arrow')}</button></div></article>`).join('')}</div>
  ${filtered.length>24?pager(filtered.length,state.reviewPage,24,'review-page'):''}
  ${!filtered.length?empty('All clear in this view', 'Change the filter or show items you marked to keep.', 'circlecheck'):''}`;
}
function duplicates() {
  const r=state.report;
  return `${heading('SAME CONTENT, DIFFERENT PLACES', 'Seeing double?', 'Exact content matches, verified with SHA-256. Intentional backups still belong.', exportButton())}
  <div class="three-facts"><div><strong>${r.duplicates.length}</strong><span>matching groups</span></div><div><strong>${bytes(r.summary.duplicate_bytes)}</strong><span>extra-copy logical size</span></div><div><strong>${number(r.coverage.hashed_files)}</strong><span>files hashed</span></div></div>
  <div class="notice">${icon('shield')}<p>Identical content doesn’t mean identical purpose. Lumen never chooses a copy to remove. Hard links aren’t counted twice, and large or changing files may be excluded.</p></div>
  ${r.duplicates.slice((state.duplicatePage-1)*12,state.duplicatePage*12).map(group=>`<section class="panel duplicate-group"><div class="panel-heading"><div><div class="eyebrow">${group.files.length} IDENTICAL COPIES</div><h2>${e(group.files[0].name)}</h2></div><div class="duplicate-saving"><strong>${bytes(group.potential_bytes)}</strong><span>extra copies</span></div></div><div class="duplicate-paths">${group.files.slice(0,20).map((file,index)=>`<div><span class="copy-number">${String(index+1).padStart(2,'0')}</span><span>${icon('file')}</span><button class="path-button" data-action="file" data-id="${file.id}">${e(file.path)}</button><span>${bytes(file.size)}</span><button class="icon-button" data-action="copy-path" data-path="${e(file.path)}" aria-label="Copy path">${icon('copy')}</button></div>`).join('')}</div>${group.files.length>20?`<p class="help-text group-limit">Showing 20 of ${number(group.files.length)} locations. The complete group is in the JSON export.</p>`:''}<div class="duplicate-bottom"><span class="hash-label">${icon('circlecheck')} SHA-256 <code>${e(group.hash.slice(0,20))}…</code></span><button class="text-link" data-action="finding" data-id="dup-${group.id}">Review context ${icon('arrow')}</button></div></section>`).join('')}
  ${r.duplicates.length>12?pager(r.duplicates.length,state.duplicatePage,12,'duplicate-page'):''}
  ${!r.duplicates.length?empty(r.coverage.hashing?'No duplicates found within these bounds':'Content verification is off',r.coverage.hashing?'No exact matches were found among the files eligible for hashing. See coverage for limits.':'Start a new scan and enable duplicate verification. File contents are read locally and never sent to the assistant.','copy',scanButton()):''}`;
}
function compatibleHistory() { const r=state.report; return state.history.filter(item=>item.id!==r.id&&item.demo===r.demo&&JSON.stringify([...item.roots].sort())===JSON.stringify([...r.roots].sort())&&item.created<=r.created); }
function history() {
  const compatible=compatibleHistory();
  if(!compatible.some(item=>item.id===state.beforeId)) state.beforeId=compatible[0]?.id||'';
  return `${heading('A STORY OVER TIME', 'What changed?', 'Compare snapshots of the same folders. Find where your storage grew.', scanButton())}
  <section class="panel comparison-panel"><div class="panel-heading"><div><h2>A before-and-after view</h2><p>Current snapshot: ${e(state.report.name)} · ${dateTime(state.report.created)}</p></div>${icon('clock')}</div><div class="compare-controls"><label>Compare with<select id="compare-before" ${compatible.length?'':'disabled'}>${compatible.length?compatible.map(item=>`<option value="${item.id}" ${item.id===state.beforeId?'selected':''}>${e(item.name)} · ${dateTime(item.created)}</option>`).join(''):'<option>No earlier compatible snapshot</option>'}</select></label><button class="button primary" data-action="compare" ${compatible.length?'':'disabled'}>${icon('layers')} Compare snapshots</button></div><div id="comparison-results">${comparisonResults()}</div></section>
  <section class="panel"><div class="panel-heading"><div><h2>Your snapshot library</h2><p>Live snapshots are stored only in Lumen’s local state folder. The latest 100 are listed here.</p></div><span class="pill">${state.history.length} snapshots</span></div><div class="snapshot-list">${[...state.history].sort((a,b)=>b.created-a.created).map(item=>`<div class="snapshot-row"><span class="item-icon">${icon(item.demo?'leaf':'drive')}</span><div><strong>${e(item.name)} <span class="mini-tag">${item.demo?'DEMO':'LOCAL'}</span></strong><span>${dateTime(item.created)} · ${number(item.summary.files)} files</span></div><strong>${bytes(item.summary.bytes)}</strong><button class="button small secondary" data-action="load-report" data-id="${item.id}" ${state.report.id===item.id?'disabled':''}>${state.report.id===item.id?'Viewing':'Open'}</button></div>`).join('')}</div></section>`;
}
function comparisonResults() {
  const c=state.comparison;
  if(!c) return '<div class="comparison-placeholder">Two snapshots. One clearer picture of what’s changed.</div>';
  return `<div class="change-stats"><div><strong class="${c.delta>0?'warm':''}">${c.delta>0?'+':''}${bytes(c.delta)}</strong><span>net logical size change</span></div><div><strong>${c.added}</strong><span>newly observed files</span></div><div><strong>${c.removed}</strong><span>no longer observed</span></div><div><strong>${c.changed}</strong><span>changed files</span></div></div><p class="help-text">${icon('info')} ${c.partial?'One or both snapshots have exclusions. A missing file may be out of scope or inaccessible, rather than deleted.':'Changes reflect observed metadata. A rename appears as one added and one missing file.'} ${number(c.total_changes ?? c.changes.length)} changes observed; up to 500 retained.</p>${c.changes.length?`<div class="change-list">${c.changes.slice(0,100).map(item=>`<div><span class="change-kind ${item.kind}">${item.kind==='removed'?'Missing':item.kind==='added'?'New':'Changed'}</span><span><strong>${e(item.name)}</strong><small>${e(item.path)}</small></span><strong class="${item.delta>0?'warm':''}">${item.delta>0?'+':''}${bytes(item.delta)}</strong></div>`).join('')}${c.changes.length>100?'<p class="help-text">Showing the largest 100 changes in this view.</p>':''}</div>`:empty('No observed changes', 'The compared file sizes and modification timestamps match.', 'check')}`;
}
function apps() {
  const r=state.report;
  return `${heading('WHAT’S INSTALLED', 'Meet your applications.', 'Declared application metadata, without running installers or changing settings.', exportButton())}
  <div class="notice">${icon('info')}<p>Application inventory reads standard Windows registry entries. Portable apps and some Store apps may be absent. A service date can reflect an update or repair. Last-used time is unknown.</p></div>
  <section class="panel">${r.apps.length?`<div class="table-scroll"><table class="file-table"><thead><tr><th>APPLICATION</th><th>VERSION</th><th>SERVICE DATE (DECLARED)</th><th>LAST USED</th></tr></thead><tbody>${r.apps.map(app=>`<tr><td><div class="app-name">${icon('monitor')}<span><strong>${e(app.name)}</strong><small>${e(app.publisher||'Publisher not declared')}</small></span></div></td><td>${e(app.version||'Unknown')}</td><td>${e(app.service_date||'Unknown')}</td><td><span class="category-tag">Unknown</span></td></tr>`).join('')}</tbody></table></div>`:empty('No application inventory in this snapshot', 'On your Windows laptop, enable installed-app metadata when starting a scan. This feature never uninstalls or repairs anything.', 'monitor', scanButton())}</section>`;
}
function assistant() {
  return `${heading('A LITTLE HELP CONNECTING THE DOTS', 'Ask, understand, decide.', 'Grounded in your snapshot. No tools to execute commands or change files.')}
  <div class="assistant-layout"><section class="panel chat-panel"><div class="chat-header"><span class="assistant-mark">${icon('spark')}</span><div><strong>Your storage, explained</strong><span>${state.report.demo?'Fictional demo snapshot':'Local snapshot'} · ${state.model?e(state.model):'Evidence guide'}</span></div><button class="icon-button" data-action="clear-chat" aria-label="Clear conversation">${icon('refresh')}</button></div><div class="chat-messages" id="chat-messages" aria-live="polite">${chatMessages()}</div><form id="ask-form" class="chat-composer"><label class="sr-only" for="question">Ask about your snapshot</label><textarea id="question" rows="2" maxlength="2000" placeholder="What’s worth reviewing first?" ${state.asking?'disabled':''}>${e(state.draft)}</textarea><button class="send-button" type="submit" ${state.asking?'disabled':''} aria-label="Send question">${icon('arrow')}</button></form><div class="chat-footnote">${state.model?'Generated locally. Verify explanations against the evidence.':'Rule-based guide · No model or API key needed'}</div></section>
  <aside class="assistant-sidebar"><section class="panel model-panel"><span class="eyebrow">CHOOSE YOUR GUIDE</span><h3>Helpful by default.<br>AI when you want it.</h3><p>The evidence guide works immediately. For richer explanations, connect a model you already run in Ollama.</p><label for="model-select">Explanation engine</label><select id="model-select"><option value="">Evidence guide (no model)</option>${state.models.map(model=>`<option value="${e(model)}" ${state.model===model?'selected':''}>${e(model)}</option>`).join('')}</select><button class="button secondary full-width" data-action="models">${icon('refresh')} Refresh local models</button><div class="model-disclosure">${icon('shield')}<span>Loopback only. No API keys. No model downloads. Filenames and metadata go to the selected local model; document contents do not.</span></div></section><section class="prompt-panel"><span class="eyebrow">A FEW GOOD QUESTIONS</span>${['What should I review first?','Which project folders can be rebuilt?','Explain my duplicate files.','Do you know when I last opened a file?'].map(q=>`<button data-action="ask-prompt" data-question="${e(q)}">${q}${icon('arrow')}</button>`).join('')}</section></aside></div>`;
}
function messageReferences(message) {
  const items=[];
  for(const id of message.references || []){const item=state.report.findings.find(f=>f.id===id);if(item)items.push({id,title:item.title,action:'finding'});}
  for(const id of message.file_references || []){const file=state.report.files.find(f=>f.id===id);if(file)items.push({id,title:file.name,action:'file'});}
  return items.length?`<div class="reference-chips">${items.map(item=>`<button data-action="${item.action}" data-id="${e(item.id)}">${icon('file')}${e(item.title)}${icon('chevron')}</button>`).join('')}</div>`:'';
}
function chatMessages() {
  return `<div class="chat-message assistant-message"><span class="message-avatar">${icon('spark')}</span><div><span class="message-label">LUMEN · EVIDENCE GUIDE</span><p>Think of me as a second pair of eyes.<br>I can explain the findings, point to the evidence, and help you understand what removal could affect.</p><p class="muted">${state.report.demo?'We’re looking at fictional demo data. Opening this demo does not scan your computer.':'I’m looking at your saved snapshot, not monitoring your computer.'}</p></div></div>${state.messages.map(message=>`<div class="chat-message ${message.role==='user'?'user-message':'assistant-message'}">${message.role==='user'?'':`<span class="message-avatar">${icon('spark')}</span>`}<div>${message.role==='user'?'':`<span class="message-label">${message.source==='ollama'?'LOCAL AI · '+e(message.model):'LUMEN · EVIDENCE GUIDE'}</span>`}<p class="message-text">${e(message.text)}</p>${messageReferences(message)}${message.note?`<small class="message-note">${e(message.note)}</small>`:''}</div></div>`).join('')}${state.asking?'<div class="thinking" role="status"><span></span><span></span><span></span> Reading the evidence…</div>':''}`;
}

function openDialog(content, drawer=false) {
  closeDialog();
  $('#overlay-root').innerHTML=`<dialog class="${drawer?'detail-drawer':'modal'}"><button class="dialog-close icon-button" data-action="close-dialog" aria-label="Close dialog">${icon('close')}</button>${content}</dialog>`;
  const dialog=$('dialog');
  dialog.setAttribute('aria-labelledby','dialog-title');
  dialog.showModal();
  dialog.addEventListener('cancel',event=>{event.preventDefault();closeDialog();});
  dialog.addEventListener('click',event=>{if(event.target===dialog){const rect=dialog.getBoundingClientRect();if(event.clientX<rect.left||event.clientX>rect.right||event.clientY<rect.top||event.clientY>rect.bottom)closeDialog();}});
}
function closeDialog() { const dialog=$('dialog'); if(dialog){dialog.close();dialog.remove();} }
function showFinding(id) {
  const item=state.report.findings.find(f=>f.id===id); if(!item)return;
  openDialog(`<div class="drawer-heading"><span class="item-icon ${item.kind}">${icon({duplicates:'copy',generated:'code',installers:'box',large:'file'}[item.kind])}</span><div class="eyebrow">${e(kindLabels[item.kind])}</div><h2 id="dialog-title">${e(item.title)}</h2><div class="drawer-size">${bytes(item.bytes)} <span>under review</span></div><span class="pill">${e(item.confidence)}</span></div><section class="drawer-section"><h3>What is it?</h3><p>${e(item.purpose)}</p></section><section class="drawer-section"><h3>${icon('circlecheck')} The evidence</h3><ul class="evidence-list">${item.evidence.map(line=>`<li>${e(line)}</li>`).join('')}</ul></section><section class="consequence-box"><h3>${icon('info')} What removal could affect</h3><p>${e(item.consequence)}</p></section><section class="drawer-section"><h3>A thoughtful next step</h3><p>${e(item.recommendation)}</p></section><section class="drawer-section"><h3>Locations <span class="count-badge">${item.paths.length}</span></h3><div class="location-list">${item.paths.slice(0,30).map(path=>`<div><code>${e(path)}</code><button class="icon-button" data-action="copy-path" data-path="${e(path)}" aria-label="Copy path">${icon('copy')}</button></div>`).join('')}${item.paths.length>30?`<p class="muted">${number(item.paths.length-30)} more locations in the exported report.</p>`:''}</div></section><div class="drawer-actions"><button class="button primary" data-action="keep" data-id="${id}">${icon('check')} ${state.decisions[id]==='keep'?'Return to review':'Mark to keep'}</button><button class="button secondary" data-action="explain-finding" data-id="${id}">${icon('spark')} Explain this</button><p>Review labels belong to this snapshot and browser. Files are never changed.</p></div>`,true);
}
function showFile(id) {
  const file=state.report.files.find(f=>f.id===id);if(!file)return;
  const finding=state.report.findings.find(item=>item.paths.includes(file.path));
  openDialog(`<div class="drawer-heading"><span class="item-icon">${icon(categoryIcons[file.category])}</span><div class="eyebrow">FILE DETAILS</div><h2 id="dialog-title">${e(file.name)}</h2><div class="drawer-size">${bytes(file.size)} <span>logical size</span></div></div><section class="drawer-section"><h3>Location</h3><div class="location-list"><div><code>${e(file.path)}</code><button class="icon-button" data-action="copy-path" data-path="${e(file.path)}" aria-label="Copy path">${icon('copy')}</button></div></div></section><section class="drawer-section"><h3>What it likely does</h3><p>${e(file.purpose || "Purpose unknown. File contents have not been inspected.")}</p><p class="help-text">Based on file and folder conventions, not content inspection.</p></section><dl class="file-properties"><div><dt>Category</dt><dd>${e(file.category)}</dd></div><div><dt>Last modified</dt><dd>${dateTime(file.modified)}</dd></div><div><dt>Last opened by a person</dt><dd>Unknown</dd></div><div><dt>Raw access timestamp</dt><dd>${dateTime(file.accessed)}</dd></div><div><dt>Size in bytes</dt><dd>${number(file.size)}</dd></div></dl><div class="consequence-box"><h3>${icon('info')} Timestamps need context</h3><p>Access time can reflect a background process, be delayed, or be disabled. It does not establish when you last opened this file. Older files can still be essential.</p></div>${finding?`<section class="drawer-section"><h3>Related finding</h3><button class="button secondary full-width" data-action="finding" data-id="${finding.id}">${e(finding.title)} ${icon('arrow')}</button></section>`:'<section class="drawer-section"><h3>No review rule matched</h3><p>This is not a guarantee of importance or safety. Lumen has not interpreted this file’s contents.</p></section>'}<div class="drawer-actions"><button class="button primary" data-action="explain-file" data-id="${file.id}">${icon('spark')} Explain this file</button></div>`,true);
}
function showScan() {
  if(state.scan?.status==='running'){toast('A scan is already in progress. You can cancel it in the progress banner.');return;}
  const disabled=state.config.demo_only;
  openDialog(`<div class="modal-symbol">${icon(disabled?'leaf':'folder')}</div><div class="eyebrow">${disabled?'A SAFE PLACE TO EXPLORE':'CHOOSE THE SCOPE'}</div><h2 id="dialog-title">${disabled?'This workspace is demo-only.':'Let’s take a look around.'}</h2><p class="modal-intro">${state.config.hosted_demo?'Explore fictional snapshots and the evidence guide here. Download the local app to scan your folders or use Ollama.':disabled?'Live filesystem scans are blocked at the server. Every dashboard view uses fictional data, so you can explore without auditing this remote desktop.':'Choose local folders to inventory. Lumen reads metadata and saves its own snapshot. It never deletes files or changes settings.'}</p>${disabled?`<div class="notice"><p>On your own laptop, run <code>python run.py</code> or double-click <strong>Start Lumen.cmd</strong> to enable scans. The app still starts with the demo and waits for you to choose folders.</p></div><button class="button primary full-width" data-action="close-dialog">Back to exploring ${icon('arrow')}</button>`:`<form id="scan-form"><label class="field-label" for="scan-name">Snapshot label <span>Optional · up to 80 characters</span></label><input id="scan-name" class="snapshot-name" maxlength="80" placeholder="Before spring cleanup"><label class="field-label" for="scan-roots">Folder paths <span>One per line · up to 8</span></label><textarea id="scan-roots" rows="3" placeholder="C:\\Users\\you\\Downloads" required></textarea><div class="preset-chips">${!state.report.demo?'<button type="button" data-action="reuse-scope">Use current snapshot folders</button>':''}${state.config.locations.map(location=>`<button type="button" data-action="add-root" data-path="${e(location.path)}">${icon('plus')} ${e(location.label)}</button>`).join('')}</div><label class="option-card"><input type="checkbox" id="scan-hash"><span><strong>Verify duplicate files</strong><small>Reads eligible file contents locally for SHA-256. Up to 512 MiB per file and 2 GiB total. No contents sent to AI.</small></span></label><label class="option-card"><input type="checkbox" id="scan-apps"><span><strong>Include installed-app metadata</strong><small>Windows only. Reads registry entries without running installers, repairs, or administrator commands.</small></span></label><div class="scan-boundaries">${icon('shield')}<p>System folders, credential files, links, and cloud placeholders are skipped. Reads can update OS-managed access timestamps. Inventory is capped at 100,000 files.</p></div><p id="scan-error" class="form-error" role="alert"></p><button class="button primary full-width" type="submit">${icon('search')} Start read-only scan</button></form>`}`);
}
function showCoverage() {
  const r=state.report,c=r.coverage;
  openDialog(`<div class="eyebrow">THE EDGES OF THE PICTURE</div><h2 id="dialog-title">Transparent by design.</h2><p class="modal-intro">A useful report tells you what it couldn’t see, too.</p><dl class="file-properties"><div><dt>Inventoried files</dt><dd>${number(r.files.length)}</dd></div><div><dt>Folders visited</dt><dd>${number(c.directories)}</dd></div><div><dt>Items skipped</dt><dd>${number(c.skipped)}</dd></div><div><dt>Inventory limit reached</dt><dd>${c.limited?'Yes — partial snapshot':'No'}</dd></div><div><dt>Files hashed</dt><dd>${number(c.hashed_files)}</dd></div><div><dt>Bytes read for hashing</dt><dd>${bytes(c.hashed_bytes)}</dd></div><div><dt>Duration</dt><dd>${r.duration} seconds</dd></div></dl><h3>Selected scope</h3><div class="location-list">${r.roots.map(root=>`<div><code>${e(root)}</code></div>`).join('')}</div>${r.warnings.length?`<h3>Notes</h3><ul class="evidence-list">${r.warnings.map(w=>`<li>${e(w)}</li>`).join('')}</ul>`:''}<h3>Skipped locations <small>(up to 500 recorded)</small></h3><div class="skipped-list">${r.skipped.map(item=>`<div><code>${e(item.path)}</code><span>${e(item.reason)}</span></div>`).join('')||'<p>No skips recorded.</p>'}</div>`,true);
}
function showPrivacy() {
  openDialog(`<div class="modal-symbol">${icon('shield')}</div><div class="eyebrow">LOCAL BY DESIGN</div><h2 id="dialog-title">An observer, never a cleaner.</h2><p class="modal-intro">Lumen gives you context. You keep control.</p><div class="privacy-list"><div>${icon('folder')}<span><strong>Explicit scope</strong><p>Nothing is scanned on startup. You choose folders and optional content hashing. Protected and inaccessible items are skipped.</p></span></div><div>${icon('shield')}<span><strong>No changes to your files</strong><p>No delete, move, uninstall, elevation, or command-execution feature exists. File reads can update OS-managed access metadata.</p></span></div><div>${icon('spark')}<span><strong>AI is optional and local</strong><p>The evidence guide needs no model. Ollama receives only your question and a bounded metadata summary with selected root paths masked. Filenames remain visible to that local model. No file contents are sent.</p></span></div><div>${icon('drive')}<span><strong>Your snapshots stay here</strong><p>${state.config.hosted_demo ? "This demo uses fictional reports." : `Live reports are stored in <code>${e(state.config.state_dir)}</code>.`} Review labels stay in this browser. Exports contain paths and filenames; review them before sharing.</p></span></div></div><div class="notice"><p>Lumen is a storage review tool, not a malware scanner or a guarantee that an item can be removed. Unknown means unknown.</p></div>`);
}
function showExport() {
  openDialog(`<div class="modal-symbol">${icon('download')}</div><div class="eyebrow">TAKE THE CLARITY WITH YOU</div><h2 id="dialog-title">Your report, to keep.</h2><p class="modal-intro">A portable record of this snapshot. Exports contain local paths and filenames; review them before sharing.</p><button class="export-option" data-action="download" data-format="html">${icon('file')}<span><strong>Readable report</strong><small>Self-contained HTML · opens offline · print to PDF</small></span>${icon('arrow')}</button><button class="export-option" data-action="download" data-format="json">${icon('code')}<span><strong>Complete snapshot</strong><small>JSON · full inventory, evidence, and coverage</small></span>${icon('arrow')}</button><button class="export-option" data-action="download" data-format="csv">${icon('grid')}<span><strong>Spreadsheet inventory</strong><small>CSV · every file, purpose, timestamps, and finding IDs</small></span>${icon('arrow')}</button><p class="help-text">Exports include measured findings, not generated AI responses or browser-only review labels.</p>`);
}

async function loadReport(id) {
  const epoch=++loadEpoch;
  const report=await api('/api/reports/'+encodeURIComponent(id));
  if(epoch!==loadEpoch)return;
  ++reportEpoch;
  state.report=report;state.reviewPage=1;state.duplicatePage=1;readDecisions(); state.query='';state.category='all';state.folder='';state.pageNumber=1;state.messages=[];state.draft='';state.comparison=null;state.beforeId='';closeDialog();shell();
}
async function navigate(page) { state.page=page;state.mobileNav=false;shell();window.scrollTo({top:0,behavior:'instant'}); }
function renderProgress() {
  const node=$('#scan-progress');if(!node)return;
  const s=state.scan;
  if(s?.status!=='running'){node.innerHTML='';return;}
  node.innerHTML=`<div class="progress-banner" role="status"><span class="spinner"></span><div><strong>${s.phase==='hashing'?'Verifying duplicate content':s.phase==='applications'?'Reading application metadata':'Building your inventory'}</strong><span>${number(s.files)} files observed · ${number(s.skipped)} skipped${s.phase==='hashing'?' · '+bytes(s.hashed_bytes||0)+' hashed':''}</span></div><button class="button small secondary" data-action="cancel-scan">Cancel scan</button></div>`;
}
let scanTimer;
let scanFailures=0;
async function pollScan() {
  try {
    state.scan=await api('/api/scan');renderProgress();
    if(state.scan.status==='running'){scanFailures=0;scanTimer=setTimeout(pollScan,700);return;}
    if(state.scan.status==='complete') {state.history=await api('/api/history');await loadReport(state.scan.report_id);toast('Snapshot ready. Nothing moved, nothing deleted.');}
    else if(state.scan.status==='cancelled')toast(state.scan.message);
    else if(state.scan.status==='error')toast(state.scan.message,true);
    scanFailures=0;
  } catch(error){
    scanFailures++;
    if(scanFailures<=5){if(scanFailures===1)toast('Connection interrupted. Reconnecting to scan progress…');scanTimer=setTimeout(pollScan,Math.min(5000,scanFailures*1000));}
    else {const node=$('#scan-progress');if(node)node.innerHTML=`<div class="notice"><p>The server could not be reached. A scan may still be running.</p><button class="button secondary small" data-action="retry-scan">Reconnect</button></div>`;toast(error.message,true);}
  }
}
async function ask(question, findingId, fileId) {
  if(state.asking){toast('Lumen is still answering your previous question.');return;}
  question=question.trim();if(!question)return;
  const reportId=state.report.id, epoch=reportEpoch;
  state.asking=true;state.draft='';state.messages.push({role:'user',text:question});state.page='assistant';closeDialog();shell();scrollChat();
  try {
    let result=await api('/api/ask',{report_id:reportId,question,model:state.model||null,finding_id:findingId||null,file_id:fileId||null});
    const jobId=result.job_id;
    for(let count=0;result.status==='running'&&count<120;count++) {await new Promise(resolve=>setTimeout(resolve,1000));result=await api('/api/answers/'+jobId);}
    if(result.status==='error')throw new Error(result.message);
    if(result.status!=='complete')throw new Error('The local model took too long. Try a smaller model or the evidence guide.');
    if(state.report.id===reportId && reportEpoch===epoch)state.messages.push({role:'assistant',text:result.result.answer,...result.result});
  } catch(error){if(state.report.id===reportId && reportEpoch===epoch)state.messages.push({role:'assistant',text:'I couldn’t complete that explanation. '+error.message,note:'You can switch to the evidence guide and try again.'});}
  finally {state.asking=false;if(state.page==='assistant'){updatePage();scrollChat();}}
}
function scrollChat() { const node=$('#chat-messages');if(node)node.scrollTop=node.scrollHeight; }
async function download(format) {
  const report=state.report;
  const response=await api(`/api/reports/${encodeURIComponent(report.id)}.${format}`,undefined,true);
  const url=URL.createObjectURL(response);const link=document.createElement('a');link.href=url;link.download=`lumen-${report.demo?'demo':report.id}.${format}`;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);closeDialog();toast('Report exported. Your scanned files were not changed.');
}

document.addEventListener('click',event=>{
  const button=event.target.closest('[data-action]');if(!button||button.disabled)return;
  const {action,id,page,path,kind,question,format}=button.dataset;
  run((async()=>{
    switch(action){
      case 'navigate':await navigate(page);break;
      case 'mobile-nav':state.mobileNav=!state.mobileNav;$('.sidebar').classList.toggle('open',state.mobileNav);button.setAttribute('aria-expanded',String(state.mobileNav));break;
      case 'search':state.page='explorer';state.category='all';state.folder='';shell();$('#file-search').focus();break;
      case 'scan':showScan();break;
      case 'retry-scan':button.disabled=true;try{clearTimeout(scanTimer);scanFailures=0;await pollScan();}finally{button.disabled=false;}break;
      case 'privacy':showPrivacy();break;
      case 'coverage':showCoverage();break;
      case 'export':showExport();break;
      case 'download':button.disabled=true;try{await download(format);}finally{button.disabled=false;}break;
      case 'close-dialog':closeDialog();break;
      case 'finding':showFinding(id);break;
      case 'file':showFile(id);break;
      case 'category':state.folder='';state.category=button.dataset.category;state.pageNumber=1;state.query='';await navigate('explorer');break;
      case 'review-filter':state.reviewKind=kind;state.reviewPage=1;updatePage();break;
      case 'review-page':state.reviewPage+=Number(button.dataset.direction);updatePage();window.scrollTo(0,0);break;
      case 'duplicate-page':state.duplicatePage+=Number(button.dataset.direction);updatePage();window.scrollTo(0,0);break;
      case 'reset-filters':state.query='';state.category='all';state.folder='';state.pageNumber=1;updatePage();break;
      case 'folder':state.folder=button.dataset.folder;state.pageNumber=1;state.category='all';state.query='';updatePage();$('#file-results').scrollIntoView({block:'start',behavior:'smooth'});break;
      case 'clear-folder':state.folder='';state.pageNumber=1;updatePage();break;
      case 'prev-files':state.pageNumber--;$('#file-results').innerHTML=fileResults();break;
      case 'next-files':state.pageNumber++;$('#file-results').innerHTML=fileResults();break;
      case 'keep':{state.decisions[id]=state.decisions[id]==='keep'?'review':'keep';let saved=true;try{localStorage.setItem(decisionKey(),JSON.stringify(state.decisions));}catch{saved=false;}closeDialog();updatePage();const message=state.decisions[id]==='keep'?'Marked to keep. File unchanged.':'Returned to the review queue.';toast(message+(saved?'':' Browser storage is unavailable; this label may be lost when the snapshot reloads.'));break;}
      case 'copy-path':try{await navigator.clipboard.writeText(path);toast('Path copied.');}catch{openDialog(`<div class="eyebrow">COPY A LOCATION</div><h2 id="dialog-title">Your clipboard needs permission.</h2><p class="modal-intro">Select and copy this path manually.</p><textarea class="copy-fallback" readonly aria-label="Path to copy">${e(path)}</textarea>`);$('.copy-fallback').focus();$('.copy-fallback').select();}break;
      case 'reuse-scope':$('#scan-roots').value=state.report.roots.join('\n');break;
      case 'add-root':{const input=$('#scan-roots');const roots=input.value.split('\n').map(v=>v.trim()).filter(Boolean);if(!roots.includes(path))roots.push(path);input.value=roots.join('\n');break;}
      case 'cancel-scan':{const result=await api('/api/scan/cancel',{});toast(result.message);if(result.requested){button.disabled=true;button.textContent='Cancelling…';}break;}
      case 'load-report':button.disabled=true;button.textContent='Opening…';try{await loadReport(id);}finally{button.disabled=false;button.textContent='Open';}break;
      case 'compare':{const epoch=reportEpoch, baseline=state.beforeId;button.disabled=true;button.textContent='Comparing…';try{const comparison=await api(`/api/compare?before=${encodeURIComponent(baseline)}&after=${encodeURIComponent(state.report.id)}`);if(epoch===reportEpoch&&baseline===state.beforeId){state.comparison=comparison;if(state.page==='history')updatePage();}}finally{button.disabled=false;button.textContent='Compare snapshots';}break;}
      case 'ask-prompt':await ask(question);break;
      case 'explain-file':await ask('Explain this file and what removing it could affect.',null,id);break;
      case 'explain-finding':await ask('Explain this finding and what removing it could affect.',id);break;
      case 'clear-chat':if(!state.asking){state.messages=[];updatePage();}else toast('Wait for the current response before clearing.');break;
      case 'models':{const label=button.textContent;button.disabled=true;button.textContent='Checking localhost…';try{const result=await api('/api/models');state.models=result.models;if(!result.models.includes(state.model))state.model='';toast(result.message);updatePage();}finally{button.disabled=false;button.textContent=label;}break;}
    }
  })());
});
document.addEventListener('input',event=>{if(event.target.id==='question')state.draft=event.target.value;if(event.target.id==='file-search'){state.query=event.target.value;state.pageNumber=1;$('#file-results').innerHTML=fileResults();}});
document.addEventListener('change',event=>{
  if(event.target.id==='category-select'){state.category=event.target.value;state.pageNumber=1;$('#file-results').innerHTML=fileResults();}
  if(event.target.id==='file-sort'){state.sort=event.target.value;state.pageNumber=1;$('#file-results').innerHTML=fileResults();}
  if(event.target.id==='show-kept'){state.showKept=event.target.checked;updatePage();}
  if(event.target.id==='compare-before'){state.beforeId=event.target.value;state.comparison=null;$('#comparison-results').innerHTML=comparisonResults();}
  if(event.target.id==='model-select'){state.model=event.target.value;updatePage();}
});
document.addEventListener('submit',event=>{
  if(event.target.id==='ask-form'){event.preventDefault();run(ask($('#question').value));}
  if(event.target.id==='scan-form'){
    event.preventDefault();
    run((async()=>{const button=$('button[type="submit"]',event.target);button.disabled=true;$('#scan-error').textContent='';try{await api('/api/scan',{name:$('#scan-name').value,roots:$('#scan-roots').value.split('\n').map(v=>v.trim()).filter(Boolean),hash_duplicates:$('#scan-hash').checked,include_apps:$('#scan-apps').checked});closeDialog();clearTimeout(scanTimer);await pollScan();}catch(error){const field=$('#scan-error');if(field)field.textContent=error.message;else throw error;}finally{button.disabled=false;}})());
  }
});
document.addEventListener('pointerdown',event=>{
  if(state.mobileNav&&!event.target.closest('.sidebar,.mobile-toggle')){state.mobileNav=false;$('.sidebar').classList.remove('open');$('.mobile-toggle').setAttribute('aria-expanded','false');}
});
document.addEventListener('keydown',event=>{
  if(event.key==='Escape'&&state.mobileNav){state.mobileNav=false;$('.sidebar').classList.remove('open');$('.mobile-toggle').setAttribute('aria-expanded','false');$('.mobile-toggle').focus();}

  if(event.key==='/'&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName)&&!$('dialog')){event.preventDefault();state.page='explorer';shell();$('#file-search').focus();}
  if(event.target.id==='question'&&event.key==='Enter'&&!event.shiftKey&&!event.isComposing){event.preventDefault();run(ask(event.target.value));}
});
async function init() {
  try {
    state.config=await api('/api/bootstrap');
    const results=await Promise.allSettled([api('/api/reports/demo-current'),api('/api/history'),api('/api/scan')]);
    if(results[0].status==='rejected')throw results[0].reason;
    state.report=results[0].value;
    state.history=results[1].status==='fulfilled'?results[1].value:[state.report];
    state.scan=results[2].status==='fulfilled'?results[2].value:{status:'idle'};
    readDecisions();shell();
    if(results[1].status==='rejected')toast('Saved snapshots could not be loaded. The demo is still available. '+results[1].reason.message,true);
    if(results[2].status==='rejected'){scanFailures=0;pollScan();}
    else if(state.scan.status==='running')pollScan();
  }
  catch(error){$('#app').innerHTML=`<div class="boot"><img src="./favicon.svg" alt="" width="48" height="48"><h1>Lumen couldn’t connect.</h1><p>${e(error.message)}</p><p>Start <code>python run.py</code>, then reload this page.</p></div>`;}
}
init();
