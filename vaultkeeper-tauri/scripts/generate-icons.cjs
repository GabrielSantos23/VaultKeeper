const { execSync } = require('child_process');
const sharp = require('sharp');
const path = require('path');
const fs = require('fs');

const inputFile = path.join(__dirname, '..', 'public', 'logo-square.png');
const iconsDir = path.join(__dirname, '..', 'src-tauri', 'icons');

// Ensure icons directory exists
if (!fs.existsSync(iconsDir)) {
  fs.mkdirSync(iconsDir, { recursive: true });
}

// PNG sizes for Tauri
const pngSizes = [32, 64, 128, 256, 512];

async function generateIcons() {
  console.log('Generating PNG icons...');
  
  // Generate PNG icons
  for (const size of pngSizes) {
    const outputFile = path.join(iconsDir, size === 128 ? '128x128.png' : size === 256 ? 'icon.png' : `${size}x${size}.png`);
    await sharp(inputFile)
      .resize(size, size, { fit: 'cover' })
      .toFile(outputFile);
    console.log(`Created ${size}x${size}.png`);
  }
  
  // Create 128x128@2x.png (256px for Retina)
  await sharp(inputFile)
    .resize(256, 256, { fit: 'cover' })
    .toFile(path.join(iconsDir, '128x128@2x.png'));
  console.log('Created 128x128@2x.png');
  
  console.log('\nIcon generation complete!');
  console.log('Note: For best results on Windows, use a tool like icofx or Greenfish Icon Editor');
  console.log('to create a multi-resolution .ico file with sizes: 16, 32, 48, 64, 128, 256');
}

generateIcons().catch(console.error);
