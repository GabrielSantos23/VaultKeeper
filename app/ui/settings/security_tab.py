
from PySide6.QtWidgets import (

    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,

    QFrame, QMessageBox, QApplication

)

from PySide6.QtCore import Qt

from pathlib import Path

from ..theme import get_theme

class SecurityTab(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

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

        self._setup_danger_zone(layout)

        layout.addStretch()

    def _setup_danger_zone(self, layout):

        theme = get_theme()

        layout.addSpacing(32)

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

        danger_container = QFrame()

        danger_container.setStyleSheet(f"""
            QFrame {{

                background-color: rgba(20, 20, 25, 0.6);
                border: 1px solid rgba(239, 68, 68, 0.2);
                border-radius: 12px;
            }}
        """)

        danger_layout = QHBoxLayout(danger_container)

        danger_layout.setContentsMargins(24, 24, 24, 24)

        danger_layout.setSpacing(24)

        icon_container = QFrame()

        icon_container.setFixedSize(48, 48)

        icon_container.setStyleSheet("""
            background-color: rgba(239, 68, 68, 0.1);
            border-radius: 24px;
        """)

        icon_layout = QVBoxLayout(icon_container)

        icon_layout.setContentsMargins(0, 0, 0, 0)

        icon_layout.setAlignment(Qt.AlignCenter)

        warning_icon = QLabel("⚠️")

        warning_icon.setStyleSheet("font-size: 20px; color: #ef4444; background: transparent; border: none;")

        warning_icon.setAlignment(Qt.AlignCenter)

        icon_layout.addWidget(warning_icon)

        danger_layout.addWidget(icon_container)

        text_layout = QVBoxLayout()

        text_layout.setSpacing(4)

        reset_title = QLabel("Reset Application")

        reset_title.setStyleSheet(f"color: {theme.colors.foreground}; font-size: 16px; font-weight: 600; background: transparent; border: none;")

        text_layout.addWidget(reset_title)

        reset_subtitle = QLabel("Permanently delete all data, credentials, and reset configuration.")

        reset_subtitle.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 13px; background: transparent; border: none;")

        reset_subtitle.setWordWrap(True)

        text_layout.addWidget(reset_subtitle)

        danger_layout.addLayout(text_layout, stretch=1)

        reset_btn = QPushButton("Reset Everything")

        reset_btn.setCursor(Qt.PointingHandCursor)

        reset_btn.setFixedHeight(40)

        reset_btn.setFixedWidth(160)

        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc2626;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #b91c1c;
            }
            QPushButton:pressed {
                background-color: #991b1b;
            }
        """)

        reset_btn.clicked.connect(self._confirm_reset)

        danger_layout.addWidget(reset_btn)

        layout.addWidget(danger_container)

    def _confirm_reset(self):

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
