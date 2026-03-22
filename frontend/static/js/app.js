// BetonLab Frontend — TS EN 13515 Laboratuvar Takip Sistemi
const API = window.location.origin;

const SIEVE_LIMITS = {
  "0-2":   {"0.063":[0,10],"0.125":[0,20],"0.25":[5,45],"0.5":[25,70],"1":[50,85],"2":[85,99],"4":[95,100]},
  "0-5":   {"0.063":[0,16],"0.125":[0,25],"0.25":[5,40],"0.5":[20,55],"1":[35,65],"2":[55,80],"4":[80,99],"5.6":[95,100]},
  "5-12":  {"1":[0,5],"2":[0,10],"4":[0,20],"5.6":[5,40],"8":[30,70],"11.2":[65,99],"16":[95,100]},
  "12-22": {"8":[0,5],"11.2":[0,15],"16":[20,55],"22.4":[80,99],"31.5":[95,100]},
};

// ─── CLOCK ────────────────────────────────────────────────────
function updateClock() {
  const now = new Date();
  document.getElementById('clock').textContent = now.toLocaleTimeString('tr-TR');
}
setInterval(updateClock, 1000);
updateClock();

// ─── API HEALTH ───────────────────────────────────────────────
async function checkApiHealth() {
  try {
    const r = await fetch(`${API}/api/health`);
    const dot = document.querySelector('.status-dot');
    if (r.ok) dot.classList.add('online');
    else dot.classList.add('offline');
  } catch { document.querySelector('.status-dot').classList.add('offline'); }
}
checkApiHealth();
setInterval(checkApiHealth, 30000);

// ─── NAVIGATION ───────────────────────────────────────────────
const pageTitles = {
  dashboard: 'Dashboard',
  sieve: 'Elek Analizi',
  pollution: 'Kirlilik Testi',
  recipes: 'Beton Reçetesi',
  report: 'Haftalık Rapor',
  trends: 'Trend Grafikleri',
};

function showPage(pageId) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  const page = document.getElementById(`page-${pageId}`);
  if (page) page.classList.add('active');
  const nav = document.querySelector(`[data-page="${pageId}"]`);
  if (nav) nav.classList.add('active');
  document.getElementById('pageTitle').textContent = pageTitles[pageId] || pageId;

  if (pageId === 'dashboard') loadDashboard();
  else if (pageId === 'sieve') loadSieveList();
  else if (pageId === 'pollution') loadPollutionList();
  else if (pageId === 'recipes') loadRecipeList();
  else if (pageId === 'report') initReportPage();
  else if (pageId === 'trends') loadTrends();

  // Close sidebar on mobile
  if (window.innerWidth < 900) document.getElementById('sidebar').classList.remove('open');
}

document.querySelectorAll('.nav-item').forEach(item => {
  item.addEventListener('click', (e) => {
    e.preventDefault();
    showPage(item.dataset.page);
  });
});

document.getElementById('menuToggle').addEventListener('click', () => {
  document.getElementById('sidebar').classList.toggle('open');
});

// ─── TOAST ────────────────────────────────────────────────────
function toast(msg, type = 'success', duration = 3500) {
  const icons = { success: '✓', error: '✕', warning: '⚠' };
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `<span>${icons[type] || '•'}</span><span>${msg}</span>`;
  document.getElementById('toastContainer').appendChild(el);
  setTimeout(() => el.remove(), duration);
}

// ─── MODAL ────────────────────────────────────────────────────
function openModal(id) { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }

document.querySelectorAll('.modal-overlay').forEach(overlay => {
  overlay.addEventListener('click', e => {
    if (e.target === overlay) overlay.classList.remove('open');
  });
});

// ─── STATUS BADGE ─────────────────────────────────────────────
function statusBadge(status) {
  if (!status) return '<span class="badge badge-warn">—</span>';
  const map = { 'UYGUN': 'ok', 'UYARI': 'warn', 'UYGUNSUZ': 'fail' };
  return `<span class="badge badge-${map[status] || 'warn'}">${status}</span>`;
}

function fmtDate(d) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('tr-TR');
}

function nullOrVal(v) { return v !== null && v !== undefined ? v : '—'; }

