const fs = require('fs');

const SCEL_LAT = -33.3942;
const SCEL_LNG = -70.7856;
const SCEL_COS = Math.cos(SCEL_LAT * Math.PI / 180); // 0.8349036

// Convert x,y (NM from SCEL) to lat,lon decimal
function xyToLatLon(x, y) {
  const lon = SCEL_LNG + x / (60 * SCEL_COS);
  const lat = SCEL_LAT + y / 60;
  return [lat, lon];
}

// Convert decimal degrees to DMS string: "33°23'39\"S 70°47'08\"W" (with escaped quotes for JS)
function decToDMS(lat, lon) {
  const latSign = lat < 0 ? 'S' : 'N';
  const lonSign = lon < 0 ? 'W' : 'E';
  const latAbs = Math.abs(lat);
  const lonAbs = Math.abs(lon);
  
  const latDeg = Math.floor(latAbs);
  const latMinFloat = (latAbs - latDeg) * 60;
  const latMin = Math.floor(latMinFloat);
  const latSec = Math.round((latMinFloat - latMin) * 60);
  
  const lonDeg = Math.floor(lonAbs);
  const lonMinFloat = (lonAbs - lonDeg) * 60;
  const lonMin = Math.floor(lonMinFloat);
  const lonSec = Math.round((lonMinFloat - lonMin) * 60);
  
  // Handle rounding overflow
  let latSecAdj = latSec, latMinAdj = latMin, latDegAdj = latDeg;
  if (latSecAdj >= 60) { latSecAdj = 0; latMinAdj++; }
  if (latMinAdj >= 60) { latMinAdj = 0; latDegAdj++; }
  
  let lonSecAdj = lonSec, lonMinAdj = lonMin, lonDegAdj = lonDeg;
  if (lonSecAdj >= 60) { lonSecAdj = 0; lonMinAdj++; }
  if (lonMinAdj >= 60) { lonMinAdj = 0; lonDegAdj++; }
  
  // Return with escaped quotes for JavaScript string
  return `${latDegAdj}°${String(latMinAdj).padStart(2,'0')}'${String(latSecAdj).padStart(2,'0')}\"${latSign} ${lonDegAdj}°${String(lonMinAdj).padStart(2,'0')}'${String(lonSecAdj).padStart(2,'0')}\"${lonSign}`;
}

// Read the file
const filePath = 'C:\\openwork\\radarnote31\\SCEL_ATC_Radar.html';
let content = fs.readFileSync(filePath, 'utf8');

// ============================================================
// 1. Convert WPT (waypoints) from x,y to DMS lat/long
// ============================================================
const wptStart = content.indexOf('const WPT = {');
if (wptStart === -1) {
  console.error('WPT not found');
  process.exit(1);
}

// Find end of WPT object
let braceCount = 0;
let inString = false;
let stringChar = '';
let i = wptStart;
for (; i < content.length; i++) {
  const ch = content[i];
  if (inString) {
    if (ch === stringChar && content[i-1] !== '\\') inString = false;
  } else if (ch === '"' || ch === "'" || ch === '`') {
    inString = true; stringChar = ch;
  } else if (ch === '{') braceCount++;
  else if (ch === '}') { braceCount--; if (braceCount === 0) { i++; break; } }
}
const wptEnd = i;
const wptCode = content.substring(wptStart, wptEnd);

console.log('Found WPT, length:', wptCode.length);

// Parse WPT entries
const wptRegex = /(\w+):\s*\{x:\s*([-\d.]+),\s*y:\s*([-\d.]+),\s*alt:\s*(\d+)\}/g;
const wpts = {};
let match;
while ((match = wptRegex.exec(wptCode)) !== null) {
  const name = match[1];
  const x = parseFloat(match[2]);
  const y = parseFloat(match[3]);
  const alt = parseInt(match[4]);
  const [lat, lon] = xyToLatLon(x, y);
  const dms = decToDMS(lat, lon);
  wpts[name] = {x, y, alt, lat, lon, dms};
}

console.log('Parsed WPT entries:', Object.keys(wpts).length);

// Generate new WPT_LL (DMS format) and WPT_XY (computed)
let newWptCode = '// ════════════════════════════════════════════════════\n';
newWptCode += '//  WAYPOINTS — SCEL AIP Chile AMDT 102 · 14 MAY 2026\n';
newWptCode += '//  Coordenadas en DMS (grados minutos segundos) — fuente oficial AIP\n';
newWptCode += '//  Conversión: x=(lon-SCEL_LNG)*60*cos(SCEL_LAT), y=(lat-SCEL_LAT)*60\n';
newWptCode += '// ════════════════════════════════════════════════════\n';
newWptCode += 'const WPT_LL = {\n';

for (const [name, w] of Object.entries(wpts)) {
  newWptCode += `  ${name}: {lat: ${w.lat.toFixed(6)}, lon: ${w.lon.toFixed(6)}, alt: ${w.alt}, dms: "${w.dms}"},\n`;
}
newWptCode += '};\n\n';

