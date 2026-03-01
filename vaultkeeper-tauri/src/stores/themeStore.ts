import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type Theme = 'light' | 'dark' | 'system'

interface ThemeState {
  theme: Theme
  resolvedTheme: 'light' | 'dark'
  setTheme: (theme: Theme) => void
  initTheme: () => void
}

const getSystemTheme = (): 'light' | 'dark' => {
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark'
  }
  return 'light'
}

const applyTheme = (theme: 'light' | 'dark') => {
  const root = window.document.documentElement
  if (theme === 'dark') {
    root.classList.add('dark')
  } else {
    root.classList.remove('dark')
  }
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      theme: 'system',
      resolvedTheme: 'light',
      
      setTheme: (theme: Theme) => {
        const resolved = theme === 'system' ? getSystemTheme() : theme
        applyTheme(resolved)
        set({ theme, resolvedTheme: resolved })
      },
      
      initTheme: () => {
        const { theme } = get()
        const resolved = theme === 'system' ? getSystemTheme() : theme
        applyTheme(resolved)
        set({ resolvedTheme: resolved })
        
        // Listen for system theme changes
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
        mediaQuery.addEventListener('change', (e) => {
          if (get().theme === 'system') {
            const newTheme = e.matches ? 'dark' : 'light'
            applyTheme(newTheme)
            set({ resolvedTheme: newTheme })
          }
        })
      },
    }),
    {
      name: 'vaultkeeper-theme',
    }
  )
)
