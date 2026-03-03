
from pathlib import Path

from typing import Optional

from PySide6.QtWidgets import (

    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,

    QFrame, QWidget, QGraphicsDropShadowEffect, QApplication,

    QMessageBox, QProgressDialog

)

from PySide6.QtCore import Qt, Signal, QSize, QTimer, QRect, QPoint

from PySide6.QtGui import QIcon, QPixmap, QColor, QFont, QPainter, QBrush

from .theme import get_theme

from .ui_utils import load_svg_icon, get_icon_path

from ..core.gdrive import get_gdrive_manager

class GoogleDriveDialog(QDialog):

    connection_successful = Signal()

    def __init__(self, parent=None):

        super().__init__(parent)

        self.gdrive = get_gdrive_manager()

        self.setup_ui()

        self._update_state()

    def setup_ui(self):

        theme = get_theme()

        self.setWindowTitle("Connect Google Drive")

        self.setModal(True)

        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)

        self.setAttribute(Qt.WA_TranslucentBackground)

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(0, 0, 0, 0)

        main_layout.setSpacing(0)

        self.card = QFrame()

        self.card.setFixedSize(388, 288)

        self.card.setStyleSheet("""
            QFrame {
                background-color: #2a2f38;
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
        """)

        shadow = QGraphicsDropShadowEffect()

        shadow.setBlurRadius(40)

        shadow.setColor(QColor(0, 0, 0, 180))

        shadow.setOffset(0, 8)

        self.card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.card)

        card_layout.setContentsMargins(32, 40, 32, 32)

        card_layout.setSpacing(16)

        icon_container = QWidget()

        icon_container.setFixedSize(56, 56)

        icon_container.setStyleSheet("""
            background-color: #3B82F6;
            border-radius: 12px;
            margin-bottom: 16px;
        """)

        icon_layout = QVBoxLayout(icon_container)

        icon_layout.setContentsMargins(0, 0, 0, 0)

        icon_layout.setAlignment(Qt.AlignCenter)

        cloud_icon = QLabel()

        cloud_icon.setPixmap(load_svg_icon("cloud_lock", 28, "#ffffff"))

        cloud_icon.setAlignment(Qt.AlignCenter)

        icon_layout.addWidget(cloud_icon)

        icon_row = QHBoxLayout()

        icon_row.addStretch()

        icon_row.addWidget(icon_container)

        icon_row.addStretch()

        card_layout.addLayout(icon_row)

        card_layout.addSpacing(8)

        self.title_label = QLabel("Connect Google Drive")

        self.title_label.setAlignment(Qt.AlignCenter)

        self.title_label.setStyleSheet("""
            color: #ffffff;
            font-size: 20px;
            font-weight: 600;
            background: transparent;
            border: none;
        """)

        card_layout.addWidget(self.title_label)

        self.description_label = QLabel("Securely backup and sync your encrypted vault to\nyour Google Drive account.")

        self.description_label.setAlignment(Qt.AlignCenter)

        self.description_label.setWordWrap(True)

        self.description_label.setStyleSheet("""
            color: #9ca3af;
            font-size: 14px;
            line-height: 1.5;
            background: transparent;
            border: none;
        """)

        card_layout.addWidget(self.description_label)

        card_layout.addSpacing(16)

        self.signin_btn = QPushButton()

        self.signin_btn.setCursor(Qt.PointingHandCursor)

        self.signin_btn.setFixedHeight(48)

        self._setup_google_button()

        self.signin_btn.clicked.connect(self._on_signin_clicked)

        card_layout.addWidget(self.signin_btn)

        card_layout.addSpacing(8)

        self.cancel_btn = QPushButton("Cancel")

        self.cancel_btn.setCursor(Qt.PointingHandCursor)

        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #6b7280;
                border: none;
                font-size: 14px;
                font-weight: 500;
                padding: 8px;
            }
            QPushButton:hover {
                color: #9ca3af;
            }
        """)

        self.cancel_btn.clicked.connect(self.reject)

        card_layout.addWidget(self.cancel_btn, alignment=Qt.AlignCenter)

        main_layout.addWidget(self.card)

        self.setFixedSize(self.card.size())

    def _setup_google_button(self, connected: bool = False):

        if connected:

            self.signin_btn.setText("  Disconnect")

            self.signin_btn.setIcon(QIcon())

            self.signin_btn.setStyleSheet("""
                QPushButton {
                    background-color: #dc2626;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 15px;
                    font-weight: 500;
                    padding: 12px 24px;
                }
                QPushButton:hover {
                    background-color: #b91c1c;
                }
            """)

        else:

            self.signin_btn.setText("  Sign in with Google")

            google_icon_path = get_icon_path("google_icon")

            if google_icon_path:

                icon = QIcon(google_icon_path)

                self.signin_btn.setIcon(icon)

                self.signin_btn.setIconSize(QSize(20, 20))

            self.signin_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ffffff;
                    color: #1f2937;
                    border: 1px solid #e5e7eb;
                    border-radius: 8px;
                    font-size: 15px;
                    font-weight: 500;
                    padding: 12px 24px;
                    text-align: center;
                }
                QPushButton:hover {
                    background-color: #f9fafb;
                    border-color: #d1d5db;
                }
            """)

    def _update_state(self):

        if self.gdrive.is_connected():

            self.title_label.setText("Google Drive Connected")

            self.description_label.setText("Your vault is syncing with Google Drive.")

            self._setup_google_button(connected=True)

            self.cancel_btn.setText("Close")

        else:

            self.title_label.setText("Connect Google Drive")

            self.description_label.setText("Securely backup and sync your encrypted vault to\nyour Google Drive account.")

            self._setup_google_button(connected=False)

            self.cancel_btn.setText("Cancel")

    def _on_signin_clicked(self):

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

                self._update_state()

        else:

            if not self.gdrive.is_configured():

                QMessageBox.warning(

                    self,

                    "Not Configured",

                    "Google Drive API credentials are not configured.\n\nPlease check that GDRIVE_CLIENT_ID and GDRIVE_CLIENT_SECRET are set in your .env file."

                )

                return

            self.signin_btn.setEnabled(False)

            self.signin_btn.setText("  Connecting...")

            self.gdrive.authenticate(

                on_success=self._on_auth_success,

                on_error=self._on_auth_error

            )

            self._start_connection_polling()

    def _start_connection_polling(self):

        self._poll_timer = QTimer(self)

        self._poll_timer.timeout.connect(self._check_connection)

        self._poll_timer.start(500)

    def _check_connection(self):

        if self.gdrive.is_connected():

            self._poll_timer.stop()

            self._handle_auth_success()

    def _on_auth_success(self):

        QTimer.singleShot(0, self._handle_auth_success)

    def _handle_auth_success(self):

        if hasattr(self, '_poll_timer'):

            self._poll_timer.stop()

        self.signin_btn.setEnabled(True)

        self._update_state()

        # Check if there's a vault in Google Drive and offer to download
        self._check_and_offer_vault_download()

        self.connection_successful.emit()

    def _check_and_offer_vault_download(self):
        """Check if there's a vault in Google Drive and offer to sync it."""
        try:
            vault_path = Path.home() / '.vaultkeeper' / 'vault.db'
            local_vault_exists = vault_path.exists()
            local_vault_size = vault_path.stat().st_size if local_vault_exists else 0
            
            # Check if vault exists in Google Drive
            import requests
            headers = self.gdrive._get_headers()
            folder_id = self.gdrive._get_or_create_vault_folder()
            
            if not folder_id:
                return
            
            query = f"name='vault.db' and '{folder_id}' in parents and trashed=false"
            params = {"q": query, "fields": "files(id,name,size,modifiedTime)"}
            response = requests.get(
                "https://www.googleapis.com/drive/v3/files",
                headers=headers,
                params=params
            )
            
            if response.status_code != 200:
                return
            
            files = response.json().get("files", [])
            cloud_exists = len(files) > 0
            
            if not cloud_exists and not local_vault_exists:
                # No vault anywhere - nothing to do
                return
            
            if not cloud_exists and local_vault_exists:
                # Only local vault - offer to upload
                reply = QMessageBox.question(
                    self,
                    "Upload Vault",
                    "Nenhum vault encontrado no Google Drive.\n\n"
                    "Deseja fazer upload do vault local para a nuvem?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                if reply == QMessageBox.Yes:
                    self._upload_vault_to_drive(vault_path)
                return
            
            if cloud_exists and not local_vault_exists:
                # Only cloud vault - must download
                message = (
                    "Vault encontrado no Google Drive!\n\n"
                    "Nenhum vault local foi encontrado neste dispositivo.\n"
                    "Deseja baixar o vault do Google Drive?"
                )
                reply = QMessageBox.question(
                    self,
                    "Vault Encontrado",
                    message,
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                if reply == QMessageBox.Yes:
                    self._download_vault_from_drive(vault_path)
                return
            
            # Both exist - offer smart sync
            cloud_file = files[0]
            cloud_size = int(cloud_file.get("size", 0))
            
            message = (
                "Vault encontrado no Google Drive!\n\n"
                f"• Vault local: {self._format_size(local_vault_size)}\n"
                f"• Vault na nuvem: {self._format_size(cloud_size)}\n\n"
                "Deseja fazer Smart Sync para mesclar as credenciais?\n"
                "(Isso manterá todas as credenciais de ambos os vaults)"
            )
            
            reply = QMessageBox.question(
                self,
                "Smart Sync",
                message,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self._smart_sync_vaults(vault_path)
                    
        except Exception as e:
            print(f"Error checking cloud vault: {e}")
            # Don't show error to user, just log it
    
    def _format_size(self, size_bytes: int) -> str:
        """Format bytes to human readable string."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
    
    def _download_vault_from_drive(self, vault_path: Path):
        """Download vault from Google Drive."""
        progress = QProgressDialog(
            "Baixando vault do Google Drive...",
            None,  # No cancel button
            0, 100,
            self
        )
        progress.setWindowTitle("Sincronizando")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(10)
        progress.show()
        QApplication.processEvents()
        
        try:
            progress.setValue(30)
            QApplication.processEvents()
            
            self.gdrive.download_vault(vault_path)
            
            progress.setValue(100)
            QApplication.processEvents()
            
            QMessageBox.information(
                self,
                "Download Concluído",
                "O vault foi baixado com sucesso do Google Drive!\n\n"
                "Reinicie o aplicativo para carregar as credenciais."
            )
            
        except Exception as e:
            progress.close()
            QMessageBox.critical(
                self,
                "Erro ao Baixar",
                f"Não foi possível baixar o vault:\n\n{str(e)}"
            )

    def _upload_vault_to_drive(self, vault_path: Path):
        """Upload vault to Google Drive."""
        progress = QProgressDialog(
            "Enviando vault para o Google Drive...",
            None,
            0, 100,
            self
        )
        progress.setWindowTitle("Sincronizando")
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
                "Upload Concluído",
                "O vault foi enviado com sucesso para o Google Drive!"
            )
            
        except Exception as e:
            progress.close()
            QMessageBox.critical(
                self,
                "Erro ao Enviar",
                f"Não foi possível enviar o vault:\n\n{str(e)}"
            )

    def _smart_sync_vaults(self, vault_path: Path):
        """Perform smart sync between local and cloud vaults."""
        progress = QProgressDialog(
            "Iniciando Smart Sync...",
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
            stats = self.gdrive.merge_vaults(
                vault_path=vault_path,
                progress_callback=on_progress
            )
            
            progress.setValue(100)
            QApplication.processEvents()
            
            # Build result message
            message = (
                f"Smart Sync concluído!\n\n"
                f"📊 Resultados:\n"
                f"• Apenas local: {stats.get('local_only', 0)} credenciais\n"
                f"• Apenas nuvem: {stats.get('cloud_only', 0)} credenciais\n"
                f"• Atualizadas da nuvem: {stats.get('updated_from_cloud', 0)}\n"
                f"• Atualizadas do local: {stats.get('updated_from_local', 0)}\n"
                f"• Total: {stats.get('total_after_merge', 0)} credenciais\n\n"
                f"Reinicie o aplicativo para ver as alterações."
            )
            
            QMessageBox.information(
                self,
                "Sync Concluído",
                message
            )
            
        except Exception as e:
            progress.close()
            QMessageBox.critical(
                self,
                "Erro no Sync",
                f"Não foi possível sincronizar:\n\n{str(e)}"
            )

    def _on_auth_error(self, error: str):

        QTimer.singleShot(0, lambda: self._handle_auth_error(error))

    def _handle_auth_error(self, error: str):

        if hasattr(self, '_poll_timer'):

            self._poll_timer.stop()

        self.signin_btn.setEnabled(True)

        self._setup_google_button(connected=False)

        QMessageBox.critical(

            self,

            "Connection Failed",

            f"Failed to connect to Google Drive:\n\n{error}"

        )

    def showEvent(self, event):

        super().showEvent(event)

        self._center_on_parent()

    def _center_on_parent(self):

        if self.parent():

            parent_rect = self.parent().geometry()

            parent_center = self.parent().mapToGlobal(

                QPoint(parent_rect.width() // 2, parent_rect.height() // 2)

            )

            self.move(

                parent_center.x() - self.width() // 2,

                parent_center.y() - self.height() // 2

            )

        else:

            screen = QApplication.primaryScreen().geometry()

            self.move(

                (screen.width() - self.width()) // 2,

                (screen.height() - self.height()) // 2

            )
