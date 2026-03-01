# Migration Guide: Python VaultKeeper to Tauri VaultKeeper

This guide explains how to migrate from the Python version of VaultKeeper to the new Tauri (Rust) version, ensuring existing users can seamlessly transition without losing their data.

## Table of Contents

1. [Overview](#overview)
2. [Data Compatibility](#data-compatibility)
3. [Migration Process](#migration-process)
4. [Auto-Update Setup](#auto-update-setup)
5. [Building and Signing Updates](#building-and-signing-updates)
6. [Release Process](#release-process)
7. [Troubleshooting](#troubleshooting)

---

## Overview

The Tauri version of VaultKeeper uses the same:
- **Database format** (SQLite with identical schema)
- **Encryption methods** (Argon2id + AES-GCM)
- **Configuration file structure** (auth.json)
- **Storage location** (`~/.vaultkeeper/` on all platforms)

This means users can switch between versions without any data migration steps.

---

## Data Compatibility

### Shared Data Location

Both versions store data in the same location:

| Platform | Path |
|----------|------|
| Windows | `%USERPROFILE%\.vaultkeeper\` |
| macOS/Linux | `~/.vaultkeeper/` |

### Files Structure

```
~/.vaultkeeper/
├── auth.json          # Master password hash & settings
├── vault.db           # SQLite database (encrypted data)
└── vault.db-journal   # SQLite journal (temporary)
```

### Database Schema

Both versions use identical SQL schemas:
- `credentials` table (passwords)
- `secure_notes` table (notes)
- `credit_cards` table (cards)
- `folders` table (organization)

---

## Migration Process

### For End Users

Users don't need to do anything special:

1. **Install the Tauri version** (it will detect existing data)
2. **Login with the same master password**
3. **All data appears automatically**

#### Windows
```powershell
# Download and run the installer
VaultKeeper-Setup.exe
# It will use the existing %USERPROFILE%\.vaultkeeper\ data
```

#### macOS
```bash
# Install the .app or .dmg
# It will use the existing ~/.vaultkeeper/ data
```

#### Linux (AppImage)
```bash
# Run the AppImage
./VaultKeeper.AppImage
# It will use the existing ~/.vaultkeeper/ data
```

### For Developers

When distributing updates, ensure:

1. **Same app identifier** in `tauri.conf.json`:
```json
{
  "identifier": "com.vaultkeeper.app"
}
```

2. **Same product name**:
```json
{
  "productName": "VaultKeeper"
}
```

---

## Auto-Update Setup

The Tauri version includes an auto-updater that checks for new releases on GitHub.

### Configuration

Already configured in `tauri.conf.json`:

```json
{
  "plugins": {
    "updater": {
      "active": true,
      "dialog": false,
      "endpoints": [
        "https://github.com/Kilo-Org/kilocode/releases/latest/download/latest.json"
      ],
      "pubkey": "dW50cnVzdGVkIGNvbW1lbnQ6IG1pbmlzaWduIHB1YmxpYyBrZXk6IDEwMzkxQzk1MUM5QUVFQkMKUldTODdwb2NsUnc1RUdRaUg0UGZINU9ZRmREN2RkcDVKK3hBSVhLUVdCb20zSjVObGQrdjFQcDEK"
    }
  }
}
```

### Environment Variables for Signing

Set these environment variables before building:

#### Windows (PowerShell)
```powershell
$env:TAURI_SIGNING_PRIVATE_KEY = "dW50cnVzdGVkIGNvbW1lbnQ6IHJzaWduIGVuY3J5cHRlZCBzZWNyZXQga2V5ClJXUlRZMEl5VWh4djVZMCtOSEd6Z3lXT2VVR244TmdYY2t2SDJsV1ZzVzdlYWpseUYxUUFBQkFBQUFBQUFBQUFBQUlBQUFBQTh1bGx0R2ZWVldPYVR3OCtoNWdqSE5iY04xZW12MURSbWJtMmV3ekEwelhnY3gzdVFldUpqMDZ0bVpTWVlMMDFIZ05xd2FZT29wRUQ3TzJVRUlWNWdTREhlSDl4MUlLcjhGZXlBaVFyQnBLMVpoMVBxcXJXOUZ1Zzd2QXRKT3B1dEVoZXNXcVQ4Mkk9Cg=="
```

#### macOS/Linux (Bash)
```bash
export TAURI_SIGNING_PRIVATE_KEY="dW50cnVzdGVkIGNvbW1lbnQ6IHJzaWduIGVuY3J5cHRlZCBzZWNyZXQga2V5ClJXUlRZMEl5VWh4djVZMCtOSEd6Z3lXT2VVR244TmdYY2t2SDJsV1ZzVzdlYWpseUYxUUFBQkFBQUFBQUFBQUFBQUlBQUFBQTh1bGx0R2ZWVldPYVR3OCtoNWdqSE5iY04xZW12MURSbWJtMmV3ekEwelhnY3gzdVFldUpqMDZ0bVpTWVlMMDFIZ05xd2FZT29wRUQ3TzJVRUlWNWdTREhlSDl4MUlLcjhGZXlBaVFyQnBLMVpoMVBxcXJXOUZ1Zzd2QXRKT3B1dEVoZXNXcVQ4Mkk9Cg=="
```

---

## Building and Signing Updates

### Prerequisites

1. **Rust** installed (https://rustup.rs/)
2. **Node.js** installed
3. **Tauri CLI**: `cargo install tauri-cli`

### Build Steps

1. **Set the private key environment variable** (see above)

2. **Build the application**:
```bash
cd vaultkeeper-tauri
npm install
npm run tauri:build
```

3. **Generate update signatures**:

The build process automatically generates:
- `.msi` (Windows installer)
- `.app` (macOS app bundle)
- `.AppImage` (Linux portable)
- `.sig` signature files for each

### Update Bundle Structure

After building, the `src-tauri/target/release/bundle/` directory contains:

```
bundle/
├── msi/
│   ├── VaultKeeper_2.0.0_x64_en-US.msi
│   └── VaultKeeper_2.0.0_x64_en-US.msi.sig
├── nsis/
│   ├── VaultKeeper_2.0.0_x64-setup.exe
│   └── VaultKeeper_2.0.0_x64-setup.exe.sig
└── appimage/
    ├── vaultkeeper_2.0.0_amd64.AppImage
    └── vaultkeeper_2.0.0_amd64.AppImage.sig
```

---

## Release Process

### 1. Update Version

Update version in both:
- `package.json`
- `src-tauri/Cargo.toml`
- `src-tauri/tauri.conf.json`

### 2. Create Release Notes

Example `RELEASE_NOTES.md`:
```markdown
## VaultKeeper 2.1.0

### New Features
- New security dashboard with breach detection
- Password hint feature
- Improved auto-lock functionality

### Improvements
- Faster startup time
- Better memory usage
- Cross-platform data compatibility

### Bug Fixes
- Fixed clipboard clearing issues
- Fixed update dialog glitches
```

### 3. Build and Sign

```bash
# Ensure private key is set
export TAURI_SIGNING_PRIVATE_KEY="..."

# Build release
npm run tauri:build
```

### 4. Create GitHub Release

1. Go to GitHub → Releases → Draft New Release
2. Tag version: `v2.1.0`
3. Title: `VaultKeeper 2.1.0`
4. Paste release notes
5. Upload all files from `target/release/bundle/`
6. **Critical**: Upload a file named `latest.json` with the update manifest

### 5. Update Manifest (latest.json)

Create `latest.json` for the updater:

```json
{
  "version": "2.1.0",
  "notes": "New security features and improvements",
  "pub_date": "2026-03-01T00:00:00Z",
  "platforms": {
    "windows-x86_64": {
      "signature": "content of .msi.sig file",
      "url": "https://github.com/Kilo-Org/kilocode/releases/download/v2.1.0/VaultKeeper_2.1.0_x64_en-US.msi"
    },
    "linux-x86_64": {
      "signature": "content of .AppImage.sig file",
      "url": "https://github.com/Kilo-Org/kilocode/releases/download/v2.1.0/vaultkeeper_2.1.0_amd64.AppImage"
    },
    "darwin-x86_64": {
      "signature": "content of .app.tar.gz.sig file",
      "url": "https://github.com/Kilo-Org/kilocode/releases/download/v2.1.0/VaultKeeper_x64.app.tar.gz"
    },
    "darwin-aarch64": {
      "signature": "content of .app.tar.gz.sig file",
      "url": "https://github.com/Kilo-Org/kilocode/releases/download/v2.1.0/VaultKeeper_aarch64.app.tar.gz"
    }
  }
}
```

**Note**: Extract the signature from the `.sig` files and put the content in the JSON.

### 6. Automate with GitHub Actions

Create `.github/workflows/release.yml`:

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    strategy:
      fail-fast: false
      matrix:
        platform: [macos-latest, ubuntu-latest, windows-latest]
    runs-on: ${{ matrix.platform }}
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 20
      
      - name: Setup Rust
        uses: dtolnay/rust-action@stable
      
      - name: Install dependencies
        run: npm install
      
      - name: Build Tauri
        uses: tauri-apps/tauri-action@v0
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          TAURI_SIGNING_PRIVATE_KEY: ${{ secrets.TAURI_SIGNING_PRIVATE_KEY }}
        with:
          tagName: ${{ github.ref_name }}
          releaseName: "VaultKeeper ${{ github.ref_name }}"
          releaseBody: "See the assets to download and install this version."
          releaseDraft: true
          prerelease: false
```

Add the private key to GitHub Secrets:
- Go to Settings → Secrets and variables → Actions
- Add `TAURI_SIGNING_PRIVATE_KEY` with your private key

---

## Troubleshooting

### "Update signature verification failed"

**Cause**: The signature in `latest.json` doesn't match the built file.

**Solution**: 
1. Rebuild with the correct private key
2. Copy the exact content from `.sig` files to `latest.json`

### "No update available" when there should be

**Cause**: The `latest.json` URL is incorrect or the version hasn't changed.

**Solution**:
1. Verify the URL in `tauri.conf.json` matches your GitHub releases
2. Ensure the version in `latest.json` is newer than the installed version

### "Failed to download update"

**Cause**: Network issues or incorrect download URLs.

**Solution**:
1. Test the URLs in a browser
2. Check GitHub release assets are public
3. Ensure the file names match exactly

### Data not appearing after switching versions

**Cause**: Different storage locations or permissions.

**Solution**:
1. Check the data directory exists:
   - Windows: `%USERPROFILE%\.vaultkeeper\`
   - macOS/Linux: `~/.vaultkeeper/`
2. Verify file permissions
3. Check the app has read/write access

### Linux AppImage won't run after update

**Cause**: AppImage needs executable permissions.

**Solution**:
```bash
chmod +x VaultKeeper.AppImage
```

---

## Security Notes

### Key Management

- **Never commit the private key** to git
- **Store it securely** (password manager, GitHub Secrets, etc.)
- **Back it up** - losing it means no more signed updates
- The public key in `tauri.conf.json` is safe to commit

### Update Verification

The updater verifies:
1. **Signature** - Signed with your private key
2. **Version** - Must be newer than current
3. **Platform** - Correct OS/architecture

---

## Summary for Users

**To migrate from Python to Tauri version:**

1. Download and install the new version
2. Login with your existing master password
3. All data is automatically available
4. Future updates will be automatic

**No manual data migration required!**

---

## Additional Resources

- [Tauri Updater Documentation](https://tauri.app/v1/guides/distribution/updater/)
- [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)
- [Code Signing](https://tauri.app/v1/guides/distribution/sign/)

---

## Questions?

If you encounter issues during migration:
1. Check the logs: `%APPDATA%\VaultKeeper\logs\` (Windows) or `~/.vaultkeeper/logs/` (macOS/Linux)
2. Open an issue on GitHub with the log files
