
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel

from PySide6.QtCore import Qt, Signal

from app.core.vault import Credential, SecureNote, CreditCard

from app.ui.theme import get_theme

from app.ui.ui_utils import load_svg_icon

from app.ui.components.favicon import FaviconLabel

class CredentialCard(QFrame):

    clicked = Signal(object)

    def __init__(self, credential: Credential, parent=None):

        super().__init__(parent)

        self.credential = credential

        self._selected = False

        self.setup_ui()

        self.setCursor(Qt.PointingHandCursor)

    def setup_ui(self):

        theme = get_theme()

        self.setFixedHeight(64)

        layout = QHBoxLayout(self)

        layout.setContentsMargins(8, 8, 8, 8)

        layout.setSpacing(12)

        self.favicon = FaviconLabel(self.credential.domain, size=40)

        layout.addWidget(self.favicon)

        text_layout = QVBoxLayout()

        text_layout.setSpacing(2)

        text_layout.setContentsMargins(0, 0, 0, 0)

        self.title = QLabel(self.credential.domain)

        self.title.setStyleSheet(f"""
            color: {theme.colors.foreground};
            font-weight: 500;
            font-size: 14px;
        """)

        text_layout.addWidget(self.title)

        self.subtitle = QLabel(self.credential.username)

        self.subtitle.setStyleSheet(f"""
            color: {theme.colors.muted_foreground};
            font-size: 12px;
        """)

        text_layout.addWidget(self.subtitle)

        layout.addLayout(text_layout)

        layout.addStretch()

        self._update_style()

    def _update_style(self):

        theme = get_theme()

        if self._selected:

            self.setStyleSheet(f"""
                CredentialCard {{

                    background-color: {theme.colors.primary};
                    border-radius: 8px;
                    border: none;
                }}
            """)

            self.title.setStyleSheet(f"""
                color: {theme.colors.primary_foreground};
                font-weight: 500;
                font-size: 14px;
                background-color: transparent;
            """)

            self.subtitle.setStyleSheet(f"""
                color: rgba(255, 255, 255, 0.8);
                font-size: 12px;
                background-color: transparent;
            """)

        else:

            self.setStyleSheet(f"""
                CredentialCard {{

                    background-color: transparent;
                    border-radius: 8px;
                    border: none;
                }}
                CredentialCard:hover {{

                    background-color: {theme.colors.accent};
                }}
            """)

            self.title.setStyleSheet(f"""
                color: {theme.colors.foreground};
                font-weight: 500;
                font-size: 14px;
                background-color: transparent;
            """)

            self.subtitle.setStyleSheet(f"""
                color: {theme.colors.muted_foreground};
                font-size: 12px;
                background-color: transparent;
            """)

    def mousePressEvent(self, event):

        self.clicked.emit(self.credential)

        super().mousePressEvent(event)

    def set_selected(self, selected: bool):

        self._selected = selected

        self._update_style()

class SecureNoteCard(QFrame):

    clicked = Signal(object)

    def __init__(self, note: SecureNote, parent=None):

        super().__init__(parent)

        self.note = note

        self.item_type = "secure_note"

        self._selected = False

        self.setup_ui()

        self.setCursor(Qt.PointingHandCursor)

    def setup_ui(self):

        theme = get_theme()

        self.setFixedHeight(64)

        layout = QHBoxLayout(self)

        layout.setContentsMargins(8, 8, 8, 8)

        layout.setSpacing(12)

        icon_container = QLabel()

        icon_container.setFixedSize(40, 40)

        icon_container.setAlignment(Qt.AlignCenter)

        icon_container.setStyleSheet("""
            background-color: #22C55E;
            border-radius: 8px;
        """)

        icon_container.setPixmap(load_svg_icon("note", 20, "#ffffff"))

        layout.addWidget(icon_container)

        text_layout = QVBoxLayout()

        text_layout.setSpacing(2)

        text_layout.setContentsMargins(0, 0, 0, 0)

        self.title = QLabel(self.note.title)

        self.title.setStyleSheet(f"""
            color: {theme.colors.foreground};
            font-weight: 500;
            font-size: 14px;
        """)

        text_layout.addWidget(self.title)

        preview = self.note.content[:50] + "..." if len(self.note.content) > 50 else self.note.content

        preview = preview.split('\n')[0]

        self.subtitle = QLabel(preview)

        self.subtitle.setStyleSheet(f"""
            color: {theme.colors.muted_foreground};
            font-size: 12px;
        """)

        text_layout.addWidget(self.subtitle)

        layout.addLayout(text_layout)

        layout.addStretch()

        self._update_style()

    def _update_style(self):

        theme = get_theme()

        if self._selected:

            self.setStyleSheet(f"""
                SecureNoteCard {{

                    background-color: {theme.colors.primary};
                    border-radius: 8px;
                    border: none;
                }}
            """)

            self.title.setStyleSheet(f"""
                color: {theme.colors.primary_foreground};
                font-weight: 500;
                font-size: 14px;
                background-color: transparent;
            """)

            self.subtitle.setStyleSheet(f"""
                color: rgba(255, 255, 255, 0.8);
                font-size: 12px;
                background-color: transparent;
            """)

        else:

            self.setStyleSheet(f"""
                SecureNoteCard {{

                    background-color: transparent;
                    border-radius: 8px;
                    border: none;
                }}
                SecureNoteCard:hover {{

                    background-color: {theme.colors.accent};
                }}
            """)

            self.title.setStyleSheet(f"""
                color: {theme.colors.foreground};
                font-weight: 500;
                font-size: 14px;
                background-color: transparent;
            """)

            self.subtitle.setStyleSheet(f"""
                color: {theme.colors.muted_foreground};
                font-size: 12px;
                background-color: transparent;
            """)

    def mousePressEvent(self, event):

        self.clicked.emit(self.note)

        super().mousePressEvent(event)

    def set_selected(self, selected: bool):

        self._selected = selected

        self._update_style()

