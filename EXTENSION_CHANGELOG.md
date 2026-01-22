# VaultKeeper Browser Extension Changelog

## [1.0.8] - 2026-01-22

### Navigation & Layout

- **Tabbed Sidebar**: Introduced a new tabbed navigation system at the top of the sidebar. You can now switch seamlessly between **All Items**, **Credit Cards**, and **Secure Notes** from any view, replacing the previous bottom navigation bar.
- **Note Detail Header**: Redesigned the Secure Note header to place action buttons (Edit, Copy as MD, Delete) inline with the title, maximizing vertical space.
- **Split-View Fixes**: Resolved layout issues where navigating directly between Cards and Notes could cause view overlapping.

### Performance & Data Management

- **Smart Caching**: Implemented a background in-memory cache to minimize redundant requests to the desktop application, significantly speeding up navigation within the extension.
- **Manual Sync**: Added a **Refresh** button to the main toolbar. This allows you to force a data synchronization with the desktop app without logging out.
- **Optimized Loading**: Data is now served instantly from cache when navigating back and forth, only fetching from disk when necessary (e.g., after edits or on valid cache expiry).

### User Interface & Experience

- **State Persistence**: The extension remembers your last active section (Cards, Notes, or Logins) and restores it when you reopen the popup.
- **Updated Icons**: Refined icons for the Password Generator and navigation tabs for better visibility and aesthetic consistency.
- **Editor Improvements**: Added formatting buttons (Lists) and Markdown export capabilities to the Secure Note editor.

### Accessibility

- **Target Sizes**: Increased the size of interactive elements and toolbar buttons for easier clicking.
- **Visual Feedback**: Added animations (spinning refresh icon) and success indicators when copying data.