// ─── DASHBOARD ────────────────────────────────────────────────
async function loadDashboard() {
  try {
    const r = await fetch(`${API}/api/dashboard/stats`);
    const d = await r.json();

    document.getElementById('statSieveVal').textContent = d.totals.sieve_analyses;
    document.getElementById('statSieveWeek').textContent = `Bu hafta: ${d.this_week.sieve_analyses}`;
    document.getElementById('statPollutionVal').textContent = d.totals.pollution_tests;
    document.getElementById('statPollutionWeek').textContent = `Bu hafta: ${d.this_week.pollution_tests}`;
    document.getElementById('statRecipesVal').textContent = d.totals.concrete_recipes;
    const nc = d.non_conformities.sieve + d.non_conformities.pollution;
    document.getElementById('statNonConformVal').textContent = nc;
    document.getElementById('statNonConformSub').textContent = `Elek: ${d.non_conformities.sieve} | Kirlilik: ${d.non_conformities.pollution}`;
    if (nc > 0) document.getElementById('statNonConform').classList.add('danger');

    // Recent sieve
    const rs = d.recent_sieve.map(r => `
      <div style="display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid var(--border);font-size:12px;">
        <span style="color:var(--text3)">${fmtDate(r.test_date)}</span>
        <span>${r.aggregate_type} mm</span>
        ${statusBadge(r.status)}
      </div>`).join('') || '<p style="color:var(--text3);font-size:12px;">Kayıt yok</p>';
    document.getElementById('recentSieve').innerHTML = rs;

    const rp = d.recent_pollution.map(r => `
      <div style="display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid var(--border);font-size:12px;">
        <span style="color:var(--text3)">${fmtDate(r.test_date)}</span>
        <span>${r.aggregate_type} mm</span>
        ${statusBadge(r.status)}
      </div>`).join('') || '<p style="color:var(--text3);font-size:12px;">Kayıt yok</p>';
    document.getElementById('recentPollution').innerHTML = rp;

    // Compliance cards
    const totalS = d.totals.sieve_analyses;
    const nonS = d.non_conformities.sieve;
    const rateS = totalS ? Math.round((totalS - nonS) / totalS * 100) : 0;
    const totalP = d.totals.pollution_tests;
    const nonP = d.non_conformities.pollution;
    const rateP = totalP ? Math.round((totalP - nonP) / totalP * 100) : 0;

    document.getElementById('complianceGrid').innerHTML = `
      <div class="compliance-item">
        <div class="compliance-rate ${rateS >= 90 ? 'c-green' : rateS >= 70 ? 'c-yellow' : 'c-red'}">${rateS}%</div>
        <div class="compliance-label">Elek Analizi Uyum</div>
      </div>
      <div class="compliance-item">
        <div class="compliance-rate ${rateP >= 90 ? 'c-green' : rateP >= 70 ? 'c-yellow' : 'c-red'}">${rateP}%</div>
        <div class="compliance-label">Kirlilik Uyum</div>
      </div>
      <div class="compliance-item">
        <div class="compliance-rate" style="color:var(--accent)">${d.totals.sieve_analyses + d.totals.pollution_tests}</div>
        <div class="compliance-label">Toplam Test</div>
      </div>
      <div class="compliance-item">
        <div class="compliance-rate" style="color:var(--yellow)">${nc}</div>
        <div class="compliance-label">Toplam Uygunsuzluk</div>
      </div>
    `;
  } catch (e) { console.error(e); toast('Dashboard yüklenemedi', 'error'); }
}

// ─── SIEVE ANALYSIS ───────────────────────────────────────────
let sievePage = 0;
const PAGE_SIZE = 20;

async function loadSieveList() {
  const type = document.getElementById('sieveFilterType').value;
  const start = document.getElementById('sieveFilterStart').value;
  const end = document.getElementById('sieveFilterEnd').value;
  let url = `${API}/api/sieve-analyses?limit=${PAGE_SIZE}&offset=${sievePage * PAGE_SIZE}`;
  if (type) url += `&aggregate_type=${type}`;
  if (start) url += `&start_date=${start}`;
  if (end) url += `&end_date=${end}`;

  try {
    const r = await fetch(url);
    const d = await r.json();
    const tbody = document.getElementById('sieveTableBody');
    if (!d.data.length) {
      tbody.innerHTML = '<tr><td colspan="6" class="loading-row">Kayıt bulunamadı</td></tr>';
      return;
    }
    tbody.innerHTML = d.data.map(row => `
      <tr>
        <td>${fmtDate(row.test_date)}</td>
        <td><code style="font-family:var(--mono);color:var(--accent)">${row.aggregate_type} mm</code></td>
        <td style="color:var(--text3)">${row.source || '—'}</td>
        <td style="color:var(--text3)">${row.operator || '—'}</td>
        <td>${statusBadge(row.status)}</td>
        <td>
          <button class="btn-icon" onclick="viewSieveDetail(${row.id})" title="Detay">⊕</button>
          <button class="btn-icon" onclick="deleteSieve(${row.id})" title="Sil" style="color:var(--red)">✕</button>
        </td>
      </tr>
    `).join('');
    renderPagination('sievePagination', d.total, sievePage, (p) => { sievePage = p; loadSieveList(); });
  } catch (e) { toast('Elek listesi yüklenemedi', 'error'); }
}

