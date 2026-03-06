import React from "react";

interface LoginProps {
  password: string;
  setPassword: (val: string) => void;
  handleUnlock: () => void;
  isLoading: boolean;
  error: string;
}

export const Login: React.FC<LoginProps> = ({
  password,
  setPassword,
  handleUnlock,
  isLoading,
  error,
}) => {
  return (
    <div className="w-full h-[480px] flex flex-col items-center justify-center text-foreground px-6 relative overflow-hidden">
      <div className="absolute top-[-150px] left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-primary/20 blur-[100px] rounded-full pointer-events-none" />

      <div className="w-full max-w-[320px] backdrop-blur-xl p-8 flex flex-col items-center relative z-10">
        <div className="w-16 h-16 rounded-2xl bg-card/50 border flex items-center justify-center shadow-lg shadow-primary/20 mb-6">
          <svg
            width="28"
            height="28"
            viewBox="0 0 24 24"
            fill="none"
            stroke="white"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
            <path d="M7 11V7a5 5 0 0 1 10 0v4" />
          </svg>
        </div>

        <h2 className="text-2xl font-bold mb-1 tracking-tight text-foreground">
          VaultKeeper
        </h2>
        <p className="text-sm text-muted-foreground mb-8 text-center font-medium">
          Enter your master password to access your secure vault.
        </p>

        <div className="w-full space-y-4">
          <div className="relative">
            <input
              type="password"
              placeholder="Master Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleUnlock()}
              autoFocus
              className="w-full h-11 px-4 bg-background/50 text-foreground border border-border/60 rounded-xl outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all text-[15px] placeholder:text-muted-foreground"
            />
          </div>

          <button
            onClick={handleUnlock}
            disabled={isLoading}
            className="w-full h-11 bg-primary text-primary-foreground border-none rounded-xl text-[15px] font-semibold cursor-pointer hover:opacity-90 active:scale-[0.98] transition-all shadow-md shadow-primary/20 disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100 flex items-center justify-center"
          >
            {isLoading ? (
              <svg
                className="animate-spin h-5 w-5 text-current"
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
              "Unlock Vault"
            )}
          </button>
        </div>

        {error && (
          <div className="mt-4 px-4 py-2 bg-destructive/10 border border-destructive/20 rounded-lg w-full flex items-center justify-center gap-2">
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="var(--destructive)"
              strokeWidth="2"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <span className="text-destructive text-[13px] font-medium">
              {error}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
