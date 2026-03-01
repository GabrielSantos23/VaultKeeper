const pngToIco = require('png-to-ico');
const fs = require('fs');
const path = require('path');

const iconsDir = path.join(__dirname, '..', 'src-tauri', 'icons');

// Generate ICO from the largest PNG
async function generateIco() {
  try {
    const buf = await pngToIco(path.join(iconsDir, 'icon.png'));
    fs.writeFileSync(path.join(iconsDir, 'icon.ico'), buf);
    console.log('Created icon.ico');
  } catch (error) {
    console.error('Error creating ICO:', error);
  }
}

generateIco();
