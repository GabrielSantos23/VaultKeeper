
import os

import base64

from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from cryptography.hazmat.primitives import hashes

from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.backends import default_backend

def derive_key_static(password: str, salt: bytes) -> bytes:
    kdf = Scrypt(
        salt=salt,
        length=32,
        n=2**14, 
        r=8,
        p=1,
        backend=default_backend()
    )
    return kdf.derive(password.encode())

class CryptoManager:

    SALT_SIZE = 16
    NONCE_SIZE = 12
    KEY_SIZE = 32
    
    N = 16384
    R = 8
    P = 1

    def __init__(self):
        self._key: Optional[bytes] = None
        self._salt: Optional[bytes] = None

    def derive_key(self, master_password: str, salt: Optional[bytes] = None) -> bytes:
        if salt is None:
            salt = os.urandom(self.SALT_SIZE)
        self._salt = salt

        kdf = Scrypt(
            salt=salt,
            length=self.KEY_SIZE,
            n=self.N,
            r=self.R,
            p=self.P,
            backend=default_backend()
        )

        self._key = kdf.derive(master_password.encode('utf-8'))
        return self._key

    def set_key(self, key: bytes, salt: bytes):

        self._key = key

        self._salt = salt

    def encrypt(self, plaintext: str) -> str:

        if self._key is None or self._salt is None:

            raise ValueError("Encryption key not set. Call derive_key() first.")

        nonce = os.urandom(self.NONCE_SIZE)

        aesgcm = AESGCM(self._key)

        ciphertext = aesgcm.encrypt(

            nonce,

            plaintext.encode('utf-8'),

            None

        )

        combined = self._salt + nonce + ciphertext

        return base64.b64encode(combined).decode('utf-8')

    def decrypt(self, encrypted_data: str, master_password: Optional[str] = None) -> str:

        try:

            combined = base64.b64decode(encrypted_data.encode('utf-8'))

        except Exception as e:

            raise ValueError(f"Invalid encrypted data format: {e}")

        if len(combined) < self.SALT_SIZE + self.NONCE_SIZE:

            raise ValueError("Encrypted data too short")

        salt = combined[:self.SALT_SIZE]

        nonce = combined[self.SALT_SIZE:self.SALT_SIZE + self.NONCE_SIZE]

        ciphertext = combined[self.SALT_SIZE + self.NONCE_SIZE:]

        if master_password:

            self.derive_key(master_password, salt)

        elif self._key is None:

            raise ValueError("Encryption key not set. Provide master_password or call derive_key() first.")

        aesgcm = AESGCM(self._key)

        try:

            plaintext = aesgcm.decrypt(nonce, ciphertext, None)

            return plaintext.decode('utf-8')

        except Exception as e:

            raise ValueError(f"Decryption failed. Invalid password or corrupted data: {e}")

    def clear_key(self):

        if self._key:

            self._key = b'\x00' * len(self._key)

        self._key = None

        self._salt = None

    @property

    def salt(self) -> Optional[bytes]:

        return self._salt

    @property

    def has_key(self) -> bool:

        return self._key is not None
