"""
VaultKeeper - Main Window UI
Modern password manager interface using PySide6
1Password-inspired design with SVG icons
"""

import sys
import secrets
import string
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QLineEdit, QPushButton, QLabel, QListWidget,
    QListWidgetItem, QDialog, QFormLayout, QTextEdit, QMessageBox,
    QFrame, QSpacerItem, QSizePolicy, QMenu, QSystemTrayIcon,
    QSplitter, QScrollArea, QToolButton, QGridLayout, QGraphicsDropShadowEffect,
    QInputDialog
)
from PySide6.QtCore import Qt, QTimer, Signal, QSize, QPropertyAnimation, QEasingCurve, QUrl, QObject
from PySide6.QtGui import QIcon, QAction, QClipboard, QFont, QPalette, QColor, QPainter, QPixmap, QImage
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from ..core.vault import VaultManager, Credential, Folder
from ..core.auth import AuthManager
from ..core.config import get_config
from ..core.password_strength import analyze_password, PasswordStrength
from ..core.totp import TOTPManager, get_totp_code, is_valid_totp_secret
from .theme import get_theme, get_stylesheet, ThemeMode, set_theme
from .settings_dialog import SettingsDialog
from .ui_utils import load_svg_icon, create_icon_button, get_icon_path, ICONS_DIR
from .gdrive_dialog import GoogleDriveDialog




# Global favicon cache
_favicon_cache: Dict[str, QPixmap] = {}
_network_manager: Optional[QNetworkAccessManager] = None


def get_network_manager() -> QNetworkAccessManager:
    """Get or create a global network manager."""
    global _network_manager
    if _network_manager is None:
        _network_manager = QNetworkAccessManager()
    return _network_manager


class FaviconLabel(QLabel):
    """A label that loads and displays favicon from a domain."""
    
    def __init__(self, domain: str, size: int = 40, parent=None):
        super().__init__(parent)
        self.domain = domain
        self.icon_size = size
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignCenter)
        
        # Set initial fallback (colored initial)
        self._show_fallback()
        
        # Try to load favicon
        self._load_favicon()
    
    def _show_fallback(self):
        """Show the fallback colored initial."""
        icon_color = get_credential_color(self.domain)
        initial = self.domain[0].upper() if self.domain else "?"
        self.setText(initial)
        font_size = int(self.icon_size * 0.4)
        radius = int(self.icon_size * 0.2)
        self.setStyleSheet(f"""
            background-color: {icon_color};
            color: white;
            border-radius: {radius}px;
            font-weight: 700;
            font-size: {font_size}px;
        """)
    
    def _load_favicon(self):
        """Load favicon from cache or network."""
        global _favicon_cache
        
        # Check cache first
        if self.domain in _favicon_cache:
            self._set_favicon(_favicon_cache[self.domain])
            return
        
        # Use Google's favicon service (reliable and fast)
        # Alternative: DuckDuckGo's service or direct favicon.ico
        clean_domain = self.domain.replace("https://", "").replace("http://", "").split("/")[0]
        favicon_url = f"https://www.google.com/s2/favicons?domain={clean_domain}&sz=64"
        
        manager = get_network_manager()
        request = QNetworkRequest(QUrl(favicon_url))
        request.setAttribute(QNetworkRequest.RedirectPolicyAttribute, QNetworkRequest.NoLessSafeRedirectPolicy)
        
        reply = manager.get(request)
        reply.finished.connect(lambda: self._on_favicon_loaded(reply))
    
    def _on_favicon_loaded(self, reply: QNetworkReply):
        """Handle favicon response."""
        global _favicon_cache
        
        if reply.error() == QNetworkReply.NoError:
            data = reply.readAll()
            image = QImage()
            if image.loadFromData(data):
                # Check if it's not a default/blank favicon (very small or all same color)
                if image.width() >= 16 and image.height() >= 16:
                    pixmap = QPixmap.fromImage(image)
                    # Scale to desired size
                    scaled = pixmap.scaled(
                        self.icon_size, self.icon_size,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    # Cache it
                    _favicon_cache[self.domain] = scaled
                    self._set_favicon(scaled)
        
        reply.deleteLater()
    
    def _set_favicon(self, pixmap: QPixmap):
        """Set the favicon pixmap."""
        self.setText("")
        self.setPixmap(pixmap)
        radius = int(self.icon_size * 0.2)
        self.setStyleSheet(f"""
            background-color: transparent;
            border-radius: {radius}px;
        """)





# Credential icon colors (vibrant colors for favicons)
CREDENTIAL_COLORS = [
    "#22c55e",  # Green
    "#3b82f6",  # Blue
    "#8b5cf6",  # Purple
    "#ec4899",  # Pink
    "#f97316",  # Orange
    "#14b8a6",  # Teal
    "#eab308",  # Yellow
    "#ef4444",  # Red
]


def get_credential_color(text: str) -> str:
    """Get a consistent color for a credential based on its domain."""
    if not text:
        return CREDENTIAL_COLORS[0]
    hash_val = sum(ord(c) for c in text)
    return CREDENTIAL_COLORS[hash_val % len(CREDENTIAL_COLORS)]


class SidebarButton(QPushButton):
    """A modern button styled for the sidebar with SVG icon."""
    
    def __init__(self, icon_name: str, text: str, font_size: int = 14, padding_left: int = 12, is_selectable: bool = True, parent=None):
        super().__init__(parent)
        self.icon_name = icon_name
        self.label_text = text
        self.font_size = font_size
        self.padding_left = padding_left
        self.is_selectable = is_selectable
        self.setText(f"  {text}")
        
        if is_selectable:
            self.setCheckable(True)
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.setCheckable(False)
            self.setCursor(Qt.ArrowCursor)
            
        self.setMinimumHeight(40)
        self.update_style()
    
    def update_style(self):
        theme = get_theme()
        
        # Update icon color based on checked state
        icon_color = theme.colors.sidebar_foreground
        if self.isChecked():
            icon_color = theme.colors.sidebar_primary_foreground
        
        self.setIcon(QIcon(load_svg_icon(self.icon_name, 18, icon_color)))
        self.setIconSize(QSize(18, 18))
        
        hover_style = ""
        checked_style = ""
        
        if self.is_selectable:
            hover_style = f"""
            QPushButton:hover {{
                background-color: {theme.colors.sidebar_accent};
            }}"""
            checked_style = f"""
            QPushButton:checked {{
                background-color: {theme.colors.sidebar_primary};
                color: {theme.colors.sidebar_primary_foreground};
            }}"""
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {theme.colors.sidebar_foreground};
                border: none;
                border-radius: 8px;
                padding: 10px {self.padding_left}px;
                text-align: left;
                font-size: {self.font_size}px;
                font-weight: 500;
            }}
            {hover_style}
            {checked_style}
        """)
    
    def setChecked(self, checked: bool):
        super().setChecked(checked)
        self.update_style()


class SidebarSection(QWidget):
    """Section header in the sidebar."""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 8)
        layout.setSpacing(0)
        
        theme = get_theme()
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            color: {theme.colors.sidebar_muted};
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
        """)
        layout.addWidget(title_label)


class CredentialCard(QFrame):
    """Modern card widget for credential in list."""
    
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
        
        # Favicon - loads from web with fallback to colored initial
        self.favicon = FaviconLabel(self.credential.domain, size=40)
        layout.addWidget(self.favicon)
        
        # Text container
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


