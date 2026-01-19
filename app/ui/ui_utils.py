
import os

from pathlib import Path

from PySide6.QtCore import Qt, QSize

from PySide6.QtGui import QPixmap, QPainter, QIcon

from PySide6.QtSvg import QSvgRenderer

from PySide6.QtWidgets import QPushButton

from .theme import get_theme

ICONS_DIR = Path(__file__).parent / "icons"

def get_icon_path(name: str) -> str:

    return str(ICONS_DIR / f"{name}.svg")

def load_svg_icon(name: str, size: int = 20, color: str = None) -> QPixmap:

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
