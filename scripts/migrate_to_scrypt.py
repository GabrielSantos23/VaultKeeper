import sqlite3
import os
import base64
import sys
import getpass
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.backends import default_backend

DB_NAME = "vault.db"
DEFAULT_DB_PATH = os.path.join(os.path.expanduser("~"), ".vaultkeeper", DB_NAME)

class LegacyCrypto:
    SALT_SIZE = 16
    NONCE_SIZE = 12
    KEY_SIZE = 32
    ITERATIONS = 600000

    def __init__(self):
        self._key: Optional[bytes] = None
        self._salt: Optional[bytes] = None

    def derive_key(self, master_password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.KEY_SIZE,
            salt=salt,
            iterations=self.ITERATIONS,
            backend=default_backend()
        )
        return kdf.derive(master_password.encode('utf-8'))

    def decrypt(self, encrypted_data: str, master_password: str) -> str:
        try:
            combined = base64.b64decode(encrypted_data.encode('utf-8'))
        except Exception:
            return None

        if len(combined) < self.SALT_SIZE + self.NONCE_SIZE:
             return None

        salt = combined[:self.SALT_SIZE]
        nonce = combined[self.SALT_SIZE:self.SALT_SIZE + self.NONCE_SIZE]
        ciphertext = combined[self.SALT_SIZE + self.NONCE_SIZE:]

        key = self.derive_key(master_password, salt)
        aesgcm = AESGCM(key)

        try:
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext.decode('utf-8')
        except Exception:
            raise ValueError("Decryption failed")

class ModernCrypto:
    SALT_SIZE = 16
    NONCE_SIZE = 12
    KEY_SIZE = 32
    N = 16384
    R = 8
    P = 1

    def __init__(self):
        self._key: Optional[bytes] = None
        self._salt: Optional[bytes] = None

    def derive_key(self, master_password: str, salt: bytes) -> bytes:
        kdf = Scrypt(
            salt=salt,
            length=self.KEY_SIZE,
            n=self.N,
            r=self.R,
            p=self.P,
            backend=default_backend()
        )
        return kdf.derive(master_password.encode('utf-8'))

    def encrypt(self, plaintext: str, master_password: str) -> str:
        salt = os.urandom(self.SALT_SIZE)
        key = self.derive_key(master_password, salt)
        
        nonce = os.urandom(self.NONCE_SIZE)
        aesgcm = AESGCM(key)
        
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
        
        combined = salt + nonce + ciphertext
        return base64.b64encode(combined).decode('utf-8')

def migrate_vault(db_path: str, password: str):
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return False

    print(f"Migrating database: {db_path}")
    
    backup_path = db_path + ".pbkdf2.bak"
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"Backup created at: {backup_path}")

    legacy = LegacyCrypto()
    modern = ModernCrypto()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    updates = 0
    errors = 0

    try:
        cursor.execute("SELECT id, password, notes, totp_secret, backup_codes FROM vault")
        rows = cursor.fetchall()
        print(f"Processing {len(rows)} credentials...")
        
        for row in rows:
            try:
                updates_in_row = {}
                
                plain_pass = legacy.decrypt(row['password'], password)
                updates_in_row['password'] = modern.encrypt(plain_pass, password)

                if row['notes']:
                    plain_notes = legacy.decrypt(row['notes'], password)
                    updates_in_row['notes'] = modern.encrypt(plain_notes, password)
                else:
                    updates_in_row['notes'] = None

                if row['totp_secret']:
                    plain_totp = legacy.decrypt(row['totp_secret'], password)
                    updates_in_row['totp_secret'] = modern.encrypt(plain_totp, password)
                else:
                    updates_in_row['totp_secret'] = None

                if row['backup_codes']:
                    plain_backup = legacy.decrypt(row['backup_codes'], password)
                    updates_in_row['backup_codes'] = modern.encrypt(plain_backup, password)
                else:
                    updates_in_row['backup_codes'] = None
                
                cursor.execute("""
                    UPDATE vault 
                    SET password=?, notes=?, totp_secret=?, backup_codes=?, updated_at=CURRENT_TIMESTAMP
                    WHERE id=?
                """, (
                    updates_in_row['password'],
                    updates_in_row['notes'],
                    updates_in_row['totp_secret'],
                    updates_in_row['backup_codes'],
                    row['id']
                ))
                updates += 1
                
            except ValueError:
                print(f"Failed to decrypt credential ID {row['id']} - Incorrect Password?")
                errors += 1
                raise Exception("Decryption failed. Wrong password likely.")

        cursor.execute("SELECT id, content FROM secure_notes")
        rows = cursor.fetchall()
        print(f"Processing {len(rows)} secure notes...")

        for row in rows:
            try:
                plain_content = legacy.decrypt(row['content'], password)
                new_content = modern.encrypt(plain_content, password)
                
                cursor.execute("UPDATE secure_notes SET content=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", 
                             (new_content, row['id']))
                updates += 1
            except Exception as e:
                print(f"Error note {row['id']}: {e}")
                errors += 1

        cursor.execute("SELECT id, card_number, cvv, notes FROM credit_cards")
        rows = cursor.fetchall()
        print(f"Processing {len(rows)} credit cards...")
        
        for row in rows:
            try:
                updates_in_row = {}
                
                plain_num = legacy.decrypt(row['card_number'], password)
                updates_in_row['card_number'] = modern.encrypt(plain_num, password)
                
                plain_cvv = legacy.decrypt(row['cvv'], password)
                updates_in_row['cvv'] = modern.encrypt(plain_cvv, password)
                
                if row['notes']:
                    plain_notes = legacy.decrypt(row['notes'], password)
                    updates_in_row['notes'] = modern.encrypt(plain_notes, password)
                else:
                    updates_in_row['notes'] = None
                    
                cursor.execute("""
                    UPDATE credit_cards
                    SET card_number=?, cvv=?, notes=?, updated_at=CURRENT_TIMESTAMP
                    WHERE id=?
                """, (
                    updates_in_row['card_number'],
                    updates_in_row['cvv'],
                    updates_in_row['notes'],
                    row['id']
                ))
                updates += 1
            except Exception as e:
                print(f"Error card {row['id']}: {e}")
                errors += 1

        conn.commit()
        print("Migration complete!")
        print(f"Total items processed: {updates}")
        if errors > 0:
            print(f"WARNING: {errors} items failed to decrypt/migrate.")
        
    except Exception as e:
        print(f"FATAL ERROR during migration: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
    
    return True

if __name__ == "__main__":
    print("VaultKeeper Migration Tool (PBKDF2 -> Scrypt)")
    print("---------------------------------------------")
    
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = DEFAULT_DB_PATH
        
    if not os.path.exists(path):
        print(f"DB not found at default location: {path}")
        path = input("Enter path to vault.db: ").strip('"')
    
    pwd = getpass.getpass("Enter Master Password: ")
    
    if migrate_vault(path, pwd):
        print("Successfully migrated to Scrypt!")
    else:
        print("Migration failed.")
