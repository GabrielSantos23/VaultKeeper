"""
VaultKeeper Session Management
Allows sharing unlocked vault state between main app and native messaging host
"""
import os
import json
import pickle
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Any
from cryptography.fernet import Fernet
import base64
import hashlib

from .config import Config


def _get_session_file() -> Path:
    """Get path to session file"""
    return Config.get_config_dir() / '.session'


def _get_machine_key() -> bytes:
    """Generate a machine-specific key for session encryption"""
    # Use a combination of username and hostname for machine-specific key
    import socket
    import getpass
    
    unique_id = f"{getpass.getuser()}@{socket.gethostname()}"
    key_material = hashlib.sha256(unique_id.encode()).digest()
    return base64.urlsafe_b64encode(key_material)


def save_session(vault_path: Path, entries: List[Dict[str, Any]], metadata: Dict[str, Any]) -> None:
    """
    Save current vault session for native host to read
    
    Args:
        vault_path: Path to vault file
        entries: List of password entries as dicts
        metadata: Vault metadata
    """
    session_data = {
        'vault_path': str(vault_path),
        'entries': entries,
        'metadata': metadata,
        'pid': os.getpid()
    }
    
    # Encrypt session data
    fernet = Fernet(_get_machine_key())
    encrypted = fernet.encrypt(json.dumps(session_data).encode())
    
    # Save to file
    session_file = _get_session_file()
    session_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(session_file, 'wb') as f:
        f.write(encrypted)


def load_session() -> Optional[Dict[str, Any]]:
    """
    Load session saved by main app
    
    Returns:
        Session data dict or None if no valid session
    """
    session_file = _get_session_file()
    
    if not session_file.exists():
        return None
    
    try:
        with open(session_file, 'rb') as f:
            encrypted = f.read()
        
        # Decrypt
        fernet = Fernet(_get_machine_key())
        decrypted = fernet.decrypt(encrypted)
        
        return json.loads(decrypted)
    
    except Exception:
        return None


def clear_session() -> None:
    """Clear session file (when vault is locked)"""
    session_file = _get_session_file()
    
    if session_file.exists():
        session_file.unlink()


def is_session_valid() -> bool:
    """Check if a valid session exists"""
    session = load_session()
    
    if not session:
        return False
    
    # Check if the process that created the session is still running
    pid = session.get('pid')
    if pid:
        try:
            # Check if process exists (doesn't kill it)
            os.kill(pid, 0)
            return True
        except OSError:
            # Process not running, clear session
            clear_session()
            return False
    
    return False
