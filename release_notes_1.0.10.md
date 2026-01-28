### 🔍 Connection & Diagnostics

- **Redesigned Connection Tool**:
  - The "Repair Connection" dialog has been completely rebuilt to provide more transparency and control.
  - **Browser Detection**: Now displays all detected browser installations, including their exact paths (supporting Snap, Flatpak, and Standard installations).
  - **Manual Installation**: Added an "Advanced" mode to manually install the Native Host manifest to a custom path if automatic detection fails.
  - **Status Indicators**: Clearly shows which browser profiles are currently connected ("Installed" vs "Not Installed").
- **UI Improvements**: Fixed layout issues in the connection dialog where buttons were truncated and text was invisible on some themes.

### 🐞 Bug Fixes

- **Theme Stability**: Fixed a crash caused by a missing color attribute (`primary_hover`) in the theme system.
- **Path Resolution**: Improved logic for detecting browser configuration paths across different Linux package formats.
