import { useAuthStore } from './stores/authStore'
import { useAutoLock } from './hooks/useAutoLock'
import { LoginView } from './views/LoginView'
import { VaultView } from './views/VaultView'

function App() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  
  // Initialize auto-lock functionality
  useAutoLock()

  return (
    <div className="w-screen h-screen bg-background overflow-hidden">
      {!isAuthenticated ? <LoginView /> : <VaultView />}
    </div>
  )
}

export default App
