
from pathlib import Path

from PySide6.QtWidgets import (

    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,

    QFrame, QMessageBox, QProgressBar, QProgressDialog, QApplication,

    QScrollArea

)

from PySide6.QtCore import Qt, QTimer

from PySide6.QtGui import QIcon

from app.core.gdrive import get_gdrive_manager

from app.core.config import get_config

from ..theme import get_theme

from ..ui_utils import get_icon_path

from .components import create_toggle_setting, create_separator, ToggleSwitch

class CloudStorageTab(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.gdrive = get_gdrive_manager()

        self.config = get_config()

        self.setup_ui()

        self.refresh_timer = QTimer(self)

        self.refresh_timer.timeout.connect(self._refresh_state)

        self.refresh_timer.start(5000)

    def setup_ui(self):

        # Main layout with scroll area
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        # Content widget inside scroll area
        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(0, 0, 8, 0)  # Right margin for scrollbar
        layout.setSpacing(12)

        theme = get_theme()

        header = QWidget()

        header_layout = QVBoxLayout(header)

        header_layout.setContentsMargins(0, 0, 0, 0)

        header_layout.setSpacing(4)

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
            font-size: 13px;
        """)

        header_layout.addWidget(page_subtitle)

        layout.addWidget(header)

        connections_label = QLabel("ACTIVE CONNECTIONS")

        connections_label.setStyleSheet("""
            color: #3b82f6;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
        """)

        layout.addWidget(connections_label)

        self._create_gdrive_card(layout, theme)

        layout.addSpacing(4)

        self._create_storage_usage_section(layout, theme)

        layout.addSpacing(4)

        self._create_storage_options_section(layout, theme)

        layout.addStretch()

        # Set scroll area content
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        if self.gdrive.is_connected():

            user_info = self.gdrive.get_user_info()

            self.gdrive_email_label.setText((user_info.get("email") if user_info else None) or "Connected")

        else:

            self.gdrive_email_label.setText("Not connected")

    def _create_gdrive_card(self, layout, theme):

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

        self.gdrive_connect_btn = QPushButton("Connect")

        self.gdrive_connect_btn.setCursor(Qt.PointingHandCursor)

        self.gdrive_connect_btn.setFixedHeight(32)

        self.gdrive_connect_btn.clicked.connect(self._on_gdrive_button_clicked)

        gdrive_layout.addWidget(self.gdrive_connect_btn)

        layout.addWidget(self.gdrive_card)

    def _create_storage_usage_section(self, layout, theme):

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

        self.usage_bar_container = QFrame()

        self.usage_bar_container.setFixedHeight(6)

        self.usage_bar_container.setStyleSheet(f"""
            background-color: {theme.colors.border};
            border-radius: 3px;
            border: none;
        """)

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

        options_label = QLabel("STORAGE OPTIONS")

        options_label.setStyleSheet("""
            color: #3b82f6;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
        """)

        layout.addWidget(options_label)

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

        auto_sync_checked = True

        auto_sync_widget, self.auto_sync_toggle = create_toggle_setting(

            "Auto-sync on change",

            "Immediately backup changes to the cloud when you edit your vault.",

            auto_sync_checked

        )

        self.auto_sync_toggle.stateChanged.connect(self._on_auto_sync_changed)

        options_layout.addWidget(auto_sync_widget)

        layout.addWidget(options_container)

        # Manual sync section
        sync_label = QLabel("MANUAL SYNC")

        sync_label.setStyleSheet("""
            color: #3b82f6;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
            margin-top: 16px;
        """)

        layout.addWidget(sync_label)

        sync_container = QFrame()

        sync_container.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.colors.card};
                border: 1px solid {theme.colors.border};
                border-radius: 12px;
            }}
        """)

        sync_buttons_layout = QHBoxLayout(sync_container)

        sync_buttons_layout.setContentsMargins(16, 12, 16, 12)

        sync_buttons_layout.setSpacing(12)

        # Download button
        self.download_btn = QPushButton("⬇ Download from Cloud")

        self.download_btn.setCursor(Qt.PointingHandCursor)

        self.download_btn.setFixedHeight(36)

        self.download_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #6b7280;
                color: #9ca3af;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(107, 114, 128, 0.1);
                border-color: #9ca3af;
                color: #d1d5db;
            }
            QPushButton:disabled {
                background-color: #1f2937;
                border-color: #374151;
                color: #4b5563;
            }
        """)

        self.download_btn.clicked.connect(self._on_download_clicked)

        sync_buttons_layout.addWidget(self.download_btn)

        # Smart Sync button (main action)
        self.smart_sync_btn = QPushButton("🔄 Smart Sync")

        self.smart_sync_btn.setCursor(Qt.PointingHandCursor)

        self.smart_sync_btn.setFixedHeight(36)

        self.smart_sync_btn.setStyleSheet("""
            QPushButton {
                background-color: #22c55e;
                border: none;
                color: white;
                border-radius: 6px;
                padding: 6px 20px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #16a34a;
            }
            QPushButton:disabled {
                background-color: #4b5563;
                color: #9ca3af;
            }
        """)

        self.smart_sync_btn.clicked.connect(self._on_smart_sync_clicked)

        sync_buttons_layout.addWidget(self.smart_sync_btn)

        # Upload button
        self.upload_btn = QPushButton("⬆ Upload")

        self.upload_btn.setCursor(Qt.PointingHandCursor)

        self.upload_btn.setFixedHeight(36)

        self.upload_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #6b7280;
                color: #9ca3af;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(107, 114, 128, 0.1);
                border-color: #9ca3af;
                color: #d1d5db;
            }
            QPushButton:disabled {
                border-color: #374151;
                color: #4b5563;
            }
        """)

        self.upload_btn.clicked.connect(self._on_upload_clicked)

        sync_buttons_layout.addWidget(self.upload_btn)

        layout.addWidget(sync_container)

        # Sync description
        sync_desc = QLabel("Smart Sync merges local and cloud credentials, keeping all unique entries.")
        sync_desc.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 11px; margin-top: 4px;")
        layout.addWidget(sync_desc)

        # Update button states based on connection
        self._update_sync_buttons()

    def _on_auto_sync_changed(self, state):

        is_checked = state == Qt.Checked

        print(f"[Settings] Auto-sync toggled: {is_checked}")

        self.config.set("cloud/auto_sync", is_checked)

    def _refresh_state(self):

        theme = get_theme()

        if self.gdrive.is_connected():

            user_info = self.gdrive.get_user_info()

            if user_info:

                email = user_info.get("email", "Connected")

                self.gdrive_email_label.setText(email)

            else:

                self.gdrive_email_label.setText("Connected")

            self.gdrive_status_badge.setVisible(True)

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

            self._update_storage_usage()

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

            self.usage_amount_label.setText("-- OF 15 GB USED")

            self.usage_bar_fill.setFixedWidth(0)

            self.usage_desc_label.setText("Connect to Google Drive to see storage usage.")

        # Update sync buttons
        self._update_sync_buttons()

    def _update_storage_usage(self):

        if hasattr(self, "_storage_worker") and self._storage_worker.isRunning():

            return

        self._storage_worker = StorageWorker(self.gdrive)

        self._storage_worker.finished.connect(self._on_storage_info_ready)

        self._storage_worker.start()

    def _on_storage_info_ready(self, storage_info):

        try:

            if storage_info:

                used_bytes = storage_info.get("used", 0)

                total_bytes = storage_info.get("total", 0)

                percent = storage_info.get("percent", 0)

                unlimited = storage_info.get("unlimited", False)

                used_str = self._format_bytes(used_bytes)

                if unlimited:

                    self.usage_amount_label.setText(f"{used_str} USED (UNLIMITED)")

                    self.usage_bar_fill.setFixedWidth(0)

                else:

                    total_str = self._format_bytes(total_bytes)

                    self.usage_amount_label.setText(f"{used_str} OF {total_str} USED")

                    if self.usage_bar_container.width() > 0:

                        bar_width = int((self.usage_bar_container.width() * percent) / 100)

                        bar_width = max(bar_width, 3 if used_bytes > 0 else 0)

                        self.usage_bar_fill.setFixedWidth(bar_width)

            else:

                self._update_storage_usage_fallback()

        except Exception as e:

            print(f"Error processing storage usage: {e}")

            self._update_storage_usage_fallback()

    def _update_storage_usage_fallback(self):

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

        if self.gdrive.is_connected():

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

            from ..gdrive_dialog import GoogleDriveDialog

            parent = self.window()

            dialog = GoogleDriveDialog(parent)

            dialog.connection_successful.connect(self._refresh_state)

            dialog.exec()

            self._refresh_state()

    def _update_sync_buttons(self):
        """Update sync buttons based on connection state."""
        is_connected = self.gdrive.is_connected()
        if hasattr(self, 'download_btn'):
            self.download_btn.setEnabled(is_connected)
        if hasattr(self, 'upload_btn'):
            self.upload_btn.setEnabled(is_connected)
        if hasattr(self, 'smart_sync_btn'):
            self.smart_sync_btn.setEnabled(is_connected)

    def _on_smart_sync_clicked(self):
        """Perform smart sync that merges local and cloud vaults."""
        if not self.gdrive.is_connected():
            QMessageBox.warning(
                self,
                "Not Connected",
                "Please connect to Google Drive first."
            )
            return

        reply = QMessageBox.question(
            self,
            "Smart Sync",
            "This will merge your local vault with the cloud vault:\n\n"
            "• Credentials only on this device will be kept\n"
            "• Credentials only in cloud will be added locally\n"
            "• Duplicates will keep the most recent version\n"
            "• The merged result will be uploaded to cloud\n\n"
            "Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply != QMessageBox.Yes:
            return

        progress = QProgressDialog(
            "Starting Smart Sync...",
            None,
            0, 100,
            self
        )
        progress.setWindowTitle("Smart Sync")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        progress.show()
        QApplication.processEvents()

        def on_progress(percent: int, message: str):
            progress.setValue(percent)
            progress.setLabelText(message)
            QApplication.processEvents()

        try:
            vault_path = Path.home() / '.vaultkeeper' / 'vault.db'
            
            stats = self.gdrive.merge_vaults(
                vault_path=vault_path,
                progress_callback=on_progress
            )
            
            progress.setValue(100)
            QApplication.processEvents()

            # Build result message
            if stats.get("local_only") == -1:
                message = "No cloud vault found.\nYour local vault was uploaded."
            elif stats.get("cloud_only") == -1:
                message = "No local vault found.\nCloud vault was downloaded."
            else:
                message = (
                    f"Sync completed successfully!\n\n"
                    f"📊 Results:\n"
                    f"• Only local: {stats.get('local_only', 0)} credentials\n"
                    f"• Only cloud: {stats.get('cloud_only', 0)} credentials\n"
                    f"• Updated from cloud: {stats.get('updated_from_cloud', 0)}\n"
                    f"• Updated from local: {stats.get('updated_from_local', 0)}\n"
                    f"• Unchanged: {stats.get('unchanged', 0)}\n"
                    f"• Total: {stats.get('total_after_merge', 0)} credentials\n\n"
                    f"Please restart the app to see changes."
                )

            QMessageBox.information(
                self,
                "Sync Complete",
                message
            )

        except Exception as e:
            progress.close()
            QMessageBox.critical(
                self,
                "Sync Failed",
                f"Smart sync failed:\n\n{str(e)}"
            )

    def _on_download_clicked(self):
        """Download vault from Google Drive."""
        if not self.gdrive.is_connected():
            QMessageBox.warning(
                self,
                "Not Connected",
                "Please connect to Google Drive first."
            )
            return

        reply = QMessageBox.question(
            self,
            "Download Vault",
            "This will replace your local vault with the version from Google Drive.\n\n"
            "A backup of your current vault will be saved.\n\n"
            "Are you sure you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        progress = QProgressDialog(
            "Downloading vault from Google Drive...",
            None,
            0, 100,
            self
        )
        progress.setWindowTitle("Syncing")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(10)
        progress.show()
        QApplication.processEvents()

        try:
            vault_path = Path.home() / '.vaultkeeper' / 'vault.db'
            
            progress.setValue(30)
            QApplication.processEvents()
            
            self.gdrive.download_vault(vault_path)
            
            progress.setValue(100)
            QApplication.processEvents()

            QMessageBox.information(
                self,
                "Download Complete",
                "Vault downloaded successfully from Google Drive!\n\n"
                "Please restart the application to load the updated credentials."
            )

        except FileNotFoundError:
            progress.close()
            QMessageBox.warning(
                self,
                "No Vault Found",
                "No vault file was found in your Google Drive.\n\n"
                "You may need to upload your vault first."
            )
        except Exception as e:
            progress.close()
            QMessageBox.critical(
                self,
                "Download Failed",
                f"Failed to download vault:\n\n{str(e)}"
            )

    def _on_upload_clicked(self):
        """Upload vault to Google Drive."""
        if not self.gdrive.is_connected():
            QMessageBox.warning(
                self,
                "Not Connected",
                "Please connect to Google Drive first."
            )
            return

        vault_path = Path.home() / '.vaultkeeper' / 'vault.db'
        if not vault_path.exists():
            QMessageBox.warning(
                self,
                "No Local Vault",
                "No local vault found to upload."
            )
            return

        reply = QMessageBox.question(
            self,
            "Upload Vault",
            "This will upload your local vault to Google Drive,\n"
            "replacing any existing version in the cloud.\n\n"
            "Are you sure you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply != QMessageBox.Yes:
            return

        progress = QProgressDialog(
            "Uploading vault to Google Drive...",
            None,
            0, 100,
            self
        )
        progress.setWindowTitle("Syncing")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(10)
        progress.show()
        QApplication.processEvents()

        try:
            progress.setValue(30)
            QApplication.processEvents()
            
            self.gdrive.upload_vault(vault_path)
            
            progress.setValue(100)
            QApplication.processEvents()

            QMessageBox.information(
                self,
                "Upload Complete",
                "Vault uploaded successfully to Google Drive!"
            )

        except Exception as e:
            progress.close()
            QMessageBox.critical(
                self,
                "Upload Failed",
                f"Failed to upload vault:\n\n{str(e)}"
            )

    def showEvent(self, event):

        super().showEvent(event)

        self._refresh_state()

    def hideEvent(self, event):

        super().hideEvent(event)

from PySide6.QtCore import QThread, Signal

class StorageWorker(QThread):

    finished = Signal(dict)

    def __init__(self, gdrive):

        super().__init__()

        self.gdrive = gdrive

    def run(self):

        try:

            info = self.gdrive.get_storage_info()

            self.finished.emit(info or {})

        except Exception as e:

            print(f"Storage fetch error: {e}")

            self.finished.emit({})
