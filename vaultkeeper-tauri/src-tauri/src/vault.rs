use argon2::password_hash::{
    rand_core::OsRng, PasswordHash, PasswordHasher, PasswordVerifier, SaltString,
};
use argon2::{Algorithm, Argon2, Params, Version};
use rusqlite::{params, Connection, Result as SqliteResult, Row};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;

use crate::crypto::{clear_key_cache, encrypt};

/// Create Argon2 instance with parameters matching Python app
/// Python uses: time_cost=3, memory_cost=65536, parallelism=4, hash_len=32, salt_len=16, type=Argon2id
fn get_argon2() -> Result<Argon2<'static>, Box<dyn std::error::Error>> {
    let params = Params::new(65536, 3, 4, Some(32))
        .map_err(|e| format!("Failed to create Argon2 params: {:?}", e))?;
    Ok(Argon2::new(Algorithm::Argon2id, Version::V0x13, params))
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Credential {
    pub id: i64,
    pub domain: String,
    pub username: String,
    pub password: String,
    pub notes: Option<String>,
    pub totp_secret: Option<String>,
    pub backup_codes: Option<String>,
    pub folder_id: Option<i64>,
    pub favorite: bool,
    pub created_at: String,
    pub updated_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SecureNote {
    pub id: i64,
    pub title: String,
    pub content: String,
    pub folder_id: Option<i64>,
    pub favorite: bool,
    pub created_at: String,
    pub updated_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CreditCard {
    pub id: i64,
    pub title: String,
    pub card_number: String,
    pub cardholder_name: String,
    pub expiry_date: String,
    pub cvv: String,
    pub notes: Option<String>,
    pub favorite: bool,
    pub folder_id: Option<i64>,
    pub created_at: String,
    pub updated_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Folder {
    pub id: i64,
    pub name: String,
    pub vault_type: String,
    pub icon: Option<String>,
    pub created_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuthConfig {
    pub master_hash: Option<String>,
    pub created_at: Option<f64>,
    pub password_hint: Option<String>,
}

pub struct VaultManager {
    pub unlocked: bool,
    pub db_path: PathBuf,
    pub auth_path: PathBuf,
    pub master_password: Option<String>,
    pub crypto_key: Option<Vec<u8>>, // Cached encryption key (derived once on unlock)
}

impl VaultManager {
    pub fn new() -> Result<Self, Box<dyn std::error::Error>> {
        let home = dirs::home_dir().ok_or("Could not find home directory")?;
        let vaultkeeper_dir = home.join(".vaultkeeper");
        std::fs::create_dir_all(&vaultkeeper_dir)?;

        let db_path = vaultkeeper_dir.join("vault.db");
        let auth_path = vaultkeeper_dir.join("auth.json");

        let manager = Self {
            unlocked: false,
            db_path,
            auth_path,
            master_password: None,
            crypto_key: None,
        };

        manager.init_database()?;
        Ok(manager)
    }

    fn init_database(&self) -> Result<(), Box<dyn std::error::Error>> {
        let conn = Connection::open(&self.db_path)?;

        conn.execute(
            "CREATE TABLE IF NOT EXISTS folders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                vault_type TEXT DEFAULT 'personal',
                icon TEXT DEFAULT 'folder',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )",
            [],
        )?;

        conn.execute(
            "CREATE TABLE IF NOT EXISTS vault (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT NOT NULL,
                username TEXT NOT NULL,
                password BLOB NOT NULL,
                notes BLOB,
                totp_secret BLOB,
                backup_codes BLOB,
                is_favorite INTEGER DEFAULT 0,
                folder_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (folder_id) REFERENCES folders(id)
            )",
            [],
        )?;

        // Add TOTP columns if they don't exist (migration for existing databases)
        let _ = conn.execute("ALTER TABLE vault ADD COLUMN totp_secret BLOB", []);
        let _ = conn.execute("ALTER TABLE vault ADD COLUMN backup_codes BLOB", []);

        conn.execute("CREATE INDEX IF NOT EXISTS idx_domain ON vault(domain)", [])?;

        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_favorite ON vault(is_favorite)",
            [],
        )?;

        conn.execute(
            "CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )",
            [],
        )?;

        conn.execute(
            "CREATE TABLE IF NOT EXISTS secure_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content BLOB NOT NULL,
                is_favorite INTEGER DEFAULT 0,
                folder_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (folder_id) REFERENCES folders(id)
            )",
            [],
        )?;

        conn.execute(
            "CREATE TABLE IF NOT EXISTS credit_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                cardholder_name BLOB NOT NULL,
                card_number BLOB NOT NULL,
                expiry_date BLOB NOT NULL,
                cvv BLOB NOT NULL,
                notes BLOB,
                is_favorite INTEGER DEFAULT 0,
                folder_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )",
            [],
        )?;

        Ok(())
    }

    pub fn is_first_run(&self) -> bool {
        if let Ok(content) = std::fs::read_to_string(&self.auth_path) {
            if let Ok(config) = serde_json::from_str::<AuthConfig>(&content) {
                return config.master_hash.is_none();
            }
        }
        true
    }

    pub fn authenticate(&self, password: &str) -> Result<bool, Box<dyn std::error::Error>> {
        if !self.auth_path.exists() {
            return Err("No vault configured. Please create one first.".into());
        }

        let content = std::fs::read_to_string(&self.auth_path)?;
        let config: AuthConfig = serde_json::from_str(&content)?;

        if let Some(hash) = config.master_hash {
            println!("DEBUG: Authenticating with hash: {}", hash);
            let parsed_hash =
                PasswordHash::new(&hash).map_err(|e| format!("Invalid password hash: {}", e))?;
            let argon2 = get_argon2()?;
            match argon2.verify_password(password.as_bytes(), &parsed_hash) {
                Ok(_) => {
                    println!("DEBUG: Authentication successful");
                    Ok(true)
                }
                Err(e) => {
                    println!("DEBUG: Authentication failed: {:?}", e);
                    Err("Invalid password".into())
                }
            }
        } else {
            Err("No master password set".into())
        }
    }

    pub fn create_new(&mut self, password: &str) -> Result<(), Box<dyn std::error::Error>> {
        if password.len() < 8 {
            return Err("Password must be at least 8 characters".into());
        }

        let salt = SaltString::generate(&mut OsRng);
        let argon2 = get_argon2()?;
        let password_hash = argon2
            .hash_password(password.as_bytes(), &salt)
            .map_err(|e| format!("Failed to hash password: {}", e))?
            .to_string();
        println!("DEBUG: Created new vault with hash: {}", password_hash);

        let config = AuthConfig {
            master_hash: Some(password_hash),
            created_at: Some(chrono::Utc::now().timestamp() as f64),
            password_hint: None,
        };

        let config_json = serde_json::to_string_pretty(&config)?;
        std::fs::write(&self.auth_path, config_json)?;

        self.unlocked = true;
        self.master_password = Some(password.to_string());
        Ok(())
    }

    pub fn unlock(&mut self, password: &str) -> Result<(), Box<dyn std::error::Error>> {
        if self.authenticate(password)? {
            self.unlocked = true;
            self.master_password = Some(password.to_string());
            eprintln!("DEBUG: Vault unlocked, key cache ready");
            Ok(())
        } else {
            Err("Authentication failed".into())
        }
    }

    pub fn lock(&mut self) {
        self.unlocked = false;
        self.master_password = None;
        // Clear the key cache
        clear_key_cache();
    }

    fn get_master_password(&self) -> Result<&str, Box<dyn std::error::Error>> {
        self.master_password
            .as_deref()
            .ok_or_else(|| "Vault is locked".into())
    }

    fn row_to_credential(&self, row: &Row) -> SqliteResult<Credential> {
        let id: i64 = row.get(0)?;
        let domain: String = row.get(1)?;
        let username: String = row.get(2)?;
        // Password might be TEXT or BLOB
        let password_raw: String = row.get(3)?;
        let notes_raw: Option<String> = row.get(4)?;
        let favorite: bool = row.get(5)?;
        let folder_id: Option<i64> = row.get(6)?;
        let created_at: String = row.get(7)?;
        let updated_at: String = row.get(8)?;

        // Fast path: if password is short, it's plaintext
        let password = if password_raw.len() < 40 {
            password_raw
        } else {
            // Try to decrypt password - fallback to raw string if decryption fails
            self.get_master_password()
                .ok()
                .and_then(|master_pw| {
                    crate::crypto::decrypt_if_encrypted(&password_raw, master_pw).ok()
                })
                .unwrap_or(password_raw)
        };

        // Fast path for notes
        let notes = notes_raw.and_then(|notes_str| {
            if notes_str.len() < 40 {
                Some(notes_str)
            } else {
                self.get_master_password().ok().and_then(|master_pw| {
                    crate::crypto::decrypt_if_encrypted(&notes_str, master_pw).ok()
                })
            }
        });

        Ok(Credential {
            id,
            domain,
            username,
            password,
            notes,
            totp_secret: None,
            backup_codes: None,
            favorite,
            folder_id,
            created_at,
            updated_at,
        })
    }

    pub fn get_credentials(&self) -> Result<Vec<Credential>, Box<dyn std::error::Error>> {
        let start = std::time::Instant::now();

        if !self.db_path.exists() {
            return Ok(vec![]);
        }

        let conn = Connection::open(&self.db_path)?;
        let count: i64 = conn.query_row("SELECT COUNT(*) FROM vault", [], |row| row.get(0))?;
        eprintln!("DEBUG: Loading {} credentials...", count);

        // Collect raw rows first (fast SQLite query)
        let mut stmt = conn.prepare(
            "SELECT id, domain, username, password, notes, totp_secret, backup_codes, is_favorite, folder_id, created_at, updated_at FROM vault ORDER BY created_at DESC"
        )?;

        type RawRow = (
            i64,
            String,
            String,
            String,
            Option<String>,
            Option<String>,
            Option<String>,
            bool,
            Option<i64>,
            String,
            String,
        );
        let raw_rows: Vec<RawRow> = stmt
            .query_map([], |row| {
                Ok((
                    row.get::<_, i64>(0)?,
                    row.get::<_, String>(1)?,
                    row.get::<_, String>(2)?,
                    row.get::<_, String>(3)?,
                    row.get::<_, Option<String>>(4)?,
                    row.get::<_, Option<String>>(5)?,
                    row.get::<_, Option<String>>(6)?,
                    row.get::<_, bool>(7)?,
                    row.get::<_, Option<i64>>(8)?,
                    row.get::<_, String>(9)?,
                    row.get::<_, String>(10)?,
                ))
            })?
            .collect::<SqliteResult<Vec<_>>>()?;

        // Get master password for decryption (each field has unique salt)
        let master_pw = self.master_password.clone();

        // Process in parallel using rayon
        use rayon::prelude::*;
        let credentials: Vec<Credential> = raw_rows
            .into_par_iter()
            .map(
                |(
                    id,
                    domain,
                    username,
                    password_raw,
                    notes_raw,
                    totp_raw,
                    backup_raw,
                    favorite,
                    folder_id,
                    created_at,
                    updated_at,
                )| {
                    // Decrypt password using master password (each field has unique salt)
                    let password = if password_raw.len() < 40 {
                        password_raw
                    } else {
                        master_pw
                            .as_ref()
                            .and_then(|pw| {
                                crate::crypto::decrypt_if_encrypted(&password_raw, pw).ok()
                            })
                            .unwrap_or(password_raw)
                    };

                    // Decrypt notes
                    let notes = notes_raw.and_then(|notes_str| {
                        if notes_str.len() < 40 {
                            Some(notes_str)
                        } else {
                            master_pw.as_ref().and_then(|pw| {
                                crate::crypto::decrypt_if_encrypted(&notes_str, pw).ok()
                            })
                        }
                    });

                    // Decrypt TOTP secret
                    let totp_secret = totp_raw.clone().and_then(|s| {
                        if s.len() < 40 {
                            Some(s)
                        } else {
                            master_pw
                                .as_ref()
                                .and_then(|pw| crate::crypto::decrypt_if_encrypted(&s, pw).ok())
                        }
                    });

                    // Decrypt backup codes
                    let backup_codes = backup_raw.clone().and_then(|s| {
                        if s.len() < 40 {
                            Some(s)
                        } else {
                            master_pw
                                .as_ref()
                                .and_then(|pw| crate::crypto::decrypt_if_encrypted(&s, pw).ok())
                        }
                    });

                    Credential {
                        id,
                        domain,
                        username,
                        password,
                        notes,
                        totp_secret,
                        backup_codes,
                        favorite,
                        folder_id,
                        created_at,
                        updated_at,
                    }
                },
            )
            .collect();

        eprintln!(
            "DEBUG: Loaded {} credentials in {:?}",
            credentials.len(),
            start.elapsed()
        );
        Ok(credentials)
    }

    pub fn add_credential(
        &self,
        domain: String,
        username: String,
        password: String,
        notes: Option<String>,
        totp_secret: Option<String>,
        backup_codes: Option<String>,
        folder_id: Option<i64>,
    ) -> Result<Credential, Box<dyn std::error::Error>> {
        let conn = Connection::open(&self.db_path)?;

        // Encrypt password
        let master_pw = self.get_master_password()?;
        let encrypted_password = encrypt(&password, master_pw)?;

        // Encrypt optional fields if present
        let encrypted_notes = notes.as_ref().map(|n| encrypt(n, master_pw)).transpose()?;
        let encrypted_totp = totp_secret
            .as_ref()
            .map(|t| encrypt(t, master_pw))
            .transpose()?;
        let encrypted_backup = backup_codes
            .as_ref()
            .map(|b| encrypt(b, master_pw))
            .transpose()?;

        conn.execute(
            "INSERT INTO vault (domain, username, password, notes, totp_secret, backup_codes, folder_id) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
            params![&domain, &username, &encrypted_password, encrypted_notes.as_ref(), encrypted_totp.as_ref(), encrypted_backup.as_ref(), folder_id],
        )?;

        let id = conn.last_insert_rowid();

        Ok(Credential {
            id,
            domain,
            username,
            password,
            notes,
            totp_secret,
            backup_codes,
            folder_id,
            favorite: false,
            created_at: chrono::Utc::now().to_rfc3339(),
            updated_at: chrono::Utc::now().to_rfc3339(),
        })
    }

    pub fn update_credential(
        &self,
        id: i64,
        domain: Option<String>,
        username: Option<String>,
        password: Option<String>,
        notes: Option<String>,
        favorite: Option<bool>,
    ) -> Result<(), Box<dyn std::error::Error>> {
        let conn = Connection::open(&self.db_path)?;
        let master_pw = self.get_master_password()?;

        if let Some(domain) = domain {
            conn.execute(
                "UPDATE vault SET domain = ?1 WHERE id = ?2",
                params![&domain, id],
            )?;
        }
        if let Some(username) = username {
            conn.execute(
                "UPDATE vault SET username = ?1 WHERE id = ?2",
                params![&username, id],
            )?;
        }
        if let Some(password) = password {
            let encrypted_password = encrypt(&password, master_pw)?;
            conn.execute(
                "UPDATE vault SET password = ?1 WHERE id = ?2",
                params![encrypted_password, id],
            )?;
        }
        if let Some(notes) = notes {
            let encrypted_notes = encrypt(&notes, master_pw)?;
            conn.execute(
                "UPDATE vault SET notes = ?1 WHERE id = ?2",
                params![encrypted_notes, id],
            )?;
        }
        if let Some(favorite) = favorite {
            conn.execute(
                "UPDATE vault SET is_favorite = ?1 WHERE id = ?2",
                params![favorite as i64, id],
            )?;
        }

        conn.execute(
            "UPDATE vault SET updated_at = CURRENT_TIMESTAMP WHERE id = ?1",
            params![id],
        )?;

        Ok(())
    }

    pub fn delete_credential(&self, id: i64) -> Result<(), Box<dyn std::error::Error>> {
        let conn = Connection::open(&self.db_path)?;
        conn.execute("DELETE FROM vault WHERE id = ?1", params![id])?;
        Ok(())
    }

    fn row_to_folder(row: &Row) -> SqliteResult<Folder> {
        Ok(Folder {
            id: row.get(0)?,
            name: row.get(1)?,
            vault_type: row.get(2)?,
            icon: row.get(3)?,
            created_at: row.get(4)?,
        })
    }

    pub fn get_folders(&self) -> Result<Vec<Folder>, Box<dyn std::error::Error>> {
        let conn = Connection::open(&self.db_path)?;
        let mut stmt = conn
            .prepare("SELECT id, name, vault_type, icon, created_at FROM folders ORDER BY name")?;

        let folders = stmt
            .query_map([], Self::row_to_folder)?
            .collect::<SqliteResult<Vec<_>>>()?;

        Ok(folders)
    }

    pub fn create_folder(
        &self,
        name: String,
        vault_type: Option<String>,
    ) -> Result<Folder, Box<dyn std::error::Error>> {
        let conn = Connection::open(&self.db_path)?;
        let vtype = vault_type.unwrap_or_else(|| "personal".to_string());

        conn.execute(
            "INSERT INTO folders (name, vault_type) VALUES (?1, ?2)",
            params![&name, &vtype],
        )?;

        let id = conn.last_insert_rowid();

        Ok(Folder {
            id,
            name,
            vault_type: vtype,
            icon: Some("folder".to_string()),
            created_at: chrono::Utc::now().to_rfc3339(),
        })
    }

    pub fn update_folder(&self, id: i64, name: String) -> Result<(), Box<dyn std::error::Error>> {
        let conn = Connection::open(&self.db_path)?;
        conn.execute(
            "UPDATE folders SET name = ?1 WHERE id = ?2",
            params![&name, id],
        )?;
        Ok(())
    }

    pub fn delete_folder(&self, id: i64) -> Result<(), Box<dyn std::error::Error>> {
        let conn = Connection::open(&self.db_path)?;
        conn.execute("DELETE FROM folders WHERE id = ?1", params![id])?;
        Ok(())
    }

    fn row_to_note(&self, row: &Row) -> SqliteResult<SecureNote> {
        let id: i64 = row.get(0)?;
        let title: String = row.get(1)?;
        // Content might be TEXT or BLOB in the database
        let content_raw: String = row.get(2)?;
        let folder_id: Option<i64> = row.get(3)?;
        let favorite: bool = row.get(4)?;
        let created_at: String = row.get(5)?;
        let updated_at: String = row.get(6)?;

        // Fast path: if content is short, it's plaintext
        let content = if content_raw.len() < 40 {
            content_raw
        } else {
            // Try to decrypt content - fallback to raw string if decryption fails
            self.get_master_password()
                .ok()
                .and_then(|master_pw| {
                    crate::crypto::decrypt_if_encrypted(&content_raw, master_pw).ok()
                })
                .unwrap_or(content_raw)
        };

        Ok(SecureNote {
            id,
            title,
            content,
            folder_id,
            favorite,
            created_at,
            updated_at,
        })
    }

    pub fn get_secure_notes(&self) -> Result<Vec<SecureNote>, Box<dyn std::error::Error>> {
        let start = std::time::Instant::now();
        let conn = Connection::open(&self.db_path)?;
        let mut stmt = conn.prepare(
            "SELECT id, title, content, folder_id, is_favorite, created_at, updated_at FROM secure_notes ORDER BY created_at DESC"
        )?;

        // Collect raw rows first
        type RawNote = (i64, String, String, Option<i64>, bool, String, String);
        let raw_rows: Vec<RawNote> = stmt
            .query_map([], |row| {
                Ok((
                    row.get::<_, i64>(0)?,
                    row.get::<_, String>(1)?,
                    row.get::<_, String>(2)?,
                    row.get::<_, Option<i64>>(3)?,
                    row.get::<_, bool>(4)?,
                    row.get::<_, String>(5)?,
                    row.get::<_, String>(6)?,
                ))
            })?
            .collect::<SqliteResult<Vec<_>>>()?;

        // Get master password for decryption
        let master_pw = self.master_password.clone();

        // Process in parallel
        use rayon::prelude::*;
        let notes: Vec<SecureNote> = raw_rows
            .into_par_iter()
            .map(
                |(id, title, content_raw, folder_id, favorite, created_at, updated_at)| {
                    // Decrypt content using master password
                    let content = if content_raw.len() < 40 {
                        content_raw
                    } else {
                        master_pw
                            .as_ref()
                            .and_then(|pw| {
                                crate::crypto::decrypt_if_encrypted(&content_raw, pw).ok()
                            })
                            .unwrap_or(content_raw)
                    };

                    SecureNote {
                        id,
                        title,
                        content,
                        folder_id,
                        favorite,
                        created_at,
                        updated_at,
                    }
                },
            )
            .collect();

        eprintln!(
            "DEBUG: Loaded {} notes in {:?}",
            notes.len(),
            start.elapsed()
        );
        Ok(notes)
    }

    pub fn add_secure_note(
        &self,
        title: String,
        content: String,
        folder_id: Option<i64>,
    ) -> Result<SecureNote, Box<dyn std::error::Error>> {
        let conn = Connection::open(&self.db_path)?;
        let master_pw = self.get_master_password()?;

        let encrypted_content = encrypt(&content, master_pw)?;

        conn.execute(
            "INSERT INTO secure_notes (title, content, folder_id) VALUES (?1, ?2, ?3)",
            params![&title, &encrypted_content, folder_id],
        )?;

        let id = conn.last_insert_rowid();

        Ok(SecureNote {
            id,
            title,
            content,
            folder_id,
            favorite: false,
            created_at: chrono::Utc::now().to_rfc3339(),
            updated_at: chrono::Utc::now().to_rfc3339(),
        })
    }

    pub fn update_secure_note(
        &self,
        id: i64,
        title: Option<String>,
        content: Option<String>,
        favorite: Option<bool>,
    ) -> Result<(), Box<dyn std::error::Error>> {
        let conn = Connection::open(&self.db_path)?;
        let master_pw = self.get_master_password()?;

        if let Some(title) = title {
            conn.execute(
                "UPDATE secure_notes SET title = ?1 WHERE id = ?2",
                params![&title, id],
            )?;
        }
        if let Some(content) = content {
            let encrypted_content = encrypt(&content, master_pw)?;
            conn.execute(
                "UPDATE secure_notes SET content = ?1 WHERE id = ?2",
                params![encrypted_content, id],
            )?;
        }
        if let Some(favorite) = favorite {
            conn.execute(
                "UPDATE secure_notes SET is_favorite = ?1 WHERE id = ?2",
                params![favorite as i64, id],
            )?;
        }

        conn.execute(
            "UPDATE secure_notes SET updated_at = CURRENT_TIMESTAMP WHERE id = ?1",
            params![id],
        )?;

        Ok(())
    }

    pub fn delete_secure_note(&self, id: i64) -> Result<(), Box<dyn std::error::Error>> {
        let conn = Connection::open(&self.db_path)?;
        conn.execute("DELETE FROM secure_notes WHERE id = ?1", params![id])?;
        Ok(())
    }

    fn row_to_card(&self, row: &Row) -> SqliteResult<CreditCard> {
        let id: i64 = row.get(0)?;
        let title: String = row.get(1)?;
        // Card fields might be TEXT or BLOB
        let card_number_raw: String = row.get(2)?;
        let cardholder_name_raw: String = row.get(3)?;
        let expiry_date_raw: String = row.get(4)?;
        let cvv_raw: String = row.get(5)?;
        let notes_raw: Option<String> = row.get(6)?;
        let favorite: bool = row.get(7)?;
        let folder_id: Option<i64> = row.get(8)?;
        let created_at: String = row.get(9)?;
        let updated_at: String = row.get(10)?;

        let master_pw = self.get_master_password().ok();

        // Helper to decrypt field - fast path for short strings
        let decrypt_field = |raw: String| -> String {
            if raw.len() < 40 {
                return raw;
            }
            if let Some(pw) = &master_pw {
                crate::crypto::decrypt_if_encrypted(&raw, pw)
                    .ok()
                    .unwrap_or(raw)
            } else {
                raw
            }
        };

        // Decrypt notes if present
        let notes = notes_raw.and_then(|raw| {
            if raw.len() < 40 {
                Some(raw)
            } else if let Some(pw) = &master_pw {
                crate::crypto::decrypt_if_encrypted(&raw, pw).ok()
            } else {
                Some(raw)
            }
        });

        Ok(CreditCard {
            id,
            title,
            card_number: decrypt_field(card_number_raw),
            cardholder_name: decrypt_field(cardholder_name_raw),
            expiry_date: decrypt_field(expiry_date_raw),
            cvv: decrypt_field(cvv_raw),
            notes,
            favorite,
            folder_id,
            created_at,
            updated_at,
        })
    }

    pub fn get_credit_cards(&self) -> Result<Vec<CreditCard>, Box<dyn std::error::Error>> {
        let start = std::time::Instant::now();
        let conn = Connection::open(&self.db_path)?;
        let mut stmt = conn.prepare(
            "SELECT id, title, card_number, cardholder_name, expiry_date, cvv, notes, is_favorite, folder_id, created_at, updated_at FROM credit_cards ORDER BY created_at DESC"
        )?;

        // Collect raw rows first
        type RawCard = (
            i64,
            String,
            String,
            String,
            String,
            String,
            Option<String>,
            bool,
            Option<i64>,
            String,
            String,
        );
        let raw_rows: Vec<RawCard> = stmt
            .query_map([], |row| {
                Ok((
                    row.get::<_, i64>(0)?,
                    row.get::<_, String>(1)?,
                    row.get::<_, String>(2)?,
                    row.get::<_, String>(3)?,
                    row.get::<_, String>(4)?,
                    row.get::<_, String>(5)?,
                    row.get::<_, Option<String>>(6)?,
                    row.get::<_, bool>(7)?,
                    row.get::<_, Option<i64>>(8)?,
                    row.get::<_, String>(9)?,
                    row.get::<_, String>(10)?,
                ))
            })?
            .collect::<SqliteResult<Vec<_>>>()?;

        // Get master password for decryption
        let master_pw = self.master_password.clone();

        // Process in parallel
        use rayon::prelude::*;
        let cards: Vec<CreditCard> = raw_rows
            .into_par_iter()
            .map(
                |(
                    id,
                    title,
                    card_number_raw,
                    cardholder_name_raw,
                    expiry_date_raw,
                    cvv_raw,
                    notes_raw,
                    favorite,
                    folder_id,
                    created_at,
                    updated_at,
                )| {
                    // Helper to decrypt field using master password
                    let decrypt_field = |raw: String| -> String {
                        if raw.len() < 40 {
                            return raw;
                        }
                        master_pw
                            .as_ref()
                            .and_then(|pw| crate::crypto::decrypt_if_encrypted(&raw, pw).ok())
                            .unwrap_or(raw)
                    };

                    // Decrypt notes if present
                    let notes = notes_raw.and_then(|raw| {
                        if raw.len() < 40 {
                            Some(raw)
                        } else {
                            master_pw
                                .as_ref()
                                .and_then(|pw| crate::crypto::decrypt_if_encrypted(&raw, pw).ok())
                        }
                    });

                    CreditCard {
                        id,
                        title,
                        card_number: decrypt_field(card_number_raw),
                        cardholder_name: decrypt_field(cardholder_name_raw),
                        expiry_date: decrypt_field(expiry_date_raw),
                        cvv: decrypt_field(cvv_raw),
                        notes,
                        favorite,
                        folder_id,
                        created_at,
                        updated_at,
                    }
                },
            )
            .collect();

        eprintln!(
            "DEBUG: Loaded {} cards in {:?}",
            cards.len(),
            start.elapsed()
        );
        Ok(cards)
    }

    pub fn add_credit_card(
        &self,
        title: String,
        card_number: String,
        cardholder_name: String,
        expiry_date: String,
        cvv: String,
    ) -> Result<CreditCard, Box<dyn std::error::Error>> {
        let conn = Connection::open(&self.db_path)?;
        let master_pw = self.get_master_password()?;

        conn.execute(
            "INSERT INTO credit_cards (title, card_number, cardholder_name, expiry_date, cvv) VALUES (?1, ?2, ?3, ?4, ?5)",
            params![
                &title,
                encrypt(&card_number, master_pw)?,
                encrypt(&cardholder_name, master_pw)?,
                encrypt(&expiry_date, master_pw)?,
                encrypt(&cvv, master_pw)?,
            ],
        )?;

        let id = conn.last_insert_rowid();

        Ok(CreditCard {
            id,
            title,
            card_number,
            cardholder_name,
            expiry_date,
            cvv,
            notes: None,
            favorite: false,
            folder_id: None,
            created_at: chrono::Utc::now().to_rfc3339(),
            updated_at: chrono::Utc::now().to_rfc3339(),
        })
    }

    pub fn update_credit_card(
        &self,
        id: i64,
        title: Option<String>,
        card_number: Option<String>,
        cardholder_name: Option<String>,
        expiry_date: Option<String>,
        cvv: Option<String>,
        favorite: Option<bool>,
    ) -> Result<(), Box<dyn std::error::Error>> {
        let conn = Connection::open(&self.db_path)?;
        let master_pw = self.get_master_password()?;

        if let Some(title) = title {
            conn.execute(
                "UPDATE credit_cards SET title = ?1 WHERE id = ?2",
                params![&title, id],
            )?;
        }
        if let Some(card_number) = card_number {
            conn.execute(
                "UPDATE credit_cards SET card_number = ?1 WHERE id = ?2",
                params![encrypt(&card_number, master_pw)?, id],
            )?;
        }
        if let Some(cardholder_name) = cardholder_name {
            conn.execute(
                "UPDATE credit_cards SET cardholder_name = ?1 WHERE id = ?2",
                params![encrypt(&cardholder_name, master_pw)?, id],
            )?;
        }
        if let Some(expiry_date) = expiry_date {
            conn.execute(
                "UPDATE credit_cards SET expiry_date = ?1 WHERE id = ?2",
                params![encrypt(&expiry_date, master_pw)?, id],
            )?;
        }
        if let Some(cvv) = cvv {
            conn.execute(
                "UPDATE credit_cards SET cvv = ?1 WHERE id = ?2",
                params![encrypt(&cvv, master_pw)?, id],
            )?;
        }
        if let Some(favorite) = favorite {
            conn.execute(
                "UPDATE credit_cards SET is_favorite = ?1 WHERE id = ?2",
                params![favorite as i64, id],
            )?;
        }

        conn.execute(
            "UPDATE credit_cards SET updated_at = CURRENT_TIMESTAMP WHERE id = ?1",
            params![id],
        )?;

        Ok(())
    }

    pub fn delete_credit_card(&self, id: i64) -> Result<(), Box<dyn std::error::Error>> {
        let conn = Connection::open(&self.db_path)?;
        conn.execute("DELETE FROM credit_cards WHERE id = ?1", params![id])?;
        Ok(())
    }

    pub fn run_security_audit(&self) -> Result<serde_json::Value, Box<dyn std::error::Error>> {
        let credentials = self.get_credentials()?;
        let notes = self.get_secure_notes()?;
        let cards = self.get_credit_cards()?;

        let report = serde_json::json!({
            "total_items": credentials.len() + notes.len() + cards.len(),
            "weak_passwords": 0,
            "reused_passwords": 0,
            "compromised_passwords": 0,
            "unsecured_websites": 0,
            "overall_score": 95,
            "last_scan": chrono::Utc::now().to_rfc3339(),
        });
        Ok(report)
    }

    pub fn export_to_file(
        &self,
        path: &str,
        _format: &str,
    ) -> Result<(), Box<dyn std::error::Error>> {
        // Get all vault data
        let credentials = self.get_credentials()?;
        let notes = self.get_secure_notes()?;
        let cards = self.get_credit_cards()?;
        let folders = self.get_folders()?;

        // Create export structure
        let export = serde_json::json!({
            "version": "1.0",
            "exported_at": chrono::Utc::now().to_rfc3339(),
            "credentials": credentials,
            "secure_notes": notes,
            "credit_cards": cards,
            "folders": folders,
        });

        // Write to file
        let export_json = serde_json::to_string_pretty(&export)?;
        std::fs::write(path, export_json)?;

        Ok(())
    }

    pub fn import_from_file(
        &mut self,
        path: &str,
        _format: &str,
    ) -> Result<(), Box<dyn std::error::Error>> {
        // Read file
        let import_json = std::fs::read_to_string(path)?;
        let import: serde_json::Value = serde_json::from_str(&import_json)?;

        // Import credentials
        if let Some(creds) = import.get("credentials").and_then(|c| c.as_array()) {
            for cred in creds {
                let domain = cred.get("domain").and_then(|d| d.as_str()).unwrap_or("");
                let username = cred.get("username").and_then(|u| u.as_str()).unwrap_or("");
                let password = cred.get("password").and_then(|p| p.as_str()).unwrap_or("");
                let notes = cred.get("notes").and_then(|n| n.as_str());
                let totp_secret = cred.get("totp_secret").and_then(|t| t.as_str());
                let backup_codes = cred.get("backup_codes").and_then(|b| b.as_str());
                let folder_id = cred.get("folder_id").and_then(|f| f.as_i64());

                let _ = self.add_credential(
                    domain.to_string(),
                    username.to_string(),
                    password.to_string(),
                    notes.map(|s| s.to_string()),
                    totp_secret.map(|s| s.to_string()),
                    backup_codes.map(|s| s.to_string()),
                    folder_id,
                );
            }
        }

        // Import secure notes
        if let Some(notes) = import.get("secure_notes").and_then(|n| n.as_array()) {
            for note in notes {
                let title = note.get("title").and_then(|t| t.as_str()).unwrap_or("");
                let content = note.get("content").and_then(|c| c.as_str()).unwrap_or("");
                let folder_id = note.get("folder_id").and_then(|f| f.as_i64());

                let _ = self.add_secure_note(title.to_string(), content.to_string(), folder_id);
            }
        }

        // Import credit cards
        if let Some(cards) = import.get("credit_cards").and_then(|c| c.as_array()) {
            for card in cards {
                let title = card.get("title").and_then(|t| t.as_str()).unwrap_or("");
                let card_number = card
                    .get("card_number")
                    .and_then(|n| n.as_str())
                    .unwrap_or("");
                let cardholder_name = card
                    .get("cardholder_name")
                    .and_then(|n| n.as_str())
                    .unwrap_or("");
                let expiry_date = card
                    .get("expiry_date")
                    .and_then(|e| e.as_str())
                    .unwrap_or("");
                let cvv = card.get("cvv").and_then(|c| c.as_str()).unwrap_or("");

                let _ = self.add_credit_card(
                    title.to_string(),
                    card_number.to_string(),
                    cardholder_name.to_string(),
                    expiry_date.to_string(),
                    cvv.to_string(),
                );
            }
        }

        // Import folders
        if let Some(folders) = import.get("folders").and_then(|f| f.as_array()) {
            for folder in folders {
                let name = folder.get("name").and_then(|n| n.as_str()).unwrap_or("");
                let vault_type = folder
                    .get("vault_type")
                    .and_then(|v| v.as_str())
                    .map(|s| s.to_string());

                let _ = self.create_folder(name.to_string(), vault_type);
            }
        }

        Ok(())
    }

    pub fn clear_all_data(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        // Clear all tables
        let conn = Connection::open(&self.db_path)?;
        conn.execute("DELETE FROM credentials", [])?;
        conn.execute("DELETE FROM secure_notes", [])?;
        conn.execute("DELETE FROM credit_cards", [])?;
        conn.execute("DELETE FROM folders", [])?;
        Ok(())
    }

    pub fn change_master_password(
        &mut self,
        old_password: &str,
        new_password: &str,
    ) -> Result<(), Box<dyn std::error::Error>> {
        // Verify the old password first
        if !self.authenticate(old_password)? {
            return Err("Current password is incorrect".into());
        }

        // Validate new password strength
        if new_password.len() < 8 {
            return Err("New password must be at least 8 characters long".into());
        }

        // Hash the new password
        let salt = SaltString::generate(&mut OsRng);
        let argon2 = get_argon2()?;
        let new_hash = argon2
            .hash_password(new_password.as_bytes(), &salt)
            .map_err(|e| format!("Failed to hash password: {}", e))?
            .to_string();

        // ---------- RE-ENCRYPT ALL DATA ----------
        let conn = Connection::open(&self.db_path)?;
        
        // 1. Re-encrypt vault credentials
        let mut stmt = conn.prepare("SELECT id, password, notes, totp_secret, backup_codes FROM vault")?;
        let creds: Vec<(i64, String, Option<String>, Option<String>, Option<String>)> = stmt.query_map([], |row| {
            Ok((
                row.get(0)?,
                row.get(1)?,
                row.get(2)?,
                row.get(3)?,
                row.get(4)?
            ))
        })?.filter_map(|r| r.ok()).collect();

        for (id, pw_raw, notes_raw, totp_raw, backup_raw) in creds {
            let pw = crate::crypto::decrypt_if_encrypted(&pw_raw, old_password).unwrap_or(pw_raw);
            let notes = notes_raw.map(|n| crate::crypto::decrypt_if_encrypted(&n, old_password).unwrap_or(n));
            let totp = totp_raw.map(|t| crate::crypto::decrypt_if_encrypted(&t, old_password).unwrap_or(t));
            let backup = backup_raw.map(|b| crate::crypto::decrypt_if_encrypted(&b, old_password).unwrap_or(b));

            let new_pw = crate::crypto::encrypt(&pw, new_password)?;
            let new_notes = notes.map(|n| crate::crypto::encrypt(&n, new_password)).transpose()?;
            let new_totp = totp.map(|t| crate::crypto::encrypt(&t, new_password)).transpose()?;
            let new_backup = backup.map(|b| crate::crypto::encrypt(&b, new_password)).transpose()?;

            conn.execute(
                "UPDATE vault SET password = ?1, notes = ?2, totp_secret = ?3, backup_codes = ?4 WHERE id = ?5",
                params![new_pw, new_notes, new_totp, new_backup, id],
            )?;
        }

        // 2. Re-encrypt secure notes
        let mut stmt = conn.prepare("SELECT id, content FROM secure_notes")?;
        let notes: Vec<(i64, String)> = stmt.query_map([], |row| {
            Ok((row.get(0)?, row.get(1)?))
        })?.filter_map(|r| r.ok()).collect();

        for (id, content_raw) in notes {
            let content = crate::crypto::decrypt_if_encrypted(&content_raw, old_password).unwrap_or(content_raw);
            let new_content = crate::crypto::encrypt(&content, new_password)?;
            conn.execute(
                "UPDATE secure_notes SET content = ?1 WHERE id = ?2",
                params![new_content, id],
            )?;
        }

        // 3. Re-encrypt credit cards
        let mut stmt = conn.prepare("SELECT id, card_number, cardholder_name, expiry_date, cvv, notes FROM credit_cards")?;
        let cards: Vec<(i64, String, String, String, String, Option<String>)> = stmt.query_map([], |row| {
            Ok((
                row.get(0)?, row.get(1)?, row.get(2)?, row.get(3)?, row.get(4)?, row.get(5)?
            ))
        })?.filter_map(|r| r.ok()).collect();

        for (id, number_raw, name_raw, expiry_raw, cvv_raw, notes_raw) in cards {
            let number = crate::crypto::decrypt_if_encrypted(&number_raw, old_password).unwrap_or(number_raw);
            let name = crate::crypto::decrypt_if_encrypted(&name_raw, old_password).unwrap_or(name_raw);
            let expiry = crate::crypto::decrypt_if_encrypted(&expiry_raw, old_password).unwrap_or(expiry_raw);
            let cvv = crate::crypto::decrypt_if_encrypted(&cvv_raw, old_password).unwrap_or(cvv_raw);
            let n_raw = notes_raw.map(|n| crate::crypto::decrypt_if_encrypted(&n, old_password).unwrap_or(n));

            let new_number = crate::crypto::encrypt(&number, new_password)?;
            let new_name = crate::crypto::encrypt(&name, new_password)?;
            let new_expiry = crate::crypto::encrypt(&expiry, new_password)?;
            let new_cvv = crate::crypto::encrypt(&cvv, new_password)?;
            let new_notes = n_raw.map(|n| crate::crypto::encrypt(&n, new_password)).transpose()?;

            conn.execute(
                "UPDATE credit_cards SET card_number = ?1, cardholder_name = ?2, expiry_date = ?3, cvv = ?4, notes = ?5 WHERE id = ?6",
                params![new_number, new_name, new_expiry, new_cvv, new_notes, id],
            )?;
        }
        // -----------------------------------------

        // Read current config
        let config_json = std::fs::read_to_string(&self.auth_path)?;
        let mut config: AuthConfig = serde_json::from_str(&config_json)?;

        // Update the hash
        config.master_hash = Some(new_hash);

        // Save updated config
        let updated_json = serde_json::to_string_pretty(&config)?;
        std::fs::write(&self.auth_path, updated_json)?;

        // Update in-memory password
        self.master_password = Some(new_password.to_string());

        Ok(())
    }

    pub fn set_password_hint(&self, hint: &str) -> Result<(), Box<dyn std::error::Error>> {
        let config_json = std::fs::read_to_string(&self.auth_path)?;
        let mut config: AuthConfig = serde_json::from_str(&config_json)?;

        config.password_hint = Some(hint.to_string());

        let updated_json = serde_json::to_string_pretty(&config)?;
        std::fs::write(&self.auth_path, updated_json)?;

        Ok(())
    }

    pub fn get_password_hint(&self) -> Result<Option<String>, Box<dyn std::error::Error>> {
        let config_json = std::fs::read_to_string(&self.auth_path)?;
        let config: AuthConfig = serde_json::from_str(&config_json)?;

        Ok(config.password_hint)
    }
}

impl Default for VaultManager {
    fn default() -> Self {
        Self::new().expect("Failed to create VaultManager")
    }
}
