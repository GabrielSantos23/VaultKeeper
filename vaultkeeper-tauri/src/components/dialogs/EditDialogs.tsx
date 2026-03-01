import { useState, useEffect } from "react";
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
import { useVaultStore, Credential, SecureNote, CreditCard } from "@/stores/vaultStore";
import {
  Key01Icon,
  Shield01Icon,
  File01Icon,
  File02Icon,
  CreditCardIcon,
} from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";

interface EditDialogsProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  item: Credential | SecureNote | CreditCard | null;
}

export function EditDialogs({ open, onOpenChange, item }: EditDialogsProps) {
  const isCredential = item && "domain" in item;
  const isNote = item && "content" in item;
  const isCard = item && "card_number" in item;

  if (!item) return null;

  if (isCredential) {
    return (
      <EditCredentialDialog
        open={open}
        onOpenChange={onOpenChange}
        credential={item as Credential}
      />
    );
  }

  if (isNote) {
    return (
      <EditSecureNoteDialog
        open={open}
        onOpenChange={onOpenChange}
        note={item as SecureNote}
      />
    );
  }

  if (isCard) {
    return (
      <EditCreditCardDialog
        open={open}
        onOpenChange={onOpenChange}
        card={item as CreditCard}
      />
    );
  }

  return null;
}

interface EditCredentialDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  credential: Credential;
}

