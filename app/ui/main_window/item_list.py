
from typing import List, Optional, Union
import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFrame, QHBoxLayout, QLineEdit, QPushButton, 
    QListView, QMenu, QStyledItemDelegate, QStyle
)
from PySide6.QtCore import (
    Qt, Signal, QSize, QTimer, QAbstractListModel, QSortFilterProxyModel, 
    QModelIndex, QRect
)
from PySide6.QtGui import QIcon, QPainter, QColor, QFont, QPen, QPixmap

from app.core.vault import Credential, SecureNote, CreditCard
from app.ui.theme import get_theme
from app.ui.ui_utils import load_svg_icon, create_icon_button
from app.ui.components.svg_spinner import SvgSpinner
from app.ui.components.favicon import get_favicon, get_credential_color

# --- CONSTANTS ---
ITEM_TYPE_CREDENTIAL = "credential"
ITEM_TYPE_NOTE = "note"
ITEM_TYPE_CARD = "card"

# --- DELEGATE ---
class VaultItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme = get_theme()
        
    def sizeHint(self, option, index):
        return QSize(option.rect.width(), 64)
        
    def paint(self, painter: QPainter, option, index):
        if not index.isValid():
            return
            
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get data
        item_type = index.data(VaultModel.TypeRole)
        title = index.data(VaultModel.TitleRole)
        subtitle = index.data(VaultModel.SubtitleRole)
        domain = index.data(VaultModel.DomainRole) # Only for credentials
        
        # Draw background
        rect = option.rect
        is_selected = option.state & QStyle.State_Selected
        is_hover = option.state & QStyle.State_MouseOver
        
        bg_color = Qt.transparent
        if is_selected:
            bg_color = QColor(self.theme.colors.primary)
        elif is_hover:
            bg_color = QColor(self.theme.colors.accent)
            
        painter.fillRect(rect, bg_color)
        
        # Draw Icon/Favicon
        icon_rect = QRect(rect.left() + 12, rect.top() + 12, 40, 40)
        
        if item_type == ITEM_TYPE_CREDENTIAL:
            self._draw_favicon(painter, icon_rect, domain, title, is_selected, index)
        elif item_type == ITEM_TYPE_NOTE:
            self._draw_generic_icon(painter, icon_rect, "note", "#22C55E")
        elif item_type == ITEM_TYPE_CARD:
            self._draw_generic_icon(painter, icon_rect, "credit_card", "#F59E0B")
            
        # Draw Text
        text_left = icon_rect.right() + 12
        text_width = rect.right() - text_left - 12
        
        # Title
        title_rect = QRect(text_left, rect.top() + 12, text_width, 20)
        title_color = QColor(self.theme.colors.primary_foreground) if is_selected else QColor(self.theme.colors.foreground)
        
        painter.setPen(title_color)
        font = painter.font()
        font.setPixelSize(14)
        font.setWeight(QFont.Medium)
        painter.setFont(font)
        
        title_metrics = painter.fontMetrics()
        elided_title = title_metrics.elidedText(title, Qt.ElideRight, text_width)
        painter.drawText(title_rect, Qt.AlignLeft | Qt.AlignVCenter, elided_title)
        
        # Subtitle
        subtitle_rect = QRect(text_left, title_rect.bottom() + 2, text_width, 18)
        subtitle_color = QColor(255, 255, 255, 200) if is_selected else QColor(self.theme.colors.muted_foreground)
        
        painter.setPen(subtitle_color)
        font.setPixelSize(12)
        font.setWeight(QFont.Normal)
        painter.setFont(font)
        
        sub_metrics = painter.fontMetrics()
        elided_sub = sub_metrics.elidedText(subtitle, Qt.ElideRight, text_width)
        painter.drawText(subtitle_rect, Qt.AlignLeft | Qt.AlignVCenter, elided_sub)
        
        painter.restore()
        
    def _draw_favicon(self, painter, rect, domain, title_fallback, is_selected, index):
        pixmap = index.data(VaultModel.IconRole)
        
        # Draw background container regardless
        if not pixmap:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(get_credential_color(domain)))
            painter.drawRoundedRect(rect, 8, 8)
            
            initial = domain[0].upper() if domain else (title_fallback[0].upper() if title_fallback else "?")
            painter.setPen(Qt.white)
            f = painter.font()
            f.setPixelSize(16)
            f.setBold(True)
            painter.setFont(f)
            painter.drawText(rect, Qt.AlignCenter, initial)
        else:
            # Draw explicit background if needed?? Usually favicon has its own or we want transparent.
            # But just in case transparent png, maybe we don't want a color box behind it if it's a nice logo.
            # Behavior in card was: setStyleSheet("background: transparent") if pixmap loaded.
            # So we DON'T draw the colored box if pixmap exists.
            
            # Center the pixmap
            # Pixmap size from cache is already scaled to icon_size (40) in FaviconLabel/Model?
            # Model uses get_favicon which calls FaviconLoader.
            # FaviconLoader loads raw image. 
            # Wait, FaviconLabel._on_image_loaded did scaling.
            # My current FaviconLoader.get_icon returns the RAW QImage converted to QPixmap?
            # NO, FaviconLoader was unmodified in terms of returning raw data in `_on_finished` callback.
            # But `get_icon` returns `_favicon_cache` entry.
            # `FaviconLabel` was putting SCALED pixmap into `_favicon_cache`.
            
            # IMPORTANT: Reset `_favicon_cache` usage.
            # In `FaviconLabel` (Turn 156), `_on_image_loaded` handles scaling and putting into cache.
            # In my new `VaultModel` (Turn 231), `on_loaded` callback receives the pixmap.
            # `get_favicon` returns cached item.
            
            # The `FaviconLoader` I patched in Turn 230:
            # `_on_finished` calls `callback(image)`. It passes a `QImage`.
            # So `VaultModel` receives a `QImage`.
            # `VaultModel` should convert to `QPixmap` and scale it before caching/setting?
            # Or `_favicon_loader` should handle scaling?
            # Currently `FaviconLabel` was doing the scaling.
            
            # I should update `VaultModel` to scale the image.
            
            pass

        if pixmap:
             # Scale if necessary (delegate painting)
             target_size = QSize(32, 32)
             scaled = pixmap.scaled(target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
             x = rect.x() + (rect.width() - target_size.width()) // 2
             y = rect.y() + (rect.height() - target_size.height()) // 2
             painter.drawPixmap(x, y, scaled)
             
    def _draw_generic_icon(self, painter, rect, icon_name, bg_color_hex):
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(bg_color_hex))
        painter.drawRoundedRect(rect, 8, 8)
        
        pixmap = load_svg_icon(icon_name, 28, "#ffffff")
        icon_x = rect.x() + (rect.width() - 28) // 2
        icon_y = rect.y() + (rect.height() - 28) // 2
        painter.drawPixmap(icon_x, icon_y, pixmap)


