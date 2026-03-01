import React, { useEffect } from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './styles/globals.css'
import { useThemeStore } from './stores/themeStore'

function Root() {
  const initTheme = useThemeStore((state) => state.initTheme)
  
  useEffect(() => {
    initTheme()
  }, [initTheme])
  
  return <App />
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>,
)
