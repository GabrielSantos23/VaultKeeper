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
import {
  Delete02Icon,
  CheckmarkCircle01Icon,
  Alert02Icon,
} from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";
import { invoke } from "@tauri-apps/api/core";
import { useVaultStore } from "@/stores/vaultStore";
import { useAuthStore } from "@/stores/authStore";
import { Loader2 } from "lucide-react";

interface DeleteAllDataDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

type DeleteState = "confirm" | "deleting" | "success" | "error";

export function DeleteAllDataDialog({
  open,
  onOpenChange,
}: DeleteAllDataDialogProps) {
  const [deleteState, setDeleteState] = useState<DeleteState>("confirm");
  const [confirmText, setConfirmText] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  const loadVaultData = useVaultStore((state) => state.loadVaultData);
  const logout = useAuthStore((state) => state.logout);

  const handleClose = () => {
    setDeleteState("confirm");
    setConfirmText("");
    setErrorMessage("");
    onOpenChange(false);
  };

  const handleDelete = async () => {
    if (confirmText !== "DELETE") {
      setErrorMessage("Please type DELETE to confirm");
      return;
    }

    setDeleteState("deleting");

    try {
      const response = await invoke<{
        success: boolean;
        data?: boolean;
        error?: string;
      }>("clear_all_data");

      if (response.success) {
        await loadVaultData();
        setDeleteState("success");
        setTimeout(() => {
          logout();
          handleClose();
        }, 2000);
      } else {
        setDeleteState("error");
        setErrorMessage(response.error || "Delete failed");
      }
    } catch (err) {
      setDeleteState("error");
      setErrorMessage(
        err instanceof Error ? err.message : "An unexpected error occurred",
      );
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[440px]">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-destructive/10 flex items-center justify-center flex-shrink-0">
              <HugeiconsIcon
                icon={Delete02Icon}
                className="w-5 h-5 text-destructive"
              />
            </div>
            <div>
              <DialogTitle className="text-destructive">
                Delete All Data
              </DialogTitle>
              <DialogDescription>
                Permanently erase all vault data
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        {deleteState === "confirm" && (
          <div className="py-4 space-y-4">
            <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
              <div className="flex items-start gap-2 text-destructive">
                <HugeiconsIcon
                  icon={Alert02Icon}
                  size={18}
                  className="shrink-0 mt-0.5"
                />
                <div>
                  <p className="font-medium">This action cannot be undone</p>
                  <p className="text-sm opacity-90 mt-1">
                    All your passwords, secure notes, credit cards, and folders
                    will be permanently deleted. You will be logged out
                    immediately.
                  </p>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">
                Type <span className="font-bold">DELETE</span> to confirm:
              </label>
              <Input
                value={confirmText}
                onChange={(e) => setConfirmText(e.target.value)}
                placeholder="Type DELETE here"
                className="uppercase"
                autoComplete="off"
              />
              {errorMessage && (
                <p className="text-sm text-destructive flex items-center gap-1">
                  <HugeiconsIcon icon={Alert02Icon} size={14} />
                  {errorMessage}
                </p>
              )}
            </div>
          </div>
        )}

        {deleteState === "deleting" && (
          <div className="py-8 flex flex-col items-center">
            <Loader2 className="w-10 h-10 animate-spin text-destructive mb-4" />
            <p className="text-sm text-muted-foreground">
              Deleting all data...
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              This may take a moment
            </p>
          </div>
        )}

        {deleteState === "success" && (
          <div className="py-8 flex flex-col items-center">
            <div className="w-16 h-16 rounded-full bg-green-100 dark:bg-green-900/20 flex items-center justify-center mb-4">
              <HugeiconsIcon
                icon={CheckmarkCircle01Icon}
                size={32}
                className="text-green-600"
              />
            </div>
            <p className="text-lg font-medium text-foreground">
              All Data Deleted
            </p>
            <p className="text-sm text-muted-foreground mt-1">
              You will be logged out in a moment...
            </p>
          </div>
        )}

        {deleteState === "error" && (
          <div className="py-4">
            <div className="p-4 rounded-lg bg-destructive/10 text-destructive">
              <p className="font-medium">Delete Failed</p>
              <p className="text-sm opacity-90">{errorMessage}</p>
            </div>
          </div>
        )}

        <DialogFooter>
          {deleteState === "confirm" && (
            <>
              <Button variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button
                onClick={handleDelete}
                variant="destructive"
                disabled={confirmText !== "DELETE"}
              >
                Delete Everything
              </Button>
            </>
          )}
          {deleteState === "error" && (
            <>
              <Button variant="outline" onClick={handleClose}>
                Close
              </Button>
              <Button
                onClick={() => {
                  setDeleteState("confirm");
                  setErrorMessage("");
                }}
                variant="destructive"
              >
                Try Again
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
