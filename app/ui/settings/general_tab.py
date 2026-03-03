
from pathlib import Path

from PySide6.QtWidgets import (

    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,

    QComboBox, QMessageBox, QSizePolicy

)

from PySide6.QtCore import Qt

from PySide6.QtGui import QDesktopServices

from app import __version__

from app.core.updater import UpdateManager

from app.core.config import get_config

from ..theme import get_theme

from ..ui_utils import get_icon_path

from .components import create_toggle_setting, create_separator, ToggleSwitch

class GeneralTab(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

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

        layout = QVBoxLayout(self)

        layout.setContentsMargins(0, 0, 0, 0)

        layout.setSpacing(24)

        theme = get_theme()

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



        self._setup_general_settings(layout)

        layout.addWidget(create_separator())

        self._setup_browser_section(layout)

        layout.addWidget(create_separator())

        self._setup_update_section(layout)

        layout.addStretch()

    def _setup_browser_section(self, layout):
        theme = get_theme()
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        title = QLabel("Browser Connection")
        title.setStyleSheet(f"color: {theme.colors.foreground}; font-size: 14px; font-weight: 500;")
        title.setWordWrap(True)
        text_layout.addWidget(title)
        
        subtitle = QLabel("Repair connection with browser extension if it stops working.")
        subtitle.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 12px;")
        subtitle.setWordWrap(True)
        text_layout.addWidget(subtitle)
        
        row.addLayout(text_layout, 1)
        
        btn_repair = QPushButton("Repair Connection")
        btn_repair.setCursor(Qt.PointingHandCursor)
        btn_repair.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        btn_repair.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.colors.sidebar_accent};
                border: 1px solid {theme.colors.border};
                color: {theme.colors.foreground};
                border-radius: 6px;
                font-size: 13px;
                padding: 6px 16px;
                min-height: 20px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors.border};
            }}
        """)
        btn_repair.clicked.connect(self._repair_connection)
        row.addWidget(btn_repair)
        
        layout.addWidget(container)

    def _repair_connection(self):
        try:
            from .connection_dialog import BrowserRepairDialog
            dialog = BrowserRepairDialog(self.window())
            dialog.exec()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open connection tool: {e}")

    def _setup_general_settings(self, layout):

        config = get_config()

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

        rev_auto_lock = {v: k for k, v in auto_lock_map.items()}

        rev_clipboard = {v: k for k, v in clipboard_map.items()}

        auto_lock_widget, auto_lock_combo = self._create_dropdown_setting(

            "Auto-lock timer",

            "Automatically lock the vault after inactivity.",

            list(auto_lock_map.keys())

        )

        current_lock = config.get_auto_lock_timeout()

        if current_lock in rev_auto_lock:

            auto_lock_combo.setCurrentText(rev_auto_lock[current_lock])

        auto_lock_combo.currentTextChanged.connect(

            lambda text: config.set_auto_lock_timeout(auto_lock_map.get(text, 900))

        )

        layout.addWidget(auto_lock_widget)

        layout.addWidget(create_separator())

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



    def _create_dropdown_setting(self, title: str, subtitle: str, options: list):

        widget = QWidget()

        layout = QHBoxLayout(widget)

        layout.setContentsMargins(0, 0, 0, 0)

        theme = get_theme()

        text_layout = QVBoxLayout()

        text_layout.setSpacing(4)

        label_title = QLabel(title)

        label_title.setStyleSheet(f"color: {theme.colors.foreground}; font-size: 14px; font-weight: 500;")
        label_title.setWordWrap(True)

        text_layout.addWidget(label_title)

        label_sub = QLabel(subtitle)

        label_sub.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 12px;")
        label_sub.setWordWrap(True)

        text_layout.addWidget(label_sub)

        layout.addLayout(text_layout, 1)

        combo = QComboBox()

        combo.addItems(options)

        combo.setCursor(Qt.PointingHandCursor)

        combo.setMinimumWidth(200)

        combo.setStyleSheet(f"""
            QComboBox {{

                background-color: #09090b;
                border: 1px solid #27272a;
                border-radius: 8px;
                padding: 8px 12px;
                color: #e4e4e7;
                font-size: 13px;
            }}
            QComboBox:hover {{

                border: 1px solid #3f3f46;
                background-color: #18181b;
            }}
            QComboBox::down-arrow {{

                image: url({{get_icon_path("chevron-down-white").replace('\\', '/')}});
                width: 16px;
                height: 16px;
                margin-right: 10px;
                color: #e4e4e7;
            }}
            QComboBox::drop-down {{

                border: none;
                width: 30px;
            }}
            QComboBox QAbstractItemView {{

                background-color: #09090b;
                border: 1px solid #27272a;
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

    def _setup_update_section(self, layout):

        theme = get_theme()

        container = QWidget()

        row = QHBoxLayout(container)

        row.setContentsMargins(0, 0, 0, 0)

        text_layout = QVBoxLayout()

        text_layout.setSpacing(4)

        title = QLabel(f"Version {__version__}")

        title.setStyleSheet(f"color: {theme.colors.foreground}; font-size: 14px; font-weight: 500;")
        title.setWordWrap(True)

        text_layout.addWidget(title)

        subtitle = QLabel("Check for the latest updates on GitHub.")

        subtitle.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 12px;")
        subtitle.setWordWrap(True)

        text_layout.addWidget(subtitle)

        row.addLayout(text_layout, 1)

        self.btn_update = QPushButton("Check for Updates")
        self.btn_update.setCursor(Qt.PointingHandCursor)
        self.btn_update.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.btn_update.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.colors.sidebar_accent};
                border: 1px solid {theme.colors.border};
                color: {theme.colors.foreground};
                border-radius: 6px;
                font-size: 13px;
                padding: 6px 16px;
                min-height: 20px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors.border};
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
        self.latest_download_url = url
        
        import platform
        if platform.system().lower() == "linux":
            reply = QMessageBox.question(
                self,
                "Update Available",
                f"A new version ({version}) is available!\n\nDue to Linux security policies, you need to download the AppImage manually.\n\nOpen download page?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                QDesktopServices.openUrl(url)
                self.btn_update.setText("Open Download")
                self.btn_update.setEnabled(True)
        else:
            self.btn_update.setText("Update Now")
            self.btn_update.setEnabled(True)
            
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

        root = str(Path(__file__).resolve().parent.parent.parent.parent)

        self.update_manager.install_update(file_path, root)

    def _on_install_complete(self):

        self.btn_update.setText("Updated!")

        QMessageBox.information(

            self,

            "Update Complete",

            "The application has been updated successfully.\nPlease restart the application to apply changes."

        )
