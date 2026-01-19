from typing import Optional, List

from PySide6.QtWidgets import (

    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,

    QFrame, QScrollArea, QApplication, QMenu, QPlainTextEdit, QTextBrowser

)

from app.ui.components.elided_label import ElidedLabel


from PySide6.QtCore import Qt, Signal, QTimer

from PySide6.QtGui import QIcon, QClipboard

from ..core.vault import SecureNote, CreditCard

from .theme import get_theme

from .ui_utils import load_svg_icon, format_timestamp

class CopyableField(QFrame):

    copied = Signal(str)

    def __init__(self, label: str, value: str, is_sensitive: bool = False, parent=None):

        super().__init__(parent)

        self.label_text = label

        self.value_text = value

        self.is_sensitive = is_sensitive

        self.is_visible = not is_sensitive

        self.setup_ui()

    def setup_ui(self):

        theme = get_theme()

        self.setStyleSheet(f"""
            CopyableField {{

                background-color: {theme.colors.card};
                border: none;
                border-radius: 0px;
            }}
        """)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(24, 16, 24, 16)

        layout.setSpacing(8)

        label = QLabel(self.label_text)

        label.setStyleSheet(f"""
            color: {theme.colors.primary};
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
        """)

        layout.addWidget(label)

        value_row = QHBoxLayout()

        value_row.setSpacing(12)

        if self.is_sensitive:

            display_text = "•" * min(len(self.value_text), 12)

        else:

            display_text = self.value_text

        self.value_label = QLabel(display_text)

        self.value_label.setStyleSheet(f"""
            color: {theme.colors.foreground};
            font-size: 15px;
            font-weight: 400;
        """)

        self.value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        value_row.addWidget(self.value_label, 1)

        if self.is_sensitive:

            self.toggle_btn = QPushButton()

            self.toggle_btn.setFixedSize(28, 28)

            self.toggle_btn.setCursor(Qt.PointingHandCursor)

            self.toggle_btn.setIcon(QIcon(load_svg_icon("view", 16, theme.colors.muted_foreground)))

            self.toggle_btn.setStyleSheet(f"""
                QPushButton {{

                    background: transparent;
                    border: none;
                    border-radius: 4px;
                }}
                QPushButton:hover {{

                    background: {theme.colors.accent};
                }}
            """)

            self.toggle_btn.clicked.connect(self._toggle_visibility)

            value_row.addWidget(self.toggle_btn)

        copy_btn = QPushButton()

        copy_btn.setFixedSize(28, 28)

        copy_btn.setCursor(Qt.PointingHandCursor)

        copy_btn.setIcon(QIcon(load_svg_icon("copy", 16, theme.colors.muted_foreground)))

        copy_btn.setStyleSheet(f"""
            QPushButton {{

                background: transparent;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{

                background: {theme.colors.accent};
            }}
        """)

        copy_btn.clicked.connect(self._copy_value)

        value_row.addWidget(copy_btn)

        layout.addLayout(value_row)

    def _toggle_visibility(self):

        self.is_visible = not self.is_visible

        theme = get_theme()

        if self.is_visible:

            self.value_label.setText(self.value_text)

            self.toggle_btn.setIcon(QIcon(load_svg_icon("visibility_off", 16, theme.colors.muted_foreground)))

        else:

            self.value_label.setText("•" * min(len(self.value_text), 12))

            self.toggle_btn.setIcon(QIcon(load_svg_icon("view", 16, theme.colors.muted_foreground)))

    def _copy_value(self):

        clipboard = QApplication.clipboard()

        clipboard.setText(self.value_text)

        self.copied.emit(self.value_text)

