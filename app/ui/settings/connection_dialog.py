from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QWidget, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

from ...native.installer import NativeHostInstaller
from ..theme import get_theme
from ..ui_utils import load_svg_icon, get_icon_path

class BrowserRepairDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Browser Connection Repair")
        self.setFixedSize(600, 500)
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
        header.setFixedHeight(80)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)
        
        title_box = QVBoxLayout()
        title_label = QLabel("Browser Detection")
        title_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {theme.colors.foreground};")
        subtitle = QLabel("VaultKeeper scans for installed browsers to register the extension.")
        subtitle.setStyleSheet(f"font-size: 13px; color: {theme.colors.muted_foreground};")
        
        title_box.addWidget(title_label)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box)
        layout.addWidget(header)

        # Content
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(16)

        # Found Browsers Section
        lbl_found = QLabel("✓ Compatible Browsers Found")
        lbl_found.setStyleSheet(f"font-weight: 600; color: #4ade80; font-size: 14px;")
        content_layout.addWidget(lbl_found)

        self.list_found = QListWidget()
        self.list_found.setStyleSheet(f"""
            QListWidget {{
                background-color: {theme.colors.card};
                border: 1px solid {theme.colors.border};
                border-radius: 8px;
                padding: 8px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 8px;
                border-radius: 4px;
            }}
            QListWidget::item:hover {{
                background-color: {theme.colors.sidebar_accent};
            }}
        """)
        content_layout.addWidget(self.list_found)

        # Missing Browsers Section
        lbl_missing = QLabel("✗ Browsers Not Found")
        lbl_missing.setStyleSheet(f"font-weight: 600; color: {theme.colors.muted_foreground}; font-size: 14px; margin-top: 10px;")
        content_layout.addWidget(lbl_missing)

        self.list_missing = QListWidget()
        self.list_missing.setStyleSheet(f"""
            QListWidget {{
                background-color: {theme.colors.card};
                border: 1px solid {theme.colors.border};
                border-radius: 8px;
                padding: 8px;
                color: {theme.colors.muted_foreground};
                outline: none;
            }}
            QListWidget::item {{
                padding: 8px;
            }}
        """)
        self.list_missing.setFixedHeight(120)
        content_layout.addWidget(self.list_missing)

        layout.addWidget(content)

        # Footer
        footer = QFrame()
        footer.setStyleSheet(f"background-color: {theme.colors.sidebar}; border-top: 1px solid {theme.colors.border};")
        footer.setFixedHeight(70)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(24, 0, 24, 0)
        
        footer_layout.addStretch()
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setFixedSize(100, 36)
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {theme.colors.border};
                color: {theme.colors.foreground};
                border-radius: 6px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {theme.colors.sidebar_accent};
            }}
        """)
        btn_cancel.clicked.connect(self.reject)
        footer_layout.addWidget(btn_cancel)

        self.btn_repair = QPushButton("Install to Found Browsers")
        self.btn_repair.setCursor(Qt.PointingHandCursor)
        self.btn_repair.setMinimumWidth(200)
        self.btn_repair.setFixedHeight(36)
        self.btn_repair.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.colors.primary};
                border: none;
                color: white;
                border-radius: 6px;
                font-weight: 600;
                padding: 0 16px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors.primary_hover};
            }}
            QPushButton:disabled {{
                background-color: {theme.colors.muted};
                color: {theme.colors.muted_foreground};
            }}
        """)
        self.btn_repair.clicked.connect(self.run_repair)
        footer_layout.addWidget(self.btn_repair)

        layout.addWidget(footer)

    def scan_browsers(self):
        paths_map = self.installer.get_browser_paths()
        self.found = []
        self.missing = []

        for browser, paths in paths_map.items():
            valid_paths = []
            for path in paths:
                # Logic matches installer.install_for_browser check
                check_path = path if path.parent.exists() else None
                if check_path:
                    valid_paths.append(str(path))
            
            if valid_paths:
                self.found.append((browser, valid_paths))
            else:
                self.missing.append(browser)

        # Populate Lists
        self.list_found.clear()
        for browser, locations in self.found:
            item = QListWidgetItem(self.list_found)
            widget = QWidget()
            h_layout = QHBoxLayout(widget)
            h_layout.setContentsMargins(0, 0, 0, 0)
            h_layout.setSpacing(8)
            
            # Browser Icon/Name
            name_lbl = QLabel(browser.title())
            theme = get_theme()
            name_lbl.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {theme.colors.foreground};")
            h_layout.addWidget(name_lbl)
            
            # Location Count
            loc_lbl = QLabel(f"{len(locations)} location(s)")
            loc_lbl.setStyleSheet("color: #4ade80; background: rgba(74, 222, 128, 0.1); padding: 2px 6px; border-radius: 4px; font-size: 11px;")
            h_layout.addWidget(loc_lbl)
            
            h_layout.addStretch()
            
            item.setSizeHint(widget.sizeHint())
            self.list_found.setItemWidget(item, widget)

        self.list_missing.clear()
        for browser in self.missing:
            item = QListWidgetItem(f"{browser.title()}")
            self.list_missing.addItem(item)
            
        if not self.found:
            self.btn_repair.setEnabled(False)
            self.btn_repair.setText("No Browsers Found")

    def run_repair(self):
        self.btn_repair.setText("Installing...")
        self.btn_repair.setEnabled(False)
        self.list_found.setEnabled(False)
        
        try:
            self.installer.create_wrapper_script()
            results = []
            
            # Only install for found browsers to avoid unnecessary checks/errors
            for browser, _ in self.found:
                success, msg = self.installer.install_for_browser(browser)
                results.append((browser, success, msg))
            
            installed_names = [r[0].title() for r in results if r[1]]
            
            if installed_names:
                QMessageBox.information(
                    self, 
                    "Success", 
                    f"VaultKeeper has been connected to:\n{', '.join(installed_names)}\n\nPlease restart your browsers."
                )
                self.accept()
            else:
                QMessageBox.warning(self, "Failure", "Failed to install to any browser.")
                self.reject()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Installation failed: {str(e)}")
            self.reject()
