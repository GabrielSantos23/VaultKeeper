# VaultKeeper Native Messaging Module
# Note: imports are kept minimal to allow installer to run without full dependencies

__all__ = ['NativeMessagingHost', 'NativeHostInstaller']

def __getattr__(name):
    """Lazy loading of modules to avoid import errors when dependencies are missing."""
    if name == 'NativeMessagingHost':
        from .host import NativeMessagingHost
        return NativeMessagingHost
    elif name == 'NativeHostInstaller':
        from .installer import NativeHostInstaller
        return NativeHostInstaller
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
