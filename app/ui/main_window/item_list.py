
from typing import List, Optional

from PySide6.QtWidgets import (

    QWidget, QVBoxLayout, QFrame, QHBoxLayout, QLineEdit, QPushButton, QScrollArea, QMenu

)

from PySide6.QtCore import Qt, Signal, QSize

from PySide6.QtGui import QIcon

from app.core.vault import Credential, SecureNote, CreditCard

from app.ui.theme import get_theme

from app.ui.ui_utils import load_svg_icon, create_icon_button

from app.ui.components.cards import CredentialCard, SecureNoteCard, CreditCardCard

class CredentialsList(QWidget):

    credential_selected = Signal(object)

    add_clicked = Signal()

    toggle_sidebar_requested = Signal()

    def __init__(self, parent=None):

        super().__init__(parent)

        self.credentials = []

        self.secure_notes = []

        self.credit_cards = []

        self.card_map = {}

        self.current_category = "all"

        self.current_folder_id = None

        self.search_query = ""

        self.sort_key = "name"

        self.sort_ascending = True

        self.setup_ui()

    def setup_ui(self):

        theme = get_theme()

        self.setStyleSheet(f"background-color: {theme.colors.list_background};")

        layout = QVBoxLayout(self)

        layout.setContentsMargins(0, 0, 0, 0)

        layout.setSpacing(0)

        header = QFrame()

        header.setStyleSheet(f"background-color: {theme.colors.list_background};")

        header_layout = QVBoxLayout(header)

        header_layout.setContentsMargins(12, 12, 16, 12)

        header_layout.setSpacing(12)

        search_layout = QHBoxLayout()

        search_layout.setSpacing(8)

        self.toggle_sidebar_btn = create_icon_button("menu_sidebar", 18, theme.colors.muted_foreground)

        self.toggle_sidebar_btn.setStyleSheet(f"""
            QPushButton {{

                background-color: transparent;
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{

                background-color: {theme.colors.accent};
            }}
        """)

        self.toggle_sidebar_btn.clicked.connect(self.toggle_sidebar_requested.emit)

        self.toggle_sidebar_btn.setVisible(False)

        search_layout.addWidget(self.toggle_sidebar_btn)

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText("Search Items...")

        self.search_input.setStyleSheet(f"""
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
        """)

        self.search_input.textChanged.connect(self.filter_credentials)

        search_layout.addWidget(self.search_input)

        header_layout.addLayout(search_layout)

        filter_layout = QHBoxLayout()

        filter_layout.setSpacing(8)

        category_btn = QPushButton("All Categories")

        category_btn.setStyleSheet(f"""
            QPushButton {{

                background-color: transparent;
                color: {theme.colors.foreground};
                border: none;
                font-size: 13px;
                text-align: left;
                padding: 0;
            }}
        """)

        filter_layout.addWidget(category_btn, alignment=Qt.AlignVCenter)

        filter_layout.addStretch()

        self.sort_btn = create_icon_button("filter", 14, theme.colors.muted_foreground)

        self.sort_btn.setFixedSize(24, 24)

        self.sort_btn.setStyleSheet(f"""
            QPushButton {{

                background-color: transparent;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{

                background-color: {theme.colors.accent};
            }}
        """)

        self.sort_btn.clicked.connect(self._show_sort_menu)

        filter_layout.addWidget(self.sort_btn, alignment=Qt.AlignVCenter)

        header_layout.addLayout(filter_layout)

        layout.addWidget(header)

        scroll = QScrollArea()

        scroll.setWidgetResizable(True)

        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll.setFrameShape(QFrame.NoFrame)

        scroll.setStyleSheet(f"background-color: {theme.colors.list_background};")

        self.list_container = QWidget()

        self.list_container.setStyleSheet(f"background-color: {theme.colors.list_background};")

        self.list_layout = QVBoxLayout(self.list_container)

        self.list_layout.setContentsMargins(8, 0, 8, 8)

        self.list_layout.setSpacing(4)

        self.list_layout.addStretch()

        scroll.setWidget(self.list_container)

        layout.addWidget(scroll)

        add_container = QWidget()

        add_container.setStyleSheet("background-color: #16191D;")

        add_layout = QHBoxLayout(add_container)

        add_layout.setContentsMargins(16, 12, 16, 16)

        self.add_btn = QPushButton()

        self.add_btn.setIcon(QIcon(load_svg_icon("add", 18, "#ffffff")))

        self.add_btn.setIconSize(QSize(18, 18))

        self.add_btn.setText(" New Item")

        self.add_btn.setCursor(Qt.PointingHandCursor)

        self.add_btn.setStyleSheet(f"""
            QPushButton {{

                background-color: #3B9EFF;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
            }}
            QPushButton:hover {{

                background-color: #3B9EFF;
            }}
        """)

        self.add_btn.clicked.connect(self.add_clicked.emit)

        add_layout.addWidget(self.add_btn)

        layout.addWidget(add_container)

    def set_credentials(self, credentials: List[Credential]):

        self.set_all_items(credentials, [], [])

    def set_all_items(self, credentials: List[Credential],

                      secure_notes: List[SecureNote],

                      credit_cards: List[CreditCard]):

        self.credentials = credentials

        self.secure_notes = secure_notes

        self.credit_cards = credit_cards

        new_keys = set()

        # Build maps for quick lookup
        cred_map = {}
        note_map = {}
        card_data_map = {}

        for c in credentials:
            key = ("credential", c.id)
            new_keys.add(key)
            cred_map[key] = c

        for n in secure_notes:
            key = ("note", n.id)
            new_keys.add(key)
            note_map[key] = n

        for card in credit_cards:
            key = ("card", card.id)
            new_keys.add(key)
            card_data_map[key] = card

        existing_keys = set(self.card_map.keys())

        self.list_container.setUpdatesEnabled(False)

        try:
            # Remove cards that no longer exist
            for key in existing_keys - new_keys:
                if key in self.card_map:
                    widget = self.card_map.pop(key)
                    self.list_layout.removeWidget(widget)
                    widget.deleteLater()

            # Update existing cards or create new ones
            spacer_index = self.list_layout.count() - 1

            for cred in credentials:
                key = ("credential", cred.id)
                if key in self.card_map:
                    # Update existing card with new data
                    old_card = self.card_map[key]
                    old_card.credential = cred
                    old_card.title.setText(cred.domain)
                    old_card.subtitle.setText(cred.username)
                else:
                    # Create new card
                    card = CredentialCard(cred)
                    card.clicked.connect(self.on_card_clicked)
                    self.list_layout.insertWidget(spacer_index, card)
                    self.card_map[key] = card

            for note in secure_notes:
                key = ("note", note.id)
                if key in self.card_map:
                    # Update existing card with new data
                    old_card = self.card_map[key]
                    old_card.note = note
                    old_card.title.setText(note.title)
                    preview = note.content[:50] + "..." if len(note.content) > 50 else note.content
                    preview = preview.split('\n')[0]
                    old_card.subtitle.setText(preview)
                else:
                    # Create new card
                    card = SecureNoteCard(note)
                    card.clicked.connect(self.on_card_clicked)
                    self.list_layout.insertWidget(spacer_index, card)
                    self.card_map[key] = card

            for cc in credit_cards:
                key = ("card", cc.id)
                if key in self.card_map:
                    # Update existing card with new data
                    old_card = self.card_map[key]
                    old_card.card = cc
                    old_card.title.setText(cc.title)
                    last_four = cc.card_number[-4:] if len(cc.card_number) >= 4 else "****"
                    old_card.subtitle.setText(f"•••• {last_four}")
                else:
                    # Create new card
                    card = CreditCardCard(cc)
                    card.clicked.connect(self.on_card_clicked)
                    self.list_layout.insertWidget(spacer_index, card)
                    self.card_map[key] = card

            self.apply_filters()

        finally:

            self.list_container.setUpdatesEnabled(True)

    def set_filter(self, category: str, folder_id: Optional[int] = None):

        self.current_category = category

        self.current_folder_id = folder_id

        self.apply_filters()

    def filter_credentials(self, query: str):

        self.search_query = query.lower()

        self.apply_filters()

    def apply_filters(self):

        self.list_container.setUpdatesEnabled(False)

        try:

            visible_items = []

            for key, card in self.card_map.items():

                item_type = key[0]

                visible = True

                if item_type == "credential":

                    item = card.credential

                    searchable = f"{item.domain} {item.username}".lower()

                    sort_name = item.domain.lower()

                    sort_date = getattr(item, 'updated_at', None) or getattr(item, 'created_at', None)

                elif item_type == "note":

                    item = card.note

                    searchable = f"{item.title} {item.content}".lower()

                    sort_name = item.title.lower()

                    sort_date = getattr(item, 'updated_at', None) or getattr(item, 'created_at', None)

                else:

                    item = card.card

                    searchable = f"{item.title} {item.cardholder_name}".lower()

                    sort_name = item.title.lower()

                    sort_date = getattr(item, 'updated_at', None) or getattr(item, 'created_at', None)

                if self.current_category == "all":

                    if item_type != "credential":

                        visible = False

                elif self.current_category == "favorites":

                    if not item.is_favorite:

                        visible = False

                elif self.current_category == "secure_notes":

                    if item_type != "note":

                        visible = False

                elif self.current_category == "credit_cards":

                    if item_type != "card":

                        visible = False

                elif self.current_category == "folder":

                    if item_type != "credential" or item.folder_id != self.current_folder_id:

                        visible = False

                if visible and self.search_query:

                    if self.search_query not in searchable:

                        visible = False

                if visible:

                    visible_items.append((key, card, sort_name, sort_date))

                else:

                    card.setVisible(False)

            if self.sort_key == "name":

                visible_items.sort(key=lambda x: x[2], reverse=not self.sort_ascending)

            elif self.sort_key == "date_modified":

                visible_items.sort(

                    key=lambda x: x[3] if x[3] else "",

                    reverse=not self.sort_ascending

                )

            spacer_item = self.list_layout.takeAt(self.list_layout.count() - 1)

            for key, card, _, _ in visible_items:

                self.list_layout.removeWidget(card)

            for key, card, _, _ in visible_items:

                card.setVisible(True)

                self.list_layout.addWidget(card)

            self.list_layout.addItem(spacer_item)

        finally:

            self.list_container.setUpdatesEnabled(True)

    def _show_sort_menu(self):

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
            QMenu::separator {{

                height: 1px;
                background-color: {theme.colors.border};
                margin: 4px 8px;
            }}
        """)

        name_action = menu.addAction("✓ Name" if self.sort_key == "name" else "  Name")

        date_action = menu.addAction("✓ Date Modified" if self.sort_key == "date_modified" else "  Date Modified")

        menu.addSeparator()

        asc_action = menu.addAction("✓ Ascending (A-Z)" if self.sort_ascending else "  Ascending (A-Z)")

        desc_action = menu.addAction("✓ Descending (Z-A)" if not self.sort_ascending else "  Descending (Z-A)")

        action = menu.exec_(self.sort_btn.mapToGlobal(self.sort_btn.rect().bottomLeft()))

        if action == name_action:

            self.sort_key = "name"

            self.apply_filters()

        elif action == date_action:

            self.sort_key = "date_modified"

            self.apply_filters()

        elif action == asc_action:

            self.sort_ascending = True

            self.apply_filters()

        elif action == desc_action:

            self.sort_ascending = False

            self.apply_filters()

    def on_card_clicked(self, item):

        clicked_key = None

        if isinstance(item, Credential):

            clicked_key = ("credential", item.id)

        elif isinstance(item, SecureNote):

            clicked_key = ("note", item.id)

        elif isinstance(item, CreditCard):

            clicked_key = ("card", item.id)

        for key, card in self.card_map.items():

            card.set_selected(key == clicked_key)

        self.credential_selected.emit(item)

    def set_sidebar_toggle_visible(self, visible: bool):

        self.toggle_sidebar_btn.setVisible(visible)
