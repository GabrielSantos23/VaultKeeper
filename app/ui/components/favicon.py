
from PySide6.QtWidgets import QLabel

from PySide6.QtCore import Qt, QUrl

from PySide6.QtGui import QPixmap, QImage

from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from typing import Optional, Dict

from app.ui.theme import get_theme

_favicon_cache: Dict[str, QPixmap] = {}

_network_manager: Optional[QNetworkAccessManager] = None

def get_network_manager() -> QNetworkAccessManager:

    global _network_manager

    if _network_manager is None:

        _network_manager = QNetworkAccessManager()

    return _network_manager

CREDENTIAL_COLORS = [

    "#22c55e",

    "#3b82f6",

    "#8b5cf6",

    "#ec4899",

    "#f97316",

    "#14b8a6",

    "#eab308",

    "#ef4444",

]

def get_credential_color(text: str) -> str:

    if not text:

        return CREDENTIAL_COLORS[0]

    hash_val = sum(ord(c) for c in text)

    return CREDENTIAL_COLORS[hash_val % len(CREDENTIAL_COLORS)]

class FaviconLabel(QLabel):

    def __init__(self, domain: str, size: int = 40, parent=None):

        super().__init__(parent)

        self.domain = domain

        self.icon_size = size

        self.setFixedSize(size, size)

        self.setAlignment(Qt.AlignCenter)

        self._show_fallback()

        self._load_favicon()

    def _show_fallback(self):

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

        global _favicon_cache

        if self.domain in _favicon_cache:

            self._set_favicon(_favicon_cache[self.domain])

            return

        clean_domain = self.domain.replace("https://", "").replace("http://", "").split("/")[0]

        favicon_url = f"https://www.google.com/s2/favicons?domain={clean_domain}&sz=64"

        manager = get_network_manager()

        request = QNetworkRequest(QUrl(favicon_url))

        request.setAttribute(QNetworkRequest.RedirectPolicyAttribute, QNetworkRequest.NoLessSafeRedirectPolicy)

        reply = manager.get(request)

        reply.finished.connect(lambda: self._on_favicon_loaded(reply))

    def _on_favicon_loaded(self, reply: QNetworkReply):

        global _favicon_cache

        if reply.error() == QNetworkReply.NoError:

            data = reply.readAll()

            image = QImage()

            if image.loadFromData(data):

                if image.width() >= 16 and image.height() >= 16:

                    pixmap = QPixmap.fromImage(image)

                    scaled = pixmap.scaled(

                        self.icon_size, self.icon_size,

                        Qt.KeepAspectRatio,

                        Qt.SmoothTransformation

                    )

                    _favicon_cache[self.domain] = scaled

                    self._set_favicon(scaled)

        reply.deleteLater()

    def _set_favicon(self, pixmap: QPixmap):

        self.setText("")

        self.setPixmap(pixmap)

        radius = int(self.icon_size * 0.2)

        self.setStyleSheet(f"""
            background-color: transparent;
            border-radius: {radius}px;
        """)
