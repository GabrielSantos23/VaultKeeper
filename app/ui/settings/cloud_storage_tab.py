"""
VaultKeeper - Cloud Storage Settings Tab
Manages Google Drive synchronization and backup preferences
"""

from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon

from app.core.gdrive import get_gdrive_manager
from app.core.config import get_config

from ..theme import get_theme
from ..ui_utils import get_icon_path
from .components import create_toggle_setting, create_separator, ToggleSwitch


class CloudStorageTab(QWidget):
    """Cloud Storage settings tab with Google Drive integration."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gdrive = get_gdrive_manager()
        self.config = get_config()
        self.setup_ui()
        
        # Set up periodic refresh
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._refresh_state)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(24)
        
        theme = get_theme()
        
        # Header
        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)
        
        page_title = QLabel("Cloud Storage")
        page_title.setStyleSheet(f"""
            color: {theme.colors.foreground};
            font-size: 18px;
            font-weight: 600;
        """)
        header_layout.addWidget(page_title)
        
        page_subtitle = QLabel("Manage your vault synchronization and backup preferences.")
        page_subtitle.setStyleSheet(f"""
            color: {theme.colors.muted_foreground};
            font-size: 14px;
        """)
        header_layout.addWidget(page_subtitle)
        
        layout.addWidget(header)
        
        # === ACTIVE CONNECTIONS SECTION ===
        connections_label = QLabel("ACTIVE CONNECTIONS")
        connections_label.setStyleSheet("""
            color: #3b82f6;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
        """)
        layout.addWidget(connections_label)
        
        # Google Drive Card
        self._create_gdrive_card(layout, theme)
        
        layout.addSpacing(8)
        
        # === STORAGE USAGE SECTION ===
        self._create_storage_usage_section(layout, theme)
        
        layout.addSpacing(16)
        
        # === STORAGE OPTIONS SECTION ===
        self._create_storage_options_section(layout, theme)
        
        layout.addStretch()
        
        layout.addStretch()
        
        # Initial UI state (Active/Not active) without blocking network calls
        # self._refresh_state() will be called on showEvent
        if self.gdrive.is_connected():
            user_info = self.gdrive.get_user_info()
            self.gdrive_email_label.setText((user_info.get("email") if user_info else None) or "Connected")
        else:
            self.gdrive_email_label.setText("Not connected")
    
    def _create_gdrive_card(self, layout, theme):
        """Create the Google Drive connection card."""
        self.gdrive_card = QFrame()
        self.gdrive_card.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.colors.card};
                border: 1px solid {theme.colors.border};
                border-radius: 12px;
            }}
        """)
        
        gdrive_layout = QHBoxLayout(self.gdrive_card)
        gdrive_layout.setContentsMargins(16, 12, 16, 12)
        gdrive_layout.setSpacing(12)
        
        # Google icon with white background
        icon_container = QFrame()
        icon_container.setFixedSize(40, 40)
        icon_container.setStyleSheet("""
            background-color: #ffffff;
            border-radius: 8px;
        """)
        icon_layout = QHBoxLayout(icon_container)
        icon_layout.setContentsMargins(4, 4, 4, 4)
        
        google_icon = QLabel()
        google_icon_path = get_icon_path("google_icon")
        if google_icon_path:
            pixmap = QIcon(google_icon_path).pixmap(24, 24)
            google_icon.setPixmap(pixmap)
        google_icon.setAlignment(Qt.AlignCenter)
        icon_layout.addWidget(google_icon)
        
        gdrive_layout.addWidget(icon_container)
        
        # Text info
        gdrive_text_layout = QVBoxLayout()
        gdrive_text_layout.setSpacing(2)
        
        gdrive_title = QLabel("Google Drive")
        gdrive_title.setStyleSheet(f"color: {theme.colors.foreground}; font-size: 14px; font-weight: 500; border: none; background: transparent;")
        gdrive_text_layout.addWidget(gdrive_title)
        
        self.gdrive_email_label = QLabel("Not connected")
        self.gdrive_email_label.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 12px; border: none; background: transparent;")
        gdrive_text_layout.addWidget(self.gdrive_email_label)
        
        gdrive_layout.addLayout(gdrive_text_layout)
        gdrive_layout.addStretch()
        
        # Status badge
        self.gdrive_status_badge = QLabel("● SYNCED")
        self.gdrive_status_badge.setStyleSheet("""
            color: #22c55e;
            background-color: rgba(34, 197, 94, 0.15);
            border-radius: 10px;
            padding: 4px 10px;
            font-size: 11px;
            font-weight: 600;
        """)
        self.gdrive_status_badge.setVisible(False)
        gdrive_layout.addWidget(self.gdrive_status_badge)
        
        # Connect/Disconnect button
        self.gdrive_connect_btn = QPushButton("Connect")
        self.gdrive_connect_btn.setCursor(Qt.PointingHandCursor)
        self.gdrive_connect_btn.setFixedHeight(32)
        self.gdrive_connect_btn.clicked.connect(self._on_gdrive_button_clicked)
        gdrive_layout.addWidget(self.gdrive_connect_btn)
        
        layout.addWidget(self.gdrive_card)
    
    def _create_storage_usage_section(self, layout, theme):
        """Create the storage usage section with progress bar."""
        usage_header = QHBoxLayout()
        
        usage_label = QLabel("STORAGE USAGE")
        usage_label.setStyleSheet("""
            color: #3b82f6;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
        """)
        usage_header.addWidget(usage_label)
        
        usage_header.addStretch()
        
        self.usage_amount_label = QLabel("-- OF 15 GB USED")
        self.usage_amount_label.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 11px; border: none; background: transparent;")
        usage_header.addWidget(self.usage_amount_label)
        
        layout.addLayout(usage_header)
        
        # Progress bar container
        self.usage_bar_container = QFrame()
        self.usage_bar_container.setFixedHeight(6)
        self.usage_bar_container.setStyleSheet(f"""
            background-color: {theme.colors.border};
            border-radius: 3px;
            border: none;
        """)
        
        # Progress bar fill
        self.usage_bar_fill = QFrame(self.usage_bar_container)
        self.usage_bar_fill.setFixedHeight(6)
        self.usage_bar_fill.setFixedWidth(0)
        self.usage_bar_fill.move(0, 0)
        self.usage_bar_fill.setStyleSheet("""
            background-color: #3b82f6;
            border-radius: 3px;
            border: none;
        """)
        
        layout.addWidget(self.usage_bar_container)
        
        self.usage_desc_label = QLabel("Connect to Google Drive to see storage usage.")
        self.usage_desc_label.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 12px; border: none; background: transparent;")
        layout.addWidget(self.usage_desc_label)
    
    def _create_storage_options_section(self, layout, theme):
        """Create the storage options section with toggles."""
        options_label = QLabel("STORAGE OPTIONS")
        options_label.setStyleSheet("""
            color: #3b82f6;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
        """)
        layout.addWidget(options_label)
        
        # Options container
        options_container = QFrame()
        options_container.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.colors.card};
                border: 1px solid {theme.colors.border};
                border-radius: 12px;
            }}
        """)
        options_layout = QVBoxLayout(options_container)
        options_layout.setContentsMargins(16, 0, 16, 0)
        options_layout.setSpacing(0)
        
        # Auto-sync option
        auto_sync_checked = True # Forced enabled
        
        auto_sync_widget, self.auto_sync_toggle = create_toggle_setting(
            "Auto-sync on change",
            "Immediately backup changes to the cloud when you edit your vault.",
            auto_sync_checked
        )
        self.auto_sync_toggle.stateChanged.connect(self._on_auto_sync_changed)
        options_layout.addWidget(auto_sync_widget)
        
        layout.addWidget(options_container)
    
    def _on_auto_sync_changed(self, state):
        """Handle auto-sync toggle change."""
        is_checked = state == Qt.Checked
        print(f"[Settings] Auto-sync toggled: {is_checked}")
        self.config.set("cloud/auto_sync", is_checked)
    
    def _refresh_state(self):
        """Refresh the UI state based on current connection status."""
        theme = get_theme()
        
        if self.gdrive.is_connected():
            user_info = self.gdrive.get_user_info()
            
            # Update email
            if user_info:
                email = user_info.get("email", "Connected")
                self.gdrive_email_label.setText(email)
            else:
                self.gdrive_email_label.setText("Connected")
            
            # Show synced badge
            self.gdrive_status_badge.setVisible(True)
            
            # Update button to disconnect style
            self.gdrive_connect_btn.setText("Disconnect")
            self.gdrive_connect_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: 1px solid #ef4444;
                    color: #ef4444;
                    border-radius: 6px;
                    padding: 6px 16px;
                    font-size: 13px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: rgba(239, 68, 68, 0.1);
                }
            """)
            
            # Update storage usage
            self._update_storage_usage()
            
            # Update description
            self.usage_desc_label.setText("Your encrypted vault occupies a minimal footprint on your cloud drive.")
            
        else:
            self.gdrive_email_label.setText("Not connected")
            self.gdrive_status_badge.setVisible(False)
            
            self.gdrive_connect_btn.setText("Connect")
            self.gdrive_connect_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3b82f6;
                    border: none;
                    color: white;
                    border-radius: 6px;
                    padding: 6px 16px;
                    font-size: 13px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #2563eb;
                }
            """)
            
            # Reset storage usage
            self.usage_amount_label.setText("-- OF 15 GB USED")
            self.usage_bar_fill.setFixedWidth(0)
            self.usage_desc_label.setText("Connect to Google Drive to see storage usage.")
    
    def _update_storage_usage(self):
        """Update storage usage display asynchronously."""
        # Avoid creating multiple workers
        if hasattr(self, "_storage_worker") and self._storage_worker.isRunning():
            return
            
        self._storage_worker = StorageWorker(self.gdrive)
        self._storage_worker.finished.connect(self._on_storage_info_ready)
        self._storage_worker.start()
        
    def _on_storage_info_ready(self, storage_info):
        """Handle storage info update on main thread."""
        try:
            if storage_info:
                used_bytes = storage_info.get("used", 0)
                total_bytes = storage_info.get("total", 0)
                percent = storage_info.get("percent", 0)
                unlimited = storage_info.get("unlimited", False)
                
                # Format used size
                used_str = self._format_bytes(used_bytes)
                
                if unlimited:
                    # Unlimited storage (Google Workspace, etc.)
                    self.usage_amount_label.setText(f"{used_str} USED (UNLIMITED)")
                    self.usage_bar_fill.setFixedWidth(0)
                else:
                    # Format total size
                    total_str = self._format_bytes(total_bytes)
                    self.usage_amount_label.setText(f"{used_str} OF {total_str} USED")
                    
                    # Update progress bar
                    if self.usage_bar_container.width() > 0:
                        bar_width = int((self.usage_bar_container.width() * percent) / 100)
                        bar_width = max(bar_width, 3 if used_bytes > 0 else 0)
                        self.usage_bar_fill.setFixedWidth(bar_width)
            else:
                # Fallback to vault file size if API fails
                self._update_storage_usage_fallback()
                
        except Exception as e:
            print(f"Error processing storage usage: {e}")
            self._update_storage_usage_fallback()
    
    def _update_storage_usage_fallback(self):
        """Fallback to showing vault file size when API is unavailable."""
        try:
            vault_path = Path.home() / '.vaultkeeper' / 'vault.db'
            
            if vault_path.exists():
                size_bytes = vault_path.stat().st_size
                size_str = self._format_bytes(size_bytes)
                self.usage_amount_label.setText(f"{size_str} (vault size)")
                self.usage_bar_fill.setFixedWidth(3 if size_bytes > 0 else 0)
            else:
                self.usage_amount_label.setText("0 B (no vault)")
                self.usage_bar_fill.setFixedWidth(0)
        except Exception as e:
            print(f"Error getting vault size: {e}")
            self.usage_amount_label.setText("-- UNKNOWN")
    
    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes into human-readable string."""
        if bytes_value < 1024:
            return f"{bytes_value} B"
        elif bytes_value < 1024 * 1024:
            return f"{bytes_value / 1024:.1f} KB"
        elif bytes_value < 1024 * 1024 * 1024:
            return f"{bytes_value / (1024 * 1024):.1f} MB"
        elif bytes_value < 1024 * 1024 * 1024 * 1024:
            return f"{bytes_value / (1024 * 1024 * 1024):.1f} GB"
        else:
            return f"{bytes_value / (1024 * 1024 * 1024 * 1024):.1f} TB"
    
    def _on_gdrive_button_clicked(self):
        """Handle Google Drive connect/disconnect button click."""
        if self.gdrive.is_connected():
            # Disconnect
            reply = QMessageBox.question(
                self,
                "Disconnect Google Drive",
                "Are you sure you want to disconnect from Google Drive?\n\nYour vault backup will no longer sync.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.gdrive.disconnect()
                self._refresh_state()
        else:
            # Connect - open the Google Drive dialog
            from ..gdrive_dialog import GoogleDriveDialog
            
            # Find the main window to center the dialog properly
            parent = self.window()
            dialog = GoogleDriveDialog(parent)
            dialog.connection_successful.connect(self._refresh_state)
            dialog.exec()
            self._refresh_state()
    
    def showEvent(self, event):
        """Refresh state when tab becomes visible."""
        super().showEvent(event)
        self._refresh_state()
    
    def hideEvent(self, event):
        """Stop refreshing when tab is hidden."""
        super().hideEvent(event)


from PySide6.QtCore import QThread, Signal

class StorageWorker(QThread):
    """Worker thread for fetching storage info."""
    finished = Signal(dict)
    
    def __init__(self, gdrive):
        super().__init__()
        self.gdrive = gdrive
        
    def run(self):
        try:
            # This blocks, so we run it in a thread
            info = self.gdrive.get_storage_info()
            self.finished.emit(info or {})
        except Exception as e:
            print(f"Storage fetch error: {e}")
            self.finished.emit({})

