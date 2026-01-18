"""
VaultKeeper - Google Drive Dialog
Modern dialog for Google Drive connection matching the design reference
"""

from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QWidget, QGraphicsDropShadowEffect, QApplication,
    QMessageBox
)
from PySide6.QtCore import Qt, Signal, QSize, QTimer, QRect, QPoint
from PySide6.QtGui import QIcon, QPixmap, QColor, QFont, QPainter, QBrush

from .theme import get_theme
from .ui_utils import load_svg_icon, get_icon_path
from ..core.gdrive import get_gdrive_manager


class GoogleDriveDialog(QDialog):
    """Dialog for connecting to Google Drive with modern design."""
    
    connection_successful = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gdrive = get_gdrive_manager()
        self.setup_ui()
        self._update_state()
    
    def setup_ui(self):
        """Setup the dialog UI matching the design reference."""
        theme = get_theme()
        
        self.setWindowTitle("Connect Google Drive")
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Card container with dark background - this IS the visible dialog
        self.card = QFrame()
        self.card.setFixedSize(388, 288)
        self.card.setStyleSheet("""
            QFrame {
                background-color: #2a2f38;
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
        """)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 8)
        self.card.setGraphicsEffect(shadow)
        
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(32, 40, 32, 32)
        card_layout.setSpacing(16)
        
        # Icon container (blue rounded square with cloud icon)
        icon_container = QWidget()
        icon_container.setFixedSize(56, 56)
        icon_container.setStyleSheet("""
            background-color: #3B82F6;
            border-radius: 12px;
        """)
        
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignCenter)
        
        # Cloud sync icon
        cloud_icon = QLabel()
        cloud_icon.setPixmap(load_svg_icon("cloud_sync", 28, "#ffffff"))
        cloud_icon.setAlignment(Qt.AlignCenter)
        icon_layout.addWidget(cloud_icon)
        
        # Center the icon container
        icon_row = QHBoxLayout()
        icon_row.addStretch()
        icon_row.addWidget(icon_container)
        icon_row.addStretch()
        card_layout.addLayout(icon_row)
        
        card_layout.addSpacing(8)
        
        # Title
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
        
        # Description
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
        
        # Sign in button (styled like Google button)
        self.signin_btn = QPushButton()
        self.signin_btn.setCursor(Qt.PointingHandCursor)
        self.signin_btn.setFixedHeight(48)
        self._setup_google_button()
        self.signin_btn.clicked.connect(self._on_signin_clicked)
        card_layout.addWidget(self.signin_btn)
        
        card_layout.addSpacing(8)
        
        # Cancel button
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
        
        # Set dialog size to match card
        self.setFixedSize(self.card.size())
    
    def _setup_google_button(self, connected: bool = False):
        """Setup the Google sign-in button styling."""
        if connected:
            # Disconnect button style
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
            # Google sign-in button style (white with Google logo)
            self.signin_btn.setText("  Sign in with Google")
            
            # Load Google icon (colorful version)
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
        """Update dialog state based on connection status."""
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
        """Handle sign-in/disconnect button click."""
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
                self._update_state()
        else:
            # Connect
            if not self.gdrive.is_configured():
                QMessageBox.warning(
                    self,
                    "Not Configured",
                    "Google Drive API credentials are not configured.\n\nPlease check that GDRIVE_CLIENT_ID and GDRIVE_CLIENT_SECRET are set in your .env file."
                )
                return
            
            # Start OAuth flow
            self.signin_btn.setEnabled(False)
            self.signin_btn.setText("  Connecting...")
            
            self.gdrive.authenticate(
                on_success=self._on_auth_success,
                on_error=self._on_auth_error
            )
            
            # Start polling for connection status
            self._start_connection_polling()
    
    def _start_connection_polling(self):
        """Poll for connection status to update UI immediately."""
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._check_connection)
        self._poll_timer.start(500)  # Check every 500ms
    
    def _check_connection(self):
        """Check if connection has been established."""
        if self.gdrive.is_connected():
            self._poll_timer.stop()
            self._handle_auth_success()
    
    def _on_auth_success(self):
        """Handle successful authentication."""
        # Use QTimer to update UI from the main thread
        QTimer.singleShot(0, self._handle_auth_success)
    
    def _handle_auth_success(self):
        """Update UI after successful authentication (main thread)."""
        if hasattr(self, '_poll_timer'):
            self._poll_timer.stop()
        self.signin_btn.setEnabled(True)
        self._update_state()
        self.connection_successful.emit()
    
    def _on_auth_error(self, error: str):
        """Handle authentication error."""
        QTimer.singleShot(0, lambda: self._handle_auth_error(error))
    
    def _handle_auth_error(self, error: str):
        """Show error message (main thread)."""
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
        """Center the dialog on parent when shown."""
        super().showEvent(event)
        self._center_on_parent()
    
    def _center_on_parent(self):
        """Center the dialog on the parent window."""
        if self.parent():
            parent_rect = self.parent().geometry()
            # Get the center of the parent in screen coordinates
            parent_center = self.parent().mapToGlobal(
                QPoint(parent_rect.width() // 2, parent_rect.height() // 2)
            )
            # Position dialog so its center matches parent center
            self.move(
                parent_center.x() - self.width() // 2,
                parent_center.y() - self.height() // 2
            )
        else:
            # Center on screen
            screen = QApplication.primaryScreen().geometry()
            self.move(
                (screen.width() - self.width()) // 2,
                (screen.height() - self.height()) // 2
            )
