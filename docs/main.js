import maplibregl from 'maplibre-gl';

const LONG_ISLAND_CENTER = [-73.05, 40.84];
const LONG_ISLAND_ZOOM = 8.9;

const LISA_COLORS = {
  HH: '#d7191c',
  LL: '#2c7bb6',
  HL: '#fdae61',
  LH: '#abd9e9',
  ns: '#e0e0e0',
};

const RESOURCE_COLORS = {
  food: '#4f9a45',
  shelter: '#b45f06',
  outreach: '#674ea7',
  legal: '#1f78b4',
  housing_support: '#8c6d31',
  behavioral_health: '#c51b7d',
  public_benefits: '#00a6a6',
  health: '#6a51a3',
  other: '#666666',
};

const CONT_STOPS = {
  mismatch_index: [-2, 0, 2],
  need_score: [-2, 0, 2],
  access_index: [0, 50, 100],
  poverty_rate: [0, 0.1, 0.3],
};

const LAYER_LABELS = {
  mismatch_index: 'Mismatch index',
  need_score: 'Need score',
  access_index: 'Access index (0-100)',
  poverty_rate: 'Poverty rate',
};

const FACTOR_LABELS = {
  need_score: 'Need score',
  poverty_rate: 'Poverty rate',
  rent_burden_rate: 'Rent burden',
  renter_share: 'Renter share',
  mismatch_index: 'Mismatch index',
};

const PERCENT_FACTORS = new Set(['poverty_rate', 'rent_burden_rate', 'renter_share']);

let map;
let mode = 'drive';
let layerKey = 'lisa';
let tractsData = { drive: null, walk: null };
let facilitiesData = null;
let diagnostics = { drive: null, walk: null };
let districtsData = null;

async function loadAll() {
  const [td, tw, fac, dd, dw, dist] = await Promise.all([
    fetch('./tracts_drive_diagnostics.geojson').then(r => r.json()),
    fetch('./tracts_walk_diagnostics.geojson').then(r => r.json()),
    fetch('./longisland_facilities.geojson').then(r => r.json()),
    fetch('./diagnostics_drive.json').then(r => r.json()),
    fetch('./diagnostics_walk.json').then(r => r.json()),
    fetch('./homeless_students_districts.geojson').then(r => r.json()),
  ]);
  tractsData.drive = td;
  tractsData.walk = tw;
  facilitiesData = fac;
  diagnostics.drive = dd;
  diagnostics.walk = dw;
  districtsData = dist;
}

function initMap() {
  map = new maplibregl.Map({
    container: 'map',
    style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
    center: LONG_ISLAND_CENTER,
    zoom: LONG_ISLAND_ZOOM,
    maxZoom: 14,
    minZoom: 8,
  });
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-left');
  window.longIslandMap = map;
}

