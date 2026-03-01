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
    // Check if first run on mount
    if (isFirstRun) {
      setIsSetupMode(true);
    }
  }, [isFirstRun]);

  useEffect(() => {
    // Load password hint when not in setup mode
    if (!isSetupMode && !isFirstRun) {
      loadPasswordHint();
    }
  }, [isSetupMode, isFirstRun]);

  const loadPasswordHint = async () => {
    try {
      const response = await invoke<{
        success: boolean;
        data?: string | null;
        error?: string;
      }>("get_password_hint");

      if (response.success) {
        setPasswordHint(response.data || null);
      }
    } catch (err) {
      console.error("Failed to load password hint:", err);
    }
  };

  useEffect(() => {
    // Calculate password strength
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
      className="w-full h-full flex items-center justify-center relative overflow-hidden"
      data-tauri-drag-region
    >
      {/* Background Effects */}
      <div className="absolute inset-0 bg-gradient-to-br from-background via-background to-background-secondary" />
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-[120px] animate-pulse" />
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-secondary/20 rounded-full blur-[120px] animate-pulse delay-1000" />

      {/* Grid Pattern */}
      <div
        className="absolute inset-0 opacity-[0.02]"
        style={{
          backgroundImage: `linear-gradient(rgba(255,255,255,.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.1) 1px, transparent 1px)`,
          backgroundSize: "50px 50px",
        }}
      />

      {/* Main Card */}
      <div className="relative z-10 w-full max-w-md mx-4">
        {/* Glass Card */}
        <div className="glass rounded-2xl p-8 shadow-glow">
          {/* Logo */}
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

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Password Input */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground-secondary">
                Master Password
              </label>
              <div className="relative group">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-foreground-muted transition-colors group-focus-within:text-primary" />
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={
                    isSetupMode
                      ? "Create a strong password"
                      : "Enter your password"
                  }
                  className="w-full bg-background-tertiary border border-border rounded-xl py-3.5 pl-12 pr-12 text-foreground placeholder:text-foreground-muted focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
                  disabled={isLoading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-foreground-muted hover:text-foreground transition-colors"
                  disabled={isLoading}
                >
                  {showPassword ? (
                    <EyeOff className="w-5 h-5" />
                  ) : (
                    <Eye className="w-5 h-5" />
                  )}
                </button>
              </div>

              {/* Password Hint - Show in login mode if hint exists */}
              {!isSetupMode && passwordHint && (
                <div className="pt-1">
                  {!showHint ? (
                    <button
                      type="button"
                      onClick={() => setShowHint(true)}
                      className="flex items-center gap-1.5 text-xs text-primary hover:text-primary/80 transition-colors"
                    >
                      <HelpCircleIcon className="w-3.5 h-3.5" />
                      Show password hint
                    </button>
                  ) : (
                    <div className="bg-primary/10 border border-primary/20 rounded-lg p-2.5 animate-fade-in">
                      <div className="flex items-center gap-1.5 mb-1">
                        <HelpCircleIcon className="w-3.5 h-3.5 text-primary" />
                        <span className="text-xs font-medium text-primary">
                          Password Hint
                        </span>
                      </div>
                      <p className="text-sm text-foreground">{passwordHint}</p>
                    </div>
                  )}
                </div>
              )}

              {/* Strength Indicator (only in setup mode) */}
              {isSetupMode && password.length > 0 && (
                <div className="space-y-2 pt-1">
                  <div className="flex gap-1">
                    {[0, 1, 2, 3].map((i) => (
                      <div
                        key={i}
                        className={`h-1 flex-1 rounded-full transition-all duration-300 ${
                          i < strength
                            ? getStrengthColor()
                            : "bg-background-elevated"
                        }`}
                      />
                    ))}
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-foreground-muted">
                      Password strength
                    </span>
                    <span
                      className={`text-xs font-medium ${
                        strength >= 3
                          ? "text-success"
                          : strength >= 2
                            ? "text-warning"
                            : "text-error"
                      }`}
                    >
                      {getStrengthLabel()}
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* Confirm Password (only in setup mode) */}
            {isSetupMode && (
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground-secondary">
                  Confirm Password
                </label>
                <div className="relative group">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-foreground-muted transition-colors group-focus-within:text-primary" />
                  <input
                    type={showConfirm ? "text" : "password"}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Confirm your password"
                    className="w-full bg-background-tertiary border border-border rounded-xl py-3.5 pl-12 pr-12 text-foreground placeholder:text-foreground-muted focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
                    disabled={isLoading}
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirm(!showConfirm)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-foreground-muted hover:text-foreground transition-colors"
                    disabled={isLoading}
                  >
                    {showConfirm ? (
                      <EyeOff className="w-5 h-5" />
                    ) : (
                      <Eye className="w-5 h-5" />
                    )}
                  </button>
                </div>
                {confirmPassword && password !== confirmPassword && (
                  <p className="text-xs text-error">Passwords do not match</p>
                )}
              </div>
            )}

            {/* Error Message */}
            {error && (
              <div className="bg-error-subtle border border-error/20 rounded-lg p-3 animate-fade-in">
                <p className="text-sm text-error">{error}</p>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={
                isLoading || (isSetupMode && password !== confirmPassword)
              }
              className="w-full bg-primary hover:bg-primary-hover disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-3.5 rounded-xl transition-all duration-200 flex items-center justify-center gap-2 shadow-lg shadow-primary/25 hover:shadow-primary/40"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  {isSetupMode ? "Create Vault" : "Unlock Vault"}
                  <ChevronRight className="w-5 h-5" />
                </>
              )}
            </button>
          </form>

          {/* Toggle Mode */}
          <div className="mt-6 text-center">
            {!isFirstRun && (
              <button
                type="button"
                onClick={() => {
                  setIsSetupMode(!isSetupMode);
                  clearError();
                  setPassword("");
                  setConfirmPassword("");
                  setShowHint(false);
                }}
                className="text-sm text-foreground-secondary hover:text-primary transition-colors"
              >
                {isSetupMode
                  ? "Already have a vault? Sign in"
                  : "Create new vault"}
              </button>
            )}
          </div>

          {/* Security Badge */}
          <div className="mt-8 pt-6 border-t border-border">
            <div className="flex items-center justify-center gap-4 text-foreground-muted">
              <div className="flex items-center gap-1.5">
                <Sparkles className="w-4 h-4" />
                <span className="text-xs">End-to-End Encrypted</span>
              </div>
              <div className="w-1 h-1 rounded-full bg-foreground-muted" />
              <span className="text-xs">Zero-Knowledge</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
