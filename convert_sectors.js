const fs = require('fs');

const SCEL_LAT = -33.3942;
const SCEL_LNG = -70.7856;
const SCEL_COS = Math.cos(SCEL_LAT * Math.PI / 180); // 0.8349036

// Convert x,y (NM from SCEL) to lat,lon
function xyToLatLon(x, y) {
  const lon = SCEL_LNG + x / (60 * SCEL_COS);
  const lat = SCEL_LAT + y / 60;
  return [parseFloat(lat.toFixed(6)), parseFloat(lon.toFixed(6))];
}

// Read the file
const filePath = 'C:\\openwork\\radarnote31\\SCEL_ATC_Radar.html';
let content = fs.readFileSync(filePath, 'utf8');

// Find SECTOR_MIN definition
const sectorMinStart = content.indexOf('const SECTOR_MIN = {');
if (sectorMinStart === -1) {
  console.error('SECTOR_MIN not found');
  process.exit(1);
}

// Find the end of SECTOR_MIN (the closing };)
let braceCount = 0;
let inString = false;
let stringChar = '';
let i = sectorMinStart;
for (; i < content.length; i++) {
  const ch = content[i];
  if (inString) {
    if (ch === stringChar && content[i-1] !== '\\') {
      inString = false;
    }
  } else if (ch === '"' || ch === "'" || ch === '`') {
    inString = true;
    stringChar = ch;
  } else if (ch === '{') {
    braceCount++;
  } else if (ch === '}') {
    braceCount--;
    if (braceCount === 0) {
      i++; // include the closing }
      break;
    }
  }
}

const sectorMinEnd = i;
const sectorMinCode = content.substring(sectorMinStart, sectorMinEnd);

console.log('Found SECTOR_MIN, length:', sectorMinCode.length);

// Parse the SECTOR_MIN object
const sectorRegex = /(\w+):\s*\{[^}]*vertices:\s*\[([^\]]+)\]/g;
const sectors = {};

let match;
const tempCode = sectorMinCode;
while ((match = sectorRegex.exec(tempCode)) !== null) {
  const name = match[1];
  const verticesStr = match[2];
  
  // Parse vertices
  const vertexRegex = /\{x:\s*([-\d.]+),\s*y:\s*([-\d.]+)\}/g;
  const vertices = [];
  let vMatch;
  while ((vMatch = vertexRegex.exec(verticesStr)) !== null) {
    const x = parseFloat(vMatch[1]);
    const y = parseFloat(vMatch[2]);
    const [lat, lon] = xyToLatLon(x, y);
    vertices.push({lat, lon});
  }
  
  // Extract other properties
  const altMatch = tempCode.substring(match.index).match(/alt:\s*'([^']+)'/);
  const fillMatch = tempCode.substring(match.index).match(/fill:\s*'([^']+)'/);
  const strokeMatch = tempCode.substring(match.index).match(/stroke:\s*'([^']+)'/);
  
  sectors[name] = {
    name,
    alt: altMatch ? altMatch[1] : '',
    fill: fillMatch ? fillMatch[1] : 'rgba(0,180,90,.02)',
    stroke: strokeMatch ? strokeMatch[1] : 'rgba(0,200,100,.35)',
    vertices
  };
}

console.log('Parsed sectors:', Object.keys(sectors).length);

// Generate new SECTOR_MIN_LL (lat/long) and SECTOR_MIN_XY (computed)
let newCode = '// ════════════════════════════════════════════════════\n';
newCode += '//  SECTOR MINIMUM ALTITUDES — AIP Chile IAC\n';
newCode += '//  Coordenadas en LAT/LON (grados decimales)\n';
newCode += '//  Conversión: x=(lon-SCEL_LNG)*60*cos(SCEL_LAT), y=(lat-SCEL_LAT)*60\n';
newCode += '// ════════════════════════════════════════════════════\n';
newCode += 'const SECTOR_MIN_LL = {\n';

for (const [name, sector] of Object.entries(sectors)) {
  newCode += `  ${name}: {\n`;
  newCode += `    name: '${name}',\n`;
  newCode += `    alt: '${sector.alt}',\n`;
  newCode += `    fill: '${sector.fill}',\n`;
  newCode += `    stroke: '${sector.stroke}',\n`;
  newCode += `    vertices: [\n`;
  for (const v of sector.vertices) {
    newCode += `      {lat: ${v.lat}, lon: ${v.lon}},\n`;
  }
  newCode += `    ]\n`;
  newCode += `  },\n`;
}
newCode += '};\n\n';

// Generate SECTOR_MIN_XY computed from LL
newCode += 'const SECTOR_MIN_XY = {};\n';
newCode += '(function(){\n';
newCode += `  const _c = Math.cos(SCEL_LAT * Math.PI / 180);\n`;
newCode += `  Object.keys(SECTOR_MIN_LL).forEach(function(k){\n`;
newCode += `    const s = SECTOR_MIN_LL[k];\n`;
newCode += `    SECTOR_MIN_XY[k] = {\n`;
newCode += `      name: s.name,\n`;
newCode += `      alt: s.alt,\n`;
newCode += `      fill: s.fill,\n`;
newCode += `      stroke: s.stroke,\n`;
newCode += `      vertices: s.vertices.map(function(v){\n`;
newCode += `        return [(v.lon - SCEL_LNG) * 60 * _c, (v.lat - SCEL_LAT) * 60];\n`;
newCode += `      })\n`;
newCode += `    };\n`;
newCode += `  });\n`;
newCode += '})();\n\n';

// Alias for backward compatibility
newCode += 'const SECTOR_MIN = SECTOR_MIN_XY;\n';

console.log('Generated new code, length:', newCode.length);

// Replace the old SECTOR_MIN definition
const newContent = content.substring(0, sectorMinStart) + newCode + content.substring(sectorMinEnd);

// Write back
fs.writeFileSync(filePath, newContent, 'utf8');
console.log('File updated successfully');

// Also update netlify-deploy
fs.writeFileSync('C:\\openwork\\radarnote31\\netlify-deploy\\index.html', newContent, 'utf8');
console.log('Netlify deploy updated');