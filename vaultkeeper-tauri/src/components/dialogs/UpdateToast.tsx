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
import { 
  DownloadIcon, 
  Cancel01Icon, 
  SparklesIcon, 
  Alert02Icon,
  CheckmarkCircle01Icon 
} from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";
import { invoke } from "@tauri-apps/api/core";
import { open as openUrl } from "@tauri-apps/plugin-shell";
import { check } from "@tauri-apps/plugin-updater";
import { ask } from "@tauri-apps/plugin-dialog";
import { Loader2 } from "lucide-react";

interface UpdateToastProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

type UpdateState = "checking" | "available" | "downloading" | "installing" | "complete" | "error" | "none";

export function UpdateToast({ open, onOpenChange }: UpdateToastProps) {
  const [updateState, setUpdateState] = useState<UpdateState>("checking");
  const [version, setVersion] = useState("");
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState("");
  const [releaseNotes, setReleaseNotes] = useState<string[]>([]);

  useEffect(() => {
    if (open) {
      checkForUpdates();
    }
  }, [open]);

  const checkForUpdates = async () => {
    setUpdateState("checking");
    setErrorMessage("");

    try {
      const update = await check();

      if (update) {
        setVersion(update.version);
        
        // Parse release notes from body
        const notes = update.body
          ? update.body
              .split("\n")
              .filter((line) => line.trim().startsWith("-") || line.trim().startsWith("*"))
              .map((line) => line.replace(/^[-*]\s*/, "").trim())
              .filter((line) => line.length > 0)
              .slice(0, 5)
          : ["Bug fixes and improvements"];
        
        setReleaseNotes(notes.length > 0 ? notes : ["Bug fixes and improvements"]);
        setUpdateState("available");
      } else {
        setUpdateState("none");
      }
    } catch (err) {
      setUpdateState("error");
      setErrorMessage(err instanceof Error ? err.message : "Failed to check for updates");
    }
  };

  const handleUpdate = async () => {
    setUpdateState("downloading");

    try {
      const update = await check();

      if (!update) {
        setUpdateState("error");
        setErrorMessage("Update no longer available");
        return;
      }

      // Download and install with progress
      let downloaded = 0;
      let contentLength = 0;

      await update.downloadAndInstall((event) => {
        switch (event.event) {
          case "Started":
            contentLength = event.data.contentLength || 0;
            setUpdateState("downloading");
            break;
          case "Progress":
            downloaded += event.data.chunkLength;
            if (contentLength > 0) {
              const percent = Math.round((downloaded * 100) / contentLength);
              setDownloadProgress(percent);
            }
            break;
          case "Finished":
            setUpdateState("installing");
            break;
        }
      });

      setUpdateState("complete");
      
      // Ask to restart
      const confirmed = await ask(
        "Update installed successfully. The app needs to restart to apply changes. Restart now?",
        { title: "Restart Required", kind: "info" }
      );

      if (confirmed) {
        await invoke("restart_app");
      }
    } catch (err) {
      setUpdateState("error");
      setErrorMessage(err instanceof Error ? err.message : "Update failed");
    }
  };

  const handleLater = () => {
    onOpenChange(false);
  };

  const handleDismiss = () => {
    onOpenChange(false);
  };

  const handleManualDownload = async () => {
    await openUrl("https://github.com/Kilo-Org/kilocode/releases/latest");
  };

  if (updateState === "none" && open) {
    return (
      <Dialog open={open} onOpenChange={handleDismiss}>
        <DialogContent className="sm:max-w-[380px]">
          <DialogHeader>
            <DialogTitle>No Updates Available</DialogTitle>
            <DialogDescription>
              You are running the latest version of VaultKeeper.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button onClick={handleDismiss}>OK</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={open} onOpenChange={handleDismiss}>
      <DialogContent className="sm:max-w-[420px] p-0 gap-0 overflow-hidden">
        {/* Header with gradient */}
        <div className="bg-gradient-to-r from-primary to-primary/80 p-4">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center">
                {updateState === "complete" ? (
                  <HugeiconsIcon icon={CheckmarkCircle01Icon} className="w-5 h-5 text-white" />
                ) : (
                  <HugeiconsIcon icon={SparklesIcon} className="w-5 h-5 text-white" />
                )}
              </div>
              <div>
                <h3 className="text-white font-semibold text-base">
                  {updateState === "complete"
                    ? "Update Installed!"
                    : updateState === "checking"
                    ? "Checking for Updates..."
                    : "Update Available"}
                </h3>
                {version && updateState !== "complete" && (
                  <p className="text-white/80 text-xs">
                    Version {version} is ready
                  </p>
                )}
              </div>
            </div>
            {updateState !== "downloading" && updateState !== "installing" && (
              <button
                onClick={handleDismiss}
                className="text-white/60 hover:text-white transition-colors p-1"
              >
                <HugeiconsIcon icon={Cancel01Icon} size={18} />
              </button>
            )}
          </div>
        </div>

        {/* Content */}
        <div className="p-5 space-y-4">
          {updateState === "checking" && (
            <div className="py-4 flex flex-col items-center">
              <Loader2 className="w-8 h-8 animate-spin text-primary mb-3" />
              <p className="text-sm text-muted-foreground">Checking for updates...</p>
            </div>
          )}

          {updateState === "available" && (
            <>
              <div className="space-y-2">
                <p className="text-sm font-medium text-foreground">What&apos;s new:</p>
                <ul className="space-y-1.5">
                  {releaseNotes.map((note, index) => (
                    <li
                      key={index}
                      className="flex items-start gap-2 text-sm text-muted-foreground"
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-primary mt-1.5 flex-shrink-0" />
                      {note}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="flex items-start gap-2 text-xs text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 p-3 rounded-lg">
                <HugeiconsIcon icon={Alert02Icon} size={14} className="flex-shrink-0 mt-0.5" />
                <p>
                  The app will restart automatically after the update is installed.
                </p>
              </div>
            </>
          )}

          {(updateState === "downloading" || updateState === "installing") && (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">
                  {updateState === "downloading" ? "Downloading..." : "Installing..."}
                </span>
                {updateState === "downloading" && (
                  <span className="font-medium text-foreground">{downloadProgress}%</span>
                )}
              </div>
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary rounded-full transition-all duration-200"
                  style={{
                    width: updateState === "installing" ? "100%" : `${downloadProgress}%`,
                  }}
                />
              </div>
            </div>
          )}

          {updateState === "complete" && (
            <div className="py-2 text-center">
              <p className="text-sm text-muted-foreground">
                The update has been installed successfully.
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                Please restart the app to apply the changes.
              </p>
            </div>
          )}

          {updateState === "error" && (
            <div className="space-y-3">
              <div className="p-3 rounded-lg bg-destructive/10 text-destructive">
                <p className="font-medium text-sm">Update Failed</p>
                <p className="text-xs opacity-90">{errorMessage}</p>
              </div>
              <p className="text-xs text-muted-foreground">
                You can try downloading the update manually from our GitHub releases page.
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        {updateState !== "checking" && (
          <DialogFooter className="p-4 pt-0 gap-2">
            {updateState === "available" && (
              <>
                <Button variant="outline" onClick={handleLater}>
                  Later
                </Button>
                <Button onClick={handleUpdate} className="gap-2">
                  <HugeiconsIcon icon={DownloadIcon} size={16} />
                  Update Now
                </Button>
              </>
            )}

            {(updateState === "downloading" || updateState === "installing") && (
              <Button disabled className="w-full">
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                {updateState === "downloading" ? "Downloading..." : "Installing..."}
              </Button>
            )}

            {updateState === "complete" && (
              <Button onClick={() => invoke("restart_app")} className="w-full">
                Restart Now
              </Button>
            )}

            {updateState === "error" && (
              <>
                <Button variant="outline" onClick={handleLater}>
                  Close
                </Button>
                <Button variant="secondary" onClick={handleManualDownload}>
                  Download Manually
                </Button>
              </>
            )}
          </DialogFooter>
        )}
      </DialogContent>
    </Dialog>
  );
}

// Hook to check for updates on app start
export function useAutoUpdater() {
  const [showUpdate, setShowUpdate] = useState(false);

  useEffect(() => {
    const checkUpdates = async () => {
      try {
        // Wait a bit after app start before checking
        await new Promise((resolve) => setTimeout(resolve, 5000));
        
        const update = await check();
        if (update) {
          setShowUpdate(true);
        }
      } catch (err) {
        console.error("Auto-update check failed:", err);
      }
    };

    checkUpdates();
  }, []);

  return { showUpdate, setShowUpdate };
}
