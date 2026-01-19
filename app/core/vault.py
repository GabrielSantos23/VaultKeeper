
import sqlite3

import threading

from pathlib import Path

from typing import Optional, List, Dict, Any

from datetime import datetime

from dataclasses import dataclass, asdict

from .crypto import CryptoManager

from .auth import AuthManager

@dataclass

class Folder:

    id: Optional[int]

    name: str

    icon: str = "folder"

    created_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:

        return asdict(self)

@dataclass

class Credential:

    id: Optional[int]

    domain: str

    username: str

    password: str

    notes: Optional[str] = None

    totp_secret: Optional[str] = None

    backup_codes: Optional[str] = None

    is_favorite: bool = False

    folder_id: Optional[int] = None

    created_at: Optional[str] = None

    updated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:

        return asdict(self)

@dataclass

class SecureNote:

    id: Optional[int]

    title: str

    content: str

    is_favorite: bool = False

    folder_id: Optional[int] = None

    created_at: Optional[str] = None

    updated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:

        return asdict(self)

@dataclass

class CreditCard:

    id: Optional[int]

    title: str

    cardholder_name: str

    card_number: str

    expiry_date: str

    cvv: str

    notes: Optional[str] = None

    is_favorite: bool = False

    folder_id: Optional[int] = None

    created_at: Optional[str] = None

    updated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:

        return asdict(self)

