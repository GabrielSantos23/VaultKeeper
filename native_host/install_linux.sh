#!/bin/bash
# VaultKeeper Native Host Installer for Linux

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
HOST_PATH="$PROJECT_DIR/app/native/host.py"
MANIFEST_NAME="com.vaultkeeper.host.json"

# Chrome/Chromium paths
CHROME_TARGET_DIR="$HOME/.config/google-chrome/NativeMessagingHosts"
CHROMIUM_TARGET_DIR="$HOME/.config/chromium/NativeMessagingHosts"

# Firefox path
FIREFOX_TARGET_DIR="$HOME/.mozilla/native-messaging-hosts"

echo "🔐 VaultKeeper Native Host Installer"
echo "====================================="
echo ""

# Get extension ID
read -p "Enter your Chrome extension ID: " EXTENSION_ID

if [ -z "$EXTENSION_ID" ]; then
    echo "❌ Extension ID is required"
    exit 1
fi

# Create manifest
create_manifest() {
    local target_file="$1"
    local browser="$2"
    
    mkdir -p "$(dirname "$target_file")"
    
    if [ "$browser" = "firefox" ]; then
        cat > "$target_file" << EOF
{
  "name": "com.vaultkeeper.host",
  "description": "VaultKeeper Native Messaging Host",
  "path": "$HOST_PATH",
  "type": "stdio",
  "allowed_extensions": [
    "vaultkeeper@example.com"
  ]
}
EOF
    else
        cat > "$target_file" << EOF
{
  "name": "com.vaultkeeper.host",
  "description": "VaultKeeper Native Messaging Host",
  "path": "$HOST_PATH",
  "type": "stdio",
  "allowed_origins": [
    "chrome-extension://$EXTENSION_ID/"
  ]
}
EOF
    fi
    
    echo "✅ Created manifest at: $target_file"
}

# Make host.py executable
chmod +x "$HOST_PATH"
echo "✅ Made host.py executable"

# Install for Chrome
if [ -d "$HOME/.config/google-chrome" ]; then
    create_manifest "$CHROME_TARGET_DIR/$MANIFEST_NAME" "chrome"
fi

# Install for Chromium
if [ -d "$HOME/.config/chromium" ]; then
    create_manifest "$CHROMIUM_TARGET_DIR/$MANIFEST_NAME" "chrome"
fi

# Install for Firefox
if [ -d "$HOME/.mozilla" ]; then
    create_manifest "$FIREFOX_TARGET_DIR/$MANIFEST_NAME" "firefox"
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "1. Install Python dependencies: pip install -r requirements.txt"
echo "2. Run the desktop app: python app/main.py"
echo "3. Load the extension in Chrome: chrome://extensions/"
echo "4. The extension should now be able to communicate with the desktop app"
