import { useEffect } from "react";
import { useAuthStore } from "./stores/authStore";
import { useAutoLock } from "./hooks/useAutoLock";
import { LoginView } from "./views/LoginView";
import { VaultView } from "./views/VaultView";
import { UpdateToast, useAutoUpdater } from "./components/dialogs";

function App() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const { showUpdate, setShowUpdate } = useAutoUpdater();

  useAutoLock();

  useEffect(() => {
    const disableContextMenu = (e: MouseEvent) => e.preventDefault();

    document.addEventListener("contextmenu", disableContextMenu);

    return () => {
      document.removeEventListener("contextmenu", disableContextMenu);
    };
  }, []);

  return (
    <div className="w-screen h-screen bg-background overflow-hidden">
      {!isAuthenticated ? <LoginView /> : <VaultView />}
      <UpdateToast open={showUpdate} onOpenChange={setShowUpdate} />
    </div>
  );
}

export default App;
