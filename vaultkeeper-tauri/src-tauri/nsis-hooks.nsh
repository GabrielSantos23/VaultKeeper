; NSIS Hooks for VaultKeeper Tauri Installer
; Handles uninstalling the old Python-based VaultKeeper (Inno Setup)

; Define translations for the uninstallation prompt
LangString UNINSTALL_OLD_PROMPT ${LANG_ENGLISH} "An older version of VaultKeeper (Python) was detected. It MUST be uninstalled to avoid conflicts. Uninstall it now?"
LangString UNINSTALL_OLD_PROMPT ${LANG_PORTUGUESEBR} "Uma versão antiga do VaultKeeper (Python) foi detectada. Ela DEVE ser desinstalada para evitar conflitos. Desinstalar agora?"

!macro NSIS_HOOK_PREINSTALL
  ; Check if old Python-based VaultKeeper (Inno Setup) is installed
  ; AppId: {D4183421-E236-4107-B603-99933096277B}
  
  StrCpy $0 "" ; Clear $0
  
  ; 1. Check by AppId (Standard way for Inno Setup)
  ReadRegStr $0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\{D4183421-E236-4107-B603-99933096277B}_is1" "UninstallString"
  ${If} $0 == ""
    ReadRegStr $0 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\{D4183421-E236-4107-B603-99933096277B}_is1" "UninstallString"
  ${EndIf}
  
  ; 2. Check by Name if AppId search failed
  ${If} $0 == ""
    ReadRegStr $0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\VaultKeeper_is1" "UninstallString"
  ${EndIf}
  ${If} $0 == ""
    ReadRegStr $0 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\VaultKeeper_is1" "UninstallString"
  ${EndIf}
  
  ${If} $0 != ""
    ; Prompt user to uninstall
    MessageBox MB_YESNO|MB_ICONEXCLAMATION "$(UNINSTALL_OLD_PROMPT)" IDYES uninstall_old IDNO skip_uninstall
    
    uninstall_old:
      ; Run the Inno Setup uninstaller silently
      ; $0 contains the uninstall sequence, sometimes it has quotes or extra params
      ExecWait '$0 /SILENT /NORESTART'
      
      ; Optional: Clean leftover folder
      ReadRegStr $2 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\{D4183421-E236-4107-B603-99933096277B}_is1" "InstallLocation"
      ${If} $2 == ""
        ReadRegStr $2 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\{D4183421-E236-4107-B603-99933096277B}_is1" "InstallLocation"
      ${EndIf}
      ${If} $2 != ""
        RMDir /r "$2"
      ${EndIf}
      
      Sleep 1000
      Goto done_uninstall
    
    skip_uninstall:
      ; If user says no, we continue (Tauri version will install in its own folder)
    
    done_uninstall:
  ${EndIf}
  
  ; Ensure no Python/VaultKeeper processes are locking files
  ExecWait 'taskkill /F /IM VaultKeeper.exe /T'
  ExecWait 'taskkill /F /IM vk_host.exe /T'
  Sleep 1000
!macroend

!macro NSIS_HOOK_POSTINSTALL
  ; Post-install logic if needed
!macroend
