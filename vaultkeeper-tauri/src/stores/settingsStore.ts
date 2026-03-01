import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface SettingsState {
  // Auto-lock settings
  autoLockTimeout: number // in seconds, 0 means never
  setAutoLockTimeout: (seconds: number) => void
  
  // Notification settings
  securityAlerts: boolean
  setSecurityAlerts: (enabled: boolean) => void
  passwordExpiry: boolean
  setPasswordExpiry: (enabled: boolean) => void
  
  // Last activity timestamp (for auto-lock)
  lastActivity: number
  touch: () => void
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      // Default: 5 minutes (300 seconds)
      autoLockTimeout: 300,
      setAutoLockTimeout: (seconds) => set({ autoLockTimeout: seconds }),
      
      securityAlerts: true,
      setSecurityAlerts: (enabled) => set({ securityAlerts: enabled }),
      
      passwordExpiry: true,
      setPasswordExpiry: (enabled) => set({ passwordExpiry: enabled }),
      
      lastActivity: Date.now(),
      touch: () => set({ lastActivity: Date.now() }),
    }),
    {
      name: 'vaultkeeper-settings',
      partialize: (state) => ({
        autoLockTimeout: state.autoLockTimeout,
        securityAlerts: state.securityAlerts,
        passwordExpiry: state.passwordExpiry,
      }),
    }
  )
)
