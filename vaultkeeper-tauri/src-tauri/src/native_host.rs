use std::fs;
use std::path::PathBuf;
use serde_json::json;

use tauri::{AppHandle, Manager};

const HOST_NAME: &str = "com.vaultkeeper.host";
const HOST_DESCRIPTION: &str = "VaultKeeper Native Messaging Host";
const CHROME_EXTENSION_ID: &str = "bklgfpmbbpfboanbdjakcgmlldhmlkco";
const FIREFOX_EXTENSION_ID: &str = "vaultkeeper@example.com";

pub fn check_native_host_installation(app: &AppHandle) {
    let result = install_all(app);
    if let Err(e) = result {
        println!("⚠️ Native host setup warning: {}", e);
    } else {
        println!("🔐 Native Host: Ready");
    }
}

#[tauri::command]
pub fn reconnect_native_host(app: AppHandle) -> Result<String, String> {
    install_all(&app).map_err(|e| format!("Failed to reconnect: {}", e))?;
    Ok("Native host reconnected successfully to all browsers.".to_string())
}

#[tauri::command]
pub fn install_native_host_for_browser(app: AppHandle, browser: String) -> Result<String, String> {
    let exe_path = get_exe_path(&app).map_err(|e| format!("{}", e))?;
    let is_firefox = matches!(browser.as_str(), "firefox" | "zen" | "librewolf" | "waterfox");
    
    #[cfg(target_os = "windows")]
    {
        let manifest_dir = dirs::data_local_dir()
            .map(|mut p| { p.push("VaultKeeper"); p })
            .unwrap_or_else(|| PathBuf::from("C:\\ProgramData\\VaultKeeper"));
        if !manifest_dir.exists() {
            let _ = fs::create_dir_all(&manifest_dir);
        }
        
        let manifest_path = manifest_dir.join(format!("{}_{}.json", HOST_NAME, browser));
        create_manifest(&manifest_path, &exe_path, is_firefox)
            .map_err(|e| format!("Failed to create manifest: {}", e))?;
        
        let reg_key = match browser.as_str() {
            "firefox" | "zen" | "librewolf" | "waterfox" => "mozilla",
            "edge" => "microsoft\\edge",
            "brave" => "bravesoftware\\brave-browser",
            "opera" => "opera software\\opera stable",
            "vivaldi" => "vivaldi",
            _ => "google\\chrome",
        };
        register_windows(reg_key, &manifest_path)
            .map_err(|e| format!("Failed to register: {}", e))?;
    }
    
    #[cfg(target_os = "linux")]
    {
        if let Some(home) = dirs::home_dir() {
            let dir = match browser.as_str() {
                "firefox" => home.join(".mozilla/native-messaging-hosts"),
                "zen" => home.join(".zen/native-messaging-hosts"),
                "chrome" => home.join(".config/google-chrome/NativeMessagingHosts"),
                "chromium" => home.join(".config/chromium/NativeMessagingHosts"),
                "brave" => home.join(".config/BraveSoftware/Brave-Browser/NativeMessagingHosts"),
                "edge" => home.join(".config/microsoft-edge/NativeMessagingHosts"),
                "vivaldi" => home.join(".config/vivaldi/NativeMessagingHosts"),
                "opera" => home.join(".config/opera/NativeMessagingHosts"),
                _ => return Err(format!("Unknown browser: {}", browser)),
            };
            install_linux_mac(&dir, &exe_path, is_firefox)
                .map_err(|e| format!("Failed: {}", e))?;
        }
    }
    
    #[cfg(target_os = "macos")]
    {
        if let Some(home) = dirs::home_dir() {
            let dir = match browser.as_str() {
                "firefox" => home.join("Library/Application Support/Mozilla/NativeMessagingHosts"),
                "chrome" => home.join("Library/Application Support/Google/Chrome/NativeMessagingHosts"),
                "chromium" => home.join("Library/Application Support/Chromium/NativeMessagingHosts"),
                "brave" => home.join("Library/Application Support/BraveSoftware/Brave-Browser/NativeMessagingHosts"),
                "edge" => home.join("Library/Application Support/Microsoft Edge/NativeMessagingHosts"),
                _ => return Err(format!("Unknown browser: {}", browser)),
            };
            install_linux_mac(&dir, &exe_path, is_firefox)
                .map_err(|e| format!("Failed: {}", e))?;
        }
    }
    
    Ok(format!("Installed native host for {}", browser))
}

