import sharp from 'sharp';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const rootDir = dirname(__dirname);

const inputPath = join(rootDir, 'public', 'logo.png');
const outputPath = join(rootDir, 'public', 'logo-square.png');

// Create a square version of the logo with padding
async function createSquareIcon() {
  try {
    // Get original image info
    const metadata = await sharp(inputPath).metadata();
    const width = metadata.width;
    const height = metadata.height;
    
    // Calculate square size (use the larger dimension)
    const size = Math.max(width, height);
    
    // Create square image with transparent background
    await sharp(inputPath)
      .resize(width, height, { fit: 'contain' })
      .extend({
        top: Math.floor((size - height) / 2),
        bottom: Math.ceil((size - height) / 2),
        left: Math.floor((size - width) / 2),
        right: Math.ceil((size - width) / 2),
        background: { r: 0, g: 0, b: 0, alpha: 0 }
      })
      .toFile(outputPath);
    
    console.log(`Created square icon: ${outputPath}`);
  } catch (error) {
    console.error('Error creating square icon:', error);
    process.exit(1);
  }
}

createSquareIcon();
