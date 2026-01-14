"""
UI Utilities and helpers.
"""
import os
from pathlib import Path
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QPainter, QIcon
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QPushButton

from .theme import get_theme

# Icons directory
ICONS_DIR = Path(__file__).parent / "icons"

def get_icon_path(name: str) -> str:
    """Get the path to an icon file."""
    return str(ICONS_DIR / f"{name}.svg")


def load_svg_icon(name: str, size: int = 20, color: str = None) -> QPixmap:
    """Load an SVG icon and optionally colorize it."""
    path = get_icon_path(name)
    if not os.path.exists(path):
        # Return empty pixmap if icon doesn't exist
        return QPixmap(size, size)
    
    # Read SVG content
    with open(path, 'r') as f:
        svg_content = f.read()
    
    # Replace currentColor with specified color
    if color:
        svg_content = svg_content.replace('currentColor', color)
    else:
        theme = get_theme()
        svg_content = svg_content.replace('currentColor', theme.colors.foreground)
    
    # Render SVG to pixmap
    renderer = QSvgRenderer(svg_content.encode())
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    
    return pixmap


def create_icon_button(icon_name: str, size: int = 20, color: str = None, tooltip: str = "") -> QPushButton:
    """Create a button with an SVG icon."""
    btn = QPushButton()
    btn.setIcon(QIcon(load_svg_icon(icon_name, size, color)))
    btn.setIconSize(QSize(size, size))
    btn.setFixedSize(size + 12, size + 12)
    btn.setCursor(Qt.PointingHandCursor)
    if tooltip:
        btn.setToolTip(tooltip)
    return btn
