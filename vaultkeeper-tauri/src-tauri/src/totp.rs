use std::time::{SystemTime, UNIX_EPOCH};
use totp_rs::{Algorithm, TOTP};
use base32::Alphabet;

fn normalize_secret(secret: &str) -> String {
    let mut cleaned = secret.to_uppercase().replace(' ', "").replace('-', "");
    cleaned = cleaned.trim_end_matches('=').to_string();
    if cleaned.is_empty() {
        return String::new();
    }
    let padding = 8 - (cleaned.len() % 8);
    if padding != 8 {
        cleaned.push_str(&"=".repeat(padding));
    }
    cleaned
}

/// Generate a TOTP code from a secret
pub fn generate_totp(secret: &str) -> Result<(String, u64), Box<dyn std::error::Error>> {
    let normalized = normalize_secret(secret);

    // Decode base32 secret
    let mut secret_bytes = base32::decode(Alphabet::Rfc4648 { padding: true }, &normalized)
        .ok_or_else(|| "Invalid Base32 secret key")?;

    // RFC 4226 / totp-rs requires secret to be at least 128 bits (16 bytes).
    // We can right-pad with zeroes, which is mathematically equivalent under HMAC.
    if secret_bytes.len() < 16 {
        secret_bytes.resize(16, 0);
    }

    // Create TOTP instance
    let totp = TOTP::new(
        Algorithm::SHA1,
        6,
        1,
        30, // 30 second period
        secret_bytes,
        None,          // issuer
        String::new(), // account_name
    )
    .map_err(|e| format!("Invalid TOTP secret: {:?}", e))?;

    // Generate current code
    let code = totp
        .generate_current()
        .map_err(|e| format!("Failed to generate TOTP: {:?}", e))?;

    // Calculate remaining seconds
    let now = SystemTime::now().duration_since(UNIX_EPOCH)?.as_secs();
    let remaining = 30 - (now % 30);

    Ok((code, remaining))
}

/// Parse a TOTP URI (otpauth://)
pub fn parse_totp_uri(uri: &str) -> Result<TotpConfig, Box<dyn std::error::Error>> {
    let url = url::Url::parse(uri)?;

    if url.scheme() != "otpauth" {
        return Err("Invalid scheme, expected otpauth".into());
    }

    let host = url.host_str().ok_or("Missing host in URI")?;
    if host != "totp" && host != "hotp" {
        return Err("Invalid host, expected totp or hotp".into());
    }

    let path = url.path();
    let label = path.trim_start_matches('/');

    let secret = url
        .query_pairs()
        .find(|(k, _)| k == "secret")
        .map(|(_, v)| v.to_string())
        .ok_or("Missing secret parameter")?;

    let issuer = url
        .query_pairs()
        .find(|(k, _)| k == "issuer")
        .map(|(_, v)| v.to_string());

    let algorithm = url
        .query_pairs()
        .find(|(k, _)| k == "algorithm")
        .map(|(_, v)| v.to_string())
        .unwrap_or_else(|| "SHA1".to_string());

    let digits = url
        .query_pairs()
        .find(|(k, _)| k == "digits")
        .and_then(|(_, v)| v.parse::<usize>().ok())
        .unwrap_or(6);

    let period = url
        .query_pairs()
        .find(|(k, _)| k == "period")
        .and_then(|(_, v)| v.parse::<u64>().ok())
        .unwrap_or(30);

    Ok(TotpConfig {
        label: label.to_string(),
        secret,
        issuer,
        algorithm,
        digits,
        period,
    })
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct TotpConfig {
    pub label: String,
    pub secret: String,
    pub issuer: Option<String>,
    pub algorithm: String,
    pub digits: usize,
    pub period: u64,
}

/// Validate if a string looks like a valid TOTP secret
pub fn is_valid_totp_secret(secret: &str) -> bool {
    let normalized = normalize_secret(secret);
    if normalized.is_empty() {
        return false;
    }
    base32::decode(Alphabet::Rfc4648 { padding: true }, &normalized).is_some()
}

/// Generate a TOTP URI for sharing
pub fn generate_totp_uri(
    secret: &str,
    account: &str,
    issuer: Option<&str>,
) -> Result<String, Box<dyn std::error::Error>> {
    let mut uri = format!("otpauth://totp/{}?secret={}", account, secret);

    if let Some(issuer) = issuer {
        uri.push_str(&format!("&issuer={}", issuer));
    }

    Ok(uri)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_normalize_secret() {
        assert_eq!(normalize_secret("jbswy3dpehpk3pxp"), "JBSWY3DPEHPK3PXP");
        assert_eq!(normalize_secret("jbsw y3dp ehpk 3pxp"), "JBSWY3DPEHPK3PXP");
        assert_eq!(normalize_secret("jbsw-y3dp-ehpk-3pxp"), "JBSWY3DPEHPK3PXP");
        assert_eq!(normalize_secret("JBSWY3DPEHPK3PXP==="), "JBSWY3DPEHPK3PXP");
        // Test padding addition
        assert_eq!(normalize_secret("MZXW6YQ"), "MZXW6YQ="); // 7 chars -> pad with 1 =
        assert_eq!(normalize_secret("MZXW6"), "MZXW6===");   // 5 chars -> pad with 3 =
    }

    #[test]
    fn test_is_valid_totp_secret() {
        assert!(is_valid_totp_secret("JBSWY3DPEHPK3PXP"));
        assert!(is_valid_totp_secret("jbswy3dpehpk3pxp"));
        assert!(is_valid_totp_secret("jbsw y3dp ehpk 3pxp"));
        assert!(is_valid_totp_secret("MZXW6YQ")); // Valid unpadded
        assert!(!is_valid_totp_secret("")); // Empty
        assert!(!is_valid_totp_secret("invalid-char!")); // Invalid base32 chars
    }

    #[test]
    fn test_totp_generation() {
        // For secret JBSWY3DPEHPK3PXP at 1700000000, standard code is 324550
        let secret = "JBSWY3DPEHPK3PXP";
        let normalized = normalize_secret(secret);
        let mut secret_bytes = base32::decode(Alphabet::Rfc4648 { padding: true }, &normalized).unwrap();
        if secret_bytes.len() < 16 {
            secret_bytes.resize(16, 0);
        }
        let totp = TOTP::new(
            Algorithm::SHA1,
            6,
            1,
            30,
            secret_bytes,
            None,
            String::new(),
        ).unwrap();
        assert_eq!(totp.generate(1700000000), "324550");
    }
}

