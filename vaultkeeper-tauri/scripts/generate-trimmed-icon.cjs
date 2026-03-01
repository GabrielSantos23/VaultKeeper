const sharp = require('sharp');
const path = require('path');

const inputFile = path.join(__dirname, '..', 'public', 'logo.png');
const trimmedFile = path.join(__dirname, '..', 'public', 'logo-trimmed.png');
const outputFile = path.join(__dirname, '..', 'src-tauri', 'icons', 'icon.png');

async function generateTrimmedIcon() {
  try {
    // First, trim the original logo to remove excess transparent space
    const trimmed = await sharp(inputFile)
      .trim() // This removes transparent pixels from edges
      .toFile(trimmedFile);
    
    console.log(`Created trimmed logo: ${trimmedFile}`);
    
    // Get the trimmed image info
    const metadata = await sharp(trimmedFile).metadata();
    console.log(`Trimmed size: ${metadata.width}x${metadata.height}`);
    
    // Now create the final icon with the trimmed logo, adding small padding
    const targetSize = 512;
    const padding = 30; // Small padding around the trimmed logo
    
    // Resize to fit within the target size with padding
    const maxLogoSize = targetSize - (padding * 2);
    
    await sharp(trimmedFile)
      .resize(maxLogoSize, maxLogoSize, { 
        fit: 'inside',
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
    
    console.log(`Created final icon: ${outputFile}`);
  } catch (error) {
    console.error('Error creating icon:', error);
    process.exit(1);
  }
}

generateTrimmedIcon();