class VaultManager:

    def __init__(self, db_path: Optional[Path] = None, auth: Optional[AuthManager] = None):

        if db_path is None:

            db_path = Path.home() / '.vaultkeeper' / 'vault.db'

        self.db_path = db_path

        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.crypto = CryptoManager()

        self.auth = auth or AuthManager()

        self._init_database()

    def _init_database(self):

        with sqlite3.connect(self.db_path) as conn:

            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS folders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    icon TEXT DEFAULT 'folder',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vault (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain TEXT NOT NULL,
                    username TEXT NOT NULL,
                    password BLOB NOT NULL,
                    notes BLOB,
                    is_favorite INTEGER DEFAULT 0,
                    folder_id INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (folder_id) REFERENCES folders(id)
                )
            ''')

            try:

                cursor.execute('ALTER TABLE vault ADD COLUMN is_favorite INTEGER DEFAULT 0')

            except sqlite3.OperationalError:

                pass

            try:

                cursor.execute('ALTER TABLE vault ADD COLUMN folder_id INTEGER')

            except sqlite3.OperationalError:

                pass

            try:

                cursor.execute('ALTER TABLE vault ADD COLUMN totp_secret BLOB')

            except sqlite3.OperationalError:

                pass

            try:

                cursor.execute('ALTER TABLE vault ADD COLUMN backup_codes BLOB')

            except sqlite3.OperationalError:

                pass

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_domain ON vault(domain)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_favorite ON vault(is_favorite)
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS secure_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content BLOB NOT NULL,
                    is_favorite INTEGER DEFAULT 0,
                    folder_id INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (folder_id) REFERENCES folders(id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS credit_cards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    cardholder_name TEXT NOT NULL,
                    card_number BLOB NOT NULL,
                    expiry_date TEXT NOT NULL,
                    cvv BLOB NOT NULL,
                    notes BLOB,
                    is_favorite INTEGER DEFAULT 0,
                    folder_id INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (folder_id) REFERENCES folders(id)
                )
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_secure_notes_favorite ON secure_notes(is_favorite)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_credit_cards_favorite ON credit_cards(is_favorite)
            ''')

            conn.commit()

    def _ensure_unlocked(self):

        if not self.auth.is_unlocked:

            raise ValueError("Vault is locked. Please unlock first.")

        if not self.crypto.has_key:

            master_password = self.auth.master_password

            if master_password:

                self.crypto.derive_key(master_password)

    def _trigger_auto_sync(self):

        try:

            from .config import get_config

            from .gdrive import get_gdrive_manager

            config = get_config()

            gdrive = get_gdrive_manager()

            auto_sync_enabled = True

            print(f"[Auto-Sync] FORCED ENABLED. Connected: {gdrive.is_connected()}")

            if auto_sync_enabled and gdrive.is_connected():

                def sync_in_background():

                    try:

                        print("[Auto-Sync] Starting upload...")

                        gdrive.upload_vault()

                        print("[Auto-Sync] Vault synced to Google Drive successfully!")

                    except Exception as e:

                        print(f"[Auto-Sync] Failed to sync: {e}")

                        import traceback

                        traceback.print_exc()

                thread = threading.Thread(target=sync_in_background, daemon=True)

                thread.start()

            else:

                if not auto_sync_enabled:

                    print("[Auto-Sync] Skipped - auto-sync is disabled")

                if not gdrive.is_connected():

                    print("[Auto-Sync] Skipped - not connected to Google Drive")

        except Exception as e:

            print(f"[Auto-Sync] Error: {e}")

            import traceback

            traceback.print_exc()

    def add_credential(self, domain: str, username: str, password: str,

                       notes: Optional[str] = None, totp_secret: Optional[str] = None,

                       backup_codes: Optional[str] = None) -> int:

        self._ensure_unlocked()

        self.auth.touch()

        encrypted_password = self.crypto.encrypt(password)

        encrypted_notes = self.crypto.encrypt(notes) if notes else None

        encrypted_totp = self.crypto.encrypt(totp_secret) if totp_secret else None

        encrypted_backup = self.crypto.encrypt(backup_codes) if backup_codes else None

        with sqlite3.connect(self.db_path) as conn:

            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO vault (domain, username, password, notes, totp_secret, backup_codes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (domain, username, encrypted_password, encrypted_notes, encrypted_totp, encrypted_backup))

            conn.commit()

            credential_id = cursor.lastrowid

        self._trigger_auto_sync()

        return credential_id

    def get_credential(self, credential_id: int) -> Optional[Credential]:

        self._ensure_unlocked()

        self.auth.touch()

        with sqlite3.connect(self.db_path) as conn:

            conn.row_factory = sqlite3.Row

            cursor = conn.cursor()

            cursor.execute('SELECT * FROM vault WHERE id = ?', (credential_id,))

            row = cursor.fetchone()

            if row:

                return self._row_to_credential(dict(row))

            return None

    def get_credentials_by_domain(self, domain: str) -> List[Credential]:

        self._ensure_unlocked()

        self.auth.touch()

        with sqlite3.connect(self.db_path) as conn:

            conn.row_factory = sqlite3.Row

            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM vault
                WHERE domain = ? OR domain LIKE ?
                ORDER BY updated_at DESC
            ''', (domain, f'%.{domain}'))

            rows = cursor.fetchall()

            return [self._row_to_credential(dict(row)) for row in rows]

    def get_all_credentials(self) -> List[Credential]:

        self._ensure_unlocked()

        self.auth.touch()

        with sqlite3.connect(self.db_path) as conn:

            conn.row_factory = sqlite3.Row

            cursor = conn.cursor()

            cursor.execute('SELECT * FROM vault ORDER BY domain, username')

            rows = cursor.fetchall()

            credentials = []

            for row in rows:

                try:

                    cred = self._row_to_credential(dict(row))

                    credentials.append(cred)

                except Exception as e:

                    print(f"Warning: Could not decrypt credential {row['id']}: {e}")

            return credentials

    def update_credential(self, credential_id: int, domain: Optional[str] = None,

                          username: Optional[str] = None, password: Optional[str] = None,

                          notes: Optional[str] = None, totp_secret: Optional[str] = None,

                          clear_totp: bool = False, backup_codes: Optional[str] = None,

                          clear_backup: bool = False) -> bool:

        self._ensure_unlocked()

        self.auth.touch()

        updates = []

        params = []

        if domain is not None:

            updates.append('domain = ?')

            params.append(domain)

        if username is not None:

            updates.append('username = ?')

            params.append(username)

        if password is not None:

            updates.append('password = ?')

            params.append(self.crypto.encrypt(password))

        if notes is not None:

            updates.append('notes = ?')

            params.append(self.crypto.encrypt(notes) if notes else None)

        if clear_totp:

            updates.append('totp_secret = ?')

            params.append(None)

        elif totp_secret is not None:

            updates.append('totp_secret = ?')

            params.append(self.crypto.encrypt(totp_secret))

        if clear_backup:

            updates.append('backup_codes = ?')

            params.append(None)

        elif backup_codes is not None:

            updates.append('backup_codes = ?')

            params.append(self.crypto.encrypt(backup_codes))

        if not updates:

            return False

        updates.append('updated_at = CURRENT_TIMESTAMP')

        params.append(credential_id)

        with sqlite3.connect(self.db_path) as conn:

            cursor = conn.cursor()

            cursor.execute(f'''
                UPDATE vault SET {', '.join(updates)} WHERE id = ?
            ''', params)

            conn.commit()

            updated = cursor.rowcount > 0

        if updated:

            self._trigger_auto_sync()

        return updated

    def delete_credential(self, credential_id: int) -> bool:

        self._ensure_unlocked()

        self.auth.touch()

        with sqlite3.connect(self.db_path) as conn:

            cursor = conn.cursor()

            cursor.execute('DELETE FROM vault WHERE id = ?', (credential_id,))

            conn.commit()

            deleted = cursor.rowcount > 0

        if deleted:

            self._trigger_auto_sync()

        return deleted

    def search_credentials(self, query: str) -> List[Credential]:

        self._ensure_unlocked()

        self.auth.touch()

        with sqlite3.connect(self.db_path) as conn:

            conn.row_factory = sqlite3.Row

            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM vault
                WHERE domain LIKE ? OR username LIKE ?
                ORDER BY domain, username
            ''', (f'%{query}%', f'%{query}%'))

            rows = cursor.fetchall()

            return [self._row_to_credential(dict(row)) for row in rows]

    def _row_to_credential(self, row: Dict[str, Any]) -> Credential:

        master_password = self.auth.master_password

        decrypted_password = self.crypto.decrypt(row['password'], master_password)

        decrypted_notes = None

        if row.get('notes'):

            try:

                decrypted_notes = self.crypto.decrypt(row['notes'], master_password)

            except:

                decrypted_notes = None

        decrypted_totp = None

        if row.get('totp_secret'):

            try:

                decrypted_totp = self.crypto.decrypt(row['totp_secret'], master_password)

            except:

                decrypted_totp = None

        decrypted_backup = None

        if row.get('backup_codes'):

            try:

                decrypted_backup = self.crypto.decrypt(row['backup_codes'], master_password)

            except:

                decrypted_backup = None

        return Credential(

            id=row['id'],

            domain=row['domain'],

            username=row['username'],

            password=decrypted_password,

            notes=decrypted_notes,

            totp_secret=decrypted_totp,

            backup_codes=decrypted_backup,

            is_favorite=bool(row.get('is_favorite', 0)),

            folder_id=row.get('folder_id'),

            created_at=row.get('created_at'),

            updated_at=row.get('updated_at')

        )

    def lock(self):

        self.auth.lock()

        self.crypto.clear_key()

    def unlock(self, password: str) -> bool:

        result = self.auth.unlock(password)

        if result:

            self.crypto.derive_key(password)

        return result

    def get_credential_count(self) -> int:

        with sqlite3.connect(self.db_path) as conn:

            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM vault')

            return cursor.fetchone()[0]

    def export_credentials(self) -> List[Dict[str, Any]]:

        credentials = self.get_all_credentials()

        return [cred.to_dict() for cred in credentials]

    def import_credentials(self, credentials: List[Dict[str, Any]]) -> int:

        count = 0

        for cred in credentials:

            try:

                self.add_credential(

                    domain=cred['domain'],

                    username=cred['username'],

                    password=cred['password'],

                    notes=cred.get('notes')

                )

                count += 1

            except Exception as e:

                print(f"Failed to import credential: {e}")

        return count

    def toggle_favorite(self, credential_id: int) -> bool:

        self._ensure_unlocked()

        self.auth.touch()

        with sqlite3.connect(self.db_path) as conn:

            cursor = conn.cursor()

            cursor.execute('SELECT is_favorite FROM vault WHERE id = ?', (credential_id,))

            row = cursor.fetchone()

            if row is None:

                return False

            new_status = 0 if row[0] else 1

            cursor.execute('UPDATE vault SET is_favorite = ? WHERE id = ?', (new_status, credential_id))

            conn.commit()

            return bool(new_status)

    def set_favorite(self, credential_id: int, is_favorite: bool) -> bool:

        self._ensure_unlocked()

        self.auth.touch()

        with sqlite3.connect(self.db_path) as conn:

            cursor = conn.cursor()

            cursor.execute('UPDATE vault SET is_favorite = ? WHERE id = ?',

                          (1 if is_favorite else 0, credential_id))

            conn.commit()

            return cursor.rowcount > 0

    def get_favorites(self) -> List[Credential]:

        self._ensure_unlocked()

        self.auth.touch()

        with sqlite3.connect(self.db_path) as conn:

            conn.row_factory = sqlite3.Row

            cursor = conn.cursor()

            cursor.execute('SELECT * FROM vault WHERE is_favorite = 1 ORDER BY domain, username')

            rows = cursor.fetchall()

            credentials = []

            for row in rows:

                try:

                    cred = self._row_to_credential(dict(row))

                    credentials.append(cred)

                except Exception as e:

                    print(f"Warning: Could not decrypt credential {row['id']}: {e}")

            return credentials

    def create_folder(self, name: str, icon: str = "folder") -> int:

        self._ensure_unlocked()

        self.auth.touch()

        with sqlite3.connect(self.db_path) as conn:

            cursor = conn.cursor()

            cursor.execute('INSERT INTO folders (name, icon) VALUES (?, ?)', (name, icon))

            conn.commit()

            return cursor.lastrowid

    def get_all_folders(self) -> List[Folder]:

        self._ensure_unlocked()

        self.auth.touch()

        with sqlite3.connect(self.db_path) as conn:

            conn.row_factory = sqlite3.Row

            cursor = conn.cursor()

            cursor.execute('SELECT * FROM folders ORDER BY name')

            rows = cursor.fetchall()

            return [Folder(

                id=row['id'],

                name=row['name'],

                icon=row['icon'],

                created_at=row['created_at'] if 'created_at' in row.keys() else None

            ) for row in rows]

    def delete_folder(self, folder_id: int) -> bool:

        self._ensure_unlocked()

        self.auth.touch()

        with sqlite3.connect(self.db_path) as conn:

            cursor = conn.cursor()

            cursor.execute('UPDATE vault SET folder_id = NULL WHERE folder_id = ?', (folder_id,))

            cursor.execute('DELETE FROM folders WHERE id = ?', (folder_id,))

            conn.commit()

            return cursor.rowcount > 0

    def update_folder(self, folder_id: int, name: str, icon: str = None) -> bool:

        self._ensure_unlocked()

        self.auth.touch()

        with sqlite3.connect(self.db_path) as conn:

            cursor = conn.cursor()

            if icon:

                cursor.execute('UPDATE folders SET name = ?, icon = ? WHERE id = ?',

                              (name, icon, folder_id))

            else:

                cursor.execute('UPDATE folders SET name = ? WHERE id = ?',

                              (name, folder_id))

            conn.commit()

            return cursor.rowcount > 0

    def set_credential_folder(self, credential_id: int, folder_id: Optional[int]) -> bool:

        self._ensure_unlocked()

        self.auth.touch()

        with sqlite3.connect(self.db_path) as conn:

            cursor = conn.cursor()

            cursor.execute('UPDATE vault SET folder_id = ? WHERE id = ?', (folder_id, credential_id))

            conn.commit()

            return cursor.rowcount > 0

    def get_credentials_by_folder(self, folder_id: int) -> List[Credential]:

        self._ensure_unlocked()

        self.auth.touch()

        with sqlite3.connect(self.db_path) as conn:

            conn.row_factory = sqlite3.Row

            cursor = conn.cursor()

            cursor.execute('SELECT * FROM vault WHERE folder_id = ? ORDER BY domain, username',

                          (folder_id,))

            rows = cursor.fetchall()

            credentials = []

            for row in rows:

                try:

                    cred = self._row_to_credential(dict(row))

                    credentials.append(cred)

                except Exception as e:

                    print(f"Warning: Could not decrypt credential {row['id']}: {e}")

            return credentials

    def add_secure_note(self, title: str, content: str, folder_id: Optional[int] = None) -> int:

        self._ensure_unlocked()

        self.auth.touch()

        encrypted_content = self.crypto.encrypt(content)

        with sqlite3.connect(self.db_path) as conn:

            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO secure_notes (title, content, folder_id)
                VALUES (?, ?, ?)
            ''', (title, encrypted_content, folder_id))

            conn.commit()

            note_id = cursor.lastrowid

        self._trigger_auto_sync()

        return note_id

    def get_secure_note(self, note_id: int) -> Optional[SecureNote]:

        self._ensure_unlocked()

        self.auth.touch()

        with sqlite3.connect(self.db_path) as conn:

            conn.row_factory = sqlite3.Row

            cursor = conn.cursor()

            cursor.execute('SELECT * FROM secure_notes WHERE id = ?', (note_id,))

            row = cursor.fetchone()

            if row:

                return self._row_to_secure_note(dict(row))

            return None

    def get_all_secure_notes(self) -> List[SecureNote]:

        self._ensure_unlocked()

        self.auth.touch()

        with sqlite3.connect(self.db_path) as conn:

            conn.row_factory = sqlite3.Row

            cursor = conn.cursor()

            cursor.execute('SELECT * FROM secure_notes ORDER BY title')

            rows = cursor.fetchall()

            notes = []

            for row in rows:

                try:

                    note = self._row_to_secure_note(dict(row))

                    notes.append(note)

                except Exception as e:

                    print(f"Warning: Could not decrypt note {row['id']}: {e}")

            return notes

    def update_secure_note(self, note_id: int, title: Optional[str] = None,

                           content: Optional[str] = None) -> bool:

        self._ensure_unlocked()

        self.auth.touch()

        updates = []

        params = []

        if title is not None:

            updates.append('title = ?')

            params.append(title)

        if content is not None:

            updates.append('content = ?')

            params.append(self.crypto.encrypt(content))

        if not updates:

            return False

        updates.append('updated_at = CURRENT_TIMESTAMP')

        params.append(note_id)

        with sqlite3.connect(self.db_path) as conn:

            cursor = conn.cursor()

            cursor.execute(f'''
                UPDATE secure_notes SET {', '.join(updates)} WHERE id = ?
            ''', params)

            conn.commit()

            updated = cursor.rowcount > 0

        if updated:

            self._trigger_auto_sync()

        return updated

    def delete_secure_note(self, note_id: int) -> bool:

        self._ensure_unlocked()

        self.auth.touch()

        with sqlite3.connect(self.db_path) as conn:

            cursor = conn.cursor()

            cursor.execute('DELETE FROM secure_notes WHERE id = ?', (note_id,))

            conn.commit()

            deleted = cursor.rowcount > 0

        if deleted:

            self._trigger_auto_sync()

        return deleted

    def toggle_secure_note_favorite(self, note_id: int) -> bool:

        self._ensure_unlocked()

        self.auth.touch()

        with sqlite3.connect(self.db_path) as conn:

            cursor = conn.cursor()

            cursor.execute('SELECT is_favorite FROM secure_notes WHERE id = ?', (note_id,))

            row = cursor.fetchone()

            if row is None:

                return False

            new_status = 0 if row[0] else 1

            cursor.execute('UPDATE secure_notes SET is_favorite = ? WHERE id = ?', (new_status, note_id))

            conn.commit()

            return bool(new_status)

    def _row_to_secure_note(self, row: Dict[str, Any]) -> SecureNote:

        master_password = self.auth.master_password

        decrypted_content = self.crypto.decrypt(row['content'], master_password)

        return SecureNote(

            id=row['id'],

            title=row['title'],

            content=decrypted_content,

            is_favorite=bool(row.get('is_favorite', 0)),

            folder_id=row.get('folder_id'),

            created_at=row.get('created_at'),

            updated_at=row.get('updated_at')

        )

    def add_credit_card(self, title: str, cardholder_name: str, card_number: str,

                        expiry_date: str, cvv: str, notes: Optional[str] = None,

                        folder_id: Optional[int] = None) -> int:

        self._ensure_unlocked()

        self.auth.touch()

        encrypted_number = self.crypto.encrypt(card_number)

        encrypted_cvv = self.crypto.encrypt(cvv)

        encrypted_notes = self.crypto.encrypt(notes) if notes else None

        with sqlite3.connect(self.db_path) as conn:

            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO credit_cards (title, cardholder_name, card_number, expiry_date, cvv, notes, folder_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (title, cardholder_name, encrypted_number, expiry_date, encrypted_cvv, encrypted_notes, folder_id))

            conn.commit()

            card_id = cursor.lastrowid

        self._trigger_auto_sync()

        return card_id

    def get_credit_card(self, card_id: int) -> Optional[CreditCard]:

        self._ensure_unlocked()

        self.auth.touch()

        with sqlite3.connect(self.db_path) as conn:

            conn.row_factory = sqlite3.Row

            cursor = conn.cursor()

            cursor.execute('SELECT * FROM credit_cards WHERE id = ?', (card_id,))

            row = cursor.fetchone()

            if row:

                return self._row_to_credit_card(dict(row))

            return None

    def get_all_credit_cards(self) -> List[CreditCard]:

        self._ensure_unlocked()

        self.auth.touch()

        with sqlite3.connect(self.db_path) as conn:

            conn.row_factory = sqlite3.Row

            cursor = conn.cursor()

            cursor.execute('SELECT * FROM credit_cards ORDER BY title')

            rows = cursor.fetchall()

            cards = []

            for row in rows:

                try:

                    card = self._row_to_credit_card(dict(row))

                    cards.append(card)

                except Exception as e:

                    print(f"Warning: Could not decrypt card {row['id']}: {e}")

            return cards

    def update_credit_card(self, card_id: int, title: Optional[str] = None,

                           cardholder_name: Optional[str] = None,

                           card_number: Optional[str] = None,

                           expiry_date: Optional[str] = None,

                           cvv: Optional[str] = None,

                           notes: Optional[str] = None) -> bool:

        self._ensure_unlocked()

        self.auth.touch()

        updates = []

        params = []

        if title is not None:

            updates.append('title = ?')

            params.append(title)

        if cardholder_name is not None:

            updates.append('cardholder_name = ?')

            params.append(cardholder_name)

        if card_number is not None:

            updates.append('card_number = ?')

            params.append(self.crypto.encrypt(card_number))

        if expiry_date is not None:

            updates.append('expiry_date = ?')

            params.append(expiry_date)

        if cvv is not None:

            updates.append('cvv = ?')

            params.append(self.crypto.encrypt(cvv))

        if notes is not None:

            updates.append('notes = ?')

            params.append(self.crypto.encrypt(notes) if notes else None)

        if not updates:

            return False

        updates.append('updated_at = CURRENT_TIMESTAMP')

        params.append(card_id)

        with sqlite3.connect(self.db_path) as conn:

            cursor = conn.cursor()

            cursor.execute(f'''
                UPDATE credit_cards SET {', '.join(updates)} WHERE id = ?
            ''', params)

            conn.commit()

            updated = cursor.rowcount > 0

        if updated:

            self._trigger_auto_sync()

        return updated

    def delete_credit_card(self, card_id: int) -> bool:

        self._ensure_unlocked()

        self.auth.touch()

        with sqlite3.connect(self.db_path) as conn:

            cursor = conn.cursor()

            cursor.execute('DELETE FROM credit_cards WHERE id = ?', (card_id,))

            conn.commit()

            deleted = cursor.rowcount > 0

        if deleted:

            self._trigger_auto_sync()

        return deleted

    def toggle_credit_card_favorite(self, card_id: int) -> bool:

        self._ensure_unlocked()

        self.auth.touch()

        with sqlite3.connect(self.db_path) as conn:

            cursor = conn.cursor()

            cursor.execute('SELECT is_favorite FROM credit_cards WHERE id = ?', (card_id,))

            row = cursor.fetchone()

            if row is None:

                return False

            new_status = 0 if row[0] else 1

            cursor.execute('UPDATE credit_cards SET is_favorite = ? WHERE id = ?', (new_status, card_id))

            conn.commit()

            return bool(new_status)

    def _row_to_credit_card(self, row: Dict[str, Any]) -> CreditCard:

        master_password = self.auth.master_password

        decrypted_number = self.crypto.decrypt(row['card_number'], master_password)

        decrypted_cvv = self.crypto.decrypt(row['cvv'], master_password)

        decrypted_notes = None

        if row.get('notes'):

            try:

                decrypted_notes = self.crypto.decrypt(row['notes'], master_password)

            except:

                decrypted_notes = None

        return CreditCard(

            id=row['id'],

            title=row['title'],

            cardholder_name=row['cardholder_name'],

            card_number=decrypted_number,

            expiry_date=row['expiry_date'],

            cvv=decrypted_cvv,

            notes=decrypted_notes,

            is_favorite=bool(row.get('is_favorite', 0)),

            folder_id=row.get('folder_id'),

            created_at=row.get('created_at'),

            updated_at=row.get('updated_at')

        )
