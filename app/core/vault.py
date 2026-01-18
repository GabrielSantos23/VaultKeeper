"""
VaultKeeper - Vault Manager Module
Business logic for credential management
"""

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
    """Represents a folder for organizing credentials."""
    id: Optional[int]
    name: str
    icon: str = "folder"
    created_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class Credential:
    """Represents a stored credential."""
    id: Optional[int]
    domain: str
    username: str
    password: str  # Decrypted password
    notes: Optional[str] = None
    totp_secret: Optional[str] = None  # Base32-encoded TOTP secret
    backup_codes: Optional[str] = None  # 2FA backup/recovery codes
    is_favorite: bool = False
    folder_id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class VaultManager:
    """
    Manages the credential vault including CRUD operations,
    encryption/decryption, and database management.
    """
    
    def __init__(self, db_path: Optional[Path] = None, auth: Optional[AuthManager] = None):
        """
        Initialize the VaultManager.
        
        Args:
            db_path: Path to the SQLite database
            auth: AuthManager instance for authentication
        """
        if db_path is None:
            db_path = Path.home() / '.vaultkeeper' / 'vault.db'
        
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.crypto = CryptoManager()
        self.auth = auth or AuthManager()
        
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database with the required schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create folders table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS folders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    icon TEXT DEFAULT 'folder',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create vault table
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
            
            # Add is_favorite column if not exists (for existing databases)
            try:
                cursor.execute('ALTER TABLE vault ADD COLUMN is_favorite INTEGER DEFAULT 0')
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            # Add folder_id column if not exists (for existing databases)
            try:
                cursor.execute('ALTER TABLE vault ADD COLUMN folder_id INTEGER')
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            # Add totp_secret column if not exists (for existing databases)
            try:
                cursor.execute('ALTER TABLE vault ADD COLUMN totp_secret BLOB')
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            # Add backup_codes column if not exists (for existing databases)
            try:
                cursor.execute('ALTER TABLE vault ADD COLUMN backup_codes BLOB')
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            # Create index on domain for faster lookups
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_domain ON vault(domain)
            ''')
            
            # Create index on is_favorite for faster filtering
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_favorite ON vault(is_favorite)
            ''')
            
            # Create settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            ''')
            
            conn.commit()
    
    def _ensure_unlocked(self):
        """Ensure the vault is unlocked before operations."""
        if not self.auth.is_unlocked:
            raise ValueError("Vault is locked. Please unlock first.")
        
        # Derive encryption key if not set
        if not self.crypto.has_key:
            master_password = self.auth.master_password
            if master_password:
                self.crypto.derive_key(master_password)
    
    def _trigger_auto_sync(self):
        """Trigger Google Drive sync if auto-sync is enabled."""
        try:
            from .config import get_config
            from .gdrive import get_gdrive_manager
            
            config = get_config()
            gdrive = get_gdrive_manager()
            
            # Force auto-sync to ALWAYS be enabled as requested
            auto_sync_enabled = True
            
            # Debug logging
            print(f"[Auto-Sync] FORCED ENABLED. Connected: {gdrive.is_connected()}")
            
            if auto_sync_enabled and gdrive.is_connected():
                # Run sync in background thread to avoid blocking UI
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
            # Don't let sync errors break vault operations
            print(f"[Auto-Sync] Error: {e}")
            import traceback
            traceback.print_exc()
    
    def add_credential(self, domain: str, username: str, password: str, 
                       notes: Optional[str] = None, totp_secret: Optional[str] = None,
                       backup_codes: Optional[str] = None) -> int:
        """
        Add a new credential to the vault.
        
        Args:
            domain: The website domain
            username: The username/email
            password: The password (will be encrypted)
            notes: Optional notes
            totp_secret: Optional TOTP secret (base32 encoded)
            backup_codes: Optional 2FA backup/recovery codes
            
        Returns:
            The ID of the newly created credential
        """
        self._ensure_unlocked()
        self.auth.touch()
        
        # Encrypt sensitive fields
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
        
        # Trigger auto-sync
        self._trigger_auto_sync()
        
        return credential_id
    
    def get_credential(self, credential_id: int) -> Optional[Credential]:
        """
        Get a credential by ID.
        
        Args:
            credential_id: The credential ID
            
        Returns:
            The Credential object or None if not found
        """
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
        """
        Get all credentials for a domain.
        
        Args:
            domain: The website domain
            
        Returns:
            List of Credential objects
        """
        self._ensure_unlocked()
        self.auth.touch()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Search for exact match or subdomain match
            cursor.execute('''
                SELECT * FROM vault 
                WHERE domain = ? OR domain LIKE ?
                ORDER BY updated_at DESC
            ''', (domain, f'%.{domain}'))
            
            rows = cursor.fetchall()
            return [self._row_to_credential(dict(row)) for row in rows]
    
    def get_all_credentials(self) -> List[Credential]:
        """
        Get all credentials in the vault.
        
        Returns:
            List of Credential objects
        """
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
                    # Skip credentials that fail to decrypt (e.g., encrypted with different key)
                    print(f"Warning: Could not decrypt credential {row['id']}: {e}")
            
            return credentials
    
    def update_credential(self, credential_id: int, domain: Optional[str] = None,
                          username: Optional[str] = None, password: Optional[str] = None,
                          notes: Optional[str] = None, totp_secret: Optional[str] = None,
                          clear_totp: bool = False, backup_codes: Optional[str] = None,
                          clear_backup: bool = False) -> bool:
        """
        Update an existing credential.
        
        Args:
            credential_id: The credential ID
            domain: New domain (optional)
            username: New username (optional)
            password: New password (optional)
            notes: New notes (optional)
            totp_secret: New TOTP secret (optional)
            clear_totp: If True, clear the TOTP secret
            backup_codes: New backup codes (optional)
            clear_backup: If True, clear the backup codes
            
        Returns:
            True if the credential was updated
        """
        self._ensure_unlocked()
        self.auth.touch()
        
        # Build update query dynamically
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
        
        # Trigger auto-sync if updated
        if updated:
            self._trigger_auto_sync()
        
        return updated
    
    def delete_credential(self, credential_id: int) -> bool:
        """
        Delete a credential.
        
        Args:
            credential_id: The credential ID
            
        Returns:
            True if the credential was deleted
        """
        self._ensure_unlocked()
        self.auth.touch()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM vault WHERE id = ?', (credential_id,))
            conn.commit()
            deleted = cursor.rowcount > 0
        
        # Trigger auto-sync if deleted
        if deleted:
            self._trigger_auto_sync()
        
        return deleted
    
    def search_credentials(self, query: str) -> List[Credential]:
        """
        Search credentials by domain or username.
        
        Args:
            query: Search query
            
        Returns:
            List of matching Credential objects
        """
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
        """
        Convert a database row to a Credential object.
        
        Args:
            row: Database row as dict
            
        Returns:
            Credential object with decrypted password
        """
        # Get master password for decryption (needed to re-derive key with correct salt)
        master_password = self.auth.master_password
        
        # Decrypt password - pass master_password so it can derive key with the salt embedded in the data
        decrypted_password = self.crypto.decrypt(row['password'], master_password)
        
        # Decrypt notes if present
        decrypted_notes = None
        if row.get('notes'):
            try:
                decrypted_notes = self.crypto.decrypt(row['notes'], master_password)
            except:
                decrypted_notes = None
        
        # Decrypt TOTP secret if present
        decrypted_totp = None
        if row.get('totp_secret'):
            try:
                decrypted_totp = self.crypto.decrypt(row['totp_secret'], master_password)
            except:
                decrypted_totp = None
        
        # Decrypt backup codes if present
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
        """Lock the vault and clear sensitive data."""
        self.auth.lock()
        self.crypto.clear_key()
    
    def unlock(self, password: str) -> bool:
        """
        Unlock the vault with the master password.
        
        Args:
            password: The master password
            
        Returns:
            True if unlock successful
        """
        result = self.auth.unlock(password)
        if result:
            self.crypto.derive_key(password)
        return result
    
    def get_credential_count(self) -> int:
        """Get the total number of credentials in the vault."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM vault')
            return cursor.fetchone()[0]
    
    def export_credentials(self) -> List[Dict[str, Any]]:
        """
        Export all credentials as a list of dictionaries.
        Used for backup purposes.
        
        Returns:
            List of credential dictionaries
        """
        credentials = self.get_all_credentials()
        return [cred.to_dict() for cred in credentials]
    
    def import_credentials(self, credentials: List[Dict[str, Any]]) -> int:
        """
        Import credentials from a list of dictionaries.
        
        Args:
            credentials: List of credential dictionaries
            
        Returns:
            Number of credentials imported
        """
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
    
    # ===== FAVORITES METHODS =====
    
    def toggle_favorite(self, credential_id: int) -> bool:
        """
        Toggle the favorite status of a credential.
        
        Args:
            credential_id: The credential ID
            
        Returns:
            The new favorite status
        """
        self._ensure_unlocked()
        self.auth.touch()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Get current status
            cursor.execute('SELECT is_favorite FROM vault WHERE id = ?', (credential_id,))
            row = cursor.fetchone()
            if row is None:
                return False
            
            new_status = 0 if row[0] else 1
            cursor.execute('UPDATE vault SET is_favorite = ? WHERE id = ?', (new_status, credential_id))
            conn.commit()
            return bool(new_status)
    
    def set_favorite(self, credential_id: int, is_favorite: bool) -> bool:
        """
        Set the favorite status of a credential.
        
        Args:
            credential_id: The credential ID
            is_favorite: The new favorite status
            
        Returns:
            True if successful
        """
        self._ensure_unlocked()
        self.auth.touch()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE vault SET is_favorite = ? WHERE id = ?', 
                          (1 if is_favorite else 0, credential_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_favorites(self) -> List[Credential]:
        """
        Get all favorite credentials.
        
        Returns:
            List of favorite Credential objects
        """
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
    
    # ===== FOLDER METHODS =====
    
    def create_folder(self, name: str, icon: str = "folder") -> int:
        """
        Create a new folder.
        
        Args:
            name: The folder name
            icon: The icon name (default: 'folder')
            
        Returns:
            The ID of the newly created folder
        """
        self._ensure_unlocked()
        self.auth.touch()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO folders (name, icon) VALUES (?, ?)', (name, icon))
            conn.commit()
            return cursor.lastrowid
    
    def get_all_folders(self) -> List[Folder]:
        """
        Get all folders.
        
        Returns:
            List of Folder objects
        """
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
        """
        Delete a folder (credentials in folder will have folder_id set to NULL).
        
        Args:
            folder_id: The folder ID
            
        Returns:
            True if the folder was deleted
        """
        self._ensure_unlocked()
        self.auth.touch()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Set folder_id to NULL for all credentials in this folder
            cursor.execute('UPDATE vault SET folder_id = NULL WHERE folder_id = ?', (folder_id,))
            # Delete the folder
            cursor.execute('DELETE FROM folders WHERE id = ?', (folder_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def update_folder(self, folder_id: int, name: str, icon: str = None) -> bool:
        """
        Update a folder's name and/or icon.
        
        Args:
            folder_id: The folder ID
            name: The new folder name
            icon: The new icon name (optional)
            
        Returns:
            True if successful
        """
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
        """
        Set the folder for a credential.
        
        Args:
            credential_id: The credential ID
            folder_id: The folder ID (or None to remove from folder)
            
        Returns:
            True if successful
        """
        self._ensure_unlocked()
        self.auth.touch()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE vault SET folder_id = ? WHERE id = ?', (folder_id, credential_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_credentials_by_folder(self, folder_id: int) -> List[Credential]:
        """
        Get all credentials in a folder.
        
        Args:
            folder_id: The folder ID
            
        Returns:
            List of Credential objects
        """
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
