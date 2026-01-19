
import os

import json

import time

from pathlib import Path

from typing import Optional, Tuple

from argon2 import PasswordHasher, Type

from argon2.exceptions import VerifyMismatchError, InvalidHash

class AuthManager:

    TIME_COST = 3

    MEMORY_COST = 65536

    PARALLELISM = 4

    HASH_LEN = 32

    SALT_LEN = 16

    DEFAULT_LOCK_TIMEOUT = 300

    MAX_ATTEMPTS = 5

    LOCKOUT_TIME = 60

    def __init__(self, config_path: Optional[Path] = None):

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

            type=Type.ID

        )

        self._is_unlocked = False

        self._last_activity = 0.0

        self._failed_attempts = 0

        self._lockout_until = 0.0

        self._master_password: Optional[str] = None

        self.lock_timeout = self.DEFAULT_LOCK_TIMEOUT

    def set_timeout(self, seconds: int):

        self.lock_timeout = seconds

    def _load_config(self) -> dict:

        if self.config_path.exists():

            with open(self.config_path, 'r') as f:

                return json.load(f)

        return {}

    def _save_config(self, config: dict):

        with open(self.config_path, 'w') as f:

            json.dump(config, f, indent=2)

    def is_first_run(self) -> bool:

        config = self._load_config()

        return 'master_hash' not in config

    def create_master_password(self, password: str) -> bool:

        self._validate_password_strength(password)

        password_hash = self._hasher.hash(password)

        config = self._load_config()

        config['master_hash'] = password_hash

        config['created_at'] = time.time()

        self._save_config(config)

        self._is_unlocked = True

        self._last_activity = time.time()

        self._master_password = password

        return True

    def _validate_password_strength(self, password: str):

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

        if time.time() < self._lockout_until:

            remaining = int(self._lockout_until - time.time())

            raise ValueError(f"Account locked. Try again in {remaining} seconds.")

        config = self._load_config()

        if 'master_hash' not in config:

            raise ValueError("No master password set. Run setup first.")

        try:

            self._hasher.verify(config['master_hash'], password)

            if self._hasher.check_needs_rehash(config['master_hash']):

                config['master_hash'] = self._hasher.hash(password)

                self._save_config(config)

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

        return self.verify_master_password(password)

    def lock(self):

        self._is_unlocked = False

        self._last_activity = 0

        if self._master_password:

            self._master_password = None

    def touch(self):

        if self._is_unlocked:

            self._last_activity = time.time()

    def check_timeout(self) -> bool:

        if self._is_unlocked:

            if self.lock_timeout > 0:

                if time.time() - self._last_activity > self.lock_timeout:

                    self.lock()

                    return True

        return False

    def change_master_password(self, old_password: str, new_password: str) -> bool:

        self.verify_master_password(old_password)

        self._validate_password_strength(new_password)

        config = self._load_config()

        config['master_hash'] = self._hasher.hash(new_password)

        config['changed_at'] = time.time()

        self._save_config(config)

        self._master_password = new_password

        return True

    @property

    def is_unlocked(self) -> bool:

        self.check_timeout()

        return self._is_unlocked

    @property

    def master_password(self) -> Optional[str]:

        if not self._is_unlocked:

            return None

        return self._master_password

    @property

    def failed_attempts(self) -> int:

        return self._failed_attempts