class DetailField(QFrame):
    """Modern field display with copy functionality."""
    
    copied = Signal(str)
    
    def __init__(self, label: str, value: str, is_password: bool = False, parent=None):
        super().__init__(parent)
        self.label_text = label
        self.value_text = value
        self.is_password = is_password
        self.password_visible = False
        self.setup_ui()
    
    def setup_ui(self):
        theme = get_theme()
        
        self.setStyleSheet(f"""
            DetailField {{
                background-color: {theme.colors.card};
                border-radius: 8px;
                border: 1px solid {theme.colors.border};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)
        
        # Label
        label = QLabel(self.label_text.upper())
        label.setStyleSheet(f"""
            color: {theme.colors.primary};
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
        """)
        layout.addWidget(label)
        
        # Value row
        value_layout = QHBoxLayout()
        value_layout.setSpacing(8)
        
        if self.is_password:
            self.value_label = QLabel("•" * 20)
        else:
            self.value_label = QLabel(self.value_text)
        
        self.value_label.setStyleSheet(f"""
            color: {theme.colors.foreground};
            font-size: 14px;
        """)
        self.value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        value_layout.addWidget(self.value_label)
        
        # Password strength indicator (only for password fields)
        if self.is_password:
            analysis = analyze_password(self.value_text)
            strength_label = QLabel(analysis.label)
            strength_label.setStyleSheet(f"""
                color: {analysis.color};
                font-size: 11px;
                font-weight: 600;
            """)
            strength_label.setToolTip("\n".join(analysis.feedback))
            value_layout.addWidget(strength_label)
        
        value_layout.addStretch()
        
        # Action buttons
        if self.is_password:
            self.toggle_btn = create_icon_button("view", 16, theme.colors.muted_foreground, "Mostrar/Ocultar")
            self.toggle_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: none;
                    border-radius: 6px;
                }}
                QPushButton:hover {{
                    background-color: {theme.colors.accent};
                }}
            """)
            self.toggle_btn.clicked.connect(self.toggle_visibility)
            value_layout.addWidget(self.toggle_btn)
        
        copy_btn = create_icon_button("copy", 16, theme.colors.muted_foreground, "Copiar")
        copy_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors.accent};
            }}
        """)
        copy_btn.clicked.connect(self.copy_value)
        value_layout.addWidget(copy_btn)
        
        layout.addLayout(value_layout)
    
    def toggle_visibility(self):
        theme = get_theme()
        self.password_visible = not self.password_visible
        if self.password_visible:
            self.value_label.setText(self.value_text)
            self.toggle_btn.setIcon(QIcon(load_svg_icon("visibility_off", 16, theme.colors.muted_foreground)))
        else:
            self.value_label.setText("•" * 20)
            self.toggle_btn.setIcon(QIcon(load_svg_icon("view", 16, theme.colors.muted_foreground)))
    
    def copy_value(self):
        QApplication.clipboard().setText(self.value_text)
        self.copied.emit(self.label_text)
        if self.is_password:
            timeout = get_config().get_clipboard_timeout()
            if timeout > 0:
                QTimer.singleShot(timeout * 1000, lambda: QApplication.clipboard().clear())


class TOTPField(QFrame):
    """Modern TOTP field display with countdown timer and copy functionality."""
    
    copied = Signal(str)
    
    def __init__(self, totp_secret: str, parent=None):
        super().__init__(parent)
        self.totp_secret = totp_secret
        self.totp_manager = TOTPManager(totp_secret)
        self.setup_ui()
        
        # Start the timer to update every second
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(1000)
        
        # Initial update
        self._update_display()
    
    def setup_ui(self):
        theme = get_theme()
        
        self.setStyleSheet(f"""
            TOTPField {{
                background-color: {theme.colors.card};
                border-radius: 8px;
                border: 1px solid {theme.colors.border};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)
        
        # Label
        label = QLabel("TWO-FACTOR CODE")
        label.setStyleSheet(f"""
            color: {theme.colors.primary};
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
        """)
        layout.addWidget(label)
        
        # Value row
        value_layout = QHBoxLayout()
        value_layout.setSpacing(12)
        
        # TOTP Code display
        self.code_label = QLabel("------")
        self.code_label.setStyleSheet(f"""
            color: {theme.colors.foreground};
            font-size: 24px;
            font-weight: 600;
            font-family: 'Consolas', 'Monaco', monospace;
            letter-spacing: 4px;
        """)
        value_layout.addWidget(self.code_label)
        
        value_layout.addStretch()
        
        # Countdown timer label
        self.timer_label = QLabel("30s")
        self.timer_label.setFixedWidth(40)
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet(f"""
            color: {theme.colors.muted_foreground};
            font-size: 12px;
            font-weight: 500;
        """)
        value_layout.addWidget(self.timer_label)
        
        # Circular progress indicator
        self.progress_widget = TOTPProgressWidget(30)
        value_layout.addWidget(self.progress_widget)
        
        # Copy button
        copy_btn = create_icon_button("copy", 16, theme.colors.muted_foreground, "Copiar")
        copy_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors.accent};
            }}
        """)
        copy_btn.clicked.connect(self.copy_value)
        value_layout.addWidget(copy_btn)
        
        layout.addLayout(value_layout)
    
    def _update_display(self):
        """Update the TOTP code and timer display."""
        try:
            code, remaining = get_totp_code(self.totp_secret)
            # Format code with space in the middle (e.g., "123 456")
            formatted_code = f"{code[:3]} {code[3:]}" if len(code) == 6 else code
            self.code_label.setText(formatted_code)
            self.timer_label.setText(f"{remaining}s")
            self.progress_widget.set_remaining(remaining)
            
            # Change color when low on time
            theme = get_theme()
            if remaining <= 5:
                self.code_label.setStyleSheet(f"""
                    color: #ef4444;
                    font-size: 24px;
                    font-weight: 600;
                    font-family: 'Consolas', 'Monaco', monospace;
                    letter-spacing: 4px;
                """)
            else:
                self.code_label.setStyleSheet(f"""
                    color: {theme.colors.foreground};
                    font-size: 24px;
                    font-weight: 600;
                    font-family: 'Consolas', 'Monaco', monospace;
                    letter-spacing: 4px;
                """)
        except Exception as e:
            self.code_label.setText("ERROR")
            self.timer_label.setText("--")
    
    def copy_value(self):
        """Copy the current TOTP code to clipboard."""
        try:
            code, _ = get_totp_code(self.totp_secret)
            QApplication.clipboard().setText(code)
            self.copied.emit("TOTP Code")
            # Auto-clear after short timeout (TOTP codes expire anyway)
            QTimer.singleShot(30000, lambda: QApplication.clipboard().clear())
        except:
            pass
    
    def cleanup(self):
        """Stop the timer when widget is being destroyed."""
        if self.update_timer:
            self.update_timer.stop()


class TOTPProgressWidget(QWidget):
    """Circular progress widget for TOTP countdown."""
    
    def __init__(self, total_seconds: int = 30, parent=None):
        super().__init__(parent)
        self.total_seconds = total_seconds
        self.remaining_seconds = total_seconds
        self.setFixedSize(24, 24)
    
    def set_remaining(self, remaining: int):
        self.remaining_seconds = remaining
        self.update()
    
    def paintEvent(self, event):
        from PySide6.QtGui import QPen
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        theme = get_theme()
        
        # Calculate progress (0 to 1)
        progress = self.remaining_seconds / self.total_seconds
        
        # Background circle
        pen = QPen(QColor(theme.colors.border))
        pen.setWidth(3)
        painter.setPen(pen)
        painter.drawEllipse(3, 3, 18, 18)
        
        # Progress arc
        if self.remaining_seconds <= 5:
            arc_color = QColor("#ef4444")  # Red when low
        elif self.remaining_seconds <= 10:
            arc_color = QColor("#f97316")  # Orange when getting low
        else:
            arc_color = QColor(theme.colors.primary)
        
        pen.setColor(arc_color)
        pen.setWidth(3)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        
        # Arc goes from 90 degrees (top) clockwise
        start_angle = 90 * 16  # Qt uses 1/16th of a degree
        span_angle = int(-progress * 360 * 16)  # Negative for clockwise
        painter.drawArc(3, 3, 18, 18, start_angle, span_angle)


class DetailPanel(QScrollArea):
    """Right panel showing credential details."""
    
    edit_requested = Signal(object)
    delete_requested = Signal(object)
    favorite_toggled = Signal(object)  # Emits credential when favorite is toggled
    folder_move_requested = Signal(object, object)  # Emits (credential, folder_id or None)
    status_message = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.credential = None
        self.available_folders = []  # List of Folder objects for move menu
        self._totp_update_timer = None  # Timer for TOTP updates
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
        # Stop any running TOTP timer
        self._stop_totp_timer()
        
        self.clear_layout()
        theme = get_theme()
        
        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setAlignment(Qt.AlignCenter)
        center_layout.setSpacing(16)
        
        # Icon
        icon_label = QLabel()
        icon_label.setPixmap(load_svg_icon("lock", 64, theme.colors.muted_foreground))
        icon_label.setAlignment(Qt.AlignCenter)
        center_layout.addWidget(icon_label)
        
        text = QLabel("Selecione uma credencial")
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
        """Recursively clear all items from a layout."""
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
        
        # Stop any running TOTP timer before clearing layout
        self._stop_totp_timer()
        
        self.clear_layout()
        
        theme = get_theme()
        
        # ===== HEADER SECTION =====
        header_widget = QWidget()
        header_widget.setStyleSheet("background-color: transparent;")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(16)
        
        # Favicon - loads from web with fallback to colored initial
        favicon = FaviconLabel(credential.domain, size=56)
        header_layout.addWidget(favicon, alignment=Qt.AlignTop)
        
        # Title section
        title_section = QVBoxLayout()
        title_section.setSpacing(6)
        
        # Domain name
        title = QLabel(credential.domain)
        title.setStyleSheet(f"""
            color: {theme.colors.foreground};
            font-size: 22px;
            font-weight: 600;
            background-color: transparent;
        """)
        title_section.addWidget(title)
        
        # Tags row with star and category
        tags_row = QHBoxLayout()
        tags_row.setSpacing(8)
        
        # Star indicator (favorite)
        if credential.is_favorite:
            star_label = QLabel()
            star_label.setPixmap(load_svg_icon("star_filled", 16, "#eab308"))
            star_label.setStyleSheet("background-color: transparent;")
            tags_row.addWidget(star_label)
        
        # Folder icon and category tag
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
        
        # Separator
        sep_label = QLabel("/")
        sep_label.setStyleSheet(f"""
            color: {theme.colors.muted_foreground};
            font-size: 12px;
            background-color: transparent;
        """)
        tags_row.addWidget(sep_label)
        
        # Type icon
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
        
        # Edit button
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
        
        # More options button
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
        
        # ===== MAIN CREDENTIALS CARD =====
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
        
        # Username field
        username_section = self._create_field_section("USERNAME", credential.username, False, theme)
        main_card_layout.addLayout(username_section)
        
        # Separator
        sep1 = QFrame()
        sep1.setFixedHeight(1)
        sep1.setStyleSheet(f"background-color: {theme.colors.border};")
        main_card_layout.addWidget(sep1)
        
        # Password field
        password_section = self._create_field_section("PASSWORD", credential.password, True, theme)
        main_card_layout.addLayout(password_section)
        
        # TOTP field (if configured)
        if credential.totp_secret:
            # Separator before TOTP
            sep_totp = QFrame()
            sep_totp.setFixedHeight(1)
            sep_totp.setStyleSheet(f"background-color: {theme.colors.border};")
            main_card_layout.addWidget(sep_totp)
            
            # TOTP section
            totp_section = self._create_totp_section(credential.totp_secret, theme)
            main_card_layout.addLayout(totp_section)
        
        # Backup 2FA Code field (if configured)
        if credential.backup_codes:
            # Separator before backup codes
            sep_backup = QFrame()
            sep_backup.setFixedHeight(1)
            sep_backup.setStyleSheet(f"background-color: {theme.colors.border};")
            main_card_layout.addWidget(sep_backup)
            
            # Backup codes section (masked like password)
            backup_section = self._create_backup_codes_section(credential.backup_codes, theme)
            main_card_layout.addLayout(backup_section)
        
        self.main_layout.addWidget(main_card)
        self.main_layout.addSpacing(16)
        
        # ===== WEBSITE SECTION =====
        website_label = QLabel("WEBSITE")
        website_label.setStyleSheet(f"""
            color: {theme.colors.primary};
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
            background-color: transparent;
        """)
        self.main_layout.addWidget(website_label)
        
        # Website link
        website_url = credential.domain if credential.domain.startswith("http") else f"https://{credential.domain}"
        website_link = QLabel(f'<a href="{website_url}" style="color: {theme.colors.foreground}; text-decoration: none;">{website_url}</a> <span style="color: {theme.colors.muted_foreground};">↗</span>')
        website_link.setOpenExternalLinks(True)
        website_link.setStyleSheet(f"""
            font-size: 14px;
            background-color: transparent;
        """)
        self.main_layout.addWidget(website_link)
        
        # ===== NOTES SECTION (if present) =====
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
        
        # ===== TIMESTAMPS =====
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
        """Create a field section with label, value, and actions."""
        section = QVBoxLayout()
        section.setSpacing(8)
        section.setContentsMargins(0, 16, 0, 16)
        
        # Header row with label and (for password) strength indicator
        header_row = QHBoxLayout()
        header_row.setSpacing(8)
        
        # Label
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
        
        # Password strength indicator
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
        
        # Value row - all items aligned horizontally
        value_row = QHBoxLayout()
        value_row.setSpacing(8)
        
        # Value display
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
        
        # Toggle visibility button for password
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
        
        # Copy button - aligned to the right
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
        """Toggle password visibility."""
        self._password_visible = not self._password_visible
        if self._password_visible:
            self._password_label.setText(self._password_value)
            button.setIcon(QIcon(load_svg_icon("visibility_off", 16, theme.colors.muted_foreground)))
        else:
            self._password_label.setText("•" * 24)
            button.setIcon(QIcon(load_svg_icon("view", 16, theme.colors.muted_foreground)))
    
    def _copy_field(self, value: str, label: str, is_password: bool):
        """Copy field value to clipboard."""
        QApplication.clipboard().setText(value)
        self.status_message.emit(f"✓ {label} copiado!")
        if is_password:
            QTimer.singleShot(10000, lambda: QApplication.clipboard().clear())
    
    def _create_totp_section(self, totp_secret: str, theme) -> QVBoxLayout:
        """Create a TOTP field section with live code updates."""
        section = QVBoxLayout()
        section.setSpacing(8)
        section.setContentsMargins(0, 16, 0, 16)
        
        # Header row
        header_row = QHBoxLayout()
        header_row.setSpacing(8)
        
        # Label
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
        
        # Value row
        value_row = QHBoxLayout()
        value_row.setSpacing(8)
        
        # Code display
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
        
        # Timer label
        self._totp_timer_label = QLabel("30s")
        self._totp_timer_label.setFixedWidth(35)
        self._totp_timer_label.setStyleSheet(f"""
            color: {theme.colors.muted_foreground};
            font-size: 12px;
            font-weight: 500;
            background-color: transparent;
        """)
        value_row.addWidget(self._totp_timer_label, alignment=Qt.AlignVCenter)
        
        # Progress widget
        self._totp_progress = TOTPProgressWidget(30)
        value_row.addWidget(self._totp_progress, alignment=Qt.AlignVCenter)
        
        value_row.addStretch()
        
        # Copy button
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
        
        # Start the TOTP update timer
        self._start_totp_timer(theme)
        
        return section
    
    def _start_totp_timer(self, theme):
        """Start timer to update TOTP code every second."""
        if hasattr(self, '_totp_update_timer') and self._totp_update_timer:
            self._totp_update_timer.stop()
        
        self._totp_update_timer = QTimer(self)
        self._totp_theme = theme
        self._totp_update_timer.timeout.connect(self._update_totp_display)
        self._totp_update_timer.start(1000)
        
        # Initial update
        self._update_totp_display()
    
    def _stop_totp_timer(self):
        """Stop the TOTP update timer if running."""
        if hasattr(self, '_totp_update_timer') and self._totp_update_timer:
            self._totp_update_timer.stop()
            self._totp_update_timer = None
    
    def _update_totp_display(self):
        """Update the TOTP code and timer display."""
        # Check if widgets still exist before updating
        if not hasattr(self, '_totp_code_label') or self._totp_code_label is None:
            self._stop_totp_timer()
            return
        
        try:
            # Additional check if Qt object is still valid
            if not self._totp_code_label.isVisible():
                pass  # Widget exists but may be hidden, still update
        except RuntimeError:
            # Qt object was deleted
            self._stop_totp_timer()
            return
        
        try:
            code, remaining = get_totp_code(self._totp_secret)
            formatted_code = f"{code[:3]} {code[3:]}" if len(code) == 6 else code
            self._totp_code_label.setText(formatted_code)
            self._totp_timer_label.setText(f"{remaining}s")
            self._totp_progress.set_remaining(remaining)
            
            # Change color when low on time
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
            # Widget was deleted, stop the timer
            self._stop_totp_timer()
        except Exception:
            # Other error (e.g., TOTP generation failed)
            try:
                self._totp_code_label.setText("ERROR")
                self._totp_timer_label.setText("--")
            except RuntimeError:
                self._stop_totp_timer()
    
    def _copy_totp_code(self):
        """Copy TOTP code to clipboard."""
        try:
            code, _ = get_totp_code(self._totp_secret)
            QApplication.clipboard().setText(code)
            self.status_message.emit("✓ TOTP Code copiado!")
            # Auto-clear after 30 seconds
            QTimer.singleShot(30000, lambda: QApplication.clipboard().clear())
        except:
            pass
    
    def _create_backup_codes_section(self, backup_codes: str, theme) -> QVBoxLayout:
        """Create a backup codes field section (masked like password)."""
        section = QVBoxLayout()
        section.setSpacing(8)
        section.setContentsMargins(0, 16, 0, 16)
        
        # Header row
        header_row = QHBoxLayout()
        header_row.setSpacing(8)
        
        # Label
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
        
        # Value row
        value_row = QHBoxLayout()
        value_row.setSpacing(8)
        
        # Masked code display
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
        
        # Toggle visibility button
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
        
        # Copy button
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
        """Toggle backup codes visibility."""
        self._backup_codes_visible = not self._backup_codes_visible
        if self._backup_codes_visible:
            self._backup_codes_label.setText(self._backup_codes_value)
            self._backup_toggle_btn.setIcon(QIcon(load_svg_icon("visibility_off", 14, theme.colors.muted_foreground)))
        else:
            self._backup_codes_label.setText("•" * min(24, len(self._backup_codes_value)))
            self._backup_toggle_btn.setIcon(QIcon(load_svg_icon("view", 14, theme.colors.muted_foreground)))
    
    def _copy_backup_codes(self):
        """Copy backup codes to clipboard."""
        QApplication.clipboard().setText(self._backup_codes_value)
        self.status_message.emit("✓ Backup Code copiado!")
        # Auto-clear after 30 seconds
        QTimer.singleShot(30000, lambda: QApplication.clipboard().clear())

    
    def _show_menu(self, button, credential):
        theme = get_theme()
        menu = QMenu(self)
        
        # Style the menu
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
        
        # Favorite action
        if credential.is_favorite:
            fav_action = menu.addAction("Remove from Favorites")
            fav_action.setIcon(QIcon(load_svg_icon("star", 16, theme.colors.warning)))
        else:
            fav_action = menu.addAction("Add to Favorites")
            fav_action.setIcon(QIcon(load_svg_icon("star", 16, theme.colors.muted_foreground)))
        
        menu.addSeparator()
        
        # Move to folder submenu
        folder_menu = menu.addMenu("Move to Folder")
        folder_menu.setIcon(QIcon(load_svg_icon("folder", 16, theme.colors.foreground)))
        
        # Remove from folder option (if credential is in a folder)
        if credential.folder_id:
            remove_folder_action = folder_menu.addAction("Remove from Folder")
            remove_folder_action.setIcon(QIcon(load_svg_icon("close", 16, theme.colors.muted_foreground)))
            folder_menu.addSeparator()
        else:
            remove_folder_action = None
        
        # Add each available folder as an option
        folder_actions = {}
        for folder in self.available_folders:
            # Skip if credential is already in this folder
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
        """Set the list of available folders for move menu."""
        self.available_folders = folders


class LoginWidget(QWidget):
    """Login screen."""
    
    login_success = Signal()
    
    def __init__(self, auth: AuthManager, parent=None):
        super().__init__(parent)
        self.auth = auth
        self.setup_ui()
    
    def setup_ui(self):
        theme = get_theme()
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(24)
        
        # Logo
        logo_container = QFrame()
        logo_container.setFixedSize(100, 100)
        logo_container.setStyleSheet(f"""
            background-color: {theme.colors.primary};
            border-radius: 24px;
        """)
        logo_layout = QVBoxLayout(logo_container)
        logo_icon = QLabel()
        logo_icon.setPixmap(load_svg_icon("lock", 48, "#ffffff"))
        logo_icon.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(logo_icon)
        layout.addWidget(logo_container, alignment=Qt.AlignCenter)
        
        # Title
        title = QLabel("VaultKeeper")
        title.setStyleSheet(f"""
            color: {theme.colors.foreground};
            font-size: 28px;
            font-weight: 700;
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Subtitle
        if self.auth.is_first_run():
            subtitle_text = "Create your master password to get started"
        else:
            subtitle_text = "Enter your master password to unlock"
        
        subtitle = QLabel(subtitle_text)
        subtitle.setStyleSheet(f"""
            color: {theme.colors.muted_foreground};
            font-size: 14px;
        """)
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        layout.addSpacing(16)
        
        # Input card
        input_card = QFrame()
        input_card.setFixedWidth(360)
        input_card.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.colors.card};
                border-radius: 12px;
                border: 1px solid {theme.colors.border};
            }}
        """)
        card_layout = QVBoxLayout(input_card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(16)
        
        # Password input
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Master Password")
        self.password_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {theme.colors.input};
                border: 1px solid {theme.colors.border};
                border-radius: 8px;
                padding: 12px 14px;
                font-size: 14px;
                color: {theme.colors.foreground};
            }}
            QLineEdit:focus {{
                border-color: {theme.colors.ring};
            }}
        """)
        self.password_input.returnPressed.connect(self.handle_login)
        card_layout.addWidget(self.password_input)
        
        # Confirm password (first run only)
        if self.auth.is_first_run():
            self.confirm_input = QLineEdit()
            self.confirm_input.setEchoMode(QLineEdit.Password)
            self.confirm_input.setPlaceholderText("Confirm Password")
            self.confirm_input.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {theme.colors.input};
                    border: 1px solid {theme.colors.border};
                    border-radius: 8px;
                    padding: 12px 14px;
                    font-size: 14px;
                    color: {theme.colors.foreground};
                }}
                QLineEdit:focus {{
                    border-color: {theme.colors.ring};
                }}
            """)
            self.confirm_input.returnPressed.connect(self.handle_login)
            card_layout.addWidget(self.confirm_input)
        
        # Error label
        self.error_label = QLabel()
        self.error_label.setStyleSheet(f"""
            color: {theme.colors.destructive};
            font-size: 13px;
            padding: 8px;
            background-color: rgba(239, 68, 68, 0.1);
            border-radius: 6px;
        """)
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.hide()
        card_layout.addWidget(self.error_label)
        
        # Login button
        login_btn = QPushButton("Unlock" if not self.auth.is_first_run() else "Create Vault")
        login_btn.setCursor(Qt.PointingHandCursor)
        login_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.colors.primary};
                color: {theme.colors.primary_foreground};
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {theme.colors.ring};
            }}
        """)
        login_btn.clicked.connect(self.handle_login)
        card_layout.addWidget(login_btn)
        
        layout.addWidget(input_card, alignment=Qt.AlignCenter)
    
    def handle_login(self):
        password = self.password_input.text()
        
        if not password:
            self.show_error("Please enter your master password")
            return
        
        try:
            if self.auth.is_first_run():
                confirm = self.confirm_input.text()
                if password != confirm:
                    self.show_error("Passwords don't match")
                    return
                self.auth.create_master_password(password)
            else:
                self.auth.verify_master_password(password)
            
            self.password_input.clear()
            if hasattr(self, 'confirm_input'):
                self.confirm_input.clear()
            self.error_label.hide()
            self.login_success.emit()
            
        except ValueError as e:
            self.show_error(str(e))
    
    def show_error(self, message: str):
        self.error_label.setText(message)
        self.error_label.show()


