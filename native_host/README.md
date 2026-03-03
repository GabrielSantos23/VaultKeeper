# Native Host Configuration

**IMPORTANT**: The files in this directory are for reference only!

The actual native messaging host manifest is **automatically installed** when you run the VaultKeeper app.

## How it works

1. When you run `python app/main.py`, the app automatically:
   - Creates the manifest file with the correct paths for your system
   - Registers it in the Windows Registry (on Windows)
   - Places it in the correct browser-specific directory

2. You don't need to manually copy or edit any files!

## Manual installation (if needed)

If you need to manually reinstall the native host:

```bash
python -m app.native.installer install
```

To check the installation status:

```bash
python -m app.native.installer check
```

## Files

- `com.vaultkeeper.host.json` - Template/example manifest (not used directly)
- `install_linux.sh` - Legacy Linux installer (deprecated, use installer.py instead)
