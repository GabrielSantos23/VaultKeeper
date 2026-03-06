import React from "react";

export interface CredentialType {
  id: string;
  domain: string;
  username: string;
  password?: string;
  notes?: string;
  totp_secret?: string;
  backup_codes?: string;
}

interface SidebarProps {
  credentials: CredentialType[];
  isLoading: boolean;
  selectedId: string | null;
  onSelect: (cred: CredentialType) => void;
  searchQuery: string;
  setSearchQuery: (q: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  credentials,
  isLoading,
  selectedId,
  onSelect,
  searchQuery,
  setSearchQuery,
}) => {
  const getDomainDisplay = (domain: string) => {
    let display = domain.replace(/^(https?:\/\/)?(www\.)?/, "");
    display = display.split("/")[0];
    return display.charAt(0).toUpperCase() + display.slice(1);
  };

  const filtered = credentials.filter(
    (c) =>
      c.domain.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.username.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  return (
    <div className="w-[260px] h-full border-r border-border/40 bg-card/10 flex flex-col shrink-0 flex-none overflow-hidden">
      <div className="p-3 border-b border-border/20 shrink-0">
        <div className="relative">
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground w-3.5 h-3.5"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="11" cy="11" r="8"></circle>
            <path d="m21 21-4.35-4.35"></path>
          </svg>
          <input
            type="text"
            placeholder="Search vault..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full h-8 pl-9 pr-3 bg-background border border-border/50 rounded-lg outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all text-[13px] placeholder:text-muted-foreground"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-0.5 scrollbar-thin scrollbar-thumb-border/50 scrollbar-track-transparent">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center h-40 gap-3 text-muted-foreground">
            <div className="w-5 h-5 border-[2px] border-muted border-t-primary rounded-full animate-spin"></div>
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-40 text-muted-foreground opacity-60">
            <svg
              className="w-8 h-8 mb-2 opacity-50"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
            >
              <path d="M21 8v13H3V8" />
              <path d="M1 3h22v5H1z" />
              <path d="M10 12h4" />
            </svg>
            <p className="text-xs font-medium">No items found</p>
          </div>
        ) : (
          filtered.map((cred) => (
            <div
              key={cred.id}
              onClick={() => onSelect(cred)}
              className={`w-full flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-colors border ${
                selectedId === cred.id
                  ? "bg-primary/10 border-primary/20 text-foreground"
                  : "border-transparent text-muted-foreground hover:bg-muted/50 hover:text-foreground"
              }`}
            >
              <div className="w-8 h-8 rounded-md bg-card border border-border/50 flex items-center justify-center overflow-hidden shrink-0">
                <img
                  src={`https://www.google.com/s2/favicons?domain=${cred.domain}&sz=32`}
                  alt={cred.domain}
                  className="w-5 h-5 object-contain"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = "none";
                    (
                      e.target as HTMLImageElement
                    ).nextElementSibling?.classList.remove("hidden");
                  }}
                />
                <svg
                  className="w-4 h-4 text-muted-foreground hidden"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <circle cx="12" cy="12" r="10" />
                  <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                </svg>
              </div>
              <div className="flex-1 min-w-0">
                <p
                  className={`text-[13px] font-medium truncate ${
                    selectedId === cred.id ? "text-foreground" : ""
                  }`}
                >
                  {getDomainDisplay(cred.domain)}
                </p>
                <p className="text-[11px] opacity-70 truncate line-clamp-1">
                  {cred.username}
                </p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
