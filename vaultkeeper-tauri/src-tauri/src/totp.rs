use std::time::{SystemTime, UNIX_EPOCH};
use totp_rs::{Algorithm, TOTP};

/// Generate a TOTP code from a secret
pub fn generate_totp(secret: &str) -> Result<(String, u64), Box<dyn std::error::Error>> {
    // Clean the secret (remove spaces, convert to uppercase)
    let cleaned = secret.to_uppercase().replace(' ', "");

    // Create TOTP instance
    let totp = TOTP::new(
        Algorithm::SHA1,
        6,
        1,
        30, // 30 second period
        cleaned.as_bytes().to_vec(),
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
    let cleaned = secret.to_uppercase().replace(' ', "");
    !cleaned.is_empty() && cleaned.len() >= 16
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