async function viewSieveDetail(id) {
  const r = await fetch(`${API}/api/sieve-analyses/${id}`);
  const d = await r.json();
  const ev = d.evaluation || {};
  const details = ev.details || [];

  const detailRows = details.map(row => `
    <div class="eval-row ${row.status === 'UYGUNSUZ' ? 'fail' : row.status === 'UYARI' ? 'warn' : ''}">
      <span class="eval-mono">${row.sieve_mm} mm</span>
      <span class="eval-mono">${row.value}%</span>
      <span class="eval-mono" style="color:var(--text3)">${row.lower_limit}%</span>
      <span class="eval-mono" style="color:var(--text3)">${row.upper_limit}%</span>
      <span>${statusBadge(row.status)} ${row.comment ? `<small style="color:var(--text3);margin-left:6px">${row.comment}</small>` : ''}</span>
    </div>
  `).join('');

  document.getElementById('detailTitle').textContent = `Elek Analizi #${id} — ${d.aggregate_type} mm`;
  document.getElementById('detailContent').innerHTML = `
    <div class="detail-grid">
      <div class="detail-item"><span class="detail-label">Test Tarihi</span><span class="detail-value">${fmtDate(d.test_date)}</span></div>
      <div class="detail-item"><span class="detail-label">Agrega Tipi</span><span class="detail-value">${d.aggregate_type} mm</span></div>
      <div class="detail-item"><span class="detail-label">Kaynak</span><span class="detail-value">${d.source || '—'}</span></div>
      <div class="detail-item"><span class="detail-label">Operatör</span><span class="detail-value">${d.operator || '—'}</span></div>
      <div class="detail-item"><span class="detail-label">Numune Ağ.</span><span class="detail-value">${d.sample_weight ? d.sample_weight + ' g' : '—'}</span></div>
      <div class="detail-item"><span class="detail-label">Genel Durum</span><span class="detail-value">${statusBadge(d.status)}</span></div>
    </div>
    ${ev.message ? `<div style="padding:10px;background:var(--surface2);border-radius:4px;font-size:13px;margin-bottom:12px;">${ev.message}</div>` : ''}
    ${ev.recommendation ? `<div style="padding:10px;background:rgba(79,156,249,.08);border-left:3px solid var(--accent);border-radius:4px;font-size:13px;margin-bottom:12px;">${ev.recommendation}</div>` : ''}
    <div class="evaluation-detail">
      <div class="eval-row header">
        <span>Elek (mm)</span><span>Değer</span><span>Alt</span><span>Üst</span><span>Sonuç</span>
      </div>
      ${detailRows || '<div style="padding:10px;color:var(--text3);font-size:12px;">Detay yok</div>'}
    </div>
  `;
  openModal('modalDetail');
}

async function deleteSieve(id) {
  if (!confirm('Bu kayıt silinsin mi?')) return;
  await fetch(`${API}/api/sieve-analyses/${id}`, { method: 'DELETE' });
  toast('Kayıt silindi', 'success');
  loadSieveList();
}

// Sieve inputs by aggregate type
function updateSieveInputs() {
  const type = document.getElementById('siAggType').value;
  const grid = document.getElementById('sieveInputsGrid');
  if (!type || !SIEVE_LIMITS[type]) {
    grid.innerHTML = '<p class="hint">Önce agrega tipini seçin</p>';
    return;
  }
  const limits = SIEVE_LIMITS[type];
  grid.innerHTML = Object.entries(limits).map(([mm, [lo, hi]]) => `
    <div class="sieve-input-item">
      <label>
        <span>∅ ${mm} mm</span>
        <span class="sieve-range">${lo}–${hi}%</span>
      </label>
      <input type="number" id="sieve_${mm.replace('.', '_')}" min="0" max="100" step="0.1" placeholder="${Math.round((lo+hi)/2)}">
    </div>
  `).join('');
}