#[tauri::command]
pub fn install_native_host_custom_path(app: AppHandle, browser: String, path: String) -> Result<String, String> {
    let exe_path = get_exe_path(&app).map_err(|e| format!("{}", e))?;
    let is_firefox = matches!(browser.as_str(), "firefox" | "zen" | "librewolf" | "waterfox");
    let dir = PathBuf::from(&path);
    
    if !dir.exists() {
        let _ = fs::create_dir_all(&dir);
    }
    if !dir.exists() {
        return Err("Directory does not exist and could not be created.".to_string());
    }
    
    let manifest_path = dir.join(format!("{}.json", HOST_NAME));
    create_manifest(&manifest_path, &exe_path, is_firefox)
        .map_err(|e| format!("Failed to create manifest: {}", e))?;
    
    #[cfg(target_os = "windows")]
    {
        let reg_key = if is_firefox { "mozilla" } else { "google\\chrome" };
        register_windows(reg_key, &manifest_path)
            .map_err(|e| format!("Failed to register: {}", e))?;
    }
    
    Ok(format!("Installed native host at {}", path))
}

fn get_exe_path(app: &AppHandle) -> Result<String, Box<dyn std::error::Error>> {
    let resource_dir = app.path().resource_dir()?;
    
    #[cfg(target_os = "windows")]
    {
        let host_exe = resource_dir.join("bin").join("vk_host.exe");
        let mut exe_path = host_exe.to_string_lossy().to_string();
        if exe_path.starts_with("\\\\?\\") {
            exe_path = exe_path.replace("\\\\?\\", "");
        }
        Ok(exe_path)
    }
    
    #[cfg(not(target_os = "windows"))]
    {
        let host_exe_source = resource_dir.join("bin").join("vk_host");
        
        // On Linux (AppImage) and macOS, the resource dir is inside a temporary mount.
        // We copy vk_host to a stable, persistent location so the native messaging
        // manifest always points to a path that exists even when the app is closed.
        let persistent_dir = dirs::data_local_dir()
            .or_else(|| dirs::home_dir().map(|h| h.join(".local/share")))
            .map(|d| d.join("vaultkeeper").join("bin"))
            .ok_or("Could not determine persistent data directory")?;
        
        fs::create_dir_all(&persistent_dir)?;
        
        let persistent_exe = persistent_dir.join("vk_host");
        
        // Always copy/update the binary from the app bundle to the persistent location
        if host_exe_source.exists() {
            fs::copy(&host_exe_source, &persistent_exe)?;
            
            // Make executable on Unix
            #[cfg(unix)]
            {
                use std::os::unix::fs::PermissionsExt;
                let mut perms = fs::metadata(&persistent_exe)?.permissions();
                perms.set_mode(0o755);
                fs::set_permissions(&persistent_exe, perms)?;
            }
            
            println!("📦 vk_host copied to: {}", persistent_exe.display());
        } else if !persistent_exe.exists() {
            return Err(format!(
                "vk_host not found at source ({}) or persistent location ({})",
                host_exe_source.display(),
                persistent_exe.display()
            ).into());
        }
        
        Ok(persistent_exe.to_string_lossy().to_string())
    }
}

