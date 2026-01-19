
import string

import secrets

from typing import Optional

from PySide6.QtWidgets import (

    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,

    QTextEdit, QFrame

)

from PySide6.QtCore import Qt

from PySide6.QtGui import QIcon

from app.core.vault import Credential

from app.core.totp import is_valid_totp_secret, get_totp_code

from app.ui.theme import get_theme

from app.ui.ui_utils import create_icon_button, load_svg_icon

class CredentialDialog(QDialog):

    def __init__(self, credential: Optional[Credential] = None, parent=None):

        super().__init__(parent)

        self.credential = credential

        self.setWindowTitle("Edit Credential" if credential else "New Credential")

        self.setFixedSize(500, 520)

        self.setModal(True)

        self.setup_ui()

    def setup_ui(self):

        theme = get_theme()

        self.setStyleSheet(f"""
            QDialog {{

                background-color: {theme.colors.background};
            }}
        """)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(32, 28, 32, 28)

        layout.setSpacing(20)

        header_layout = QHBoxLayout()

        header_layout.setSpacing(12)

        title = QLabel("Edit Credential" if self.credential else "New Credential")

        title.setStyleSheet(f"""
            color: {theme.colors.foreground};
            font-size: 20px;
            font-weight: 600;
        """)

        header_layout.addWidget(title)

        header_layout.addStretch()

        layout.addLayout(header_layout)

        form_layout = QVBoxLayout()

        form_layout.setSpacing(16)

        domain_user_row = QHBoxLayout()

        domain_user_row.setSpacing(16)

        self.domain_field = self._create_field("DOMAIN", "example.com", theme)

        if self.credential:

            self.domain_field['input'].setText(self.credential.domain)

        domain_user_row.addLayout(self.domain_field['layout'], 1)

        self.username_field = self._create_field("USERNAME", "user@email.com", theme)

        if self.credential:

            self.username_field['input'].setText(self.credential.username)

        domain_user_row.addLayout(self.username_field['layout'], 1)

        form_layout.addLayout(domain_user_row)

        password_group = QVBoxLayout()

        password_group.setSpacing(6)

        password_label = QLabel("PASSWORD")

        password_label.setStyleSheet(f"""
            color: {theme.colors.primary};
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
        """)

        password_group.addWidget(password_label)

        password_row = QHBoxLayout()

        password_row.setSpacing(8)

        self.password_input = QLineEdit()

        self.password_input.setEchoMode(QLineEdit.Password)

        self.password_input.setPlaceholderText("••••••••")

        if self.credential:

            self.password_input.setText(self.credential.password)

        self.password_input.setStyleSheet(self._get_input_style())

        password_row.addWidget(self.password_input)

        generate_btn = create_icon_button("key", 16, theme.colors.muted_foreground, "Generate password")

        generate_btn.setStyleSheet(f"""
            QPushButton {{

                background-color: {theme.colors.secondary};
                border: 1px solid {theme.colors.border};
                border-radius: 8px;
            }}
            QPushButton:hover {{

                background-color: {theme.colors.accent};
            }}
        """)

        generate_btn.setFixedSize(42, 42)

        generate_btn.clicked.connect(self.generate_password)

        password_row.addWidget(generate_btn, alignment=Qt.AlignBottom)

        show_btn = create_icon_button("view", 16, theme.colors.muted_foreground, "Show/hide")

        show_btn.setStyleSheet(f"""
            QPushButton {{

                background-color: {theme.colors.secondary};
                border: 1px solid {theme.colors.border};
                border-radius: 8px;
            }}
            QPushButton:hover {{

                background-color: {theme.colors.accent};
            }}
        """)

        show_btn.setFixedSize(42, 42)

        show_btn.clicked.connect(self.toggle_password)

        password_row.addWidget(show_btn, alignment=Qt.AlignBottom)

        password_group.addLayout(password_row)

        form_layout.addLayout(password_group)

        totp_backup_row = QHBoxLayout()

        totp_backup_row.setSpacing(16)

        totp_group = QVBoxLayout()

        totp_group.setSpacing(6)

        totp_label = QLabel("2FA SECRET")

        totp_label.setStyleSheet(f"""
            color: {theme.colors.primary};
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
        """)

        totp_group.addWidget(totp_label)

        totp_input_row = QHBoxLayout()

        totp_input_row.setSpacing(8)

        self.totp_input = QLineEdit()

        self.totp_input.setPlaceholderText("Base32 secret key")

        if self.credential and self.credential.totp_secret:

            self.totp_input.setText(self.credential.totp_secret)

        self.totp_input.setStyleSheet(self._get_input_style())

        self.totp_input.textChanged.connect(self._validate_totp_input)

        totp_input_row.addWidget(self.totp_input)

        if self.credential and self.credential.totp_secret:

            clear_totp_btn = create_icon_button("delete", 14, theme.colors.muted_foreground, "Clear")

            clear_totp_btn.setStyleSheet(f"""
                QPushButton {{

                    background-color: {theme.colors.secondary};
                    border: 1px solid {theme.colors.border};
                    border-radius: 8px;
                }}
                QPushButton:hover {{

                    background-color: {theme.colors.destructive};
                }}
            """)

            clear_totp_btn.setFixedSize(42, 42)

            clear_totp_btn.clicked.connect(self._clear_totp)

            totp_input_row.addWidget(clear_totp_btn, alignment=Qt.AlignBottom)

        totp_group.addLayout(totp_input_row)

        self.totp_validation_label = QLabel("")

        self.totp_validation_label.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 10px;")

        totp_group.addWidget(self.totp_validation_label)

        totp_backup_row.addLayout(totp_group, 1)

        backup_group = QVBoxLayout()

        backup_group.setSpacing(6)

        backup_label = QLabel("BACKUP CODES")

        backup_label.setStyleSheet(f"""
            color: {theme.colors.primary};
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
        """)

        backup_group.addWidget(backup_label)

        backup_input_row = QHBoxLayout()

        backup_input_row.setSpacing(8)

        self.backup_input = QLineEdit()

        self.backup_input.setPlaceholderText("Recovery codes")

        self.backup_input.setEchoMode(QLineEdit.Password)

        if self.credential and self.credential.backup_codes:

            self.backup_input.setText(self.credential.backup_codes)

        self.backup_input.setStyleSheet(self._get_input_style())

        backup_input_row.addWidget(self.backup_input)

        backup_toggle_btn = create_icon_button("view", 14, theme.colors.muted_foreground, "Show/hide")

        backup_toggle_btn.setStyleSheet(f"""
            QPushButton {{

                background-color: {theme.colors.secondary};
                border: 1px solid {theme.colors.border};
                border-radius: 8px;
            }}
            QPushButton:hover {{

                background-color: {theme.colors.accent};
            }}
        """)

        backup_toggle_btn.setFixedSize(42, 42)

        backup_toggle_btn.clicked.connect(self._toggle_backup_visibility)

        backup_input_row.addWidget(backup_toggle_btn, alignment=Qt.AlignBottom)

        if self.credential and self.credential.backup_codes:

            clear_backup_btn = create_icon_button("close", 14, theme.colors.muted_foreground, "Clear")

            clear_backup_btn.setStyleSheet(f"""
                QPushButton {{

                    background-color: {theme.colors.secondary};
                    border: 1px solid {theme.colors.border};
                    border-radius: 8px;
                }}
                QPushButton:hover {{

                    background-color: {theme.colors.destructive};
                }}
            """)

            clear_backup_btn.setFixedSize(42, 42)

            clear_backup_btn.clicked.connect(self._clear_backup)

            backup_input_row.addWidget(clear_backup_btn, alignment=Qt.AlignBottom)

        backup_group.addLayout(backup_input_row)

        backup_spacer = QLabel("")

        backup_spacer.setStyleSheet(f"font-size: 10px;")

        backup_group.addWidget(backup_spacer)

        totp_backup_row.addLayout(backup_group, 1)

        form_layout.addLayout(totp_backup_row)

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

        if self.credential and self.credential.notes:

            self.notes_input.setText(self.credential.notes)

        self.notes_input.setStyleSheet(f"""
            QTextEdit {{

                background-color: {theme.colors.input};
                color: {theme.colors.foreground};
                border: 1px solid {theme.colors.border};
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
            }}
            QTextEdit:focus {{

                border-color: {theme.colors.primary};
            }}
        """)

        notes_group.addWidget(self.notes_input)

        form_layout.addLayout(notes_group)

        form_layout.addStretch()

        layout.addLayout(form_layout)

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

    def _create_field(self, label_text: str, placeholder: str, theme, width: int = None) -> dict:

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

        input_field.setStyleSheet(self._get_input_style())

        if width:

            input_field.setFixedWidth(width)

        layout.addWidget(input_field)

        return {'layout': layout, 'input': input_field}

    @property

    def domain_input(self):

        return self.domain_field['input']

    @property

    def username_input(self):

        return self.username_field['input']

    def _get_input_style(self) -> str:

        theme = get_theme()

        return f"""
            QLineEdit {{

                background-color: {theme.colors.input};
                border: 1px solid {theme.colors.border};
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 14px;
                color: {theme.colors.foreground};
            }}
            QLineEdit:focus {{

                border-color: {theme.colors.ring};
            }}
        """

    def generate_password(self):

        chars = string.ascii_letters + string.digits + "!@#$%^&*"

        password = ''.join(secrets.choice(chars) for _ in range(16))

        self.password_input.setText(password)

        self.password_input.setEchoMode(QLineEdit.Normal)

    def toggle_password(self):

        if self.password_input.echoMode() == QLineEdit.Password:

            self.password_input.setEchoMode(QLineEdit.Normal)

        else:

            self.password_input.setEchoMode(QLineEdit.Password)

    def _validate_totp_input(self, text: str):

        theme = get_theme()

        if not text.strip():

            self.totp_validation_label.setText("")

            return

        if is_valid_totp_secret(text.strip()):

            try:

                code, remaining = get_totp_code(text.strip())

                self.totp_validation_label.setText(f"✓ Valid - Current code: {code} ({remaining}s remaining)")

                self.totp_validation_label.setStyleSheet(f"color: #22c55e; font-size: 11px;")

            except:

                self.totp_validation_label.setText("✗ Invalid TOTP secret")

                self.totp_validation_label.setStyleSheet(f"color: #ef4444; font-size: 11px;")

        else:

            self.totp_validation_label.setText("✗ Invalid base32 format")

            self.totp_validation_label.setStyleSheet(f"color: #ef4444; font-size: 11px;")

    def _clear_totp(self):

        self.totp_input.clear()

        self._totp_cleared = True

        self.totp_validation_label.setText("TOTP will be removed when saved")

        self.totp_validation_label.setStyleSheet(f"color: #f97316; font-size: 11px;")

    def _toggle_backup_visibility(self):

        if self.backup_input.echoMode() == QLineEdit.Password:

            self.backup_input.setEchoMode(QLineEdit.Normal)

        else:

            self.backup_input.setEchoMode(QLineEdit.Password)

    def _clear_backup(self):

        self.backup_input.clear()

        self._backup_cleared = True

    def get_data(self) -> dict:

        totp_secret = self.totp_input.text().strip() or None

        clear_totp = getattr(self, '_totp_cleared', False) and not totp_secret

        backup_codes = self.backup_input.text().strip() or None

        clear_backup = getattr(self, '_backup_cleared', False) and not backup_codes

        return {

            'domain': self.domain_input.text().strip(),

            'username': self.username_input.text().strip(),

            'password': self.password_input.text(),

            'notes': self.notes_input.toPlainText().strip() or None,

            'totp_secret': totp_secret,

            'clear_totp': clear_totp,

            'backup_codes': backup_codes,

            'clear_backup': clear_backup

        }