async function saveSieveAnalysis() {
  const testDate = document.getElementById('siTestDate').value;
  const aggType = document.getElementById('siAggType').value;
  if (!testDate || !aggType) { toast('Tarih ve agrega tipi zorunlu', 'error'); return; }

  const limits = SIEVE_LIMITS[aggType] || {};
  const sieveResults = {};
  for (const mm of Object.keys(limits)) {
    const el = document.getElementById(`sieve_${mm.replace('.', '_')}`);
    if (el && el.value !== '') sieveResults[mm] = parseFloat(el.value);
  }
  if (!Object.keys(sieveResults).length) { toast('En az bir elek değeri girin', 'error'); return; }

  const body = {
    test_date: testDate,
    aggregate_type: aggType,
    sample_weight: parseFloat(document.getElementById('siWeight').value) || null,
    operator: document.getElementById('siOperator').value || null,
    source: document.getElementById('siSource').value || null,
    notes: document.getElementById('siNotes').value || null,
    sieve_results: sieveResults,
  };

  try {
    const r = await fetch(`${API}/api/sieve-analyses`, {
      method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)
    });
    const d = await r.json();
    closeModal('modalSieve');
    const status = d.evaluation?.status || 'UYGUN';
    toast(`Kaydedildi — ${status}`, status === 'UYGUN' ? 'success' : 'warning');
    loadSieveList();
    if (status !== 'UYGUN') viewSieveDetail(d.id);
  } catch { toast('Kayıt başarısız', 'error'); }
}

// ─── POLLUTION TESTS ──────────────────────────────────────────
let pollPage = 0;

async function loadPollutionList() {
  const type = document.getElementById('pollFilterType').value;
  const start = document.getElementById('pollFilterStart').value;
  const end = document.getElementById('pollFilterEnd').value;
  let url = `${API}/api/pollution-tests?limit=${PAGE_SIZE}&offset=${pollPage * PAGE_SIZE}`;
  if (type) url += `&aggregate_type=${type}`;
  if (start) url += `&start_date=${start}`;
  if (end) url += `&end_date=${end}`;

  try {
    const r = await fetch(url);
    const d = await r.json();
    const tbody = document.getElementById('pollutionTableBody');
    if (!d.data.length) {
      tbody.innerHTML = '<tr><td colspan="8" class="loading-row">Kayıt bulunamadı</td></tr>';
      return;
    }
    tbody.innerHTML = d.data.map(row => `
      <tr>
        <td>${fmtDate(row.test_date)}</td>
        <td><code style="font-family:var(--mono);color:var(--accent)">${row.aggregate_type} mm</code></td>
        <td>${row.bypass_open ? '<span style="color:var(--red);font-weight:700">AÇIK⚠</span>' : '<span style="color:var(--green)">KAPALI</span>'}</td>
        <td class="eval-mono">${nullOrVal(row.mb_value)}</td>
        <td class="eval-mono">${nullOrVal(row.sand_equivalent)}</td>
        <td class="eval-mono">${nullOrVal(row.fine_content)}</td>
        <td>${statusBadge(row.status)}</td>
        <td>
          <button class="btn-icon" onclick="viewPollutionDetail(${row.id})">⊕</button>
        </td>
      </tr>
    `).join('');
    renderPagination('pollutionPagination', d.total, pollPage, (p) => { pollPage = p; loadPollutionList(); });
  } catch { toast('Kirlilik listesi yüklenemedi', 'error'); }
}

