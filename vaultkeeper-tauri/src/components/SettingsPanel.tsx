import { useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import {
  Settings02Icon,
  Database02Icon,
  Notification02Icon,
  PaintBoardIcon,
  Key01Icon,
  DownloadCircle01Icon,
  UploadCircle01Icon,
  Delete02Icon,
  LockPasswordIcon,
  Moon02Icon,
  Sun03Icon,
  Globe02Icon,
  Clock01Icon,
  ShieldUserIcon,
  CheckmarkCircle01Icon,
  Alert02Icon,
  Settings05Icon,
  ArrowDown01Icon,
} from "@hugeicons/core-free-icons";
import { HugeiconsIcon, IconSvgElement } from "@hugeicons/react";
import { Switch } from "@/components/ui/switch";
import { useThemeStore } from "../stores/themeStore";
import { useSettingsStore } from "../stores/settingsStore";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  ChangeMasterPasswordDialog,
  PasswordHintDialog,
  ExportVaultDialog,
  ImportVaultDialog,
  ClearClipboardDialog,
  DeleteAllDataDialog,
  UpdateToast,
} from "./dialogs";

type Tab = "general" | "security" | "data";

const TABS: { id: Tab; label: string; icon: IconSvgElement }[] = [
  { id: "general", label: "General", icon: Settings02Icon },
  { id: "security", label: "Security", icon: CheckmarkCircle01Icon },
  { id: "data", label: "Data Management", icon: Database02Icon },
];

// Auto-lock options (value in seconds)
const AUTO_LOCK_OPTIONS = [
  { label: "1 minute", value: 60 },
  { label: "5 minutes", value: 300 },
  { label: "15 minutes", value: 900 },
  { label: "30 minutes", value: 1800 },
  { label: "1 hour", value: 3600 },
  { label: "Never", value: 0 },
] as const;

function SectionHeader({
  icon,
  label,
  color = "var(--primary)",
}: {
  icon: IconSvgElement;
  label: string;
  color?: string;
}) {
  return (
    <div className="flex items-center gap-2 px-4 py-3 border-b border-border bg-background">
      <HugeiconsIcon
        icon={icon}
        size={14}
        style={{ color }}
        className="shrink-0"
      />
      <span
        className="text-xs font-semibold uppercase tracking-wider"
        style={{ color: "var(--muted-foreground)" }}
      >
        {label}
      </span>
    </div>
  );
}

function SettingRow({
  label,
  description,
  children,
  danger = false,
  last = false,
}: {
  label: string;
  description?: string;
  children?: React.ReactNode;
  danger?: boolean;
  last?: boolean;
}) {
  return (
    <div
      className={`flex items-center justify-between gap-6 px-4 py-3.5 ${!last ? "border-b border-border" : ""}`}
    >
      <div className="min-w-0">
        <p
          className={`text-sm font-medium ${danger ? "text-destructive" : "text-foreground"}`}
        >
          {label}
        </p>
        {description && (
          <p className="text-xs text-muted-foreground mt-0.5">{description}</p>
        )}
      </div>
      {children && <div className="shrink-0">{children}</div>}
    </div>
  );
}

function ActionButton({
  label,
  onClick,
  danger = false,
  icon,
  disabled = false,
}: {
  label: string;
  onClick?: () => void;
  danger?: boolean;
  icon?: IconSvgElement;
  disabled?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      style={
        danger
          ? {
              backgroundColor:
                "color-mix(in oklch, var(--destructive) 10%, transparent)",
              color: "var(--destructive)",
              border:
                "1px solid color-mix(in oklch, var(--destructive) 25%, transparent)",
            }
          : {
              backgroundColor: "var(--accent)",
              color: "var(--foreground)",
              border: "1px solid var(--border)",
            }
      }
      onMouseEnter={(e) => {
        if (danger)
          e.currentTarget.style.backgroundColor =
            "color-mix(in oklch, var(--destructive) 18%, transparent)";
        else e.currentTarget.style.backgroundColor = "var(--muted)";
      }}
      onMouseLeave={(e) => {
        if (danger)
          e.currentTarget.style.backgroundColor =
            "color-mix(in oklch, var(--destructive) 10%, transparent)";
        else e.currentTarget.style.backgroundColor = "var(--accent)";
      }}
    >
      {icon && <HugeiconsIcon icon={icon} size={13} />}
      {label}
    </button>
  );
}

