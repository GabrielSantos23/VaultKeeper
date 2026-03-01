import { useState } from "react";
import { useAuthStore } from "../stores/authStore";
import { useVaultStore } from "../stores/vaultStore";
import {
  CreditCardIcon,
  Home03Icon,
  StarIcon,
  Key01Icon,
  File02Icon,
  ResetPasswordIcon,
  Settings02Icon,
  PlusSignIcon,
  FolderIcon,
  Logout01Icon,
  FlashIcon,
  ArrowRight01Icon,
  Delete02Icon,
} from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";
import {
  AddCredentialDialog,
  AddSecureNoteDialog,
  AddCreditCardDialog,
  AddFolderDialog,
} from "./dialogs";

import {
  Sidebar as ShadcnSidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
  SidebarTrigger,
  useSidebar,
} from "@/components/ui/sidebar";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

interface SidebarProps {
  activeView:
    | "vault"
    | "notes"
    | "cards"
    | "generator"
    | "security"
    | "settings";
  onViewChange: (
    view: "vault" | "notes" | "cards" | "generator" | "security" | "settings",
  ) => void;
}

export function Sidebar({ activeView, onViewChange }: SidebarProps) {
  const { state } = useSidebar();
  const isCollapsed = state === "collapsed";

  const [popoverOpen, setPopoverOpen] = useState(false);
  const [showAddCredential, setShowAddCredential] = useState(false);
  const [showAddNote, setShowAddNote] = useState(false);
  const [showAddCard, setShowAddCard] = useState(false);
  const [showAddFolder, setShowAddFolder] = useState(false);
  const [folderToDelete, setFolderToDelete] = useState<{
    id: number;
    name: string;
  } | null>(null);

  const logout = useAuthStore((state) => state.logout);
  const folders = useVaultStore((state) => state.folders);
  const deleteFolder = useVaultStore((state) => state.deleteFolder);
  const selectedCategory = useVaultStore((state) => state.selectedCategory);
  const setSelectedCategory = useVaultStore(
    (state) => state.setSelectedCategory,
  );

  const handleCategoryClick = (category: string, view?: "notes" | "cards") => {
    setSelectedCategory(category);
    if (view) {
      onViewChange(view);
    } else {
      onViewChange("vault");
    }
  };

  const credentialsCount = useVaultStore((state) => state.credentials.length);
  const notesCount = useVaultStore((state) => state.secureNotes.length);
  const cardsCount = useVaultStore((state) => state.creditCards.length);
  const favoritesCount = useVaultStore(
    (state) =>
      state.credentials.filter((c) => c.favorite).length +
      state.secureNotes.filter((n) => n.favorite).length +
      state.creditCards.filter((c) => c.favorite).length,
  );

  const categoryItems = [
    {
      id: "all",
      label: "All Items",
      icon: Home03Icon,
      count: credentialsCount + notesCount + cardsCount,
    },
    {
      id: "favorites",
      label: "Favorites",
      icon: StarIcon,
      count: favoritesCount,
    },
    {
      id: "credentials",
      label: "Passwords",
      icon: Key01Icon,
      count: credentialsCount,
    },
    {
      id: "notes",
      label: "Secure Notes",
      icon: File02Icon,
      count: notesCount,
      view: "notes" as const,
    },
    {
      id: "cards",
      label: "Credit Cards",
      icon: CreditCardIcon,
      count: cardsCount,
      view: "cards" as const,
    },
  ];

  const isItemActive = (item: (typeof categoryItems)[0]) =>
    (selectedCategory === item.id && activeView === "vault") ||
    (item.view === "notes" && activeView === "notes") ||
    (item.view === "cards" && activeView === "cards");

  const openDialog = (setter: (v: boolean) => void) => {
    setPopoverOpen(false);
    setter(true);
  };

  const addMenuItems = [
    {
      icon: Key01Icon,
      label: "Password",
      description: "Login credentials",
      action: () => openDialog(setShowAddCredential),
    },
    {
      icon: File02Icon,
      label: "Secure Note",
      description: "Encrypted text",
      action: () => openDialog(setShowAddNote),
    },
    {
      icon: CreditCardIcon,
      label: "Credit Card",
      description: "Card details",
      action: () => openDialog(setShowAddCard),
    },
    {
      icon: FolderIcon,
      label: "Folder",
      description: "Organize items",
      action: () => openDialog(setShowAddFolder),
    },
  ];

  const handleConfirmDelete = () => {
    if (folderToDelete) {
      deleteFolder(folderToDelete.id);
      // If we were viewing this folder, go back to all items
      if (selectedCategory === `folder_${folderToDelete.id}`) {
        setSelectedCategory("all");
        onViewChange("vault");
      }
      setFolderToDelete(null);
    }
  };

  return (
    <>
      <ShadcnSidebar collapsible="icon">
        <SidebarHeader className="py-4">
          <SidebarMenu>
            <div
              className={`flex px-2 transition-all ${
                isCollapsed
                  ? "flex-col items-center gap-4"
                  : "flex-row items-center gap-2"
              }`}
            >
              {/* New Item Button & Popover */}
              <SidebarMenuItem
                className={
                  isCollapsed ? "flex justify-center w-full" : "flex-1"
                }
              >
                <Popover
                  open={popoverOpen}
                  onOpenChange={(open) => setPopoverOpen(open)}
                >
                  <PopoverTrigger asChild>
                    <div
                      className={`
                        flex items-center justify-center rounded-md bg-primary/10 text-primary
                        hover:bg-primary/20 transition-all font-medium cursor-pointer
                        ${isCollapsed ? "size-9" : "w-full gap-2 px-3 py-2"}
                      `}
                    >
                      <HugeiconsIcon icon={PlusSignIcon} size={16} />
                      {!isCollapsed && <span>New item</span>}
                    </div>
                  </PopoverTrigger>

                  {/* Popover Content */}
                  <PopoverContent
                    side={isCollapsed ? "right" : "bottom"}
                    align={isCollapsed ? "start" : "center"}
                    className="z-[9999] w-52 p-1.5 rounded-xl bg-muted border shadow-xl"
                    sideOffset={isCollapsed ? 12 : 4}
                  >
                    {addMenuItems.map(
                      ({ icon, label, description, action }) => (
                        <button
                          key={label}
                          onClick={action}
                          className="w-full flex items-center gap-3 px-2.5 py-2 rounded-lg hover:bg-sidebar-accent/50 text-left transition-colors"
                        >
                          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-accent text-primary">
                            <HugeiconsIcon icon={icon} size={15} />
                          </div>
                          <div className="flex flex-col min-w-0">
                            <span className="text-sm font-medium leading-none mb-0.5">
                              {label}
                            </span>
                            <span className="text-xs text-muted-foreground">
                              {description}
                            </span>
                          </div>
                        </button>
                      ),
                    )}
                  </PopoverContent>
                </Popover>
              </SidebarMenuItem>

              {/* Toggle button */}
              <SidebarMenuItem
                className={`flex ${isCollapsed ? "justify-center w-full" : ""}`}
              >
                <SidebarTrigger className="text-muted-foreground" />
              </SidebarMenuItem>
            </div>
          </SidebarMenu>
        </SidebarHeader>

        <SidebarContent>
          <Collapsible defaultOpen className="group/collapsible">
            <SidebarGroup>
              <SidebarGroupLabel asChild>
                <CollapsibleTrigger className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Main Menu
                  <HugeiconsIcon
                    icon={ArrowRight01Icon}
                    size={14}
                    className="ml-auto transition-transform group-data-[state=open]/collapsible:rotate-90"
                  />
                </CollapsibleTrigger>
              </SidebarGroupLabel>
              <CollapsibleContent>
                <SidebarGroupContent>
                  <SidebarMenu>
                    {categoryItems.map((item) => {
                      const active = isItemActive(item);
                      return (
                        <SidebarMenuItem key={item.id}>
                          <SidebarMenuButton
                            isActive={active}
                            tooltip={item.label}
                            onClick={() =>
                              handleCategoryClick(item.id, item.view)
                            }
                            className="data-[active=true]:bg-sidebar-accent/50 data-[active=true]:text-primary hover:bg-sidebar-accent/50 hover:text-primary"
                          >
                            <HugeiconsIcon
                              icon={item.icon}
                              size={16}
                              variant={active ? "solid" : "stroke"}
                              className={active ? "fill-current" : ""}
                            />
                            <span>{item.label}</span>
                            {item.count !== undefined && !isCollapsed && (
                              <span
                                className={`ml-auto text-xs tabular-nums opacity-75 ${active ? "text-primary" : "text-muted-foreground"}`}
                              >
                                {item.count}
                              </span>
                            )}
                          </SidebarMenuButton>
                        </SidebarMenuItem>
                      );
                    })}
                  </SidebarMenu>
                </SidebarGroupContent>
              </CollapsibleContent>
            </SidebarGroup>
          </Collapsible>

          <Collapsible defaultOpen className="group/collapsible">
            <SidebarGroup>
              <SidebarGroupLabel asChild>
                <CollapsibleTrigger className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Folders
                  <HugeiconsIcon
                    icon={ArrowRight01Icon}
                    size={14}
                    className="ml-auto transition-transform group-data-[state=open]/collapsible:rotate-90"
                  />
                </CollapsibleTrigger>
              </SidebarGroupLabel>
              <CollapsibleContent>
                <SidebarGroupContent>
                  <SidebarMenu>
                    {folders.map((folder) => {
                      const active =
                        selectedCategory === `folder_${folder.id}` &&
                        activeView === "vault";
                      return (
                        <SidebarMenuItem key={folder.id}>
                          <SidebarMenuButton
                            isActive={active}
                            tooltip={folder.name}
                            onClick={() =>
                              handleCategoryClick(`folder_${folder.id}`)
                            }
                            className="group/folder data-[active=true]:bg-sidebar-accent/50 data-[active=true]:text-primary hover:bg-sidebar-accent/50 hover:text-primary"
                          >
                            <HugeiconsIcon
                              icon={FolderIcon}
                              size={16}
                              variant={active ? "solid" : "stroke"}
                              className={active ? "fill-current" : ""}
                            />
                            <span className="flex-1 truncate">
                              {folder.name}
                            </span>
                            {/* Trash icon — only visible on hover */}
                            <span
                              role="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                setFolderToDelete({
                                  id: folder.id,
                                  name: folder.name,
                                });
                              }}
                              className="opacity-0 group-hover/folder:opacity-100 transition-opacity p-0.5 rounded hover:text-destructive"
                            >
                              <HugeiconsIcon icon={Delete02Icon} size={14} />
                            </span>
                          </SidebarMenuButton>
                        </SidebarMenuItem>
                      );
                    })}
                  </SidebarMenu>
                </SidebarGroupContent>
              </CollapsibleContent>
            </SidebarGroup>
          </Collapsible>

          <SidebarGroup>
            <SidebarGroupLabel className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Tools
            </SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {[
                  {
                    view: "generator" as const,
                    icon: FlashIcon,
                    label: "Password Generator",
                  },
                  {
                    view: "security" as const,
                    icon: ResetPasswordIcon,
                    label: "Security Audit",
                  },
                ].map(({ view, icon, label }) => (
                  <SidebarMenuItem key={view}>
                    <SidebarMenuButton
                      isActive={activeView === view}
                      tooltip={label}
                      onClick={() => onViewChange(view)}
                      className="data-[active=true]:bg-sidebar-accent/50 data-[active=true]:text-primary hover:bg-sidebar-accent/50 hover:text-primary"
                    >
                      <HugeiconsIcon
                        icon={icon}
                        size={16}
                        variant={activeView === view ? "solid" : "stroke"}
                        className={activeView === view ? "fill-current" : ""}
                      />
                      <span>{label}</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>

          <SidebarGroup>
            <SidebarGroupLabel className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Settings
            </SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                <SidebarMenuItem>
                  <SidebarMenuButton
                    isActive={activeView === "settings"}
                    tooltip="Settings"
                    onClick={() => onViewChange("settings")}
                    className="data-[active=true]:bg-sidebar-accent/50 data-[active=true]:text-primary hover:bg-sidebar-accent/50 hover:text-primary"
                  >
                    <HugeiconsIcon
                      icon={Settings02Icon}
                      size={16}
                      variant={activeView === "settings" ? "solid" : "stroke"}
                      className={
                        activeView === "settings" ? "fill-current" : ""
                      }
                    />
                    <span>Settings</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        </SidebarContent>

        <SidebarFooter className="border-t border-muted-foreground/10">
          <SidebarMenu>
            <SidebarMenuItem className="pt-2.5">
              <SidebarMenuButton
                onClick={logout}
                tooltip="Lock Vault"
                className="text-muted-foreground hover:bg-destructive/15 hover:text-destructive transition-colors"
              >
                <HugeiconsIcon icon={Logout01Icon} size={16} />
                <span>Lock Vault</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarFooter>

        <SidebarRail />
      </ShadcnSidebar>

      <AlertDialog
        open={!!folderToDelete}
        onOpenChange={(open) => !open && setFolderToDelete(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              Delete "{folderToDelete?.name}"?
            </AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete the folder. Items inside will not be
              deleted but will become unorganized.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete folder
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AddCredentialDialog
        open={showAddCredential}
        onOpenChange={setShowAddCredential}
      />
      <AddSecureNoteDialog open={showAddNote} onOpenChange={setShowAddNote} />
      <AddCreditCardDialog open={showAddCard} onOpenChange={setShowAddCard} />
      <AddFolderDialog open={showAddFolder} onOpenChange={setShowAddFolder} />
    </>
  );
}