class CreditCardPreview(QFrame):

    def __init__(self, card: CreditCard, parent=None):

        super().__init__(parent)

        self.card = card

        self.setup_ui()

    def setup_ui(self):

        theme = get_theme()

        self.setStyleSheet(f"background-color: {theme.colors.card}; border: none;")

        container_layout = QVBoxLayout(self)

        container_layout.setContentsMargins(24, 16, 24, 16)

        container_layout.setAlignment(Qt.AlignCenter)

        card_frame = QFrame()

        card_frame.setFixedSize(300, 180)

        card_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1e4976, stop:1 #0c2a4a);
                border-radius: 14px;
                border: 1px solid rgba(255,255,255,0.15);
            }
        """)

        card_layout = QVBoxLayout(card_frame)

        card_layout.setContentsMargins(20, 16, 20, 16)

        card_layout.setSpacing(0)

        top_row = QHBoxLayout()

        chip = QFrame()

        chip.setFixedSize(45, 32)

        chip.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #d4af37, stop:1 #aa8c2c);
                border-radius: 4px;
                border: none;
            }
        """)

        top_row.addWidget(chip)

        top_row.addStretch()

        brand = QFrame()

        brand.setFixedSize(50, 35)

        brand.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #22c55e, stop:1 #16a34a);
                border-radius: 4px;
                border: none;
            }
        """)

        top_row.addWidget(brand)

        card_layout.addLayout(top_row)

        card_layout.addStretch()

        last4 = self.card.card_number[-4:] if len(self.card.card_number) >= 4 else "****"

        number_label = QLabel(f"•••• •••• ••••  {last4}")

        number_label.setStyleSheet("""
            color: white;
            font-size: 18px;
            font-weight: 500;
            letter-spacing: 2px;
            font-family: 'Consolas', 'Monaco', monospace;
            background: transparent;
            border: none;
        """)

        card_layout.addWidget(number_label)

        card_layout.addStretch()

        bottom_row = QHBoxLayout()

        name_label = ElidedLabel(self.card.cardholder_name.upper())

        name_label.setStyleSheet("""
            color: white;
            font-size: 12px;
            font-weight: 500;
            letter-spacing: 1px;
            background: transparent;
            border: none;
        """)

        bottom_row.addWidget(name_label, 1)

        expiry_col = QVBoxLayout()

        expiry_col.setSpacing(2)

        expiry_title = QLabel("EXPIRES")

        expiry_title.setStyleSheet("""
            color: rgba(255,255,255,0.5);
            font-size: 8px;
            letter-spacing: 0.5px;
            background: transparent;
            border: none;
        """)

        expiry_col.addWidget(expiry_title)

        expiry_value = QLabel(self.card.expiry_date)

        expiry_value.setStyleSheet("""
            color: white;
            font-size: 12px;
            font-weight: 500;
            background: transparent;
            border: none;
        """)

        expiry_col.addWidget(expiry_value)

        bottom_row.addLayout(expiry_col)

        card_layout.addLayout(bottom_row)

        container_layout.addWidget(card_frame, alignment=Qt.AlignCenter)

class SecureNoteDetailPanel(QWidget):

    edit_requested = Signal(object)

    delete_requested = Signal(object)

    favorite_toggled = Signal(object)

    # Threshold for using async loading (in characters)
    LARGE_CONTENT_THRESHOLD = 5000

    def __init__(self, note: SecureNote, parent=None):

        super().__init__(parent)

        self.note = note

        self._content_loaded = False

        self.setup_ui()

    def setup_ui(self):

        theme = get_theme()

        self.setStyleSheet(f"background-color: {theme.colors.background};")

        layout = QVBoxLayout(self)

        layout.setContentsMargins(0, 0, 0, 0)

        layout.setSpacing(0)

        scroll = QScrollArea()

        scroll.setWidgetResizable(True)

        scroll.setFrameShape(QFrame.NoFrame)

        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll.setStyleSheet(f"background-color: {theme.colors.background};")

        content = QWidget()

        content.setStyleSheet(f"background-color: {theme.colors.background};")

        self.content_layout = QVBoxLayout(content)

        self.content_layout.setContentsMargins(0, 0, 0, 0)

        self.content_layout.setSpacing(1)

        header = self._create_header(theme)

        self.content_layout.addWidget(header)

        # Content frame
        self.content_frame = QFrame()

        self.content_frame.setStyleSheet(f"background-color: {theme.colors.card}; border: none;")

        self.cf_layout = QVBoxLayout(self.content_frame)

        self.cf_layout.setContentsMargins(24, 20, 24, 20)

        self.cf_layout.setSpacing(12)

        content_label = QLabel("CONTENT")

        content_label.setStyleSheet(f"""
            color: {theme.colors.primary};
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
        """)

        self.cf_layout.addWidget(content_label)

        # Check if content is large
        is_large_content = len(self.note.content) > self.LARGE_CONTENT_THRESHOLD

        if is_large_content:
            # Show loading placeholder first
            self.loading_label = QLabel("Loading content...")
            self.loading_label.setStyleSheet(f"""
                color: {theme.colors.muted_foreground};
                font-size: 14px;
                padding: 12px;
                background-color: {theme.colors.input};
                border-radius: 8px;
            """)
            self.cf_layout.addWidget(self.loading_label)

            # Schedule async content loading
            QTimer.singleShot(50, self._load_content_async)
        else:
            # Load content immediately for small notes
            self._create_note_text_widget(theme)

        self.content_layout.addWidget(self.content_frame, 1)  # stretch factor to expand

        # Meta frame
        meta_frame = QFrame()

        meta_frame.setStyleSheet(f"background-color: {theme.colors.card}; border: none;")

        meta_layout = QVBoxLayout(meta_frame)

        meta_layout.setContentsMargins(24, 16, 24, 16)

        meta_layout.setSpacing(4)

        if self.note.updated_at:

            modified = QLabel(f"MODIFIED: {format_timestamp(self.note.updated_at)}")

            modified.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 10px; letter-spacing: 0.5px;")

            modified.setAlignment(Qt.AlignRight)

            meta_layout.addWidget(modified)

        if self.note.created_at:

            created = QLabel(f"CREATED: {format_timestamp(self.note.created_at)}")

            created.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 10px; letter-spacing: 0.5px;")

            created.setAlignment(Qt.AlignRight)

            meta_layout.addWidget(created)

        self.content_layout.addWidget(meta_frame)

        scroll.setWidget(content)

        layout.addWidget(scroll)

    def _load_content_async(self):
        """Load content asynchronously for large notes."""
        if self._content_loaded:
            return

        theme = get_theme()

        # Remove loading label
        if hasattr(self, 'loading_label'):
            self.loading_label.deleteLater()

        # Create the actual content widget
        self._create_note_text_widget(theme)
        self._content_loaded = True

    def _create_note_text_widget(self, theme):
        """Create the note text widget - handles both plain text and HTML content."""
        from PySide6.QtWidgets import QSizePolicy

        content = self.note.content
        is_html = content.strip().startswith('<!DOCTYPE') or content.strip().startswith('<html')
        is_large_content = len(content) > self.LARGE_CONTENT_THRESHOLD

        if is_html:
            # Use QTextBrowser for HTML content - renders HTML properly
            note_text = QTextBrowser()
            note_text.setHtml(content)
            note_text.setReadOnly(True)
            note_text.setOpenExternalLinks(True)
            note_text.setStyleSheet(f"""
                QTextBrowser {{
                    color: {theme.colors.foreground};
                    font-size: 14px;
                    padding: 12px;
                    background-color: {theme.colors.input};
                    border-radius: 8px;
                    border: none;
                }}
                QTextBrowser:focus {{
                    border: none;
                    outline: none;
                }}
            """)
            note_text.setMinimumHeight(200)
            # Allow it to expand to fill available space
            note_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        elif is_large_content:
            # Use QPlainTextEdit for large plain text content - better performance
            note_text = QPlainTextEdit()
            note_text.setPlainText(content)
            note_text.setReadOnly(True)
            note_text.setStyleSheet(f"""
                QPlainTextEdit {{
                    color: {theme.colors.foreground};
                    font-size: 14px;
                    padding: 12px;
                    background-color: {theme.colors.input};
                    border-radius: 8px;
                    border: none;
                }}
                QPlainTextEdit:focus {{
                    border: none;
                    outline: none;
                }}
            """)
            note_text.setMinimumHeight(200)
            # Allow it to expand to fill available space
            note_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        else:
            # Use QTextBrowser for small content too - better for expansion
            note_text = QTextBrowser()
            note_text.setPlainText(content)
            note_text.setReadOnly(True)
            note_text.setStyleSheet(f"""
                QTextBrowser {{
                    color: {theme.colors.foreground};
                    font-size: 14px;
                    padding: 12px;
                    background-color: {theme.colors.input};
                    border-radius: 8px;
                    border: none;
                }}
            """)
            note_text.setMinimumHeight(150)
            note_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.cf_layout.addWidget(note_text, 1)  # stretch factor of 1

    def _create_header(self, theme) -> QFrame:

        header = QFrame()

        header.setStyleSheet(f"background-color: {theme.colors.card}; border: none;")

        header_layout = QHBoxLayout(header)

        header_layout.setContentsMargins(24, 20, 16, 20)

        header_layout.setSpacing(16)

        icon_container = QLabel()

        icon_container.setFixedSize(56, 56)

        icon_container.setAlignment(Qt.AlignCenter)

        icon_container.setStyleSheet("""
            background-color: #22C55E;
            border-radius: 12px;
        """)

        icon_container.setPixmap(load_svg_icon("note", 28, "#ffffff"))

        header_layout.addWidget(icon_container)

        title_layout = QVBoxLayout()

        title_layout.setSpacing(4)

        title = QLabel(self.note.title)

        title.setStyleSheet(f"""
            color: {theme.colors.foreground};
            font-size: 22px;
            font-weight: 600;
        """)

        title_layout.addWidget(title)

        subtitle = QLabel("Secure Note")

        subtitle.setStyleSheet(f"""
            color: {theme.colors.muted_foreground};
            font-size: 12px;
        """)

        title_layout.addWidget(subtitle)

        header_layout.addLayout(title_layout, 1)

        edit_btn = QPushButton("Edit")

        edit_btn.setFixedSize(70, 32)

        edit_btn.setCursor(Qt.PointingHandCursor)

        edit_btn.setStyleSheet(f"""
            QPushButton {{

                background-color: {theme.colors.card};
                color: {theme.colors.foreground};
                border: 1px solid {theme.colors.border};
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{

                background-color: {theme.colors.accent};
            }}
        """)

        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.note))

        header_layout.addWidget(edit_btn)

        menu_btn = QPushButton()

        menu_btn.setFixedSize(32, 32)

        menu_btn.setCursor(Qt.PointingHandCursor)

        menu_btn.setIcon(QIcon(load_svg_icon("more_vert", 20, theme.colors.muted_foreground)))

        menu_btn.setStyleSheet(f"""
            QPushButton {{

                background-color: transparent;
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{

                background-color: {theme.colors.accent};
            }}
        """)

        menu_btn.clicked.connect(lambda: self._show_menu(menu_btn))

        header_layout.addWidget(menu_btn)

        return header

    def _show_menu(self, button):

        theme = get_theme()

        menu = QMenu(self)

        menu.setStyleSheet(f"""
            QMenu {{

                background-color: {theme.colors.card};
                border: 1px solid {theme.colors.border};
                border-radius: 8px;
                padding: 4px;
            }}
            QMenu::item {{

                padding: 8px;
                font-size: 13px;
                font-weight: 500;
            }}
            QMenu::item:selected {{

                background-color: {theme.colors.accent};
            }}
        """)

        fav_text = "Remove from Favorites" if self.note.is_favorite else "Add to Favorites"

        fav_action = menu.addAction(fav_text)

        fav_action.setIcon(

            QIcon(load_svg_icon("star", 16, theme.colors.muted_foreground))

        )

        menu.addSeparator()

        delete_action = menu.addAction("Delete")

        delete_action.setIcon(QIcon(load_svg_icon("delete", 16, theme.colors.destructive)))

        action = menu.exec_(button.mapToGlobal(button.rect().bottomLeft()))

        if action == fav_action:

            self.favorite_toggled.emit(self.note)

        elif action == delete_action:

            self.delete_requested.emit(self.note)

class CreditCardDetailPanel(QWidget):

    edit_requested = Signal(object)

    delete_requested = Signal(object)

    favorite_toggled = Signal(object)

    def __init__(self, card: CreditCard, parent=None):

        super().__init__(parent)

        self.card = card

        self.setup_ui()

    def setup_ui(self):

        theme = get_theme()

        self.setStyleSheet(f"background-color: {theme.colors.background};")

        layout = QVBoxLayout(self)

        layout.setContentsMargins(0, 0, 0, 0)

        layout.setSpacing(0)

        scroll = QScrollArea()

        scroll.setWidgetResizable(True)

        scroll.setFrameShape(QFrame.NoFrame)

        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll.setStyleSheet(f"background-color: {theme.colors.background};")

        content = QWidget()

        content.setStyleSheet(f"background-color: {theme.colors.background};")

        content_layout = QVBoxLayout(content)

        content_layout.setContentsMargins(0, 0, 0, 0)

        content_layout.setSpacing(1)

        header = self._create_header(theme)

        content_layout.addWidget(header)

        card_preview = CreditCardPreview(self.card)

        content_layout.addWidget(card_preview)

        separator = QFrame()

        separator.setFixedHeight(1)

        separator.setStyleSheet(f"background-color: {theme.colors.border};")

        content_layout.addWidget(separator)

        name_field = CopyableField("CARDHOLDER NAME", self.card.cardholder_name)

        content_layout.addWidget(name_field)

        masked_number = f"•••• •••• ••••  {self.card.card_number[-4:]}" if len(self.card.card_number) >= 4 else self.card.card_number

        number_field = CopyableField("CARD NUMBER", masked_number, is_sensitive=True)

        number_field.value_text = self.card.card_number

        content_layout.addWidget(number_field)

        exp_cvv_frame = QFrame()

        exp_cvv_frame.setStyleSheet(f"background-color: {theme.colors.card}; border: none;")

        exp_cvv_layout = QHBoxLayout(exp_cvv_frame)

        exp_cvv_layout.setContentsMargins(0, 0, 0, 0)

        exp_cvv_layout.setSpacing(0)

        expiry_field = CopyableField("EXPIRY", self.card.expiry_date)

        exp_cvv_layout.addWidget(expiry_field)

        cvv_field = CopyableField("CVV", "•••", is_sensitive=True)

        cvv_field.value_text = self.card.cvv

        exp_cvv_layout.addWidget(cvv_field)

        content_layout.addWidget(exp_cvv_frame)

        if self.card.notes:

            notes_frame = QFrame()

            notes_frame.setStyleSheet(f"background-color: {theme.colors.card}; border: none;")

            notes_layout = QVBoxLayout(notes_frame)

            notes_layout.setContentsMargins(24, 16, 24, 16)

            notes_layout.setSpacing(8)

            notes_label = QLabel("NOTES")

            notes_label.setStyleSheet(f"""
                color: {theme.colors.primary};
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 0.5px;
            """)

            notes_layout.addWidget(notes_label)

            notes_text = QLabel(self.card.notes)

            notes_text.setWordWrap(True)

            notes_text.setStyleSheet(f"""
                color: {theme.colors.foreground};
                font-size: 14px;
            """)

            notes_layout.addWidget(notes_text)

            content_layout.addWidget(notes_frame)

        meta_frame = QFrame()

        meta_frame.setStyleSheet(f"background-color: {theme.colors.card}; border: none;")

        meta_layout = QVBoxLayout(meta_frame)

        meta_layout.setContentsMargins(24, 16, 24, 16)

        meta_layout.setSpacing(4)

        if self.card.updated_at:

            modified = QLabel(f"MODIFIED: {format_timestamp(self.card.updated_at)}")

            modified.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 10px; letter-spacing: 0.5px;")

            modified.setAlignment(Qt.AlignRight)

            meta_layout.addWidget(modified)

        if self.card.created_at:

            created = QLabel(f"CREATED: {format_timestamp(self.card.created_at)}")

            created.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 10px; letter-spacing: 0.5px;")

            created.setAlignment(Qt.AlignRight)

            meta_layout.addWidget(created)

        content_layout.addWidget(meta_frame)

        content_layout.addStretch()

        scroll.setWidget(content)

        layout.addWidget(scroll)

    def _create_header(self, theme) -> QFrame:

        header = QFrame()

        header.setStyleSheet(f"background-color: {theme.colors.card}; border: none;")

        header_layout = QHBoxLayout(header)

        header_layout.setContentsMargins(24, 20, 16, 20)

        header_layout.setSpacing(16)

        icon_container = QLabel()

        icon_container.setFixedSize(56, 56)

        icon_container.setAlignment(Qt.AlignCenter)

        icon_container.setStyleSheet("""
            background-color: #F59E0B;
            border-radius: 12px;
        """)

        icon_container.setPixmap(load_svg_icon("credit_card", 28, "#ffffff"))

        header_layout.addWidget(icon_container)

        title_layout = QVBoxLayout()

        title_layout.setSpacing(4)

        title = QLabel(self.card.title)

        title.setStyleSheet(f"""
            color: {theme.colors.foreground};
            font-size: 22px;
            font-weight: 600;
        """)

        title_layout.addWidget(title)

        subtitle = QLabel("Credit Card")

        subtitle.setStyleSheet(f"""
            color: {theme.colors.muted_foreground};
            font-size: 12px;
        """)

        title_layout.addWidget(subtitle)

        header_layout.addLayout(title_layout, 1)

        edit_btn = QPushButton("Edit")

        edit_btn.setFixedSize(70, 32)

        edit_btn.setCursor(Qt.PointingHandCursor)

        edit_btn.setStyleSheet(f"""
            QPushButton {{

                background-color: {theme.colors.card};
                color: {theme.colors.foreground};
                border: 1px solid {theme.colors.border};
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{

                background-color: {theme.colors.accent};
            }}
        """)

        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.card))

        header_layout.addWidget(edit_btn)

        menu_btn = QPushButton()

        menu_btn.setFixedSize(32, 32)

        menu_btn.setCursor(Qt.PointingHandCursor)

        menu_btn.setIcon(QIcon(load_svg_icon("more_vert", 20, theme.colors.muted_foreground)))

        menu_btn.setStyleSheet(f"""
            QPushButton {{

                background-color: transparent;
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{

                background-color: {theme.colors.accent};
            }}
        """)

        menu_btn.clicked.connect(lambda: self._show_menu(menu_btn))

        header_layout.addWidget(menu_btn)

        return header

    def _show_menu(self, button):

        theme = get_theme()

        menu = QMenu(self)

        menu.setStyleSheet(f"""
            QMenu {{

                background-color: {theme.colors.card};
                border: 1px solid {theme.colors.border};
                border-radius: 8px;
                padding: 4px;
            }}
            QMenu::item {{

                padding: 8px 16px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{

                background-color: {theme.colors.accent};
            }}
        """)

        fav_text = "Remove from Favorites" if self.card.is_favorite else "Add to Favorites"

        fav_action = menu.addAction(fav_text)

        menu.addSeparator()

        delete_action = menu.addAction("Delete")

        delete_action.setIcon(QIcon(load_svg_icon("delete", 16, theme.colors.destructive)))

        action = menu.exec_(button.mapToGlobal(button.rect().bottomLeft()))

        if action == fav_action:

            self.favorite_toggled.emit(self.card)

        elif action == delete_action:

            self.delete_requested.emit(self.card)
