import { useEffect, useState } from "react";
import { Sidebar } from "../components/Sidebar";
import { ItemList } from "../components/ItemList";
import { DetailPanel } from "../components/DetailPanel";
import { GeneratorView } from "../components/GeneratorView";
import { SecurityDashboard } from "../components/SecurityDashboard";
import { SettingsPanel } from "../components/SettingsPanel";
import { SecureNotesPage } from "./SecureNotesPage";
import { CreditCardsPage } from "./CreditCardsPage";
import { useVaultStore } from "../stores/vaultStore";
import { useSidebar, SidebarProvider } from "../components/ui/sidebar";
import { TooltipProvider } from "@/components/ui/tooltip";
import { TitleBar } from "@/components/title-bar";
import { useThemeStore } from "@/stores/themeStore";

export function VaultView() {
  const { theme, setTheme } = useThemeStore();
  const isDark = theme === "dark";
  const toggleTheme = () => setTheme(isDark ? "light" : "dark");

  const [activeView, setActiveView] = useState<
    "vault" | "notes" | "cards" | "generator" | "security" | "settings"
  >("vault");
  const loadVaultData = useVaultStore((state) => state.loadVaultData);

  useEffect(() => {
    loadVaultData();
  }, [loadVaultData]);

  return (
    <div className="w-full h-full flex flex-col bg-background">
      <TitleBar
        activeView={activeView}
        isDark={isDark}
        onThemeToggle={toggleTheme}
      />
      <div className="flex-1 flex overflow-hidden">
        <SidebarProvider>
          <Sidebar activeView={activeView} onViewChange={setActiveView} />
          <TooltipProvider>
            <div className="flex-1 flex overflow-hidden">
              {activeView === "vault" && (
                <>
                  <ItemList />
                  <DetailPanel />
                </>
              )}
              {activeView === "notes" && <SecureNotesPage />}
              {activeView === "cards" && <CreditCardsPage />}
              {activeView === "generator" && <GeneratorView />}
              {activeView === "security" && <SecurityDashboard />}
              {activeView === "settings" && <SettingsPanel />}
            </div>
          </TooltipProvider>
        </SidebarProvider>
      </div>
    </div>
  );
}
