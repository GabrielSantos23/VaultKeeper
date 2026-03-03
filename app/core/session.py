
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

    return Config.get_config_dir() / '.session'

def _get_machine_key() -> bytes:

    import socket

    import getpass

    unique_id = f"{getpass.getuser()}@{socket.gethostname()}"

    key_material = hashlib.sha256(unique_id.encode()).digest()

    return base64.urlsafe_b64encode(key_material)

def save_session(vault_path: Path, entries: List[Dict[str, Any]], metadata: Dict[str, Any]) -> None:

    session_data = {

        'vault_path': str(vault_path),

        'entries': entries,

        'metadata': metadata,

        'pid': os.getpid()

    }

    fernet = Fernet(_get_machine_key())

    encrypted = fernet.encrypt(json.dumps(session_data).encode())

    session_file = _get_session_file()

    session_file.parent.mkdir(parents=True, exist_ok=True)

    with open(session_file, 'wb') as f:

        f.write(encrypted)

def load_session() -> Optional[Dict[str, Any]]:

    session_file = _get_session_file()

    if not session_file.exists():

        return None

    try:

        with open(session_file, 'rb') as f:

            encrypted = f.read()

        fernet = Fernet(_get_machine_key())

        decrypted = fernet.decrypt(encrypted)

        return json.loads(decrypted)

    except Exception:

        return None

def clear_session() -> None:

    session_file = _get_session_file()

    if session_file.exists():

        session_file.unlink()

def is_session_valid() -> bool:

    session = load_session()

    if not session:

        return False

    pid = session.get('pid')

    if pid:

        try:

            os.kill(pid, 0)

            return True

        except OSError:

            clear_session()

            return False

    return False
