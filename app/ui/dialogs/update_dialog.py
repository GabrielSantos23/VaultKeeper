
from PySide6.QtWidgets import (

    QDialog, QVBoxLayout, QHBoxLayout, QLabel,

    QPushButton, QProgressBar, QWidget

)

from PySide6.QtCore import Qt, QSize

from PySide6.QtGui import QIcon

from app.core.updater import UpdateManager

class UpdateDialog(QDialog):

    def __init__(self, parent=None, version: str = "", download_url: str = ""):

        super().__init__(parent)

        self.version = version

        self.download_url = download_url

        self.manager = UpdateManager()

        self.setWindowTitle("Update Available")

        self.setFixedWidth(400)

        self.setup_ui()

        self.setup_connections()

    def setup_ui(self):

        layout = QVBoxLayout(self)

        layout.setSpacing(20)

        layout.setContentsMargins(24, 24, 24, 24)

        header_layout = QVBoxLayout()

        header_layout.setSpacing(8)

        title = QLabel("New Version Available")

        title.setObjectName("title")

        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.message = QLabel(f"A new version of VaultKeeper ({self.version}) is available to download.")

        self.message.setWordWrap(True)

        self.message.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.message.setObjectName("muted")

        header_layout.addWidget(title)

        header_layout.addWidget(self.message)

        layout.addLayout(header_layout)

        self.progress_bar = QProgressBar()

        self.progress_bar.setRange(0, 100)

        self.progress_bar.setValue(0)

        self.progress_bar.hide()

        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")

        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.status_label.setObjectName("muted")

        self.status_label.hide()

        layout.addWidget(self.status_label)

        self.button_layout = QHBoxLayout()

        self.button_layout.setSpacing(12)

        self.cancel_btn = QPushButton("Not Now")

        self.cancel_btn.setObjectName("secondary")

        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.update_btn = QPushButton("Update Now")

        self.update_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.button_layout.addWidget(self.cancel_btn)

        self.button_layout.addWidget(self.update_btn)

        layout.addLayout(self.button_layout)

    def setup_connections(self):

        self.update_btn.clicked.connect(self.start_update)

        self.cancel_btn.clicked.connect(self.reject)

        self.manager.download_progress.connect(self.on_download_progress)

        self.manager.download_complete.connect(self.on_download_complete)

        self.manager.download_error.connect(self.on_error)

        self.manager.install_complete.connect(self.on_install_complete)

    def start_update(self):

        self.update_btn.setEnabled(False)

        self.cancel_btn.setEnabled(False)

        self.progress_bar.show()

        self.status_label.show()

        self.status_label.setText("Downloading update...")

        self.manager.download_update(self.download_url)

    def on_download_progress(self, percent):

        self.progress_bar.setValue(percent)

    def on_download_complete(self, file_path):

        self.status_label.setText("Installing update...")

        self.progress_bar.setRange(0, 0)

        import os

        install_dir = os.getcwd()

        self.manager.install_update(file_path, install_dir)

    def on_install_complete(self):

        self.status_label.setText("Update started. Closing...")

        from PySide6.QtWidgets import QApplication

        QApplication.quit()

    def on_error(self, error):

        self.status_label.setText(f"Error: {error}")

        self.status_label.setObjectName("error")

        self.progress_bar.hide()

        self.update_btn.setEnabled(True)

        self.cancel_btn.setEnabled(True)