# --- WRAPPER CLASSES ---
class VaultItemWrapper:
    def __init__(self, item, type_):
        self.item = item
        self.type = type_
        self.id = item.id
        
        # Cache basic display data
        if type_ == ITEM_TYPE_CREDENTIAL:
            self.title = item.domain
            self.subtitle = item.username
            self.domain = item.domain
            self.updated_at = getattr(item, 'updated_at', 0) or getattr(item, 'created_at', 0)
            self.search_text = f"{item.domain} {item.username}".lower()
            self.is_favorite = item.is_favorite
            self.folder_id = item.folder_id
        elif type_ == ITEM_TYPE_NOTE:
            self.title = item.title
            import re
            # Remove HTML tags for preview
            clean_content = re.sub(r'<[^>]+>', '', item.content)
            # Remove HTML entities like &nbsp; if desired, but basic tag stripping is good start
            preview = clean_content.strip()[:50].split('\n')[0]
            self.subtitle = preview
            self.domain = ""
            self.updated_at = getattr(item, 'updated_at', 0) or getattr(item, 'created_at', 0)
            self.search_text = f"{item.title} {item.content}".lower()
            self.is_favorite = item.is_favorite
            self.folder_id = None
        elif type_ == ITEM_TYPE_CARD:
            self.title = item.title
            last_four = item.card_number[-4:] if len(item.card_number) >= 4 else "****"
            self.subtitle = f"•••• {last_four}"
            self.domain = ""
            self.updated_at = getattr(item, 'updated_at', 0) or getattr(item, 'created_at', 0)
            self.search_text = f"{item.title} {item.cardholder_name}".lower()  
            self.is_favorite = item.is_favorite
            self.folder_id = None
            
        self.icon_pixmap = None # Cache for favicon

