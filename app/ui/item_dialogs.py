
from typing import Optional

from PySide6.QtWidgets import (

    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,

    QLineEdit, QTextEdit, QFrame, QWidget, QGridLayout

)

from PySide6.QtCore import Qt, Signal, QRegularExpression

from PySide6.QtGui import QIcon, QRegularExpressionValidator

from ..core.vault import SecureNote, CreditCard

from .theme import get_theme

from .ui_utils import load_svg_icon, get_icon_path

from .secure_note_dialog import SecureNoteDialog

class ItemTypeButton(QFrame):

    clicked = Signal()

    def __init__(self, icon_name: str, label: str, icon_color: str = "#3B9EFF", parent=None):

        super().__init__(parent)

        self.icon_name = icon_name

        self.label_text = label

        self.icon_color = icon_color

        self._enabled = True

        self.setFixedSize(140, 100)

        self.setCursor(Qt.PointingHandCursor)

        self.setup_ui()

    def setup_ui(self):

        self.theme = get_theme()

        self._update_style()

        layout = QVBoxLayout(self)

        layout.setContentsMargins(10, 16, 10, 10)

        layout.setSpacing(8)

        layout.setAlignment(Qt.AlignCenter)

        self.icon_label = QLabel()

        self.icon_label.setPixmap(load_svg_icon(self.icon_name, 32, self.icon_color))

        self.icon_label.setAlignment(Qt.AlignCenter)

        self.icon_label.setStyleSheet("background: transparent; border: none;")

        layout.addWidget(self.icon_label)

        self.text_label = QLabel(self.label_text)

        self.text_label.setAlignment(Qt.AlignCenter)

        self.text_label.setStyleSheet(f"""
            color: {self.theme.colors.foreground};
            font-size: 12px;
            font-weight: 500;
            background: transparent;
            border: none;
        """)

        layout.addWidget(self.text_label)

    def _update_style(self):

        if self._enabled:

            self.setStyleSheet(f"""
                QFrame {{

                    background-color: {self.theme.colors.card};
                    border: 1px solid {self.theme.colors.border};
                    border-radius: 12px;
                }}
                QFrame:hover {{

                    background-color: {self.theme.colors.accent};
                    border-color: {self.theme.colors.primary};
                }}
            """)

        else:

            self.setStyleSheet(f"""
                QFrame {{

                    background-color: {self.theme.colors.card};
                    border: 1px solid {self.theme.colors.border};
                    border-radius: 12px;
                    opacity: 0.5;
                }}
            """)

    def setEnabled(self, enabled: bool):

        self._enabled = enabled

        self._update_style()

        if not enabled:

            self.setCursor(Qt.ArrowCursor)

        else:

            self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):

        if self._enabled:

            self.clicked.emit()

        super().mousePressEvent(event)

class AddNewItemDialog(QDialog):

    login_selected = Signal()

    credit_card_selected = Signal()

    secure_note_selected = Signal()

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setWindowTitle("Add New Item")

        self.setFixedSize(520, 360)

        self.setModal(True)

        self.setup_ui()

    def setup_ui(self):

        theme = get_theme()

        self.setStyleSheet(f"""
            QDialog {{

                background-color: {theme.colors.background};
                border-radius: 16px;
            }}
        """)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(24, 20, 24, 16)

        layout.setSpacing(10)

        title = QLabel("Add New Item")

        title.setStyleSheet(f"""
            color: {theme.colors.foreground};
            font-size: 20px;
            font-weight: 600;
        """)

        layout.addWidget(title)

        grid_container = QFrame()

        grid_container.setStyleSheet(f"""
            QFrame {{

                background-color: {theme.colors.card};
                border-radius: 12px;
                border: 1px solid {theme.colors.border};
            }}
        """)

        grid_container_layout = QVBoxLayout(grid_container)

        grid_container_layout.setContentsMargins(16, 16, 16, 16)

        grid = QGridLayout()

        grid.setSpacing(14)

        btn_login = ItemTypeButton("key", "Login", "#3B9EFF")

        btn_login.clicked.connect(self._on_login)

        grid.addWidget(btn_login, 0, 0)

        btn_credit_card = ItemTypeButton("credit_card", "Credit Card", "#F59E0B")

        btn_credit_card.clicked.connect(self._on_credit_card)

        grid.addWidget(btn_credit_card, 0, 1)

        btn_secure_note = ItemTypeButton("note", "Secure Note", "#22C55E")

        btn_secure_note.clicked.connect(self._on_secure_note)

        grid.addWidget(btn_secure_note, 0, 2)

        btn_identity = ItemTypeButton("person", "Identity", "#8B5CF6")

        btn_identity.setEnabled(False)

        grid.addWidget(btn_identity, 1, 0)

        btn_document = ItemTypeButton("folder", "Document", "#EF4444")

        btn_document.setEnabled(False)

        grid.addWidget(btn_document, 1, 1)

        btn_more = QPushButton("...")

        btn_more.setFixedSize(140, 100)

        btn_more.setEnabled(False)

        btn_more.setStyleSheet(f"""
            QPushButton {{

                background-color: transparent;
                border: 1px dashed {theme.colors.border};
                border-radius: 12px;
                color: {theme.colors.muted_foreground};
                font-size: 20px;
            }}
        """)

        grid.addWidget(btn_more, 1, 2)

        grid_container_layout.addLayout(grid)

        layout.addWidget(grid_container)

        btn_layout = QHBoxLayout()

        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")

        cancel_btn.setFixedSize(90, 36)

        cancel_btn.setCursor(Qt.PointingHandCursor)

        cancel_btn.setStyleSheet(f"""
            QPushButton {{

                background-color: {theme.colors.card};
                color: {theme.colors.foreground};
                border: 1px solid {theme.colors.border};
                border-radius: 8px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{

                background-color: {theme.colors.accent};
            }}
        """)

        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def _on_login(self):

        self.login_selected.emit()

        self.accept()

    def _on_credit_card(self):

        self.credit_card_selected.emit()

        self.accept()

    def _on_secure_note(self):

        self.secure_note_selected.emit()

        self.accept()

