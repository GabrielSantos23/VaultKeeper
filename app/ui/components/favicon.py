from PySide6.QtWidgets import QLabel

from PySide6.QtCore import Qt, QUrl

from PySide6.QtGui import QPixmap, QImage

from typing import Optional, Dict

from app.ui.theme import get_theme

_favicon_cache: Dict[str, QPixmap] = {}

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

from pathlib import Path

ICONS_DIR = Path(__file__).parent.parent / "icons" / "service_icons"

# Inverted mapping from fetch_favicons.py for precise fallback
DOMAIN_TO_NAME = {
    "google.com": "google", "github.com": "github", "gitlab.com": "gitlab", "bitbucket.org": "bitbucket",
    "stackoverflow.com": "stackoverflow", "microsoft.com": "microsoft", "apple.com": "apple", "openai.com": "openai",
    "anthropic.com": "anthropic", "docker.com": "docker", "aws.amazon.com": "aws", "vercel.com": "vercel",
    "netlify.com": "netlify", "cloudflare.com": "cloudflare", "heroku.com": "heroku", "digitalocean.com": "digitalocean",
    "firebase.google.com": "firebase", "supabase.com": "supabase", "postman.com": "postman", "python.org": "python",
    "discord.com": "discord", "facebook.com": "facebook", "instagram.com": "instagram", "twitter.com": "twitter",
    "x.com": "x", "linkedin.com": "linkedin", "reddit.com": "reddit", "whatsapp.com": "whatsapp",
    "telegram.org": "telegram", "slack.com": "slack", "twitch.tv": "twitch", "tiktok.com": "tiktok",
    "pinterest.com": "pinterest", "tumblr.com": "tumblr", "joinmastodon.org": "mastodon", "netflix.com": "netflix",
    "spotify.com": "spotify", "youtube.com": "youtube", "disneyplus.com": "disneyplus", "hbomax.com": "hbomax",
    "primevideo.com": "primevideo", "tv.apple.com": "apple-tv", "store.steampowered.com": "steam",
    "epicgames.com": "epicgames", "roblox.com": "roblox", "crunchyroll.com": "crunchyroll", "nintendo.com": "nintendo",
    "playstation.com": "playstation", "xbox.com": "xbox", "notion.so": "notion", "dropbox.com": "dropbox",
    "trello.com": "trello", "figma.com": "figma", "canva.com": "canva", "adobe.com": "adobe", "zoom.us": "zoom",
    "atlassian.com": "atlassian", "evernote.com": "evernote", "monday.com": "monday", "asana.com": "asana",
    "miro.com": "miro", "linear.app": "linear", "amazon.com.br": "amazon", "ebay.com": "ebay",
    "aliexpress.com": "aliexpress", "mercadolivre.com.br": "mercadolivre", "shopee.com.br": "shopee",
    "magazineluiza.com.br": "magalu", "ifood.com.br": "ifood", "uber.com": "uber", "airbnb.com.br": "airbnb",
    "booking.com": "booking", "paypal.com": "paypal", "stripe.com": "stripe", "binance.com": "binance",
    "coinbase.com": "coinbase", "nubank.com.br": "nubank", "itau.com.br": "itau", "bradesco.com.br": "bradesco",
    "santander.com.br": "santander", "bancointer.com.br": "bancointer", "caixa.gov.br": "caixa", "bb.com.br": "bb",
    "wise.com": "wise", "revolut.com": "revolut", "wikipedia.org": "wikipedia", "medium.com": "medium",
    "quora.com": "quora", "g1.globo.com": "g1", "uol.com.br": "uol", "folha.uol.com.br": "folha",
    "estadao.com.br": "estadao", "nytimes.com": "nytimes", "theverge.com": "theverge", "techcrunch.com": "techcrunch",
    "udemy.com": "udemy", "coursera.org": "coursera", "duolingo.com": "duolingo", "gov.br": "govbr"
}

class FaviconLoader:
    def __init__(self):
        print(f"DEBUG: ICONS_DIR resolved to: {ICONS_DIR}")
        
    def get_icon(self, domain: str) -> Optional[QPixmap]:
        global _favicon_cache
        if domain in _favicon_cache:
            return _favicon_cache[domain]
            
        return self._load_local(domain)

    def _load_local(self, domain: str) -> Optional[QPixmap]:
        if not domain:
            return None
            
        clean = domain.replace("https://", "").replace("http://", "").split("/")[0].lower()
        if clean.startswith("www."):
            clean = clean[4:]
        
        # Determine filename
        filename = DOMAIN_TO_NAME.get(clean)
        
        if not filename:
            # Try simple heuristic: 'google' from 'google.com'
            parts = clean.split('.')
            if len(parts) >= 2:
                # check 'google'
                potential = parts[-2] if parts[-1] in ('com', 'org', 'net', 'io', 'so') else parts[0]
                # Fallback: check if we have a file that matches distinct parts
                for part in parts:
                    if (ICONS_DIR / f"{part}.webp").exists():
                        filename = part
                        break
        
        if not filename:
             return None
             
        path = ICONS_DIR / f"{filename}.webp"
        if path.exists():
            image = QImage()
            if image.load(str(path)):
                pixmap = QPixmap.fromImage(image)
                _favicon_cache[domain] = pixmap
                return pixmap
        
        return None

_favicon_loader = FaviconLoader()

def get_favicon(domain: str) -> Optional[QPixmap]:
    """
    Returns cached or locally loaded pixmap if available.
    Returns None if no icon found.
    Sync operation (disk I/O).
    """
    return _favicon_loader.get_icon(domain)

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
            QLabel {{
                background-color: {icon_color};
                color: white;
                border-radius: {radius}px;
                font-weight: 700;
                font-size: {font_size}px;
            }}
        """)

    def _load_favicon(self):
        pixmap = get_favicon(self.domain)
        if pixmap:
            # Scale for display
            scaled = pixmap.scaled(
                self.icon_size, self.icon_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self._set_favicon(scaled)

    def _set_favicon(self, pixmap: QPixmap):
        self.setText("")
        self.setPixmap(pixmap)
        radius = int(self.icon_size * 0.2)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: transparent;
                border-radius: {radius}px;
            }}
        """)
