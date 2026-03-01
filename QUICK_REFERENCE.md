# Quick Migration Reference

## For Users: Zero-Downtime Migration

Python users can switch to Tauri instantly - **no data export/import needed**!

### Why It Works

Both apps use:
- ✅ Same database file (`~/.vaultkeeper/vault.db`)
- ✅ Same encryption (Argon2id + AES-GCM)
- ✅ Same config format (`auth.json`)
- ✅ Same folder structure

### Migration Steps

1. **Close the Python app** (if running)
2. **Install Tauri version**
3. **Open Tauri app**
4. **Login with same password**
5. ✅ Done! All data is there

---

## For Developers: Release Checklist

### Before Release

- [ ] Update version in:
  - `package.json`
  - `src-tauri/Cargo.toml`
  - `src-tauri/tauri.conf.json`

- [ ] Set signing key:
  ```bash
  export TAURI_SIGNING_PRIVATE_KEY="dW50cnVzdGVkIGNvbW1lbnQ6IHJzaWduIGVuY3J5cHRlZCBzZWNyZXQga2V5ClJXUlRZMEl5VWh4djVZMCtOSEd6Z3lXT2VVR244TmdYY2t2SDJsV1ZzVzdlYWpseUYxUUFBQkFBQUFBQUFBQUFBQUlBQUFBQTh1bGx0R2ZWVldPYVR3OCtoNWdqSE5iY04xZW12MURSbWJtMmV3ekEwelhnY3gzdVFldUpqMDZ0bVpTWVlMMDFIZ05xd2FZT29wRUQ3TzJVRUlWNWdTREhlSDl4MUlLcjhGZXlBaVFyQnBLMVpoMVBxcXJXOUZ1Zzd2QXRKT3B1dEVoZXNXcVQ4Mkk9Cg=="
  ```

- [ ] Build release:
  ```bash
  cd vaultkeeper-tauri
  npm run tauri:build
  ```

### Create GitHub Release

1. Draft new release with tag `v2.x.x`
2. Upload all files from `target/release/bundle/`
3. Create `latest.json` manifest (see below)
4. Upload `latest.json` to release
5. Publish release

### latest.json Template

```json
{
  "version": "2.1.0",
  "notes": "New features and improvements",
  "pub_date": "2026-03-01T00:00:00Z",
  "platforms": {
    "windows-x86_64": {
      "signature": "PASTE_CONTENT_OF_.msi.sig_FILE_HERE",
      "url": "https://github.com/Kilo-Org/kilocode/releases/download/v2.1.0/VaultKeeper_2.1.0_x64_en-US.msi"
    },
    "linux-x86_64": {
      "signature": "PASTE_CONTENT_OF_.AppImage.sig_FILE_HERE", 
      "url": "https://github.com/Kilo-Org/kilocode/releases/download/v2.1.0/vaultkeeper_2.1.0_amd64.AppImage"
    },
    "darwin-x86_64": {
      "signature": "PASTE_CONTENT_OF_.app.tar.gz.sig_FILE_HERE",
      "url": "https://github.com/Kilo-Org/kilocode/releases/download/v2.1.0/VaultKeeper_x64.app.tar.gz"
    },
    "darwin-aarch64": {
      "signature": "PASTE_CONTENT_OF_.app.tar.gz.sig_FILE_HERE",
      "url": "https://github.com/Kilo-Org/kilocode/releases/download/v2.1.0/VaultKeeper_aarch64.app.tar.gz"
    }
  }
}
```

---

## Key Points

### Data Compatibility ✅

| Feature | Python | Tauri | Compatible? |
|---------|--------|-------|-------------|
| Master password hash | ✅ Argon2id | ✅ Argon2id | ✅ Yes |
| Database encryption | ✅ AES-GCM | ✅ AES-GCM | ✅ Yes |
| SQLite schema | ✅ | ✅ Identical | ✅ Yes |
| Config file (auth.json) | ✅ | ✅ Same format | ✅ Yes |
| Storage location | ✅ `~/.vaultkeeper` | ✅ `~/.vaultkeeper` | ✅ Yes |

### Auto-Update Flow

1. App starts → checks GitHub for `latest.json`
2. If newer version exists → shows update dialog
3. User clicks "Update" → downloads in background
4. Download complete → installs update
5. User restarts app → runs new version

### Security

- Updates are **signed** with your private key
- App **verifies signature** before installing
- If signature invalid → update rejected
- Man-in-the-middle attacks prevented

---

## Important Files

| File | Purpose | Keep Secret? |
|------|---------|--------------|
| `tauri.conf.json` → `pubkey` | Public verification key | ❌ Safe to commit |
| `TAURI_SIGNING_PRIVATE_KEY` env var | Signs updates | ✅ YES - NEVER SHARE |
| `~/.vaultkeeper/auth.json` | User's auth config | ✅ User's data |
| `~/.vaultkeeper/vault.db` | Encrypted vault | ✅ User's data |

---

## Testing Updates

1. Build version 2.0.0 → Install it
2. Build version 2.0.1 → Create release
3. Open 2.0.0 → Should detect 2.0.1
4. Click update → Should download & install
5. Restart → Should be on 2.0.1

---

## Emergency: Lost Private Key

If you lose the private key:
1. Generate new key pair: `cargo tauri signer generate`
2. Update `pubkey` in `tauri.conf.json`
3. Tell users to manually download new version
4. Old versions cannot auto-update (signature mismatch)

**Always backup your private key!**
