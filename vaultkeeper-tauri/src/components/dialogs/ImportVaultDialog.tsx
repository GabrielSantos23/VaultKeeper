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
import {
  UploadCircle01Icon,
  CheckmarkCircle01Icon,
  Alert02Icon,
} from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";
import { invoke } from "@tauri-apps/api/core";
import { open as openDialog } from "@tauri-apps/plugin-dialog";
import { useVaultStore } from "@/stores/vaultStore";
import { Loader2 } from "lucide-react";

interface ImportVaultDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

type ImportState =
  | "idle"
  | "selecting"
  | "confirm"
  | "importing"
  | "success"
  | "error";

export function ImportVaultDialog({
  open,
  onOpenChange,
}: ImportVaultDialogProps) {
  const [importState, setImportState] = useState<ImportState>("idle");
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [importStats, setImportStats] = useState({
    credentials: 0,
    notes: 0,
    cards: 0,
  });

  const loadVaultData = useVaultStore((state) => state.loadVaultData);

  const handleClose = () => {
    setImportState("idle");
    setSelectedFile(null);
    setErrorMessage("");
    setImportStats({ credentials: 0, notes: 0, cards: 0 });
    onOpenChange(false);
  };

  const handleSelectFile = async () => {
    setImportState("selecting");

    try {
      const selected = await openDialog({
        filters: [
          { name: "JSON", extensions: ["json"] },
          { name: "All Files", extensions: ["*"] },
        ],
        multiple: false,
      });

      if (selected && typeof selected === "string") {
        setSelectedFile(selected);
        setImportState("confirm");
      } else {
        setImportState("idle");
      }
    } catch (err) {
      setImportState("error");
      setErrorMessage("Failed to select file");
    }
  };

  const handleImport = async () => {
    if (!selectedFile) return;

    setImportState("importing");

    try {
      const response = await invoke<{
        success: boolean;
        data?: boolean;
        error?: string;
      }>("import_vault", {
        path: selectedFile,
        format: "json",
      });

      if (response.success) {
        await loadVaultData();
        setImportState("success");
        setTimeout(() => {
          handleClose();
        }, 2000);
      } else {
        setImportState("error");
        setErrorMessage(response.error || "Import failed");
      }
    } catch (err) {
      setImportState("error");
      setErrorMessage(
        err instanceof Error ? err.message : "An unexpected error occurred",
      );
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[420px]">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
              <HugeiconsIcon
                icon={UploadCircle01Icon}
                className="w-5 h-5 text-primary"
              />
            </div>
            <div>
              <DialogTitle>Import Vault</DialogTitle>
              <DialogDescription>
                Restore your vault from a backup file
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        {importState === "idle" && (
          <div className="py-4">
            <div className="bg-muted rounded-lg p-4 space-y-2">
              <p className="text-sm text-foreground">
                Import vault data from a previously exported JSON file.
              </p>
              <div className="flex items-start gap-2 text-sm text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 p-3 rounded-lg">
                <HugeiconsIcon
                  icon={Alert02Icon}
                  size={16}
                  className="shrink-0 mt-0.5"
                />
                <p>
                  Imported data will be merged with your existing vault.
                  Duplicate entries may be created.
                </p>
              </div>
            </div>
            {errorMessage && (
              <div className="mt-4 p-3 rounded-lg bg-destructive/10 text-destructive text-sm flex items-center gap-2">
                <HugeiconsIcon icon={Alert02Icon} size={16} />
                {errorMessage}
              </div>
            )}
          </div>
        )}

        {importState === "selecting" && (
          <div className="py-8 flex flex-col items-center">
            <Loader2 className="w-10 h-10 animate-spin text-primary mb-4" />
            <p className="text-sm text-muted-foreground">
              Opening file browser...
            </p>
          </div>
        )}

        {importState === "confirm" && selectedFile && (
          <div className="py-4">
            <div className="bg-muted rounded-lg p-4">
              <p className="text-sm font-medium text-foreground mb-2">
                Selected file:
              </p>
              <p className="text-xs text-muted-foreground break-all bg-background p-2 rounded">
                {selectedFile}
              </p>
            </div>
            <div className="mt-4 flex items-start gap-2 text-sm text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 p-3 rounded-lg">
              <HugeiconsIcon
                icon={Alert02Icon}
                size={16}
                className="flex-shrink-0 mt-0.5"
              />
              <p>
                This will merge the imported data with your existing vault. Are
                you sure you want to continue?
              </p>
            </div>
          </div>
        )}

        {importState === "importing" && (
          <div className="py-8 flex flex-col items-center">
            <Loader2 className="w-10 h-10 animate-spin text-primary mb-4" />
            <p className="text-sm text-muted-foreground">
              Importing your vault...
            </p>
          </div>
        )}

        {importState === "success" && (
          <div className="py-8 flex flex-col items-center">
            <div className="w-16 h-16 rounded-full bg-green-100 dark:bg-green-900/20 flex items-center justify-center mb-4">
              <HugeiconsIcon
                icon={CheckmarkCircle01Icon}
                size={32}
                className="text-green-600"
              />
            </div>
            <p className="text-lg font-medium text-foreground">
              Import Complete!
            </p>
            <p className="text-sm text-muted-foreground mt-1">
              Your vault has been restored successfully.
            </p>
          </div>
        )}

        {importState === "error" && (
          <div className="py-4">
            <div className="p-4 rounded-lg bg-destructive/10 text-destructive">
              <p className="font-medium">Import Failed</p>
              <p className="text-sm opacity-90">{errorMessage}</p>
            </div>
          </div>
        )}

        <DialogFooter>
          {importState === "idle" && (
            <>
              <Button variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button onClick={handleSelectFile}>Select Backup File</Button>
            </>
          )}
          {importState === "confirm" && (
            <>
              <Button variant="outline" onClick={() => setImportState("idle")}>
                Back
              </Button>
              <Button onClick={handleImport}>Import Data</Button>
            </>
          )}
          {(importState === "error" || importState === "selecting") && (
            <>
              <Button variant="outline" onClick={handleClose}>
                Close
              </Button>
              <Button
                onClick={importState === "error" ? handleSelectFile : undefined}
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
