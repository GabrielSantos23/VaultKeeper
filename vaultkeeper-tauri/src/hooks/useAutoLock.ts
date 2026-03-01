import { useEffect, useRef } from 'react'
import { useSettingsStore } from '../stores/settingsStore'
import { useAuthStore } from '../stores/authStore'

const CHECK_INTERVAL = 5000 // Check every 5 seconds

export function useAutoLock() {
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    // Start the timer immediately
    intervalRef.current = setInterval(() => {
      const auth = useAuthStore.getState()
      const settings = useSettingsStore.getState()

      // Only proceed if authenticated and timeout is enabled
      if (!auth.isAuthenticated) return
      if (settings.autoLockTimeout === 0) return

      const elapsed = (Date.now() - settings.lastActivity) / 1000

      if (elapsed > settings.autoLockTimeout) {
        auth.logout()
      }
    }, CHECK_INTERVAL)

    // Initial touch when setting up
    const initialAuth = useAuthStore.getState()
    if (initialAuth.isAuthenticated) {
      useSettingsStore.getState().touch()
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [])

  // Activity tracking - always track, but only touch when authenticated
  useEffect(() => {
    const events = ['mousedown', 'keydown', 'touchstart', 'scroll', 'click', 'mousemove']
    let throttle: ReturnType<typeof setTimeout> | null = null

    const onActivity = () => {
      const auth = useAuthStore.getState()
      if (!auth.isAuthenticated) return
      if (throttle) return

      throttle = setTimeout(() => {
        useSettingsStore.getState().touch()
        throttle = null
      }, 500)
    }

    events.forEach(e => window.addEventListener(e, onActivity, { passive: true }))

    return () => {
      events.forEach(e => window.removeEventListener(e, onActivity))
      if (throttle) clearTimeout(throttle)
    }
  }, [])
}