async function viewPollutionDetail(id) {
  const r = await fetch(`${API}/api/pollution-tests/${id}`);
  const d = await r.json();
  const ev = d.evaluation || {};
  const details = ev.details || [];

  const detailRows = details.map(row => `
    <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 12px;border-bottom:1px solid var(--border);font-size:12px;">
      <span>${row.parameter}</span>
      <span class="eval-mono">${row.value} ${row.unit || ''}</span>
      <span style="color:var(--text3)">Limit: ${row.limit || '—'} ${row.unit || ''}</span>
      ${statusBadge(row.status)}
    </div>
  `).join('');

  document.getElementById('detailTitle').textContent = `Kirlilik Testi #${id} — ${d.aggregate_type} mm`;
  document.getElementById('detailContent').innerHTML = `
    <div class="detail-grid">
      <div class="detail-item"><span class="detail-label">Test Tarihi</span><span class="detail-value">${fmtDate(d.test_date)}</span></div>
      <div class="detail-item"><span class="detail-label">Agrega</span><span class="detail-value">${d.aggregate_type} mm</span></div>
      <div class="detail-item"><span class="detail-label">Kaynak</span><span class="detail-value">${d.source || '—'}</span></div>
      <div class="detail-item"><span class="detail-label">Operatör</span><span class="detail-value">${d.operator || '—'}</span></div>
      <div class="detail-item"><span class="detail-label">Baypas</span><span class="detail-value">${d.bypass_open ? '<span style="color:var(--red)">AÇIK ⚠</span>' : '<span style="color:var(--green)">KAPALI</span>'}</span></div>
      <div class="detail-item"><span class="detail-label">Genel Durum</span><span class="detail-value">${statusBadge(d.status)}</span></div>
    </div>
    ${ev.message ? `<div style="padding:10px;background:var(--surface2);border-radius:4px;font-size:13px;margin-bottom:12px;">${ev.message}</div>` : ''}
    <div class="evaluation-detail">
      ${detailRows || '<div style="padding:10px;color:var(--text3);font-size:12px;">Ölçüm verisi girilmemiş</div>'}
    </div>
  `;
  openModal('modalDetail');
}

async function savePollutionTest() {
  const testDate = document.getElementById('ptTestDate').value;
  const aggType = document.getElementById('ptAggType').value;
  if (!testDate || !aggType) { toast('Tarih ve agrega tipi zorunlu', 'error'); return; }

  const body = {
    test_date: testDate,
    aggregate_type: aggType,
    operator: document.getElementById('ptOperator').value || null,
    source: document.getElementById('ptSource').value || null,
    bypass_open: document.getElementById('ptBypass').checked,
    washing_water_dirty: document.getElementById('ptWaterDirty').checked,
    washing_water_insufficient: document.getElementById('ptWaterInsuf').checked,
    mb_value: parseFloat(document.getElementById('ptMB').value) || null,
    sand_equivalent: parseFloat(document.getElementById('ptSE').value) || null,
    fine_content: parseFloat(document.getElementById('ptFine').value) || null,
    clay_lumps: parseFloat(document.getElementById('ptClay').value) || null,
    notes: document.getElementById('ptNotes').value || null,
  };

  try {
    const r = await fetch(`${API}/api/pollution-tests`, {
      method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)
    });
    const d = await r.json();
    closeModal('modalPollution');
    const status = d.evaluation?.status || 'UYGUN';
    toast(`Kaydedildi — ${status}`, status === 'UYGUN' ? 'success' : 'warning');
    loadPollutionList();
    if (status !== 'UYGUN') viewPollutionDetail(d.id);
  } catch { toast('Kayıt başarısız', 'error'); }
}

// ─── RECIPES ──────────────────────────────────────────────────
async function loadRecipeList() {
  const cls = document.getElementById('recipeFilterClass').value;
  let url = `${API}/api/concrete-recipes?limit=100`;
  if (cls) url += `&concrete_class=${encodeURIComponent(cls)}`;

  try {
    const r = await fetch(url);
    const d = await r.json();
    const grid = document.getElementById('recipesGrid');

    if (!d.data.length) {
      grid.innerHTML = '<div class="empty-state"><div class="empty-icon">⊟</div><p>Reçete bulunamadı</p></div>';
      return;
    }

    grid.innerHTML = d.data.map(rec => `
      <div class="recipe-card">
        <div class="recipe-card-header">
          <span class="recipe-class">${rec.concrete_class}</span>
          <span class="recipe-code">${rec.recipe_code}</span>
        </div>
        <div class="recipe-card-body">
          <div class="recipe-row"><span class="label">Çimento</span><span class="value">${rec.cement_type || '—'} / ${rec.cement_content || '—'} kg/m³</span></div>
          <div class="recipe-row"><span class="label">S/Ç</span><span class="value">${rec.water_cement_ratio || '—'}</span></div>
          <div class="recipe-row"><span class="label">0-5 mm</span><span class="value">${rec.aggregate_0_5 || 0} kg/m³</span></div>
          <div class="recipe-row"><span class="label">5-12 mm</span><span class="value">${rec.aggregate_5_12 || 0} kg/m³</span></div>
          <div class="recipe-row"><span class="label">12-22 mm</span><span class="value">${rec.aggregate_12_22 || 0} kg/m³</span></div>
          <div class="recipe-row"><span class="label">Katkı</span><span class="value">${rec.admixture_content || 0} kg/m³</span></div>
          <div class="recipe-row"><span class="label">Hedef f'c</span><span class="value">${rec.target_strength || '—'} MPa</span></div>
          <div class="recipe-row"><span class="label">Kıvam</span><span class="value">${rec.consistency_class || '—'} / ${rec.target_slump || '—'} mm</span></div>
        </div>
      </div>
    `).join('');
  } catch { toast('Reçete listesi yüklenemedi', 'error'); }
}

