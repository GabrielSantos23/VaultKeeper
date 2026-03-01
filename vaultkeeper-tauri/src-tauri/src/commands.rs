use serde::{Deserialize, Serialize};
use tauri::State;
use std::sync::Mutex;

use crate::vault::{VaultManager, Credential, SecureNote, CreditCard, Folder};
use crate::crypto::{generate_password as gen_password, check_password_strength as check_strength};

pub struct AppState {
    pub vault: Mutex<VaultManager>,
}

impl AppState {
    pub fn new() -> Result<Self, Box<dyn std::error::Error>> {
        Ok(Self {
            vault: Mutex::new(VaultManager::new()?),
        })
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ApiResponse<T> {
    pub success: bool,
    pub data: Option<T>,
    pub error: Option<String>,
}

#[tauri::command]
pub async fn check_first_run(state: State<'_, AppState>) -> Result<ApiResponse<bool>, String> {
    let vault = state.vault.lock().map_err(|e| e.to_string())?;
    let is_first = vault.is_first_run();
    Ok(ApiResponse { success: true, data: Some(is_first), error: None })
}

#[tauri::command]
pub async fn authenticate(state: State<'_, AppState>, password: String) -> Result<ApiResponse<bool>, String> {
    let vault = state.vault.lock().map_err(|e| e.to_string())?;
    match vault.authenticate(&password) {
        Ok(_) => Ok(ApiResponse { success: true, data: Some(true), error: None }),
        Err(e) => Ok(ApiResponse { success: false, data: Some(false), error: Some(e.to_string()) }),
    }
}

#[tauri::command]
pub async fn create_vault(state: State<'_, AppState>, password: String) -> Result<ApiResponse<bool>, String> {
    let mut vault = state.vault.lock().map_err(|e| e.to_string())?;
    match vault.create_new(&password) {
        Ok(_) => Ok(ApiResponse { success: true, data: Some(true), error: None }),
        Err(e) => Ok(ApiResponse { success: false, data: Some(false), error: Some(e.to_string()) }),
    }
}

#[tauri::command]
pub async fn unlock_vault(state: State<'_, AppState>, password: String) -> Result<ApiResponse<bool>, String> {
    let mut vault = state.vault.lock().map_err(|e| e.to_string())?;
    match vault.unlock(&password) {
        Ok(_) => Ok(ApiResponse { success: true, data: Some(true), error: None }),
        Err(e) => Ok(ApiResponse { success: false, data: Some(false), error: Some(e.to_string()) }),
    }
}

#[tauri::command]
pub async fn lock_vault(state: State<'_, AppState>) -> Result<ApiResponse<bool>, String> {
    let mut vault = state.vault.lock().map_err(|e| e.to_string())?;
    vault.lock();
    Ok(ApiResponse { success: true, data: Some(true), error: None })
}

#[tauri::command]
pub async fn get_credentials(state: State<'_, AppState>) -> Result<ApiResponse<Vec<Credential>>, String> {
    let vault = state.vault.lock().map_err(|e| e.to_string())?;
    match vault.get_credentials() {
        Ok(creds) => Ok(ApiResponse { success: true, data: Some(creds), error: None }),
        Err(e) => {
            eprintln!("Error getting credentials: {}", e);
            Ok(ApiResponse { success: false, data: None, error: Some(e.to_string()) })
        }
    }
}

#[tauri::command]
pub async fn add_credential(
    state: State<'_, AppState>,
    domain: String,
    username: String,
    password: String,
    notes: Option<String>,
    totp_secret: Option<String>,
    backup_codes: Option<String>,
    folder_id: Option<i64>,
) -> Result<ApiResponse<Credential>, String> {
    let vault = state.vault.lock().map_err(|e| e.to_string())?;
    match vault.add_credential(domain, username, password, notes, totp_secret, backup_codes, folder_id) {
        Ok(cred) => Ok(ApiResponse { success: true, data: Some(cred), error: None }),
        Err(e) => Ok(ApiResponse { success: false, data: None, error: Some(e.to_string()) }),
    }
}

#[tauri::command]
pub async fn update_credential(
    state: State<'_, AppState>,
    id: i64,
    domain: Option<String>,
    username: Option<String>,
    password: Option<String>,
    notes: Option<String>,
    favorite: Option<bool>,
) -> Result<ApiResponse<bool>, String> {
    let vault = state.vault.lock().map_err(|e| e.to_string())?;
    match vault.update_credential(id, domain, username, password, notes, favorite) {
        Ok(_) => Ok(ApiResponse { success: true, data: Some(true), error: None }),
        Err(e) => Ok(ApiResponse { success: false, data: Some(false), error: Some(e.to_string()) }),
    }
}

#[tauri::command]
pub async fn update_credit_card(
    state: State<'_, AppState>,
    id: i64,
    title: Option<String>,
    card_number: Option<String>,
    cardholder_name: Option<String>,
    expiry_date: Option<String>,
    cvv: Option<String>,
    favorite: Option<bool>,
) -> Result<ApiResponse<bool>, String> {
    let vault = state.vault.lock().map_err(|e| e.to_string())?;
    match vault.update_credit_card(id, title, card_number, cardholder_name, expiry_date, cvv, favorite) {
        Ok(_) => Ok(ApiResponse { success: true, data: Some(true), error: None }),
        Err(e) => Ok(ApiResponse { success: false, data: Some(false), error: Some(e.to_string()) }),
    }
}

#[tauri::command]
pub async fn delete_credential(state: State<'_, AppState>, id: i64) -> Result<ApiResponse<bool>, String> {
    let vault = state.vault.lock().map_err(|e| e.to_string())?;
    match vault.delete_credential(id) {
        Ok(_) => Ok(ApiResponse { success: true, data: Some(true), error: None }),
        Err(e) => Ok(ApiResponse { success: false, data: Some(false), error: Some(e.to_string()) }),
    }
}

#[tauri::command]
pub async fn get_folders(state: State<'_, AppState>) -> Result<ApiResponse<Vec<Folder>>, String> {
    let vault = state.vault.lock().map_err(|e| e.to_string())?;
    match vault.get_folders() {
        Ok(folders) => Ok(ApiResponse { success: true, data: Some(folders), error: None }),
        Err(e) => Ok(ApiResponse { success: false, data: None, error: Some(e.to_string()) }),
    }
}

#[tauri::command]
pub async fn create_folder(
    state: State<'_, AppState>,
    name: String,
    vault_type: Option<String>,
) -> Result<ApiResponse<Folder>, String> {
    let vault = state.vault.lock().map_err(|e| e.to_string())?;
    match vault.create_folder(name, vault_type) {
        Ok(folder) => Ok(ApiResponse { success: true, data: Some(folder), error: None }),
        Err(e) => Ok(ApiResponse { success: false, data: None, error: Some(e.to_string()) }),
    }
}

#[tauri::command]
pub async fn update_folder(
    state: State<'_, AppState>,
    id: i64,
    name: String,
) -> Result<ApiResponse<bool>, String> {
    let vault = state.vault.lock().map_err(|e| e.to_string())?;
    match vault.update_folder(id, name) {
        Ok(_) => Ok(ApiResponse { success: true, data: Some(true), error: None }),
        Err(e) => Ok(ApiResponse { success: false, data: Some(false), error: Some(e.to_string()) }),
    }
}

#[tauri::command]
pub async fn delete_folder(state: State<'_, AppState>, id: i64) -> Result<ApiResponse<bool>, String> {
    let vault = state.vault.lock().map_err(|e| e.to_string())?;
    match vault.delete_folder(id) {
        Ok(_) => Ok(ApiResponse { success: true, data: Some(true), error: None }),
        Err(e) => Ok(ApiResponse { success: false, data: Some(false), error: Some(e.to_string()) }),
    }
}

#[tauri::command]
pub async fn get_secure_notes(state: State<'_, AppState>) -> Result<ApiResponse<Vec<SecureNote>>, String> {
    let vault = state.vault.lock().map_err(|e| e.to_string())?;
    match vault.get_secure_notes() {
        Ok(notes) => Ok(ApiResponse { success: true, data: Some(notes), error: None }),
        Err(e) => {
            eprintln!("Error getting secure notes: {}", e);
            Ok(ApiResponse { success: false, data: None, error: Some(e.to_string()) })
        }
    }
}

#[tauri::command]
pub async fn add_secure_note(
    state: State<'_, AppState>,
    title: String,
    content: String,
    folder_id: Option<i64>,
) -> Result<ApiResponse<SecureNote>, String> {
    let vault = state.vault.lock().map_err(|e| e.to_string())?;
    match vault.add_secure_note(title, content, folder_id) {
        Ok(note) => Ok(ApiResponse { success: true, data: Some(note), error: None }),
        Err(e) => Ok(ApiResponse { success: false, data: None, error: Some(e.to_string()) }),
    }
}

#[tauri::command]
pub async fn update_secure_note(
    state: State<'_, AppState>,
    id: i64,
    title: Option<String>,
    content: Option<String>,
    favorite: Option<bool>,
) -> Result<ApiResponse<bool>, String> {
    let vault = state.vault.lock().map_err(|e| e.to_string())?;
    match vault.update_secure_note(id, title, content, favorite) {
        Ok(_) => Ok(ApiResponse { success: true, data: Some(true), error: None }),
        Err(e) => Ok(ApiResponse { success: false, data: Some(false), error: Some(e.to_string()) }),
    }
}

#[tauri::command]
pub async fn delete_secure_note(state: State<'_, AppState>, id: i64) -> Result<ApiResponse<bool>, String> {
    let vault = state.vault.lock().map_err(|e| e.to_string())?;
    match vault.delete_secure_note(id) {
        Ok(_) => Ok(ApiResponse { success: true, data: Some(true), error: None }),
        Err(e) => Ok(ApiResponse { success: false, data: Some(false), error: Some(e.to_string()) }),
    }
}

#[tauri::command]
pub async fn get_credit_cards(state: State<'_, AppState>) -> Result<ApiResponse<Vec<CreditCard>>, String> {
    let vault = state.vault.lock().map_err(|e| e.to_string())?;
    match vault.get_credit_cards() {
        Ok(cards) => Ok(ApiResponse { success: true, data: Some(cards), error: None }),
        Err(e) => {
            eprintln!("Error getting credit cards: {}", e);
            Ok(ApiResponse { success: false, data: None, error: Some(e.to_string()) })
        }
    }
}

#[tauri::command]
pub async fn add_credit_card(
    state: State<'_, AppState>,
    title: String,
    card_number: String,
    cardholder_name: String,
    expiry_date: String,
    cvv: String,
) -> Result<ApiResponse<CreditCard>, String> {
    let vault = state.vault.lock().map_err(|e| e.to_string())?;
    match vault.add_credit_card(title, card_number, cardholder_name, expiry_date, cvv) {
        Ok(card) => Ok(ApiResponse { success: true, data: Some(card), error: None }),
        Err(e) => Ok(ApiResponse { success: false, data: None, error: Some(e.to_string()) }),
    }
}

#[tauri::command]
pub async fn delete_credit_card(state: State<'_, AppState>, id: i64) -> Result<ApiResponse<bool>, String> {
    let vault = state.vault.lock().map_err(|e| e.to_string())?;
    match vault.delete_credit_card(id) {
        Ok(_) => Ok(ApiResponse { success: true, data: Some(true), error: None }),
        Err(e) => Ok(ApiResponse { success: false, data: Some(false), error: Some(e.to_string()) }),
    }
}

#[tauri::command]
pub fn generate_password(
    length: u32,
    include_uppercase: bool,
    include_lowercase: bool,
    include_numbers: bool,
    include_symbols: bool,
) -> Result<String, String> {
    gen_password(length, include_uppercase, include_lowercase, include_numbers, include_symbols)
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub fn check_password_strength(password: String) -> Result<serde_json::Value, String> {
    let strength = check_strength(&password);
    serde_json::to_value(strength).map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn copy_to_clipboard(_text: String) -> Result<(), String> {
    // Implementation handled by frontend using tauri clipboard plugin
    Ok(())
}

#[tauri::command]
pub async fn run_security_check(state: State<'_, AppState>) -> Result<ApiResponse<serde_json::Value>, String> {
    let vault = state.vault.lock().map_err(|e| e.to_string())?;
    match vault.run_security_audit() {
        Ok(report) => Ok(ApiResponse { success: true, data: Some(report), error: None }),
        Err(e) => Ok(ApiResponse { success: false, data: None, error: Some(e.to_string()) }),
    }
}

#[tauri::command]
pub async fn export_vault(
    state: State<'_, AppState>,
    path: String,
    format: String,
) -> Result<ApiResponse<bool>, String> {
    let vault = state.vault.lock().map_err(|e| e.to_string())?;
    match vault.export_to_file(&path, &format) {
        Ok(_) => Ok(ApiResponse { success: true, data: Some(true), error: None }),
        Err(e) => Ok(ApiResponse { success: false, data: Some(false), error: Some(e.to_string()) }),
    }
}

#[tauri::command]
pub async fn import_vault(
    state: State<'_, AppState>,
    path: String,
    format: String,
) -> Result<ApiResponse<bool>, String> {
    let mut vault = state.vault.lock().map_err(|e| e.to_string())?;
    match vault.import_from_file(&path, &format) {
        Ok(_) => Ok(ApiResponse { success: true, data: Some(true), error: None }),
        Err(e) => Ok(ApiResponse { success: false, data: Some(false), error: Some(e.to_string()) }),
    }
}

#[tauri::command]
pub async fn change_master_password(
    state: State<'_, AppState>,
    old_password: String,
    new_password: String,
) -> Result<ApiResponse<bool>, String> {
    let mut vault = state.vault.lock().map_err(|e| e.to_string())?;
    match vault.change_master_password(&old_password, &new_password) {
        Ok(_) => Ok(ApiResponse { success: true, data: Some(true), error: None }),
        Err(e) => Ok(ApiResponse { success: false, data: Some(false), error: Some(e.to_string()) }),
    }
}

#[tauri::command]
pub async fn set_password_hint(
    state: State<'_, AppState>,
    hint: String,
) -> Result<ApiResponse<bool>, String> {
    let vault = state.vault.lock().map_err(|e| e.to_string())?;
    match vault.set_password_hint(&hint) {
        Ok(_) => Ok(ApiResponse { success: true, data: Some(true), error: None }),
        Err(e) => Ok(ApiResponse { success: false, data: Some(false), error: Some(e.to_string()) }),
    }
}

#[tauri::command]
pub async fn get_password_hint(
    state: State<'_, AppState>,
) -> Result<ApiResponse<Option<String>>, String> {
    let vault = state.vault.lock().map_err(|e| e.to_string())?;
    match vault.get_password_hint() {
        Ok(hint) => Ok(ApiResponse { success: true, data: Some(hint), error: None }),
        Err(e) => Ok(ApiResponse { success: false, data: None, error: Some(e.to_string()) }),
    }
}

// TOTP Commands

#[derive(Debug, Serialize, Deserialize)]
pub struct TotpResponse {
    pub code: String,
    pub remaining_seconds: u64,
}

#[tauri::command]
pub async fn generate_totp_code(secret: String) -> Result<ApiResponse<TotpResponse>, String> {
    match crate::totp::generate_totp(&secret) {
        Ok((code, remaining)) => Ok(ApiResponse {
            success: true,
            data: Some(TotpResponse {
                code,
                remaining_seconds: remaining,
            }),
            error: None,
        }),
        Err(e) => Ok(ApiResponse {
            success: false,
            data: None,
            error: Some(e.to_string()),
        }),
    }
}

#[tauri::command]
pub async fn validate_totp_secret(secret: String) -> Result<ApiResponse<bool>, String> {
    let is_valid = crate::totp::is_valid_totp_secret(&secret);
    Ok(ApiResponse {
        success: true,
        data: Some(is_valid),
        error: None,
    })
}

#[tauri::command]
pub async fn parse_totp_uri(uri: String) -> Result<ApiResponse<crate::totp::TotpConfig>, String> {
    match crate::totp::parse_totp_uri(&uri) {
        Ok(config) => Ok(ApiResponse {
            success: true,
            data: Some(config),
            error: None,
        }),
        Err(e) => Ok(ApiResponse {
            success: false,
            data: None,
            error: Some(e.to_string()),
        }),
    }
}

#[tauri::command]
pub async fn clear_clipboard() -> Result<ApiResponse<bool>, String> {
    // Use Tauri's clipboard manager to clear it
    // This is handled on the frontend via the clipboard manager plugin
    Ok(ApiResponse {
        success: true,
        data: Some(true),
        error: None,
    })
}

#[tauri::command]
pub async fn clear_all_data(
    state: State<'_, AppState>,
) -> Result<ApiResponse<bool>, String> {
    let mut vault = state.vault.lock().map_err(|e| e.to_string())?;
    match vault.clear_all_data() {
        Ok(_) => Ok(ApiResponse { success: true, data: Some(true), error: None }),
        Err(e) => Ok(ApiResponse { success: false, data: Some(false), error: Some(e.to_string()) }),
    }
}

#[tauri::command]
pub async fn restart_app(app: tauri::AppHandle) -> Result<(), String> {
    app.restart();
}
