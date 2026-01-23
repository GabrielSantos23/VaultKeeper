#!/usr/bin/env python3
import sqlite3
import base64
from pathlib import Path

db_path = Path.home() / '.vaultkeeper' / 'vault.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute('SELECT id, title, content FROM secure_notes')
for row in cursor.fetchall():
    note_id, title, content = row
    content_type = type(content).__name__
    try:
        if isinstance(content, bytes):
            decoded = base64.b64decode(content.decode('utf-8'))
        else:
            decoded = base64.b64decode(content)
        print(f'Note {note_id} ({title}): content_type={content_type}, decoded_len={len(decoded)}, salt={decoded[:16].hex()}')
    except Exception as e:
        print(f'Note {note_id} ({title}): content_type={content_type}, ERROR: {e}')

conn.close()
