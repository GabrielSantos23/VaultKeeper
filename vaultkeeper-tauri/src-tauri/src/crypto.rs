use aes_gcm::aead::{Aead, KeyInit};
use aes_gcm::{Aes256Gcm, Key, Nonce};
use base64::{engine::general_purpose, Engine as _};
use rand::Rng;
use ring::rand::SecureRandom;
use scrypt::{scrypt, Params};
use sha2::{Digest, Sha256};
use std::collections::HashMap;
use std::sync::Mutex;
use zeroize::Zeroize;

const SALT_SIZE: usize = 16;
const NONCE_SIZE: usize = 12;
const KEY_SIZE: usize = 32;

// Scrypt parameters (stronger since v2.1)
const SCRYPT_LOG_N: u8 = 17;      // N=131072 (new, stronger)
const SCRYPT_R: u32 = 8;
const SCRYPT_P: u32 = 1;
const SCRYPT_LOG_N_LEGACY: u8 = 14; // N=16384 (old, kept for migration)

// Global key cache: (password_hash + salt) -> derived_key
lazy_static::lazy_static! {
    static ref KEY_CACHE: Mutex<HashMap<String, [u8; KEY_SIZE]>> = Mutex::new(HashMap::new());
}

/// Clear the key cache (call when locking vault)
pub fn clear_key_cache() {
    if let Ok(mut cache) = KEY_CACHE.lock() {
        for (_, key) in cache.drain() {
            let mut key_copy = key;
            key_copy.zeroize();
        }
    }
}