# --- MODEL ---
class VaultModel(QAbstractListModel):
    
    TypeRole = Qt.UserRole + 1
    TitleRole = Qt.UserRole + 2
    SubtitleRole = Qt.UserRole + 3
    DomainRole = Qt.UserRole + 4
    ItemRole = Qt.UserRole + 5
    IconRole = Qt.UserRole + 6
    SortDateRole = Qt.UserRole + 7
    IsFavoriteRole = Qt.UserRole + 8
    FolderIdRole = Qt.UserRole + 9
    SearchRole = Qt.UserRole + 10
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items: List[VaultItemWrapper] = []
        
    def rowCount(self, parent=QModelIndex()):
        return len(self.items)
        
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self.items):
            return None
            
        item = self.items[index.row()]
        
        if role == self.TypeRole:
            return item.type
        elif role == self.TitleRole:
            return item.title
        elif role == self.SubtitleRole:
            return item.subtitle
        elif role == self.DomainRole:
            return item.domain
        elif role == self.ItemRole:
            return item.item
        elif role == self.SortDateRole:
            return item.updated_at
        elif role == self.IsFavoriteRole:
            return item.is_favorite
        elif role == self.FolderIdRole:
            return item.folder_id
        elif role == self.SearchRole:
            return item.search_text
            
        elif role == self.IconRole:
            # Handle Icon Loading (Sync)
            if item.type == ITEM_TYPE_CREDENTIAL:
                if item.icon_pixmap is None:
                     # Try to get from cache/disk safely
                     pix = get_favicon(item.domain)
                     if pix:
                         item.icon_pixmap = pix
                         return pix
                     # If return None, it stays None, drawing default fallback
                     return None
                else:
                    return item.icon_pixmap
            return None
            
        return None

    def update_data(self, credentials, notes, cards):
        self.beginResetModel()
        self.items = []
        
        # Helper to safely create items
        for c in credentials:
            self.items.append(VaultItemWrapper(c, ITEM_TYPE_CREDENTIAL))
        for n in notes:
            self.items.append(VaultItemWrapper(n, ITEM_TYPE_NOTE))
        for c in cards:
            self.items.append(VaultItemWrapper(c, ITEM_TYPE_CARD))
            
        self.endResetModel()

    def clear(self):
        self.beginResetModel()
        self.items = []
        self.endResetModel()

    def add_items(self, wrappers):
        if not wrappers:
            return
        start = len(self.items)
        self.beginInsertRows(QModelIndex(), start, start + len(wrappers) - 1)
        self.items.extend(wrappers)
        self.endInsertRows()

