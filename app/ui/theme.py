"""
VaultKeeper Theme System
Modern design system with light and dark themes for PySide6
Based on 1Password-like design
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ThemeMode(Enum):
    """Available theme modes."""
    LIGHT = "light"
    DARK = "dark"


@dataclass
class ThemeColors:
    """Theme color definitions."""
    background: str
    foreground: str
    card: str
    card_foreground: str
    popover: str
    popover_foreground: str
    primary: str
    primary_foreground: str
    secondary: str
    secondary_foreground: str
    muted: str
    muted_foreground: str
    accent: str
    accent_foreground: str
    destructive: str
    destructive_foreground: str
    border: str
    input: str
    ring: str
    success: str
    success_foreground: str
    warning: str
    warning_foreground: str
    list_background: str         # Background for credentials list
    sidebar: str
    sidebar_foreground: str
    sidebar_primary: str
    sidebar_primary_foreground: str
    sidebar_accent: str
    sidebar_accent_foreground: str
    sidebar_border: str
    sidebar_ring: str
    sidebar_muted: str


# Light theme colors (1Password inspired)
LIGHT_COLORS = ThemeColors(
    background="#f5f6f7",
    foreground="#1a1a1a",
    card="#ffffff",
    card_foreground="#1a1a1a",
    popover="#ffffff",
    popover_foreground="#1a1a1a",
    primary="#0073e6",           # Blue primary
    primary_foreground="#ffffff",
    secondary="#e8eaed",
    secondary_foreground="#1a1a1a",
    muted="#f0f1f2",
    muted_foreground="#6b7280",
    accent="#e8eaed",
    accent_foreground="#1a1a1a",
    destructive="#dc2626",
    destructive_foreground="#ffffff",
    border="#d1d5db",
    input="#ffffff",
    ring="#0073e6",
    success="#22c55e",
    success_foreground="#ffffff",
    warning="#f59e0b",
    warning_foreground="#ffffff",
    list_background="#ebedef",   # Light list background
    sidebar="#1e2530",           # Dark blue sidebar
    sidebar_foreground="#ffffff",
    sidebar_primary="#3b82f6",
    sidebar_primary_foreground="#ffffff",
    sidebar_accent="#2d3748",
    sidebar_accent_foreground="#ffffff",
    sidebar_border="#374151",
    sidebar_ring="#3b82f6",
    sidebar_muted="#9ca3af",
)

# Dark theme colors (1Password inspired - main theme)
DARK_COLORS = ThemeColors(
    background="#1C1F24",        # Detail panel background
    foreground="#e5e7eb",        # Light text
    card="#1C1F24",              # Card background same as detail panel
    card_foreground="#e5e7eb",
    popover="#2d333b",
    popover_foreground="#e5e7eb",
    primary="#3b9eff",           # Bright blue primary
    primary_foreground="#ffffff",
    secondary="#2a2e35",
    secondary_foreground="#e5e7eb",
    muted="#252930",
    muted_foreground="#9ca3af",  # Gray muted text
    accent="#2a2e35",
    accent_foreground="#e5e7eb",
    destructive="#ef4444",
    destructive_foreground="#ffffff",
    border="#2a2e35",            # Subtle border
    input="#252930",
    ring="#3b9eff",
    success="#22c55e",           # Green for password strength
    success_foreground="#ffffff",
    warning="#f59e0b",           # Orange/yellow for warnings
    warning_foreground="#ffffff",
    list_background="#16191D",   # Credentials list background
    sidebar="#0F1115",           # VaultKeeper sidebar (darkest)
    sidebar_foreground="#e5e7eb",
    sidebar_primary="#3b9eff",   # Blue selected state
    sidebar_primary_foreground="#ffffff",
    sidebar_accent="#1a1d22",    # Hover state
    sidebar_accent_foreground="#ffffff",
    sidebar_border="#1a1d22",
    sidebar_ring="#3b9eff",
    sidebar_muted="#6b7280",
)


@dataclass
class ThemeSpacing:
    """Theme spacing definitions (based on 0.25rem = 4px)."""
    unit: int = 4  # Base spacing unit in pixels
    
    @property
    def xs(self) -> int:
        return self.unit  # 4px
    
    @property
    def sm(self) -> int:
        return self.unit * 2  # 8px
    
    @property
    def md(self) -> int:
        return self.unit * 3  # 12px
    
    @property
    def lg(self) -> int:
        return self.unit * 4  # 16px
    
    @property
    def xl(self) -> int:
        return self.unit * 6  # 24px
    
    @property
    def xxl(self) -> int:
        return self.unit * 8  # 32px


@dataclass
class ThemeRadius:
    """Theme border radius definitions (based on 0.5rem = 8px)."""
    base: int = 8  # Base radius in pixels
    
    @property
    def sm(self) -> int:
        return max(0, self.base - 4)  # 4px
    
    @property
    def md(self) -> int:
        return max(0, self.base - 2)  # 6px
    
    @property
    def lg(self) -> int:
        return self.base  # 8px
    
    @property
    def xl(self) -> int:
        return self.base + 4  # 12px
    
    @property
    def full(self) -> int:
        return 9999  # Fully rounded


@dataclass
class ThemeShadows:
    """Theme shadow definitions."""
    none: str = "none"
    
    @property
    def xs(self) -> str:
        return "0px 1px 2px rgba(0, 0, 0, 0.09)"
    
    @property
    def sm(self) -> str:
        return "0px 1px 2px rgba(0, 0, 0, 0.18)"
    
    @property
    def md(self) -> str:
        return "0px 2px 4px rgba(0, 0, 0, 0.18)"
    
    @property
    def lg(self) -> str:
        return "0px 4px 6px rgba(0, 0, 0, 0.18)"
    
    @property
    def xl(self) -> str:
        return "0px 8px 10px rgba(0, 0, 0, 0.18)"
    
    @property
    def xxl(self) -> str:
        return "0px 12px 24px rgba(0, 0, 0, 0.45)"


@dataclass
class ThemeFonts:
    """Theme font definitions."""
    sans: str = "'Segoe UI', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif"
    mono: str = "'Fira Code', 'JetBrains Mono', 'Consolas', monospace"
    serif: str = "Georgia, 'Times New Roman', serif"
    
    # Font sizes in pixels
    size_xs: int = 11
    size_sm: int = 13
    size_base: int = 14
    size_lg: int = 16
    size_xl: int = 18
    size_2xl: int = 22
    size_3xl: int = 28
    size_4xl: int = 36


class Theme:
    """Complete theme definition with all design tokens."""
    
    def __init__(self, mode: ThemeMode = ThemeMode.DARK):
        self.mode = mode
        self.colors = DARK_COLORS if mode == ThemeMode.DARK else LIGHT_COLORS
        self.spacing = ThemeSpacing()
        self.radius = ThemeRadius()
        self.shadows = ThemeShadows()
        self.fonts = ThemeFonts()
    
    def toggle(self) -> "Theme":
        """Toggle between light and dark mode."""
        new_mode = ThemeMode.LIGHT if self.mode == ThemeMode.DARK else ThemeMode.DARK
        return Theme(new_mode)
    
    def get_stylesheet(self) -> str:
        """Generate complete Qt stylesheet for the current theme."""
        c = self.colors
        r = self.radius
        f = self.fonts
        s = self.spacing
        
        return f"""
            /* ===== BASE STYLES ===== */
            QMainWindow, QWidget {{
                background-color: {c.background};
                color: {c.foreground};
                font-family: {f.sans};
                font-size: {f.size_base}px;
            }}
            
            /* ===== TEXT INPUTS ===== */
            QLineEdit {{
                background-color: {c.input};
                border: 1px solid {c.border};
                border-radius: {r.md}px;
                padding: {s.md}px {s.lg}px;
                color: {c.foreground};
                font-size: {f.size_sm}px;
                selection-background-color: {c.primary};
                selection-color: {c.primary_foreground};
            }}
            
            QLineEdit:focus {{
                border-color: {c.ring};
                border-width: 2px;
            }}
            
            QLineEdit:disabled {{
                background-color: {c.muted};
                color: {c.muted_foreground};
            }}
            
            QLineEdit::placeholder {{
                color: {c.muted_foreground};
            }}
            
            /* ===== TEXT AREA ===== */
            QTextEdit {{
                background-color: {c.input};
                border: 1px solid {c.border};
                border-radius: {r.md}px;
                padding: {s.md}px;
                color: {c.foreground};
                font-size: {f.size_sm}px;
                selection-background-color: {c.primary};
                selection-color: {c.primary_foreground};
            }}
            
            QTextEdit:focus {{
                border-color: {c.ring};
                border-width: 2px;
            }}
            
            /* ===== PRIMARY BUTTONS ===== */
            QPushButton {{
                background-color: {c.primary};
                color: {c.primary_foreground};
                border: none;
                border-radius: {r.md}px;
                padding: {s.md}px {s.xl}px;
                font-size: {f.size_sm}px;
                font-weight: 500;
                min-height: 20px;
            }}
            
            QPushButton:hover {{
                background-color: {c.ring};
            }}
            
            QPushButton:pressed {{
                background-color: {c.primary};
            }}
            
            QPushButton:disabled {{
                background-color: {c.muted};
                color: {c.muted_foreground};
            }}
            
            /* ===== SECONDARY BUTTONS ===== */
            QPushButton#secondary, QPushButton[secondary="true"] {{
                background-color: {c.secondary};
                color: {c.secondary_foreground};
            }}
            
            QPushButton#secondary:hover, QPushButton[secondary="true"]:hover {{
                background-color: {c.accent};
            }}
            
            /* ===== DESTRUCTIVE BUTTONS ===== */
            QPushButton#destructive, QPushButton[destructive="true"] {{
                background-color: {c.destructive};
                color: {c.destructive_foreground};
            }}
            
            QPushButton#destructive:hover, QPushButton[destructive="true"]:hover {{
                background-color: {c.destructive};
            }}
            
            /* ===== GHOST BUTTONS ===== */
            QPushButton#ghost, QPushButton[ghost="true"] {{
                background-color: transparent;
                color: {c.foreground};
            }}
            
            QPushButton#ghost:hover, QPushButton[ghost="true"]:hover {{
                background-color: {c.accent};
                color: {c.accent_foreground};
            }}
            
            /* ===== OUTLINE BUTTONS ===== */
            QPushButton#outline, QPushButton[outline="true"] {{
                background-color: transparent;
                color: {c.foreground};
                border: 1px solid {c.border};
            }}
            
            QPushButton#outline:hover, QPushButton[outline="true"]:hover {{
                background-color: {c.accent};
                color: {c.accent_foreground};
            }}
            
            /* ===== ICON BUTTONS ===== */
            QPushButton#icon, QPushButton[icon="true"] {{
                background-color: transparent;
                color: {c.foreground};
                padding: {s.sm}px;
                min-width: 32px;
                max-width: 32px;
                min-height: 32px;
                max-height: 32px;
                border-radius: {r.md}px;
            }}
            
            QPushButton#icon:hover, QPushButton[icon="true"]:hover {{
                background-color: {c.accent};
            }}
            
            /* ===== LIST WIDGET ===== */
            QListWidget {{
                background-color: {c.card};
                border: 1px solid {c.border};
                border-radius: {r.lg}px;
                padding: {s.sm}px;
                outline: none;
            }}
            
            QListWidget::item {{
                background-color: transparent;
                border-radius: {r.sm}px;
                padding: {s.md}px;
                margin: {s.xs}px 0;
                color: {c.card_foreground};
            }}
            
            QListWidget::item:selected {{
                background-color: {c.primary};
                color: {c.primary_foreground};
            }}
            
            QListWidget::item:hover {{
                background-color: {c.muted};
            }}
            
            /* ===== LABELS ===== */
            QLabel {{
                color: {c.foreground};
                font-size: {f.size_sm}px;
            }}
            
            QLabel#title {{
                font-size: {f.size_3xl}px;
                font-weight: bold;
                color: {c.foreground};
            }}
            
            QLabel#subtitle {{
                font-size: {f.size_sm}px;
                color: {c.muted_foreground};
            }}
            
            QLabel#error {{
                color: {c.destructive};
                font-size: {f.size_sm}px;
            }}
            
            QLabel#muted {{
                color: {c.muted_foreground};
            }}
            
            /* ===== CARDS ===== */
            QFrame#card {{
                background-color: {c.card};
                border: 1px solid {c.border};
                border-radius: {r.lg}px;
                padding: {s.xl}px;
            }}
            
            /* ===== DIALOGS ===== */
            QDialog {{
                background-color: {c.popover};
                color: {c.popover_foreground};
                border-radius: {r.lg}px;
            }}
            
            /* ===== MENU ===== */
            QMenu {{
                background-color: {c.popover};
                color: {c.popover_foreground};
                border: 1px solid {c.border};
                border-radius: {r.md}px;
                padding: {s.xs}px;
            }}
            
            QMenu::item {{
                padding: {s.sm}px {s.lg}px;
                border-radius: {r.sm}px;
            }}
            
            QMenu::item:selected {{
                background-color: {c.accent};
                color: {c.accent_foreground};
            }}
            
            QMenu::separator {{
                height: 1px;
                background-color: {c.border};
                margin: {s.xs}px {s.sm}px;
            }}
            
            /* ===== SCROLLBAR ===== */
            QScrollBar:vertical {{
                background-color: transparent;
                width: 8px;
                margin: 0;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {c.muted};
                border-radius: 4px;
                min-height: 30px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {c.muted_foreground};
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
            
            QScrollBar:horizontal {{
                background-color: transparent;
                height: 8px;
                margin: 0;
            }}
            
            QScrollBar::handle:horizontal {{
                background-color: {c.muted};
                border-radius: 4px;
                min-width: 30px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background-color: {c.muted_foreground};
            }}
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0;
            }}
            
            /* ===== TOOLTIP ===== */
            QToolTip {{
                background-color: {c.popover};
                color: {c.popover_foreground};
                border: 1px solid {c.border};
                border-radius: {r.sm}px;
                padding: {s.sm}px {s.md}px;
                font-size: {f.size_xs}px;
            }}
            
            /* ===== MESSAGE BOX ===== */
            QMessageBox {{
                background-color: {c.card};
            }}
            
            QMessageBox QLabel {{
                color: {c.card_foreground};
                font-size: {f.size_sm}px;
            }}
            
            /* ===== TAB WIDGET ===== */
            QTabWidget::pane {{
                background-color: {c.card};
                border: 1px solid {c.border};
                border-radius: {r.md}px;
                padding: {s.lg}px;
            }}
            
            QTabBar::tab {{
                background-color: {c.muted};
                color: {c.muted_foreground};
                padding: {s.sm}px {s.lg}px;
                margin-right: 2px;
                border-top-left-radius: {r.sm}px;
                border-top-right-radius: {r.sm}px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {c.card};
                color: {c.foreground};
            }}
            
            QTabBar::tab:hover:!selected {{
                background-color: {c.accent};
            }}
            
            /* ===== CHECKBOX ===== */
            QCheckBox {{
                color: {c.foreground};
                spacing: {s.sm}px;
            }}
            
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid {c.border};
                border-radius: {r.sm}px;
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {c.primary};
                border-color: {c.primary};
            }}
            
            QCheckBox::indicator:hover {{
                border-color: {c.ring};
            }}
            
            /* ===== RADIO BUTTON ===== */
            QRadioButton {{
                color: {c.foreground};
                spacing: {s.sm}px;
            }}
            
            QRadioButton::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid {c.border};
                border-radius: 8px;
            }}
            
            QRadioButton::indicator:checked {{
                background-color: {c.primary};
                border-color: {c.primary};
            }}
            
            QRadioButton::indicator:hover {{
                border-color: {c.ring};
            }}
            
            /* ===== COMBO BOX ===== */
            QComboBox {{
                background-color: {c.input};
                border: 1px solid {c.border};
                border-radius: {r.md}px;
                padding: {s.sm}px {s.md}px;
                color: {c.foreground};
                min-height: 20px;
            }}
            
            QComboBox:hover {{
                border-color: {c.ring};
            }}
            
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {c.popover};
                border: 1px solid {c.border};
                border-radius: {r.md}px;
                selection-background-color: {c.accent};
                selection-color: {c.accent_foreground};
            }}
            
            /* ===== PROGRESS BAR ===== */
            QProgressBar {{
                background-color: {c.secondary};
                border: none;
                border-radius: {r.full}px;
                height: 8px;
                text-align: center;
            }}
            
            QProgressBar::chunk {{
                background-color: {c.primary};
                border-radius: {r.full}px;
            }}
            
            /* ===== SLIDER ===== */
            QSlider::groove:horizontal {{
                background-color: {c.secondary};
                height: 4px;
                border-radius: 2px;
            }}
            
            QSlider::handle:horizontal {{
                background-color: {c.primary};
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }}
            
            QSlider::handle:horizontal:hover {{
                background-color: {c.ring};
            }}
            
            /* ===== SPIN BOX ===== */
            QSpinBox, QDoubleSpinBox {{
                background-color: {c.input};
                border: 1px solid {c.border};
                border-radius: {r.md}px;
                padding: {s.sm}px {s.md}px;
                color: {c.foreground};
            }}
            
            QSpinBox:focus, QDoubleSpinBox:focus {{
                border-color: {c.ring};
            }}
            
            QSpinBox::up-button, QDoubleSpinBox::up-button,
            QSpinBox::down-button, QDoubleSpinBox::down-button {{
                background-color: {c.secondary};
                border: none;
                width: 20px;
            }}
            
            /* ===== SIDEBAR STYLES ===== */
            QWidget#sidebar {{
                background-color: {c.sidebar};
            }}
            
            QLabel#sidebar {{
                color: {c.sidebar_foreground};
            }}
            
            QPushButton#sidebar {{
                background-color: transparent;
                color: {c.sidebar_foreground};
                text-align: left;
                padding: {s.sm}px {s.lg}px;
                border-radius: {r.sm}px;
            }}
            
            QPushButton#sidebar:hover {{
                background-color: {c.sidebar_accent};
                color: {c.sidebar_accent_foreground};
            }}
            
            QPushButton#sidebar:checked, QPushButton#sidebar[checked="true"] {{
                background-color: {c.sidebar_primary};
                color: {c.sidebar_primary_foreground};
            }}
            
            /* ===== GROUP BOX ===== */
            QGroupBox {{
                background-color: {c.card};
                border: 1px solid {c.border};
                border-radius: {r.lg}px;
                margin-top: 16px;
                padding-top: 16px;
                font-weight: 500;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 16px;
                padding: 0 8px;
                color: {c.foreground};
            }}
            
            /* ===== SPLITTER ===== */
            QSplitter::handle {{
                background-color: {c.border};
            }}
            
            QSplitter::handle:horizontal {{
                width: 1px;
            }}
            
            QSplitter::handle:vertical {{
                height: 1px;
            }}
            
            /* ===== STATUS BAR ===== */
            QStatusBar {{
                background-color: {c.muted};
                color: {c.muted_foreground};
            }}
            
            QStatusBar::item {{
                border: none;
            }}
        """


# Global theme instance (default to dark mode)
_current_theme: Theme = Theme(ThemeMode.DARK)


def get_theme() -> Theme:
    """Get the current theme."""
    return _current_theme


def set_theme(mode: ThemeMode) -> Theme:
    """Set the current theme mode and return the new theme."""
    global _current_theme
    _current_theme = Theme(mode)
    return _current_theme


def toggle_theme() -> Theme:
    """Toggle between light and dark mode."""
    global _current_theme
    _current_theme = _current_theme.toggle()
    return _current_theme


def get_stylesheet() -> str:
    """Get the stylesheet for the current theme."""
    return _current_theme.get_stylesheet()
