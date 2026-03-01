import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useVaultStore } from "@/stores/vaultStore";
import {
  Key01Icon,
  Shield01Icon,
  File01Icon,
} from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";

interface AddCredentialDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AddCredentialDialog({
  open,
  onOpenChange,
}: AddCredentialDialogProps) {
  const [domain, setDomain] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [totpSecret, setTotpSecret] = useState("");
  const [backupCodes, setBackupCodes] = useState("");
  const [notes, setNotes] = useState("");
  const [folderId, setFolderId] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const addCredential = useVaultStore((state) => state.addCredential);
  const folders = useVaultStore((state) => state.folders);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!domain || !username || !password) return;

    setIsSubmitting(true);
    await addCredential({
      domain,
      username,
      password,
      totp_secret: totpSecret || undefined,
      backup_codes: backupCodes || undefined,
      notes: notes || undefined,
      folder_id: folderId ? parseInt(folderId) : undefined,
    });
    setIsSubmitting(false);

    setDomain("");
    setUsername("");
    setPassword("");
    setTotpSecret("");
    setBackupCodes("");
    setNotes("");
    setFolderId("");
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[640px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
              <HugeiconsIcon
                icon={Key01Icon}
                className="w-5 h-5 text-primary"
              />
            </div>
            <div>
              <DialogTitle>Add Password</DialogTitle>
              <DialogDescription>
                Add a new password to your vault
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-5 py-4">
          {/* Row 1: Domain */}
          <div className="space-y-1.5">
            <Label htmlFor="domain">Website / Domain</Label>
            <Input
              id="domain"
              placeholder="e.g., google.com"
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              required
            />
          </div>

          {/* Row 2: Username + Password side by side */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="username">Username / Email</Label>
              <Input
                id="username"
                placeholder="user@example.com"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="Enter password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
          </div>

          {/* Row 3: 2FA Secret + Folder side by side */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="totpSecret" className="flex items-center gap-1.5">
                <HugeiconsIcon
                  icon={Shield01Icon}
                  className="w-3.5 h-3.5 text-muted-foreground"
                />
                2FA Secret
                <span className="text-muted-foreground font-normal">
                  (optional)
                </span>
              </Label>
              <Input
                id="totpSecret"
                placeholder="TOTP secret key"
                value={totpSecret}
                onChange={(e) => setTotpSecret(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                From your authenticator app setup
              </p>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="folder">
                Folder
                <span className="text-muted-foreground font-normal ml-1">
                  (optional)
                </span>
              </Label>
              <Select value={folderId} onValueChange={setFolderId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a folder" />
                </SelectTrigger>
                <SelectContent>
                  {folders.map((folder) => (
                    <SelectItem key={folder.id} value={folder.id.toString()}>
                      {folder.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Row 4: Backup Codes + Notes side by side */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label
                htmlFor="backupCodes"
                className="flex items-center gap-1.5"
              >
                <HugeiconsIcon
                  icon={File01Icon}
                  className="w-3.5 h-3.5 text-muted-foreground"
                />
                Backup Codes
                <span className="text-muted-foreground font-normal">
                  (optional)
                </span>
              </Label>
              <Textarea
                id="backupCodes"
                placeholder="One code per line..."
                value={backupCodes}
                onChange={(e) => setBackupCodes(e.target.value)}
                rows={3}
              />
              <p className="text-xs text-muted-foreground">
                For account recovery
              </p>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="notes">
                Notes
                <span className="text-muted-foreground font-normal ml-1">
                  (optional)
                </span>
              </Label>
              <Textarea
                id="notes"
                placeholder="Additional notes..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
              />
            </div>
          </div>

          <DialogFooter className="pt-1">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Adding..." : "Add Password"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
