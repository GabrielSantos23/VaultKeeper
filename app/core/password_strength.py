"""
VaultKeeper - Password Strength Evaluator
Module to evaluate password strength with 4 levels of security assessment.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple


class PasswordStrength(Enum):
    """Password strength levels."""
    WEAK = 1
    FAIR = 2
    GOOD = 3
    STRONG = 4


@dataclass
class PasswordAnalysis:
    """Result of password strength analysis."""
    strength: PasswordStrength
    score: int  # 0-100
    label: str
    color: str  # Hex color for UI display
    feedback: List[str]  # Suggestions for improvement


# Common weak passwords list (abbreviated)
COMMON_PASSWORDS = {
    "password", "123456", "12345678", "qwerty", "abc123", "monkey",
    "1234567", "letmein", "trustno1", "dragon", "baseball", "iloveyou",
    "master", "sunshine", "ashley", "bailey", "shadow", "123123",
    "654321", "superman", "qazwsx", "michael", "football", "password1",
    "password123", "welcome", "jesus", "ninja", "mustang", "password12",
}

# Common keyboard patterns
KEYBOARD_PATTERNS = [
    "qwerty", "qwertz", "azerty", "asdfgh", "zxcvbn",
    "1234567890", "0987654321", "qazwsx", "1qaz2wsx",
]


def _has_lowercase(password: str) -> bool:
    """Check if password contains lowercase letters."""
    return bool(re.search(r'[a-z]', password))


def _has_uppercase(password: str) -> bool:
    """Check if password contains uppercase letters."""
    return bool(re.search(r'[A-Z]', password))


def _has_digits(password: str) -> bool:
    """Check if password contains digits."""
    return bool(re.search(r'\d', password))


def _has_special_chars(password: str) -> bool:
    """Check if password contains special characters."""
    return bool(re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:\'",.<>?/`~\\]', password))


def _has_repeated_chars(password: str, max_repeat: int = 3) -> bool:
    """Check if password has too many repeated characters in a row."""
    pattern = r'(.)\1{' + str(max_repeat - 1) + r',}'
    return bool(re.search(pattern, password))


def _has_sequential_chars(password: str) -> bool:
    """Check if password contains sequential characters (abc, 123, etc.)."""
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
            # Also check reverse
            if seq[i:i+3][::-1] in password_lower:
                return True
    return False


def _is_common_password(password: str) -> bool:
    """Check if password is in common passwords list."""
    return password.lower() in COMMON_PASSWORDS


def _has_keyboard_pattern(password: str) -> bool:
    """Check if password contains keyboard patterns."""
    password_lower = password.lower()
    for pattern in KEYBOARD_PATTERNS:
        if pattern in password_lower:
            return True
    return False


def _calculate_entropy_score(password: str) -> float:
    """Calculate a simplified entropy-based score."""
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
    
    # Simplified entropy: log2(charset_size^length)
    import math
    entropy = len(password) * math.log2(charset_size)
    
    # Normalize to 0-100 scale (assuming 128 bits as maximum practical entropy)
    return min(100, (entropy / 128) * 100)


def analyze_password(password: str) -> PasswordAnalysis:
    """
    Analyze password strength and return detailed analysis.
    
    The password is evaluated based on:
    - Length
    - Character variety (lowercase, uppercase, numbers, special chars)
    - Absence of common patterns
    - Absence of repeated characters
    - Not in common passwords list
    
    Returns PasswordAnalysis with:
    - strength: WEAK, FAIR, GOOD, or STRONG
    - score: 0-100
    - label: Human-readable strength label
    - color: Hex color for UI display
    - feedback: List of suggestions for improvement
    """
    if not password:
        return PasswordAnalysis(
            strength=PasswordStrength.WEAK,
            score=0,
            label="EMPTY",
            color="#ef4444",  # Red
            feedback=["Enter a password"]
        )
    
    score = 0
    feedback = []
    
    # Length scoring (up to 30 points)
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
    
    # Character variety (up to 40 points)
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
    
    # Penalties
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
    
    # Entropy bonus (up to 20 points)
    entropy_bonus = _calculate_entropy_score(password) * 0.2
    score += int(entropy_bonus)
    
    # Clamp score
    score = max(0, min(100, score))
    
    # Determine strength level
    if score < 30:
        strength = PasswordStrength.WEAK
        label = "WEAK"
        color = "#ef4444"  # Red
    elif score < 50:
        strength = PasswordStrength.FAIR
        label = "FAIR"
        color = "#f97316"  # Orange
    elif score < 75:
        strength = PasswordStrength.GOOD
        label = "GOOD"
        color = "#eab308"  # Yellow
    else:
        strength = PasswordStrength.STRONG
        label = "STRONG"
        color = "#22c55e"  # Green
        feedback = ["Excellent password!"] if not feedback else feedback[:1]
    
    # Limit feedback to top 3 suggestions
    feedback = feedback[:3]
    
    return PasswordAnalysis(
        strength=strength,
        score=score,
        label=label,
        color=color,
        feedback=feedback
    )


def get_strength_bar_segments(analysis: PasswordAnalysis) -> List[Tuple[str, bool]]:
    """
    Get segments for a 4-part strength bar.
    
    Returns list of (color, is_filled) tuples for 4 segments.
    """
    strength_level = analysis.strength.value  # 1-4
    
    colors = [
        "#ef4444",  # Red (Weak)
        "#f97316",  # Orange (Fair)
        "#eab308",  # Yellow (Good)
        "#22c55e",  # Green (Strong)
    ]
    
    segments = []
    for i in range(4):
        is_filled = i < strength_level
        # Use the current strength color for filled segments
        color = analysis.color if is_filled else "#374151"  # Gray for unfilled
        segments.append((color, is_filled))
    
    return segments
