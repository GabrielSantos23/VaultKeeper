
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QApplication, QWidget, QPushButton

from PySide6.QtCore import Qt, Signal, QTimer

from PySide6.QtGui import QIcon, QPainter, QColor, QPen

from app.core.password_strength import analyze_password

from app.core.totp import TOTPManager, get_totp_code

from app.core.config import get_config

from app.ui.theme import get_theme

from app.ui.ui_utils import load_svg_icon, create_icon_button

class DetailField(QFrame):

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

        label = QLabel(self.label_text.upper())

        label.setStyleSheet(f"""
            color: {theme.colors.primary};
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
        """)

        layout.addWidget(label)

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

class TOTPProgressWidget(QWidget):

    def __init__(self, total_seconds: int = 30, parent=None):

        super().__init__(parent)

        self.total_seconds = total_seconds

        self.remaining_seconds = total_seconds

        self.setFixedSize(24, 24)

    def set_remaining(self, remaining: int):

        self.remaining_seconds = remaining

        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing)

        theme = get_theme()

        progress = self.remaining_seconds / self.total_seconds

        pen = QPen(QColor(theme.colors.border))

        pen.setWidth(3)

        painter.setPen(pen)

        painter.drawEllipse(3, 3, 18, 18)

        if self.remaining_seconds <= 5:

            arc_color = QColor("#ef4444")

        elif self.remaining_seconds <= 10:

            arc_color = QColor("#f97316")

        else:

            arc_color = QColor(theme.colors.primary)

        pen.setColor(arc_color)

        pen.setWidth(3)

        pen.setCapStyle(Qt.RoundCap)

        painter.setPen(pen)

        start_angle = 90 * 16

        span_angle = int(-progress * 360 * 16)

        painter.drawArc(3, 3, 18, 18, start_angle, span_angle)

class TOTPField(QFrame):

    copied = Signal(str)

    def __init__(self, totp_secret: str, parent=None):

        super().__init__(parent)

        self.totp_secret = totp_secret

        self.totp_manager = TOTPManager(totp_secret)

        self.setup_ui()

        self.update_timer = QTimer(self)

        self.update_timer.timeout.connect(self._update_display)

        self.update_timer.start(1000)

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

        label = QLabel("TWO-FACTOR CODE")

        label.setStyleSheet(f"""
            color: {theme.colors.primary};
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
        """)

        layout.addWidget(label)

        value_layout = QHBoxLayout()

        value_layout.setSpacing(12)

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

        self.timer_label = QLabel("30s")

        self.timer_label.setFixedWidth(40)

        self.timer_label.setAlignment(Qt.AlignCenter)

        self.timer_label.setStyleSheet(f"""
            color: {theme.colors.muted_foreground};
            font-size: 12px;
            font-weight: 500;
        """)

        value_layout.addWidget(self.timer_label)

        self.progress_widget = TOTPProgressWidget(30)

        value_layout.addWidget(self.progress_widget)

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

        try:

            code, remaining = get_totp_code(self.totp_secret)

            formatted_code = f"{code[:3]} {code[3:]}" if len(code) == 6 else code

            self.code_label.setText(formatted_code)

            self.timer_label.setText(f"{remaining}s")

            self.progress_widget.set_remaining(remaining)

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

        try:

            code, _ = get_totp_code(self.totp_secret)

            QApplication.clipboard().setText(code)

            self.copied.emit("TOTP Code")

            QTimer.singleShot(30000, lambda: QApplication.clipboard().clear())

        except:

            pass

    def cleanup(self):

        if self.update_timer:

            self.update_timer.stop()
