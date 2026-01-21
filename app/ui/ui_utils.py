
import os

from pathlib import Path

from datetime import datetime, timezone

from PySide6.QtCore import Qt, QSize

from PySide6.QtGui import QPixmap, QPainter, QIcon

from PySide6.QtSvg import QSvgRenderer

from PySide6.QtWidgets import QPushButton

from .theme import get_theme


def format_timestamp(timestamp_str: str) -> str:
    """Convert a UTC timestamp string from SQLite to local timezone and format it nicely."""
    if not timestamp_str:
        return ""
    
    try:
        # SQLite CURRENT_TIMESTAMP format: 'YYYY-MM-DD HH:MM:SS'
        # Parse as UTC
        utc_dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
        
        # Convert to local timezone
        local_dt = utc_dt.astimezone()
        
        # Format nicely
        return local_dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        # If parsing fails, return the original string
        return timestamp_str

ICONS_DIR = Path(__file__).parent / "icons"

def get_icon_path(name: str) -> str:

    return str(ICONS_DIR / f"{name}.svg")

_icon_cache = {}

def load_svg_icon(name: str, size: int = 20, color: str = None) -> QPixmap:
    cache_key = (name, size, color)
    if cache_key in _icon_cache:
        return _icon_cache[cache_key]

    if os.path.isabs(name) or (os.path.sep in name) or ('/' in name):
        path = name
    else:
        path = get_icon_path(name)

    if not os.path.exists(path):
        return QPixmap(size, size)

    with open(path, 'r') as f:
        svg_content = f.read()

    if color:
        svg_content = svg_content.replace('currentColor', color)
    else:
        theme = get_theme()
        svg_content = svg_content.replace('currentColor', theme.colors.foreground)

    renderer = QSvgRenderer(svg_content.encode())
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    
    _icon_cache[cache_key] = pixmap
    return pixmap

def create_icon_button(icon_name: str, size: int = 20, color: str = None, tooltip: str = "") -> QPushButton:

    btn = QPushButton()

    btn.setIcon(QIcon(load_svg_icon(icon_name, size, color)))

    btn.setIconSize(QSize(size, size))

    btn.setFixedSize(size + 12, size + 12)

    btn.setCursor(Qt.PointingHandCursor)

    if tooltip:

        btn.setToolTip(tooltip)

    return btn
