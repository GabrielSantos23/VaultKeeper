
import hmac

import hashlib

import struct

import time

import base64

import re

from typing import Optional, Tuple

from urllib.parse import parse_qs, urlparse

class TOTPManager:

    def __init__(self, secret: str, digits: int = 6, interval: int = 30, algorithm: str = 'sha1'):

        self.secret = self._normalize_secret(secret)

        self.digits = digits

        self.interval = interval

        self.algorithm = algorithm.lower()

    @staticmethod

    def _normalize_secret(secret: str) -> str:

        secret = re.sub(r'[\s-]', '', secret.upper())

        padding = 8 - (len(secret) % 8)

        if padding != 8:

            secret += '=' * padding

        return secret

    def _get_hash_algorithm(self):

        algorithms = {

            'sha1': hashlib.sha1,

            'sha256': hashlib.sha256,

            'sha512': hashlib.sha512,

        }

        return algorithms.get(self.algorithm, hashlib.sha1)

    def _decode_secret(self) -> bytes:

        try:

            return base64.b32decode(self.secret)

        except Exception:

            raise ValueError("Invalid TOTP secret. Must be a valid base32 string.")

    def _get_counter(self, timestamp: Optional[float] = None) -> int:

        if timestamp is None:

            timestamp = time.time()

        return int(timestamp // self.interval)

    def generate(self, timestamp: Optional[float] = None) -> str:

        key = self._decode_secret()

        counter = self._get_counter(timestamp)

        counter_bytes = struct.pack('>Q', counter)

        hash_func = self._get_hash_algorithm()

        hmac_hash = hmac.new(key, counter_bytes, hash_func).digest()

        offset = hmac_hash[-1] & 0x0F

        code = struct.unpack('>I', hmac_hash[offset:offset + 4])[0]

        code &= 0x7FFFFFFF

        code %= 10 ** self.digits

        return str(code).zfill(self.digits)

    def get_remaining_seconds(self) -> int:

        return self.interval - int(time.time() % self.interval)

    def verify(self, code: str, window: int = 1, timestamp: Optional[float] = None) -> bool:

        if timestamp is None:

            timestamp = time.time()

        for offset in range(-window, window + 1):

            check_time = timestamp + (offset * self.interval)

            if self.generate(check_time) == code.zfill(self.digits):

                return True

        return False

def parse_totp_uri(uri: str) -> dict:

    parsed = urlparse(uri)

    if parsed.scheme != 'otpauth':

        raise ValueError("Invalid TOTP URI: must start with 'otpauth://'")

    if parsed.netloc != 'totp':

        raise ValueError("Invalid TOTP URI: only 'totp' type is supported")

    label = parsed.path.lstrip('/')

    if ':' in label:

        issuer_from_label, account = label.split(':', 1)

    else:

        issuer_from_label = None

        account = label

    params = parse_qs(parsed.query)

    if 'secret' not in params:

        raise ValueError("Invalid TOTP URI: missing 'secret' parameter")

    secret = params['secret'][0]

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

    from urllib.parse import quote

    if issuer:

        label = f"{quote(issuer)}:{quote(account)}"

    else:

        label = quote(account)

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

    try:

        normalized = TOTPManager._normalize_secret(secret)

        base64.b32decode(normalized)

        return True

    except Exception:

        return False

def get_totp_code(secret: str) -> Tuple[str, int]:

    totp = TOTPManager(secret)

    return totp.generate(), totp.get_remaining_seconds()
