import React, { useState, useEffect } from "react";
import browser from "webextension-polyfill";
import { CredentialType } from "./Sidebar";

interface DetailProps {
  credential: CredentialType | null;
  onEdit?: (cred: CredentialType) => void;
  onDelete?: (id: string) => void;
}

export const Details: React.FC<DetailProps> = ({
  credential,
  onEdit,
  onDelete,
}) => {
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [totp, setTotp] = useState<string | null>(null);
  const [cooldown, setCooldown] = useState<number>(30);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  useEffect(() => {
    setShowDeleteConfirm(false);
    setShowPassword(false);
    let interval: ReturnType<typeof setInterval>;

    if (credential?.totp_secret) {
      const fetchTotp = async () => {
        try {
          const res: any = await browser.runtime.sendMessage({
            action: "get_totp",
            id: credential.id,
          });
          if (res && res.success) {
            setTotp(res.code); // Use `res.code` instead of `res.totp` if that's what backend returns
            setCooldown(res.remaining_seconds || 30);
          }
        } catch (e) {}
      };

      fetchTotp();

      interval = setInterval(() => {
        setCooldown((prev) => {
          if (prev <= 1) {
            fetchTotp();
            return 30; // Reset temporarily while fetching
          }
          return prev - 1;
        });
      }, 1000);
    } else {
      setTotp(null);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [credential]);

  if (!credential) {
    return (
      <div className="flex-1 h-full flex flex-col items-center justify-center text-muted-foreground bg-background">
        <svg
          className="w-16 h-16 mb-4 opacity-20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4" />
        </svg>
        <p className="text-[14px] font-medium opacity-60">
          Select an item to view details
        </p>
      </div>
    );
  }

  const handleCopy = async (text: string, field: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedField(field);
      setTimeout(() => setCopiedField(null), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  const autofill = async () => {
    try {
      const [tab] = await browser.tabs.query({
        active: true,
        currentWindow: true,
      });
      if (tab?.id) {
        await browser.tabs.sendMessage(tab.id, {
          action: "fill",
          username: credential.username,
          password: credential.password,
          totp: totp,
        });
        window.close();
      }
    } catch (err) {}
  };

  return (
    <div className="flex-1 h-full flex flex-col bg-background overflow-hidden relative">
      <div className="flex-1 overflow-y-auto px-6 py-6 pb-20 relative z-10 scrollbar-thin scrollbar-thumb-border/50 scrollbar-track-transparent">
        <div className="flex items-start justify-between mb-8">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-card border border-border shadow-sm flex items-center justify-center p-2.5 shrink-0">
              <img
                src={`https://www.google.com/s2/favicons?domain=${credential.domain}&sz=64`}
                alt={credential.domain}
                className="w-full h-full object-contain"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = "none";
                  (
                    e.target as HTMLImageElement
                  ).nextElementSibling?.classList.remove("hidden");
                }}
              />
              <svg
                className="w-8 h-8 text-black hidden"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
              >
                <circle cx="12" cy="12" r="10" />
                <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-foreground truncate max-w-[200px]">
                {credential.domain.replace(/^(https?:\/\/)?(www\.)?/, "")}
              </h1>
              <p className="text-sm text-muted-foreground truncate w-[200px]">
                {credential.username}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1.5 mt-1">
            <button
              onClick={() => onEdit?.(credential)}
              className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted rounded-xl transition-colors"
              title="Edit"
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M12 20h9" />
                <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z" />
              </svg>
            </button>
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="p-2 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-xl transition-colors"
              title="Delete"
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M3 6h18" />
                <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
                <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
              </svg>
            </button>
          </div>
        </div>

        <div className="space-y-4">
          <div className="w-full">
            <p className="text-[12px] font-semibold text-muted-foreground uppercase tracking-wider mb-1.5 ml-1">
              Username
            </p>
            <div className="flex items-center w-full bg-card/60 backdrop-blur-sm border border-border/50 rounded-xl overflow-hidden hover:border-primary/40 transition-colors">
              <input
                type="text"
                readOnly
                value={credential.username}
                className="flex-1 bg-transparent px-4 py-3 text-[14px] text-foreground outline-none w-full min-w-0"
              />
              <button
                onClick={() => handleCopy(credential.username, "user")}
                title="Copy username"
                className="shrink-0 px-4 h-full flex items-center justify-center border-l border-border/30 hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
              >
                {copiedField === "user" ? (
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="var(--primary)"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                ) : (
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                  </svg>
                )}
              </button>
            </div>
          </div>

          <div className="w-full">
            <p className="text-[12px] font-semibold text-muted-foreground uppercase tracking-wider mb-1.5 ml-1">
              Password
            </p>
            <div className="flex items-center w-full bg-card/60 backdrop-blur-sm border border-border/50 rounded-xl overflow-hidden hover:border-primary/40 transition-colors">
              <input
                type={showPassword ? "text" : "password"}
                readOnly
                value={credential.password || ""}
                className="flex-1 bg-transparent px-4 py-3 text-[14px] text-foreground tracking-widest outline-none w-full min-w-0"
              />
              <button
                onClick={() => setShowPassword(!showPassword)}
                title={showPassword ? "Hide password" : "Show password"}
                className="shrink-0 px-3 h-full flex items-center justify-center hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
              >
                {showPassword ? (
                  <svg
                    width="16"
                    height="16"
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
                    width="16"
                    height="16"
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
              <button
                onClick={() => handleCopy(credential.password || "", "pass")}
                title="Copy password"
                className="shrink-0 px-4 h-full flex items-center justify-center border-l border-border/30 hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
              >
                {copiedField === "pass" ? (
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="var(--primary)"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                ) : (
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                  </svg>
                )}
              </button>
            </div>
          </div>

          {credential.totp_secret && (
            <div className="w-full">
              <p className="text-[12px] font-semibold text-muted-foreground uppercase tracking-wider mb-1.5 ml-1 flex items-center gap-1.5">
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <circle cx="12" cy="12" r="10" />
                  <polyline points="12 6 12 12 16 14" />
                </svg>
                Authenticator
              </p>
              <div className="flex items-center w-full bg-card/60 border border-border/50 rounded-xl overflow-hidden hover:border-primary/40 transition-colors">
                <div className="flex-1 px-4 py-3 text-[15px] font-mono font-medium outline-none w-full tracking-[0.2em] flex items-center text-foreground">
                  {totp ? totp : "------"}
                </div>
                <button
                  onClick={() => handleCopy(totp || "", "totp")}
                  className="shrink-0 px-4 h-full py-3 flex items-center justify-center border-l border-border/30 hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                >
                  {copiedField === "totp" ? (
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="var(--primary)"
                      strokeWidth="2.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  ) : (
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                    </svg>
                  )}
                </button>
              </div>
              <p className="text-[11px] font-medium text-muted-foreground mt-2 ml-1 opacity-80">
                Refreshes in {cooldown}s
              </p>
            </div>
          )}
        </div>
      </div>

      <div className="p-4 bg-background border-t border-border/50 shrink-0">
        <button
          onClick={autofill}
          className="w-full py-2.5 bg-primary text-primary-foreground font-semibold rounded-xl text-[14px] shadow-lg shadow-primary/20 hover:opacity-90 active:scale-[0.98] transition-all flex items-center justify-center gap-2 border-none cursor-pointer"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
          </svg>
          Autofill on current page
        </button>
      </div>

      {showDeleteConfirm && (
        <div className="absolute inset-0 z-50 flex items-center justify-center p-6 bg-background/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full bg-card border border-border rounded-2xl shadow-xl overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="p-6">
              <div className="w-12 h-12 rounded-full bg-destructive/10 flex items-center justify-center mb-4">
                <svg
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="var(--destructive)"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M3 6h18" />
                  <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
                  <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-foreground mb-2">
                Delete Credential?
              </h3>
              <p className="text-sm text-muted-foreground">
                This action cannot be undone. This credential will be
                permanently removed from your vault.
              </p>
            </div>
            <div className="p-4 bg-muted/50 border-t border-border flex gap-3">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="flex-1 px-4 py-2.5 bg-background border border-border text-foreground hover:bg-muted font-medium rounded-xl text-sm transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setShowDeleteConfirm(false);
                  if (onDelete && credential.id) {
                    onDelete(credential.id);
                  }
                }}
                className="flex-1 px-4 py-2.5 bg-destructive text-destructive-foreground hover:bg-destructive/90 font-medium rounded-xl text-sm transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
