// Prevents additional console window on Windows in release mode
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::Manager;
use vaultkeeper_lib::commands;
use vaultkeeper_lib::AppState;

mod native_host;

fn load_icon() -> Option<tauri::image::Image<'static>> {
    let icon_bytes = include_bytes!("../icons/icon.png");
    let img = image::load_from_memory(icon_bytes).ok()?;
    let rgba = img.to_rgba8();
    let (width, height) = rgba.dimensions();
    Some(tauri::image::Image::new_owned(
        rgba.into_raw(),
        width,
        height,
    ))
}

fn main() {
    #[cfg(target_os = "linux")]
    {
        std::env::set_var("WEBKIT_DISABLE_COMPOSITING_MODE", "1");
        std::env::set_var("WEBKIT_DISABLE_DMABUF_RENDERER", "1");
    }

    let state = AppState::new().expect("Failed to initialize app state");

    tauri::Builder::default()
        .manage(state)
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_http::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_os::init())
        .plugin(tauri_plugin_process::init())
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_clipboard_manager::init())
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .setup(|app| {
            // Set window icon
            let window = app.get_webview_window("main").unwrap();
            if let Some(icon) = load_icon() {
                let _ = window.set_icon(icon);
            }

            native_host::check_native_host_installation(app.handle());

            #[cfg(debug_assertions)]
            {
                window.open_devtools();
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::check_first_run,
            commands::authenticate,
            commands::create_vault,
            commands::unlock_vault,
            commands::lock_vault,
            commands::get_credentials,
            commands::add_credential,
            commands::update_credential,
            commands::delete_credential,
            commands::get_folders,
            commands::create_folder,
            commands::update_folder,
            commands::delete_folder,
            commands::get_secure_notes,
            commands::add_secure_note,
            commands::update_secure_note,
            commands::delete_secure_note,
            commands::get_credit_cards,
            commands::add_credit_card,
            commands::update_credit_card,
            commands::delete_credit_card,
            commands::generate_password,
            commands::check_password_strength,
            commands::copy_to_clipboard,
            commands::run_security_check,
            commands::export_vault,
            commands::import_vault,
            commands::change_master_password,
            commands::set_password_hint,
            commands::get_password_hint,
            commands::clear_clipboard,
            commands::clear_all_data,
            commands::restart_app,
            commands::generate_totp_code,
            commands::validate_totp_secret,
            commands::parse_totp_uri,
            native_host::reconnect_native_host,
            native_host::install_native_host_for_browser,
            native_host::install_native_host_custom_path,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
