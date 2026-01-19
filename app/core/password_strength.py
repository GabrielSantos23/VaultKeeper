
import re

from dataclasses import dataclass

from enum import Enum

from typing import List, Tuple

class PasswordStrength(Enum):

    WEAK = 1

    FAIR = 2

    GOOD = 3

    STRONG = 4

@dataclass

class PasswordAnalysis:

    strength: PasswordStrength

    score: int

    label: str

    color: str

    feedback: List[str]

COMMON_PASSWORDS = {

    "password", "123456", "12345678", "qwerty", "abc123", "monkey",

    "1234567", "letmein", "trustno1", "dragon", "baseball", "iloveyou",

    "master", "sunshine", "ashley", "bailey", "shadow", "123123",

    "654321", "superman", "qazwsx", "michael", "football", "password1",

    "password123", "welcome", "jesus", "ninja", "mustang", "password12",

}

KEYBOARD_PATTERNS = [

    "qwerty", "qwertz", "azerty", "asdfgh", "zxcvbn",

    "1234567890", "0987654321", "qazwsx", "1qaz2wsx",

]

def _has_lowercase(password: str) -> bool:

    return bool(re.search(r'[a-z]', password))

def _has_uppercase(password: str) -> bool:

    return bool(re.search(r'[A-Z]', password))

def _has_digits(password: str) -> bool:

    return bool(re.search(r'\d', password))

def _has_special_chars(password: str) -> bool:

    return bool(re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:\'",.<>?/`~\\]', password))

def _has_repeated_chars(password: str, max_repeat: int = 3) -> bool:

    pattern = r'(.)\1{' + str(max_repeat - 1) + r',}'

    return bool(re.search(pattern, password))

def _has_sequential_chars(password: str) -> bool:

    sequences = [

        "abcdefghijklmnopqrstuvwxyz",

        "0123456789",

        "qwertyuiop",

        "asdfghjkl",

        "zxcvbnm",

    ]

    password_lower = password.lower()

    for seq in sequences:

        for i in range(len(seq) - 2):

            if seq[i:i+3] in password_lower:

                return True

            if seq[i:i+3][::-1] in password_lower:

                return True

    return False

def _is_common_password(password: str) -> bool:

    return password.lower() in COMMON_PASSWORDS

def _has_keyboard_pattern(password: str) -> bool:

    password_lower = password.lower()

    for pattern in KEYBOARD_PATTERNS:

        if pattern in password_lower:

            return True

    return False

def _calculate_entropy_score(password: str) -> float:

    charset_size = 0

    if _has_lowercase(password):

        charset_size += 26

    if _has_uppercase(password):

        charset_size += 26

    if _has_digits(password):

        charset_size += 10

    if _has_special_chars(password):

        charset_size += 32

    if charset_size == 0:

        return 0

    import math

    entropy = len(password) * math.log2(charset_size)

    return min(100, (entropy / 128) * 100)

def analyze_password(password: str) -> PasswordAnalysis:

    if not password:

        return PasswordAnalysis(

            strength=PasswordStrength.WEAK,

            score=0,

            label="EMPTY",

            color="#ef4444",

            feedback=["Enter a password"]

        )

    score = 0

    feedback = []

    length = len(password)

    if length < 6:

        score += 5

        feedback.append("Use at least 8 characters")

    elif length < 8:

        score += 10

        feedback.append("Consider using 12+ characters")

    elif length < 12:

        score += 20

        feedback.append("Great! Consider 16+ for maximum security")

    elif length < 16:

        score += 25

    else:

        score += 30

    has_lower = _has_lowercase(password)

    has_upper = _has_uppercase(password)

    has_digit = _has_digits(password)

    has_special = _has_special_chars(password)

    variety_count = sum([has_lower, has_upper, has_digit, has_special])

    score += variety_count * 10

    if not has_lower:

        feedback.append("Add lowercase letters")

    if not has_upper:

        feedback.append("Add uppercase letters")

    if not has_digit:

        feedback.append("Add numbers")

    if not has_special:

        feedback.append("Add special characters (!@#$%...)")

    if _is_common_password(password):

        score -= 30

        feedback.insert(0, "Avoid common passwords")

    if _has_repeated_chars(password):

        score -= 10

        feedback.append("Avoid repeated characters (aaa, 111)")

    if _has_sequential_chars(password):

        score -= 10

        feedback.append("Avoid sequential patterns (abc, 123)")

    if _has_keyboard_pattern(password):

        score -= 10

        feedback.append("Avoid keyboard patterns (qwerty)")

    entropy_bonus = _calculate_entropy_score(password) * 0.2

    score += int(entropy_bonus)

    score = max(0, min(100, score))

    if score < 30:

        strength = PasswordStrength.WEAK

        label = "WEAK"

        color = "#ef4444"

    elif score < 50:

        strength = PasswordStrength.FAIR

        label = "FAIR"

        color = "#f97316"

    elif score < 75:

        strength = PasswordStrength.GOOD

        label = "GOOD"

        color = "#eab308"

    else:

        strength = PasswordStrength.STRONG

        label = "STRONG"

        color = "#22c55e"

        feedback = ["Excellent password!"] if not feedback else feedback[:1]

    feedback = feedback[:3]

    return PasswordAnalysis(

        strength=strength,

        score=score,

        label=label,

        color=color,

        feedback=feedback

    )

def get_strength_bar_segments(analysis: PasswordAnalysis) -> List[Tuple[str, bool]]:

    strength_level = analysis.strength.value

    colors = [

        "#ef4444",

        "#f97316",

        "#eab308",

        "#22c55e",

    ]

    segments = []

    for i in range(4):

        is_filled = i < strength_level

        color = analysis.color if is_filled else "#374151"

        segments.append((color, is_filled))

    return segments