# --- PROXY MODEL ---
class VaultSortFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.filter_category = "all"
        self.filter_folder_id = None
        self.search_query = ""
        self.setDynamicSortFilter(True)
        self.setSortCaseSensitivity(Qt.CaseInsensitive)
        
    def set_category_filter(self, category: str, folder_id: Optional[int] = None):
        self.filter_category = category
        self.filter_folder_id = folder_id
        self.invalidateFilter()
        
    def set_search_query(self, query: str):
        self.search_query = query.lower()
        self.invalidateFilter()
        
    def filterAcceptsRow(self, source_row, source_parent):
        # 1. Category Filter
        idx = self.sourceModel().index(source_row, 0, source_parent)
        
        item_type = idx.data(VaultModel.TypeRole)
        is_fav = idx.data(VaultModel.IsFavoriteRole)
        folder_id = idx.data(VaultModel.FolderIdRole)
        
        if self.filter_category == "favorites" and not is_fav:
            return False
        if self.filter_category == "secure_notes" and item_type != ITEM_TYPE_NOTE:
            return False
        if self.filter_category == "credit_cards" and item_type != ITEM_TYPE_CARD:
            return False
        if self.filter_category == "folder":
             if item_type != ITEM_TYPE_CREDENTIAL or folder_id != self.filter_folder_id:
                 return False
        if self.filter_category == "all":
            pass # Show all credentials? Original logic hid non-credentials in "all"? 
            # Re-checking logic: "if self.current_category == "all": if item_type != "credential": visible = False"
            # So "All Categories" actually meant "All Logins". 
            if item_type != ITEM_TYPE_CREDENTIAL:
                 return False
                 
        # 2. Search Filter
        if self.search_query:
            search_text = idx.data(VaultModel.SearchRole)
            if self.search_query not in search_text:
                return False
                
        return True

    def lessThan(self, left, right):
        # Handle sorting by date or string
        # Default sort role is TitleRole (DisplayRole-ish)
        # We might switch to DateRole
        
        # Check current sort role set in View
        return super().lessThan(left, right)