function addAllLayers() {
  map.addSource('tracts', { type: 'geojson', data: tractsData[mode] });
  map.addSource('facilities', { type: 'geojson', data: facilitiesData });
  map.addSource('districts', { type: 'geojson', data: districtsData });

  map.addLayer({
    id: 'tract-fill',
    type: 'fill',
    source: 'tracts',
    paint: { 'fill-color': lisaColorExpr(), 'fill-opacity': 0.7 },
  });
  map.addLayer({
    id: 'tract-hover',
    type: 'line',
    source: 'tracts',
    paint: { 'line-color': '#000', 'line-width': 2 },
    filter: ['==', 'GEOID', ''],
  });
  map.addLayer({
    id: 'tract-stroke',
    type: 'line',
    source: 'tracts',
    paint: { 'line-color': '#555', 'line-width': 0.25, 'line-opacity': 0.5 },
  });
  map.addLayer({
    id: 'districts-fill',
    type: 'fill',
    source: 'districts',
    layout: { visibility: 'none' },
    paint: {
      'fill-color': [
        'interpolate', ['linear'], ['get', 'homeless_k12_avg'],
        0, 'rgba(255,255,204,0.75)',
        50, 'rgba(254,217,118,0.75)',
        150, 'rgba(253,141,60,0.8)',
        400, 'rgba(240,59,32,0.85)',
        1300, 'rgba(128,0,38,0.9)',
      ],
      'fill-outline-color': '#333',
    },
  });
  map.addLayer({
    id: 'districts-stroke',
    type: 'line',
    source: 'districts',
    layout: { visibility: 'none' },
    paint: { 'line-color': '#222', 'line-width': 0.6, 'line-opacity': 0.7 },
  });
  map.addLayer({
    id: 'facilities-halo',
    type: 'circle',
    source: 'facilities',
    paint: {
      'circle-radius': [
        'interpolate', ['linear'], ['zoom'],
        8, ['case', ['==', ['get', 'is_access_resource'], true], 6.5, 5],
        13, ['case', ['==', ['get', 'is_access_resource'], true], 12, 8],
      ],
      'circle-color': '#ffffff',
      'circle-opacity': 0.9,
    },
  });
  map.addLayer({
    id: 'facilities',
    type: 'circle',
    source: 'facilities',
    paint: {
      'circle-radius': [
        'interpolate', ['linear'], ['zoom'],
        8, ['case', ['==', ['get', 'is_access_resource'], true], 4.8, 3.5],
        13, ['case', ['==', ['get', 'is_access_resource'], true], 9, 6],
      ],
      'circle-color': resourceColorExpr(),
      'circle-opacity': ['case', ['==', ['get', 'is_access_resource'], true], 0.96, 0.75],
      'circle-stroke-width': ['case', ['==', ['get', 'is_access_resource'], true], 1.4, 1],
      'circle-stroke-color': '#1f2937',
    },
  });

  map.on('click', 'tract-fill', (e) => showTractDetail(e.features[0]));
  map.on('mousemove', 'tract-fill', (e) => {
    const f = e.features[0];
    map.setFilter('tract-hover', ['==', 'GEOID', f.properties.GEOID]);
    map.getCanvas().style.cursor = 'pointer';
  });
  map.on('mouseleave', 'tract-fill', () => {
    map.setFilter('tract-hover', ['==', 'GEOID', '']);
    map.getCanvas().style.cursor = '';
  });

  map.on('click', 'districts-fill', (e) => {
    const p = e.features[0].properties;
    const avg = number(p.homeless_k12_avg, 0);
    const y2020 = number(p.homeless_k12_2020, 0);
    new maplibregl.Popup({ offset: 8, maxWidth: '280px' })
      .setLngLat(e.lngLat)
      .setHTML(
        `<strong>${escape(p.display_name)}</strong><br>
         <span class="muted">${escape(p.county_name || '')} school district</span><br>
         <span class="muted">McKinney-Vento 3-yr avg: <b>${avg}</b></span><br>
         <span class="muted">2020-21: ${y2020}</span><br>
         <span class="muted small">K-12 students identified as homeless at any point in the year. Includes doubled-up students and unaccompanied youth.</span>`
      )
      .addTo(map);
  });

  map.on('click', 'facilities', (e) => {
    const p = e.features[0].properties;
    const modeled = p.is_access_resource === true || p.is_access_resource === 'true'
      ? 'included in access score'
      : 'context layer only';
    new maplibregl.Popup({ offset: 10, maxWidth: '300px' })
      .setLngLat(e.features[0].geometry.coordinates)
      .setHTML(
        `<strong>${escape(p.name || '(unnamed)')}</strong><br>
         <span class="muted">${escape(p.county || '')} · ${escape(p.resource_group || p.type || '')}</span><br>
         <span class="muted">${escape(modeled)}</span><br>
         ${p.short_description ? `<span class="muted small">${escape(p.short_description)}</span>` : ''}`
      )
      .addTo(map);
  });
}

function lisaColorExpr() {
  return [
    'match', ['get', 'lisa_mismatch_index_label'],
    'HH', LISA_COLORS.HH,
    'LL', LISA_COLORS.LL,
    'HL', LISA_COLORS.HL,
    'LH', LISA_COLORS.LH,
    LISA_COLORS.ns,
  ];
}

function resourceColorExpr() {
  return [
    'match', ['get', 'resource_group'],
    'food', RESOURCE_COLORS.food,
    'shelter', RESOURCE_COLORS.shelter,
    'outreach', RESOURCE_COLORS.outreach,
    'legal', RESOURCE_COLORS.legal,
    'housing_support', RESOURCE_COLORS.housing_support,
    'behavioral_health', RESOURCE_COLORS.behavioral_health,
    'public_benefits', RESOURCE_COLORS.public_benefits,
    'health', RESOURCE_COLORS.health,
    RESOURCE_COLORS.other,
  ];
}

