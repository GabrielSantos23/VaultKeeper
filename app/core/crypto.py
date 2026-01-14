"""
VaultKeeper - Cryptography Module
AES-256-GCM encryption for secure password storage
"""

import os
import base64
from typing import Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend


class CryptoManager:
    """
    Manages encryption and decryption using AES-256-GCM.
    The key is derived from the master password using PBKDF2.
    """
    
    SALT_SIZE = 16  # 128 bits
    NONCE_SIZE = 12  # 96 bits (recommended for GCM)
    KEY_SIZE = 32  # 256 bits
    ITERATIONS = 600000  # OWASP recommended for PBKDF2-SHA256
    
    def __init__(self):
        self._key: Optional[bytes] = None
        self._salt: Optional[bytes] = None
    
    def derive_key(self, master_password: str, salt: Optional[bytes] = None) -> bytes:
        """
        Derive an encryption key from the master password using PBKDF2.
        
        Args:
            master_password: The user's master password
            salt: Optional salt; if None, generates a new one
            
        Returns:
            The derived key
        """
        if salt is None:
            salt = os.urandom(self.SALT_SIZE)
        
        self._salt = salt
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.KEY_SIZE,
            salt=salt,
            iterations=self.ITERATIONS,
            backend=default_backend()
        )
        
        self._key = kdf.derive(master_password.encode('utf-8'))
        return self._key
    
    def set_key(self, key: bytes, salt: bytes):
        """Set the encryption key and salt directly."""
        self._key = key
        self._salt = salt
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string using AES-256-GCM.
        
        Args:
            plaintext: The string to encrypt
            
        Returns:
            Base64-encoded ciphertext with nonce and salt prepended
            
        Raises:
            ValueError: If the key hasn't been derived yet
        """
        if self._key is None or self._salt is None:
            raise ValueError("Encryption key not set. Call derive_key() first.")
        
        nonce = os.urandom(self.NONCE_SIZE)
        aesgcm = AESGCM(self._key)
        
        ciphertext = aesgcm.encrypt(
            nonce,
            plaintext.encode('utf-8'),
            None  # No additional authenticated data
        )
        
        # Combine salt + nonce + ciphertext
        combined = self._salt + nonce + ciphertext
        return base64.b64encode(combined).decode('utf-8')
    
    def decrypt(self, encrypted_data: str, master_password: Optional[str] = None) -> str:
        """
        Decrypt an encrypted string using AES-256-GCM.
        
        Args:
            encrypted_data: Base64-encoded encrypted data
            master_password: Optional master password to derive key (if not already set)
            
        Returns:
            The decrypted plaintext string
            
        Raises:
            ValueError: If decryption fails or key isn't available
        """
        try:
            combined = base64.b64decode(encrypted_data.encode('utf-8'))
        except Exception as e:
            raise ValueError(f"Invalid encrypted data format: {e}")
        
        if len(combined) < self.SALT_SIZE + self.NONCE_SIZE:
            raise ValueError("Encrypted data too short")
        
        # Extract components
        salt = combined[:self.SALT_SIZE]
        nonce = combined[self.SALT_SIZE:self.SALT_SIZE + self.NONCE_SIZE]
        ciphertext = combined[self.SALT_SIZE + self.NONCE_SIZE:]
        
        # Derive key if master password provided
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
        """Clear the encryption key from memory."""
        if self._key:
            # Overwrite with zeros before clearing
            self._key = b'\x00' * len(self._key)
        self._key = None
        self._salt = None
    
    @property
    def salt(self) -> Optional[bytes]:
        """Get the current salt."""
        return self._salt
    
    @property
    def has_key(self) -> bool:
        """Check if the encryption key is set."""
        return self._key is not None
