import { useState, useEffect } from "react";
import { useVaultStore } from "../stores/vaultStore";
import { writeText } from "@tauri-apps/plugin-clipboard-manager";
import { invoke } from "@tauri-apps/api/core";
import { EditDialogs } from "./dialogs/EditDialogs";
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
import {
  Copy01Icon,
  Link01Icon,
  Edit02Icon,
  Delete02Icon,
  StarIcon,
  ViewIcon,
  ViewOffSlashIcon,
  Globe02Icon,
  File02Icon,
  CreditCardIcon,
  Clock01Icon,
  FolderIcon,
  LockPasswordIcon,
  ShieldKeyIcon,
  ShieldUserIcon,
  Time04Icon,
  CheckmarkCircle01Icon,
} from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";

interface TotpResponse {
  success: boolean;
  data?: { code: string; remaining_seconds: number };
  error?: string;
}

export function DetailPanel() {
  const [showPassword, setShowPassword] = useState(false);
  const [showCardNumber, setShowCardNumber] = useState(false);
  const [showCVV, setShowCVV] = useState(false);
  const [showBackupCodes, setShowBackupCodes] = useState(false);
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [totpCode, setTotpCode] = useState<string>("");
  const [totpRemaining, setTotpRemaining] = useState<number>(0);
  const [isGeneratingTotp, setIsGeneratingTotp] = useState(false);

  const selectedItem = useVaultStore((state) => state.selectedItem);
  const folders = useVaultStore((state) => state.folders);
  const deleteCredential = useVaultStore((state) => state.deleteCredential);
  const deleteSecureNote = useVaultStore((state) => state.deleteSecureNote);
  const deleteCreditCard = useVaultStore((state) => state.deleteCreditCard);
  const updateCredential = useVaultStore((state) => state.updateCredential);
  const updateSecureNote = useVaultStore((state) => state.updateSecureNote);
  const updateCreditCard = useVaultStore((state) => state.updateCreditCard);

  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [itemToDelete, setItemToDelete] = useState<typeof selectedItem>(null);

  useEffect(() => {
    if (selectedItem && "domain" in selectedItem && selectedItem.totp_secret) {
      generateTotpCode(selectedItem.totp_secret);
    } else {
      setTotpCode("");
      setTotpRemaining(0);
    }
  }, [selectedItem]);

  useEffect(() => {
    if (!totpCode || totpRemaining === 0) return;
    const interval = setInterval(() => {
      setTotpRemaining((prev) => {
        if (prev <= 1) {
          if (
            selectedItem &&
            "domain" in selectedItem &&
            selectedItem.totp_secret
          ) {
            generateTotpCode(selectedItem.totp_secret);
          }
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [totpCode, totpRemaining, selectedItem]);

  const generateTotpCode = async (secret: string) => {
    if (isGeneratingTotp) return;
    setIsGeneratingTotp(true);
    try {
      const response = await invoke<TotpResponse>("generate_totp_code", {
        secret,
      });
      if (response.success && response.data) {
        setTotpCode(response.data.code);
        setTotpRemaining(response.data.remaining_seconds);
      }
    } catch (error) {
      console.error("Failed to generate TOTP:", error);
    } finally {
      setIsGeneratingTotp(false);
    }
  };

  const handleCopy = async (text: string, field: string) => {
    try {
      await writeText(text);
      setCopiedField(field);
      setTimeout(() => setCopiedField(null), 2000);
    } catch (error) {
      console.error("Failed to copy:", error);
    }
  };

  const handleFavorite = async () => {
    if (!selectedItem) return;

    const newFavorite = !selectedItem.favorite;

    if ("domain" in selectedItem) {
      await updateCredential(selectedItem.id, { favorite: newFavorite });
    } else if ("content" in selectedItem) {
      await updateSecureNote(selectedItem.id, { favorite: newFavorite });
    } else if ("card_number" in selectedItem) {
      await updateCreditCard(selectedItem.id, { favorite: newFavorite });
    }
  };

  const openDeleteDialog = () => {
    if (!selectedItem) return;
    setItemToDelete(selectedItem);
    setIsDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!itemToDelete) return;

    if ("domain" in itemToDelete) {
      await deleteCredential(itemToDelete.id);
    } else if ("content" in itemToDelete) {
      await deleteSecureNote(itemToDelete.id);
    } else if ("card_number" in itemToDelete) {
      await deleteCreditCard(itemToDelete.id);
    }

    setIsDeleteDialogOpen(false);
    setItemToDelete(null);
  };

  if (!selectedItem) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-4 bg-background">
        <div className="w-16 h-16 rounded-2xl flex items-center justify-center bg-muted">
          <HugeiconsIcon
            icon={LockPasswordIcon}
            size={28}
            className="text-muted-foreground/40"
          />
        </div>
        <div className="text-center">
          <p className="text-sm font-medium mb-1 text-foreground">
            No item selected
          </p>
          <p className="text-xs text-muted-foreground">
            Choose an item from the list to view its details
          </p>
        </div>
      </div>
    );
  }

  const isCredential = "domain" in selectedItem;
  const isNote = "content" in selectedItem;
  const isCard = "card_number" in selectedItem;
  const folder = selectedItem.folder_id
    ? folders.find((f) => f.id === selectedItem.folder_id)
    : null;

  const typeConfig = isCredential
    ? { icon: Globe02Icon, color: "var(--chart-1)" }
    : isNote
      ? { icon: File02Icon, color: "var(--chart-2)" }
      : { icon: CreditCardIcon, color: "var(--chart-4)" };

  const title = isCredential ? selectedItem.domain : selectedItem.title;
  const totpExpiring = totpRemaining <= 5;

  return (
    <div className="flex-1 h-full flex flex-col overflow-hidden bg-background">
      <div className="px-6 py-4 shrink-0 border-b border-border">
        <div className="flex items-center gap-4">
          <div
            className="w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0"
            style={{
              backgroundColor: `color-mix(in oklch, ${typeConfig.color} 12%, transparent)`,
            }}
          >
            <HugeiconsIcon
              icon={typeConfig.icon}
              size={20}
              style={{ color: typeConfig.color }}
            />
          </div>

          <div className="flex-1 min-w-0">
            <h1 className="text-base font-semibold truncate text-foreground">
              {title}
            </h1>
            <div className="flex items-center gap-3 mt-0.5">
              {isCredential && (
                <span className="text-xs truncate text-muted-foreground">
                  {selectedItem.username}
                </span>
              )}
              {folder && (
                <div className="flex items-center gap-1">
                  <HugeiconsIcon
                    icon={FolderIcon}
                    size={11}
                    className="text-muted-foreground/60"
                  />
                  <span className="text-xs text-muted-foreground/60">
                    {folder.name}
                  </span>
                </div>
              )}
            </div>
          </div>

          <div className="flex items-center gap-0.5 flex-shrink-0">
            <ActionButton
              icon={StarIcon}
              tooltip={
                selectedItem.favorite
                  ? "Remove from Favorites"
                  : "Add to Favorites"
              }
              onClick={handleFavorite}
              active={selectedItem.favorite}
              activeColor="var(--chart-5)"
            />
            <ActionButton
              icon={Edit02Icon}
              tooltip="Edit"
              onClick={() => setIsEditDialogOpen(true)}
            />
            <ActionButton
              icon={Delete02Icon}
              tooltip="Delete"
              onClick={openDeleteDialog}
              danger
            />
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-5 space-y-4 pb-20">
        {isCredential && (
          <>
            <Field label="Username">
              <FieldRow
                value={selectedItem.username}
                onCopy={() => handleCopy(selectedItem.username, "username")}
                copied={copiedField === "username"}
              />
            </Field>

            <Field label="Password">
              <FieldRow
                value={selectedItem.password}
                masked={!showPassword}
                maskChar="•"
                onToggleVisibility={() => setShowPassword((v) => !v)}
                isVisible={showPassword}
                onCopy={() => handleCopy(selectedItem.password, "password")}
                copied={copiedField === "password"}
                mono
              />
            </Field>

            {selectedItem.totp_secret && (
              <Field label="Two-Factor Code" icon={ShieldUserIcon}>
                <div className="rounded-lg border border-border overflow-hidden">
                  <div className="flex items-center gap-3 px-4 py-3 bg-muted">
                    <span className="flex-1 text-xl font-mono font-semibold tracking-[0.25em] text-foreground">
                      {totpCode
                        ? `${totpCode.slice(0, 3)} ${totpCode.slice(3)}`
                        : "--- ---"}
                    </span>
                    <div
                      className={`flex items-center gap-1.5 text-xs tabular-nums ${totpExpiring ? "text-destructive" : "text-muted-foreground"}`}
                    >
                      <HugeiconsIcon icon={Time04Icon} size={13} />
                      {totpRemaining}s
                    </div>
                    <CopyButton
                      onCopy={() => totpCode && handleCopy(totpCode, "totp")}
                      copied={copiedField === "totp"}
                      disabled={!totpCode}
                    />
                  </div>
                  <div className="h-0.5 bg-border">
                    <div
                      className={`h-full transition-all duration-1000 ${totpExpiring ? "bg-destructive" : "bg-primary"}`}
                      style={{ width: `${(totpRemaining / 30) * 100}%` }}
                    />
                  </div>
                </div>
              </Field>
            )}

            <Field label="Website">
              <a
                href={`https://${selectedItem.domain}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-sm text-primary hover:opacity-75 transition-opacity"
              >
                <HugeiconsIcon icon={Link01Icon} size={14} />
                {selectedItem.domain}
              </a>
            </Field>

            {selectedItem.notes && (
              <Field label="Notes">
                <div className="text-sm rounded-lg px-4 py-3 whitespace-pre-wrap leading-relaxed bg-muted text-foreground border border-border">
                  {selectedItem.notes}
                </div>
              </Field>
            )}

            {selectedItem.backup_codes && (
              <Field label="Backup Codes" icon={ShieldKeyIcon}>
                <div className="rounded-lg px-4 py-3 bg-muted border border-border">
                  <button
                    onClick={() => setShowBackupCodes((v) => !v)}
                    className="flex items-center gap-2 text-sm font-medium mb-2 text-muted-foreground hover:text-foreground transition-colors"
                  >
                    <HugeiconsIcon
                      icon={showBackupCodes ? ViewOffSlashIcon : ViewIcon}
                      size={14}
                    />
                    {showBackupCodes ? "Hide" : "Reveal"} backup codes
                  </button>
                  {showBackupCodes && (
                    <pre className="text-xs font-mono whitespace-pre-wrap text-foreground">
                      {selectedItem.backup_codes}
                    </pre>
                  )}
                </div>
              </Field>
            )}
          </>
        )}

        {isNote && (
          <Field label="Content">
            <div className="text-sm rounded-lg px-4 py-4 whitespace-pre-wrap leading-relaxed min-h-[120px] bg-muted text-foreground border border-border">
              {selectedItem.content}
            </div>
          </Field>
        )}

        {isCard && (
          <>
            <Field label="Card Number">
              <FieldRow
                value={selectedItem.card_number}
                masked={!showCardNumber}
                maskValue={`•••• •••• •••• ${selectedItem.card_number.slice(-4)}`}
                onToggleVisibility={() => setShowCardNumber((v) => !v)}
                isVisible={showCardNumber}
                onCopy={() =>
                  handleCopy(selectedItem.card_number, "card_number")
                }
                copied={copiedField === "card_number"}
                mono
              />
            </Field>

            <Field label="Cardholder">
              <FieldRow value={selectedItem.cardholder_name} />
            </Field>

            <div className="grid grid-cols-2 gap-4">
              <Field label="Expiry Date">
                <FieldRow value={selectedItem.expiry_date} />
              </Field>
              <Field label="CVV">
                <FieldRow
                  value={selectedItem.cvv}
                  masked={!showCVV}
                  maskValue="•••"
                  onToggleVisibility={() => setShowCVV((v) => !v)}
                  isVisible={showCVV}
                  onCopy={() => handleCopy(selectedItem.cvv, "cvv")}
                  copied={copiedField === "cvv"}
                  mono
                />
              </Field>
            </div>
          </>
        )}

        <div className="pt-4 mt-2 flex items-center gap-5 border-t border-border">
          {[
            {
              label: "Created",
              value: new Date(selectedItem.created_at).toLocaleDateString(),
            },
            {
              label: "Updated",
              value: new Date(selectedItem.updated_at).toLocaleDateString(),
            },
          ].map(({ label, value }) => (
            <div key={label} className="flex items-center gap-1.5">
              <HugeiconsIcon
                icon={Clock01Icon}
                size={13}
                className="text-muted-foreground/50"
              />
              <span className="text-xs text-muted-foreground">
                {label}: <span className="text-foreground">{value}</span>
              </span>
            </div>
          ))}
        </div>
      </div>

      <EditDialogs
        open={isEditDialogOpen}
        onOpenChange={setIsEditDialogOpen}
        item={selectedItem}
      />

      <AlertDialog
        open={isDeleteDialogOpen}
        onOpenChange={setIsDeleteDialogOpen}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Item</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this item? This action cannot be
              undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setItemToDelete(null)}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConfirm}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

function Field({
  label,
  icon,
  children,
}: {
  label: string;
  icon?: React.ComponentType<any>;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-center gap-1.5">
        {icon && (
          <HugeiconsIcon
            icon={icon}
            size={13}
            className="text-muted-foreground"
          />
        )}
        <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
          {label}
        </span>
      </div>
      {children}
    </div>
  );
}

function FieldRow({
  value,
  masked = false,
  maskChar = "•",
  maskValue,
  isVisible,
  onToggleVisibility,
  onCopy,
  copied,
  mono = false,
  disabled = false,
}: {
  value: string;
  masked?: boolean;
  maskChar?: string;
  maskValue?: string;
  isVisible?: boolean;
  onToggleVisibility?: () => void;
  onCopy?: () => void;
  copied?: boolean;
  mono?: boolean;
  disabled?: boolean;
}) {
  const display = masked
    ? (maskValue ?? maskChar.repeat(Math.min(value.length, 12)))
    : value;

  return (
    <div className="flex items-center gap-2 px-3 py-2.5 rounded-lg bg-muted border border-border">
      <span
        className={`flex-1 text-sm truncate text-foreground ${mono ? "font-mono" : ""}`}
      >
        {display}
      </span>
      {onToggleVisibility && (
        <button
          onClick={onToggleVisibility}
          className="flex-shrink-0 p-1 rounded transition-colors text-muted-foreground hover:text-foreground"
        >
          <HugeiconsIcon
            icon={isVisible ? ViewOffSlashIcon : ViewIcon}
            size={15}
          />
        </button>
      )}
      {onCopy && (
        <CopyButton onCopy={onCopy} copied={!!copied} disabled={disabled} />
      )}
    </div>
  );
}

function CopyButton({
  onCopy,
  copied,
  disabled = false,
}: {
  onCopy: () => void;
  copied: boolean;
  disabled?: boolean;
}) {
  return (
    <button
      onClick={onCopy}
      disabled={disabled}
      className={`flex-shrink-0 p-1 rounded transition-colors disabled:opacity-40 ${copied ? "text-primary" : "text-muted-foreground hover:text-primary"}`}
    >
      <HugeiconsIcon
        icon={copied ? CheckmarkCircle01Icon : Copy01Icon}
        size={15}
      />
    </button>
  );
}

function ActionButton({
  icon,
  tooltip,
  onClick,
  danger = false,
  active = false,
  activeColor,
}: {
  icon: React.ComponentType<any>;
  tooltip: string;
  onClick?: () => void;
  danger?: boolean;
  active?: boolean;
  activeColor?: string;
}) {
  return (
    <button
      title={tooltip}
      onClick={onClick}
      className={`w-8 h-8 flex items-center justify-center rounded-lg transition-colors ${
        danger
          ? "text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
          : "text-muted-foreground hover:bg-muted hover:text-foreground"
      }`}
      style={active && activeColor ? { color: activeColor } : undefined}
    >
      <HugeiconsIcon
        icon={icon}
        size={16}
        style={active && activeColor ? { fill: activeColor } : undefined}
      />
    </button>
  );
}
