# VaultKeeper Firefox Extension Source Code

This repository contains the full source code for the **VaultKeeper** browser extension, built using Vite, React, TypeScript, and Tailwind CSS.

## ⚠️ Important Note About Native Messaging

VaultKeeper is a companion extension that heavily relies on a **Native Messaging Host** (a local desktop application) to encrypt, decrypt, and manage credentials securely on the user's OS.
Because the extension communicates with this desktop host via `nativeMessaging`, **it will not fully work in isolation** during an AMO review unless the corresponding Native Host script is also installed on the reviewer's machine.

For the purpose of source code review and compilation verification, the extension can be built and inspected. However, the UI will likely display "Could not connect to VaultKeeper app" due to the missing Native Host.

## Prerequisites for Building

To build the extension from source, you will need the following installed:

1. **Node.js** (v18 or higher recommended)
2. **Bun** (We use Bun as our package manager and script runner. Installation guide: https://bun.sh)

## How to Build the Extension

1. Ensure you are in the root directory of the source code (`vite-web-extension`).
2. Install the necessary dependencies:
   ```bash
   bun install
   ```
3. Run the Firefox build script. This will use Vite to compile the TypeScript/React code and bundle the assets:
   ```bash
   bun run build:firefox
   ```
4. Once the build finishes, a new folder named `dist_firefox` will be generated in the root directory.

## Loading the Extension for Review

1. Open Firefox and navigate to `about:debugging#/runtime/this-firefox`.
2. Click on **Load Temporary Add-on...**
3. Navigate to the newly created `dist_firefox` folder.
4. Select the `manifest.json` file inside the `dist_firefox` directory.

The extension will now be loaded into your Firefox instance for review.

## Project Structure Overview

- `src/pages/background/`: Contains the service worker logic bridging the extension UI to the Native Messaging Host.
- `src/pages/popup/`: Contains the React UI components for the extension's popup interface.
- `src/pages/content/`: Contains the content scripts injected into web pages (e.g., for auto-filling credentials).
- `manifest.json`: The core manifest configuration file.
- `vite.config.firefox.ts`: The Vite configuration specifically tailored for building the Firefox/Gecko target.
