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
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { File02Icon, Alert02Icon } from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";
import { invoke } from "@tauri-apps/api/core";

interface PasswordHintDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function PasswordHintDialog({
  open,
  onOpenChange,
}: PasswordHintDialogProps) {
  const [hint, setHint] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Load existing hint when dialog opens
  useEffect(() => {
    if (open) {
      loadHint();
    } else {
      resetForm();
    }
  }, [open]);

  const loadHint = async () => {
    setIsLoading(true);
    try {
      const response = await invoke<{
        success: boolean;
        data?: string | null;
        error?: string;
      }>("get_password_hint");

      if (response.success && response.data) {
        setHint(response.data);
      }
    } catch (err) {
      console.error("Failed to load hint:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const resetForm = () => {
    setHint("");
    setError(null);
    setSuccess(false);
  };

  const handleClose = () => {
    resetForm();
    onOpenChange(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const response = await invoke<{
        success: boolean;
        data?: boolean;
        error?: string;
      }>("set_password_hint", {
        hint: hint.trim(),
      });

      if (response.success) {
        setSuccess(true);
        setTimeout(() => {
          handleClose();
        }, 1500);
      } else {
        setError(response.error || "Failed to save hint");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unexpected error occurred");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[480px]">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
              <HugeiconsIcon icon={File02Icon} className="w-5 h-5 text-primary" />
            </div>
            <div>
              <DialogTitle>Password Hint</DialogTitle>
              <DialogDescription>
                Set a hint to help remember your master password
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        {success ? (
          <div className="py-8 text-center">
            <div className="w-16 h-16 rounded-full bg-green-100 dark:bg-green-900/20 flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <p className="text-lg font-medium text-foreground">Hint Saved!</p>
            <p className="text-sm text-muted-foreground mt-1">
              Your password hint has been updated successfully.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4 py-4">
            {error && (
              <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm flex items-center gap-2">
                <HugeiconsIcon icon={Alert02Icon} size={16} />
                {error}
              </div>
            )}

            <div className="space-y-1.5">
              <Label htmlFor="hint">Hint</Label>
              {isLoading ? (
                <div className="h-24 rounded-md bg-muted animate-pulse" />
              ) : (
                <>
                  <Textarea
                    id="hint"
                    placeholder="e.g., My childhood pet's name + my birth year"
                    value={hint}
                    onChange={(e) => setHint(e.target.value)}
                    rows={3}
                    maxLength={200}
                  />
                  <div className="flex items-start gap-2 text-xs text-muted-foreground">
                    <HugeiconsIcon icon={Alert02Icon} size={14} className="mt-0.5 flex-shrink-0" />
                    <p>
                      This hint will be visible to anyone who can access your device. 
                      Make sure it&apos;s something only you would understand.
                    </p>
                  </div>
                  <p className="text-xs text-muted-foreground text-right">
                    {hint.length}/200 characters
                  </p>
                </>
              )}
            </div>

            <DialogFooter className="pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={handleClose}
                disabled={isSubmitting || isLoading}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting || isLoading}>
                {isSubmitting ? "Saving..." : "Save Hint"}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
