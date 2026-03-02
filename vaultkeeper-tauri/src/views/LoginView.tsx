import { useState, useEffect } from "react";
import {
  Lock,
  Eye,
  EyeOff,
  Loader2,
  ChevronRight,
  Sparkles,
  HelpCircleIcon,
} from "lucide-react";
import { useAuthStore } from "../stores/authStore";
import { invoke } from "@tauri-apps/api/core";

export function LoginView() {
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [isSetupMode, setIsSetupMode] = useState(false);
  const [strength, setStrength] = useState(0);
  const [passwordHint, setPasswordHint] = useState<string | null>(null);
  const [showHint, setShowHint] = useState(false);

  const { login, createVault, isLoading, error, clearError, isFirstRun } =
    useAuthStore();

  useEffect(() => {
    if (isFirstRun) setIsSetupMode(true);
  }, [isFirstRun]);

  useEffect(() => {
    if (!isSetupMode && !isFirstRun) loadPasswordHint();
  }, [isSetupMode, isFirstRun]);

  const loadPasswordHint = async () => {
    try {
      const response = await invoke<{
        success: boolean;
        data?: string | null;
      }>("get_password_hint");

      if (response.success) {
        setPasswordHint(response.data || null);
      }
    } catch (err) {
      console.error("Failed to load password hint:", err);
    }
  };

  useEffect(() => {
    let score = 0;
    if (password.length >= 8) score++;
    if (password.length >= 12) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[0-9]/.test(password)) score++;
    if (/[^A-Za-z0-9]/.test(password)) score++;
    setStrength(Math.min(score, 4));
  }, [password]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();

    if (isSetupMode) {
      await createVault(password, confirmPassword);
    } else {
      await login(password);
    }
  };

  const getStrengthColor = () => {
    switch (strength) {
      case 0:
      case 1:
        return "bg-error";
      case 2:
        return "bg-warning";
      case 3:
        return "bg-info";
      case 4:
        return "bg-success";
      default:
        return "bg-foreground-muted";
    }
  };

  const getStrengthLabel = () => {
    switch (strength) {
      case 0:
        return "Too weak";
      case 1:
        return "Weak";
      case 2:
        return "Fair";
      case 3:
        return "Good";
      case 4:
        return "Strong";
      default:
        return "";
    }
  };

  return (
    <div
      data-tauri-drag-region
      className="w-full h-full relative overflow-hidden"
    >
      <div
        data-tauri-drag-region
        className="absolute inset-0 bg-gradient-to-br from-background via-background to-background-secondary"
      />
      <div
        data-tauri-drag-region
        className="absolute top-0 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-[120px] animate-pulse"
      />
      <div
        data-tauri-drag-region
        className="absolute bottom-0 right-1/4 w-96 h-96 bg-secondary/20 rounded-full blur-[120px] animate-pulse delay-1000"
      />

      <div
        data-tauri-drag-region
        className="absolute inset-0 opacity-[0.02]"
        style={{
          backgroundImage: `linear-gradient(rgba(255,255,255,.1) 1px, transparent 1px),
                            linear-gradient(90deg, rgba(255,255,255,.1) 1px, transparent 1px)`,
          backgroundSize: "50px 50px",
        }}
      />

      <div className="relative z-10 w-full h-full flex items-center justify-center pointer-events-none">
        <div className="pointer-events-auto w-full max-w-md mx-4">
          <div className="glass rounded-2xl p-8 shadow-glow">
            <div className="flex flex-col items-center mb-8">
              <div className="w-20 h-20 rounded-2xl overflow-hidden flex items-center justify-center mb-4 shadow-glow animate-pulse-glow">
                <img
                  src="/logo.png"
                  alt="VaultKeeper"
                  className="w-full h-full object-cover"
                />
              </div>

              <h1 className="text-3xl font-bold gradient-text">VaultKeeper</h1>

              <p className="text-foreground-secondary mt-2 text-sm">
                {isSetupMode
                  ? "Create your secure vault"
                  : "Enter your master password"}
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground-secondary">
                  Master Password
                </label>

                <div className="relative group">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-foreground-muted group-focus-within:text-primary" />

                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder={
                      isSetupMode
                        ? "Create a strong password"
                        : "Enter your password"
                    }
                    className="w-full bg-background-tertiary border border-border rounded-xl py-3.5 pl-12 pr-12 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                    disabled={isLoading}
                  />

                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-foreground-muted hover:text-foreground"
                  >
                    {showPassword ? <EyeOff /> : <Eye />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={
                  isLoading || (isSetupMode && password !== confirmPassword)
                }
                className="w-full bg-primary hover:bg-primary-hover text-white font-semibold py-3.5 rounded-xl flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <Loader2 className="animate-spin" />
                ) : (
                  <>
                    {isSetupMode ? "Create Vault" : "Unlock Vault"}
                    <ChevronRight />
                  </>
                )}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