function continuousExpr(varName) {
  const [lo, mid, hi] = CONT_STOPS[varName];
  return [
    'case',
    ['==', ['get', varName], null], '#d0d0d0',
    ['interpolate', ['linear'], ['get', varName],
      lo, 'rgb(43,140,190)',
      mid, 'rgb(247,247,247)',
      hi, 'rgb(227,74,51)',
    ],
  ];
}

function wireUI() {
  document.querySelectorAll('.mode-switch button').forEach(btn => {
    btn.onclick = () => {
      if (btn.classList.contains('active')) return;
      document.querySelectorAll('.mode-switch button').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      mode = btn.dataset.mode;
      map.getSource('tracts').setData(tractsData[mode]);
      renderGate();
      renderLegend();
      renderCorrelation();
    };
  });

  document.querySelectorAll('input[name=layer]').forEach(r => {
    r.onchange = (e) => {
      layerKey = e.target.value;
      map.setPaintProperty(
        'tract-fill',
        'fill-color',
        layerKey === 'lisa' ? lisaColorExpr() : continuousExpr(layerKey),
      );
      renderLegend();
    };
  });

  document.getElementById('facilities-toggle').onchange = (e) => {
    const vis = e.target.checked ? 'visible' : 'none';
    map.setLayoutProperty('facilities-halo', 'visibility', vis);
    map.setLayoutProperty('facilities', 'visibility', vis);
  };

  document.getElementById('districts-toggle').onchange = (e) => {
    const vis = e.target.checked ? 'visible' : 'none';
    map.setLayoutProperty('districts-fill', 'visibility', vis);
    map.setLayoutProperty('districts-stroke', 'visibility', vis);
    map.setPaintProperty('tract-fill', 'fill-opacity', e.target.checked ? 0.25 : 0.7);
    renderLegend();
  };

  document.getElementById('factor-select').onchange = renderCorrelation;
}

function renderGate() {
  const g = diagnostics[mode].validation_gate;
  const verdictMap = {
    'mismatch-story-weak': 'Resources follow need by this mode',
    'mismatch-story-strong': 'Mismatch story has signal',
    'inconclusive': 'No clear spatial relation',
  };
  document.getElementById('gate-verdict').textContent = verdictMap[g.verdict] || g.verdict;
  document.getElementById('gate-text').textContent = g.interpretation;
}

function renderLegend() {
  const el = document.getElementById('legend-body');
  const districtsOn = document.getElementById('districts-toggle')?.checked;
  let html = '';
  if (districtsOn) {
    html += `
      <div class="legend-row"><span><b>K-12 homeless students</b> <span class="muted">3-yr avg 2018-21</span></span></div>
      <div class="gradient" style="background:linear-gradient(to right,
        rgb(255,255,204), rgb(254,217,118), rgb(253,141,60), rgb(240,59,32), rgb(128,0,38));"></div>
      <div class="gradient-labels"><span>0</span><span>50</span><span>150</span><span>400</span><span>1300+</span></div>
      <hr style="border:none;border-top:1px solid var(--border);margin:10px 0;">
    `;
  }
  if (layerKey === 'lisa') {
    const counts = diagnostics[mode].lisa_counts.mismatch_index || {};
    html += [
      ['HH', 'high need / low access (cluster)'],
      ['LL', 'low need / high access (cluster)'],
      ['HL', 'outlier: high need, low-need neighbours'],
      ['LH', 'outlier: low need, high-need neighbours'],
      ['ns', 'not significant'],
    ].map(([k, label]) => `
      <div class="legend-row">
        <span class="swatch" style="background:${LISA_COLORS[k]}"></span>
        <span>${k} <span class="muted">${label}</span></span>
        <span class="muted" style="margin-left:auto">${counts[k] ?? 0}</span>
      </div>`).join('');
  } else {
    const [lo, mid, hi] = CONT_STOPS[layerKey];
    html += `
      <div class="legend-row"><span>${LAYER_LABELS[layerKey] || layerKey}</span></div>
      <div class="gradient"></div>
      <div class="gradient-labels">
        <span>${lo}</span><span>${mid}</span><span>${hi}</span>
      </div>`;
  }
  html += `
    <hr style="border:none;border-top:1px solid var(--border);margin:10px 0;">
    <div class="legend-row"><span><b>Resources</b> <span class="muted">larger dots enter access score</span></span></div>
    ${Object.entries(RESOURCE_COLORS).map(([k, color]) => `
      <div class="legend-row">
        <span class="swatch circle" style="background:${color}"></span>
        <span>${labelize(k)}</span>
      </div>`).join('')}`;
  el.innerHTML = html;
}

