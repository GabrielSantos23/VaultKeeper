import React, { useState, useEffect } from "react";
import browser from "webextension-polyfill";
import { Login } from "./components/Login";
import { UnlockedVault } from "./components/UnlockedVault";
export default function Popup() {
  const [status, setStatus] = useState<string>("checking");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    checkStatus();
  }, []);

  const checkStatus = async () => {
    try {
      const response: any = await browser.runtime.sendMessage({
        action: "status",
      });
      if (!response || !response.success) {
        setStatus("disconnected");
        return;
      }
      if (response.first_run) {
        setStatus("setup");
        return;
      }
      if (response.unlocked) {
        setStatus("unlocked");
      } else {
        setStatus("locked");
      }
    } catch (err) {
      setStatus("disconnected");
    }
  };

  const handleUnlock = async () => {
    if (!password) {
      setError("Enter your master password");
      return;
    }

    setIsLoading(true);
    setError("");

    try {
      const response: any = await browser.runtime.sendMessage({
        action: "unlock",
        password,
      });
      if (response && response.success) {
        setPassword("");
        setStatus("unlocked");
      } else {
        setError(response?.error || "Incorrect password");
      }
    } catch (err) {
      setError("Connection error");
    } finally {
      setIsLoading(false);
    }
  };

  if (status === "checking") {
    return (
      <div className="w-full h-[480px] flex flex-col items-center justify-center gap-4 text-muted-foreground bg-background">
        <div className="w-8 h-8 border-[3px] border-muted border-t-primary rounded-full animate-spin-slow"></div>
        <p>Connecting...</p>
      </div>
    );
  }

  if (status === "disconnected") {
    return (
      <div className="w-full h-[480px] flex items-center justify-center bg-background text-foreground">
        <div className="text-center">
          <div className="text-[40px] mb-3">⚠️</div>
          <h3 className="text-lg font-semibold mb-2">Connection Failed</h3>
          <p className="text-muted-foreground mb-4">
            Could not connect to VaultKeeper app
          </p>
          <button
            onClick={checkStatus}
            className="bg-secondary text-secondary-foreground border border-border px-5 py-2.5 rounded-md text-[13px] font-medium cursor-pointer hover:bg-muted active:bg-border transition-all"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (status === "setup") {
    return (
      <div className="w-full h-[480px] flex flex-col items-center justify-center bg-background text-foreground px-10">
        <div className="w-16 h-16 rounded-lg bg-primary/10 text-primary flex items-center justify-center mb-6">
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            <path d="M12 8v4" />
            <path d="M12 16h.01" />
          </svg>
        </div>
        <h2 className="text-2xl font-bold text-center mb-2">
          Welcome to VaultKeeper
        </h2>
        <p className="text-center text-muted-foreground mb-10 max-w-[400px]">
          Your secure vault is almost ready. Open the VaultKeeper Desktop App to
          complete setup.
        </p>
        <button
          onClick={checkStatus}
          className="bg-primary text-primary-foreground border-none px-6 py-2.5 rounded-md text-sm font-medium cursor-pointer hover:opacity-90 active:opacity-100 transition-all"
        >
          Check Again
        </button>
      </div>
    );
  }

  if (status === "unlocked") {
    return <UnlockedVault />;
  }

  return (
    <Login
      password={password}
      setPassword={setPassword}
      handleUnlock={handleUnlock}
      isLoading={isLoading}
      error={error}
    />
  );
}
