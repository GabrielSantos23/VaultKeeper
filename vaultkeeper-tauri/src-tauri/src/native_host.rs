use std::fs;
use std::path::PathBuf;
use serde_json::json;

const HOST_NAME: &str = "com.vaultkeeper.host";
const HOST_DESCRIPTION: &str = "VaultKeeper Native Messaging Host";
const CHROME_EXTENSION_ID: &str = "bklgfpmbbpfboanbdjakcgmlldhmlkco";
const FIREFOX_EXTENSION_ID: &str = "vaultkeeper@example.com";

pub fn check_native_host_installation() {
    let result = install_all();
    if let Err(e) = result {
        println!("⚠️ Native host setup warning: {}", e);
    } else {
        println!("🔐 Native Host: Ready");
    }
}

fn install_all() -> Result<(), Box<dyn std::error::Error>> {
    let current_exe = std::env::current_exe()?;
    let exe_path = current_exe.to_string_lossy().to_string();

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
            // Firefox
            install_linux_mac(&home.join(".mozilla/native-messaging-hosts"), &exe_path, true)?;
            
            // Chrome
            install_linux_mac(&home.join(".config/google-chrome/NativeMessagingHosts"), &exe_path, false)?;
            
            // Chromium
            install_linux_mac(&home.join(".config/chromium/NativeMessagingHosts"), &exe_path, false)?;

            // Brave
            install_linux_mac(&home.join(".config/BraveSoftware/Brave-Browser/NativeMessagingHosts"), &exe_path, false)?;

            // Edge
            install_linux_mac(&home.join(".config/microsoft-edge/NativeMessagingHosts"), &exe_path, false)?;
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