function EditCredentialDialog({
  open,
  onOpenChange,
  credential,
}: EditCredentialDialogProps) {
  const [domain, setDomain] = useState(credential.domain);
  const [username, setUsername] = useState(credential.username);
  const [password, setPassword] = useState(credential.password);
  const [totpSecret, setTotpSecret] = useState(credential.totp_secret || "");
  const [backupCodes, setBackupCodes] = useState(credential.backup_codes || "");
  const [notes, setNotes] = useState(credential.notes || "");
  const [folderId, setFolderId] = useState<string>(
    credential.folder_id ? credential.folder_id.toString() : ""
  );
  const [isSubmitting, setIsSubmitting] = useState(false);

  const updateCredential = useVaultStore((state) => state.updateCredential);
  const folders = useVaultStore((state) => state.folders);

  useEffect(() => {
    if (open) {
      setDomain(credential.domain);
      setUsername(credential.username);
      setPassword(credential.password);
      setTotpSecret(credential.totp_secret || "");
      setBackupCodes(credential.backup_codes || "");
      setNotes(credential.notes || "");
      setFolderId(credential.folder_id ? credential.folder_id.toString() : "");
    }
  }, [open, credential]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!domain || !username || !password) return;

    setIsSubmitting(true);
    await updateCredential(credential.id, {
      domain,
      username,
      password,
      totp_secret: totpSecret || undefined,
      backup_codes: backupCodes || undefined,
      notes: notes || undefined,
      folder_id: folderId ? parseInt(folderId) : undefined,
    });
    setIsSubmitting(false);
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
              <DialogTitle>Edit Password</DialogTitle>
              <DialogDescription>
                Update password credentials
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-5 py-4">
          <div className="space-y-1.5">
            <Label htmlFor="edit-domain">Website / Domain</Label>
            <Input
              id="edit-domain"
              placeholder="e.g., google.com"
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="edit-username">Username / Email</Label>
              <Input
                id="edit-username"
                placeholder="user@example.com"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="edit-password">Password</Label>
              <Input
                id="edit-password"
                type="password"
                placeholder="Enter password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="edit-totpSecret" className="flex items-center gap-1.5">
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
                id="edit-totpSecret"
                placeholder="TOTP secret key"
                value={totpSecret}
                onChange={(e) => setTotpSecret(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                From your authenticator app setup
              </p>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="edit-folder">
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

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label
                htmlFor="edit-backupCodes"
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
                id="edit-backupCodes"
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
              <Label htmlFor="edit-notes">
                Notes
                <span className="text-muted-foreground font-normal ml-1">
                  (optional)
                </span>
              </Label>
              <Textarea
                id="edit-notes"
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
              {isSubmitting ? "Saving..." : "Save Changes"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

interface EditSecureNoteDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  note: SecureNote;
}

function EditSecureNoteDialog({
  open,
  onOpenChange,
  note,
}: EditSecureNoteDialogProps) {
  const [title, setTitle] = useState(note.title);
  const [content, setContent] = useState(note.content);
  const [folderId, setFolderId] = useState<string>(
    note.folder_id ? note.folder_id.toString() : ""
  );
  const [isSubmitting, setIsSubmitting] = useState(false);

  const updateSecureNote = useVaultStore((state) => state.updateSecureNote);
  const folders = useVaultStore((state) => state.folders);

  useEffect(() => {
    if (open) {
      setTitle(note.title);
      setContent(note.content);
      setFolderId(note.folder_id ? note.folder_id.toString() : "");
    }
  }, [open, note]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !content) return;

    setIsSubmitting(true);
    await updateSecureNote(note.id, {
      title,
      content,
      folder_id: folderId ? parseInt(folderId) : undefined,
    });
    setIsSubmitting(false);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-secondary/10 flex items-center justify-center">
              <HugeiconsIcon
                icon={File02Icon}
                className="w-5 h-5 text-secondary"
              />
            </div>
            <div>
              <DialogTitle>Edit Secure Note</DialogTitle>
              <DialogDescription>Update your secure note</DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="edit-title">Title</Label>
            <Input
              id="edit-title"
              placeholder="e.g., WiFi Password"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="edit-content">Content</Label>
            <Textarea
              id="edit-content"
              placeholder="Enter your note content..."
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={8}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="edit-folder">Folder (optional)</Label>
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

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Saving..." : "Save Changes"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

interface EditCreditCardDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  card: CreditCard;
}

function EditCreditCardDialog({
  open,
  onOpenChange,
  card,
}: EditCreditCardDialogProps) {
  const [title, setTitle] = useState(card.title);
  const [cardNumber, setCardNumber] = useState(card.card_number);
  const [cardholderName, setCardholderName] = useState(card.cardholder_name);
  const [expiryDate, setExpiryDate] = useState(card.expiry_date);
  const [cvv, setCvv] = useState(card.cvv);
  const [notes, setNotes] = useState(card.notes || "");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const updateCreditCard = useVaultStore((state) => state.updateCreditCard);

  useEffect(() => {
    if (open) {
      setTitle(card.title);
      setCardNumber(card.card_number);
      setCardholderName(card.cardholder_name);
      setExpiryDate(card.expiry_date);
      setCvv(card.cvv);
      setNotes(card.notes || "");
    }
  }, [open, card]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !cardNumber || !cardholderName) return;

    setIsSubmitting(true);
    await updateCreditCard(card.id, {
      title,
      card_number: cardNumber,
      cardholder_name: cardholderName,
      expiry_date: expiryDate,
      cvv,
      notes: notes || undefined,
    });
    setIsSubmitting(false);
    onOpenChange(false);
  };

  const formatCardNumber = (value: string) => {
    const digits = value.replace(/\D/g, "");
    const formatted = digits.replace(/(\d{4})(?=\d)/g, "$1 ");
    return formatted.slice(0, 19);
  };

  const formatExpiryDate = (value: string) => {
    const digits = value.replace(/\D/g, "");
    if (digits.length >= 2) {
      return `${digits.slice(0, 2)}/${digits.slice(2, 4)}`;
    }
    return digits;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-success/10 flex items-center justify-center">
              <HugeiconsIcon
                icon={CreditCardIcon}
                className="w-5 h-5 text-success"
              />
            </div>
            <div>
              <DialogTitle>Edit Credit Card</DialogTitle>
              <DialogDescription>
                Update your credit card details
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="edit-title">Card Name</Label>
            <Input
              id="edit-title"
              placeholder="e.g., Personal Visa"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="edit-cardNumber">Card Number</Label>
            <Input
              id="edit-cardNumber"
              placeholder="1234 5678 9012 3456"
              value={cardNumber}
              onChange={(e) => setCardNumber(formatCardNumber(e.target.value))}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="edit-cardholderName">Cardholder Name</Label>
            <Input
              id="edit-cardholderName"
              placeholder="JOHN DOE"
              value={cardholderName}
              onChange={(e) => setCardholderName(e.target.value.toUpperCase())}
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="edit-expiryDate">Expiry Date</Label>
              <Input
                id="edit-expiryDate"
                placeholder="MM/YY"
                value={expiryDate}
                onChange={(e) =>
                  setExpiryDate(formatExpiryDate(e.target.value))
                }
                maxLength={5}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="edit-cvv">CVV</Label>
              <Input
                id="edit-cvv"
                type="password"
                placeholder="123"
                value={cvv}
                onChange={(e) =>
                  setCvv(e.target.value.replace(/\D/g, "").slice(0, 4))
                }
                maxLength={4}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="edit-notes">Notes (optional)</Label>
            <Textarea
              id="edit-notes"
              placeholder="Add any additional notes..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
            />
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Saving..." : "Save Changes"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