class CreditCardCard(QFrame):

    clicked = Signal(object)

    def __init__(self, card: CreditCard, parent=None):

        super().__init__(parent)

        self.card = card

        self.item_type = "credit_card"

        self._selected = False

        self.setup_ui()

        self.setCursor(Qt.PointingHandCursor)

    def setup_ui(self):

        theme = get_theme()

        self.setFixedHeight(64)

        layout = QHBoxLayout(self)

        layout.setContentsMargins(8, 8, 8, 8)

        layout.setSpacing(12)

        icon_container = QLabel()

        icon_container.setFixedSize(40, 40)

        icon_container.setAlignment(Qt.AlignCenter)

        icon_container.setStyleSheet("""
            background-color: #F59E0B;
            border-radius: 8px;
        """)

        icon_container.setPixmap(load_svg_icon("credit_card", 20, "#ffffff"))

        layout.addWidget(icon_container)

        text_layout = QVBoxLayout()

        text_layout.setSpacing(2)

        text_layout.setContentsMargins(0, 0, 0, 0)

        self.title = QLabel(self.card.title)

        self.title.setStyleSheet(f"""
            color: {theme.colors.foreground};
            font-weight: 500;
            font-size: 14px;
        """)

        text_layout.addWidget(self.title)

        last_four = self.card.card_number[-4:] if len(self.card.card_number) >= 4 else "****"

        self.subtitle = QLabel(f"•••• {last_four}")

        self.subtitle.setStyleSheet(f"""
            color: {theme.colors.muted_foreground};
            font-size: 12px;
        """)

        text_layout.addWidget(self.subtitle)

        layout.addLayout(text_layout)

        layout.addStretch()

        self._update_style()

    def _update_style(self):

        theme = get_theme()

        if self._selected:

            self.setStyleSheet(f"""
                CreditCardCard {{

                    background-color: {theme.colors.primary};
                    border-radius: 8px;
                    border: none;
                }}
            """)

            self.title.setStyleSheet(f"""
                color: {theme.colors.primary_foreground};
                font-weight: 500;
                font-size: 14px;
                background-color: transparent;
            """)

            self.subtitle.setStyleSheet(f"""
                color: rgba(255, 255, 255, 0.8);
                font-size: 12px;
                background-color: transparent;
            """)

        else:

            self.setStyleSheet(f"""
                CreditCardCard {{

                    background-color: transparent;
                    border-radius: 8px;
                    border: none;
                }}
                CreditCardCard:hover {{

                    background-color: {theme.colors.accent};
                }}
            """)

            self.title.setStyleSheet(f"""
                color: {theme.colors.foreground};
                font-weight: 500;
                font-size: 14px;
                background-color: transparent;
            """)

            self.subtitle.setStyleSheet(f"""
                color: {theme.colors.muted_foreground};
                font-size: 12px;
                background-color: transparent;
            """)

    def mousePressEvent(self, event):

        self.clicked.emit(self.card)

        super().mousePressEvent(event)

    def set_selected(self, selected: bool):

        self._selected = selected

        self._update_style()