// Generate WPT_XY computed from LL
newWptCode += 'const WPT_XY = {};\n';
newWptCode += '(function(){\n';
newWptCode += `  const _c = Math.cos(SCEL_LAT * Math.PI / 180);\n`;
newWptCode += `  Object.keys(WPT_LL).forEach(function(k){\n`;
newWptCode += `    const w = WPT_LL[k];\n`;
newWptCode += `    WPT_XY[k] = {x: (w.lon - SCEL_LNG) * 60 * _c, y: (w.lat - SCEL_LAT) * 60, alt: w.alt, dms: w.dms};\n`;
newWptCode += `  });\n`;
newWptCode += '})();\n\n';

// Alias for backward compatibility
newWptCode += 'const WPT = WPT_XY;\n';

// ============================================================
// 2. Convert THR (runway thresholds) to DMS
// ============================================================
// Find the 4 THR const lines
const thr17lMatch = content.match(/const THR17L_X=([-\d.]+),\s*THR17L_Y=([-\d.]+);/);
const thr35rMatch = content.match(/const THR35R_X=([-\d.]+),\s*THR35R_Y=([-\d.]+);/);
const thr17rMatch = content.match(/const THR17R_X=([-\d.]+),\s*THR17R_Y=([-\d.]+);/);
const thr35lMatch = content.match(/const THR35L_X=([-\d.]+),\s*THR35L_Y=([-\d.]+);/);

if (!thr17lMatch || !thr35rMatch || !thr17rMatch || !thr35lMatch) {
  console.error('Could not parse THR coordinates');
  process.exit(1);
}

const thrCoords = {
  THR17L: {x: parseFloat(thr17lMatch[1]), y: parseFloat(thr17lMatch[2])},
  THR35R: {x: parseFloat(thr35rMatch[1]), y: parseFloat(thr35rMatch[2])},
  THR17R: {x: parseFloat(thr17rMatch[1]), y: parseFloat(thr17rMatch[2])},
  THR35L: {x: parseFloat(thr35lMatch[1]), y: parseFloat(thr35lMatch[2])}
};

const thrLL = {};
for (const [name, coord] of Object.entries(thrCoords)) {
  const [lat, lon] = xyToLatLon(coord.x, coord.y);
  const dms = decToDMS(lat, lon);
  thrLL[name] = {x: coord.x, y: coord.y, lat, lon, dms};
}

console.log('THR coordinates converted to DMS:');
for (const [name, t] of Object.entries(thrLL)) {
  console.log(`  ${name}: ${t.dms} (x=${t.x}, y=${t.y})`);
}

// Generate new THR block with DMS
let newThrCode = '// ════════════════════════════════════════════════════\n';
newThrCode += '//  RUNWAY THRESHOLDS — SCEL AIP Chile\n';
newThrCode += '//  Coordenadas en DMS (grados minutos segundos) — fuente oficial AIP\n';
newThrCode += '//  Conversión: x=(lon-SCEL_LNG)*60*cos(SCEL_LAT), y=(lat-SCEL_LAT)*60\n';
newThrCode += '// ════════════════════════════════════════════════════\n';
newThrCode += 'const THR_LL = {\n';
for (const [name, t] of Object.entries(thrLL)) {
  newThrCode += `  ${name}: {lat: ${t.lat.toFixed(6)}, lon: ${t.lon.toFixed(6)}, dms: "${t.dms}"},\n`;
}
newThrCode += '};\n\n';

newThrCode += 'const THR_XY = {};\n';
newThrCode += '(function(){\n';
newThrCode += `  const _c = Math.cos(SCEL_LAT * Math.PI / 180);\n`;
newThrCode += `  Object.keys(THR_LL).forEach(function(k){\n`;
newThrCode += `    const t = THR_LL[k];\n`;
newThrCode += `    THR_XY[k] = {x: (t.lon - SCEL_LNG) * 60 * _c, y: (t.lat - SCEL_LAT) * 60, dms: t.dms};\n`;
newThrCode += `  });\n`;
newThrCode += '})();\n\n';

// Backward compatibility aliases
newThrCode += 'const THR17L_X = THR_XY.THR17L.x, THR17L_Y = THR_XY.THR17L.y;\n';
newThrCode += 'const THR35R_X = THR_XY.THR35R.x, THR35R_Y = THR_XY.THR35R.y;\n';
newThrCode += 'const THR17R_X = THR_XY.THR17R.x, THR17R_Y = THR_XY.THR17R.y;\n';
newThrCode += 'const THR35L_X = THR_XY.THR35L.x, THR35L_Y = THR_XY.THR35L.y;\n';

// ============================================================
// Replace WPT in content
// ============================================================
let newContent = content.substring(0, wptStart) + newWptCode + content.substring(wptEnd);

// Replace THR block (4 lines)
const thrStart = content.indexOf('const THR17L_X=');
const thrEnd = content.indexOf('const FAF_DIST_NM=', thrStart);
newContent = newContent.substring(0, thrStart) + newThrCode + newContent.substring(thrEnd);

// Write back
fs.writeFileSync(filePath, newContent, 'utf8');
console.log('File updated successfully');

// Also update netlify-deploy
fs.writeFileSync('C:\\openwork\\radarnote31\\netlify-deploy\\index.html', newContent, 'utf8');
console.log('Netlify deploy updated');