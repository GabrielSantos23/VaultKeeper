"""
VaultKeeper - Settings Dialog
Modern settings interface matching the application design.
"""

from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QStackedWidget, QComboBox, 
    QScrollArea, QCheckBox, QAbstractItemView, QListView,
    QMessageBox
)
from PySide6.QtCore import Qt, Signal, QSize, QRect, QUrl
from PySide6.QtGui import QIcon, QPainter, QColor, QPaintEvent, QBrush, QDesktopServices

from app import __version__
from app.core.updater import UpdateManager

from .theme import get_theme
from .ui_utils import load_svg_icon, get_icon_path
from ..core.config import get_config

class ToggleSwitch(QCheckBox):
    """A modern iOS-style toggle switch."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(44, 24)
        self.setCursor(Qt.PointingHandCursor)
        self.stateChanged.connect(self.update)
        
    def hitButton(self, pos):
        return self.contentsRect().contains(pos)
        
    def paintEvent(self, e: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Colors (hardcoded based on image or theme)
        # Blue active: #3b82f6 (common tailwind blue) or custom
        # In image it looks like a vibrant blue
        theme = get_theme()
        active_color = QColor("#3b82f6") 
        inactive_color = QColor(theme.colors.muted if hasattr(theme.colors, 'muted') else "#3f3f46")
        handle_color = QColor("#ffffff")
        
        # Track
        rect = self.contentsRect()
        if self.isChecked():
            painter.setBrush(QBrush(active_color))
            painter.setPen(Qt.NoPen)
        else:
            painter.setBrush(QBrush(inactive_color))
            painter.setPen(Qt.NoPen)
            
        painter.drawRoundedRect(rect, 12, 12)
        
        # Handle
        handle_x = 22 if self.isChecked() else 2
        handle_rect = QRect(handle_x, 2, 20, 20)
        painter.setBrush(QBrush(handle_color))
        painter.drawEllipse(handle_rect)
        painter.end()

class SettingsSidebarButton(QPushButton):
    """Sidebar navigation button."""
    
    def __init__(self, icon_name: str, text: str, parent=None):
        super().__init__(parent)
        self.icon_name = icon_name
        self.setText(f"  {text}")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(40)
        self.update_style()
        
    def update_style(self):
        theme = get_theme()
        
        # Determine colors based on state
        bg_color = theme.colors.sidebar_accent if self.isChecked() else "transparent"
        text_color = theme.colors.sidebar_primary_foreground if self.isChecked() else theme.colors.sidebar_foreground
        
        # Icon color matches text usually
        # For the image, selected item has blue background? 
        # Actually image "General" is highlighted with blue bg.
        
        if self.isChecked():
            # Use a blue-ish accent for selected state like in image
            # Image shows dark blue bg for "General"
            bg_color = "rgba(59, 130, 246, 0.2)" # Semi-transparent blue
            text_color = "#60a5fa" # Blue text
            icon_color = "#60a5fa"
            border_left = f"3px solid {text_color}"
        else:
            bg_color = "transparent"
            text_color = theme.colors.sidebar_muted
            icon_color = theme.colors.sidebar_muted
            border_left = "3px solid transparent"
            
        self.setIcon(QIcon(load_svg_icon(self.icon_name, 16, icon_color)))
        self.setIconSize(QSize(16, 16))
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                border: none;
                border-radius: 6px;
                padding: 12px;
                text-align: left;
                font-size: 14px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {theme.colors.sidebar_accent};
            }}
        """)

