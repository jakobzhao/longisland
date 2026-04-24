import maplibregl from 'maplibre-gl';

const NASSAU_CENTER = [-73.58, 40.73];
const NASSAU_ZOOM = 10.4;

const LISA_COLORS = {
  HH: '#d7191c',
  LL: '#2c7bb6',
  HL: '#fdae61',
  LH: '#abd9e9',
  ns: '#e0e0e0',
};

const FACILITY_COLORS = {
  food_pantry: '#6aa84f',
  food_bank:   '#38761d',
  shelter:     '#b45f06',
  outreach:    '#674ea7',
  other:       '#666',
};

const CONT_STOPS = {
  mismatch_index: [-2, 0, 2],
  need_score:     [-2, 0, 2],
  access_score:   [0, 5, 20],
  poverty_rate:   [0, 0.1, 0.3],
};

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
    fetch('./nassau_facilities.geojson').then(r => r.json()),
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
    center: NASSAU_CENTER,
    zoom: NASSAU_ZOOM,
    maxZoom: 14,
    minZoom: 9,
  });
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-left');
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
        0,   'rgba(255,255,204,0.75)',
        50,  'rgba(254,217,118,0.75)',
        150, 'rgba(253,141,60,0.8)',
        400, 'rgba(240,59,32,0.85)',
        1300,'rgba(128,0,38,0.9)',
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
    id: 'facilities',
    type: 'circle',
    source: 'facilities',
    paint: {
      'circle-radius': ['interpolate', ['linear'], ['zoom'], 9, 2.5, 13, 5],
      'circle-color': [
        'match', ['get', 'type'],
        'food_pantry', FACILITY_COLORS.food_pantry,
        'food_bank',   FACILITY_COLORS.food_bank,
        'shelter',     FACILITY_COLORS.shelter,
        'outreach',    FACILITY_COLORS.outreach,
        FACILITY_COLORS.other,
      ],
      'circle-stroke-width': 1,
      'circle-stroke-color': '#fff',
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
    const avg = (+p.homeless_k12_avg).toFixed(0);
    const y2020 = (+p.homeless_k12_2020).toFixed(0);
    new maplibregl.Popup({ offset: 8, maxWidth: '280px' })
      .setLngLat(e.lngLat)
      .setHTML(
        `<strong>${escape(p.display_name)}</strong><br>
         <span class="muted">McKinney-Vento 3-yr avg: <b>${avg}</b></span><br>
         <span class="muted">2020-21: ${y2020}</span><br>
         <span class="muted small">K-12 students identified as homeless at any point in the year (NYSED SIRS). Includes unaccompanied youth (~10-12% nationally).</span>`
      )
      .addTo(map);
  });

  map.on('click', 'facilities', (e) => {
    const p = e.features[0].properties;
    new maplibregl.Popup({ offset: 10 })
      .setLngLat(e.features[0].geometry.coordinates)
      .setHTML(
        `<strong>${escape(p.name || '(unnamed)')}</strong><br>
         <span class="muted">${escape(p.type || '')} · ${escape(p.source || '')}</span>`
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
    };
  });

  document.querySelectorAll('input[name=layer]').forEach(r => {
    r.onchange = (e) => {
      layerKey = e.target.value;
      if (layerKey === 'lisa') {
        map.setPaintProperty('tract-fill', 'fill-color', lisaColorExpr());
      } else {
        map.setPaintProperty('tract-fill', 'fill-color', continuousExpr(layerKey));
      }
      renderLegend();
    };
  });

  document.getElementById('facilities-toggle').onchange = (e) => {
    map.setLayoutProperty('facilities', 'visibility',
      e.target.checked ? 'visible' : 'none');
  };

  document.getElementById('districts-toggle').onchange = (e) => {
    const vis = e.target.checked ? 'visible' : 'none';
    map.setLayoutProperty('districts-fill', 'visibility', vis);
    map.setLayoutProperty('districts-stroke', 'visibility', vis);
    map.setPaintProperty('tract-fill', 'fill-opacity',
      e.target.checked ? 0.25 : 0.7);
    renderLegend();
  };
}

function renderGate() {
  const g = diagnostics[mode].validation_gate;
  const verdictMap = {
    'mismatch-story-weak':   'Services already follow need',
    'mismatch-story-strong': 'Mismatch story has signal',
    'inconclusive':          'No clear spatial relation',
  };
  document.getElementById('gate-verdict').textContent =
    verdictMap[g.verdict] || g.verdict;
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
      <div class="legend-row"><span>${layerKey}</span></div>
      <div class="gradient"></div>
      <div class="gradient-labels">
        <span>${lo}</span><span>${mid}</span><span>${hi}</span>
      </div>`;
  }
  el.innerHTML = html;
}

function showTractDetail(feat) {
  const p = feat.properties;
  const pct = (x, d=1) => (x == null || isNaN(x)) ? '—' : (x * 100).toFixed(d) + '%';
  const num = (x, d=2) => (x == null || isNaN(x)) ? '—' : (+x).toFixed(d);
  const body = document.getElementById('detail-body');
  document.getElementById('tract-detail').classList.remove('empty');
  body.innerHTML = `
    <table>
      <tr><td>GEOID</td><td>${escape(p.GEOID)}</td></tr>
      <tr><td>LISA (mismatch)</td><td><strong style="color:${LISA_COLORS[p.lisa_mismatch_index_label] || '#000'}">${p.lisa_mismatch_index_label}</strong></td></tr>
      <tr><td>Mismatch percentile</td><td>${num(p.mismatch_pct, 0)}</td></tr>
      <tr><td>Mismatch index</td><td>${num(p.mismatch_index)}</td></tr>
      <tr><td>Need score</td><td>${num(p.need_score)}</td></tr>
      <tr><td>Access score</td><td>${num(p.access_score)}</td></tr>
    </table>
    <h3>ACS context</h3>
    <table>
      <tr><td>Poverty rate</td><td>${pct(p.poverty_rate)}</td></tr>
      <tr><td>Rent burden (≥30%)</td><td>${pct(p.rent_burden_rate)}</td></tr>
      <tr><td>Renter share</td><td>${pct(p.renter_share)}</td></tr>
      <tr><td>Median HH income</td><td>${p.median_hh_inc ? '$' + (+p.median_hh_inc).toLocaleString() : '—'}</td></tr>
      <tr><td>Total population</td><td>${p.pop_total ? (+p.pop_total).toLocaleString() : '—'}</td></tr>
    </table>
  `;
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
})();