const BROWSER_OPTIONS = [
  { id: "firefox", label: "Firefox" },
  { id: "chrome", label: "Chrome" },
  { id: "chromium", label: "Chromium" },
  { id: "brave", label: "Brave" },
  { id: "edge", label: "Edge" },
  { id: "vivaldi", label: "Vivaldi" },
  { id: "opera", label: "Opera" },
  { id: "zen", label: "Zen" },
] as const;

function GeneralSettings() {
  const { theme, setTheme } = useThemeStore();
  const { autoLockTimeout, setAutoLockTimeout } = useSettingsStore();

  const [reconnecting, setReconnecting] = useState(false);
  const [reconnectStatus, setReconnectStatus] = useState<
    "idle" | "success" | "error"
  >("idle");
  const [reconnectMessage, setReconnectMessage] = useState("");

  const handleReconnect = async () => {
    setReconnecting(true);
    setReconnectStatus("idle");
    try {
      const msg = await invoke<string>("reconnect_native_host");
      setReconnectStatus("success");
      setReconnectMessage(msg);
    } catch (err: any) {
      setReconnectStatus("error");
      setReconnectMessage(String(err));
    } finally {
      setReconnecting(false);
      setTimeout(() => setReconnectStatus("idle"), 5000);
    }
  };

  const [installingBrowser, setInstallingBrowser] = useState(false);
  const [browserInstallStatus, setBrowserInstallStatus] = useState<
    "idle" | "success" | "error"
  >("idle");
  const [browserInstallMsg, setBrowserInstallMsg] = useState("");

  const handleInstallBrowser = async (browserId: string) => {
    setInstallingBrowser(true);
    setBrowserInstallStatus("idle");
    try {
      await invoke<string>("install_native_host_for_browser", {
        browser: browserId,
      });
      setBrowserInstallStatus("success");
      setBrowserInstallMsg(`Installed for ${browserId}`);
    } catch (err: any) {
      setBrowserInstallStatus("error");
      setBrowserInstallMsg(String(err));
    } finally {
      setInstallingBrowser(false);
      setTimeout(() => setBrowserInstallStatus("idle"), 5000);
    }
  };

  const [customBrowserType, setCustomBrowserType] = useState("chrome");
  const [customPath, setCustomPath] = useState("");
  const [installingCustom, setInstallingCustom] = useState(false);

  const handleInstallCustom = async () => {
    if (!customPath.trim()) return;
    setInstallingCustom(true);
    try {
      await invoke<string>("install_native_host_custom_path", {
        browser: customBrowserType,
        path: customPath.trim(),
      });
      setBrowserInstallStatus("success");
      setBrowserInstallMsg("Installed at custom path");
      setCustomPath("");
    } catch (err: any) {
      setBrowserInstallStatus("error");
      setBrowserInstallMsg(String(err));
    } finally {
      setInstallingCustom(false);
      setTimeout(() => setBrowserInstallStatus("idle"), 5000);
    }
  };

  const themeOptions = [
    { id: "dark", label: "Dark", icon: Moon02Icon },
    { id: "light", label: "Light", icon: Sun03Icon },
    { id: "system", label: "System", icon: Settings05Icon },
  ] as const;

  // Find the current auto-lock label
  const currentAutoLockLabel =
    AUTO_LOCK_OPTIONS.find((opt) => opt.value === autoLockTimeout)?.label ||
    "5 minutes";

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-border overflow-hidden">
        <SectionHeader icon={PaintBoardIcon} label="Appearance" />
        <div className="bg-muted">
          <SettingRow
            label="Theme"
            description="Choose your preferred colour scheme"
          >
            <div className="flex items-center gap-0.5 p-1 rounded-lg bg-background border border-border">
              {themeOptions.map(({ id, label, icon }) => (
                <button
                  key={id}
                  onClick={() => setTheme(id)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all"
                  style={
                    theme === id
                      ? {
                          backgroundColor: "var(--primary)",
                          color: "var(--primary-foreground)",
                        }
                      : { color: "var(--muted-foreground)" }
                  }
                  onMouseEnter={(e) => {
                    if (theme !== id)
                      e.currentTarget.style.color = "var(--foreground)";
                  }}
                  onMouseLeave={(e) => {
                    if (theme !== id)
                      e.currentTarget.style.color = "var(--muted-foreground)";
                  }}
                >
                  <HugeiconsIcon icon={icon} size={13} />
                  {label}
                </button>
              ))}
            </div>
          </SettingRow>
        </div>
      </div>
      {/* 
      <div className="rounded-xl border border-border overflow-hidden">
        <SectionHeader icon={Notification02Icon} label="Notifications" />
        <div className="bg-muted">
          <SettingRow
            label="Security Alerts"
            description="Get notified about potential security issues"
          >
            <Switch
              checked={securityAlerts}
              onCheckedChange={setSecurityAlerts}
            />
          </SettingRow>
          <SettingRow
            label="Password Expiry"
            description="Remind me to update old passwords"
            last
          >
            <Switch
              checked={passwordExpiry}
              onCheckedChange={setPasswordExpiry}
            />
          </SettingRow>
        </div>
      </div> */}

      <div className="rounded-xl border border-border overflow-hidden">
        <SectionHeader icon={Clock01Icon} label="Auto-lock" />
        <div className="bg-muted">
          <SettingRow
            label="Lock after inactivity"
            description="Automatically lock your vault when idle"
            last
          >
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium bg-background border border-border text-foreground hover:bg-accent transition-colors min-w-[120px] justify-between">
                  <span>{currentAutoLockLabel}</span>
                  <HugeiconsIcon icon={ArrowDown01Icon} size={14} />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="min-w-[140px]">
                {AUTO_LOCK_OPTIONS.map((option) => (
                  <DropdownMenuItem
                    key={option.value}
                    onClick={() => setAutoLockTimeout(option.value)}
                    className={`text-xs cursor-pointer ${
                      autoLockTimeout === option.value ? "bg-primary/10" : ""
                    }`}
                  >
                    {option.label}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          </SettingRow>
        </div>
      </div>

      <div className="rounded-xl border border-border overflow-hidden">
        <SectionHeader icon={Globe02Icon} label="Browser Extension" />
        <div className="bg-muted">
          <SettingRow
            label="Reconnect All Browsers"
            description="Re-install native messaging manifests for all detected browsers"
          >
            <div className="flex items-center gap-2">
              {reconnectStatus === "success" && (
                <span className="text-xs text-green-500 flex items-center gap-1">
                  <HugeiconsIcon icon={CheckmarkCircle01Icon} size={12} />
                  Connected
                </span>
              )}
              {reconnectStatus === "error" && (
                <span className="text-xs text-destructive flex items-center gap-1">
                  <HugeiconsIcon icon={Alert02Icon} size={12} />
                  Failed
                </span>
              )}
              <ActionButton
                label={reconnecting ? "Reconnecting..." : "Reconnect All"}
                icon={Globe02Icon}
                onClick={handleReconnect}
                disabled={reconnecting}
              />
            </div>
          </SettingRow>

          <SettingRow
            label="Install for Specific Browser"
            description="Manually connect to a specific browser"
          >
            <div className="flex items-center gap-2">
              {browserInstallStatus === "success" && (
                <span className="text-xs text-green-500 flex items-center gap-1">
                  <HugeiconsIcon icon={CheckmarkCircle01Icon} size={12} />
                  Installed
                </span>
              )}
              {browserInstallStatus === "error" && (
                <span
                  className="text-xs text-destructive flex items-center gap-1 max-w-[180px] truncate"
                  title={browserInstallMsg}
                >
                  <HugeiconsIcon icon={Alert02Icon} size={12} />
                  Failed
                </span>
              )}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button
                    disabled={installingBrowser}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium bg-background border border-border text-foreground hover:bg-accent transition-colors min-w-[120px] justify-between disabled:opacity-50"
                  >
                    <span>
                      {installingBrowser ? "Installing..." : "Select Browser"}
                    </span>
                    <HugeiconsIcon icon={ArrowDown01Icon} size={14} />
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="min-w-[140px]">
                  {BROWSER_OPTIONS.map((b) => (
                    <DropdownMenuItem
                      key={b.id}
                      onClick={() => handleInstallBrowser(b.id)}
                      className="text-xs cursor-pointer"
                    >
                      {b.label}
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </SettingRow>

          <SettingRow
            label="Custom Path (Advanced)"
            description="Install native host manifest to a custom directory"
            last
          >
            <div className="flex items-center gap-2">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium bg-background border border-border text-foreground hover:bg-accent transition-colors min-w-[90px] justify-between">
                    <span>
                      {BROWSER_OPTIONS.find((b) => b.id === customBrowserType)
                        ?.label || "Chrome"}
                    </span>
                    <HugeiconsIcon icon={ArrowDown01Icon} size={12} />
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="min-w-[120px]">
                  {BROWSER_OPTIONS.map((b) => (
                    <DropdownMenuItem
                      key={b.id}
                      onClick={() => setCustomBrowserType(b.id)}
                      className={`text-xs cursor-pointer ${customBrowserType === b.id ? "bg-primary/10" : ""}`}
                    >
                      {b.label}
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>
              <input
                type="text"
                value={customPath}
                onChange={(e) => setCustomPath(e.target.value)}
                placeholder="Path to NativeMessagingHosts"
                className="px-2.5 py-1.5 rounded-lg text-xs bg-background border border-border text-foreground w-[200px] focus:outline-none focus:border-primary"
              />
              <ActionButton
                label={installingCustom ? "Installing..." : "Install"}
                onClick={handleInstallCustom}
                disabled={installingCustom || !customPath.trim()}
              />
            </div>
          </SettingRow>
        </div>
      </div>
    </div>
  );
}

function SecuritySettings() {
  const [showChangePassword, setShowChangePassword] = useState(false);
  const [showPasswordHint, setShowPasswordHint] = useState(false);

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-border overflow-hidden">
        <SectionHeader icon={Key01Icon} label="Master Password" />
        <div className="bg-muted">
          <SettingRow
            label="Change Master Password"
            description="Update your vault's master password"
          >
            <ActionButton
              label="Change"
              onClick={() => setShowChangePassword(true)}
            />
          </SettingRow>
          <SettingRow
            label="Password Hint"
            description="Add a hint to help remember your password"
            last
          >
            <ActionButton
              label="Set Hint"
              onClick={() => setShowPasswordHint(true)}
            />
          </SettingRow>
        </div>
      </div>

      <ChangeMasterPasswordDialog
        open={showChangePassword}
        onOpenChange={setShowChangePassword}
      />
      <PasswordHintDialog
        open={showPasswordHint}
        onOpenChange={setShowPasswordHint}
      />

      <div className="rounded-xl border border-border overflow-hidden">
        <SectionHeader icon={LockPasswordIcon} label="Security Audit Log" />
        <div className="bg-muted">
          <SettingRow
            label="Last successful login"
            description="Today at 10:30 AM"
          >
            <span
              className="flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full"
              style={{
                backgroundColor:
                  "color-mix(in oklch, var(--chart-4) 12%, transparent)",
                color: "var(--chart-4)",
              }}
            >
              <HugeiconsIcon icon={CheckmarkCircle01Icon} size={12} />
              Success
            </span>
          </SettingRow>
          <SettingRow
            label="Last failed attempt"
            description="Yesterday at 3:45 PM"
            last
          >
            <span
              className="flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full"
              style={{
                backgroundColor:
                  "color-mix(in oklch, var(--destructive) 12%, transparent)",
                color: "var(--destructive)",
              }}
            >
              <HugeiconsIcon icon={Alert02Icon} size={12} />
              Failed
            </span>
          </SettingRow>
        </div>
      </div>
    </div>
  );
}

function DataSettings() {
  const [showExport, setShowExport] = useState(false);
  const [showImport, setShowImport] = useState(false);
  const [showClearClipboard, setShowClearClipboard] = useState(false);
  const [showDeleteAll, setShowDeleteAll] = useState(false);

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-border overflow-hidden">
        <SectionHeader icon={Database02Icon} label="Import & Export" />
        <div className="bg-muted">
          <SettingRow
            label="Export Vault"
            description="Download an encrypted backup of your vault"
          >
            <ActionButton
              label="Export"
              icon={DownloadCircle01Icon}
              onClick={() => setShowExport(true)}
            />
          </SettingRow>
          <SettingRow
            label="Import Vault"
            description="Restore your vault from a previous backup"
            last
          >
            <ActionButton
              label="Import"
              icon={UploadCircle01Icon}
              onClick={() => setShowImport(true)}
            />
          </SettingRow>
        </div>
      </div>

      <div
        className="rounded-xl overflow-hidden"
        style={{
          border:
            "1px solid color-mix(in oklch, var(--destructive) 25%, transparent)",
        }}
      >
        <div className="flex items-center gap-2 px-4 py-3 border-b border-destructive/20 bg-background">
          <HugeiconsIcon
            icon={Delete02Icon}
            size={14}
            style={{ color: "var(--destructive)" }}
          />
          <span className="text-xs font-semibold uppercase tracking-wider text-destructive">
            Danger Zone
          </span>
        </div>
        <div className="bg-muted">
          <SettingRow
            label="Clear Clipboard"
            description="Remove all copied passwords from the clipboard"
          >
            <ActionButton
              label="Clear"
              onClick={() => setShowClearClipboard(true)}
            />
          </SettingRow>
          <SettingRow
            label="Delete All Data"
            description="Permanently erase all vault data. This cannot be undone."
            danger
            last
          >
            <ActionButton
              label="Delete All"
              danger
              icon={Delete02Icon}
              onClick={() => setShowDeleteAll(true)}
            />
          </SettingRow>
        </div>
      </div>

      <ExportVaultDialog open={showExport} onOpenChange={setShowExport} />
      <ImportVaultDialog open={showImport} onOpenChange={setShowImport} />
      <ClearClipboardDialog
        open={showClearClipboard}
        onOpenChange={setShowClearClipboard}
      />
      <DeleteAllDataDialog
        open={showDeleteAll}
        onOpenChange={setShowDeleteAll}
      />
    </div>
  );
}

export function SettingsPanel() {
  const [activeTab, setActiveTab] = useState<Tab>("general");

  return (
    <div className="flex-1 h-full overflow-y-auto bg-background">
      <div className="h-full flex flex-col p-6 gap-5">
        <div className="flex items-center gap-3 pb-4 border-b border-border shrink-0">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
            style={{
              backgroundColor:
                "color-mix(in oklch, var(--muted-foreground) 10%, transparent)",
            }}
          >
            <HugeiconsIcon
              icon={Settings02Icon}
              size={20}
              className="text-muted-foreground"
            />
          </div>
          <div>
            <h1 className="text-sm font-semibold text-foreground">Settings</h1>
            <p className="text-xs text-muted-foreground">
              Customise your VaultKeeper experience
            </p>
          </div>
        </div>

        <div className="flex gap-0.5 shrink-0 border-b border-border">
          {TABS.map(({ id, label, icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className="flex items-center gap-2 px-4 py-2.5 text-xs font-medium border-b-2 transition-colors -mb-px"
              style={
                activeTab === id
                  ? { borderColor: "var(--primary)", color: "var(--primary)" }
                  : {
                      borderColor: "transparent",
                      color: "var(--muted-foreground)",
                    }
              }
              onMouseEnter={(e) => {
                if (activeTab !== id)
                  e.currentTarget.style.color = "var(--foreground)";
              }}
              onMouseLeave={(e) => {
                if (activeTab !== id)
                  e.currentTarget.style.color = "var(--muted-foreground)";
              }}
            >
              <HugeiconsIcon icon={icon} size={14} />
              {label}
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-y-auto min-h-0">
          {activeTab === "general" && <GeneralSettings />}
          {activeTab === "security" && <SecuritySettings />}
          {activeTab === "data" && <DataSettings />}
        </div>
      </div>
    </div>
  );
}
