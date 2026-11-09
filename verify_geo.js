const fs = require('fs');
const html = fs.readFileSync('C:/openwork/radarnote31/SCEL_ATC_Radar.html', 'utf8');

const SCEL_LAT = -33.3942, SCEL_LNG = -70.7856;
const COS = Math.cos(SCEL_LAT * Math.PI / 180);

function dms(v, isLat) {
  let a = Math.abs(v);
  let d = Math.floor(a);
  let mf = (a - d) * 60;
  let m = Math.floor(mf);
  let s = Math.round((mf - m) * 60);
  if (s === 60) { s = 0; m++; }
  if (m === 60) { m = 0; d++; }
  const h = v < 0 ? (isLat ? 'S' : 'W') : (isLat ? 'N' : 'E');
  return String(d).padStart(2, '0') + String(m).padStart(2, '0') + String(s).padStart(2, '0') + h;
}
function pretty(v, isLat) {
  let a = Math.abs(v), d = Math.floor(a), mf = (a - d) * 60, m = Math.floor(mf), s = Math.round((mf - m) * 60);
  if (s === 60) { s = 0; m++; } if (m === 60) { m = 0; d++; }
  const h = v < 0 ? (isLat ? 'S' : 'W') : (isLat ? 'N' : 'E');
  return d + '\u00b0' + String(m).padStart(2, '0') + "'" + String(s).padStart(2, '0') + '"' + h;
}
// parse DMS like 33\u00b023'34"S or 33\u00b025'11"S
function parseDMS(str) {
  const m = /(\d{1,3})\u00b0(\d{1,2})'(\d{1,2}(?:\.\d+)?)"/.exec(str);
  if (!m) return null;
  const sign = /S|W/.test(str) ? -1 : 1;
  return sign * (parseInt(m[1], 10) + parseInt(m[2], 10) / 60 + parseFloat(m[3]) / 3600);
}

console.log('=== SCEL_LAT / SCEL_LNG ===');
console.log('SCEL_LAT = ' + SCEL_LAT + '  ->  ' + pretty(SCEL_LAT, true) + '  (' + dms(SCEL_LAT, true) + ')');
console.log('published SCEL ARP = 33\u00b023\'34"S  = -33.3927778');
console.log('delta = ' + ((SCEL_LAT - (-33.3927778)) * 60).toFixed(2) + "' = " + ((SCEL_LAT - (-33.3927778)) * 60 * 60).toFixed(1) + '"  (' + ((SCEL_LAT - (-33.3927778)) * 60 * 1852).toFixed(0) + ' m)\n');

// ---- thresholds ----
const thr = {
  'THR17L': { x: -0.056, y: 1.088, aip: "33\u00b022'33.89\"S" },
  'THR35R': { x: 0.022, y: -0.641, aip: "33\u00b024'17.60\"S" },
  'THR17R': { x: -0.907, y: 1.335, aip: "33\u00b022'19.02\"S" },
  'THR35L': { x: -0.816, y: -0.719, aip: "33\u00b024'22.25\"S" },
};
console.log('=== RUNWAY THRESHOLDS: app readout vs AIP ===');
for (const [k, t] of Object.entries(thr)) {
  const lat = SCEL_LAT + t.y / 60;
  const aip = parseDMS(t.aip);
  const err = ((lat - aip) * 60); // arcmin
  console.log(k.padEnd(7) + ' y=' + String(t.y).padEnd(7) + ' readout=' + dms(lat, true).padEnd(9) +
    ' AIP=' + t.aip.padEnd(16) + ' err=' + (err >= 0 ? '+' : '') + (err * 60).toFixed(2) + '"');
}

// ---- AMB VOR ----
console.log('\n=== AMB (Santiago VOR/DME 116.1) ===');
const amb = { x: 0.06, y: -1.53 };
const ambLat = SCEL_LAT + amb.y / 60;
const ambLon = SCEL_LNG + amb.x / (60 * COS);
console.log('app  : lat=' + pretty(ambLat, true) + ' (' + dms(ambLat, true) + ')  lon=' + pretty(ambLon, false));
console.log('AIP  : 33\u00b025\'11"S 70\u00b047\'04"W   (OpenAIP: -33.419700, -70.784400)');
console.log('delta lat = ' + ((ambLat - (-33.4197)) * 60 * 60).toFixed(2) + '"');
console.log('AMB sits ' + Math.abs((ambLat - SCEL_LAT) * 60).toFixed(3) + "' (" + Math.abs((ambLat - SCEL_LAT) * 60 * 1852).toFixed(0) + ' m) SOUTH of app origin\n');

// ---- what y gives exactly 332509S ? ----
const target = -(33 + 25 / 60 + 9 / 3600);
const yNeeded = (target - SCEL_LAT) * 60;
console.log('=== 332509S corresponds to y = ' + yNeeded.toFixed(4) + ' NM (lat ' + target.toFixed(6) + ') ===');
console.log('AMB y = -1.53  -> readout ' + dms(ambLat, true) + '  (delta from 332509S = ' + ((ambLat - target) * 60 * 60).toFixed(1) + '")');
console.log('ARP y = 0      -> readout ' + dms(SCEL_LAT, true));
console.log('published ARP  -> 332334S  (y=' + ((-33.3927778 - SCEL_LAT) * 60).toFixed(3) + ' NM)\n');

// ---- scan NAVAIDS block for duplicate keys / any entry reading 332509S ----
const start = html.indexOf('const NAVAIDS = {');
const end = html.indexOf('\n};', start);
const block = html.slice(start, end);
console.log('=== NAVAIDS entries whose readout is 332508S-332510S ===');
let hits = 0;
const keyRe = /^\s*'?([A-Z0-9_]+)'?\s*:\s*\{x:\s*(-?[\d.]+)\s*,\s*y:\s*(-?[\d.]+)/gm;
let m;
const seen = new Map();
while ((m = keyRe.exec(block)) !== null) {
  const key = m[1], x = parseFloat(m[2]), y = parseFloat(m[3]);
  if (seen.has(key)) console.log('DUPLICATE KEY: ' + key + ' (first y=' + seen.get(key) + ', second y=' + y + ') -> last wins');
  seen.set(key, y);
  const lat = SCEL_LAT + y / 60;
  const s = dms(lat, true);
  if (s === '332508S' || s === '332509S' || s === '332510S') {
    console.log('  ' + key + '  y=' + y + '  -> ' + s);
    hits++;
  }
}
console.log('hits=' + hits + ', unique keys=' + seen.size);

// any key named AMB?
console.log('AMB entries: ' + [...seen.keys()].filter(k => k === 'AMB').length);

// ---- scan whole file for y values landing in 332509S window ----
console.log('\n=== any {x,y} literal in file landing in 332508S-332510S ===');
const pairRe = /\{x:\s*(-?[\d.]+)\s*,\s*y:\s*(-?[\d.]+)\s*[,}]/g;
let n = 0, found = 0;
while ((m = pairRe.exec(html)) !== null) {
  n++;
  const y = parseFloat(m[2]);
  const lat = SCEL_LAT + y / 60;
  const s = dms(lat, true);
  if (s === '332509S') {
    found++;
    if (found <= 12) console.log('  y=' + y + ' x=' + m[1] + ' -> ' + s + '  @' + m.index);
  }
}
console.log('scanned ' + n + ' {x,y} literals, ' + found + ' land on 332509S');
