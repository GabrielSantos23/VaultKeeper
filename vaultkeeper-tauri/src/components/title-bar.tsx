import { getCurrentWindow } from "@tauri-apps/api/window";
import {
  Moon02Icon,
  Sun03Icon,
  Search01Icon,
} from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";
import { useState } from "react";

interface TitleBarProps {
  activeView:
    | "vault"
    | "notes"
    | "cards"
    | "generator"
    | "security"
    | "settings";
  onThemeToggle?: () => void;
  isDark?: boolean;
}

const VIEW_LABELS: Record<TitleBarProps["activeView"], string> = {
  vault: "Vault",
  notes: "Secure Notes",
  cards: "Credit Cards",
  generator: "Password Generator",
  security: "Security Audit",
  settings: "Settings",
};

export function TitleBar({}: TitleBarProps) {
  const [searchValue, setSearchValue] = useState("");
  const [searchFocused, setSearchFocused] = useState(false);

  const appWindow = getCurrentWindow();

  const minimize = () => appWindow.minimize();
  const maximize = () => appWindow.toggleMaximize();
  const close = () => appWindow.close();

  return (
    <header
      data-tauri-drag-region
      className="h-11 flex items-center justify-between shrink-0 select-none z-20 relative"
      style={{
        backgroundColor: "var(--sidebar)",
        borderBottom: "1px solid var(--border)",
      }}
    >
      <div
        data-tauri-drag-region
        className="flex items-center  gap-2 px-4 w-64 shrink-0"
      >
        <div
          className="w-5 h-5 rounded-md overflow-hidden shrink-0"
          style={{ backgroundColor: "var(--primary)" }}
        >
          <img src="/logo.png" alt="" className="w-full h-full object-cover" />
        </div>
        <span
          className="text-sm font-semibold tracking-tight"
          style={{ color: "var(--foreground)" }}
        >
          VaultKeeper
        </span>
      </div>

      <div className="flex items-center h-full">
        <div
          className="w-px h-5 mx-1"
          style={{ backgroundColor: "var(--border)" }}
        />

        <button
          title="Minimize"
          onClick={minimize}
          className="w-11 h-full flex items-center justify-center transition-colors"
          style={{ color: "var(--muted-foreground)" }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = "var(--muted)";
            e.currentTarget.style.color = "var(--foreground)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = "transparent";
            e.currentTarget.style.color = "var(--muted-foreground)";
          }}
        >
          <svg width="11" height="2" viewBox="0 0 11 2" fill="none">
            <rect width="11" height="2" rx="1" fill="currentColor" />
          </svg>
        </button>

        <button
          title="Maximize"
          onClick={maximize}
          className="w-11 h-full flex items-center justify-center transition-colors"
          style={{ color: "var(--muted-foreground)" }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = "var(--muted)";
            e.currentTarget.style.color = "var(--foreground)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = "transparent";
            e.currentTarget.style.color = "var(--muted-foreground)";
          }}
        >
          <svg width="11" height="11" viewBox="0 0 11 11" fill="none">
            <rect
              x="0.5"
              y="0.5"
              width="10"
              height="10"
              rx="1.5"
              stroke="currentColor"
              strokeWidth="1.5"
            />
          </svg>
        </button>

        <button
          title="Close"
          onClick={close}
          className="w-11 h-full flex items-center justify-center transition-colors group"
          style={{ color: "var(--muted-foreground)" }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = "var(--destructive)";
            e.currentTarget.style.color = "var(--destructive-foreground)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = "transparent";
            e.currentTarget.style.color = "var(--muted-foreground)";
          }}
        >
          <svg width="11" height="11" viewBox="0 0 11 11" fill="none">
            <path
              d="M1 1L10 10M10 1L1 10"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          </svg>
        </button>
      </div>
    </header>
  );
}
