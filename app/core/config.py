from PySide6.QtCore import QSettings, QObject, Signal
from pathlib import Path
import os
import sys

GITHUB_REPO = "GabrielSantos23/VaultKeeper"

class ConfigManager(QObject):
    settings_changed = Signal(str, object)

    def __init__(self):
        super().__init__()
        self.settings = QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope, "VaultKeeper", "AppConfig")
        if not self.settings.isWritable():
            print("Warning: Settings file is not writable")

    def get(self, key: str, default=None):
        return self.settings.value(key, default)

    def set(self, key: str, value):
        self.settings.setValue(key, value)
        self.settings.sync()
        self.settings_changed.emit(key, value)

    def get_bool(self, key: str, default: bool = False) -> bool:
        return self.settings.value(key, default, type=bool)

    def get_auto_lock_timeout(self) -> int:
        val = self.settings.value("general/auto_lock_timeout", 900)
        return int(val) if val is not None else 900

    def set_auto_lock_timeout(self, seconds: int):
        self.set("general/auto_lock_timeout", seconds)

    def get_clipboard_timeout(self) -> int:
        val = self.settings.value("general/clipboard_timeout", 60)
        return int(val) if val is not None else 60

    def set_clipboard_timeout(self, seconds: int):
        self.set("general/clipboard_timeout", seconds)

    def get_notifications_enabled(self) -> bool:
        val = self.settings.value("general/notifications", True, type=bool)
        return val

    def set_notifications_enabled(self, enabled: bool):
        self.set("general/notifications", enabled)

    def get_local_sync_enabled(self) -> bool:
        return self.settings.value("general/local_sync", True, type=bool)

    def set_local_sync_enabled(self, enabled: bool):
        self.set("general/local_sync", enabled)

class Config:
    @staticmethod
    def get_config_dir() -> Path:
        """Standardized way to get the config directory across platforms."""
        if sys.platform == 'win32':
            return Path(os.environ['USERPROFILE']) / '.vaultkeeper'
        else:
            return Path.home() / '.vaultkeeper'

_config = ConfigManager()

def get_config() -> ConfigManager:
    return _config
