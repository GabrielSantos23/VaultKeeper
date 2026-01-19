
from typing import List, Optional

from PySide6.QtWidgets import (

    QScrollArea, QFrame, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton,

    QMenu, QApplication

)

from PySide6.QtCore import Qt, Signal, QTimer, QSize

from PySide6.QtGui import QIcon

from app.core.vault import Credential, SecureNote, CreditCard

from app.core.totp import get_totp_code

from app.core.password_strength import analyze_password

from app.core.config import get_config

from app.ui.theme import get_theme

from app.ui.ui_utils import load_svg_icon, create_icon_button

from app.ui.components.favicon import FaviconLabel

from app.ui.components.fields import TOTPProgressWidget

from app.ui.item_detail_panels import SecureNoteDetailPanel, CreditCardDetailPanel
from app.ui.components.elided_label import ElidedLabel

class DetailPanel(QScrollArea):

    edit_requested = Signal(object)

    delete_requested = Signal(object)

    favorite_toggled = Signal(object)

    folder_move_requested = Signal(object, object)

    status_message = Signal(str)

    def __init__(self, parent=None):

        super().__init__(parent)

        self.credential = None

        self.current_note = None

        self.current_card = None

        self.available_folders = []

        self._totp_update_timer = None

        self.setup_ui()

    def setup_ui(self):

        theme = get_theme()

        self.setWidgetResizable(True)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.setFrameShape(QFrame.NoFrame)

        self.setStyleSheet(f"""
            QScrollArea {{

                background-color: {theme.colors.background};
                border: none;
            }}
        """)

        self.container = QWidget()

        self.setWidget(self.container)

        self.main_layout = QVBoxLayout(self.container)

        self.main_layout.setContentsMargins(24, 24, 24, 24)

        self.main_layout.setSpacing(16)

        self.show_empty_state()

    def show_empty_state(self):

        self._stop_totp_timer()

        self.clear_layout()

        theme = get_theme()

        center = QWidget()

        center_layout = QVBoxLayout(center)

        center_layout.setAlignment(Qt.AlignCenter)

        center_layout.setSpacing(16)

        icon_label = QLabel()

        icon_label.setPixmap(load_svg_icon("lock", 64, theme.colors.muted_foreground))

        icon_label.setAlignment(Qt.AlignCenter)

        center_layout.addWidget(icon_label)

        text = QLabel("Select a credential")

        text.setStyleSheet(f"""
            color: {theme.colors.muted_foreground};
            font-size: 16px;
            font-weight: 500;
        """)

        text.setAlignment(Qt.AlignCenter)

        center_layout.addWidget(text)

        self.main_layout.addStretch()

        self.main_layout.addWidget(center)

        self.main_layout.addStretch()

    def clear_layout(self):

        self._clear_layout_recursive(self.main_layout)

    def _clear_layout_recursive(self, layout):

        if layout is None:

            return

        while layout.count():

            child = layout.takeAt(0)

            if child.widget():

                child.widget().deleteLater()

            elif child.layout():

                self._clear_layout_recursive(child.layout())

                child.layout().deleteLater()

    def show_credential(self, credential: Credential):

        self.credential = credential

        self._stop_totp_timer()

        self.clear_layout()

        theme = get_theme()

        header_widget = QWidget()

        header_widget.setStyleSheet("background-color: transparent;")

        header_layout = QHBoxLayout(header_widget)

        header_layout.setContentsMargins(0, 0, 0, 0)

        header_layout.setSpacing(16)

        favicon = FaviconLabel(credential.domain, size=56)

        header_layout.addWidget(favicon, alignment=Qt.AlignTop)

        title_section = QVBoxLayout()

        title_section.setSpacing(6)

        title = ElidedLabel(credential.domain)

        title.setStyleSheet(f"""
            color: {theme.colors.foreground};
            font-size: 22px;
            font-weight: 600;
            background-color: transparent;
        """)

        title_section.addWidget(title)

        tags_row = QHBoxLayout()

        tags_row.setSpacing(8)

        if credential.is_favorite:

            star_label = QLabel()

            star_label.setPixmap(load_svg_icon("star_filled", 16, "#eab308"))

            star_label.setStyleSheet("background-color: transparent;")

            tags_row.addWidget(star_label)

        folder_icon = QLabel()

        folder_icon.setPixmap(load_svg_icon("folder", 12, theme.colors.muted_foreground))

        folder_icon.setStyleSheet("background-color: transparent;")

        tags_row.addWidget(folder_icon)

        folder_name = "All Items"

        if credential.folder_id and self.available_folders:

            for folder in self.available_folders:

                if folder.id == credential.folder_id:

                    folder_name = folder.name

                    break

        category_label = QLabel(folder_name)

        category_label.setStyleSheet(f"""
            color: {theme.colors.muted_foreground};
            font-size: 12px;
            background-color: transparent;
        """)

        tags_row.addWidget(category_label)

        sep_label = QLabel("/")

        sep_label.setStyleSheet(f"""
            color: {theme.colors.muted_foreground};
            font-size: 12px;
            background-color: transparent;
        """)

        tags_row.addWidget(sep_label)

        type_icon = QLabel()

        type_icon.setPixmap(load_svg_icon("globe", 12, theme.colors.muted_foreground))

        type_icon.setStyleSheet("background-color: transparent;")

        tags_row.addWidget(type_icon)

        type_label = QLabel("Login")

        type_label.setStyleSheet(f"""
            color: {theme.colors.muted_foreground};
            font-size: 12px;
            background-color: transparent;
        """)

        tags_row.addWidget(type_label)

        tags_row.addStretch()

        title_section.addLayout(tags_row)

        header_layout.addLayout(title_section, stretch=1)

        edit_btn = QPushButton()

        edit_btn.setIcon(QIcon(load_svg_icon("edit", 14, theme.colors.foreground)))

        edit_btn.setIconSize(QSize(14, 14))

        edit_btn.setText(" Edit")

        edit_btn.setCursor(Qt.PointingHandCursor)

        edit_btn.setFixedHeight(36)

        edit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.colors.secondary};
                color: {theme.colors.secondary_foreground};
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
                font-weight: 500;
                font-size: 14px;
            }}
            QPushButton:hover {{

                background-color: {theme.colors.accent};
            }}
        """)

        edit_btn.clicked.connect(lambda: self.edit_requested.emit(credential))

        header_layout.addWidget(edit_btn, alignment=Qt.AlignTop)

        more_btn = create_icon_button("more_vert", 18, theme.colors.muted_foreground)

        more_btn.setFixedSize(36, 36)

        more_btn.setStyleSheet(f"""
            QPushButton {{

                background-color: transparent;
                border: none;
                border-radius: 8px;
            }}
            QPushButton:hover {{

                background-color: {theme.colors.accent};
            }}
        """)

        more_btn.clicked.connect(lambda: self._show_menu(more_btn, credential))

        header_layout.addWidget(more_btn, alignment=Qt.AlignTop)

        self.main_layout.addWidget(header_widget)

        self.main_layout.addSpacing(24)

        main_card = QWidget()

        main_card.setObjectName("MainCredentialsCard")

        main_card.setAutoFillBackground(True)

        main_card.setStyleSheet(f"""
            #MainCredentialsCard {{

                background-color: #16191D;
                border-radius: 16px;
                border: 1px solid {theme.colors.border};
            }}
            #MainCredentialsCard QLabel {{

                background-color: transparent;
            }}
            #MainCredentialsCard QPushButton {{

                background-color: transparent;
            }}
        """)

        main_card_layout = QVBoxLayout(main_card)

        main_card_layout.setContentsMargins(20, 4, 20, 4)

        main_card_layout.setSpacing(0)

        username_section = self._create_field_section("USERNAME", credential.username, False, theme)

        main_card_layout.addLayout(username_section)

        sep1 = QFrame()

        sep1.setFixedHeight(1)

        sep1.setStyleSheet(f"background-color: {theme.colors.border};")

        main_card_layout.addWidget(sep1)

        password_section = self._create_field_section("PASSWORD", credential.password, True, theme)

        main_card_layout.addLayout(password_section)

        if credential.totp_secret:

            sep_totp = QFrame()

            sep_totp.setFixedHeight(1)

            sep_totp.setStyleSheet(f"background-color: {theme.colors.border};")

            main_card_layout.addWidget(sep_totp)

            totp_section = self._create_totp_section(credential.totp_secret, theme)

            main_card_layout.addLayout(totp_section)

        if credential.backup_codes:

            sep_backup = QFrame()

            sep_backup.setFixedHeight(1)

            sep_backup.setStyleSheet(f"background-color: {theme.colors.border};")

            main_card_layout.addWidget(sep_backup)

            backup_section = self._create_backup_codes_section(credential.backup_codes, theme)

            main_card_layout.addLayout(backup_section)

        self.main_layout.addWidget(main_card)

        self.main_layout.addSpacing(16)

        website_label = QLabel("WEBSITE")

        website_label.setStyleSheet(f"""
            color: {theme.colors.primary};
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
            background-color: transparent;
        """)

        self.main_layout.addWidget(website_label)

        website_url = credential.domain if credential.domain.startswith("http") else f"https://{credential.domain}"

        website_link = QLabel(f'<a href="{website_url}" style="color: {theme.colors.foreground}; text-decoration: none;">{website_url}</a> <span style="color: {theme.colors.muted_foreground};">↗</span>')

        website_link.setOpenExternalLinks(True)

        website_link.setStyleSheet(f"""
            font-size: 14px;
            background-color: transparent;
        """)

        self.main_layout.addWidget(website_link)

        if credential.notes:

            self.main_layout.addSpacing(20)

            notes_label = QLabel("NOTES")

            notes_label.setStyleSheet(f"""
                color: {theme.colors.primary};
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 0.5px;
                background-color: transparent;
            """)

            self.main_layout.addWidget(notes_label)

            notes_text = QLabel(credential.notes)

            notes_text.setWordWrap(True)

            notes_text.setStyleSheet(f"""
                color: {theme.colors.foreground};
                font-size: 14px;
                line-height: 1.5;
                background-color: transparent;
            """)

            self.main_layout.addWidget(notes_text)

        self.main_layout.addStretch()

        timestamps_widget = QWidget()

        timestamps_widget.setStyleSheet("background-color: transparent;")

        ts_layout = QVBoxLayout(timestamps_widget)

        ts_layout.setSpacing(4)

        ts_layout.setContentsMargins(0, 16, 0, 0)

        if hasattr(credential, 'updated_at') and credential.updated_at:

            modified = QLabel(f"MODIFIED: {credential.updated_at}")

            modified.setStyleSheet(f"""
                color: {theme.colors.muted_foreground};
                font-size: 10px;
                letter-spacing: 0.5px;
                background-color: transparent;
            """)

            modified.setAlignment(Qt.AlignCenter)

            ts_layout.addWidget(modified)

        if hasattr(credential, 'created_at') and credential.created_at:

            created = QLabel(f"CREATED: {credential.created_at}")

            created.setStyleSheet(f"""
                color: {theme.colors.muted_foreground};
                font-size: 10px;
                letter-spacing: 0.5px;
                background-color: transparent;
            """)

            created.setAlignment(Qt.AlignCenter)

            ts_layout.addWidget(created)

        self.main_layout.addWidget(timestamps_widget)

    def _create_field_section(self, label: str, value: str, is_password: bool, theme) -> QVBoxLayout:

        section = QVBoxLayout()

        section.setSpacing(8)

        section.setContentsMargins(0, 16, 0, 16)

        header_row = QHBoxLayout()

        header_row.setSpacing(8)

        label_widget = QLabel(label)

        label_widget.setStyleSheet(f"""
            color: {theme.colors.primary};
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
            background-color: transparent;
        """)

        header_row.addWidget(label_widget)

        header_row.addStretch()

        if is_password:

            analysis = analyze_password(value)

            strength_label = QLabel(analysis.label)

            strength_label.setStyleSheet(f"""
                color: {analysis.color};
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 0.5px;
                background-color: transparent;
            """)

            strength_label.setToolTip("\n".join(analysis.feedback))

            header_row.addWidget(strength_label)

            strength_icon = QLabel()

            strength_icon.setPixmap(load_svg_icon("shield", 12, analysis.color))

            strength_icon.setStyleSheet("background-color: transparent;")

            header_row.addWidget(strength_icon)

        section.addLayout(header_row)

        value_row = QHBoxLayout()

        value_row.setSpacing(8)

        if is_password:

            self._password_label = QLabel("•" * 24)

            self._password_value = value

            self._password_visible = False

            value_widget = self._password_label

        else:

            value_widget = QLabel(value)

        value_widget.setStyleSheet(f"""
            color: {theme.colors.foreground};
            font-size: 15px;
            background-color: transparent;
        """)

        value_row.addWidget(value_widget, alignment=Qt.AlignVCenter)

        if is_password:

            toggle_btn = create_icon_button("view", 14, theme.colors.muted_foreground)

            toggle_btn.setFixedSize(24, 24)

            toggle_btn.setStyleSheet(f"""
                QPushButton {{

                    background-color: transparent;
                    border: none;
                    border-radius: 4px;
                }}
                QPushButton:hover {{

                    background-color: {theme.colors.accent};
                }}
            """)

            toggle_btn.clicked.connect(lambda: self._toggle_password_visibility(toggle_btn, theme))

            value_row.addWidget(toggle_btn, alignment=Qt.AlignVCenter)

        value_row.addStretch()

        copy_btn = create_icon_button("copy", 14, theme.colors.muted_foreground)

        copy_btn.setFixedSize(24, 24)

        copy_btn.setStyleSheet(f"""
            QPushButton {{

                background-color: transparent;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{

                background-color: {theme.colors.accent};
            }}
        """)

        copy_btn.clicked.connect(lambda: self._copy_field(value, label, is_password))

        value_row.addWidget(copy_btn, alignment=Qt.AlignVCenter)

        section.addLayout(value_row)

        return section

    def _toggle_password_visibility(self, button, theme):

        self._password_visible = not self._password_visible

        if self._password_visible:

            self._password_label.setText(self._password_value)

            button.setIcon(QIcon(load_svg_icon("visibility_off", 16, theme.colors.muted_foreground)))

        else:

            self._password_label.setText("•" * 24)

            button.setIcon(QIcon(load_svg_icon("view", 16, theme.colors.muted_foreground)))

    def _copy_field(self, value: str, label: str, is_password: bool):

        QApplication.clipboard().setText(value)

        self.status_message.emit(f"✓ {label} copiado!")

        if is_password:

            QTimer.singleShot(10000, lambda: QApplication.clipboard().clear())

    def _create_totp_section(self, totp_secret: str, theme) -> QVBoxLayout:

        section = QVBoxLayout()

        section.setSpacing(8)

        section.setContentsMargins(0, 16, 0, 16)

        header_row = QHBoxLayout()

        header_row.setSpacing(8)

        label_widget = QLabel("TWO-FACTOR CODE")

        label_widget.setStyleSheet(f"""
            color: {theme.colors.primary};
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
            background-color: transparent;
        """)

        header_row.addWidget(label_widget)

        header_row.addStretch()

        section.addLayout(header_row)

        value_row = QHBoxLayout()

        value_row.setSpacing(8)

        self._totp_secret = totp_secret

        self._totp_code_label = QLabel("--- ---")

        self._totp_code_label.setStyleSheet(f"""
            color: {theme.colors.foreground};
            font-size: 20px;
            font-weight: 600;
            font-family: 'Consolas', 'Monaco', monospace;
            letter-spacing: 2px;
            background-color: transparent;
        """)

        value_row.addWidget(self._totp_code_label, alignment=Qt.AlignVCenter)

        self._totp_timer_label = QLabel("30s")

        self._totp_timer_label.setFixedWidth(35)

        self._totp_timer_label.setStyleSheet(f"""
            color: {theme.colors.muted_foreground};
            font-size: 12px;
            font-weight: 500;
            background-color: transparent;
        """)

        value_row.addWidget(self._totp_timer_label, alignment=Qt.AlignVCenter)

        self._totp_progress = TOTPProgressWidget(30)

        value_row.addWidget(self._totp_progress, alignment=Qt.AlignVCenter)

        value_row.addStretch()

        copy_btn = create_icon_button("copy", 14, theme.colors.muted_foreground)

        copy_btn.setFixedSize(24, 24)

        copy_btn.setStyleSheet(f"""
            QPushButton {{

                background-color: transparent;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{

                background-color: {theme.colors.accent};
            }}
        """)

        copy_btn.clicked.connect(self._copy_totp_code)

        value_row.addWidget(copy_btn, alignment=Qt.AlignVCenter)

        section.addLayout(value_row)

        self._start_totp_timer(theme)

        return section

    def _start_totp_timer(self, theme):

        if hasattr(self, '_totp_update_timer') and self._totp_update_timer:

            self._totp_update_timer.stop()

        self._totp_update_timer = QTimer(self)

        self._totp_theme = theme

        self._totp_update_timer.timeout.connect(self._update_totp_display)

        self._totp_update_timer.start(1000)

        self._update_totp_display()

    def _stop_totp_timer(self):

        if hasattr(self, '_totp_update_timer') and self._totp_update_timer:

            self._totp_update_timer.stop()

            self._totp_update_timer = None

    def _update_totp_display(self):

        if not hasattr(self, '_totp_code_label') or self._totp_code_label is None:

            self._stop_totp_timer()

            return

        try:

            if not self._totp_code_label.isVisible():

                pass

        except RuntimeError:

            self._stop_totp_timer()

            return

        try:

            code, remaining = get_totp_code(self._totp_secret)

            formatted_code = f"{code[:3]} {code[3:]}" if len(code) == 6 else code

            self._totp_code_label.setText(formatted_code)

            self._totp_timer_label.setText(f"{remaining}s")

            self._totp_progress.set_remaining(remaining)

            if remaining <= 5:

                self._totp_code_label.setStyleSheet("""
                    color: #ef4444;
                    font-size: 20px;
                    font-weight: 600;
                    font-family: 'Consolas', 'Monaco', monospace;
                    letter-spacing: 2px;
                    background-color: transparent;
                """)

            else:

                self._totp_code_label.setStyleSheet(f"""
                    color: {self._totp_theme.colors.foreground};
                    font-size: 20px;
                    font-weight: 600;
                    font-family: 'Consolas', 'Monaco', monospace;
                    letter-spacing: 2px;
                    background-color: transparent;
                """)

        except RuntimeError:

            self._stop_totp_timer()

        except Exception:

            try:

                self._totp_code_label.setText("ERROR")

                self._totp_timer_label.setText("--")

            except RuntimeError:

                self._stop_totp_timer()

    def _copy_totp_code(self):

        try:

            code, _ = get_totp_code(self._totp_secret)

            QApplication.clipboard().setText(code)

            self.status_message.emit("✓ TOTP Code copiado!")

            QTimer.singleShot(30000, lambda: QApplication.clipboard().clear())

        except:

            pass

    def _create_backup_codes_section(self, backup_codes: str, theme) -> QVBoxLayout:

        section = QVBoxLayout()

        section.setSpacing(8)

        section.setContentsMargins(0, 16, 0, 16)

        header_row = QHBoxLayout()

        header_row.setSpacing(8)

        label_widget = QLabel("BACKUP 2FA CODE")

        label_widget.setStyleSheet(f"""
            color: {theme.colors.primary};
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
            background-color: transparent;
        """)

        header_row.addWidget(label_widget)

        header_row.addStretch()

        section.addLayout(header_row)

        value_row = QHBoxLayout()

        value_row.setSpacing(8)

        self._backup_codes_value = backup_codes

        self._backup_codes_visible = False

        self._backup_codes_label = QLabel("•" * min(24, len(backup_codes)))

        self._backup_codes_label.setStyleSheet(f"""
            color: {theme.colors.foreground};
            font-size: 15px;
            font-family: 'Consolas', 'Monaco', monospace;
            background-color: transparent;
        """)

        value_row.addWidget(self._backup_codes_label, alignment=Qt.AlignVCenter)

        value_row.addStretch()

        self._backup_toggle_btn = create_icon_button("view", 14, theme.colors.muted_foreground)

        self._backup_toggle_btn.setFixedSize(24, 24)

        self._backup_toggle_btn.setStyleSheet(f"""
            QPushButton {{

                background-color: transparent;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{

                background-color: {theme.colors.accent};
            }}
        """)

        self._backup_toggle_btn.clicked.connect(lambda: self._toggle_backup_visibility(theme))

        value_row.addWidget(self._backup_toggle_btn, alignment=Qt.AlignVCenter)

        copy_btn = create_icon_button("copy", 14, theme.colors.muted_foreground)

        copy_btn.setFixedSize(24, 24)

        copy_btn.setStyleSheet(f"""
            QPushButton {{

                background-color: transparent;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{

                background-color: {theme.colors.accent};
            }}
        """)

        copy_btn.clicked.connect(self._copy_backup_codes)

        value_row.addWidget(copy_btn, alignment=Qt.AlignVCenter)

        section.addLayout(value_row)

        return section

    def _toggle_backup_visibility(self, theme):

        self._backup_codes_visible = not self._backup_codes_visible

        if self._backup_codes_visible:

            self._backup_codes_label.setText(self._backup_codes_value)

            self._backup_toggle_btn.setIcon(QIcon(load_svg_icon("visibility_off", 14, theme.colors.muted_foreground)))

        else:

            self._backup_codes_label.setText("•" * min(24, len(self._backup_codes_value)))

            self._backup_toggle_btn.setIcon(QIcon(load_svg_icon("view", 14, theme.colors.muted_foreground)))

    def _copy_backup_codes(self):

        QApplication.clipboard().setText(self._backup_codes_value)

        self.status_message.emit("✓ Backup Code copiado!")

        QTimer.singleShot(30000, lambda: QApplication.clipboard().clear())

    def _show_menu(self, button, credential):

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

                color: {theme.colors.foreground};
                padding: 8px 16px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{

                background-color: {theme.colors.accent};
            }}
        """)

        if credential.is_favorite:

            fav_action = menu.addAction("Remove from Favorites")

            fav_action.setIcon(QIcon(load_svg_icon("star", 16, theme.colors.warning)))

        else:

            fav_action = menu.addAction("Add to Favorites")

            fav_action.setIcon(QIcon(load_svg_icon("star", 16, theme.colors.muted_foreground)))

        menu.addSeparator()

        folder_menu = menu.addMenu("Move to Folder")

        folder_menu.setIcon(QIcon(load_svg_icon("folder", 16, theme.colors.foreground)))

        if credential.folder_id:

            remove_folder_action = folder_menu.addAction("Remove from Folder")

            remove_folder_action.setIcon(QIcon(load_svg_icon("close", 16, theme.colors.muted_foreground)))

            folder_menu.addSeparator()

        else:

            remove_folder_action = None

        folder_actions = {}

        for folder in self.available_folders:

            if credential.folder_id == folder.id:

                continue

            action = folder_menu.addAction(folder.name)

            action.setIcon(QIcon(load_svg_icon("folder", 16, theme.colors.primary)))

            folder_actions[action] = folder

        if not folder_actions and not remove_folder_action:

            empty_action = folder_menu.addAction("No folders available")

            empty_action.setEnabled(False)

        menu.addSeparator()

        delete_action = menu.addAction("Delete")

        delete_action.setIcon(QIcon(load_svg_icon("delete", 16, theme.colors.destructive)))

        action = menu.exec_(button.mapToGlobal(button.rect().bottomLeft()))

        if action == fav_action and self.credential:

            self.favorite_toggled.emit(self.credential)

        elif action == delete_action and self.credential:

            self.delete_requested.emit(self.credential)

        elif action == remove_folder_action and self.credential:

            self.folder_move_requested.emit(self.credential, None)

        elif action in folder_actions:

            self.folder_move_requested.emit(self.credential, folder_actions[action].id)

    def set_available_folders(self, folders: List):

        self.available_folders = folders

    def show_secure_note(self, note: SecureNote):

        self._stop_totp_timer()

        self.clear_layout()

        self.credential = None

        self.current_note = note

        self.current_card = None

        note_panel = SecureNoteDetailPanel(note)

        note_panel.edit_requested.connect(self._edit_secure_note)

        note_panel.delete_requested.connect(self._delete_secure_note)

        note_panel.favorite_toggled.connect(self._toggle_note_favorite)

        self.main_layout.addWidget(note_panel)

    def show_credit_card(self, card: CreditCard):

        self._stop_totp_timer()

        self.clear_layout()

        self.credential = None

        self.current_note = None

        self.current_card = card

        card_panel = CreditCardDetailPanel(card)

        card_panel.edit_requested.connect(self._edit_credit_card)

        card_panel.delete_requested.connect(self._delete_credit_card)

        card_panel.favorite_toggled.connect(self._toggle_card_favorite)

        self.main_layout.addWidget(card_panel)

    def _edit_secure_note(self, note: SecureNote):

        self.edit_requested.emit(note)

    def _delete_secure_note(self, note: SecureNote):

        self.delete_requested.emit(note)

    def _toggle_note_favorite(self, note: SecureNote):

        self.favorite_toggled.emit(note)

    def _edit_credit_card(self, card: CreditCard):

        self.edit_requested.emit(card)

    def _delete_credit_card(self, card: CreditCard):

        self.delete_requested.emit(card)

    def _toggle_card_favorite(self, card: CreditCard):

        self.favorite_toggled.emit(card)
