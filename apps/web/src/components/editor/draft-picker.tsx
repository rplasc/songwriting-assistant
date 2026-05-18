"use client";

import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";
import type { DraftSummary } from "@/features/drafts/drafts-types";

interface DraftPickerProps {
  drafts: DraftSummary[];
  currentDraftId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
}

function formatTimestamp(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  const month = date.toLocaleDateString(undefined, { month: "short" });
  const day = date.getDate();
  const time = date
    .toLocaleTimeString(undefined, {
      hour: "numeric",
      minute: "2-digit",
    })
    .toLowerCase()
    .replace(/\s/g, "");
  return `${month} ${day} · ${time}`;
}

export function DraftPicker({
  drafts,
  currentDraftId,
  onSelect,
  onNew,
}: DraftPickerProps) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handleClick = (event: MouseEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", handleClick);
    document.addEventListener("keydown", handleKey);
    return () => {
      document.removeEventListener("mousedown", handleClick);
      document.removeEventListener("keydown", handleKey);
    };
  }, [open]);

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((prev) => !prev)}
        className={cn(
          "inline-flex items-center gap-1.5 rounded-md border border-border bg-surface px-2.5 py-1 text-[11px] font-medium tracking-wide text-foreground",
          "transition-colors duration-150 ease-out",
          "hover:border-accent/50 hover:bg-accent-muted/50 hover:text-accent",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40 focus-visible:border-accent/50",
          open && "border-accent/50 bg-accent-muted/40 text-accent",
        )}
      >
        Drafts
        <span
          aria-hidden
          className={cn(
            "text-[8px] text-muted-foreground transition-transform duration-200 ease-out",
            open && "rotate-180 text-accent/80",
          )}
        >
          ▼
        </span>
      </button>

      {open && (
        <div
          role="menu"
          aria-label="Saved drafts"
          className={cn(
            "absolute right-0 z-20 mt-1.5 w-64 overflow-hidden rounded-md border border-border bg-surface",
            "shadow-[0_4px_20px_-4px_rgb(0,0,0,0.08),0_2px_6px_-2px_rgb(0,0,0,0.06)]",
            "origin-top-right motion-safe:animate-[draft-picker-in_180ms_ease-out]",
          )}
        >
          <button
            type="button"
            role="menuitem"
            onClick={() => {
              onNew();
              setOpen(false);
            }}
            className={cn(
              "block w-full px-3 py-2 text-left text-[12px] font-medium text-accent",
              "transition-colors duration-150 ease-out",
              "hover:bg-accent-muted/60",
              "focus-visible:outline-none focus-visible:bg-accent-muted/60",
            )}
          >
            Start a new draft
          </button>
          <div className="border-t border-border" />
          {drafts.length === 0 ? (
            <p className="px-3 py-2.5 text-[11px] italic text-muted-foreground">
              Nothing saved yet.
            </p>
          ) : (
            <ul className="max-h-64 overflow-y-auto py-1">
              {drafts.map((draft) => {
                const active = draft.id === currentDraftId;
                return (
                  <li key={draft.id}>
                    <button
                      type="button"
                      role="menuitem"
                      onClick={() => {
                        onSelect(draft.id);
                        setOpen(false);
                      }}
                      className={cn(
                        "flex w-full flex-col gap-0.5 px-3 py-1.5 text-left",
                        "transition-colors duration-150 ease-out",
                        "hover:bg-surface-muted",
                        "focus-visible:outline-none focus-visible:bg-surface-muted",
                        active && "bg-surface-muted",
                      )}
                    >
                      <span className="truncate text-[12px] font-medium text-foreground">
                        {draft.title}
                      </span>
                      <span className="text-[10px] text-muted-foreground tabular-nums">
                        {formatTimestamp(draft.updatedAt)}
                        {active ? " · open" : ""}
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
