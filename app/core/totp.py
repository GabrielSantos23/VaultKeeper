"""
VaultKeeper - TOTP (Time-based One-Time Password) Module
Implements RFC 6238 TOTP for two-factor authentication
"""

import hmac
import hashlib
import struct
import time
import base64
import re
from typing import Optional, Tuple
from urllib.parse import parse_qs, urlparse


class TOTPManager:
    """
    Manages TOTP (Time-based One-Time Password) generation.
    Implements RFC 6238 for 2FA code generation.
    """
    
    def __init__(self, secret: str, digits: int = 6, interval: int = 30, algorithm: str = 'sha1'):
        """
        Initialize TOTP manager.
        
        Args:
            secret: Base32-encoded secret key
            digits: Number of digits in the OTP (default: 6)
            interval: Time step in seconds (default: 30)
            algorithm: Hash algorithm (sha1, sha256, sha512)
        """
        self.secret = self._normalize_secret(secret)
        self.digits = digits
        self.interval = interval
        self.algorithm = algorithm.lower()
        
    @staticmethod
    def _normalize_secret(secret: str) -> str:
        """
        Normalize a base32 secret by removing spaces and converting to uppercase.
        
        Args:
            secret: The raw secret string
            
        Returns:
            Normalized base32 secret
        """
        # Remove spaces, dashes, and convert to uppercase
        secret = re.sub(r'[\s-]', '', secret.upper())
        # Add padding if necessary
        padding = 8 - (len(secret) % 8)
        if padding != 8:
            secret += '=' * padding
        return secret
    
    def _get_hash_algorithm(self):
        """Get the hash algorithm function based on config."""
        algorithms = {
            'sha1': hashlib.sha1,
            'sha256': hashlib.sha256,
            'sha512': hashlib.sha512,
        }
        return algorithms.get(self.algorithm, hashlib.sha1)
    
    def _decode_secret(self) -> bytes:
        """Decode the base32 secret to bytes."""
        try:
            return base64.b32decode(self.secret)
        except Exception:
            raise ValueError("Invalid TOTP secret. Must be a valid base32 string.")
    
    def _get_counter(self, timestamp: Optional[float] = None) -> int:
        """
        Get the counter value for the given timestamp.
        
        Args:
            timestamp: Unix timestamp (default: current time)
            
        Returns:
            Counter value
        """
        if timestamp is None:
            timestamp = time.time()
        return int(timestamp // self.interval)
    
    def generate(self, timestamp: Optional[float] = None) -> str:
        """
        Generate a TOTP code.
        
        Args:
            timestamp: Unix timestamp (default: current time)
            
        Returns:
            The TOTP code as a string
        """
        # Get the secret as bytes
        key = self._decode_secret()
        
        # Get the counter
        counter = self._get_counter(timestamp)
        
        # Pack the counter as a big-endian 8-byte integer
        counter_bytes = struct.pack('>Q', counter)
        
        # Calculate HMAC
        hash_func = self._get_hash_algorithm()
        hmac_hash = hmac.new(key, counter_bytes, hash_func).digest()
        
        # Dynamic truncation
        offset = hmac_hash[-1] & 0x0F
        code = struct.unpack('>I', hmac_hash[offset:offset + 4])[0]
        code &= 0x7FFFFFFF
        code %= 10 ** self.digits
        
        # Pad with zeros if necessary
        return str(code).zfill(self.digits)
    
    def get_remaining_seconds(self) -> int:
        """
        Get the number of seconds remaining until the current code expires.
        
        Returns:
            Seconds remaining (0 to interval-1)
        """
        return self.interval - int(time.time() % self.interval)
    
    def verify(self, code: str, window: int = 1, timestamp: Optional[float] = None) -> bool:
        """
        Verify a TOTP code.
        
        Args:
            code: The code to verify
            window: Number of intervals to check before and after (default: 1)
            timestamp: Unix timestamp (default: current time)
            
        Returns:
            True if the code is valid
        """
        if timestamp is None:
            timestamp = time.time()
            
        # Check codes within the window
        for offset in range(-window, window + 1):
            check_time = timestamp + (offset * self.interval)
            if self.generate(check_time) == code.zfill(self.digits):
                return True
        return False


def parse_totp_uri(uri: str) -> dict:
    """
    Parse an otpauth:// URI and extract TOTP parameters.
    
    Args:
        uri: The otpauth URI (e.g., otpauth://totp/Example:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=Example)
        
    Returns:
        Dictionary with TOTP parameters:
        - secret: Base32-encoded secret
        - issuer: Optional issuer name
        - account: Account name
        - algorithm: Hash algorithm (default: sha1)
        - digits: Number of digits (default: 6)
        - period: Time period in seconds (default: 30)
    """
    parsed = urlparse(uri)
    
    if parsed.scheme != 'otpauth':
        raise ValueError("Invalid TOTP URI: must start with 'otpauth://'")
    
    if parsed.netloc != 'totp':
        raise ValueError("Invalid TOTP URI: only 'totp' type is supported")
    
    # Parse the label (path)
    label = parsed.path.lstrip('/')
    if ':' in label:
        issuer_from_label, account = label.split(':', 1)
    else:
        issuer_from_label = None
        account = label
    
    # Parse query parameters
    params = parse_qs(parsed.query)
    
    # Get secret (required)
    if 'secret' not in params:
        raise ValueError("Invalid TOTP URI: missing 'secret' parameter")
    secret = params['secret'][0]
    
    # Get optional parameters
    issuer = params.get('issuer', [issuer_from_label])[0] if params.get('issuer') or issuer_from_label else None
    algorithm = params.get('algorithm', ['sha1'])[0].lower()
    digits = int(params.get('digits', ['6'])[0])
    period = int(params.get('period', ['30'])[0])
    
    return {
        'secret': secret,
        'issuer': issuer,
        'account': account,
        'algorithm': algorithm,
        'digits': digits,
        'period': period,
    }


def generate_totp_uri(secret: str, account: str, issuer: Optional[str] = None,
                      algorithm: str = 'sha1', digits: int = 6, period: int = 30) -> str:
    """
    Generate an otpauth:// URI for TOTP.
    
    Args:
        secret: Base32-encoded secret
        account: Account name (e.g., user@example.com)
        issuer: Optional issuer name
        algorithm: Hash algorithm (default: sha1)
        digits: Number of digits (default: 6)
        period: Time period in seconds (default: 30)
        
    Returns:
        The otpauth URI
    """
    from urllib.parse import quote
    
    # Build the label
    if issuer:
        label = f"{quote(issuer)}:{quote(account)}"
    else:
        label = quote(account)
    
    # Build the URI
    uri = f"otpauth://totp/{label}?secret={secret}"
    
    if issuer:
        uri += f"&issuer={quote(issuer)}"
    if algorithm != 'sha1':
        uri += f"&algorithm={algorithm.upper()}"
    if digits != 6:
        uri += f"&digits={digits}"
    if period != 30:
        uri += f"&period={period}"
    
    return uri


def is_valid_totp_secret(secret: str) -> bool:
    """
    Check if a string is a valid base32 TOTP secret.
    
    Args:
        secret: The secret to validate
        
    Returns:
        True if valid
    """
    try:
        # Normalize the secret
        normalized = TOTPManager._normalize_secret(secret)
        # Try to decode
        base64.b32decode(normalized)
        return True
    except Exception:
        return False


def get_totp_code(secret: str) -> Tuple[str, int]:
    """
    Get the current TOTP code and remaining seconds.
    
    Args:
        secret: Base32-encoded secret
        
    Returns:
        Tuple of (code, remaining_seconds)
    """
    totp = TOTPManager(secret)
    return totp.generate(), totp.get_remaining_seconds()