async function saveRecipe() {
  const body = {
    recipe_code: document.getElementById('rcCode').value,
    concrete_class: document.getElementById('rcClass').value,
    cement_type: document.getElementById('rcCementType').value || null,
    cement_content: parseFloat(document.getElementById('rcCement').value) || null,
    water_cement_ratio: parseFloat(document.getElementById('rcWC').value) || null,
    aggregate_0_2: parseFloat(document.getElementById('rcAgg02').value) || 0,
    aggregate_0_5: parseFloat(document.getElementById('rcAgg05').value) || 0,
    aggregate_5_12: parseFloat(document.getElementById('rcAgg512').value) || 0,
    aggregate_12_22: parseFloat(document.getElementById('rcAgg1222').value) || 0,
    aggregate_0_315: parseFloat(document.getElementById('rcAgg0315').value) || 0,
    admixture_type: null,
    admixture_content: parseFloat(document.getElementById('rcAdmixture').value) || 0,
    target_slump: parseFloat(document.getElementById('rcSlump').value) || null,
    target_strength: parseFloat(document.getElementById('rcStrength').value) || null,
    consistency_class: document.getElementById('rcConsistency').value,
    exposure_class: document.getElementById('rcExposure').value || null,
    notes: document.getElementById('rcNotes').value || null,
  };
  if (!body.recipe_code) { toast('Reçete kodu zorunlu', 'error'); return; }
  try {
    await fetch(`${API}/api/concrete-recipes`, {
      method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)
    });
    closeModal('modalRecipe');
    toast('Reçete kaydedildi', 'success');
    loadRecipeList();
  } catch { toast('Kayıt başarısız', 'error'); }
}

// ─── WEEKLY REPORT ────────────────────────────────────────────
function initReportPage() {
  const today = new Date();
  const monday = new Date(today);
  monday.setDate(today.getDate() - today.getDay() + 1);
  document.getElementById('reportWeekStart').value = monday.toISOString().split('T')[0];
}

async function generateReport() {
  const weekStart = document.getElementById('reportWeekStart').value;
  if (!weekStart) { toast('Hafta başlangıç tarihi seçin', 'error'); return; }

  const container = document.getElementById('reportContainer');
  container.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text3)">Rapor oluşturuluyor…</div>';

  try {
    const r = await fetch(`${API}/api/reports/weekly?week_start=${weekStart}`);
    const d = await r.json();
    renderReport(d, container);
  } catch { toast('Rapor oluşturulamadı', 'error'); }
}

