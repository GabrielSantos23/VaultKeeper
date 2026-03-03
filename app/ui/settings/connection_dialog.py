from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QWidget, QFrame, QMessageBox,
    QLineEdit, QComboBox, QFileDialog
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

from ...native.installer import NativeHostInstaller
from ..theme import get_theme
from ..ui_utils import load_svg_icon

class BrowserRepairDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Browser Connection")
        self.setFixedSize(700, 600)
        self.installer = NativeHostInstaller()
        self.setup_ui()
        self.scan_browsers()

    def setup_ui(self):
        theme = get_theme()
        
        # Main Layout
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet(f"background-color: {theme.colors.background}; color: {theme.colors.foreground};")

        # Header
        header = QFrame()
        header.setStyleSheet(f"background-color: {theme.colors.sidebar}; border-bottom: 1px solid {theme.colors.border};")
        header.setFixedHeight(70)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)
        
        title_box = QVBoxLayout()
        title_label = QLabel("Browser Integration")
        title_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {theme.colors.foreground};")
        subtitle = QLabel("Manage native messaging hosts for your browsers.")
        subtitle.setStyleSheet(f"font-size: 13px; color: {theme.colors.muted_foreground};")
        
        title_box.addWidget(title_label)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box)
        layout.addWidget(header)

        # Content
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 24, 24, 12)
        content_layout.setSpacing(20)

        # 1. Detected Browsers List
        lbl_detected = QLabel("Detected Installations")
        lbl_detected.setStyleSheet(f"font-weight: 600; font-size: 14px; color: {theme.colors.foreground};")
        content_layout.addWidget(lbl_detected)

        self.list_browsers = QListWidget()
        self.list_browsers.setStyleSheet(f"""
            QListWidget {{
                background-color: {theme.colors.card};
                border: 1px solid {theme.colors.border};
                border-radius: 8px;
                padding: 4px;
                outline: none;
            }}
            QListWidget::item {{
                border-bottom: 1px solid {theme.colors.border};
                padding: 4px;
            }}
            QListWidget::item:last {{
                border-bottom: none;
            }}
            QListWidget::item:hover {{
                background-color: {theme.colors.sidebar_accent};
            }}
        """)
        content_layout.addWidget(self.list_browsers)

        # 2. Manual Installation
        manual_group = QFrame()
        manual_group.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.colors.card};
                border: 1px dashed {theme.colors.border};
                border-radius: 8px;
            }}
        """)
        manual_layout = QVBoxLayout(manual_group)
        manual_layout.setContentsMargins(16, 16, 16, 16)
        manual_layout.setSpacing(12)

        lbl_manual = QLabel("Manual Installation (Advanced)")
        lbl_manual.setStyleSheet(f"font-weight: 600; font-size: 14px; border: none; background: transparent;")
        manual_layout.addWidget(lbl_manual)
        
        lbl_manual_input = QLabel("If your browser isn't listed, select its type and native messaging folder:")
        lbl_manual_input.setStyleSheet(f"font-size: 12px; color: {theme.colors.muted_foreground}; border: none; background: transparent;")
        manual_layout.addWidget(lbl_manual_input)

        form_layout = QHBoxLayout()
        form_layout.setContentsMargins(0, 0, 0, 0)
        
        self.combo_type = QComboBox()
        self.combo_type.addItems(["Firefox", "Chrome", "Chromium", "Brave", "Edge", "Vivaldi", "Opera", "Zen"])
        self.combo_type.setFixedWidth(100)
        self.combo_type.setFixedHeight(36)
        self.combo_type.setStyleSheet(f"""
            QComboBox {{
                background-color: {theme.colors.input};
                border: 1px solid {theme.colors.border};
                border-radius: 6px;
                color: {theme.colors.foreground};
                padding: 4px 8px;
            }}
        """)
        form_layout.addWidget(self.combo_type)

        self.input_path = QLineEdit()
        self.input_path.setPlaceholderText("Path to 'NativeMessagingHosts' or 'native-messaging-hosts' folder")
        self.input_path.setFixedHeight(36)
        self.input_path.setStyleSheet(f"""
            QLineEdit {{
                background-color: {theme.colors.input};
                border: 1px solid {theme.colors.border};
                border-radius: 6px;
                color: {theme.colors.foreground};
                padding: 0 12px;
            }}
        """)
        form_layout.addWidget(self.input_path)

        btn_browse = QPushButton("Browse...")
        btn_browse.setCursor(Qt.PointingHandCursor)
        btn_browse.setFixedHeight(36)
        btn_browse.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.colors.secondary};
                color: {theme.colors.secondary_foreground};
                border: 1px solid {theme.colors.border};
                border-radius: 6px;
                padding: 0 12px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors.accent};
            }}
        """)
        btn_browse.clicked.connect(self.browse_folder)
        form_layout.addWidget(btn_browse)

        manual_layout.addLayout(form_layout)

        btn_install_manual = QPushButton("Install to Custom Path")
        btn_install_manual.setCursor(Qt.PointingHandCursor)
        btn_install_manual.setFixedHeight(32)
        btn_install_manual.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.colors.sidebar_accent};
                color: {theme.colors.foreground};
                border: 1px solid {theme.colors.border};
                border-radius: 6px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {theme.colors.border};
            }}
        """)
        btn_install_manual.clicked.connect(self.install_manual)
        manual_layout.addWidget(btn_install_manual)

        content_layout.addWidget(manual_group)

        layout.addWidget(content)

        # Footer
        footer = QFrame()
        footer.setStyleSheet(f"background-color: {theme.colors.sidebar}; border-top: 1px solid {theme.colors.border};")
        footer.setFixedHeight(70)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(24, 0, 24, 0)
        
        status_info = QLabel("Changes require browser restart.")
        status_info.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-style: italic;")
        footer_layout.addWidget(status_info)
        
        footer_layout.addStretch()
        
        btn_close = QPushButton("Close")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setFixedSize(100, 36)
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.colors.card};
                border: 1px solid {theme.colors.border};
                color: {theme.colors.foreground};
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors.sidebar_accent};
            }}
        """)
        btn_close.clicked.connect(self.reject)
        footer_layout.addWidget(btn_close)

        self.btn_install_all = QPushButton("Install to All Detected")
        self.btn_install_all.setCursor(Qt.PointingHandCursor)
        self.btn_install_all.setFixedSize(180, 36)
        self.btn_install_all.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.colors.primary};
                border: none;
                color: white;
                border-radius: 6px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {theme.colors.primary_hover};
            }}
        """)
        self.btn_install_all.clicked.connect(self.install_all)
        footer_layout.addWidget(self.btn_install_all)

        layout.addWidget(footer)

    def scan_browsers(self):
        paths_map = self.installer.get_browser_paths()
        self.detected_paths = []
        self.list_browsers.clear()
        
        theme = get_theme()

        for browser, paths in paths_map.items():
            for path in paths:
                # Check if this path actually exists/is valid for installation
                if path.parent.exists():
                    self.detected_paths.append((browser, path))
                    self._add_browser_item(browser, path, theme)
        
        if not self.detected_paths:
            no_item = QListWidgetItem(self.list_browsers)
            lbl = QLabel("No standard browser installations found.")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"color: {theme.colors.muted_foreground}; padding: 20px;")
            self.list_browsers.setItemWidget(no_item, lbl)
            self.btn_install_all.setEnabled(False)
        else:
            self.btn_install_all.setEnabled(True)

    def _add_browser_item(self, browser, path, theme):
        item = QListWidgetItem(self.list_browsers)
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(12, 8, 12, 8)
        
        # Icon placeholder (or could use load_svg_icon if icons matched keys)
        
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        name_lbl = QLabel(browser.title())
        name_lbl.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {theme.colors.foreground};")
        info_layout.addWidget(name_lbl)
        
        path_lbl = QLabel(str(path))
        path_lbl.setStyleSheet(f"font-size: 12px; color: {theme.colors.muted_foreground}; font-family: monospace;")
        path_lbl.setWordWrap(True)
        info_layout.addWidget(path_lbl)
        
        layout.addLayout(info_layout, 1)
        
        # Check if already installed
        manifest_path = path / "com.vaultkeeper.host.json"
        is_installed = manifest_path.exists()
        
        status_lbl = QLabel("Installed" if is_installed else "Not Installed")
        status_color = theme.colors.success if is_installed else theme.colors.muted_foreground
        status_lbl.setStyleSheet(f"color: {status_color}; font-size: 12px; font-weight: 500;")
        layout.addWidget(status_lbl)
        
        item.setSizeHint(widget.sizeHint())
        self.list_browsers.addItem(item)
        self.list_browsers.setItemWidget(item, widget)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select NativeMessagingHosts Folder")
        if folder:
            self.input_path.setText(folder)

    def install_manual(self):
        path_str = self.input_path.text().strip()
        if not path_str:
            return
            
        path = Path(path_str)
        browser_type = self.combo_type.currentText().lower()
        
        # Map common names to internal keys if needed
        type_map = {"chrome": "chrome", "firefox": "firefox", "edge": "edge", "brave": "brave", "chromium": "chromium", "zen": "zen"}
        internal_type = type_map.get(browser_type, "chrome") # default to chrome structure if unknown

        self.installer.create_wrapper_script()
        success, msg = self.installer.install_at_path(internal_type, path)
        
        if success:
             QMessageBox.information(self, "Success", f"Installed successfully to:\n{path}")
             self.input_path.clear()
             self.scan_browsers() # Refresh list to see if it shows up (if it matches standard paths) or just to reset state
        else:
             QMessageBox.warning(self, "Error", f"Installation failed:\n{msg}")

    def install_all(self):
        self.installer.create_wrapper_script()
        count = 0
        errors = []
        
        for browser, path in self.detected_paths:
            success, msg = self.installer.install_at_path(browser, path)
            if success:
                count += 1
            else:
                errors.append(f"{browser}: {msg}")
        
        if errors:
            QMessageBox.warning(self, "Partial Success", f"Installed to {count} locations.\nErrors:\n" + "\n".join(errors))
        else:
            QMessageBox.information(self, "Success", f"Successfully installed to all {count} detected locations.")
            
        self.scan_browsers() # Refresh status labels
