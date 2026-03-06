import React, { useState, useEffect } from "react";
import browser from "webextension-polyfill";
import { Sidebar, CredentialType } from "./Sidebar";
import { Details } from "./Details";
import { EditCredential } from "./EditCredential";

export const UnlockedVault: React.FC = () => {
  const [credentials, setCredentials] = useState<CredentialType[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    loadCredentials();
    const savedId = localStorage.getItem("vk_selectedId");
    const savedSearch = localStorage.getItem("vk_searchQuery");

    if (savedId) setSelectedId(savedId);
    if (savedSearch) setSearchQuery(savedSearch);
  }, []);

  useEffect(() => {
    if (selectedId !== null) localStorage.setItem("vk_selectedId", selectedId);
    if (searchQuery !== null)
      localStorage.setItem("vk_searchQuery", searchQuery);
  }, [selectedId, searchQuery]);

  const loadCredentials = async () => {
    try {
      const response: any = await browser.runtime.sendMessage({
        action: "get_all_credentials",
      });

      if (response && response.success) {
        setCredentials(response.credentials || []);
      }
    } catch (err) {
    } finally {
      setIsLoading(false);
    }
  };

  const lockVault = async () => {
    try {
      await browser.runtime.sendMessage({ action: "lock" });
      window.close();
    } catch (e) {}
  };

  const handleDelete = async (id: string) => {
    try {
      await browser.runtime.sendMessage({
        action: "delete_credentials",
        id,
      });
      setSelectedId(null);
      setIsEditing(false);
      await loadCredentials();
    } catch (e) {}
  };

  const selectedCredential = React.useMemo(() => {
    return credentials.find((c) => c.id === selectedId) || null;
  }, [credentials, selectedId]);

  return (
    <div className="w-full h-[480px] flex flex-col bg-background text-foreground overflow-hidden">
      <header className="flex items-center justify-between px-5 py-3 border-b border-border/50 bg-card/40 backdrop-blur-md z-30 shrink-0 shadow-[0_1px_2px_rgba(0,0,0,0.05)]">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-md bg-primary/10 border border-primary/20 flex items-center justify-center">
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="var(--primary)"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>
          </div>
          <h2 className="text-[15px] font-semibold tracking-tight">
            VaultKeeper
          </h2>
        </div>

        <button
          onClick={lockVault}
          className="text-muted-foreground hover:text-foreground hover:bg-muted p-1.5 rounded-lg transition-colors flex items-center gap-1.5"
          title="Lock Vault"
        >
          <span className="text-[12px] font-medium hidden sm:block">Lock</span>
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
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
            <path d="M7 11V7a5 5 0 0 1 9.9-1" />
          </svg>
        </button>
      </header>

      <div className="flex-1 flex overflow-hidden">
        <Sidebar
          credentials={credentials}
          isLoading={isLoading}
          selectedId={selectedId}
          onSelect={(c) => {
            setSelectedId(c.id);
            setIsEditing(false);
          }}
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
        />
        {isEditing && selectedCredential ? (
          <EditCredential
            credential={selectedCredential}
            onSave={() => {
              setIsEditing(false);
              loadCredentials();
            }}
            onCancel={() => setIsEditing(false)}
          />
        ) : (
          <Details
            credential={selectedCredential}
            onEdit={() => setIsEditing(true)}
            onDelete={handleDelete}
          />
        )}
      </div>
    </div>
  );
};
