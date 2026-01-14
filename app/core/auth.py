"""
VaultKeeper - Authentication Module
Master password management using Argon2
"""

import os
import json
import time
from pathlib import Path
from typing import Optional, Tuple
from argon2 import PasswordHasher, Type
from argon2.exceptions import VerifyMismatchError, InvalidHash


class AuthManager:
    """
    Manages master password authentication using Argon2id.
    Argon2id is the recommended variant for password hashing.
    """
    
    # Argon2id parameters (OWASP recommended)
    TIME_COST = 3  # Number of iterations
    MEMORY_COST = 65536  # 64 MB
    PARALLELISM = 4  # Number of parallel threads
    HASH_LEN = 32  # 256 bits
    SALT_LEN = 16  # 128 bits
    
    # Lock settings
    DEFAULT_LOCK_TIMEOUT = 300  # 5 minutes of inactivity default
    MAX_ATTEMPTS = 5  # Maximum failed attempts before lockout
    LOCKOUT_TIME = 60  # Lockout duration in seconds
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the AuthManager.
        
        Args:
            config_path: Path to store the master password hash
        """
        if config_path is None:
            config_path = Path.home() / '.vaultkeeper' / 'auth.json'
        
        self.config_path = config_path
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._hasher = PasswordHasher(
            time_cost=self.TIME_COST,
            memory_cost=self.MEMORY_COST,
            parallelism=self.PARALLELISM,
            hash_len=self.HASH_LEN,
            salt_len=self.SALT_LEN,
            type=Type.ID  # Argon2id
        )
        
        self._is_unlocked = False
        self._last_activity = 0.0
        self._failed_attempts = 0
        self._lockout_until = 0.0
        self._master_password: Optional[str] = None
        self.lock_timeout = self.DEFAULT_LOCK_TIMEOUT

    def set_timeout(self, seconds: int):
        """Set the auto-lock timeout in seconds."""
        self.lock_timeout = seconds
    
    def _load_config(self) -> dict:
        """Load configuration from file."""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_config(self, config: dict):
        """Save configuration to file."""
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def is_first_run(self) -> bool:
        """Check if this is the first run (no master password set)."""
        config = self._load_config()
        return 'master_hash' not in config
    
    def create_master_password(self, password: str) -> bool:
        """
        Create a new master password.
        
        Args:
            password: The master password to set
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If password doesn't meet requirements
        """
        # Validate password strength
        self._validate_password_strength(password)
        
        # Hash the password
        password_hash = self._hasher.hash(password)
        
        # Save to config
        config = self._load_config()
        config['master_hash'] = password_hash
        config['created_at'] = time.time()
        self._save_config(config)
        
        # Unlock the vault
        self._is_unlocked = True
        self._last_activity = time.time()
        self._master_password = password
        
        return True
    
    def _validate_password_strength(self, password: str):
        """
        Validate password meets minimum requirements.
        
        Raises:
            ValueError: If password doesn't meet requirements
        """
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError(
                "Password must contain at least one uppercase letter, "
                "one lowercase letter, and one digit"
            )
    
    def verify_master_password(self, password: str) -> bool:
        """
        Verify the master password.
        
        Args:
            password: The password to verify
            
        Returns:
            True if the password is correct
            
        Raises:
            ValueError: If no master password is set or lockout is active
        """
        # Check lockout
        if time.time() < self._lockout_until:
            remaining = int(self._lockout_until - time.time())
            raise ValueError(f"Account locked. Try again in {remaining} seconds.")
        
        config = self._load_config()
        if 'master_hash' not in config:
            raise ValueError("No master password set. Run setup first.")
        
        try:
            self._hasher.verify(config['master_hash'], password)
            
            # Check if rehash is needed (parameters changed)
            if self._hasher.check_needs_rehash(config['master_hash']):
                config['master_hash'] = self._hasher.hash(password)
                self._save_config(config)
            
            # Reset failed attempts on success
            self._failed_attempts = 0
            self._is_unlocked = True
            self._last_activity = time.time()
            self._master_password = password
            
            return True
            
        except VerifyMismatchError:
            self._failed_attempts += 1
            
            if self._failed_attempts >= self.MAX_ATTEMPTS:
                self._lockout_until = time.time() + self.LOCKOUT_TIME
                self._failed_attempts = 0
                raise ValueError(
                    f"Too many failed attempts. Locked for {self.LOCKOUT_TIME} seconds."
                )
            
            remaining = self.MAX_ATTEMPTS - self._failed_attempts
            raise ValueError(f"Invalid password. {remaining} attempts remaining.")
    
    def unlock(self, password: str) -> bool:
        """
        Unlock the vault with the master password.
        
        Args:
            password: The master password
            
        Returns:
            True if unlock successful
        """
        return self.verify_master_password(password)
    
    def lock(self):
        """Lock the vault and clear sensitive data from memory."""
        self._is_unlocked = False
        self._last_activity = 0
        
        # Clear password from memory
        if self._master_password:
            self._master_password = None
    
    def touch(self):
        """Update last activity time to prevent auto-lock."""
        if self._is_unlocked:
            self._last_activity = time.time()
    
    def check_timeout(self) -> bool:
        """
        Check if the vault should be locked due to inactivity.
        
        Returns:
            True if the vault was locked due to timeout
        """
        if self._is_unlocked:
            # If timeout is 0, auto-lock is disabled
            if self.lock_timeout > 0:
                if time.time() - self._last_activity > self.lock_timeout:
                    self.lock()
                    return True
        return False
    
    def change_master_password(self, old_password: str, new_password: str) -> bool:
        """
        Change the master password.
        
        Args:
            old_password: The current master password
            new_password: The new master password
            
        Returns:
            True if successful
        """
        # Verify old password
        self.verify_master_password(old_password)
        
        # Validate new password
        self._validate_password_strength(new_password)
        
        # Hash and save new password
        config = self._load_config()
        config['master_hash'] = self._hasher.hash(new_password)
        config['changed_at'] = time.time()
        self._save_config(config)
        
        self._master_password = new_password
        
        return True
    
    @property
    def is_unlocked(self) -> bool:
        """Check if the vault is currently unlocked."""
        self.check_timeout()
        return self._is_unlocked
    
    @property
    def master_password(self) -> Optional[str]:
        """
        Get the current master password (only available when unlocked).
        This should only be used for key derivation.
        """
        if not self._is_unlocked:
            return None
        return self._master_password
    
    @property
    def failed_attempts(self) -> int:
        """Get the current number of failed attempts."""
        return self._failed_attempts