class CredentialDialog(QDialog):
    """Dialog for adding/editing credentials."""
    
    def __init__(self, credential: Optional[Credential] = None, parent=None):
        super().__init__(parent)
        self.credential = credential
        self.setWindowTitle("Edit Credential" if credential else "New Credential")
        self.setMinimumWidth(420)
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
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Title
        title = QLabel("Edit Credential" if self.credential else "New Credential")
        title.setStyleSheet(f"""
            color: {theme.colors.foreground};
            font-size: 18px;
            font-weight: 600;
        """)
        layout.addWidget(title)
        
        # Form
        form_layout = QVBoxLayout()
        form_layout.setSpacing(12)
        
        # Domain
        domain_label = QLabel("Domain")
        domain_label.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 12px; font-weight: 500;")
        form_layout.addWidget(domain_label)
        
        self.domain_input = QLineEdit()
        self.domain_input.setPlaceholderText("example.com")
        if self.credential:
            self.domain_input.setText(self.credential.domain)
        self.domain_input.setStyleSheet(self._get_input_style())
        form_layout.addWidget(self.domain_input)
        
        # Username
        username_label = QLabel("Username")
        username_label.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 12px; font-weight: 500;")
        form_layout.addWidget(username_label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("user@email.com")
        if self.credential:
            self.username_input.setText(self.credential.username)
        self.username_input.setStyleSheet(self._get_input_style())
        form_layout.addWidget(self.username_input)
        
        # Password
        password_label = QLabel("Password")
        password_label.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 12px; font-weight: 500;")
        form_layout.addWidget(password_label)
        
        password_row = QHBoxLayout()
        password_row.setSpacing(8)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("••••••••")
        if self.credential:
            self.password_input.setText(self.credential.password)
        self.password_input.setStyleSheet(self._get_input_style())
        password_row.addWidget(self.password_input)
        
        generate_btn = create_icon_button("key", 18, theme.colors.muted_foreground, "Generate password")
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
        generate_btn.setFixedSize(40, 40)
        generate_btn.clicked.connect(self.generate_password)
        password_row.addWidget(generate_btn)
        
        show_btn = create_icon_button("view", 18, theme.colors.muted_foreground, "Show/hide")
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
        show_btn.setFixedSize(40, 40)
        show_btn.clicked.connect(self.toggle_password)
        password_row.addWidget(show_btn)
        
        form_layout.addLayout(password_row)
        
        # Notes
        notes_label = QLabel("Notes (optional)")
        notes_label.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 12px; font-weight: 500;")
        form_layout.addWidget(notes_label)
        
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Additional notes...")
        self.notes_input.setMaximumHeight(80)
        if self.credential and self.credential.notes:
            self.notes_input.setText(self.credential.notes)
        self.notes_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {theme.colors.input};
                border: 1px solid {theme.colors.border};
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                color: {theme.colors.foreground};
            }}
            QTextEdit:focus {{
                border-color: {theme.colors.ring};
            }}
        """)
        form_layout.addWidget(self.notes_input)
        
        # TOTP Secret
        totp_label = QLabel("TOTP Secret (optional)")
        totp_label.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 12px; font-weight: 500;")
        form_layout.addWidget(totp_label)
        
        totp_hint = QLabel("Enter the base32 secret key from your authenticator app setup")
        totp_hint.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 10px;")
        totp_hint.setWordWrap(True)
        form_layout.addWidget(totp_hint)
        
        totp_row = QHBoxLayout()
        totp_row.setSpacing(8)
        
        self.totp_input = QLineEdit()
        self.totp_input.setPlaceholderText("e.g., JBSWY3DPEHPK3PXP")
        if self.credential and self.credential.totp_secret:
            self.totp_input.setText(self.credential.totp_secret)
        self.totp_input.setStyleSheet(self._get_input_style())
        self.totp_input.textChanged.connect(self._validate_totp_input)
        totp_row.addWidget(self.totp_input)
        
        # Clear TOTP button (only for editing existing credentials with TOTP)
        if self.credential and self.credential.totp_secret:
            clear_totp_btn = create_icon_button("close", 18, theme.colors.muted_foreground, "Clear TOTP")
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
            clear_totp_btn.setFixedSize(40, 40)
            clear_totp_btn.clicked.connect(self._clear_totp)
            totp_row.addWidget(clear_totp_btn)
        
        form_layout.addLayout(totp_row)
        
        # TOTP validation label
        self.totp_validation_label = QLabel("")
        self.totp_validation_label.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 11px;")
        form_layout.addWidget(self.totp_validation_label)
        
        # Backup 2FA Codes
        backup_label = QLabel("Backup 2FA Codes (optional)")
        backup_label.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 12px; font-weight: 500;")
        form_layout.addWidget(backup_label)
        
        backup_hint = QLabel("Enter your recovery/backup codes for two-factor authentication")
        backup_hint.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 10px;")
        backup_hint.setWordWrap(True)
        form_layout.addWidget(backup_hint)
        
        backup_row = QHBoxLayout()
        backup_row.setSpacing(8)
        
        self.backup_input = QLineEdit()
        self.backup_input.setPlaceholderText("e.g., XXXX-XXXX-XXXX or recovery code list")
        self.backup_input.setEchoMode(QLineEdit.Password)
        if self.credential and self.credential.backup_codes:
            self.backup_input.setText(self.credential.backup_codes)
        self.backup_input.setStyleSheet(self._get_input_style())
        backup_row.addWidget(self.backup_input)
        
        # Toggle visibility button for backup codes
        backup_toggle_btn = create_icon_button("view", 18, theme.colors.muted_foreground, "Show/hide")
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
        backup_toggle_btn.setFixedSize(40, 40)
        backup_toggle_btn.clicked.connect(self._toggle_backup_visibility)
        backup_row.addWidget(backup_toggle_btn)
        
        # Clear backup codes button (only for editing existing credentials with backup)
        if self.credential and self.credential.backup_codes:
            clear_backup_btn = create_icon_button("close", 18, theme.colors.muted_foreground, "Clear Backup")
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
            clear_backup_btn.setFixedSize(40, 40)
            clear_backup_btn.clicked.connect(self._clear_backup)
            backup_row.addWidget(clear_backup_btn)
        
        form_layout.addLayout(backup_row)
        
        layout.addLayout(form_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.colors.secondary};
                color: {theme.colors.secondary_foreground};
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {theme.colors.accent};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.colors.primary};
                color: {theme.colors.primary_foreground};
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {theme.colors.ring};
            }}
        """)
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
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
        """Validate the TOTP secret input and show feedback."""
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
        """Clear the TOTP secret field."""
        self.totp_input.clear()
        self._totp_cleared = True
        self.totp_validation_label.setText("TOTP will be removed when saved")
        self.totp_validation_label.setStyleSheet(f"color: #f97316; font-size: 11px;")
    
    def _toggle_backup_visibility(self):
        """Toggle backup codes input visibility."""
        if self.backup_input.echoMode() == QLineEdit.Password:
            self.backup_input.setEchoMode(QLineEdit.Normal)
        else:
            self.backup_input.setEchoMode(QLineEdit.Password)
    
    def _clear_backup(self):
        """Clear the backup codes field."""
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



