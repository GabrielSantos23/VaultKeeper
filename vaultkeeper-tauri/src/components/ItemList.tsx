import { useState, useMemo } from "react";
import { useVaultStore } from "../stores/vaultStore";
import {
  SearchIcon,
  Globe02Icon,
  File02Icon,
  CreditCardIcon,
  StarIcon,
  FolderIcon,
  LockIcon,
  Loading03Icon,
  LayoutGridIcon,
} from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";

export function ItemList() {
  const [searchQuery, setSearchQuery] = useState("");

  const credentials = useVaultStore((state) => state.credentials);
  const secureNotes = useVaultStore((state) => state.secureNotes);
  const creditCards = useVaultStore((state) => state.creditCards);
  const folders = useVaultStore((state) => state.folders);
  const selectedItem = useVaultStore((state) => state.selectedItem);
  const selectedCategory = useVaultStore((state) => state.selectedCategory);
  const setSelectedItem = useVaultStore((state) => state.setSelectedItem);
  const isLoading = useVaultStore((state) => state.isLoading);

  const filteredItems = useMemo(() => {
    let items: Array<{ type: string; data: any }> = [];

    switch (selectedCategory) {
      case "all":
        items = [
          ...credentials.map((c) => ({ type: "credential", data: c })),
          ...secureNotes.map((n) => ({ type: "note", data: n })),
          ...creditCards.map((c) => ({ type: "card", data: c })),
        ];
        break;
      case "credentials":
        items = credentials.map((c) => ({ type: "credential", data: c }));
        break;
      case "notes":
        items = secureNotes.map((n) => ({ type: "note", data: n }));
        break;
      case "cards":
        items = creditCards.map((c) => ({ type: "card", data: c }));
        break;
      case "favorites":
        items = [
          ...credentials
            .filter((c) => c.favorite)
            .map((c) => ({ type: "credential", data: c })),
          ...secureNotes
            .filter((n) => n.favorite)
            .map((n) => ({ type: "note", data: n })),
          ...creditCards
            .filter((c) => c.favorite)
            .map((c) => ({ type: "card", data: c })),
        ];
        break;
      default:
        if (selectedCategory.startsWith("folder_")) {
          const folderId = parseInt(selectedCategory.split("_")[1]);
          items = [
            ...credentials
              .filter((c) => c.folder_id === folderId)
              .map((c) => ({ type: "credential", data: c })),
            ...secureNotes
              .filter((n) => n.folder_id === folderId)
              .map((n) => ({ type: "note", data: n })),
          ];
        }
    }

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      items = items.filter((item) => {
        if (item.type === "credential")
          return (
            item.data.domain.toLowerCase().includes(query) ||
            item.data.username.toLowerCase().includes(query)
          );
        if (item.type === "note")
          return (
            item.data.title.toLowerCase().includes(query) ||
            item.data.content.toLowerCase().includes(query)
          );
        if (item.type === "card")
          return item.data.title.toLowerCase().includes(query);
        return false;
      });
    }

    return items;
  }, [credentials, secureNotes, creditCards, selectedCategory, searchQuery]);

  const getFaviconUrl = (domain: string) =>
    `https://www.google.com/s2/favicons?domain=${domain}&sz=64`;

  const getCategoryLabel = () => {
    if (selectedCategory === "all") return "All Items";
    if (selectedCategory === "favorites") return "Favorites";
    if (selectedCategory === "credentials") return "Passwords";
    if (selectedCategory === "notes") return "Secure Notes";
    if (selectedCategory === "cards") return "Credit Cards";
    if (selectedCategory.startsWith("folder_")) {
      const folderId = parseInt(selectedCategory.split("_")[1]);
      return folders.find((f) => f.id === folderId)?.name ?? "Folder";
    }
    return "Items";
  };

  const typeConfig = {
    credential: {
      bg: "color-mix(in oklch, var(--chart-1) 12%, transparent)",
      color: "var(--chart-1)",
      icon: Globe02Icon,
    },
    note: {
      bg: "color-mix(in oklch, var(--chart-2) 12%, transparent)",
      color: "var(--chart-2)",
      icon: File02Icon,
    },
    card: {
      bg: "color-mix(in oklch, var(--chart-4) 12%, transparent)",
      color: "var(--chart-4)",
      icon: CreditCardIcon,
    },
  };

  const getItemTitle = (item: { type: string; data: any }) => {
    if (item.type === "credential") return item.data.domain;
    if (item.type === "note") return item.data.title;
    if (item.type === "card") return item.data.title;
    return "Unknown";
  };

  const getItemSubtitle = (item: { type: string; data: any }) => {
    if (item.type === "credential") return item.data.username;
    if (item.type === "note") return item.data.content?.slice(0, 48) + "…";
    if (item.type === "card") return "•••• " + item.data.card_number?.slice(-4);
    return "";
  };

  /**
   * Selection logic:
   * Since IDs are not unique across tables, we determine type by object keys
   */
  const isSelected = (item: { type: string; data: any }) => {
    if (!selectedItem) return false;
    const idMatch = selectedItem.id === item.data.id;
    if (!idMatch) return false;

    let selectedType = "";
    if ('domain' in selectedItem) selectedType = "credential";
    else if ('card_number' in selectedItem) selectedType = "card";
    else if ('content' in selectedItem) selectedType = "note";

    return (('type' in selectedItem && selectedItem.type) || selectedType) === item.type;
  };

  return (
    <div className="w-80 h-full flex flex-col bg-background border-r border-border">
      <div className="px-4 pt-5 pb-3 border-b border-border">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-semibold text-foreground">
            {getCategoryLabel()}
          </h2>
          <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-muted-foreground/10 text-muted-foreground">
            {filteredItems.length}
          </span>
        </div>

        <div className="relative">
          <HugeiconsIcon
            icon={SearchIcon}
            size={15}
            className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none text-muted-foreground"
          />
          <input
            type="text"
            placeholder="Search…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-lg pl-9 pr-3 py-2 text-sm outline-none transition-colors bg-muted border border-border text-foreground focus:border-ring"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center h-full gap-3 text-muted-foreground">
            <HugeiconsIcon
              icon={Loading03Icon}
              size={28}
              className="animate-spin text-primary"
            />
            <p className="text-sm">Loading…</p>
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 gap-3 text-muted-foreground">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-muted">
              <HugeiconsIcon
                icon={LayoutGridIcon}
                size={22}
                className="opacity-50"
              />
            </div>
            <p className="text-sm">No items found</p>
          </div>
        ) : (
          <div className="p-2 space-y-0.5 pb-20">
            {filteredItems.map((item) => {
              const selected = isSelected(item);
              const cfg = typeConfig[item.type as keyof typeof typeConfig];
              const folder = folders.find((f) => f.id === item.data.folder_id);

              return (
                <button
                  key={`${item.type}-${item.data.id}`}
                  onClick={() =>
                    setSelectedItem({ ...item.data, type: item.type })
                  }
                  className={`
                    w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-all duration-150 border
                    ${
                      selected
                        ? "bg-muted border-primary/25"
                        : "border-transparent hover:bg-muted"
                    }
                  `}
                >
                  <div className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0 overflow-hidden bg-accent">
                    {item.type === "credential" ? (
                      <img
                        src={getFaviconUrl(item.data.domain)}
                        alt=""
                        className="w-5 h-5"
                        onError={(e) => {
                          e.currentTarget.style.display = "none";
                          e.currentTarget.nextElementSibling?.classList.remove(
                            "hidden",
                          );
                        }}
                      />
                    ) : null}
                    <HugeiconsIcon
                      icon={cfg?.icon ?? LockIcon}
                      size={16}
                      className={item.type === "credential" ? "hidden" : ""}
                      style={{ color: cfg?.color }}
                    />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 mb-0.5">
                      <span
                        className={`text-sm font-medium truncate ${selected ? "text-primary" : "text-foreground"}`}
                      >
                        {getItemTitle(item)}
                      </span>
                      {item.data.favorite && (
                        <HugeiconsIcon
                          icon={StarIcon}
                          size={12}
                          style={{
                            color: "var(--chart-5)",
                            fill: "var(--chart-5)",
                          }}
                          className="shrink-0"
                        />
                      )}
                    </div>
                    <p className="text-xs truncate text-muted-foreground">
                      {getItemSubtitle(item)}
                    </p>
                    {folder && (
                      <div className="flex items-center gap-1 mt-1 opacity-65">
                        <HugeiconsIcon
                          icon={FolderIcon}
                          size={11}
                          className="text-muted-foreground"
                        />
                        <span className="text-xs text-muted-foreground">
                          {folder.name}
                        </span>
                      </div>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
