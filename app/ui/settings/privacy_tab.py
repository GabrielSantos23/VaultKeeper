
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

from ..theme import get_theme

class PrivacyTab(QWidget):

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

        page_title = QLabel("Privacy Settings")

        page_title.setStyleSheet(f"""
            color: {theme.colors.foreground};
            font-size: 18px;
            font-weight: 600;
        """)

        header_layout.addWidget(page_title)

        page_subtitle = QLabel("Control how your data is used and shared.")

        page_subtitle.setStyleSheet(f"""
            color: {theme.colors.muted_foreground};
            font-size: 14px;
        """)

        header_layout.addWidget(page_subtitle)

        layout.addWidget(header)

        placeholder = QLabel("Privacy settings coming soon...")

        placeholder.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 14px;")

        layout.addWidget(placeholder)

        layout.addStretch()
