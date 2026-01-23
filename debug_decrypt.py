#!/usr/bin/env python3
import sqlite3
import base64
import sys
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.backends import default_backend

SALT_SIZE = 16
NONCE_SIZE = 12

def derive_key(password: str, salt: bytes) -> bytes:
    kdf = Scrypt(
        salt=salt,
        length=32,
        n=16384,
        r=8,
        p=1,
        backend=default_backend()
    )
    return kdf.derive(password.encode('utf-8'))

def decrypt(encrypted_data: str, password: str) -> str:
    combined = base64.b64decode(encrypted_data)
    salt = combined[:SALT_SIZE]
    nonce = combined[SALT_SIZE:SALT_SIZE + NONCE_SIZE]
    ciphertext = combined[SALT_SIZE + NONCE_SIZE:]
    
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode('utf-8')

if len(sys.argv) < 2:
    print("Usage: python debug_decrypt.py <master_password>")
    sys.exit(1)

password = sys.argv[1]

db_path = Path.home() / '.vaultkeeper' / 'vault.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute('SELECT id, title, content FROM secure_notes')
for row in cursor.fetchall():
    note_id, title, content = row
    try:
        decrypted = decrypt(content, password)
        print(f'Note {note_id} ({title}): OK - "{decrypted[:50]}..."')
    except Exception as e:
        print(f'Note {note_id} ({title}): FAILED - {e}')

conn.close()
