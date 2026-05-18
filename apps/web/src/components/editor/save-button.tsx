"use client";

import { cn } from "@/lib/utils";
import type { SaveStatus } from "@/features/drafts/drafts-types";

interface SaveButtonProps {
  status: SaveStatus;
  onSave: () => void;
}

export function SaveButton({ status, onSave }: SaveButtonProps) {
  const disabled = status === "saving" || status === "idle" || status === "saved";
  return (
    <button
      type="button"
      onClick={onSave}
      disabled={disabled}
      className={cn(
        "rounded-md border border-border bg-surface px-2.5 py-1 text-[11px] font-medium tracking-wide text-foreground",
        "transition-colors duration-150 ease-out",
        "hover:border-accent/50 hover:bg-accent-muted/50 hover:text-accent",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40 focus-visible:border-accent/50",
        "disabled:cursor-default disabled:text-muted-foreground/70 disabled:border-border/70 disabled:bg-surface disabled:hover:bg-surface disabled:hover:text-muted-foreground/70 disabled:hover:border-border/70",
      )}
    >
      {status === "saving" ? "Saving…" : "Save"}
    </button>
  );
}
