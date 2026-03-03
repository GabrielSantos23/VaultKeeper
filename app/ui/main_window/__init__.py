
import sys

from PySide6.QtWidgets import (

    QApplication, QMainWindow, QStackedWidget

)

from PySide6.QtCore import QTimer

from app.core.auth import AuthManager

from app.core.vault import VaultManager

from app.core.config import get_config

from app.ui.theme import get_stylesheet

from app.core.updater import UpdateManager

from .login_widget import LoginWidget

from .vault_widget import VaultWidget

class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.auth = AuthManager()

        self.vault = VaultManager(auth=self.auth)

        self.setWindowTitle("VaultKeeper")

        self.setMinimumSize(1200, 800)

        self.setup_ui()

        self.setup_auto_lock()

        self.check_updates()

    def setup_ui(self):

        self.setStyleSheet(get_stylesheet())

        self.stack = QStackedWidget()

        self.setCentralWidget(self.stack)

        self.login_widget = LoginWidget(self.auth)

        self.login_widget.login_success.connect(self.show_vault)

        self.stack.addWidget(self.login_widget)

        self.vault_widget = None

    def setup_auto_lock(self):

        self.lock_timer = QTimer(self)

        self.lock_timer.timeout.connect(self.check_auto_lock)

        self.lock_timer.start(10000)

        self.update_auto_lock()
        
        # Setup Local Sync
        self.setup_local_sync()

        get_config().settings_changed.connect(self.on_settings_changed)

    def setup_local_sync(self):
        try:
            from app.core.local_sync import LocalSyncServer
            from app.core.config import Config
            vault_path = Config.get_config_dir() / 'vault.db'
            self.sync_server = LocalSyncServer(vault_path)
            
            if get_config().get_local_sync_enabled():
                self.sync_server.start()
                print("📡 Local Sync Server: Started")
        except Exception as e:
            print(f"⚠️ Failed to setup local sync: {e}")
            self.sync_server = None

    def on_settings_changed(self, key, value):

        if key == "general/auto_lock_timeout":

            self.update_auto_lock()
            
        elif key == "general/local_sync":
            if self.sync_server:
                if value:
                    self.sync_server.start()
                    print("📡 Local Sync Server: Started (Settings)")
                else:
                    self.sync_server.stop()
                    print("📡 Local Sync Server: Stopped (Settings)")

    def update_auto_lock(self):

        timeout = get_config().get_auto_lock_timeout()

        self.auth.set_timeout(timeout)

    def check_auto_lock(self):

        if self.auth.check_timeout():

            self.show_login()

    def check_updates(self):

        self.update_manager = UpdateManager()

        self.update_manager.update_available.connect(self.on_update_available)

        self.update_manager.check_for_updates()

    def on_update_available(self, version, url):

        from app.ui.dialogs.update_dialog import UpdateDialog

        dialog = UpdateDialog(self, version, url)

        dialog.exec()

    def show_vault(self):

        if self.vault_widget:

            self.stack.removeWidget(self.vault_widget)

        # Removed synchronous derive_key to prevent freeze
        # self.vault.crypto.derive_key(self.auth.master_password)

        self.vault_widget = VaultWidget(self.vault, master_password=self.auth.master_password)

        self.vault_widget.lock_requested.connect(self.lock_vault)

        self.stack.addWidget(self.vault_widget)

        self.stack.setCurrentWidget(self.vault_widget)

    def show_login(self):

        self.stack.setCurrentWidget(self.login_widget)

    def lock_vault(self):

        self.vault.lock()

        self.show_login()

def main():

    app = QApplication(sys.argv)

    app.setApplicationName("VaultKeeper")

    app.setOrganizationName("VaultKeeper")

    app.setOrganizationDomain("vaultkeeper.com")

    window = MainWindow()

    window.show()

    sys.exit(app.exec())

if __name__ == '__main__':

    main()
