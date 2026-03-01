const sharp = require('sharp');
const path = require('path');

const inputFile = path.join(__dirname, '..', 'public', 'logo-square.png');
const outputFile = path.join(__dirname, '..', 'src-tauri', 'icons', 'icon.png');

// Create a larger icon with the logo taking up more space (less padding)
async function generateLargeIcon() {
  try {
    // Create a 512x512 image with minimal padding so logo is larger
    const padding = 20; // Very small padding so logo fills more space
    
    await sharp(inputFile)
      .resize(512 - (padding * 2), 512 - (padding * 2), { 
        fit: 'contain',
        background: { r: 0, g: 0, b: 0, alpha: 0 }
      })
      .extend({
        top: padding,
        bottom: padding,
        left: padding,
        right: padding,
        background: { r: 0, g: 0, b: 0, alpha: 0 }
      })
      .toFile(outputFile);
    
    console.log(`Created large icon: ${outputFile}`);
  } catch (error) {
    console.error('Error creating icon:', error);
    process.exit(1);
  }
}

generateLargeIcon();
