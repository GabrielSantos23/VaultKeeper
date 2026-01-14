"""
Configuration Management for VaultKeeper.
Uses QSettings for persistence.
"""

from PySide6.QtCore import QSettings, QObject, Signal

class ConfigManager(QObject):
    """
    Manages application settings and configuration.
    Emits signals when settings change.
    """
    settings_changed = Signal(str, object) # key, new_value

    def __init__(self):
        super().__init__()
        self.settings = QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope, "VaultKeeper", "AppConfig")
        # Ensure we can write
        if not self.settings.isWritable():
            print("Warning: Settings file is not writable")
        
    def get(self, key: str, default=None):
        """Get a setting value."""
        return self.settings.value(key, default)
        
    def set(self, key: str, value):
        """Set a setting value."""
        self.settings.setValue(key, value)
        self.settings.sync() # Force write to disk
        self.settings_changed.emit(key, value)
        
    def get_auto_lock_timeout(self) -> int:
        """Get auto-lock timeout in seconds. 0 means never."""
        # Default to 15 minutes (900 seconds) if not set
        val = self.settings.value("general/auto_lock_timeout", 900)
        return int(val) if val is not None else 900
        
    def set_auto_lock_timeout(self, seconds: int):
        self.set("general/auto_lock_timeout", seconds)
        
    def get_clipboard_timeout(self) -> int:
        """Get clipboard clear timeout in seconds. 0 means never."""
        # Default to 60 seconds
        val = self.settings.value("general/clipboard_timeout", 60)
        return int(val) if val is not None else 60
        
    def set_clipboard_timeout(self, seconds: int):
        self.set("general/clipboard_timeout", seconds)
        
    def get_notifications_enabled(self) -> bool:
        # Default True. QSettings stores bools as strings or check state often, need careful conversion
        val = self.settings.value("general/notifications", True, type=bool)
        return val
        
    def set_notifications_enabled(self, enabled: bool):
        self.set("general/notifications", enabled)

# Global instance
_config = ConfigManager()

def get_config() -> ConfigManager:
    return _config