function renderCorrelation() {
  const svg = document.getElementById('corr-chart');
  const stat = document.getElementById('corr-stat');
  const note = document.getElementById('corr-note');
  const factor = document.getElementById('factor-select').value;
  const label = FACTOR_LABELS[factor] || factor;
  const rows = (tractsData[mode]?.features || [])
    .map(f => ({
      x: Number(f.properties[factor]),
      y: Number(f.properties.access_index),
    }))
    .filter(d => Number.isFinite(d.x) && Number.isFinite(d.y));

  if (!rows.length) {
    stat.textContent = 'No tract data';
    note.textContent = 'This comparison is unavailable for the selected mode.';
    svg.innerHTML = '';
    return;
  }

  const w = 304;
  const h = 190;
  const m = { top: 12, right: 10, bottom: 34, left: 34 };
  const xVals = rows.map(d => d.x);
  const yVals = rows.map(d => d.y);
  let xMin = Math.min(...xVals);
  let xMax = Math.max(...xVals);
  if (xMin === xMax) {
    xMin -= 1;
    xMax += 1;
  }
  const yMin = 0;
  const yMax = Math.max(100, Math.max(...yVals));
  const sx = x => m.left + ((x - xMin) / (xMax - xMin)) * (w - m.left - m.right);
  const sy = y => h - m.bottom - ((y - yMin) / (yMax - yMin)) * (h - m.top - m.bottom);
  const r = pearson(rows);
  const fit = linearFit(rows);
  const yA = clamp(fit.intercept + fit.slope * xMin, yMin, yMax);
  const yB = clamp(fit.intercept + fit.slope * xMax, yMin, yMax);
  const pointStep = Math.max(1, Math.ceil(rows.length / 500));
  const points = rows
    .filter((_, i) => i % pointStep === 0)
    .map(d => `<circle class="corr-point" cx="${sx(d.x).toFixed(1)}" cy="${sy(d.y).toFixed(1)}" r="2.1"></circle>`)
    .join('');

  stat.textContent = `Access index vs ${label}: r = ${r.toFixed(2)} · n = ${rows.length}`;
  note.textContent = correlationNote(factor, r);
  svg.innerHTML = `
    <title id="corr-title">Access index compared with ${escape(label)}</title>
    <desc id="corr-desc">Scatter plot of ${rows.length} longisland census tracts. Y axis is access index from zero to one hundred. X axis is ${escape(label)}.</desc>
    <line class="corr-grid" x1="${m.left}" x2="${w - m.right}" y1="${sy(50)}" y2="${sy(50)}"></line>
    <line class="corr-axis" x1="${m.left}" x2="${m.left}" y1="${m.top}" y2="${h - m.bottom}"></line>
    <line class="corr-axis" x1="${m.left}" x2="${w - m.right}" y1="${h - m.bottom}" y2="${h - m.bottom}"></line>
    ${points}
    <line class="corr-line" x1="${sx(xMin).toFixed(1)}" y1="${sy(yA).toFixed(1)}" x2="${sx(xMax).toFixed(1)}" y2="${sy(yB).toFixed(1)}"></line>
    <text class="corr-label" x="${m.left}" y="${h - 8}">${escape(formatFactor(factor, xMin))}</text>
    <text class="corr-label" x="${w - m.right}" y="${h - 8}" text-anchor="end">${escape(formatFactor(factor, xMax))}</text>
    <text class="corr-label" x="4" y="${sy(100) + 3}">100</text>
    <text class="corr-label" x="8" y="${sy(0)}">0</text>
    <text class="corr-label" x="${w - m.right}" y="${m.top + 9}" text-anchor="end">Access index</text>
  `;
}