/// Derive a key from password using Scrypt with caching (uses STRONG params)
pub fn derive_key_cached(
    password: &str,
    salt: &[u8],
) -> Result<[u8; KEY_SIZE], Box<dyn std::error::Error>> {
    // Create cache key from a hash of the full password + salt (never store password chars)
    let mut hasher = Sha256::new();
    hasher.update(password.as_bytes());
    hasher.update(salt);
    let cache_key = format!("v2:{}", general_purpose::STANDARD.encode(hasher.finalize()));

    // Check cache first
    {
        let cache = KEY_CACHE.lock().map_err(|e| e.to_string())?;
        if let Some(key) = cache.get(&cache_key) {
            return Ok(*key);
        }
    }

    // Derive key with STRONG params
    let mut key = [0u8; KEY_SIZE];
    let params = Params::new(SCRYPT_LOG_N, SCRYPT_R, SCRYPT_P, KEY_SIZE)?;
    scrypt(password.as_bytes(), salt, &params, &mut key)?;

    // Cache the result
    {
        let mut cache = KEY_CACHE.lock().map_err(|e| e.to_string())?;
        if cache.len() >= 1000 {
            cache.clear();
        }
        cache.insert(cache_key, key);
    }

    Ok(key)
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct PasswordStrength {
    pub score: u8, // 0-4
    pub label: String,
    pub color: String,
    pub suggestions: Vec<String>,
}

/// Derive a key from password using Scrypt (STRONG params: N=131072, r=8, p=1)
pub fn derive_key(
    password: &str,
    salt: &[u8],
) -> Result<[u8; KEY_SIZE], Box<dyn std::error::Error>> {
    let mut key = [0u8; KEY_SIZE];
    let params = Params::new(SCRYPT_LOG_N, SCRYPT_R, SCRYPT_P, KEY_SIZE)?;
    scrypt(password.as_bytes(), salt, &params, &mut key)?;
    Ok(key)
}

/// Derive a key using LEGACY Scrypt params (N=16384) — for backward compatibility only
fn derive_key_legacy(
    password: &str,
    salt: &[u8],
) -> Result<[u8; KEY_SIZE], Box<dyn std::error::Error>> {
    let mut key = [0u8; KEY_SIZE];
    let params = Params::new(SCRYPT_LOG_N_LEGACY, SCRYPT_R, SCRYPT_P, KEY_SIZE)?;
    scrypt(password.as_bytes(), salt, &params, &mut key)?;
    Ok(key)
}

/// Encrypt data using AES-256-GCM
/// Format: base64(salt + nonce + ciphertext)
pub fn encrypt(plaintext: &str, password: &str) -> Result<String, Box<dyn std::error::Error>> {
    // Generate random salt
    let mut salt = [0u8; SALT_SIZE];
    let rng = ring::rand::SystemRandom::new();
    rng.fill(&mut salt).map_err(|_| "Failed to generate salt")?;

    // Derive key
    let key_bytes = derive_key(password, &salt)?;
    let key = Key::<Aes256Gcm>::from_slice(&key_bytes);
    let cipher = Aes256Gcm::new(key);

    // Generate random nonce
    let mut nonce_bytes = [0u8; NONCE_SIZE];
    rng.fill(&mut nonce_bytes)
        .map_err(|_| "Failed to generate nonce")?;
    let nonce = Nonce::from_slice(&nonce_bytes);

    // Encrypt
    let ciphertext = cipher
        .encrypt(nonce, plaintext.as_bytes())
        .map_err(|e| format!("Encryption failed: {:?}", e))?;

    // Combine: salt + nonce + ciphertext
    let mut combined = Vec::with_capacity(SALT_SIZE + NONCE_SIZE + ciphertext.len());
    combined.extend_from_slice(&salt);
    combined.extend_from_slice(&nonce_bytes);
    combined.extend_from_slice(&ciphertext);

    // Base64 encode
    Ok(general_purpose::STANDARD.encode(&combined))
}

/// Decrypt data using AES-256-GCM with automatic parameter migration
/// Tries strong params first, falls back to legacy params
pub fn decrypt(encrypted_data: &str, password: &str) -> Result<String, Box<dyn std::error::Error>> {
    // Base64 decode
    let combined = general_purpose::STANDARD
        .decode(encrypted_data)
        .map_err(|e| format!("Invalid base64: {}", e))?;

    if combined.len() < SALT_SIZE + NONCE_SIZE {
        return Err("Encrypted data too short".into());
    }

    // Extract salt, nonce, ciphertext
    let salt = &combined[0..SALT_SIZE];
    let nonce_bytes = &combined[SALT_SIZE..SALT_SIZE + NONCE_SIZE];
    let ciphertext = &combined[SALT_SIZE + NONCE_SIZE..];
    let nonce = Nonce::from_slice(nonce_bytes);

    // Try with STRONG params first (new encryption)
    if let Ok(key_bytes) = derive_key_cached(password, salt) {
        let key = Key::<Aes256Gcm>::from_slice(&key_bytes);
        let cipher = Aes256Gcm::new(key);
        if let Ok(plaintext) = cipher.decrypt(nonce, ciphertext) {
            return Ok(String::from_utf8(plaintext)?);
        }
    }

    // Fallback to LEGACY params (old encryption)
    let key_bytes = derive_key_legacy(password, salt)?;
    let key = Key::<Aes256Gcm>::from_slice(&key_bytes);
    let cipher = Aes256Gcm::new(key);
    let plaintext = cipher
        .decrypt(nonce, ciphertext)
        .map_err(|e| format!("Decryption failed: {:?}", e))?;

    Ok(String::from_utf8(plaintext)?)
}

/// Decrypt using a cached key (fast - no Scrypt derivation)
fn decrypt_with_key(
    encrypted_data: &str,
    key: &[u8],
) -> Result<String, Box<dyn std::error::Error>> {
    let combined = general_purpose::STANDARD
        .decode(encrypted_data)
        .map_err(|e| format!("Invalid base64: {}", e))?;

    if combined.len() < SALT_SIZE + NONCE_SIZE {
        return Err("Encrypted data too short".into());
    }

    // Extract salt (skip), nonce, ciphertext
    let nonce_bytes = &combined[SALT_SIZE..SALT_SIZE + NONCE_SIZE];
    let ciphertext = &combined[SALT_SIZE + NONCE_SIZE..];

    let key = Key::<Aes256Gcm>::from_slice(key);
    let cipher = Aes256Gcm::new(key);
    let nonce = Nonce::from_slice(nonce_bytes);

    let plaintext = cipher
        .decrypt(nonce, ciphertext)
        .map_err(|e| format!("Decryption failed: {:?}", e))?;

    Ok(String::from_utf8(plaintext)?)
}

/// Try to decrypt if the data looks encrypted (base64 and long enough)
/// Uses cached key for fast decryption
pub fn decrypt_if_encrypted_with_key(
    data: &str,
    key: &[u8],
) -> Result<String, Box<dyn std::error::Error>> {
    // If data is short, assume it's plaintext (fast path)
    if data.len() < 40 {
        return Ok(data.to_string());
    }

    // Quick check: if it contains common plaintext chars at high frequency, assume plaintext
    let printable_count = data
        .chars()
        .filter(|c| {
            c.is_ascii_alphanumeric()
                || *c == ' '
                || *c == '-'
                || *c == '_'
                || *c == '.'
                || *c == '@'
        })
        .count();
    let ratio = printable_count as f64 / data.len() as f64;

    // If >80% printable and contains spaces/newlines, likely plaintext
    if ratio > 0.8 && (data.contains(' ') || data.contains('\n')) {
        return Ok(data.to_string());
    }

    // Try to decode as base64
    match general_purpose::STANDARD.decode(data) {
        Ok(decoded) => {
            // Check if it has the expected structure (salt + nonce + ciphertext)
            if decoded.len() >= SALT_SIZE + NONCE_SIZE + 16 {
                // Try to decrypt with cached key
                match decrypt_with_key(data, key) {
                    Ok(plaintext) => Ok(plaintext),
                    Err(_) => {
                        // Decryption failed, might be plaintext stored as base64
                        String::from_utf8(decoded).map_err(|_| "Invalid data format".into())
                    }
                }
            } else {
                // Too short to be encrypted data, might be plaintext
                Ok(data.to_string())
            }
        }
        Err(_) => {
            // Not valid base64, assume plaintext
            Ok(data.to_string())
        }
    }
}

/// Legacy decrypt function (slow - derives key with Scrypt)
/// Kept for backwards compatibility
pub fn decrypt_if_encrypted(
    data: &str,
    password: &str,
) -> Result<String, Box<dyn std::error::Error>> {
    // If data is short, assume it's plaintext (fast path)
    if data.len() < 40 {
        return Ok(data.to_string());
    }

    // Quick check: if it contains common plaintext chars at high frequency, assume plaintext
    let printable_count = data
        .chars()
        .filter(|c| {
            c.is_ascii_alphanumeric()
                || *c == ' '
                || *c == '-'
                || *c == '_'
                || *c == '.'
                || *c == '@'
        })
        .count();
    let ratio = printable_count as f64 / data.len() as f64;

    // If >80% printable and contains spaces/newlines, likely plaintext
    if ratio > 0.8 && (data.contains(' ') || data.contains('\n')) {
        return Ok(data.to_string());
    }

    // Try to decode as base64
    match general_purpose::STANDARD.decode(data) {
        Ok(decoded) => {
            // Check if it has the expected structure (salt + nonce + ciphertext)
            if decoded.len() >= SALT_SIZE + NONCE_SIZE + 16 {
                // Try to decrypt
                match decrypt(data, password) {
                    Ok(plaintext) => Ok(plaintext),
                    Err(_) => {
                        // Decryption failed, might be plaintext stored as base64
                        String::from_utf8(decoded).map_err(|_| "Invalid data format".into())
                    }
                }
            } else {
                // Too short to be encrypted data, might be plaintext
                Ok(data.to_string())
            }
        }
        Err(_) => {
            // Not valid base64, assume plaintext
            Ok(data.to_string())
        }
    }
}

pub fn generate_password(
    length: u32,
    include_uppercase: bool,
    include_lowercase: bool,
    include_numbers: bool,
    include_symbols: bool,
) -> Result<String, Box<dyn std::error::Error>> {
    let mut charset = String::new();

    if include_lowercase {
        charset.push_str("abcdefghijklmnopqrstuvwxyz");
    }
    if include_uppercase {
        charset.push_str("ABCDEFGHIJKLMNOPQRSTUVWXYZ");
    }
    if include_numbers {
        charset.push_str("0123456789");
    }
    if include_symbols {
        charset.push_str("!@#$%^&*()_+-=[]{}|;:,.<>?");
    }

    if charset.is_empty() {
        return Err("At least one character set must be selected".into());
    }

    let mut rng = rand::thread_rng();
    let password: String = (0..length)
        .map(|_| {
            let idx = rng.gen_range(0..charset.len());
            charset.chars().nth(idx).unwrap()
        })
        .collect();

    Ok(password)
}

pub fn check_password_strength(password: &str) -> PasswordStrength {
    let mut score = 0;
    let mut suggestions = Vec::new();

    // Length check
    if password.len() >= 8 {
        score += 1;
    } else {
        suggestions.push("Use at least 8 characters".to_string());
    }

    if password.len() >= 12 {
        score += 1;
    }

    // Character variety checks
    let has_upper = password.chars().any(|c| c.is_uppercase());
    let has_lower = password.chars().any(|c| c.is_lowercase());
    let has_digit = password.chars().any(|c| c.is_numeric());
    let has_symbol = password.chars().any(|c| !c.is_alphanumeric());

    let variety_count = [has_upper, has_lower, has_digit, has_symbol]
        .iter()
        .filter(|&&x| x)
        .count();

    if variety_count >= 2 {
        score += 1;
    }
    if variety_count >= 3 {
        score += 1;
    }

    if !has_upper {
        suggestions.push("Add uppercase letters".to_string());
    }
    if !has_lower {
        suggestions.push("Add lowercase letters".to_string());
    }
    if !has_digit {
        suggestions.push("Add numbers".to_string());
    }
    if !has_symbol {
        suggestions.push("Add special characters".to_string());
    }

    let (label, color) = match score {
        0 | 1 => ("Weak", "#ef4444"),
        2 => ("Fair", "#f97316"),
        3 => ("Good", "#eab308"),
        4 => ("Strong", "#22c55e"),
        _ => ("Unknown", "#6b7280"),
    };

    PasswordStrength {
        score,
        label: label.to_string(),
        color: color.to_string(),
        suggestions,
    }
}

pub fn hash_password(password: &str, salt: &[u8]) -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    let mut hasher = Sha256::new();
    hasher.update(password.as_bytes());
    hasher.update(salt);
    Ok(hasher.finalize().to_vec())
}

pub fn generate_salt() -> Result<Vec<u8>, ring::error::Unspecified> {
    let rng = ring::rand::SystemRandom::new();
    let mut salt = [0u8; 16];
    rng.fill(&mut salt)?;
    Ok(salt.to_vec())
}
