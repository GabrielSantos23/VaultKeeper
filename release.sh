#!/bin/bash

# Release helper script for VaultKeeper
# Usage: ./release.sh v2.1.0

set -e

VERSION=$1

if [ -z "$VERSION" ]; then
    echo "Usage: ./release.sh v2.1.0"
    exit 1
fi

echo "🚀 Starting release process for $VERSION"

# Check if private key is set
if [ -z "$TAURI_SIGNING_PRIVATE_KEY" ]; then
    echo "❌ Error: TAURI_SIGNING_PRIVATE_KEY environment variable not set"
    echo "Set it with: export TAURI_SIGNING_PRIVATE_KEY='...'"
    exit 1
fi

# Update version in files
echo "📋 Updating version numbers..."

# package.json
sed -i "s/\"version\": \".*\"/\"version\": \"${VERSION#v}\"/" vaultkeeper-tauri/package.json

# Cargo.toml
sed -i "s/^version = \".*\"/version = \"${VERSION#v}\"/" vaultkeeper-tauri/src-tauri/Cargo.toml

echo "✅ Version updated to ${VERSION#v}"

# Build the app
echo "🔨 Building VaultKeeper..."
cd vaultkeeper-tauri
npm install
npm run tauri:build

echo "✅ Build complete!"

# Show output files
echo ""
echo "📦 Release artifacts created:"
echo ""
ls -lh src-tauri/target/release/bundle/*/

echo ""
echo "📤 Next steps:"
echo "1. Create a new GitHub release with tag: $VERSION"
echo "2. Upload all files from: vaultkeeper-tauri/src-tauri/target/release/bundle/"
echo "3. Create and upload latest.json manifest"
echo ""
echo "🔗 GitHub Releases URL: https://github.com/Kilo-Org/kilocode/releases/new"
