"""
VaultKeeper - Settings UI Components
Shared components for settings pages
"""

from PySide6.QtWidgets import (
    QCheckBox, QPushButton, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from PySide6.QtCore import Qt, QSize, QRect
from PySide6.QtGui import QIcon, QPainter, QColor, QPaintEvent, QBrush

from ..theme import get_theme
from ..ui_utils import load_svg_icon


class ToggleSwitch(QCheckBox):
    """A modern iOS-style toggle switch."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(44, 24)
        self.setCursor(Qt.PointingHandCursor)
        self.stateChanged.connect(self.update)
        
    def hitButton(self, pos):
        return self.contentsRect().contains(pos)
        
    def paintEvent(self, e: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        theme = get_theme()
        active_color = QColor("#3b82f6") 
        inactive_color = QColor(theme.colors.muted if hasattr(theme.colors, 'muted') else "#3f3f46")
        handle_color = QColor("#ffffff")
        
        # Track
        rect = self.contentsRect()
        if self.isChecked():
            painter.setBrush(QBrush(active_color))
            painter.setPen(Qt.NoPen)
        else:
            painter.setBrush(QBrush(inactive_color))
            painter.setPen(Qt.NoPen)
            
        painter.drawRoundedRect(rect, 12, 12)
        
        # Handle
        handle_x = 22 if self.isChecked() else 2
        handle_rect = QRect(handle_x, 2, 20, 20)
        painter.setBrush(QBrush(handle_color))
        painter.drawEllipse(handle_rect)
        painter.end()


class SettingsSidebarButton(QPushButton):
    """Sidebar navigation button."""
    
    def __init__(self, icon_name: str, text: str, parent=None):
        super().__init__(parent)
        self.icon_name = icon_name
        self.setText(f"  {text}")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(40)
        self.update_style()
        
    def update_style(self):
        theme = get_theme()
        
        if self.isChecked():
            bg_color = "rgba(59, 130, 246, 0.2)"
            text_color = "#60a5fa"
            icon_color = "#60a5fa"
        else:
            bg_color = "transparent"
            text_color = theme.colors.sidebar_muted
            icon_color = theme.colors.sidebar_muted
            
        self.setIcon(QIcon(load_svg_icon(self.icon_name, 16, icon_color)))
        self.setIconSize(QSize(16, 16))
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                border: none;
                border-radius: 6px;
                padding: 12px;
                text-align: left;
                font-size: 14px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {theme.colors.sidebar_accent};
            }}
        """)


def create_toggle_setting(title: str, subtitle: str, checked: bool) -> tuple[QWidget, ToggleSwitch]:
    """Create a toggle setting widget with title, subtitle and toggle switch."""
    widget = QWidget()
    layout = QHBoxLayout(widget)
    layout.setContentsMargins(0, 12, 0, 12)
    
    theme = get_theme()
    
    # Labels
    text_layout = QVBoxLayout()
    text_layout.setSpacing(4)
    
    label_title = QLabel(title)
    label_title.setStyleSheet(f"""
        color: {theme.colors.foreground};
        font-size: 14px;
        font-weight: 500;
        border: none;
        background: transparent;
    """)
    text_layout.addWidget(label_title)
    
    label_sub = QLabel(subtitle)
    label_sub.setStyleSheet(f"""
        color: {theme.colors.muted_foreground};
        font-size: 12px;
        border: none;
        background: transparent;
    """)
    text_layout.addWidget(label_sub)
    
    layout.addLayout(text_layout)
    
    toggle = ToggleSwitch()
    toggle.setChecked(checked)
    layout.addWidget(toggle)
    
    return widget, toggle


def create_separator() -> QFrame:
    """Create a horizontal separator line."""
    sep = QFrame()
    sep.setFixedHeight(1)
    theme = get_theme()
    sep.setStyleSheet(f"background-color: {theme.colors.border};")
    return sep
