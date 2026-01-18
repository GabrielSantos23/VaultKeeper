"""
VaultKeeper - Security Settings Tab
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QMessageBox, QApplication
)
from PySide6.QtCore import Qt
from pathlib import Path

from ..theme import get_theme


class SecurityTab(QWidget):
    """Security settings tab with danger zone."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
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
        
        page_title = QLabel("Security Settings")
        page_title.setStyleSheet(f"""
            color: {theme.colors.foreground};
            font-size: 18px;
            font-weight: 600;
        """)
        header_layout.addWidget(page_title)
        
        page_subtitle = QLabel("Manage security options and sensitive operations.")
        page_subtitle.setStyleSheet(f"""
            color: {theme.colors.muted_foreground};
            font-size: 14px;
        """)
        header_layout.addWidget(page_subtitle)
        
        layout.addWidget(header)
        
        # Danger Zone
        self._setup_danger_zone(layout)
        
        layout.addStretch()
    
    def _setup_danger_zone(self, layout):
        """Setup the danger zone section with reset button."""
        theme = get_theme()
        
        layout.addSpacing(32)
        
        # Danger Zone Header
        danger_header = QLabel("Danger Zone")
        danger_header.setStyleSheet(f"""
            color: #ef4444;
            font-size: 16px;
            font-weight: 600;
        """)
        layout.addWidget(danger_header)
        
        danger_desc = QLabel("Irreversible actions. Please proceed with caution.")
        danger_desc.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 12px;")
        layout.addWidget(danger_desc)
        
        layout.addSpacing(16)
        
        # Danger Zone Container
        danger_container = QFrame()
        danger_container.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(239, 68, 68, 0.1);
                border: 1px solid rgba(239, 68, 68, 0.3);
                border-radius: 12px;
                padding: 16px;
            }}
        """)
        danger_layout = QVBoxLayout(danger_container)
        danger_layout.setSpacing(16)
        
        # Reset Application Row
        reset_row = QHBoxLayout()
        
        reset_text_layout = QVBoxLayout()
        reset_text_layout.setSpacing(4)
        
        reset_title = QLabel("Reset Application")
        reset_title.setStyleSheet(f"color: {theme.colors.foreground}; font-size: 14px; font-weight: 500;")
        reset_text_layout.addWidget(reset_title)
        
        reset_subtitle = QLabel("Delete all credentials, remove native host, and reset to initial state.")
        reset_subtitle.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 12px;")
        reset_text_layout.addWidget(reset_subtitle)
        
        reset_row.addLayout(reset_text_layout)
        
        # Reset Button
        reset_btn = QPushButton("Reset Everything")
        reset_btn.setCursor(Qt.PointingHandCursor)
        reset_btn.setFixedWidth(140)
        reset_btn.setFixedHeight(36)
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc2626;
                border: none;
                color: white;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #b91c1c;
            }
            QPushButton:pressed {
                background-color: #991b1b;
            }
        """)
        reset_btn.clicked.connect(self._confirm_reset)
        reset_row.addWidget(reset_btn)
        
        danger_layout.addLayout(reset_row)
        layout.addWidget(danger_container)
    
    def _confirm_reset(self):
        """Show confirmation dialog before reset."""
        reply = QMessageBox.warning(
            self,
            "⚠️ Confirm Reset",
            "Are you sure you want to reset the application?\n\n"
            "This will:\n"
            "• Delete ALL saved credentials\n"
            "• Remove the native messaging host\n"
            "• Clear all application data\n\n"
            "This action CANNOT be undone!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            second_reply = QMessageBox.critical(
                self,
                "Final Confirmation",
                "This is your LAST chance!\n\n"
                "All your passwords will be permanently deleted.\n\n"
                "Are you absolutely sure?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if second_reply == QMessageBox.Yes:
                self._perform_reset()
    
    def _perform_reset(self):
        """Perform the complete application reset."""
        try:
            vaultkeeper_dir = Path.home() / '.vaultkeeper'
            vaultkeeper_dir.mkdir(parents=True, exist_ok=True)
            
            reset_marker = vaultkeeper_dir / '.reset_pending'
            reset_marker.write_text('RESET_REQUESTED')
            
            QMessageBox.information(
                self,
                "Reset Scheduled",
                "The reset has been scheduled.\n\n"
                "The application will now close.\n"
                "When you restart, all data will be deleted\n"
                "and you'll set up a new vault."
            )
            
            QApplication.quit()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Reset Failed",
                f"An error occurred:\n\n{str(e)}"
            )
