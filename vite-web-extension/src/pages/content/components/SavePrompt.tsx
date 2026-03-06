import React, { useState, useEffect, useCallback } from "react";
import browser from "webextension-polyfill";
import { Icons } from "./Icons";
import { currentDomain } from "../constants";
import { saveCredentials, updateCredentials } from "../api";
import { requestCredentials } from "../core";
import { clearPendingCredentials } from "../helpers";

export const SavePrompt = ({
  config,
  onClose,
}: {
  config: any;
  onClose: () => void;
}) => {
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [isClosing, setIsClosing] = useState(false);

  const handleClose = useCallback(() => {
    setIsClosing(true);
    clearPendingCredentials();
    setTimeout(onClose, 250);
  }, [onClose]);

  useEffect(() => {
    const timer = setTimeout(
      handleClose,
      config.showUnlockForm ? 60000 : 30000,
    );
    return () => clearTimeout(timer);
  }, [handleClose, config]);

  const handleAction = async () => {
    if (config.showUnlockForm) {
      if (!password) return setError("Please enter your master password");
      setLoading(true);
      try {
        const r: any = await browser.runtime.sendMessage({
          action: "unlock",
          password,
        });
        if (r?.success) {
          handleClose();
          if (config.unlockContext === "fill") {
            requestCredentials(config.targetField);
          } else {
            if (config.isUpdateMode && config.credentialId) {
              await updateCredentials(config.credentials, config.credentialId);
            } else {
              await saveCredentials(config.credentials);
            }
          }
        } else {
          setError("Invalid master password");
        }
      } catch {
        setError("Failed to unlock vault");
      } finally {
        setLoading(false);
      }
    } else {
      setLoading(true);
      let res;
      if (config.isUpdateMode && config.credentialId) {
        res = await updateCredentials(config.credentials, config.credentialId);
      } else {
        res = await saveCredentials(config.credentials);
      }
      setLoading(false);
      if (res !== "locked") {
        handleClose();
      }
    }
  };

  const handleNever = () => {
    const list = JSON.parse(
      localStorage.getItem("vaultkeeper_never_save") || "[]",
    );
    list.push(currentDomain);
    localStorage.setItem("vaultkeeper_never_save", JSON.stringify(list));
    handleClose();
  };

  return (
    <div className="fixed! inset-0! z-2147483647 flex! items-start! justify-end! p-5! pointer-events-none! font-['Inter','Segoe_UI',system-ui,sans-serif]!">
      <div
        className="fixed inset-0 bg-black/35 backdrop-blur-[6px] pointer-events-auto transition-opacity duration-250"
        style={{ opacity: isClosing ? 0 : 1 }}
        onClick={handleClose}
      />
      <div
        className={`relative w-[420px]! bg-card! border! border-border! rounded-[16px]! overflow-hidden! pointer-events-auto! ${isClosing ? "animate-[vk-slide-up-out_0.25s_cubic-bezier(0.4,0,1,1)_forwards]" : "animate-[vk-slide-down_0.35s_cubic-bezier(0.16,1,0.3,1)]"}`}
        style={{ fontFamily: "'Inter', 'Segoe UI', system-ui, sans-serif" }}
      >
        <div className="flex! items-center! justify-between! px-6! pt-5! pb-1!">
          <p className="text-[15px]! font-semibold! text-card-foreground! tracking-tight! m-0! text-left! normal-case!">
            {config.showUnlockForm
              ? "Unlock vault"
              : config.isUpdateMode
                ? "Update password?"
                : "Save this password?"}
          </p>
          <button
            onClick={handleClose}
            className="w-7! h-7! flex! items-center! justify-center! bg-transparent! border! border-transparent! rounded-md! text-muted-foreground! cursor-pointer! hover:bg-accent! hover:text-accent-foreground! transition-all! duration-200! p-0!"
          >
            <Icons.Close />
          </button>
        </div>

        <div className="px-6! py-5!">
          {config.showUnlockForm ? (
            <div className="flex! flex-col! items-center! mb-1!">
              <div className="w-14! h-14! rounded-2xl! bg-muted! border! border-border! flex! items-center! justify-center! mb-5!">
                <Icons.Lock
                  size={26}
                  color="currentColor"
                  className="text-primary!"
                  strokeWidth={2.5}
                />
              </div>
              <p className="text-[13px]! text-muted-foreground! text-center! mb-5! leading-relaxed! m-0! normal-case!">
                {config.unlockContext === "fill"
                  ? "Enter your master password to access credentials"
                  : "Enter your master password to save credentials"}
              </p>
              <input
                type="password"
                id="vk-master-password"
                autoFocus
                placeholder="Master Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAction()}
                className="w-full! h-[44px]! px-4! m-0! bg-input/20! text-foreground! border-[1.5px]! border-input! rounded-[12px]! text-[15px]! outline-none! focus:border-primary! focus:shadow-[0_0_0_3px_var(--color-primary-10)]! transition-all! duration-200! font-['Inter','Segoe_UI',system-ui,sans-serif]! box-border! placeholder:text-muted-foreground!"
                style={{ WebkitAppearance: "none", appearance: "none" }}
              />
              {error && (
                <p className="mt-2.5 px-3.5 py-2.5 bg-destructive/10 border border-destructive/20 rounded-md text-destructive text-[13px] w-full text-center">
                  {error}
                </p>
              )}
            </div>
          ) : (
            <>
              <div className="mb-5!">
                <div className="text-[11px]! font-medium! text-muted-foreground! uppercase! tracking-widest! mb-1.5! text-left! leading-normal! m-0!">
                  Website
                </div>
                <div className="text-[14px]! font-medium! text-foreground! truncate! text-left! leading-normal! m-0! normal-case!">
                  {currentDomain}
                </div>
              </div>
              <div className="mb-5!">
                <div className="text-[11px]! font-medium! text-muted-foreground! uppercase! tracking-widest! mb-1.5! text-left! leading-normal! m-0!">
                  Username
                </div>
                <div className="text-[14px]! font-medium! text-foreground! truncate! text-left! leading-normal! m-0! normal-case!">
                  {config.credentials?.username || "-"}
                </div>
              </div>
              <div>
                <div className="text-[11px]! font-medium! text-muted-foreground! uppercase! tracking-widest! mb-1.5! text-left! leading-normal! m-0!">
                  Password
                </div>
                <div className="text-[14px]! font-medium! text-foreground! text-left! leading-normal! m-0! normal-case!">
                  ••••••••
                </div>
              </div>
            </>
          )}
        </div>

        <div className="flex! gap-3! px-6! pb-6!">
          {config.showUnlockForm || config.isUpdateMode ? (
            <button
              onClick={handleClose}
              className="flex-1! px-4! py-[11px]! bg-secondary! text-secondary-foreground! border! border-border! rounded-[10px]! text-[13px]! font-semibold! cursor-pointer! hover:bg-accent! hover:text-accent-foreground! transition-all! m-0!"
            >
              Cancel
            </button>
          ) : (
            <button
              onClick={handleNever}
              className="flex-1! px-4! py-[11px]! bg-secondary! text-secondary-foreground! border! border-border! rounded-[10px]! text-[13px]! font-semibold! cursor-pointer! hover:bg-accent! hover:text-accent-foreground! transition-all! m-0!"
            >
              Never for this site
            </button>
          )}
          <button
            onClick={handleAction}
            disabled={loading}
            className="flex-1! px-4! py-[11px]! bg-primary! border-none! text-primary-foreground! rounded-[10px]! text-[13px]! font-semibold! cursor-pointer! hover:opacity-90! hover:-translate-y-px! disabled:opacity-50! transition-all! flex! justify-center! items-center! m-0!"
          >
            {loading ? (
              <span className="w-4! h-4! border-2! border-white/20! border-t-white! rounded-full! mr-1.5! animate-[vk-spin_.6s_linear_infinite]" />
            ) : null}
            {config.showUnlockForm
              ? config.unlockContext === "fill"
                ? "Unlock & Fill"
                : "Unlock & Save"
              : config.isUpdateMode
                ? "Update Password"
                : "Save Password"}
          </button>
        </div>
      </div>
    </div>
  );
};