class CreditCardDialog(QDialog):

    def __init__(self, card: Optional[CreditCard] = None, parent=None):

        super().__init__(parent)

        self.card = card

        self.setWindowTitle("Edit Credit Card" if card else "Add Credit Card")

        self.setFixedSize(700, 540)

        self.setModal(True)

        self._formatting = False

        self.setup_ui()

    def setup_ui(self):

        theme = get_theme()

        self.setStyleSheet(f"""
            QDialog {{

                background-color: {theme.colors.background};
            }}
        """)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(28, 24, 28, 24)

        layout.setSpacing(20)

        header_layout = QHBoxLayout()

        header_layout.setSpacing(12)

        title = QLabel("Edit Credit Card" if self.card else "Add Credit Card")

        title.setStyleSheet(f"""
            color: {theme.colors.foreground};
            font-size: 20px;
            font-weight: 600;
        """)

        header_layout.addWidget(title)

        header_layout.addStretch()

        layout.addLayout(header_layout)

        content_layout = QHBoxLayout()

        content_layout.setSpacing(32)

        preview_container = QVBoxLayout()

        preview_container.setSpacing(12)

        self.card_preview = self._create_card_preview(theme)

        preview_container.addWidget(self.card_preview)

        preview_label = QLabel("Live preview")

        preview_label.setAlignment(Qt.AlignCenter)

        preview_label.setStyleSheet(f"""
            color: {theme.colors.muted_foreground};
            font-size: 11px;
        """)

        preview_container.addWidget(preview_label)

        preview_container.addStretch()

        content_layout.addLayout(preview_container)

        form_layout = QVBoxLayout()

        form_layout.setSpacing(14)

        self.title_input = self._create_field("CARD TITLE", "e.g., Business Credit Card", theme)

        form_layout.addLayout(self.title_input['layout'])

        self.name_input = self._create_field("CARDHOLDER NAME", "JOHN DOE", theme)

        self.name_input['input'].textChanged.connect(self._update_preview)

        form_layout.addLayout(self.name_input['layout'])

        self.number_input = self._create_field("CARD NUMBER", "0000 0000 0000 0000", theme)

        self.number_input['input'].setMaxLength(19)

        self.number_input['input'].textChanged.connect(self._format_card_number)

        form_layout.addLayout(self.number_input['layout'])

        exp_cvv_layout = QHBoxLayout()

        exp_cvv_layout.setSpacing(16)

        self.expiry_input = self._create_field("EXPIRY", "MM/YY", theme, width=100)

        self.expiry_input['input'].setMaxLength(5)

        self.expiry_input['input'].textChanged.connect(self._format_expiry)

        exp_cvv_layout.addLayout(self.expiry_input['layout'])

        self.cvv_input = self._create_field("CVV", "•••", theme, width=80, is_password=True)

        self.cvv_input['input'].setMaxLength(4)

        exp_cvv_layout.addLayout(self.cvv_input['layout'])

        exp_cvv_layout.addStretch()

        form_layout.addLayout(exp_cvv_layout)

        notes_group = QVBoxLayout()

        notes_group.setSpacing(6)

        notes_label = QLabel("NOTES")

        notes_label.setStyleSheet(f"""
            color: {theme.colors.primary};
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
        """)

        notes_group.addWidget(notes_label)

        self.notes_input = QTextEdit()

        self.notes_input.setPlaceholderText("Add any additional details here...")

        self.notes_input.setMaximumHeight(60)

        self.notes_input.setStyleSheet(f"""
            QTextEdit {{

                background-color: {theme.colors.input};
                color: {theme.colors.foreground};
                border: 1px solid {theme.colors.border};
                border-radius: 16px;
                padding: 10px;
                font-size: 13px;
            }}
            QTextEdit:focus {{

                border-color: {theme.colors.primary};
            }}
        """)

        notes_group.addWidget(self.notes_input)

        form_layout.addLayout(notes_group)

        form_layout.addStretch()

        content_layout.addLayout(form_layout, 1)

        layout.addLayout(content_layout)

        if self.card:

            self.title_input['input'].setText(self.card.title)

            self.name_input['input'].setText(self.card.cardholder_name)

            formatted_num = self._format_number_string(self.card.card_number)

            self.number_input['input'].setText(formatted_num)

            self.expiry_input['input'].setText(self.card.expiry_date)

            self.cvv_input['input'].setText(self.card.cvv)

            if self.card.notes:

                self.notes_input.setPlainText(self.card.notes)

            self._update_preview()

        btn_layout = QHBoxLayout()

        btn_layout.setSpacing(12)

        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")

        cancel_btn.setFixedSize(100, 40)

        cancel_btn.setCursor(Qt.PointingHandCursor)

        cancel_btn.setStyleSheet(f"""
            QPushButton {{

                background: transparent;
                color: {theme.colors.muted_foreground};
                border: none;
                font-size: 14px;
                font-weight: 500;
            }}
            QPushButton:hover {{

                color: {theme.colors.foreground};
            }}
        """)

        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save")

        save_btn.setFixedSize(100, 40)

        save_btn.setCursor(Qt.PointingHandCursor)

        save_btn.setStyleSheet(f"""
            QPushButton {{

                background-color: {theme.colors.primary};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{

                background-color: #2563eb;
            }}
        """)

        save_btn.clicked.connect(self.accept)

        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _format_number_string(self, number: str) -> str:

        clean = ''.join(filter(str.isdigit, number))

        groups = [clean[i:i+4] for i in range(0, len(clean), 4)]

        return ' '.join(groups)

    def _format_card_number(self, text: str):

        if self._formatting:

            return

        self._formatting = True

        cursor_pos = self.number_input['input'].cursorPosition()

        old_text = text

        clean = ''.join(filter(str.isdigit, text))

        clean = clean[:16]

        formatted = self._format_number_string(clean)

        self.number_input['input'].setText(formatted)

        new_pos = cursor_pos

        if len(formatted) > len(old_text):

            new_pos = cursor_pos + (len(formatted) - len(old_text))

        elif len(formatted) < len(old_text) and cursor_pos > 0:

            new_pos = cursor_pos - (len(old_text) - len(formatted))

        self.number_input['input'].setCursorPosition(min(new_pos, len(formatted)))

        self._formatting = False

        self._update_preview()

    def _format_expiry(self, text: str):

        if self._formatting:

            return

        self._formatting = True

        cursor_pos = self.expiry_input['input'].cursorPosition()

        clean = ''.join(filter(str.isdigit, text))

        clean = clean[:4]

        if len(clean) >= 2:

            formatted = clean[:2] + '/' + clean[2:]

        else:

            formatted = clean

        self.expiry_input['input'].setText(formatted)

        if len(formatted) > cursor_pos:

            self.expiry_input['input'].setCursorPosition(cursor_pos if cursor_pos <= 2 else cursor_pos + 1)

        else:

            self.expiry_input['input'].setCursorPosition(len(formatted))

        self._formatting = False

        self._update_preview()

    def _create_card_preview(self, theme) -> QFrame:

        card = QFrame()

        card.setFixedSize(280, 170)

        card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1e4976, stop:1 #0c2a4a);
                border-radius: 14px;
                border: 1px solid rgba(255,255,255,0.15);
            }
        """)

        card_layout = QVBoxLayout(card)

        card_layout.setContentsMargins(20, 16, 20, 14)

        card_layout.setSpacing(0)

        top_row = QHBoxLayout()

        top_row.setContentsMargins(0, 0, 0, 0)

        chip = QFrame()

        chip.setFixedSize(40, 28)

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

        card_brand = QFrame()

        card_brand.setFixedSize(45, 30)

        card_brand.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #22c55e, stop:1 #16a34a);
                border-radius: 4px;
                border: none;
            }
        """)

        top_row.addWidget(card_brand)

        card_layout.addLayout(top_row)

        card_layout.addStretch()

        number_row = QHBoxLayout()

        number_row.setContentsMargins(0, 0, 0, 0)

        self.preview_number = QLabel("•••• •••• ••••")

        self.preview_number.setStyleSheet("""
            color: white;
            font-size: 16px;
            font-weight: 500;
            letter-spacing: 2px;
            font-family: 'Consolas', 'Monaco', monospace;
            background: transparent;
            border: none;
        """)

        number_row.addWidget(self.preview_number)

        self.preview_last4 = QLabel("0000")

        self.preview_last4.setStyleSheet("""
            color: white;
            font-size: 16px;
            font-weight: 600;
            letter-spacing: 2px;
            font-family: 'Consolas', 'Monaco', monospace;
            background: transparent;
            border: none;
        """)

        number_row.addWidget(self.preview_last4)

        number_row.addStretch()

        card_layout.addLayout(number_row)

        card_layout.addStretch()

        bottom_row = QHBoxLayout()

        bottom_row.setContentsMargins(0, 0, 0, 0)

        self.preview_name = QLabel("YOUR NAME")

        self.preview_name.setStyleSheet("""
            color: white;
            font-size: 11px;
            font-weight: 500;
            letter-spacing: 1px;
            background: transparent;
            border: none;
        """)

        bottom_row.addWidget(self.preview_name)

        bottom_row.addStretch()

        expiry_col = QVBoxLayout()

        expiry_col.setSpacing(2)

        expiry_col.setContentsMargins(0, 0, 0, 0)

        expiry_label = QLabel("EXPIRES")

        expiry_label.setStyleSheet("""
            color: rgba(255,255,255,0.5);
            font-size: 8px;
            letter-spacing: 0.5px;
            background: transparent;
            border: none;
        """)

        expiry_col.addWidget(expiry_label)

        self.preview_expiry = QLabel("MM/YY")

        self.preview_expiry.setStyleSheet("""
            color: white;
            font-size: 11px;
            font-weight: 500;
            background: transparent;
            border: none;
        """)

        expiry_col.addWidget(self.preview_expiry)

        bottom_row.addLayout(expiry_col)

        card_layout.addLayout(bottom_row)

        return card

    def _create_field(self, label_text: str, placeholder: str, theme, width: int = None, is_password: bool = False) -> dict:

        layout = QVBoxLayout()

        layout.setSpacing(6)

        label = QLabel(label_text)

        label.setStyleSheet(f"""
            color: {theme.colors.primary};
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
        """)

        layout.addWidget(label)

        input_field = QLineEdit()

        input_field.setPlaceholderText(placeholder)

        if is_password:

            input_field.setEchoMode(QLineEdit.Password)

        input_field.setStyleSheet(f"""
            QLineEdit {{

                background-color: {theme.colors.input};
                color: {theme.colors.foreground};
                border: 1px solid {theme.colors.border};
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 14px;
            }}
            QLineEdit:focus {{

                border-color: {theme.colors.primary};
            }}
        """)

        if width:

            input_field.setFixedWidth(width)

        layout.addWidget(input_field)

        return {'layout': layout, 'input': input_field}

    def _update_preview(self):

        name = self.name_input['input'].text().strip() or "YOUR NAME"

        self.preview_name.setText(name.upper())

        number = self.number_input['input'].text().strip()

        clean_num = ''.join(filter(str.isdigit, number))

        if len(clean_num) >= 4:

            self.preview_last4.setText(clean_num[-4:])

        else:

            self.preview_last4.setText("0000")

        expiry = self.expiry_input['input'].text().strip() or "MM/YY"

        self.preview_expiry.setText(expiry)

    def get_data(self) -> dict:

        raw_number = ''.join(filter(str.isdigit, self.number_input['input'].text()))

        return {

            'title': self.title_input['input'].text().strip(),

            'cardholder_name': self.name_input['input'].text().strip(),

            'card_number': raw_number,

            'expiry_date': self.expiry_input['input'].text().strip(),

            'cvv': self.cvv_input['input'].text().strip(),

            'notes': self.notes_input.toPlainText().strip() or None

        }
