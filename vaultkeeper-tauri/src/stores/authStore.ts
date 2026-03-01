import { create } from 'zustand'
import { invoke } from '@tauri-apps/api/core'
import { useSettingsStore } from './settingsStore'

interface AuthState {
  isAuthenticated: boolean
  isFirstRun: boolean
  isLoading: boolean
  error: string | null
  checkFirstRun: () => Promise<void>
  login: (password: string) => Promise<void>
  createVault: (password: string, confirmPassword: string) => Promise<void>
  logout: () => void
  clearError: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: false,
  isFirstRun: false,
  isLoading: false,
  error: null,

  checkFirstRun: async () => {
    try {
      const response = await invoke<{
        success: boolean
        data?: boolean
        error?: string
      }>('check_first_run')

      if (response.success) {
        set({ isFirstRun: response.data ?? true })
      }
    } catch (error) {
      console.error('Failed to check first run:', error)
      set({ isFirstRun: true })
    }
  },

  login: async (password: string) => {
    set({ isLoading: true, error: null })
    try {
      const response = await invoke<{
        success: boolean
        data?: boolean
        error?: string
      }>('unlock_vault', { password })

      if (response.success && response.data) {
        set({ isAuthenticated: true, isLoading: false })
        // Reset activity timer on successful login
        useSettingsStore.getState().touch()
      } else {
        set({
          isAuthenticated: false,
          isLoading: false,
          error: response.error || 'Invalid master password',
        })
      }
    } catch (error) {
      set({
        isAuthenticated: false,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Authentication failed',
      })
    }
  },

  createVault: async (password: string, confirmPassword: string) => {
    set({ isLoading: true, error: null })

    if (password !== confirmPassword) {
      set({ isLoading: false, error: "Passwords don't match" })
      return
    }

    if (password.length < 8) {
      set({ isLoading: false, error: 'Password must be at least 8 characters' })
      return
    }

    try {
      const response = await invoke<{
        success: boolean
        data?: boolean
        error?: string
      }>('create_vault', { password })

      if (response.success && response.data) {
        set({ isAuthenticated: true, isFirstRun: false, isLoading: false })
        // Reset activity timer on successful vault creation
        useSettingsStore.getState().touch()
      } else {
        set({
          isAuthenticated: false,
          isLoading: false,
          error: response.error || 'Failed to create vault',
        })
      }
    } catch (error) {
      set({
        isAuthenticated: false,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to create vault',
      })
    }
  },

  logout: () => {
    invoke('lock_vault')
    set({ isAuthenticated: false, error: null })
  },

  clearError: () => set({ error: null }),
}))
