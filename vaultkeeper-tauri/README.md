# VaultKeeper Tauri

A modern, secure password manager built with **Rust Tauri** and **React + Tailwind CSS 4**.

## Features

### Security First
- **End-to-End Encryption**: All data is encrypted locally using industry-standard algorithms
- **Zero-Knowledge Architecture**: Your master password never leaves your device
- **Secure Clipboard**: Automatic clipboard clearing after password copy
- **Auto-lock**: Vault automatically locks after period of inactivity

### Modern UI
- **Dark Theme**: Elegant dark interface designed for extended use
- **Glassmorphism Design**: Modern translucent UI elements
- **Smooth Animations**: Polished transitions and micro-interactions
- **Responsive Layout**: Adapts to different window sizes

### Core Functionality
- **Password Storage**: Securely store login credentials
- **Secure Notes**: Keep sensitive information encrypted
- **Credit Cards**: Store payment information securely
- **Folders**: Organize your vault with custom folders
- **Password Generator**: Create strong, random passwords
- **Security Dashboard**: Monitor vault security health
- **Favorites**: Quick access to frequently used items

## Tech Stack

- **Backend**: Rust + Tauri v2
- **Frontend**: React 18 + TypeScript
- **Styling**: Tailwind CSS 4 (Beta)
- **State Management**: Zustand
- **Icons**: Lucide React
- **Crypto**: ring, argon2, aes-gcm

## Project Structure

```
vaultkeeper-tauri/
├── src/                    # React frontend
│   ├── components/         # UI components
│   ├── stores/            # Zustand state stores
│   ├── styles/            # Global styles
│   ├── views/             # Main view components
│   ├── App.tsx            # Root component
│   └── main.tsx           # Entry point
├── src-tauri/             # Rust backend
│   ├── src/
│   │   ├── main.rs        # Entry point
│   │   ├── commands.rs    # Tauri commands
│   │   ├── crypto.rs      # Cryptographic functions
│   │   └── vault.rs       # Vault management
│   ├── Cargo.toml         # Rust dependencies
│   └── tauri.conf.json    # Tauri configuration
├── package.json           # Node dependencies
├── tsconfig.json          # TypeScript config
├── vite.config.ts         # Vite configuration
└── index.html             # HTML template
```

## Getting Started

### Prerequisites

- [Rust](https://rustup.rs/) (latest stable)
- [Node.js](https://nodejs.org/) (18+)
- [Tauri CLI](https://tauri.app/v1/guides/getting-started/prerequisites)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd vaultkeeper-tauri
```

2. Install dependencies:
```bash
npm install
```

3. Run in development mode:
```bash
npm run tauri:dev
```

### Building for Production

```bash
npm run tauri:build
```

This will create platform-specific binaries in `src-tauri/target/release/`.

## Development

### Frontend Development

The frontend uses Vite for fast HMR (Hot Module Replacement). Run:

```bash
npm run dev
```

This starts the Vite dev server without the Tauri backend for faster frontend iteration.

### Backend Development

Rust source files are in `src-tauri/src/`. To rebuild after changes:

```bash
cd src-tauri
cargo build
```

### Adding Tauri Commands

1. Add command in `src-tauri/src/commands.rs`:
```rust
#[tauri::command]
pub async fn my_command(arg: String) -> Result<String, String> {
    Ok(format!("Hello, {}!", arg))
}
```

2. Register in `src-tauri/src/main.rs`:
```rust
.invoke_handler(tauri::generate_handler![
    // ... existing commands
    commands::my_command,
])
```

3. Call from frontend:
```typescript
import { invoke } from '@tauri-apps/api/core'

const result = await invoke<string>('my_command', { arg: 'World' })
```

## Theming

The app uses a custom dark theme with CSS custom properties. Colors are defined in `src/styles/globals.css`:

```css
@theme {
  --color-background: #0a0a0f;
  --color-primary: #3b82f6;
  --color-secondary: #8b5cf6;
  /* ... */
}
```

## Security Considerations

- Master password is never stored in plain text
- Encryption keys are derived using Argon2id
- All encryption/decryption happens locally
- Clipboard is automatically cleared after 30 seconds
- Session timeout after inactivity

## Roadmap

- [ ] Browser extension integration
- [ ] Cloud sync (encrypted)
- [ ] Biometric authentication
- [ ] Password breach monitoring
- [ ] TOTP/2FA code generation
- [ ] Import from other password managers
- [ ] Emergency access
- [ ] Secure file storage

## License

MIT License - See LICENSE file for details

## Credits

Built with [Tauri](https://tauri.app/), [React](https://react.dev/), and [Tailwind CSS](https://tailwindcss.com/).
