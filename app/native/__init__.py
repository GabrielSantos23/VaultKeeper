
__all__ = ['NativeMessagingHost', 'NativeHostInstaller']

def __getattr__(name):

    if name == 'NativeMessagingHost':

        from .host import NativeMessagingHost

        return NativeMessagingHost

    elif name == 'NativeHostInstaller':

        from .installer import NativeHostInstaller

        return NativeHostInstaller

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