function showTractDetail(feat) {
  const p = feat.properties;
  const body = document.getElementById('detail-body');
  document.getElementById('tract-detail').classList.remove('empty');
  body.innerHTML = `
    <table>
      <tr><td>County</td><td>${escape(p.county_name)}</td></tr>
      <tr><td>GEOID</td><td>${escape(p.GEOID)}</td></tr>
      <tr><td>LISA (mismatch)</td><td><strong style="color:${LISA_COLORS[p.lisa_mismatch_index_label] || '#000'}">${p.lisa_mismatch_index_label}</strong></td></tr>
      <tr><td>Mismatch percentile</td><td>${number(p.mismatch_pct, 0)}</td></tr>
      <tr><td>Mismatch index</td><td>${number(p.mismatch_index)}</td></tr>
      <tr><td>Need score</td><td>${number(p.need_score)}</td></tr>
      <tr><td>Access index</td><td>${number(p.access_index, 0)}</td></tr>
      <tr><td>Raw access score</td><td>${number(p.access_score, 4)}</td></tr>
    </table>
    <h3>ACS context</h3>
    <table>
      <tr><td>Poverty rate</td><td>${percent(p.poverty_rate)}</td></tr>
      <tr><td>Rent burden (>=30%)</td><td>${percent(p.rent_burden_rate)}</td></tr>
      <tr><td>Renter share</td><td>${percent(p.renter_share)}</td></tr>
      <tr><td>Median HH income</td><td>${p.median_hh_inc ? '$' + (+p.median_hh_inc).toLocaleString() : '—'}</td></tr>
      <tr><td>Total population</td><td>${p.pop_total ? (+p.pop_total).toLocaleString() : '—'}</td></tr>
    </table>
  `;
}

function percent(x, d = 1) {
  return (x == null || isNaN(x)) ? '—' : (x * 100).toFixed(d) + '%';
}

function number(x, d = 2) {
  return (x == null || isNaN(x)) ? '—' : (+x).toFixed(d);
}

function pearson(rows) {
  const n = rows.length;
  const mx = rows.reduce((a, d) => a + d.x, 0) / n;
  const my = rows.reduce((a, d) => a + d.y, 0) / n;
  let num = 0;
  let dx = 0;
  let dy = 0;
  rows.forEach(d => {
    const vx = d.x - mx;
    const vy = d.y - my;
    num += vx * vy;
    dx += vx * vx;
    dy += vy * vy;
  });
  return dx && dy ? num / Math.sqrt(dx * dy) : 0;
}

function linearFit(rows) {
  const n = rows.length;
  const mx = rows.reduce((a, d) => a + d.x, 0) / n;
  const my = rows.reduce((a, d) => a + d.y, 0) / n;
  let num = 0;
  let den = 0;
  rows.forEach(d => {
    num += (d.x - mx) * (d.y - my);
    den += (d.x - mx) ** 2;
  });
  const slope = den ? num / den : 0;
  return { slope, intercept: my - slope * mx };
}

function correlationNote(factor, r) {
  if (factor === 'mismatch_index') {
    return 'Critical check: mismatch already includes access, so a negative relationship is expected. Use this as a sanity check, not as independent proof.';
  }
  if (Math.abs(r) < 0.15) {
    return 'Critical reading: weak correlation. Resource access is not strongly aligned with this factor, so local gaps deserve closer review.';
  }
  if (r > 0) {
    return 'Critical reading: access rises with this factor, but the relationship is not enough by itself; clusters and outliers still show where optimization matters.';
  }
  return 'Critical reading: higher need appears associated with lower access. That supports a stronger social-responsibility critique.';
}

function formatFactor(factor, x) {
  return PERCENT_FACTORS.has(factor) ? percent(x, 0) : number(x, 1);
}

function clamp(x, lo, hi) {
  return Math.max(lo, Math.min(hi, x));
}

function labelize(s) {
  return s.replaceAll('_', ' ');
}

function escape(s) {
  return String(s ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

(async () => {
  initMap();
  const dataReady = loadAll();
  const mapReady = new Promise(res => {
    if (map.loaded()) res();
    else map.once('load', res);
  });
  await Promise.all([dataReady, mapReady]);
  addAllLayers();
  wireUI();
  renderGate();
  renderLegend();
  renderCorrelation();
})();