class FolderDialog(QDialog):
    """Custom dialog for creating/renaming folders."""
    
    
    def __init__(self, parent=None, title="Create New Folder", current_name=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(440, 320)
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
        
        # Title
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"font-size: 20px; font-weight: 600; color: #ffffff;")
        layout.addWidget(lbl_title)
        
        # Form layout
        form = QVBoxLayout()
        form.setSpacing(16)
        
        # Folder Name Field
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
        
        # Vault Selection Field (Dropdown)
        vault_group = QVBoxLayout()
        vault_group.setSpacing(8)
        lbl_vault = QLabel("Select Vault")
        lbl_vault.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 13px; font-weight: 500;")
        vault_group.addWidget(lbl_vault)
        
        from PySide6.QtWidgets import QComboBox
        self.vault_combo = QComboBox()
        self.vault_combo.addItems(["Personal"]) # Currently only Personal supported in UI logic
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
                image: url({get_icon_path("chevron-down").replace('\\', '/')});
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
        
        # Buttons
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
            self.accept()
        else:
            self.input.setFocus()


class Sidebar(QFrame):
    """Left sidebar with categories."""
    
    category_changed = Signal(str)
    extension_clicked = Signal()
    lock_clicked = Signal()
    toggle_sidebar = Signal()  # Signal to toggle sidebar visibility
    add_folder_clicked = Signal()  # Signal to add a new folder
    folder_selected = Signal(int)  # Signal when a folder is selected (emits folder_id)
    folder_edit_requested = Signal(object)  # Signal to edit a folder (emits Folder)
    folder_delete_requested = Signal(object)  # Signal to delete a folder (emits Folder)
    settings_clicked = Signal()  # Signal for settings button
    google_drive_clicked = Signal()  # Signal for Google Drive button
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SidebarFrame")
        self.setFixedWidth(200)
        self.current_category = "all"
        self.folders = []  # List of Folder objects
        self.folder_buttons = []  # List of folder buttons
        self.setup_ui()
    
    def setup_ui(self):
        theme = get_theme()
        
        # Configure frame
        self.setFrameShape(QFrame.NoFrame)
        
        # Force background color - use specific ID selector
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
        
        # ===== HEADER =====
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(8, 0, 4, 16)
        header_layout.setSpacing(8)
        
        # Logo icon
        logo_icon = QLabel()
        logo_icon.setPixmap(load_svg_icon("shield", 24, theme.colors.primary))
        header_layout.addWidget(logo_icon, alignment=Qt.AlignVCenter)
        
        # App name
        app_name = QLabel("VaultKeeper")
        app_name.setStyleSheet(f"""
            color: {theme.colors.sidebar_foreground};
            font-size: 16px;
            font-weight: 600;
        """)
        header_layout.addWidget(app_name, alignment=Qt.AlignVCenter)
        
        header_layout.addStretch()
        
        # Toggle sidebar button - aligned with text
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
        
        # ===== MAIN BUTTONS =====
        self.btn_all = SidebarButton("grid", "All Items")
        self.btn_all.setChecked(True)
        self.btn_all.clicked.connect(lambda: self.set_category("all"))
        self.layout.addWidget(self.btn_all)
        
        self.btn_favorites = SidebarButton("star", "Favorites")
        self.btn_favorites.clicked.connect(lambda: self.set_category("favorites"))
        self.layout.addWidget(self.btn_favorites)
        
        # ===== VAULTS SECTION with add button =====
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
        
        # Add folder button - aligned with text
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
        
        # Container for folder buttons (will be populated dynamically)
        self.folders_container = QWidget()
        self.folders_container.setStyleSheet("background-color: transparent;")
        self.folders_layout = QVBoxLayout(self.folders_container)
        self.folders_layout.setContentsMargins(0, 0, 0, 0)
        self.folders_layout.setSpacing(2)
        self.layout.addWidget(self.folders_container)
        
        # Default vaults
        # Personal - acting as a header
        self.btn_personal = SidebarButton("person", "Personal", font_size=16, is_selectable=False)
        self.folders_layout.addWidget(self.btn_personal)
        
        # Container specifically for personal folders (sub-items)
        self.personal_folders_container = QWidget()
        self.personal_folders_container.setStyleSheet("background-color: transparent;")
        self.personal_folders_layout = QVBoxLayout(self.personal_folders_container)
        self.personal_folders_layout.setContentsMargins(0, 0, 0, 0)
        self.personal_folders_layout.setSpacing(2)
        self.folders_layout.addWidget(self.personal_folders_container)
        
        # Team Vault - acting as a header
        self.btn_team = SidebarButton("team", "Team Vault", font_size=16, is_selectable=False)
        self.folders_layout.addWidget(self.btn_team)
        
        # Professional - acting as a header
        self.btn_professional = SidebarButton("work", "Professional", font_size=16, is_selectable=False)
        self.folders_layout.addWidget(self.btn_professional)
        
        self.static_buttons = [
            self.btn_all, self.btn_favorites
        ]
        
        # Initial empty state for personal folders
        self.personal_folders_container.setVisible(False)
        
        self.layout.addStretch()
        
        # ===== BOTTOM SECTION - Settings and Google Drive buttons =====
        bottom_layout = QVBoxLayout()
        bottom_layout.setContentsMargins(4, 8, 4, 4)
        bottom_layout.setSpacing(4)
        
        theme = get_theme()

        # Sync status indicator (hidden by default)
        self.sync_status_widget = QWidget()
        self.sync_status_widget.setVisible(False)
        sync_status_layout = QHBoxLayout(self.sync_status_widget)
        sync_status_layout.setContentsMargins(12, 8, 12, 8)
        sync_status_layout.setSpacing(8)
        
        # Sync icon/spinner
        self.sync_icon_label = QLabel()
        self.sync_icon_label.setPixmap(load_svg_icon("cloud_sync", 14, "#3b82f6"))
        self.sync_icon_label.setFixedSize(16, 16)
        sync_status_layout.addWidget(self.sync_icon_label)
        
        # Sync text
        self.sync_status_label = QLabel("Syncing...")
        self.sync_status_label.setStyleSheet("""
            color: #3b82f6;
            font-size: 12px;
            font-weight: 500;
        """)
        sync_status_layout.addWidget(self.sync_status_label)
        sync_status_layout.addStretch()
        
        bottom_layout.addWidget(self.sync_status_widget)

        # Google Drive sync button
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
        
        # Settings button
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
        
        self.layout.addLayout(bottom_layout)
        
        # Register for Google Drive sync callbacks
        self._setup_gdrive_callbacks()
    
    def _setup_gdrive_callbacks(self):
        """Setup callbacks for Google Drive sync status."""
        from app.core.gdrive import GoogleDriveManager
        
        GoogleDriveManager.on_sync_start(self._on_sync_start)
        GoogleDriveManager.on_sync_end(self._on_sync_end)
    
    def _on_sync_start(self):
        """Handle sync start - show indicator."""
        print("[UI] Sync start signal received")
        from PySide6.QtCore import QTimer
        # Use QTimer to ensure this runs on the main thread
        QTimer.singleShot(0, self._show_sync_indicator)
    
    def _on_sync_end(self, success: bool, error: str = None):
        """Handle sync end - update and hide indicator."""
        print(f"[UI] Sync end signal received. Success: {success}")
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, lambda: self._hide_sync_indicator(success, error))
    
    def _show_sync_indicator(self):
        """Show the sync indicator."""
        print("[UI] Showing sync indicator widget")
        self.sync_status_label.setText("Syncing...")
        self.sync_status_label.setStyleSheet("""
            color: #3b82f6;
            font-size: 12px;
            font-weight: 500;
        """)
        self.sync_status_widget.setVisible(True)
        # Force update layout
        self.sync_status_widget.update()
        self.update()
    
    def _hide_sync_indicator(self, success: bool, error: str = None):
        """Hide the sync indicator after showing result."""
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
        
        # Hide after 2 seconds
        from PySide6.QtCore import QTimer
        QTimer.singleShot(2000, lambda: self.sync_status_widget.setVisible(False))
    
    def update_gdrive_status(self):
        """Update Google Drive button based on connection status."""
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
        """Update the list of folders in the sidebar."""
        self.folders = folders
        
        # Clear existing dynamic folder buttons
        for btn in self.folder_buttons:
            btn.deleteLater()
        self.folder_buttons.clear()
        
        theme = get_theme()
        
        # Show container only if there are folders
        self.personal_folders_container.setVisible(bool(folders))
        
        # Add buttons for each folder
        for folder in folders:
            # Indented sub-items (padding_left=32)
            btn = SidebarButton("folder", folder.name, font_size=13, padding_left=32)
            btn.clicked.connect(lambda checked, f=folder: self.on_folder_clicked(f))
            
            # Enable context menu for folder buttons
            btn.setContextMenuPolicy(Qt.CustomContextMenu)
            btn.customContextMenuRequested.connect(
                lambda pos, b=btn, f=folder: self._show_folder_context_menu(b, f, pos)
            )
            
            self.personal_folders_layout.addWidget(btn)
            self.folder_buttons.append(btn)
    
    def _show_folder_context_menu(self, button, folder: Folder, pos):
        """Show context menu for a folder button."""
        theme = get_theme()
        menu = QMenu(self)
        
        # Style the menu
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
        
        # Edit action
        edit_action = menu.addAction("Rename Folder")
        edit_action.setIcon(QIcon(load_svg_icon("edit", 16, theme.colors.foreground)))
        
        menu.addSeparator()
        
        # Delete action
        delete_action = menu.addAction("Delete Folder")
        delete_action.setIcon(QIcon(load_svg_icon("delete", 16, theme.colors.destructive)))
        
        action = menu.exec_(button.mapToGlobal(pos))
        
        if action == edit_action:
            self.folder_edit_requested.emit(folder)
        elif action == delete_action:
            self.folder_delete_requested.emit(folder)
    
    def on_folder_clicked(self, folder: Folder):
        """Handle folder button click."""
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
        }
        if category in btn_map:
            btn_map[category].setChecked(True)
        elif category.startswith("folder_"):
            # Find and check the folder button
            folder_id = int(category.split("_")[1])
            for i, folder in enumerate(self.folders):
                if folder.id == folder_id and i < len(self.folder_buttons):
                    self.folder_buttons[i].setChecked(True)
                    break
        
        self.category_changed.emit(category)


