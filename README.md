# 🔐 VaultKeeper 2.0 - Password Manager

A secure desktop password manager with browser extension integration. Built with **Rust + Tauri + React** for maximum performance and security.

> 🎉 **Version 2.0 is here!** Completely rewritten in Rust with better performance, auto-updates, and seamless migration from the Python version.

## 🚀 What's New in 2.0

- ⚡ **Lightning fast** - Native binary, no Python runtime needed
- 🔄 **Auto-updates** - Get new features automatically
- 💾 **Zero migration** - Existing Python users keep all their data
- 🎨 **Modern UI** - Beautiful new interface with dark mode
- 🔒 **Same security** - Identical encryption (Argon2id + AES-256-GCM)
- 🌐 **Browser extension** - Works with Chrome, Firefox, and Edge
- 📱 **Cross-platform** - Windows, macOS, and Linux

## 📦 Installation

### Download Pre-built Binaries

| Platform | Download |
|----------|----------|
| Windows | `VaultKeeper-Setup.exe` (Installer) |
| macOS Intel | `VaultKeeper_x64.app.tar.gz` |
| macOS Apple Silicon | `VaultKeeper_aarch64.app.tar.gz` |
| Linux | `vaultkeeper.AppImage` (Portable) |

Download from [GitHub Releases](https://github.com/Kilo-Org/kilocode/releases/latest)

### Build from Source

```bash
# Clone the repository
git clone https://github.com/Kilo-Org/kilocode.git
cd kilocode/vaultkeeper-tauri

# Install dependencies
npm install

# Run in development mode
npm run tauri:dev

# Build for production
npm run tauri:build
```

## 🔄 Migrating from Python Version

**Good news: No data migration required!** 🎉

The new Tauri version is **fully compatible** with the Python version:

- ✅ Same database format (SQLite)
- ✅ Same encryption (Argon2id + AES-256-GCM)
- ✅ Same storage location (`~/.vaultkeeper/`)
- ✅ Same master password

### Migration Steps

1. **Close the Python app** completely
2. **Download and install** the Tauri version
3. **Login with your existing master password**
4. **Done!** All your data is automatically there

See [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) for detailed instructions.

## 🏗️ Architecture

```
┌────────────────┐      Native Messaging      ┌────────────────────┐
│ Browser        │ ◀──────────────────────▶  │ VaultKeeper App    │
│ Extension      │                            │ (Rust + Tauri)     │
└────────────────┘                            └────────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │ SQLite Database │
                                              │ (Encrypted)     │
                                              └─────────────────┘
```

## 🛡️ Security

### Encryption

- **Master Password Hash**: Argon2id (OWASP recommended)
- **Database Encryption**: AES-256-GCM
- **Unique Salt**: Per credential (16 bytes)
- **Key Derivation**: PBKDF2 with 600,000 iterations

### Protections

- 🔒 Auto-lock after inactivity
- 🧹 Clipboard auto-clear (10 seconds)
- 🚫 Key never stored on disk
- 🔐 All encryption happens locally

## 📁 Data Storage

Data is stored in your home directory:

| Platform | Location |
|----------|----------|
| Windows | `%USERPROFILE%\.vaultkeeper\` |
| macOS | `~/.vaultkeeper/` |
| Linux | `~/.vaultkeeper/` |

Files:
- `vault.db` - SQLite database (encrypted)
- `auth.json` - Authentication config
- `native_host.log` - Debug logs

## 🔌 Browser Extension

### Installation

1. Open your browser's extension page:
   - Chrome: `chrome://extensions/`
   - Firefox: `about:addons`
   - Edge: `edge://extensions/`

2. Enable **Developer Mode**

3. Click **Load Unpacked** and select the `extension/` folder

4. The extension will automatically connect to the desktop app

### Features

- 🔍 Auto-detect login forms
- 📝 Auto-fill credentials
- 🔎 Search passwords
- 📋 Copy passwords to clipboard
- ➕ Save new credentials

## 🛠️ Development

### Prerequisites

- [Node.js](https://nodejs.org/) 18+
- [Rust](https://rustup.rs/)
- [Tauri CLI](https://tauri.app/v1/guides/getting-started/prerequisites)

### Setup

```bash
cd vaultkeeper-tauri

# Install dependencies
npm install

# Run development server
npm run tauri:dev

# Build for production
npm run tauri:build
```

### Project Structure

```
vaultkeeper-tauri/
├── src/
│   ├── components/     # React components
│   ├── stores/         # Zustand state management
│   ├── views/          # Page views
│   └── hooks/          # Custom React hooks
├── src-tauri/
│   ├── src/            # Rust backend code
│   └── Cargo.toml      # Rust dependencies
├── extension/          # Browser extension
└── package.json
```

## 🔄 Auto-Updates

VaultKeeper includes an auto-updater that checks for new versions on GitHub. When an update is available:

1. You'll see a notification in the app
2. Click "Update Now" to download
3. The app will restart automatically

Updates are signed with our private key for security.

## 🐛 Troubleshooting

### App won't start

- Check that `~/.vaultkeeper/` has write permissions
- Try running as administrator (Windows) or with `sudo` (Linux/macOS)

### Data not appearing after migration

1. Verify the Python app was closed before installing
2. Check that data exists in `~/.vaultkeeper/vault.db`
3. Try logging out and back in

### Extension not connecting

1. Make sure the desktop app is running
2. Check the browser console for errors
3. Reinstall the Native Host:
   ```bash
   python -m app.native.installer install
   ```

### Update fails

1. Check your internet connection
2. Try downloading manually from GitHub Releases
3. Report the issue with logs from `~/.vaultkeeper/logs/`

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Tauri](https://tauri.app/)
- UI powered by [React](https://react.dev/) and [Tailwind CSS](https://tailwindcss.com/)
- Icons by [HugeIcons](https://hugeicons.com/)

---

<p align="center">
  Made with ❤️ by the VaultKeeper Team
</p>
