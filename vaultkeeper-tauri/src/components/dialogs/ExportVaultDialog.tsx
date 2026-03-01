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
import { DownloadCircle01Icon, CheckmarkCircle01Icon, Alert02Icon } from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";
import { invoke } from "@tauri-apps/api/core";
import { save } from "@tauri-apps/plugin-dialog";
import { Loader2 } from "lucide-react";

interface ExportVaultDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

type ExportState = "idle" | "exporting" | "success" | "error";

export function ExportVaultDialog({
  open,
  onOpenChange,
}: ExportVaultDialogProps) {
  const [exportState, setExportState] = useState<ExportState>("idle");
  const [errorMessage, setErrorMessage] = useState("");

  const handleClose = () => {
    setExportState("idle");
    setErrorMessage("");
    onOpenChange(false);
  };

  const handleExport = async () => {
    setExportState("exporting");
    
    try {
      const filePath = await save({
        filters: [
          { name: "JSON", extensions: ["json"] },
          { name: "All Files", extensions: ["*"] },
        ],
        defaultPath: "vaultkeeper_backup.json",
      });

      if (!filePath) {
        setExportState("idle");
        return;
      }

      const response = await invoke<{
        success: boolean;
        data?: boolean;
        error?: string;
      }>("export_vault", {
        path: filePath,
        format: "json",
      });

      if (response.success) {
        setExportState("success");
        setTimeout(() => {
          handleClose();
        }, 2000);
      } else {
        setExportState("error");
        setErrorMessage(response.error || "Export failed");
      }
    } catch (err) {
      setExportState("error");
      setErrorMessage(err instanceof Error ? err.message : "An unexpected error occurred");
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[420px]">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
              <HugeiconsIcon icon={DownloadCircle01Icon} className="w-5 h-5 text-primary" />
            </div>
            <div>
              <DialogTitle>Export Vault</DialogTitle>
              <DialogDescription>
                Download a backup of your vault data
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        {exportState === "idle" && (
          <div className="py-4">
            <div className="bg-muted rounded-lg p-4 space-y-2">
              <p className="text-sm text-foreground">
                This will export all your vault data including:
              </p>
              <ul className="text-sm text-muted-foreground list-disc list-inside">
                <li>Passwords and credentials</li>
                <li>Secure notes</li>
                <li>Credit cards</li>
                <li>Folders</li>
              </ul>
            </div>
            {errorMessage && (
              <div className="mt-4 p-3 rounded-lg bg-destructive/10 text-destructive text-sm flex items-center gap-2">
                <HugeiconsIcon icon={Alert02Icon} size={16} />
                {errorMessage}
              </div>
            )}
          </div>
        )}

        {exportState === "exporting" && (
          <div className="py-8 flex flex-col items-center">
            <Loader2 className="w-10 h-10 animate-spin text-primary mb-4" />
            <p className="text-sm text-muted-foreground">Exporting your vault...</p>
          </div>
        )}

        {exportState === "success" && (
          <div className="py-8 flex flex-col items-center">
            <div className="w-16 h-16 rounded-full bg-green-100 dark:bg-green-900/20 flex items-center justify-center mb-4">
              <HugeiconsIcon icon={CheckmarkCircle01Icon} size={32} className="text-green-600" />
            </div>
            <p className="text-lg font-medium text-foreground">Export Complete!</p>
            <p className="text-sm text-muted-foreground mt-1">
              Your vault has been backed up successfully.
            </p>
          </div>
        )}

        {exportState === "error" && (
          <div className="py-4">
            <div className="p-4 rounded-lg bg-destructive/10 text-destructive">
              <p className="font-medium">Export Failed</p>
              <p className="text-sm opacity-90">{errorMessage}</p>
            </div>
          </div>
        )}

        <DialogFooter>
          {exportState === "idle" && (
            <>
              <Button variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button onClick={handleExport}>
                Choose Location
              </Button>
            </>
          )}
          {exportState === "error" && (
            <>
              <Button variant="outline" onClick={handleClose}>
                Close
              </Button>
              <Button onClick={handleExport}>
                Try Again
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
