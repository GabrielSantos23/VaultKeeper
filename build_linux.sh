#!/bin/bash
# VaultKeeper Build Script for Linux
# Creates a standalone executable and AppImage for Linux

set -e

echo "=========================================="
echo "  VaultKeeper Build Script - Linux"
echo "=========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
VERSION="1.0.5"
APP_NAME="VaultKeeper"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check Python
echo -e "\n${YELLOW}[1/7] Checking Python...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo -e "${RED}Error: Python not found!${NC}"
    exit 1
fi
echo "Using: $($PYTHON --version)"

# Create/activate virtual environment
echo -e "\n${YELLOW}[2/7] Setting up virtual environment...${NC}"
if [ ! -d ".venv" ]; then
    $PYTHON -m venv .venv
fi
source .venv/bin/activate

# Install dependencies
echo -e "\n${YELLOW}[3/7] Installing dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

# Build executable
echo -e "\n${YELLOW}[4/7] Building executable...${NC}"
pyinstaller vaultkeeper.spec --clean --noconfirm

# Create distribution package (tar.gz)
echo -e "\n${YELLOW}[5/7] Creating distribution package...${NC}"
DIST_NAME="${APP_NAME}-${VERSION}-linux-x64"
DIST_DIR="dist/${DIST_NAME}"

mkdir -p "$DIST_DIR"
cp -r dist/VaultKeeper "$DIST_DIR/"
cp README.md "$DIST_DIR/" 2>/dev/null || true

cd dist
tar -czvf "${DIST_NAME}.tar.gz" "${DIST_NAME}"
cd ..

# Create AppImage
echo -e "\n${YELLOW}[6/7] Creating AppImage...${NC}"
APPDIR="dist/${APP_NAME}.AppDir"

# Create AppDir structure
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"

# Copy executable and dependencies
cp -r dist/VaultKeeper/* "$APPDIR/usr/bin/"

# Create .desktop file
cat > "$APPDIR/${APP_NAME}.desktop" << EOF
[Desktop Entry]
Type=Application
Name=VaultKeeper
Exec=VaultKeeper
Icon=vaultkeeper
Categories=Utility;Security;
Comment=Secure Password Manager
Terminal=false
EOF

# Copy desktop file to share
cp "$APPDIR/${APP_NAME}.desktop" "$APPDIR/usr/share/applications/"

# Create/Copy icon (use a simple placeholder if no icon exists)
if [ -f "app/ui/icons/icon.png" ]; then
    cp "app/ui/icons/icon.png" "$APPDIR/vaultkeeper.png"
    cp "app/ui/icons/icon.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/vaultkeeper.png"
else
    # Create a simple placeholder icon using Python
    $PYTHON << 'PYEOF'
from PySide6.QtGui import QImage, QPainter, QColor, QFont
from PySide6.QtCore import Qt, QRect
from PySide6.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
img = QImage(256, 256, QImage.Format_ARGB32)
img.fill(QColor(59, 158, 255))  # Blue background

painter = QPainter(img)
painter.setRenderHint(QPainter.Antialiasing)

# Draw a simple lock icon
painter.setPen(Qt.white)
painter.setBrush(QColor(255, 255, 255))
font = QFont("Sans", 120, QFont.Bold)
painter.setFont(font)
painter.drawText(QRect(0, 0, 256, 256), Qt.AlignCenter, "🔐")
painter.end()

img.save("dist/VaultKeeper.AppDir/vaultkeeper.png")
img.save("dist/VaultKeeper.AppDir/usr/share/icons/hicolor/256x256/apps/vaultkeeper.png")
print("Icon created")
PYEOF
fi

# Create AppRun script
cat > "$APPDIR/AppRun" << 'EOF'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin:${PATH}"
exec "${HERE}/usr/bin/VaultKeeper" "$@"
EOF
chmod +x "$APPDIR/AppRun"

# Download appimagetool if not present
echo -e "\n${YELLOW}[7/7] Packaging AppImage...${NC}"
APPIMAGETOOL="appimagetool-x86_64.AppImage"
if [ ! -f "$APPIMAGETOOL" ]; then
    echo "Downloading appimagetool..."
    wget -q "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage" -O "$APPIMAGETOOL"
    chmod +x "$APPIMAGETOOL"
fi

# Create AppImage
ARCH=x86_64 ./"$APPIMAGETOOL" "$APPDIR" "dist/${APP_NAME}-${VERSION}-x86_64.AppImage"

# Cleanup
rm -rf "$APPDIR"

echo -e "\n${GREEN}=========================================="
echo "  Build Complete!"
echo "==========================================${NC}"
echo ""
echo -e "Outputs:"
echo -e "  ${GREEN}Executable:${NC}  dist/VaultKeeper/VaultKeeper"
echo -e "  ${GREEN}Tar.gz:${NC}      dist/${DIST_NAME}.tar.gz"
echo -e "  ${GREEN}AppImage:${NC}    dist/${APP_NAME}-${VERSION}-x86_64.AppImage"
echo ""
echo "To run:"
echo "  ./dist/VaultKeeper/VaultKeeper"
echo "  ./dist/${APP_NAME}-${VERSION}-x86_64.AppImage"
