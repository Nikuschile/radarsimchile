const fs = require('fs');

const filePath = 'C:\\openwork\\radarnote31\\SCEL_ATC_Radar.html';
let content = fs.readFileSync(filePath, 'utf8');

// Fix unescaped double quotes in DMS strings
// Pattern: dms: "XX°XX'XX"X XX°XX'XX"X" -> dms: "XX°XX'XX\"X XX°XX'XX\"X"
let fixed = content.replace(/dms:\s*"([^"]*)"([NS])\s+([^"]*)"([EW])"/g, 
  (match, latPart, latHemi, lonPart, lonHemi) => {
    return `dms: "${latPart}\\"${latHemi} ${lonPart}\\"${lonHemi}"`;
  });

// Also fix THR_LL
fixed = fixed.replace(/dms:\s*"([^"]*)"([NS])\s+([^"]*)"([EW])"/g, 
  (match, latPart, latHemi, lonPart, lonHemi) => {
    return `dms: "${latPart}\\"${latHemi} ${lonPart}\\"${lonHemi}"`;
  });

// Count fixes
const matches = content.match(/dms:\s*"([^"]*)"([NS])\s+([^"]*)"([EW])"/g);
console.log('Found', matches ? matches.length : 0, 'DMS strings to fix');

if (fixed !== content) {
  fs.writeFileSync(filePath, fixed, 'utf8');
  console.log('Fixed escaping in SCEL_ATC_Radar.html');
  
  // Also update netlify-deploy
  fs.writeFileSync('C:\\openwork\\radarnote31\\netlify-deploy\\index.html', fixed, 'utf8');
  console.log('Fixed escaping in netlify-deploy/index.html');
} else {
  console.log('No changes needed');
}