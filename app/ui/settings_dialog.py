"""
VaultKeeper - Settings Dialog
Modern settings interface matching the application design.
"""

from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QStackedWidget
)
from PySide6.QtCore import Qt

from .theme import get_theme
from .settings import (
    SettingsSidebarButton,
    GeneralTab,
    SecurityTab,
    PrivacyTab,
    CloudStorageTab
)


class SettingsDialog(QDialog):
    """Main settings dialog."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setFixedSize(800, 600)
        self.setup_ui()
        
    def setup_ui(self):
        theme = get_theme()
        
        # Main Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # --- Sidebar ---
        sidebar = QFrame()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet(f"""
            background-color: {theme.colors.sidebar}; 
            border-right: 1px solid {theme.colors.border};
        """)
        
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 24, 16, 24)
        sidebar_layout.setSpacing(8)
        
        # Title
        title = QLabel("Settings")
        title.setStyleSheet(f"""
            color: {theme.colors.foreground};
            font-size: 18px;
            font-weight: 700;
        """)
        sidebar_layout.addWidget(title)
        
        sidebar_layout.addSpacing(16)
        
        # Navigation Buttons
        self.nav_group = []
        
        # General
        self.btn_general = SettingsSidebarButton("settings", "General")
        self.btn_general.clicked.connect(lambda: self.switch_page(0))
        sidebar_layout.addWidget(self.btn_general)
        self.nav_group.append(self.btn_general)
        
        # Security
        self.btn_security = SettingsSidebarButton("shield", "Security")
        self.btn_security.clicked.connect(lambda: self.switch_page(1))
        sidebar_layout.addWidget(self.btn_security)
        self.nav_group.append(self.btn_security)
        
        # Privacy
        self.btn_privacy = SettingsSidebarButton("lock", "Privacy")
        self.btn_privacy.clicked.connect(lambda: self.switch_page(2))
        sidebar_layout.addWidget(self.btn_privacy)
        self.nav_group.append(self.btn_privacy)
        
        # Cloud Storage
        self.btn_cloud = SettingsSidebarButton("cloud_sync", "Cloud Storage")
        self.btn_cloud.clicked.connect(lambda: self.switch_page(3))
        sidebar_layout.addWidget(self.btn_cloud)
        self.nav_group.append(self.btn_cloud)
        
        sidebar_layout.addStretch()
        
        # Close Settings Button
        close_btn = QPushButton("Close Settings")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setFixedHeight(36)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.colors.card}; 
                border: 1px solid {theme.colors.border};
                color: {theme.colors.foreground};
                border-radius: 8px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {theme.colors.accent};
            }}
        """)
        close_btn.clicked.connect(self.accept)
        sidebar_layout.addWidget(close_btn)
        
        layout.addWidget(sidebar)
        
        # --- Content Area ---
        content = QFrame()
        content.setStyleSheet(f"background-color: {theme.colors.background};")
        
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(40, 40, 40, 40)
        
        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)
        
        # Add Pages
        # We use a placeholder approach for lazy loading if needed, or just add them.
        # Since we optimized CloudStorageTab, adding them here should be fast now.
        self.pages = {}
        self.stack.addWidget(GeneralTab()) # Index 0
        self.stack.addWidget(SecurityTab()) # Index 1
        self.stack.addWidget(PrivacyTab())  # Index 2
        self.stack.addWidget(CloudStorageTab()) # Index 3
        
        layout.addWidget(content)
        
        # Set initial page
        self.btn_general.setChecked(True)
        self.btn_general.update_style()
        self.stack.setCurrentIndex(0)
        
    def switch_page(self, index):
        self.stack.setCurrentIndex(index)
        
        # Update buttons
        for i, btn in enumerate(self.nav_group):
            btn.setChecked(i == index)
            btn.update_style()