class CredentialsList(QWidget):
    credential_selected = Signal(object)
    add_clicked = Signal()
    toggle_sidebar_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        theme = get_theme()
        self.setStyleSheet(f"background-color: {theme.colors.list_background};")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # --- HEADER ---
        header = QFrame()
        header.setStyleSheet(f"background-color: {theme.colors.list_background};")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(12, 12, 16, 12)
        header_layout.setSpacing(12)
        
        # Search Row
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)
        
        self.toggle_sidebar_btn = create_icon_button("menu_sidebar", 18, theme.colors.muted_foreground)
        self.toggle_sidebar_btn.clicked.connect(self.toggle_sidebar_requested.emit)
        # self.toggle_sidebar_btn.setVisible(False)
        # Fix: If invisible, it shouldn't paint artifacts. 
        # But if the layout allocation remains or backgrounds paint weirdly...
        self.toggle_sidebar_btn.setFixedSize(0, 0)
        self.toggle_sidebar_btn.hide()
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
        self.search_input.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(self.search_input)
        header_layout.addLayout(search_layout)
        
        # Filter Row
        filter_layout = QHBoxLayout()
        self.category_btn = QPushButton("All Logins")
        self.category_btn.setStyleSheet(f"background: transparent; color: {theme.colors.foreground}; border: none; font-size: 13px; text-align: left; padding: 0;")
        filter_layout.addWidget(self.category_btn)
        filter_layout.addStretch()
        
        self.sort_btn = create_icon_button("filter", 14, theme.colors.muted_foreground)
        self.sort_btn.clicked.connect(self._show_sort_menu)
        filter_layout.addWidget(self.sort_btn)
        header_layout.addLayout(filter_layout)
        
        layout.addWidget(header)
        
        # --- LIST VIEW ---
        self.model = VaultModel()
        self.proxy_model = VaultSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setSortRole(VaultModel.TitleRole)
        
        self.list_view = QListView()
        self.list_view.setModel(self.proxy_model)
        self.list_view.setItemDelegate(VaultItemDelegate(self.list_view))
        self.list_view.setFrameShape(QFrame.NoFrame)
        self.list_view.setStyleSheet(f"""
            QListView {{
                background-color: {theme.colors.list_background};
                border: none;
                outline: none;
            }}
            QListView::item {{
                border-bottom: 1px solid {theme.colors.border};
            }}
        """)
        self.list_view.setVerticalScrollMode(QListView.ScrollPerPixel)
        self.list_view.setUniformItemSizes(True) # Optimization
        self.list_view.setSelectionMode(QListView.SingleSelection)
        self.list_view.selectionModel().currentChanged.connect(self.on_selection_changed)
        
        layout.addWidget(self.list_view)
        
        # --- SPINNER ---
        # self.spinner_container = QWidget(self) # REMOVED: Caused artifact
        
        self.spinner = SvgSpinner(size=48, parent=None)
        self.spinner.setStyleSheet("background: transparent; border: none;")
        
        self.loading_overlay = QWidget(self.list_view)
        self.loading_overlay.setVisible(False)
        self.loading_overlay.setStyleSheet("background: transparent;")
        self.loading_overlay.setAttribute(Qt.WA_TranslucentBackground) # Ensure overlay itself is translucent
        
        l_layout = QVBoxLayout(self.loading_overlay)
        l_layout.setAlignment(Qt.AlignCenter)
        l_layout.addWidget(self.spinner)
        
        
    def start_loading(self):
        self.loading_overlay.resize(self.list_view.size())
        self.loading_overlay.setVisible(True)
        self.spinner.start()
        
    def stop_loading(self):
        self.spinner.stop()
        self.loading_overlay.setVisible(False)
        
    def resizeEvent(self, event):
        self.loading_overlay.resize(self.list_view.size())
        super().resizeEvent(event)
        
    def set_all_items(self, credentials, notes, cards):
        self.model.update_data(credentials, notes, cards)
        # Select first item if nothing selected?
        if self.proxy_model.rowCount() > 0:
            # self.list_view.setCurrentIndex(self.proxy_model.index(0, 0))
            pass
    
    def clear_items(self):
        self.model.clear()

    def add_items_batch(self, credentials, notes, cards):
        wrappers = []
        for c in credentials: wrappers.append(VaultItemWrapper(c, ITEM_TYPE_CREDENTIAL))
        for n in notes: wrappers.append(VaultItemWrapper(n, ITEM_TYPE_NOTE))
        for c in cards: wrappers.append(VaultItemWrapper(c, ITEM_TYPE_CARD))
        self.model.add_items(wrappers)
            
    def set_filter(self, category, folder_id=None):
        label_map = {
            "all": "All Logins",
            "favorites": "Favorites",
            "secure_notes": "Secure Notes",
            "credit_cards": "Credit Cards",
            "folder": "Folder"
        }
        self.category_btn.setText(label_map.get(category, "Items"))
        self.proxy_model.set_category_filter(category, folder_id)
        
    def on_search_changed(self, query):
        self.proxy_model.set_search_query(query)
        
    def on_selection_changed(self, current, previous):
        if not current.isValid():
            return
            
        # Map proxy index to source index
        # Actually current is proxy index
        item = current.data(VaultModel.ItemRole)
        if item:
            self.credential_selected.emit(item)
            
    def set_sidebar_toggle_visible(self, visible):
        self.toggle_sidebar_btn.setVisible(visible)

    def _show_sort_menu(self):
        theme = get_theme()
        menu = QMenu(self)
        # ... (Reuse styling from memory or previous file, stripped for brevity but functionality remains)
        menu.setStyleSheet(f"QMenu {{ background-color: {theme.colors.card}; border: 1px solid {theme.colors.border}; }} QMenu::item {{ color: {theme.colors.foreground}; padding: 8px 16px; }}")

        # Reuse simple actions
        a_name = menu.addAction("Name")
        a_date = menu.addAction("Date Modified")
        menu.addSeparator()
        a_asc = menu.addAction("Ascending")
        a_desc = menu.addAction("Descending")
        
        action = menu.exec(self.sort_btn.mapToGlobal(self.sort_btn.rect().bottomLeft()))
        
        if action == a_name:
            self.proxy_model.setSortRole(VaultModel.TitleRole)
            self.proxy_model.sort(0, self.proxy_model.sortOrder())
        elif action == a_date:
            self.proxy_model.setSortRole(VaultModel.SortDateRole)
            self.proxy_model.sort(0, self.proxy_model.sortOrder())
        elif action == a_asc:
            self.proxy_model.sort(0, Qt.AscendingOrder)
        elif action == a_desc:
            self.proxy_model.sort(0, Qt.DescendingOrder)
