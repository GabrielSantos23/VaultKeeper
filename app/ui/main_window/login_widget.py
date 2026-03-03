
from PySide6.QtWidgets import (

    QWidget, QVBoxLayout, QFrame, QLabel, QLineEdit, QPushButton, QHBoxLayout

)

from PySide6.QtGui import QIcon

from PySide6.QtCore import Qt, Signal, QThread
from app.ui.components.svg_spinner import SvgSpinner

from app.core.auth import AuthManager

from app.ui.theme import get_theme

from app.ui.ui_utils import load_svg_icon

class LoginWorker(QThread):
    finished = Signal(bool, str)

    def __init__(self, auth_manager, password):
        super().__init__()
        self.auth = auth_manager
        self.password = password

    def run(self):
        try:
            if self.auth.is_first_run():
                self.auth.create_master_password(self.password)
            else:
                self.auth.verify_master_password(self.password)
            self.finished.emit(True, "")
        except ValueError as e:
            self.finished.emit(False, str(e))
        except Exception as e:
            self.finished.emit(False, f"An unexpected error occurred: {str(e)}")

class LoginWidget(QWidget):

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

        title = QLabel("VaultKeeper")

        title.setStyleSheet(f"""
            color: {theme.colors.foreground};
            font-size: 28px;
            font-weight: 700;
        """)

        title.setAlignment(Qt.AlignCenter)

        layout.addWidget(title)

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

        self.password_container, self.password_input = self.create_password_field(

            "Master Password", theme.colors.muted_foreground

        )

        self.password_input.returnPressed.connect(self.handle_login)

        card_layout.addWidget(self.password_container)

        if self.auth.is_first_run():

            self.confirm_container, self.confirm_input = self.create_password_field(

                "Confirm Password", theme.colors.muted_foreground

            )

            self.confirm_input.returnPressed.connect(self.handle_login)

            card_layout.addWidget(self.confirm_container)

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

        self.login_btn = QPushButton("Unlock" if not self.auth.is_first_run() else "Create Vault")

        self.login_btn.setCursor(Qt.PointingHandCursor)

        self.login_btn.setStyleSheet(f"""
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

        self.login_btn.clicked.connect(self.handle_login)

        card_layout.addWidget(self.login_btn)
        
        # Add Spinner (Hidden by default)
        self.spinner_container = QWidget()
        self.spinner_container.setFixedHeight(40)
        spinner_layout = QHBoxLayout(self.spinner_container)
        spinner_layout.setContentsMargins(0, 0, 0, 0)
        spinner_layout.setAlignment(Qt.AlignCenter)
        self.spinner = SvgSpinner(size=24, parent=self.spinner_container)
        spinner_layout.addWidget(self.spinner)
        card_layout.addWidget(self.spinner_container)
        self.spinner_container.hide()

        layout.addWidget(input_card, alignment=Qt.AlignCenter)

    def set_loading(self, loading: bool):
        self.login_btn.setVisible(not loading)
        self.spinner_container.setVisible(loading)
        self.password_input.setEnabled(not loading)
        if hasattr(self, 'confirm_input'):
            self.confirm_input.setEnabled(not loading)
            
        if loading:
            self.spinner.start()
            self.error_label.hide()
        else:
            self.spinner.stop()

    def handle_login(self):

        password = self.password_input.text()

        if not password:

            self.show_error("Please enter your master password")

            return

        if self.auth.is_first_run():
             confirm = self.confirm_input.text()
             if password != confirm:
                 self.show_error("Passwords don't match")
                 return

        self.set_loading(True)
        
        self.worker = LoginWorker(self.auth, password)
        self.worker.finished.connect(self.on_login_finished)
        self.worker.start()

    def on_login_finished(self, success, message):
        self.set_loading(False)
        self.setCursor(Qt.ArrowCursor)
        
        if success:
            self.password_input.clear()
            if hasattr(self, 'confirm_input'):
                self.confirm_input.clear()
            self.error_label.hide()
            self.login_success.emit()
        else:
            self.show_error(message)

    def show_error(self, message: str):

        self.error_label.setText(message)

        self.error_label.show()

    def create_password_field(self, placeholder: str, icon_color: str):

        theme = get_theme()

        container = QFrame()

        container.setCursor(Qt.IBeamCursor)

        container.setStyleSheet(f"""
            QFrame {{

                background-color: {theme.colors.input};
                border: 1px solid {theme.colors.border};
                border-radius: 8px;
            }}
        """)

        layout = QHBoxLayout(container)

        layout.setContentsMargins(4, 4, 12, 4)

        layout.setSpacing(8)

        line_edit = QLineEdit()

        line_edit.setEchoMode(QLineEdit.Password)

        line_edit.setPlaceholderText(placeholder)

        line_edit.setStyleSheet(f"""
            border: none;
            background: transparent;
            font-size: 14px;
            color: {theme.colors.foreground};
            padding: 8px;
        """)

        toggle_btn = QPushButton()

        toggle_btn.setCursor(Qt.PointingHandCursor)

        toggle_btn.setIcon(QIcon(load_svg_icon("view", 16, icon_color)))

        toggle_btn.setFixedSize(24, 24)

        toggle_btn.setToolTip("Show Password")

        toggle_btn.setStyleSheet("border: none; background: transparent; padding: 0;")

        def toggle():

            if line_edit.echoMode() == QLineEdit.Password:

                line_edit.setEchoMode(QLineEdit.Normal)

                toggle_btn.setIcon(QIcon(load_svg_icon("visibility_off", 16, icon_color)))

                toggle_btn.setToolTip("Hide Password")

            else:

                line_edit.setEchoMode(QLineEdit.Password)

                toggle_btn.setIcon(QIcon(load_svg_icon("view", 16, icon_color)))

                toggle_btn.setToolTip("Show Password")

        toggle_btn.clicked.connect(toggle)

        layout.addWidget(line_edit)

        layout.addWidget(toggle_btn)

        original_focus_in = line_edit.focusInEvent

        original_focus_out = line_edit.focusOutEvent

        def focus_in(event):

            container.setStyleSheet(f"""
                QFrame {{

                    background-color: {theme.colors.input};
                    border: 1px solid {theme.colors.ring};
                    border-radius: 8px;
                }}
            """)

            original_focus_in(event)

        def focus_out(event):

            container.setStyleSheet(f"""
                QFrame {{

                    background-color: {theme.colors.input};
                    border: 1px solid {theme.colors.border};
                    border-radius: 8px;
                }}
            """)

            original_focus_out(event)

        line_edit.focusInEvent = focus_in

        line_edit.focusOutEvent = focus_out

        return container, line_edit
