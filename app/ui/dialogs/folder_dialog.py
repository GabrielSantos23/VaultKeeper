
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QPushButton, QComboBox, QMessageBox

from PySide6.QtCore import Qt

from app.ui.theme import get_theme

from app.ui.ui_utils import get_icon_path

class FolderDialog(QDialog):

    def __init__(self, parent=None, title="Create New Folder", current_name=""):

        super().__init__(parent)

        self.setWindowTitle(title)

        self.setFixedSize(440, 380)

        self.folder_name = None

        self.selected_vault = "Personal"

        theme = get_theme()

        self.setStyleSheet(f"""
            QDialog {{

                background-color: #16191D;
            }}
            QLabel {{

                background: transparent;
                border: none;
            }}
        """)

        layout = QVBoxLayout(self)

        layout.setSpacing(24)

        layout.setContentsMargins(32, 32, 32, 32)

        lbl_title = QLabel(title)

        lbl_title.setStyleSheet(f"font-size: 20px; font-weight: 600; color: #ffffff;")

        layout.addWidget(lbl_title)

        form = QVBoxLayout()

        form.setSpacing(16)

        name_group = QVBoxLayout()

        name_group.setSpacing(8)

        lbl_name = QLabel("Folder Name")

        lbl_name.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 13px; font-weight: 500;")

        name_group.addWidget(lbl_name)

        self.input = QLineEdit(current_name)

        self.input.setPlaceholderText("Enter folder name...")

        self.input.setStyleSheet(f"""
            QLineEdit {{

                background-color: #0f1115;
                color: #ffffff;
                border: 1px solid {theme.colors.border};
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
            }}
            QLineEdit:focus {{

                border: 1px solid {theme.colors.primary};
            }}
        """)

        self.input.setFocus()

        name_group.addWidget(self.input)

        form.addLayout(name_group)

        vault_group = QVBoxLayout()

        vault_group.setSpacing(8)

        lbl_vault = QLabel("Select Vault")

        lbl_vault.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 13px; font-weight: 500;")

        vault_group.addWidget(lbl_vault)

        self.vault_combo = QComboBox()

        self.vault_combo.addItems(["Personal", "Team Vault", "Professional"])

        self.vault_combo.setStyleSheet(f"""
            QComboBox {{

                background-color: #0f1115;
                color: #ffffff;
                border: 1px solid {theme.colors.border};
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
            }}
            QComboBox::drop-down {{

                border: none;
                width: 30px;
            }}
            QComboBox::down-arrow {{

                image: url({{get_icon_path("chevron-down-white").replace('\\', '/')}});
                width: 16px;
                height: 16px;
            }}
            QComboBox QAbstractItemView {{

                background-color: #0f1115;
                color: #ffffff;
                selection-background-color: {theme.colors.accent};
                border: 1px solid {theme.colors.border};
            }}
        """)

        vault_group.addWidget(self.vault_combo)

        form.addLayout(vault_group)

        layout.addLayout(form)

        layout.addStretch()

        btn_layout = QHBoxLayout()

        btn_layout.setSpacing(12)

        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")

        cancel_btn.setCursor(Qt.PointingHandCursor)

        cancel_btn.setFixedWidth(100)

        cancel_btn.setStyleSheet(f"""
            QPushButton {{

                background-color: transparent;
                color: {theme.colors.muted_foreground};
                border: none;
                font-size: 14px;
                font-weight: 500;
            }}
            QPushButton:hover {{

                color: #ffffff;
            }}
        """)

        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Create Folder")

        save_btn.setCursor(Qt.PointingHandCursor)

        save_btn.setFixedWidth(140)

        save_btn.setFixedHeight(40)

        self._setup_save_btn_style(save_btn, theme)

        save_btn.clicked.connect(self.accept_folder)

        btn_layout.addWidget(cancel_btn)

        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _setup_save_btn_style(self, btn, theme):

        btn.setStyleSheet(f"""
            QPushButton {{

                background-color: #3b82f6;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{

                background-color: #2563eb;
            }}
        """)

    def accept_folder(self):

        name = self.input.text().strip()

        if name:

            self.folder_name = name
            self.selected_vault = self.vault_combo.currentText()

            self.accept()

        else:

            self.input.setFocus()
