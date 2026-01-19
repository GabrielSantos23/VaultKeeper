
const COMMON_PASSWORDS = new Set([
  "password",
  "123456",
  "12345678",
  "qwerty",
  "abc123",
  "monkey",
  "1234567",
  "letmein",
  "trustno1",
  "dragon",
  "baseball",
  "iloveyou",
  "master",
  "sunshine",
  "ashley",
  "bailey",
  "shadow",
  "123123",
  "654321",
  "superman",
  "qazwsx",
  "michael",
  "football",
  "password1",
  "password123",
  "welcome",
  "jesus",
  "ninja",
  "mustang",
  "password12",
]);

const KEYBOARD_PATTERNS = [
  "qwerty",
  "qwertz",
  "azerty",
  "asdfgh",
  "zxcvbn",
  "1234567890",
  "0987654321",
  "qazwsx",
  "1qaz2wsx",
];

const PasswordStrength = {
  WEAK: 1,
  FAIR: 2,
  GOOD: 3,
  STRONG: 4,
};

function hasLowercase(password) {
  return /[a-z]/.test(password);
}

function hasUppercase(password) {
  return /[A-Z]/.test(password);
}

function hasDigits(password) {
  return /\d/.test(password);
}

function hasSpecialChars(password) {
  return /[!@#$%^&*()_+\-=\[\]{}|;:'",.<>?/`~\\]/.test(password);
}

function hasRepeatedChars(password, maxRepeat = 3) {
  const pattern = new RegExp(`(.)\\1{${maxRepeat - 1},}`);
  return pattern.test(password);
}

function hasSequentialChars(password) {
  const sequences = [
    "abcdefghijklmnopqrstuvwxyz",
    "0123456789",
    "qwertyuiop",
    "asdfghjkl",
    "zxcvbnm",
  ];
  const passwordLower = password.toLowerCase();

  for (const seq of sequences) {
    for (let i = 0; i < seq.length - 2; i++) {
      const sub = seq.substring(i, i + 3);
      if (passwordLower.includes(sub)) return true;

      const subRev = sub.split("").reverse().join("");
      if (passwordLower.includes(subRev)) return true;
    }
  }
  return false;
}

function isCommonPassword(password) {
  return COMMON_PASSWORDS.has(password.toLowerCase());
}

function hasKeyboardPattern(password) {
  const passwordLower = password.toLowerCase();
  return KEYBOARD_PATTERNS.some((pattern) => passwordLower.includes(pattern));
}

function calculateEntropyScore(password) {
  let charsetSize = 0;
  if (hasLowercase(password)) charsetSize += 26;
  if (hasUppercase(password)) charsetSize += 26;
  if (hasDigits(password)) charsetSize += 10;
  if (hasSpecialChars(password)) charsetSize += 32;

  if (charsetSize === 0) return 0;

  const entropy = password.length * Math.log2(charsetSize);
  return Math.min(100, (entropy / 128) * 100);
}

function analyzePassword(password) {
  if (!password) {
    return {
      strength: PasswordStrength.WEAK,
      score: 0,
      label: "EMPTY",
      color: "var(--vk-accent-red)",
      feedback: ["Enter a password"],
    };
  }

  let score = 0;
  let feedback = [];
  const length = password.length;
  if (length < 6) {
    score += 5;
    feedback.push("Use at least 8 characters");
  } else if (length < 8) {
    score += 10;
    feedback.push("Consider using 12+ characters");
  } else if (length < 12) {
    score += 20;
    feedback.push("Great! Consider 16+ for maximum security");
  } else if (length < 16) {
    score += 25;
  } else {
    score += 30;
  }
  const hasLower = hasLowercase(password);
  const hasUpper = hasUppercase(password);
  const hasDigit = hasDigits(password);
  const hasSpecial = hasSpecialChars(password);

  const varietyCount = [hasLower, hasUpper, hasDigit, hasSpecial].filter(
    Boolean,
  ).length;
  score += varietyCount * 10;

  if (!hasLower) feedback.push("Add lowercase letters");
  if (!hasUpper) feedback.push("Add uppercase letters");
  if (!hasDigit) feedback.push("Add numbers");
  if (!hasSpecial) feedback.push("Add special characters");
  if (isCommonPassword(password)) {
    score -= 30;
    feedback.unshift("Avoid common passwords");
  }

  if (hasRepeatedChars(password)) {
    score -= 10;
    feedback.push("Avoid repeated characters");
  }

  if (hasSequentialChars(password)) {
    score -= 10;
    feedback.push("Avoid sequential patterns");
  }

  if (hasKeyboardPattern(password)) {
    score -= 10;
    feedback.push("Avoid keyboard patterns");
  }
  const entropyBonus = calculateEntropyScore(password) * 0.2;
  score += Math.floor(entropyBonus);
  score = Math.max(0, Math.min(100, score));
  let strength, label, color;

  if (score < 30) {
    strength = PasswordStrength.WEAK;
    label = "Weak";
    color = "var(--vk-accent-red)";
  } else if (score < 50) {
    strength = PasswordStrength.FAIR;
    label = "Fair";
    color = "var(--vk-accent-warning)";
  } else if (score < 75) {
    strength = PasswordStrength.GOOD;
    label = "Good";
    color = "#eab308";
  } else {
    strength = PasswordStrength.STRONG;
    label = "Fantastic";
    color = "var(--vk-accent-green)";
    if (feedback.length === 0) feedback = ["Excellent password!"];
  }

  return {
    strength,
    score,
    label,
    color,
    feedback: feedback.slice(0, 3),
  };
}