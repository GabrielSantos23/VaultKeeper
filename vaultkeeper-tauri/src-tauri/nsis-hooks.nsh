; NSIS Hooks for VaultKeeper Tauri Installer
; Handles uninstalling the old Python-based VaultKeeper (Inno Setup)

; Define translations for the uninstallation prompt
LangString UNINSTALL_OLD_PROMPT ${LANG_ENGLISH} "An older version of VaultKeeper (Python) was detected. It MUST be uninstalled to avoid conflicts. Uninstall it now?"
LangString UNINSTALL_OLD_PROMPT ${LANG_PORTUGUESEBR} "Uma versão antiga do VaultKeeper (Python) foi detectada. Ela DEVE ser desinstalada para evitar conflitos. Desinstalar agora?"

!macro NSIS_HOOK_PREINSTALL
  ; Kill processes first to avoid file locks
  ExecWait 'taskkill /F /IM VaultKeeper.exe /T'
  ExecWait 'taskkill /F /IM vk_host.exe /T'
  Sleep 1000

  ; Check if old Python-based VaultKeeper (Inno Setup) is installed
  ; AppId: {D4183421-E236-4107-B603-99933096277B}
  ; Inno Setup on 64-bit Windows writes to WOW6432Node, so we need to check both views
  
  StrCpy $0 "" ; Clear $0

  ; --- Check 64-bit registry view first ---
  SetRegView 64
  ReadRegStr $0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\{D4183421-E236-4107-B603-99933096277B}_is1" "UninstallString"
  ${If} $0 == ""
    ReadRegStr $0 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\{D4183421-E236-4107-B603-99933096277B}_is1" "UninstallString"
  ${EndIf}
  ${If} $0 == ""
    ReadRegStr $0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\VaultKeeper_is1" "UninstallString"
  ${EndIf}
  ${If} $0 == ""
    ReadRegStr $0 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\VaultKeeper_is1" "UninstallString"
  ${EndIf}

  ; --- Check 32-bit registry view (WOW6432Node) ---
  ${If} $0 == ""
    SetRegView 32
    ReadRegStr $0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\{D4183421-E236-4107-B603-99933096277B}_is1" "UninstallString"
  ${EndIf}
  ${If} $0 == ""
    ReadRegStr $0 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\{D4183421-E236-4107-B603-99933096277B}_is1" "UninstallString"
  ${EndIf}
  ${If} $0 == ""
    ReadRegStr $0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\VaultKeeper_is1" "UninstallString"
  ${EndIf}
  ${If} $0 == ""
    ReadRegStr $0 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\VaultKeeper_is1" "UninstallString"
  ${EndIf}

  ; Restore default registry view
  SetRegView 64

  ; --- Also check for unins000.exe directly in common install paths ---
  ${If} $0 == ""
    IfFileExists "$PROGRAMFILES32\VaultKeeper\unins000.exe" 0 +2
      StrCpy $0 '"$PROGRAMFILES32\VaultKeeper\unins000.exe"'
  ${EndIf}
  ${If} $0 == ""
    IfFileExists "$PROGRAMFILES64\VaultKeeper\unins000.exe" 0 +2
      StrCpy $0 '"$PROGRAMFILES64\VaultKeeper\unins000.exe"'
  ${EndIf}

  ${If} $0 != ""
    ; Prompt user to uninstall
    MessageBox MB_YESNO|MB_ICONEXCLAMATION "$(UNINSTALL_OLD_PROMPT)" IDYES uninstall_old IDNO skip_uninstall
    
    uninstall_old:
      ; Run the Inno Setup uninstaller silently
      ExecWait '$0 /SILENT /NORESTART'
      Sleep 2000
      
      ; Clean leftover folder
      IfFileExists "$PROGRAMFILES32\VaultKeeper\*.*" 0 +2
        RMDir /r "$PROGRAMFILES32\VaultKeeper"
      IfFileExists "$PROGRAMFILES64\VaultKeeper\*.*" 0 +2
        RMDir /r "$PROGRAMFILES64\VaultKeeper"
      
      Goto done_uninstall
    
    skip_uninstall:
    
    done_uninstall:
  ${EndIf}
!macroend

!macro NSIS_HOOK_POSTINSTALL
  ; Post-install logic if needed
!macroend