class SettingsDialog(QDialog):
    """Main settings dialog."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setFixedSize(800, 600)
        # Frameless window matching modern app style if desired, 
        # but standard dialog with title bar is safer for now.
        # Image shows a modal floating in center.
        
        self.update_manager = UpdateManager()
        self.update_manager.update_available.connect(self._on_update_available)
        self.update_manager.no_update.connect(self._on_no_update)
        self.update_manager.check_failed.connect(self._on_update_error)
        self.update_manager.download_progress.connect(self._on_download_progress)
        self.update_manager.download_complete.connect(self._on_download_complete)
        self.update_manager.download_error.connect(self._on_update_error)
        self.update_manager.install_complete.connect(self._on_install_complete)
        
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
        
        # Excluded Appearance/Account per instructions
        
        sidebar_layout.addStretch()
        
        # Done Button
        done_btn = QPushButton("Done")
        done_btn.setCursor(Qt.PointingHandCursor)
        done_btn.setFixedHeight(36)
        done_btn.setStyleSheet(f"""
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
        done_btn.clicked.connect(self.accept)
        sidebar_layout.addWidget(done_btn)
        
        layout.addWidget(sidebar)
        
        # --- Content Area ---
        content = QFrame()
        content.setStyleSheet(f"background-color: {theme.colors.background};")
        
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(40, 40, 40, 40)
        
        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)
        
        # Add Pages
        self.stack.addWidget(self.create_general_page())
        self.stack.addWidget(self._create_placeholder_page("Security Settings"))
        self.stack.addWidget(self._create_placeholder_page("Privacy Settings"))
        
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

    def _setup_general_settings(self, layout):
        config = get_config()
        
        # Maps for settings
        auto_lock_map = {
            "After 15 minutes": 900,
            "After 5 minutes": 300,
            "After 1 minute": 60,
            "Never": 0
        }
        
        clipboard_map = {
            "60 seconds": 60,
            "30 seconds": 30,
            "10 seconds": 10,
            "Never": 0
        }
        
        # Reverse maps for initialization
        rev_auto_lock = {v: k for k, v in auto_lock_map.items()}
        rev_clipboard = {v: k for k, v in clipboard_map.items()}
        
        # Auto-lock
        auto_lock_widget, auto_lock_combo = self._create_dropdown_setting(
            "Auto-lock timer",
            "Automatically lock the vault after inactivity.",
            list(auto_lock_map.keys())
        )
        
        current_lock = config.get_auto_lock_timeout()
        # Find closest match or default
        if current_lock in rev_auto_lock:
            auto_lock_combo.setCurrentText(rev_auto_lock[current_lock])
            
        auto_lock_combo.currentTextChanged.connect(
            lambda text: config.set_auto_lock_timeout(auto_lock_map.get(text, 900))
        )
        
        layout.addWidget(auto_lock_widget)
        layout.addWidget(self._create_separator())
        
        # Clipboard
        clip_widget, clip_combo = self._create_dropdown_setting(
            "Clear clipboard after",
            "Remove copied passwords from clipboard for security.",
            list(clipboard_map.keys())
        )
        
        current_clip = config.get_clipboard_timeout()
        if current_clip in rev_clipboard:
            clip_combo.setCurrentText(rev_clipboard[current_clip])
            
        clip_combo.currentTextChanged.connect(
            lambda text: config.set_clipboard_timeout(clipboard_map.get(text, 60))
        )
        
        layout.addWidget(clip_widget)
        layout.addWidget(self._create_separator())
        
        # Notifications
        notif_widget, notif_toggle = self._create_toggle_setting(
            "Show desktop notifications",
            "Get alerts for security updates and vault activities.",
            config.get_notifications_enabled()
        )
        notif_toggle.stateChanged.connect(
            lambda state: config.set_notifications_enabled(state == Qt.Checked)
        )
        layout.addWidget(notif_widget)

    def create_general_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(24)
        
        theme = get_theme()
        
        # Header
        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)
        
        page_title = QLabel("General Settings")
        page_title.setStyleSheet(f"""
            color: {theme.colors.foreground};
            font-size: 18px;
            font-weight: 600;
        """)
        header_layout.addWidget(page_title)
        
        page_subtitle = QLabel("Manage your application preferences and behavior.")
        page_subtitle.setStyleSheet(f"""
            color: {theme.colors.muted_foreground};
            font-size: 14px;
        """)
        header_layout.addWidget(page_subtitle)
        
        layout.addWidget(header)
        layout.addSpacing(8)
        
        # Language (Functional logic omitted for now as requested specific buttons)
        lang_widget, _ = self._create_dropdown_setting(
            "Language selection",
            "Choose the display language for the interface.",
            ["English (US)", "Portuguese (BR)", "Spanish"]
        )
        layout.addWidget(lang_widget)
        layout.addWidget(self._create_separator())
        
        self._setup_general_settings(layout)
        
        layout.addWidget(self._create_separator())
        self._setup_update_section(layout)
        
        layout.addStretch()
        
        return page

    def _create_dropdown_setting(self, title: str, subtitle: str, options: list) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        theme = get_theme()
        
        # --- Lado Esquerdo (Textos) ---
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        label_title = QLabel(title)
        label_title.setStyleSheet(f"color: {theme.colors.foreground}; font-size: 14px; font-weight: 500;")
        text_layout.addWidget(label_title)
        
        label_sub = QLabel(subtitle)
        label_sub.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 12px;")
        text_layout.addWidget(label_sub)
        
        layout.addLayout(text_layout)
        
        # --- O SELECT (QComboBox) ---
        combo = QComboBox()
        combo.addItems(options)
        combo.setCursor(Qt.PointingHandCursor)
        combo.setFixedWidth(200) # Largura fixa para ficar elegante
        

        combo.setStyleSheet(f"""
            QComboBox {{
                background-color: #09090b;
                border: 1px solid #27272a;
                border-radius: 8px;
                padding: 8px 12px;
                color: #e4e4e7;
                font-size: 13px;
                font-family: 'Segoe UI', sans-serif;
            }}
            
            QComboBox:hover {{
                border: 1px solid #3f3f46;
                background-color: #18181b;
            }}

            QComboBox::down-arrow {{
                image: url({get_icon_path("chevron-down")});
                width: 16px;
                height: 16px;
                margin-right: 10px;
            }}

            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            
            /* --- CORREÇÃO AQUI --- */
            QComboBox QAbstractItemView {{
                background-color: #09090b; /* Fundo do menu */
                
                /* Define a borda escura para sobrescrever a branca */
                border: 1px solid #27272a; 
                
                /* Importante: remove o anel de foco/seleção branco */
                outline: 0px; 
                
                border-radius: 8px;
                color: #e4e4e7;
                selection-background-color: #27272a;
                selection-color: white;
                padding: 4px;
            }}
        """)
        
        layout.addWidget(combo)
        return widget, combo
        
    def _create_toggle_setting(self, title: str, subtitle: str, checked: bool) -> tuple[QWidget, ToggleSwitch]:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        theme = get_theme()
        
        # Labels
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        label_title = QLabel(title)
        label_title.setStyleSheet(f"""
            color: {theme.colors.foreground};
            font-size: 14px;
            font-weight: 500;
        """)
        text_layout.addWidget(label_title)
        
        label_sub = QLabel(subtitle)
        label_sub.setStyleSheet(f"""
            color: {theme.colors.muted_foreground};
            font-size: 12px;
        """)
        text_layout.addWidget(label_sub)
        
        layout.addLayout(text_layout)
        
        # Control
        # Using native QCheckBox for simplicity if custom one fails, but I wrote a custom ToggleSwitch class above
        toggle = ToggleSwitch()
        toggle.setChecked(checked)
        
        return widget, toggle

    def _create_separator(self) -> QFrame:
        sep = QFrame()
        sep.setFixedHeight(1)
        theme = get_theme()
        sep.setStyleSheet(f"background-color: {theme.colors.border};")
        return sep

    def _create_placeholder_page(self, title: str) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        
        theme = get_theme()
        label = QLabel(title)
        label.setStyleSheet(f"color: {theme.colors.foreground}; font-size: 16px;")
        layout.addWidget(label)
        layout.addStretch()
        return page

    def _setup_update_section(self, layout):
        theme = get_theme()
        
        # Container
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        
        # Text
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        title = QLabel(f"Version {__version__}")
        title.setStyleSheet(f"color: {theme.colors.foreground}; font-size: 14px; font-weight: 500;")
        text_layout.addWidget(title)
        
        subtitle = QLabel("Check for the latest updates on GitHub.")
        subtitle.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 12px;")
        text_layout.addWidget(subtitle)
        
        row.addLayout(text_layout)
        
        # Button
        self.btn_update = QPushButton("Check for Updates")
        self.btn_update.setCursor(Qt.PointingHandCursor)
        self.btn_update.setFixedWidth(140)
        self.btn_update.setFixedHeight(32)
        self.btn_update.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.colors.sidebar_accent}; 
                border: 1px solid {theme.colors.border};
                color: {theme.colors.foreground};
                border-radius: 6px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors.border};
            }}
            QPushButton:disabled {{
                opacity: 0.5;
            }}
        """)
        self.btn_update.clicked.connect(self._check_update)
        row.addWidget(self.btn_update)
        
        layout.addWidget(container)

    def _check_update(self):
        self.btn_update.setText("Checking...")
        self.btn_update.setEnabled(False)
        self.update_manager.check_for_updates()
        
    def _on_update_available(self, version, url):
        self.btn_update.setText("Update Now")
        self.btn_update.setEnabled(True)
        self.latest_download_url = url
        
        reply = QMessageBox.question(
            self, 
            "Update Available", 
            f"A new version ({version}) is available!\nDo you want to download and install it now?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.btn_update.setText("Starting...")
            self.btn_update.setEnabled(False)
            self.update_manager.download_update(url)
            
    def _on_no_update(self):
        self.btn_update.setText("Check for Updates")
        self.btn_update.setEnabled(True)
        QMessageBox.information(self, "Up to Date", "You are using the latest version.")
        
    def _on_update_error(self, error):
        self.btn_update.setText("Check for Updates")
        self.btn_update.setEnabled(True)
        QMessageBox.warning(self, "Update Failed", f"Error:\n{error}")

    def _on_download_progress(self, percent):
        self.btn_update.setText(f"Downloading {percent}%")
        
    def _on_download_complete(self, file_path):
        self.btn_update.setText("Installing...")
        # Determine project root (app level or repo level?)
        # Current file: app/ui/settings_dialog.py
        # app module: app/
        # Root: app/..
        root = str(Path(__file__).resolve().parent.parent.parent)
        self.update_manager.install_update(file_path, root)
        
    def _on_install_complete(self):
        self.btn_update.setText("Updated!")
        QMessageBox.information(
            self, 
            "Update Complete", 
            "The application has been updated successfully.\nPlease restart the application to apply changes."
        )