function renderReport(d, container) {
  const statusColor = d.overall_status === 'UYGUN' ? 'var(--green)' : d.overall_status === 'UYARI' ? 'var(--yellow)' : 'var(--red)';
  const ss = d.sieve_summary;
  const ps = d.pollution_summary;
  const byTypeSieve = Object.entries(ss.by_type || {}).map(([t, v]) =>
    `<div class="report-stat"><span class="r-label">${t} mm</span><span class="r-value">${v.count} test / ${v.conforming} uygun</span></div>`
  ).join('');
  const byTypePoll = Object.entries(ps.by_type || {}).map(([t, v]) =>
    `<div class="report-stat"><span class="r-label">${t} mm</span><span class="r-value">${v.count} test / ${v.conforming} uygun</span></div>`
  ).join('');

  const nonConformHtml = d.non_conformities.length
    ? d.non_conformities.map(nc => `
        <div class="nonconform-item">
          <div class="nc-header">${fmtDate(nc.date)} — ${nc.type} — ${nc.aggregate} mm</div>
          <div class="nc-detail">${(nc.issues || []).join('; ')}</div>
        </div>`).join('')
    : '<p style="color:var(--green);font-size:13px">✓ Bu hafta uygunsuzluk tespit edilmedi</p>';

  const recsHtml = d.recommendations.map(rec => `
    <div class="recommendation-item rec-${rec.priority.replace('Ü','U').replace('İ','I')}">
      <div class="rec-priority" style="color:${rec.priority==='KRİTİK'?'var(--red)':rec.priority==='YÜKSEK'?'var(--yellow)':'var(--accent)'}">
        ${rec.priority} — ${rec.category}
      </div>
      <div>${rec.text}</div>
    </div>`).join('');

  container.innerHTML = `
    <div class="report-header">
      <div>
        <div class="report-title">Haftalık Laboratuvar Raporu — Hafta ${d.week_number}/${d.year}</div>
        <div class="report-subtitle">${fmtDate(d.week_start)} – ${fmtDate(d.week_end)} | Standart: ${d.standard}</div>
        <div class="report-subtitle" style="margin-top:4px">Toplam Test: ${d.total_tests} | Oluşturulma: ${new Date(d.generated_at).toLocaleString('tr-TR')}</div>
      </div>
      <div class="report-status-badge" style="background:${statusColor}22;color:${statusColor};border:1px solid ${statusColor}44">
        ${d.overall_status}
      </div>
    </div>

    <div class="report-grid">
      <div class="report-section">
        <div class="report-section-header">Elek Analizi Özeti</div>
        <div class="report-section-body">
          <div class="report-stat"><span class="r-label">Toplam Test</span><span class="r-value">${ss.count}</span></div>
          <div class="report-stat"><span class="r-label">Uygun</span><span class="r-value" style="color:var(--green)">${ss.conforming}</span></div>
          <div class="report-stat"><span class="r-label">Uyarı</span><span class="r-value" style="color:var(--yellow)">${ss.warning || 0}</span></div>
          <div class="report-stat"><span class="r-label">Uygunsuz</span><span class="r-value" style="color:var(--red)">${ss.non_conforming}</span></div>
          <div class="report-stat"><span class="r-label">Uyum Oranı</span><span class="r-value" style="color:var(--accent)">%${ss.compliance_rate}</span></div>
          ${byTypeSieve}
        </div>
      </div>
      <div class="report-section">
        <div class="report-section-header">Kirlilik Testi Özeti</div>
        <div class="report-section-body">
          <div class="report-stat"><span class="r-label">Toplam Test</span><span class="r-value">${ps.count}</span></div>
          <div class="report-stat"><span class="r-label">Uygun</span><span class="r-value" style="color:var(--green)">${ps.conforming}</span></div>
          <div class="report-stat"><span class="r-label">Uygunsuz</span><span class="r-value" style="color:var(--red)">${ps.non_conforming}</span></div>
          <div class="report-stat"><span class="r-label">Baypas Sorunu</span><span class="r-value" style="color:${ps.bypass_issues>0?'var(--red)':'var(--green)'}">${ps.bypass_issues}</span></div>
          <div class="report-stat"><span class="r-label">Yıkama Sorunu</span><span class="r-value" style="color:${ps.washing_issues>0?'var(--yellow)':'var(--green)'}">${ps.washing_issues}</span></div>
          <div class="report-stat"><span class="r-label">Uyum Oranı</span><span class="r-value" style="color:var(--accent)">%${ps.compliance_rate}</span></div>
          ${byTypePoll}
        </div>
      </div>
    </div>

    <div class="card mb-4">
      <div class="card-header"><span class="card-title">Uygunsuzluklar</span></div>
      <div class="card-body">${nonConformHtml}</div>
    </div>

    <div class="card">
      <div class="card-header"><span class="card-title">Öneriler & Aksiyonlar</span></div>
      <div class="card-body">${recsHtml}</div>
    </div>
  `;
}

async function saveReport() {
  const weekStart = document.getElementById('reportWeekStart').value;
  if (!weekStart) { toast('Rapor oluşturun', 'error'); return; }
  try {
    await fetch(`${API}/api/reports/weekly/save?week_start=${weekStart}`, { method: 'POST' });
    toast('Rapor kaydedildi', 'success');
  } catch { toast('Kayıt başarısız', 'error'); }
}

// ─── TRENDS ───────────────────────────────────────────────────
let trendChartInst = null;
let pollChartInst = null;

