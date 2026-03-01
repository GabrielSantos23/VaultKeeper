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
import { ClipboardIcon, CheckmarkCircle01Icon, Alert02Icon } from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";
import { writeText } from "@tauri-apps/plugin-clipboard-manager";
import { invoke } from "@tauri-apps/api/core";
import { Loader2 } from "lucide-react";

interface ClearClipboardDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

type ClearState = "confirm" | "clearing" | "success" | "error";

export function ClearClipboardDialog({
  open,
  onOpenChange,
}: ClearClipboardDialogProps) {
  const [clearState, setClearState] = useState<ClearState>("confirm");
  const [errorMessage, setErrorMessage] = useState("");

  const handleClose = () => {
    setClearState("confirm");
    setErrorMessage("");
    onOpenChange(false);
  };

  const handleClear = async () => {
    setClearState("clearing");
    
    try {
      // Write empty string to clipboard
      await writeText("");
      
      // Also call the backend command
      await invoke("clear_clipboard");
      
      setClearState("success");
      setTimeout(() => {
        handleClose();
      }, 1500);
    } catch (err) {
      setClearState("error");
      setErrorMessage(err instanceof Error ? err.message : "Failed to clear clipboard");
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[380px]">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-amber-100 dark:bg-amber-900/20 flex items-center justify-center flex-shrink-0">
              <HugeiconsIcon icon={ClipboardIcon} className="w-5 h-5 text-amber-600" />
            </div>
            <div>
              <DialogTitle>Clear Clipboard</DialogTitle>
              <DialogDescription>
                Remove sensitive data from clipboard
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        {clearState === "confirm" && (
          <div className="py-4">
            <div className="bg-muted rounded-lg p-4 space-y-2">
              <p className="text-sm text-foreground">
                This will clear your system clipboard to remove any copied passwords 
                or sensitive data.
              </p>
              <p className="text-xs text-muted-foreground">
                This action is recommended after copying passwords, especially on 
                shared computers.
              </p>
            </div>
            {errorMessage && (
              <div className="mt-4 p-3 rounded-lg bg-destructive/10 text-destructive text-sm flex items-center gap-2">
                <HugeiconsIcon icon={Alert02Icon} size={16} />
                {errorMessage}
              </div>
            )}
          </div>
        )}

        {clearState === "clearing" && (
          <div className="py-6 flex flex-col items-center">
            <Loader2 className="w-8 h-8 animate-spin text-primary mb-3" />
            <p className="text-sm text-muted-foreground">Clearing clipboard...</p>
          </div>
        )}

        {clearState === "success" && (
          <div className="py-6 flex flex-col items-center">
            <div className="w-14 h-14 rounded-full bg-green-100 dark:bg-green-900/20 flex items-center justify-center mb-3">
              <HugeiconsIcon icon={CheckmarkCircle01Icon} size={28} className="text-green-600" />
            </div>
            <p className="text-base font-medium text-foreground">Clipboard Cleared!</p>
            <p className="text-xs text-muted-foreground mt-1">
              Your clipboard is now empty.
            </p>
          </div>
        )}

        {clearState === "error" && (
          <div className="py-4">
            <div className="p-3 rounded-lg bg-destructive/10 text-destructive">
              <p className="font-medium text-sm">Failed to Clear</p>
              <p className="text-xs opacity-90">{errorMessage}</p>
            </div>
          </div>
        )}

        <DialogFooter>
          {clearState === "confirm" && (
            <>
              <Button variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button onClick={handleClear} variant="secondary">
                Clear Clipboard
              </Button>
            </>
          )}
          {clearState === "error" && (
            <>
              <Button variant="outline" onClick={handleClose}>
                Close
              </Button>
              <Button onClick={handleClear} variant="secondary">
                Try Again
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