class CredentialsList(QWidget):
    """Center panel with credentials list."""
    
    credential_selected = Signal(object)
    add_clicked = Signal()
    toggle_sidebar_requested = Signal()  # Signal to toggle sidebar
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.credentials = []
        self.card_map = {}  # Map credential.id -> CredentialCard
        self.current_category = "all"
        self.current_folder_id = None
        self.search_query = ""
        self.setup_ui()
    
    def setup_ui(self):
        theme = get_theme()
        
        # Use list_background color for this panel
        self.setStyleSheet(f"background-color: {theme.colors.list_background};")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # ===== HEADER =====
        header = QFrame()
        header.setStyleSheet(f"background-color: {theme.colors.list_background};")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(12, 12, 16, 12)
        header_layout.setSpacing(12)
        
        # Search row with toggle button
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)
        
        # Toggle sidebar button (hidden by default, shown when sidebar is collapsed)
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
        self.toggle_sidebar_btn.setVisible(False)  # Hidden by default
        search_layout.addWidget(self.toggle_sidebar_btn)
        
        # Search input
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
        
        # Category filter
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
        
        sort_btn = create_icon_button("list", 14, theme.colors.muted_foreground)
        sort_btn.setFixedSize(24, 24)
        sort_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors.accent};
            }}
        """)
        filter_layout.addWidget(sort_btn, alignment=Qt.AlignVCenter)
        
        header_layout.addLayout(filter_layout)
        
        layout.addWidget(header)
        
        # ===== SCROLLABLE LIST =====
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
        self.credentials = credentials
        
        # Optimize updates by reusing existing widgets
        new_ids = {c.id for c in credentials}
        existing_ids = set(self.card_map.keys())
        
        self.list_container.setUpdatesEnabled(False)
        try:
            # Remove deleted credentials
            for cid in existing_ids - new_ids:
                if cid in self.card_map:
                    card = self.card_map.pop(cid)
                    self.list_layout.removeWidget(card)
                    card.deleteLater()
            
            # Add new or update existing credentials
            # Note: We insert before the stretch item (last item)
            spacer_index = self.list_layout.count() - 1
            
            for cred in credentials:
                if cred.id in self.card_map:
                    # Update existing card
                    self.card_map[cred.id].update_credential(cred)
                else:
                    # Create new card
                    card = CredentialCard(cred)
                    card.clicked.connect(self.on_card_clicked)
                    self.list_layout.insertWidget(spacer_index, card)
                    self.card_map[cred.id] = card
                    
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
        """Show/hide cards based on current filters."""
        self.list_container.setUpdatesEnabled(False)
        try:
            for card in self.card_map.values():
                cred = card.credential
                visible = True
                
                # Category filter logic
                if self.current_category == "favorites":
                    if not cred.is_favorite:
                        visible = False
                elif self.current_category == "folder":
                    if cred.folder_id != self.current_folder_id:
                        visible = False
                # "all" category shows everything
                
                # Search filter logic (AND)
                if visible and self.search_query:
                    if (self.search_query not in cred.domain.lower() and 
                        self.search_query not in cred.username.lower()):
                        visible = False
                        
                card.setVisible(visible)
        finally:
            self.list_container.setUpdatesEnabled(True)
    
    def on_card_clicked(self, credential: Credential):
        for card in self.card_map.values():
            card.set_selected(card.credential.id == credential.id)
        self.credential_selected.emit(credential)
    
    def set_sidebar_toggle_visible(self, visible: bool):
        """Show or hide the sidebar toggle button."""
        self.toggle_sidebar_btn.setVisible(visible)


class VaultWidget(QWidget):
    """Main vault interface with three-panel layout."""
    
    lock_requested = Signal()
    
    def __init__(self, vault: VaultManager, parent=None):
        super().__init__(parent)
        self.vault = vault
        self.sidebar_visible = True
        self.current_category = "all"
        self.setup_ui()
        
        # Defer loading to allow UI to render first
        from PySide6.QtCore import QTimer
        QTimer.singleShot(50, self.load_data)
        
    def load_data(self):
        """Load initial data."""
        self.load_folders()
        self.load_credentials()
    
    def setup_ui(self):
        theme = get_theme()
        
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.category_changed.connect(self.on_category_changed)
        self.sidebar.toggle_sidebar.connect(self.toggle_sidebar)
        self.sidebar.add_folder_clicked.connect(self.add_folder)
        # We don't need folder_selected as category_changed handles it via "folder_ID"
        self.sidebar.folder_edit_requested.connect(self.on_folder_edit)
        self.sidebar.folder_delete_requested.connect(self.on_folder_delete)
        self.sidebar.settings_clicked.connect(self.on_settings_clicked)
        self.sidebar.google_drive_clicked.connect(self.on_google_drive_clicked)
        self.main_layout.addWidget(self.sidebar)
        
        # Center - credentials list
        self.credentials_list = CredentialsList()
        self.credentials_list.credential_selected.connect(self.on_credential_selected)
        self.credentials_list.add_clicked.connect(self.add_credential)
        self.credentials_list.toggle_sidebar_requested.connect(self.toggle_sidebar)
        self.credentials_list.setMinimumWidth(280)
        self.credentials_list.setMaximumWidth(350)
        self.main_layout.addWidget(self.credentials_list)
        
        # Right - details
        self.detail_panel = DetailPanel()
        self.detail_panel.edit_requested.connect(self.edit_credential)
        self.detail_panel.delete_requested.connect(self.delete_credential)
        self.detail_panel.favorite_toggled.connect(self.toggle_favorite)
        self.detail_panel.folder_move_requested.connect(self.move_credential_to_folder)
        self.detail_panel.status_message.connect(self.show_status)
        self.main_layout.addWidget(self.detail_panel, stretch=1)
    
    def toggle_sidebar(self):
        """Toggle sidebar visibility."""
        self.sidebar_visible = not self.sidebar_visible
        self.sidebar.setVisible(self.sidebar_visible)
        self.credentials_list.set_sidebar_toggle_visible(not self.sidebar_visible)
    
    def load_folders(self):
        """Load and display folders in the sidebar."""
        try:
            folders = self.vault.get_all_folders()
            self.sidebar.set_folders(folders)
            # Update available folders in detail panel for move menu
            self.detail_panel.set_available_folders(folders)
        except Exception as e:
            print(f"Error loading folders: {e}")
    
    def load_credentials(self):
        """Load all credentials and update list."""
        try:
            # We load ALL credentials now and let the list handle filtering
            # This improves performance when switching categories
            credentials = self.vault.get_all_credentials()
            self.credentials_list.set_credentials(credentials)
        except Exception as e:
            print(f"Error loading credentials: {e}")
    
    def on_category_changed(self, category: str):
        """Handle category change from sidebar."""
        self.current_category = category
        
        # Update list filter instead of reloading everything
        if category == "all":
            self.credentials_list.set_filter("all")
        elif category == "favorites":
            self.credentials_list.set_filter("favorites")
        elif category.startswith("folder_"):
            try:
                folder_id = int(category.split("_")[1])
                self.credentials_list.set_filter("folder", folder_id)
            except (IndexError, ValueError):
                self.credentials_list.set_filter("all")
        
        # Clear the detail panel when changing categories
        self.detail_panel.show_empty_state()
    
    def on_credential_selected(self, credential: Credential):
        self.detail_panel.show_credential(credential)
    
    def add_folder(self):
        """Show dialog to create a new folder."""
        dialog = FolderDialog(self, "Create Folder")
        if dialog.exec():
            name = dialog.folder_name
            if name:
                try:
                    self.vault.create_folder(name)
                    # Force immediate reload of folders
                    self.load_folders()
                    # Show the sidebar button container
                    self.sidebar.personal_folders_container.setVisible(True)
                    self.show_status(f"Folder '{name}' created")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to create folder: {e}")
    
    def on_folder_edit(self, folder: Folder):
        """Handle folder edit request."""
        dialog = FolderDialog(self, "Rename Folder", folder.name)
        if dialog.exec():
            name = dialog.folder_name
            if name and name != folder.name:
                try:
                    if self.vault.update_folder(folder.id, name):
                        self.load_folders()
                        self.show_status(f"Folder renamed to '{name}'")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to rename folder: {e}")
    
    def on_folder_delete(self, folder: Folder):
        """Handle folder delete request."""
        reply = QMessageBox.question(
            self,
            "Delete Folder",
            f"Are you sure you want to delete folder '{folder.name}'?\nCredentials inside will not be deleted but will be moved to 'All Items'.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if self.vault.delete_folder(folder.id):
                    self.load_folders()
                    self.show_status(f"Folder '{folder.name}' deleted")
                    # If this folder was selected, go back to all items
                    if self.current_category == f"folder_{folder.id}":
                        self.set_category("all")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete folder: {e}")

    def move_credential_to_folder(self, credential, folder_id):
        """Move a credential to a different folder."""
        try:
            if self.vault.set_credential_folder(credential.id, folder_id):
                # Update UI
                updated_cred = self.vault.get_credential(credential.id)
                if updated_cred:
                    self.detail_panel.show_credential(updated_cred)
                    self.load_credentials()  # Reload list to reflect changes
                    
                    if folder_id is None:
                        self.show_status("Removed from folder")
                    else:
                        folder_name = next((f.name for f in self.vault.get_all_folders() if f.id == folder_id), "folder")
                        self.show_status(f"Moved to {folder_name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to move credential: {e}")
    
    def toggle_favorite(self, credential: Credential):
        """Toggle favorite status of a credential."""
        try:
            new_status = self.vault.toggle_favorite(credential.id)
            # Reload the credential to show updated status
            updated = self.vault.get_credential(credential.id)
            if updated:
                self.detail_panel.show_credential(updated)
            # Reload the list if we're in favorites view
            if self.current_category == "favorites":
                self.load_credentials()
        except Exception as e:
            print(f"Error toggling favorite: {e}")
    
    def on_settings_clicked(self):
        """Handle settings button click."""
        dialog = SettingsDialog(self)
        dialog.exec()
    
    def on_google_drive_clicked(self):
        """Handle Google Drive sync button click."""
        dialog = GoogleDriveDialog(self)
        dialog.connection_successful.connect(self._on_gdrive_connected)
        dialog.exec()
    
    def _on_gdrive_connected(self):
        """Handle successful Google Drive connection."""
        self.show_status("Connected to Google Drive")
    
    def add_credential(self):
        dialog = CredentialDialog(parent=self)
        if dialog.exec():
            data = dialog.get_data()
            if data['domain'] and data['username'] and data['password']:
                # Remove keys that are only valid for update_credential
                add_data = {k: v for k, v in data.items() if k not in ('clear_totp', 'clear_backup')}
                self.vault.add_credential(**add_data)
                self.load_credentials()
    
    def edit_credential(self, credential: Credential):
        dialog = CredentialDialog(credential, parent=self)
        if dialog.exec():
            data = dialog.get_data()
            self.vault.update_credential(credential.id, **data)
            self.load_credentials()
            updated = next((c for c in self.vault.get_all_credentials() if c.id == credential.id), None)
            if updated:
                self.detail_panel.show_credential(updated)
    
    def delete_credential(self, credential: Credential):
        reply = QMessageBox.question(
            self, 
            "Confirm Delete", 
            f"Are you sure you want to delete the credential for\n\n{credential.domain}?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.vault.delete_credential(credential.id)
            self.load_credentials()
            self.detail_panel.show_empty_state()
    
    def show_status(self, message: str):
        # Could show a toast notification here
        pass
    
    def setup_extension(self):
        try:
            from ..native.installer import NativeHostInstaller
            
            installer = NativeHostInstaller()
            installer.create_wrapper_script()
            results = installer.install_all()
            
            installed = [browser.title() for browser, success, msg in results if success]
            
            if installed:
                QMessageBox.information(
                    self, 
                    "Extension Configured",
                    f"Native Host installed for:\n\n• " + "\n• ".join(installed)
                )
            else:
                QMessageBox.warning(
                    self,
                    "No Browser Found",
                    "No compatible browser was found."
                )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to configure:\n\n{e}")


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.auth = AuthManager()
        self.vault = VaultManager(auth=self.auth)
        
        self.setWindowTitle("VaultKeeper")
        self.setMinimumSize(1000, 700)
        self.setup_ui()
        self.setup_auto_lock()
    
    def setup_ui(self):
        self.setStyleSheet(get_stylesheet())
        
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        self.login_widget = LoginWidget(self.auth)
        self.login_widget.login_success.connect(self.show_vault)
        self.stack.addWidget(self.login_widget)
        
        self.vault_widget = None
    
    def setup_auto_lock(self):
        self.lock_timer = QTimer(self)
        self.lock_timer.timeout.connect(self.check_auto_lock)
        # Check every 10 seconds to be responsive enough
        self.lock_timer.start(10000) 
        
        # Initialize with config
        self.update_auto_lock()
        
        # Listen for changes
        get_config().settings_changed.connect(self.on_settings_changed)
    
    def on_settings_changed(self, key, value):
        if key == "general/auto_lock_timeout":
            self.update_auto_lock()
            
    def update_auto_lock(self):
        timeout = get_config().get_auto_lock_timeout()
        self.auth.set_timeout(timeout)
    
    def check_auto_lock(self):
        if self.auth.check_timeout():
            self.show_login()
    
    def show_vault(self):
        if self.vault_widget:
            self.stack.removeWidget(self.vault_widget)
        
        self.vault.crypto.derive_key(self.auth.master_password)
        self.vault_widget = VaultWidget(self.vault)
        self.vault_widget.lock_requested.connect(self.lock_vault)
        self.stack.addWidget(self.vault_widget)
        self.stack.setCurrentWidget(self.vault_widget)
    
    def show_login(self):
        self.stack.setCurrentWidget(self.login_widget)
    
    def lock_vault(self):
        self.vault.lock()
        self.show_login()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("VaultKeeper")
    app.setOrganizationName("VaultKeeper")
    app.setOrganizationDomain("vaultkeeper.com")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