async function loadTrends() {
  const type = document.getElementById('trendAggType').value;
  const days = document.getElementById('trendDays').value;

  try {
    const [trendRes, pollRes] = await Promise.all([
      fetch(`${API}/api/dashboard/trend?aggregate_type=${type}&days=${days}`),
      fetch(`${API}/api/dashboard/pollution-trend?days=${days}`)
    ]);
    const trendData = await trendRes.json();
    const pollData = await pollRes.json();

    renderTrendChart(trendData.data, type);
    renderPollutionChart(pollData.data);
  } catch { toast('Trend verisi yüklenemedi', 'error'); }
}

function renderTrendChart(data, type) {
  const ctx = document.getElementById('trendChart').getContext('2d');
  if (trendChartInst) trendChartInst.destroy();

  if (!data.length) return;

  // Get all sieve sizes for this type
  const allSieves = Object.keys(SIEVE_LIMITS[type] || {});
  const colors = ['#4f9cf9','#22c55e','#f59e0b','#ef4444','#a78bfa','#fb923c','#34d399','#f472b6'];

  const datasets = allSieves.slice(0, 5).map((mm, i) => ({
    label: `${mm} mm`,
    data: data.map(d => d.sieve_results[mm] || null),
    borderColor: colors[i],
    backgroundColor: colors[i] + '22',
    tension: 0.3,
    pointRadius: 4,
    borderWidth: 2,
  }));

  const labels = data.map(d => new Date(d.test_date).toLocaleDateString('tr-TR', {day:'2-digit',month:'2-digit'}));

  trendChartInst = new Chart(ctx, {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true,
      plugins: {
        legend: { labels: { color: '#8892aa', font: { family: 'IBM Plex Mono', size: 11 } } },
        tooltip: { backgroundColor: '#141720', borderColor: '#252a38', borderWidth: 1 }
      },
      scales: {
        x: { ticks: { color: '#5a6480', font: { size: 11 } }, grid: { color: '#252a38' } },
        y: { ticks: { color: '#5a6480', font: { size: 11 } }, grid: { color: '#252a38' }, min: 0, max: 100 }
      }
    }
  });
}

function renderPollutionChart(data) {
  const ctx = document.getElementById('pollutionChart').getContext('2d');
  if (pollChartInst) pollChartInst.destroy();

  if (!data.length) return;

  const labels = data.map(d => new Date(d.test_date).toLocaleDateString('tr-TR', {day:'2-digit',month:'2-digit'}));

  pollChartInst = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        { label: 'MB (g/kg)', data: data.map(d => d.mb_value), backgroundColor: '#4f9cf944', borderColor: '#4f9cf9', borderWidth: 1 },
        { label: 'İnce Madde (%)', data: data.map(d => d.fine_content), backgroundColor: '#f59e0b44', borderColor: '#f59e0b', borderWidth: 1 },
      ]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { labels: { color: '#8892aa', font: { family: 'IBM Plex Mono', size: 11 } } },
        tooltip: { backgroundColor: '#141720', borderColor: '#252a38', borderWidth: 1 }
      },
      scales: {
        x: { ticks: { color: '#5a6480', font: { size: 11 } }, grid: { color: '#252a38' } },
        y: { ticks: { color: '#5a6480', font: { size: 11 } }, grid: { color: '#252a38' } }
      }
    }
  });
}

// ─── PAGINATION ───────────────────────────────────────────────
function renderPagination(containerId, total, currentPage, onPageClick) {
  const totalPages = Math.ceil(total / PAGE_SIZE);
  const container = document.getElementById(containerId);
  if (totalPages <= 1) { container.innerHTML = ''; return; }

  let html = '';
  const start = Math.max(0, currentPage - 2);
  const end = Math.min(totalPages - 1, currentPage + 2);

  if (currentPage > 0) html += `<button class="page-btn" onclick="(${onPageClick.toString()})(${currentPage-1})">‹</button>`;
  for (let i = start; i <= end; i++) {
    html += `<button class="page-btn ${i===currentPage?'active':''}" onclick="(${onPageClick.toString()})(${i})">${i+1}</button>`;
  }
  if (currentPage < totalPages - 1) html += `<button class="page-btn" onclick="(${onPageClick.toString()})(${currentPage+1})">›</button>`;

  container.innerHTML = html;
}

// ─── INIT ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // Set today's date as default
  const today = new Date().toISOString().split('T')[0];
  ['siTestDate', 'ptTestDate'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = today;
  });
  loadDashboard();
});
