"use client";

import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";
import {
  ADD_SECTION_LABEL,
  SECTION_LABEL_PRESETS,
} from "@/features/draft-analysis/draft-analysis-copy";
import type { Language } from "@/features/language/language-types";

interface SectionInsertMenuProps {
  language: Language;
  onInsert: (label: string) => void;
}

/**
 * Click path for section labels: picks a preset and inserts a `[Label]`
 * line at the caret. Typing the brackets directly does the same thing.
 */
export function SectionInsertMenu({ language, onInsert }: SectionInsertMenuProps) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handleClick = (event: MouseEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) setOpen(false);
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
        onClick={() => setOpen((v) => !v)}
        className={cn(
          "rounded-sm font-mono text-[10px] uppercase tracking-[0.18em] text-accent",
          "transition-colors duration-150 ease-out hover:text-foreground",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40",
        )}
      >
        {ADD_SECTION_LABEL[language]}
      </button>
      {open && (
        <div
          role="menu"
          aria-label={ADD_SECTION_LABEL[language]}
          className={cn(
            "absolute right-0 z-20 mt-1.5 w-40 overflow-hidden rounded-md border border-border bg-surface py-1",
            "shadow-[0_4px_20px_-4px_rgb(0,0,0,0.08),0_2px_6px_-2px_rgb(0,0,0,0.06)]",
            "origin-top-right motion-safe:animate-[draft-picker-in_180ms_ease-out]",
          )}
        >
          {SECTION_LABEL_PRESETS[language].map((preset) => (
            <button
              key={preset}
              type="button"
              role="menuitem"
              onClick={() => {
                onInsert(preset);
                setOpen(false);
              }}
              className={cn(
                "block w-full px-3 py-1.5 text-left text-[12px] text-foreground",
                "transition-colors duration-150 ease-out hover:bg-surface-muted",
                "focus-visible:outline-none focus-visible:bg-surface-muted",
              )}
            >
              [{preset}]
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