fn install_all(app: &AppHandle) -> Result<(), Box<dyn std::error::Error>> {
    let exe_path = get_exe_path(app)?;

    #[cfg(target_os = "windows")]
    {
        let manifest_dir = dirs::data_local_dir()
            .map(|mut p| {
                p.push("VaultKeeper");
                p
            })
            .unwrap_or_else(|| PathBuf::from("C:\\ProgramData\\VaultKeeper"));

        if !manifest_dir.exists() {
            fs::create_dir_all(&manifest_dir)?;
        }

        let firefox_manifest = manifest_dir.join(format!("{}_firefox.json", HOST_NAME));
        let chrome_manifest = manifest_dir.join(format!("{}_chrome.json", HOST_NAME));

        create_manifest(&firefox_manifest, &exe_path, true)?;
        create_manifest(&chrome_manifest, &exe_path, false)?;

        register_windows("mozilla", &firefox_manifest)?;
        register_windows("google\\chrome", &chrome_manifest)?;
        register_windows("microsoft\\edge", &chrome_manifest)?;
        register_windows("bravesoftware\\brave-browser", &chrome_manifest)?;
    }

    #[cfg(target_os = "linux")]
    {
        if let Some(home) = dirs::home_dir() {
            // Firefox (standard, Snap, Flatpak)
            install_linux_mac(&home.join(".mozilla/native-messaging-hosts"), &exe_path, true)?;
            install_linux_mac(&home.join("snap/firefox/common/.mozilla/native-messaging-hosts"), &exe_path, true)?;
            install_linux_mac(&home.join(".var/app/org.mozilla.firefox/.mozilla/native-messaging-hosts"), &exe_path, true)?;
            
            // Zen Browser
            install_linux_mac(&home.join(".zen/native-messaging-hosts"), &exe_path, true)?;
            
            // Chrome
            install_linux_mac(&home.join(".config/google-chrome/NativeMessagingHosts"), &exe_path, false)?;
            
            // Chromium (standard, Snap, Flatpak)
            install_linux_mac(&home.join(".config/chromium/NativeMessagingHosts"), &exe_path, false)?;
            install_linux_mac(&home.join("snap/chromium/common/.chromium/NativeMessagingHosts"), &exe_path, false)?;

            // Brave
            install_linux_mac(&home.join(".config/BraveSoftware/Brave-Browser/NativeMessagingHosts"), &exe_path, false)?;

            // Edge
            install_linux_mac(&home.join(".config/microsoft-edge/NativeMessagingHosts"), &exe_path, false)?;
            
            // Vivaldi
            install_linux_mac(&home.join(".config/vivaldi/NativeMessagingHosts"), &exe_path, false)?;
            
            // Opera
            install_linux_mac(&home.join(".config/opera/NativeMessagingHosts"), &exe_path, false)?;
        }
    }

    #[cfg(target_os = "macos")]
    {
        if let Some(home) = dirs::home_dir() {
            install_linux_mac(&home.join("Library/Application Support/Mozilla/NativeMessagingHosts"), &exe_path, true)?;
            install_linux_mac(&home.join("Library/Application Support/Google/Chrome/NativeMessagingHosts"), &exe_path, false)?;
            install_linux_mac(&home.join("Library/Application Support/Chromium/NativeMessagingHosts"), &exe_path, false)?;
            install_linux_mac(&home.join("Library/Application Support/BraveSoftware/Brave-Browser/NativeMessagingHosts"), &exe_path, false)?;
            install_linux_mac(&home.join("Library/Application Support/Microsoft Edge/NativeMessagingHosts"), &exe_path, false)?;
        }
    }

    Ok(())
}

fn create_manifest(path: &PathBuf, exe_path: &str, is_firefox: bool) -> Result<(), Box<dyn std::error::Error>> {
    let mut manifest = json!({
        "name": HOST_NAME,
        "description": HOST_DESCRIPTION,
        "path": exe_path,
        "type": "stdio"
    });

    if is_firefox {
        manifest.as_object_mut().unwrap().insert(
            "allowed_extensions".to_string(), 
            json!([FIREFOX_EXTENSION_ID])
        );
    } else {
        manifest.as_object_mut().unwrap().insert(
            "allowed_origins".to_string(), 
            json!([format!("chrome-extension://{}/", CHROME_EXTENSION_ID)])
        );
    }

    let json_str = serde_json::to_string_pretty(&manifest)?;
    fs::write(path, json_str)?;
    
    Ok(())
}

#[cfg(not(target_os = "windows"))]
fn install_linux_mac(dir: &PathBuf, exe_path: &str, is_firefox: bool) -> Result<(), Box<dyn std::error::Error>> {
    if !dir.exists() {
        let _ = fs::create_dir_all(dir);
    }
    
    if dir.exists() {
        let manifest_path = dir.join(format!("{}.json", HOST_NAME));
        create_manifest(&manifest_path, exe_path, is_firefox)?;
    }
    Ok(())
}

#[cfg(target_os = "windows")]
fn register_windows(browser_key: &str, manifest_path: &PathBuf) -> Result<(), Box<dyn std::error::Error>> {
    use winreg::enums::*;
    use winreg::RegKey;

    let hkcu = RegKey::predef(HKEY_CURRENT_USER);
    let path = format!("Software\\{}\\NativeMessagingHosts\\{}", browser_key, HOST_NAME);
    
    // Attempt creates key or opens existing
    let (key, _) = hkcu.create_subkey(&path)?;
    key.set_value("", &manifest_path.to_string_lossy().to_string())?;

    Ok(())
}
