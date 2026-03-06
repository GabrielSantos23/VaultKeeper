import React, { useState } from "react";
import browser from "webextension-polyfill";
import { CredentialType } from "./Sidebar";

interface EditCredentialProps {
  credential: CredentialType;
  onSave: () => void;
  onCancel: () => void;
}

export const EditCredential: React.FC<EditCredentialProps> = ({
  credential,
  onSave,
  onCancel,
}) => {
  const [domain, setDomain] = useState(credential.domain || "");
  const [username, setUsername] = useState(credential.username || "");
  const [password, setPassword] = useState(credential.password || "");
  const [notes, setNotes] = useState(credential.notes || "");
  const [totpSecret, setTotpSecret] = useState(credential.totp_secret || "");
  const [backupCodes, setBackupCodes] = useState(credential.backup_codes || "");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [showPassword, setShowPassword] = useState(false);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!domain || !username || !password) {
      setError("Domain, Username, and Password are required");
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const resp: any = await browser.runtime.sendMessage({
        action: "update_credentials",
        id: credential.id,
        domain: domain.trim(),
        username: username.trim(),
        password: password,
        notes: notes.trim() || null,
        totp_secret: totpSecret.trim() || null,
        backup_codes: backupCodes.trim() || null,
      });

      if (resp && resp.success) {
        onSave();
      } else {
        setError(resp.error || "Failed to update credential");
      }
    } catch (err: any) {
      setError(err.message || "An error occurred while saving");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex-1 h-full flex flex-col bg-background overflow-hidden relative">
      <div className="flex items-center justify-between px-6 py-4 border-b border-border/50 shrink-0 bg-background/80 backdrop-blur-sm z-10">
        <h2 className="text-lg font-semibold text-foreground tracking-tight">
          Edit Item
        </h2>
        <button
          onClick={onCancel}
          className="p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground rounded-lg transition-colors"
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M18 6 6 18" />
            <path d="m6 6 12 12" />
          </svg>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6 scrollbar-thin scrollbar-thumb-border/50 scrollbar-track-transparent">
        {error && (
          <div className="mb-4 p-3 bg-destructive/10 border border-destructive/20 text-destructive text-sm rounded-xl">
            {error}
          </div>
        )}

        <form id="edit-form" onSubmit={handleSave} className="space-y-4 pb-10">
          <div className="space-y-1.5">
            <label className="text-[12px] font-semibold text-muted-foreground uppercase tracking-wider ml-1">
              Domain / URL *
            </label>
            <input
              type="text"
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              disabled={isLoading}
              className="w-full bg-card/60 border border-border/50 rounded-xl px-4 py-3 text-[14px] text-foreground outline-none focus:border-primary/50 transition-colors"
              placeholder="example.com"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-[12px] font-semibold text-muted-foreground uppercase tracking-wider ml-1">
              Username *
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={isLoading}
              className="w-full bg-card/60 border border-border/50 rounded-xl px-4 py-3 text-[14px] text-foreground outline-none focus:border-primary/50 transition-colors"
              placeholder="user@example.com"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-[12px] font-semibold text-muted-foreground uppercase tracking-wider ml-1">
              Password *
            </label>
            <div className="flex items-center w-full bg-card/60 border border-border/50 rounded-xl overflow-hidden focus-within:border-primary/50 transition-colors">
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={isLoading}
                className="flex-1 bg-transparent px-4 py-3 text-[14px] text-foreground outline-none min-w-0"
                placeholder="••••••••••••"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                tabIndex={-1}
                className="px-3 text-muted-foreground hover:text-foreground transition-colors"
              >
                {showPassword ? (
                  <svg
                    width="18"
                    height="18"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                    <line x1="1" y1="1" x2="23" y2="23"></line>
                  </svg>
                ) : (
                  <svg
                    width="18"
                    height="18"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                    <circle cx="12" cy="12" r="3"></circle>
                  </svg>
                )}
              </button>
            </div>
          </div>

          <div className="space-y-1.5 pt-2 border-t border-border/30">
            <label className="text-[12px] font-semibold text-muted-foreground uppercase tracking-wider ml-1">
              Authenticator (TOTP Secret)
            </label>
            <input
              type="text"
              value={totpSecret}
              onChange={(e) => setTotpSecret(e.target.value)}
              disabled={isLoading}
              className="w-full bg-card/60 border border-border/50 rounded-xl px-4 py-3 text-[14px] text-foreground outline-none focus:border-primary/50 transition-colors font-mono"
              placeholder="e.g. JBSWY3DPEHPK3PXP"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-[12px] font-semibold text-muted-foreground uppercase tracking-wider ml-1">
              Recovery / Backup Codes
            </label>
            <textarea
              value={backupCodes}
              onChange={(e) => setBackupCodes(e.target.value)}
              disabled={isLoading}
              rows={3}
              className="w-full bg-card/60 border border-border/50 rounded-xl px-4 py-3 text-[14px] text-foreground outline-none focus:border-primary/50 transition-colors font-mono resize-none"
              placeholder="Enter fallback codes..."
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-[12px] font-semibold text-muted-foreground uppercase tracking-wider ml-1">
              Notes
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              disabled={isLoading}
              rows={3}
              className="w-full bg-card/60 border border-border/50 rounded-xl px-4 py-3 text-[14px] text-foreground outline-none focus:border-primary/50 transition-colors resize-none"
              placeholder="Optional details..."
            />
          </div>
        </form>
      </div>

      <div className="p-4 bg-background border-t border-border/50 shrink-0 flex gap-3 z-10">
        <button
          type="button"
          onClick={onCancel}
          disabled={isLoading}
          className="flex-1 py-2.5 bg-muted text-foreground font-semibold rounded-xl text-[14px] hover:bg-muted/80 transition-colors border-none cursor-pointer"
        >
          Cancel
        </button>
        <button
          type="submit"
          form="edit-form"
          disabled={isLoading}
          className="flex-1 py-2.5 bg-primary text-primary-foreground font-semibold rounded-xl text-[14px] shadow-lg shadow-primary/20 hover:opacity-90 active:scale-[0.98] transition-all flex items-center justify-center gap-2 border-none cursor-pointer disabled:opacity-70 disabled:pointer-events-none"
        >
          {isLoading ? (
            <svg
              className="animate-spin w-5 h-5"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              ></circle>
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
          ) : (
            "Save Changes"
          )}
        </button>
      </div>
    </div>
  );
};
