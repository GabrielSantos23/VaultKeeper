import string
import secrets
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QSlider, QCheckBox, QApplication, QProgressBar, QScrollArea,
    QTextEdit
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QClipboard, QIcon, QTextOption
from app.ui.theme import get_theme
from app.ui.ui_utils import load_svg_icon, get_icon_path

class GeneratorView(QWidget):
    use_password_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.generate_password()

    def setup_ui(self):
        theme = get_theme()
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("QScrollArea { background: transparent; } QWidget#generator_content { background: transparent; }")

        self.content_widget = QWidget()
        self.content_widget.setObjectName("generator_content")
        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area)

        layout = QVBoxLayout(self.content_widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

    # Header com ícone e descrição
        header_layout = QHBoxLayout()
        
        icon_label = QLabel()
        icon_label.setPixmap(QIcon(load_svg_icon("lock", 24, theme.colors.primary)).pixmap(24, 24))
        icon_label.setFixedSize(48, 48)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(f"""
            background-color: {theme.colors.primary};
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            padding: 0 20px;
        """)
        header_layout.addWidget(icon_label)
        
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        
        header = QLabel("Password Generator")
        header.setStyleSheet(f"""
            color: {theme.colors.foreground};
            font-size: 24px;
            font-weight: 700;
        """)
        title_layout.addWidget(header)
        
        subtitle = QLabel("Create strong, secure passwords instantly")
        subtitle.setStyleSheet(f"""
            color: {theme.colors.muted_foreground};
            font-size: 14px;
        """)
        title_layout.addWidget(subtitle)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        # Use Password Button
        btn_use_password = QPushButton("Use Password")
        btn_use_password.setCursor(Qt.PointingHandCursor)
        btn_use_password.setFixedHeight(40)
        btn_use_password.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.colors.primary};
                color: {theme.colors.primary_foreground};
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors.ring};
            }}
        """)
        btn_use_password.clicked.connect(self.request_use_password)
        header_layout.addWidget(btn_use_password)
        
        layout.addLayout(header_layout)

        # Password Display Card
        self.display_card = QFrame()
        self.display_card.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.colors.card};
                border: 1px solid {theme.colors.border};
                border-radius: 12px;
            }}
        """)
        card_layout = QVBoxLayout(self.display_card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(20)
        
        # Security Badge
        badge_layout = QHBoxLayout()
        badge_layout.addStretch()
        security_badge = QLabel("🛡 STRONGLY SECURED")
        security_badge.setStyleSheet(f"""
            background-color: #10b981;
            color: #ffffff;
            font-size: 11px;
            font-weight: 700;
            padding: 6px 12px;
            border-radius: 12px;
        """)
        badge_layout.addWidget(security_badge)
        badge_layout.addStretch()
        card_layout.addLayout(badge_layout)
        
                 # Password Display
        password_container = QFrame()
        password_container.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.colors.list_background};
                border: 1px solid {theme.colors.border};
                border-radius: 12px;
            }}
        """)
        password_container_layout = QVBoxLayout(password_container)
        password_container_layout.setContentsMargins(16, 16, 16, 16)
        password_container_layout.setSpacing(0)
        
        self.password_display = QTextEdit()
        self.password_display.setReadOnly(True)
        self.password_display.setFrameShape(QFrame.NoFrame)
        self.password_display.setMaximumHeight(100)
        self.password_display.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.password_display.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Enable wrapping anywhere (inside words)
        self.password_display.setLineWrapMode(QTextEdit.WidgetWidth)
        self.password_display.setWordWrapMode(QTextOption.WrapAnywhere)
        
        # Center align text
        text_option = self.password_display.document().defaultTextOption()
        text_option.setAlignment(Qt.AlignCenter)
        self.password_display.document().setDefaultTextOption(text_option)

        self.password_display.setStyleSheet(f"""
            QTextEdit {{
                color: {theme.colors.primary};
                font-size: 24px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-weight: 700;
                letter-spacing: 1px;
                background-color: transparent;
                border: none;
            }}
        """)
        
        password_container_layout.addWidget(self.password_display)
        card_layout.addWidget(password_container)
        
        # Action Buttons
        actions_container = QWidget()
        actions_container.setStyleSheet("background-color: transparent;")
        actions_container.setMinimumHeight(52)
        actions_layout = QHBoxLayout(actions_container)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(12)
        
        actions_layout.addStretch()

        self.btn_copy = QPushButton("Copy Password")
        self.btn_copy.setIcon(QIcon(load_svg_icon("copy", 18, theme.colors.foreground)))
        self.btn_copy.setCursor(Qt.PointingHandCursor)
        self.btn_copy.setFixedHeight(44)
        self.btn_copy.setFixedWidth(180)
        self.btn_copy.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.colors.list_background};
                color: {theme.colors.foreground};
                border: 1px solid {theme.colors.border};
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                padding: 0 12px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors.accent};
            }}
        """)
        self.btn_copy.clicked.connect(self.copy_to_clipboard)
        actions_layout.addWidget(self.btn_copy)

        self.btn_regenerate = QPushButton("Regenerate")
        self.btn_regenerate.setIcon(QIcon(load_svg_icon("refresh", 18, theme.colors.primary)))
        self.btn_regenerate.setCursor(Qt.PointingHandCursor)
        self.btn_regenerate.setFixedHeight(44)
        self.btn_regenerate.setFixedWidth(180)
        self.btn_regenerate.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.colors.list_background};
                color: {theme.colors.primary};
                border: 1px solid {theme.colors.border};
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                padding: 0 12px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors.accent};
            }}
        """)
        self.btn_regenerate.clicked.connect(self.generate_password)
        actions_layout.addWidget(self.btn_regenerate)
        
        actions_layout.addStretch()
        
        card_layout.addWidget(actions_container)
        
        # Strength Meter
        strength_layout = QVBoxLayout()
        strength_layout.setSpacing(12)
        
        strength_header = QHBoxLayout()
        strength_label = QLabel("STRENGTH METER")
        strength_label.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 11px; font-weight: 700;")
        strength_header.addWidget(strength_label)
        strength_header.addStretch()
        
        self.strength_text = QLabel("EXCELLENT STRENGTH")
        self.strength_text.setStyleSheet(f"color: #10b981; font-size: 11px; font-weight: 700;")
        strength_header.addWidget(self.strength_text)
        strength_layout.addLayout(strength_header)
        
        # Strength bars
        bars_layout = QHBoxLayout()
        bars_layout.setSpacing(8)
        self.strength_bars = []
        for i in range(4):
            bar = QFrame()
            bar.setFixedHeight(4)
            bar.setStyleSheet(f"""
                background-color: #10b981;
                border-radius: 2px;
            """)
            bars_layout.addWidget(bar)
            self.strength_bars.append(bar)
        
        strength_layout.addLayout(bars_layout)
        card_layout.addLayout(strength_layout)
        
        layout.addWidget(self.display_card)

        # Controls Row
        controls_row = QHBoxLayout()
        controls_row.setSpacing(24)

        # Password Length Card
        length_card = QFrame()
        length_card.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.colors.card};
                border: 1px solid {theme.colors.border};
                border-radius: 12px;
            }}
        """)
        length_layout = QVBoxLayout(length_card)
        length_layout.setContentsMargins(20, 20, 20, 20)
        length_layout.setSpacing(16)

        length_header = QHBoxLayout()
        length_label = QLabel("PASSWORD LENGTH")
        length_label.setStyleSheet(f"color: {theme.colors.primary}; font-size: 12px; font-weight: 700;")
        length_header.addWidget(length_label)
        length_header.addStretch()
        
        self.length_value = QLabel("20")
        self.length_value.setStyleSheet(f"color: {theme.colors.foreground}; font-size: 32px; font-weight: 700; background-color: transparent;")
        length_layout.addLayout(length_header)
        length_layout.addWidget(self.length_value, alignment=Qt.AlignCenter)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(8)
        self.slider.setMaximum(100)
        self.slider.setValue(20)
        self.slider.setCursor(Qt.PointingHandCursor)
        self.slider.setStyleSheet(f"""
            QSlider {{
                background-color: transparent;
            }}
            QSlider::groove:horizontal {{
                height: 6px;
                background: {theme.colors.list_background};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {theme.colors.primary};
                width: 18px;
                height: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }}
            QSlider::sub-page:horizontal {{
                background: {theme.colors.primary};
                border-radius: 3px;
            }}
        """)
        self.slider.valueChanged.connect(self._on_length_changed)
        length_layout.addWidget(self.slider)
        
        slider_labels = QHBoxLayout()
        short_label = QLabel("SHORT (8)")
        short_label.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 11px;")
        long_label = QLabel("LONG (100)")
        long_label.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 11px;")
        slider_labels.addWidget(short_label)
        slider_labels.addStretch()
        slider_labels.addWidget(long_label)
        length_layout.addLayout(slider_labels)

        controls_row.addWidget(length_card, 1)

        # Security Preferences Card
        prefs_card = QFrame()
        prefs_card.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.colors.card};
                border: 1px solid {theme.colors.border};
                border-radius: 12px;
            }}
        """)
        prefs_layout = QVBoxLayout(prefs_card)
        prefs_layout.setContentsMargins(20, 20, 20, 20)
        prefs_layout.setSpacing(12)

        prefs_label = QLabel("SECURITY PREFERENCES")
        prefs_label.setStyleSheet(f"color: {theme.colors.primary}; font-size: 12px; font-weight: 700; background-color: transparent; border:none;")
        prefs_layout.addWidget(prefs_label)

        self.check_numbers = self._create_checkbox("Numbers (0-9)", True)
        self.check_symbols = self._create_checkbox("Symbols (!@#$)", True)
        self.check_upper = self._create_checkbox("Uppercase (A-Z)", True)
        self.check_lower = self._create_checkbox("Lowercase (a-z)", True)
        
        prefs_layout.addWidget(self.check_numbers)
        prefs_layout.addWidget(self.check_symbols)
        prefs_layout.addWidget(self.check_upper)
        prefs_layout.addWidget(self.check_lower)

        controls_row.addWidget(prefs_card, 1)

        layout.addLayout(controls_row)

        # Security Pro Tip
        tip_card = QFrame()
        tip_card.setStyleSheet(f"""
            QFrame {{
                background-color: #1E242F;
                border: 1px solid {theme.colors.primary};
                border-radius: 12px;
            }}
        """)
        tip_layout = QHBoxLayout(tip_card)
        tip_layout.setContentsMargins(20, 20, 20, 20)
        tip_layout.setSpacing(20)
        
        # Icon Container
        icon_container = QLabel("💡")
        icon_container.setFixedSize(48, 48)
        icon_container.setAlignment(Qt.AlignCenter)
        icon_container.setStyleSheet(f"""
            QLabel {{
                background-color: #263246;
                color: {theme.colors.primary};
                border-radius: 24px;
                font-size: 20px;
                border: none;
            }}
        """)
        tip_layout.addWidget(icon_container, 0)
        
        tip_content = QVBoxLayout()
        tip_content.setSpacing(4)
        
        tip_title = QLabel("SECURITY PRO-TIP")
        tip_title.setStyleSheet(f"color: {theme.colors.primary}; font-size: 12px; font-weight: 700; background-color: transparent; border:none;")
        tip_content.addWidget(tip_title)
        
        tip_text = QLabel("A longer password is almost always better than a complex one. Aim for at least 16 characters for maximum security across your accounts. We recommend using a different password for every single service.")
        tip_text.setWordWrap(True)
        tip_text.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 13px; line-height: 1.5; background-color: transparent; border:none;")
        tip_content.addWidget(tip_text)
        
        tip_layout.addLayout(tip_content, 1)
        
        layout.addWidget(tip_card)
        layout.addStretch()

    def _create_checkbox(self, text, checked):
        cb = QCheckBox(text)
        cb.setChecked(checked)
        cb.setCursor(Qt.PointingHandCursor)
        theme = get_theme()
        cb.setStyleSheet(f"""
            QCheckBox {{
                color: {theme.colors.foreground};
                font-size: 14px;
                spacing: 12px;
                background-color: transparent;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border: 2px solid {theme.colors.border};
                border-radius: 10px;
                background: {theme.colors.background};
            }}
            QCheckBox::indicator:hover {{
                border-color: {theme.colors.primary};
            }}
            QCheckBox::indicator:checked {{
                background-color: {theme.colors.primary};
                border-color: {theme.colors.primary};
            }}
        """)
        cb.stateChanged.connect(self.generate_password)
        
        return cb

    def _on_length_changed(self, value):
        self.length_value.setText(str(value))
        self.generate_password()

    def generate_password(self):
        length = self.slider.value()
        use_upper = self.check_upper.isChecked()
        use_lower = self.check_lower.isChecked()
        use_numbers = self.check_numbers.isChecked()
        use_symbols = self.check_symbols.isChecked()

        if not any([use_upper, use_lower, use_numbers, use_symbols]):
            self.password_display.setPlainText("Select at least one option")
            self.btn_copy.setEnabled(False)
            return

        chars = ""
        if use_upper: chars += string.ascii_uppercase
        if use_lower: chars += string.ascii_lowercase
        if use_numbers: chars += string.digits
        if use_symbols: chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"

        password = []
        if use_upper: password.append(secrets.choice(string.ascii_uppercase))
        if use_lower: password.append(secrets.choice(string.ascii_lowercase))
        if use_numbers: password.append(secrets.choice(string.digits))
        if use_symbols: password.append(secrets.choice("!@#$%^&*()_+-=[]{}|;:,.<>?"))

        remaining = length - len(password)
        if remaining > 0:
            password.extend(secrets.choice(chars) for _ in range(remaining))
        
        secrets.SystemRandom().shuffle(password)
        final_password = "".join(password)
        
        self.password_display.setPlainText(final_password)
        self.btn_copy.setEnabled(True)
        self._update_strength_meter(length, use_upper, use_lower, use_numbers, use_symbols)

    def _update_strength_meter(self, length, upper, lower, numbers, symbols):
        theme = get_theme()
        char_types = sum([upper, lower, numbers, symbols])
        
        if length >= 16 and char_types >= 3:
            strength = 4
            color = "#10b981"
            text = "EXCELLENT STRENGTH"
        elif length >= 12 and char_types >= 2:
            strength = 3
            color = "#10b981"
            text = "GOOD STRENGTH"
        elif length >= 8:
            strength = 2
            color = "#f59e0b"
            text = "FAIR STRENGTH"
        else:
            strength = 1
            color = "#ef4444"
            text = "WEAK STRENGTH"
        
        self.strength_text.setText(text)
        self.strength_text.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: 700;")
        
        for i, bar in enumerate(self.strength_bars):
            if i < strength:
                bar.setStyleSheet(f"background-color: {color}; border-radius: 2px;")
            else:
                bar.setStyleSheet(f"background-color: {theme.colors.input}; border-radius: 2px;")

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.password_display.toPlainText())
        
        theme = get_theme()
        original_text = self.btn_copy.text()
        self.btn_copy.setText("Copied!")
        self.btn_copy.setStyleSheet(f"""
            QPushButton {{
                background-color: #10b981;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                padding: 0 12px;
            }}
        """)
        
        QTimer.singleShot(2000, lambda: self._reset_copy_button(original_text))

    def _reset_copy_button(self, original_text):
        theme = get_theme()
        self.btn_copy.setText(original_text)
        self.btn_copy.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.colors.list_background};
                color: {theme.colors.foreground};
                border: 1px solid {theme.colors.border};
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                padding: 0 12px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors.accent};
            }}
        """)

    def request_use_password(self):
        self.use_password_requested.emit(self.password_display.toPlainText())