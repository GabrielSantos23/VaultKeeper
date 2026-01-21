
from typing import List

from PySide6.QtWidgets import (

    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QMenu

)

from PySide6.QtCore import Qt, Signal, QSize, QTimer

from PySide6.QtGui import QIcon, QAction

from app.core.vault import Folder

from app.core.gdrive import GoogleDriveManager

from app.ui.theme import get_theme

from app.ui.ui_utils import load_svg_icon, create_icon_button

from app.ui.components.sidebar import SidebarButton

class Sidebar(QFrame):

    category_changed = Signal(str)

    extension_clicked = Signal()

    lock_clicked = Signal()

    toggle_sidebar = Signal()

    add_folder_clicked = Signal()

    folder_selected = Signal(int)

    folder_edit_requested = Signal(object)

    folder_delete_requested = Signal(object)

    settings_clicked = Signal()

    google_drive_clicked = Signal()

    add_item_clicked = Signal()

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setObjectName("SidebarFrame")

        self.setFixedWidth(200)

        self.current_category = "all"

        self.folders = []

        self.folder_buttons = []

        self.setup_ui()

    def setup_ui(self):

        theme = get_theme()

        self.setFrameShape(QFrame.NoFrame)

        self.setStyleSheet(f"""
            #SidebarFrame {{

                background-color: {theme.colors.sidebar};
            }}
            #SidebarFrame QLabel {{

                background-color: transparent;
            }}
            #SidebarFrame QPushButton {{

                background-color: transparent;
            }}
        """)

        self.layout = QVBoxLayout(self)

        self.layout.setContentsMargins(8, 12, 8, 12)

        self.layout.setSpacing(2)

        header_layout = QHBoxLayout()

        header_layout.setContentsMargins(8, 0, 4, 16)

        header_layout.setSpacing(8)

        logo_icon = QLabel()

        logo_icon.setPixmap(load_svg_icon("shield", 24, theme.colors.primary))

        header_layout.addWidget(logo_icon, alignment=Qt.AlignVCenter)

        app_name = QLabel("VaultKeeper")

        app_name.setStyleSheet(f"""
            color: {theme.colors.sidebar_foreground};
            font-size: 16px;
            font-weight: 600;
        """)

        header_layout.addWidget(app_name, alignment=Qt.AlignVCenter)

        header_layout.addStretch()

        self.toggle_btn = create_icon_button("menu_sidebar", 18, theme.colors.sidebar_muted)

        self.toggle_btn.setFixedSize(28, 28)

        self.toggle_btn.setStyleSheet(f"""
            QPushButton {{

                background-color: transparent;
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{

                background-color: {theme.colors.sidebar_accent};
            }}
        """)

        self.toggle_btn.clicked.connect(self.toggle_sidebar.emit)

        header_layout.addWidget(self.toggle_btn, alignment=Qt.AlignVCenter)

        self.layout.addLayout(header_layout)

        self.btn_all = SidebarButton("grid", "All Items")

        self.btn_all.setChecked(True)

        self.btn_all.clicked.connect(lambda: self.set_category("all"))

        self.layout.addWidget(self.btn_all)

        self.btn_favorites = SidebarButton("star", "Favorites")

        self.btn_favorites.clicked.connect(lambda: self.set_category("favorites"))

        self.layout.addWidget(self.btn_favorites)

        self.btn_watchtower = SidebarButton("view", "Watchtower")
        self.btn_watchtower.clicked.connect(lambda: self.set_category("watchtower"))
        self.layout.addWidget(self.btn_watchtower)

        self.btn_secure_notes = SidebarButton("note", "Secure Notes")

        self.btn_secure_notes.clicked.connect(lambda: self.set_category("secure_notes"))

        self.layout.addWidget(self.btn_secure_notes)

        self.btn_credit_cards = SidebarButton("credit_card", "Credit Cards")

        self.btn_credit_cards.clicked.connect(lambda: self.set_category("credit_cards"))

        self.layout.addWidget(self.btn_credit_cards)

        self.btn_generator = SidebarButton("key", "Generator")

        self.btn_generator.clicked.connect(lambda: self.set_category("generator"))

        self.layout.addWidget(self.btn_generator)

        vaults_header = QWidget()

        vaults_header.setStyleSheet("background-color: transparent;")

        vaults_header_layout = QHBoxLayout(vaults_header)

        vaults_header_layout.setContentsMargins(12, 16, 8, 8)

        vaults_header_layout.setSpacing(4)

        vaults_title = QLabel("VAULTS")

        vaults_title.setStyleSheet(f"""
            color: {theme.colors.sidebar_muted};
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
            background-color: transparent;
        """)

        vaults_header_layout.addWidget(vaults_title, alignment=Qt.AlignVCenter)

        vaults_header_layout.addStretch()

        add_folder_btn = create_icon_button("add", 12, theme.colors.sidebar_muted)

        add_folder_btn.setFixedSize(18, 18)

        add_folder_btn.setStyleSheet(f"""
            QPushButton {{

                background-color: transparent;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{

                background-color: {theme.colors.sidebar_accent};
            }}
        """)

        add_folder_btn.setToolTip("Create new folder")

        add_folder_btn.clicked.connect(self.add_folder_clicked.emit)

        vaults_header_layout.addWidget(add_folder_btn, alignment=Qt.AlignVCenter)

        self.layout.addWidget(vaults_header)

        self.folders_container = QWidget()

        self.folders_container.setStyleSheet("background-color: transparent;")

        self.folders_layout = QVBoxLayout(self.folders_container)

        self.folders_layout.setContentsMargins(0, 0, 0, 0)

        self.folders_layout.setSpacing(2)

        self.layout.addWidget(self.folders_container)

        self.btn_personal = SidebarButton("person", "Personal", font_size=16, is_selectable=False)

        self.folders_layout.addWidget(self.btn_personal)

        self.personal_folders_container = QWidget()

        self.personal_folders_container.setStyleSheet("background-color: transparent;")

        self.personal_folders_layout = QVBoxLayout(self.personal_folders_container)

        self.personal_folders_layout.setContentsMargins(0, 0, 0, 0)

        self.personal_folders_layout.setSpacing(2)

        self.folders_layout.addWidget(self.personal_folders_container)

        self.btn_team = SidebarButton("team", "Team Vault", font_size=16, is_selectable=False)

        self.folders_layout.addWidget(self.btn_team)

        self.team_folders_container = QWidget()

        self.team_folders_container.setStyleSheet("background-color: transparent;")

        self.team_folders_layout = QVBoxLayout(self.team_folders_container)

        self.team_folders_layout.setContentsMargins(0, 0, 0, 0)

        self.team_folders_layout.setSpacing(2)

        self.folders_layout.addWidget(self.team_folders_container)

        self.btn_professional = SidebarButton("work", "Professional", font_size=16, is_selectable=False)

        self.folders_layout.addWidget(self.btn_professional)

        self.professional_folders_container = QWidget()

        self.professional_folders_container.setStyleSheet("background-color: transparent;")

        self.professional_folders_layout = QVBoxLayout(self.professional_folders_container)

        self.professional_folders_layout.setContentsMargins(0, 0, 0, 0)

        self.professional_folders_layout.setSpacing(2)

        self.folders_layout.addWidget(self.professional_folders_container)

        self.static_buttons = [

            self.btn_all, self.btn_favorites, self.btn_watchtower, self.btn_secure_notes, self.btn_credit_cards, self.btn_generator

        ]

        self.personal_folders_container.setVisible(False)
        self.team_folders_container.setVisible(False)
        self.professional_folders_container.setVisible(False)

        self.layout.addStretch()

        bottom_layout = QVBoxLayout()

        bottom_layout.setContentsMargins(4, 8, 4, 4)

        bottom_layout.setSpacing(4)

        theme = get_theme()

        self.sync_status_widget = QWidget()

        self.sync_status_widget.setVisible(False)

        sync_status_layout = QHBoxLayout(self.sync_status_widget)

        sync_status_layout.setContentsMargins(12, 8, 12, 8)

        sync_status_layout.setSpacing(8)

        self.sync_icon_label = QLabel()

        self.sync_icon_label.setPixmap(load_svg_icon("cloud_sync", 14, "#3b82f6"))

        self.sync_icon_label.setFixedSize(16, 16)

        sync_status_layout.addWidget(self.sync_icon_label)

        self.sync_status_label = QLabel("Syncing...")

        self.sync_status_label.setStyleSheet("""
            color: #3b82f6;
            font-size: 12px;
            font-weight: 500;
        """)

        sync_status_layout.addWidget(self.sync_status_label)

        sync_status_layout.addStretch()

        bottom_layout.addWidget(self.sync_status_widget)

        self.drive_btn = QPushButton()

        self.drive_btn.setIcon(QIcon(load_svg_icon("google_drive", 18, theme.colors.sidebar_foreground)))

        self.drive_btn.setIconSize(QSize(18, 18))

        self.drive_btn.setText("  Google Drive Sync")

        self.drive_btn.setCursor(Qt.PointingHandCursor)

        self.drive_btn.setStyleSheet(f"""
            QPushButton {{

                background-color: transparent;
                color: {theme.colors.sidebar_foreground};
                border: none;
                border-radius: 8px;
                padding: 10px 12px;
                text-align: left;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{

                background-color: {theme.colors.sidebar_accent};
            }}
        """)

        self.drive_btn.clicked.connect(self.google_drive_clicked.emit)

        bottom_layout.addWidget(self.drive_btn)

        self.settings_btn = QPushButton()

        self.settings_btn.setIcon(QIcon(load_svg_icon("settings", 18, theme.colors.sidebar_foreground)))

        self.settings_btn.setIconSize(QSize(18, 18))

        self.settings_btn.setText("  Settings")

        self.settings_btn.setCursor(Qt.PointingHandCursor)

        self.settings_btn.setStyleSheet(f"""
            QPushButton {{

                background-color: transparent;
                color: {theme.colors.sidebar_foreground};
                border: none;
                border-radius: 8px;
                padding: 10px 12px;
                text-align: left;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{

                background-color: {theme.colors.sidebar_accent};
            }}
        """)

        self.settings_btn.clicked.connect(self.settings_clicked.emit)

        bottom_layout.addWidget(self.settings_btn)

        # New Item Button
        self.add_btn = QPushButton()
        self.add_btn.setIcon(QIcon(load_svg_icon("add", 18, "#ffffff")))
        self.add_btn.setIconSize(QSize(18, 18))
        self.add_btn.setText(" New Item")
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.colors.primary};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {theme.colors.accent};
            }}
        """)
        self.add_btn.clicked.connect(self.add_item_clicked.emit)
        bottom_layout.addWidget(self.add_btn)

        self.layout.addLayout(bottom_layout)

        self._setup_gdrive_callbacks()

    def _setup_gdrive_callbacks(self):

        GoogleDriveManager.on_sync_start(self._on_sync_start)

        GoogleDriveManager.on_sync_end(self._on_sync_end)

    def _on_sync_start(self):

        QTimer.singleShot(0, self._show_sync_indicator)

    def _on_sync_end(self, success: bool, error: str = None):

        QTimer.singleShot(0, lambda: self._hide_sync_indicator(success, error))

    def _show_sync_indicator(self):

        self.sync_status_label.setText("Syncing...")

        self.sync_status_label.setStyleSheet("""
            color: #3b82f6;
            font-size: 12px;
            font-weight: 500;
        """)

        self.sync_status_widget.setVisible(True)

        self.sync_status_widget.update()

        self.update()

    def _hide_sync_indicator(self, success: bool, error: str = None):

        if success:

            self.sync_status_label.setText("✓ Synced")

            self.sync_status_label.setStyleSheet("""
                color: #22c55e;
                font-size: 12px;
                font-weight: 500;
            """)

        else:

            self.sync_status_label.setText("✗ Sync failed")

            self.sync_status_label.setStyleSheet("""
                color: #ef4444;
                font-size: 12px;
                font-weight: 500;
            """)

        from PySide6.QtCore import QTimer

        QTimer.singleShot(2000, lambda: self.sync_status_widget.setVisible(False))

    def update_gdrive_status(self):

        from app.core.gdrive import get_gdrive_manager

        gdrive = get_gdrive_manager()

        theme = get_theme()

        if gdrive.is_connected():

            self.drive_btn.setIcon(QIcon(load_svg_icon("google_drive", 18, "#22c55e")))

            self.drive_btn.setText("  Google Drive ✓")

        else:

            self.drive_btn.setIcon(QIcon(load_svg_icon("google_drive", 18, theme.colors.sidebar_foreground)))

            self.drive_btn.setText("  Google Drive Sync")

    def set_folders(self, folders: List[Folder]):

        self.folders = folders

        for btn in self.folder_buttons:

            btn.deleteLater()

        self.folder_buttons.clear()

        theme = get_theme()

        self.personal_folders_container.setVisible(False)
        self.team_folders_container.setVisible(False)
        self.professional_folders_container.setVisible(False)

        has_personal = False
        has_team = False
        has_professional = False

        for folder in folders:

            btn = SidebarButton("folder", folder.name, font_size=13, padding_left=32)

            btn.clicked.connect(lambda checked, f=folder: self.on_folder_clicked(f))

            btn.setContextMenuPolicy(Qt.CustomContextMenu)

            btn.customContextMenuRequested.connect(

                lambda pos, b=btn, f=folder: self._show_folder_context_menu(b, f, pos)

            )

            # Determine vault type (default to personal if not set)
            v_type = getattr(folder, 'vault_type', 'personal')
            if v_type == 'team':
                self.team_folders_layout.addWidget(btn)
                has_team = True
            elif v_type == 'professional':
                self.professional_folders_layout.addWidget(btn)
                has_professional = True
            else:
                self.personal_folders_layout.addWidget(btn)
                has_personal = True

            self.folder_buttons.append(btn)
            
        self.personal_folders_container.setVisible(has_personal)
        self.team_folders_container.setVisible(has_team)
        self.professional_folders_container.setVisible(has_professional)

    def _show_folder_context_menu(self, button, folder: Folder, pos):

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

        edit_action = menu.addAction("Rename Folder")

        edit_action.setIcon(QIcon(load_svg_icon("edit", 16, theme.colors.foreground)))

        menu.addSeparator()

        delete_action = menu.addAction("Delete Folder")

        delete_action.setIcon(QIcon(load_svg_icon("delete", 16, theme.colors.destructive)))

        action = menu.exec_(button.mapToGlobal(pos))

        if action == edit_action:

            self.folder_edit_requested.emit(folder)

        elif action == delete_action:

            self.folder_delete_requested.emit(folder)

    def on_folder_clicked(self, folder: Folder):

        self.set_category(f"folder_{folder.id}")

        self.folder_selected.emit(folder.id)

    def set_category(self, category: str):

        self.current_category = category

        for btn in self.static_buttons + self.folder_buttons:

            if btn:

                btn.setChecked(False)

        btn_map = {

            "all": self.btn_all,

            "favorites": self.btn_favorites,

            "watchtower": self.btn_watchtower,

            "secure_notes": self.btn_secure_notes,

            "credit_cards": self.btn_credit_cards,

            "generator": self.btn_generator,

        }

        if category in btn_map:

            btn_map[category].setChecked(True)

        elif category.startswith("folder_"):

            folder_id = int(category.split("_")[1])

            for i, folder in enumerate(self.folders):

                if folder.id == folder_id and i < len(self.folder_buttons):

                    self.folder_buttons[i].setChecked(True)

                    break

        self.category_changed.emit(category)

    def set_all_items_loading(self, loading: bool):
        if loading:
            self.btn_all.start_loading()
        else:
            self.btn_all.stop_loading()
