"use client";

import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";
import type { DraftSummary } from "@/features/drafts/drafts-types";

interface DraftPickerProps {
  drafts: DraftSummary[];
  currentDraftId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
}

function TrashIcon() {
  return (
    <svg
      aria-hidden
      viewBox="0 0 16 16"
      width="16"
      height="16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.25"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M3 4h10" />
      <path d="M6.5 4V2.75A.75.75 0 0 1 7.25 2h1.5a.75.75 0 0 1 .75.75V4" />
      <path d="M4.25 4 5 13.25a.75.75 0 0 0 .75.7h4.5a.75.75 0 0 0 .75-.7L11.75 4" />
    </svg>
  );
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
  onDelete,
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
                  <li
                    key={draft.id}
                    className={cn(
                      "group flex items-center transition-colors duration-150 ease-out",
                      "hover:bg-surface-muted focus-within:bg-surface-muted",
                      active && "bg-surface-muted",
                    )}
                  >
                    <button
                      type="button"
                      role="menuitem"
                      onClick={() => {
                        onSelect(draft.id);
                        setOpen(false);
                      }}
                      className={cn(
                        "flex min-w-0 flex-1 flex-col gap-0.5 px-3 py-1.5 text-left",
                        "focus-visible:outline-none",
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
                    <button
                      type="button"
                      aria-label={`Delete draft “${draft.title}”`}
                      title="Delete draft"
                      onClick={(event) => {
                        event.stopPropagation();
                        onDelete(draft.id);
                      }}
                      className={cn(
                        "mr-2 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-sm",
                        "text-muted-foreground/40 transition-colors duration-150 ease-out",
                        "opacity-0 group-hover:opacity-100 focus-visible:opacity-100",
                        "hover:text-danger focus-visible:text-danger",
                        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-danger/30",
                      )}
                    >
                      <TrashIcon />
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
