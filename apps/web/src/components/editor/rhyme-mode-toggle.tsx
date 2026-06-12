"use client";

import { cn } from "@/lib/utils";
import {
  RHYME_MODE_OPTIONS,
  type ClientRhymeMode,
} from "@/features/analysis/rhyme-modes";

interface RhymeModeToggleProps {
  value: ClientRhymeMode;
  onChange: (mode: ClientRhymeMode) => void;
}

export function RhymeModeToggle({ value, onChange }: RhymeModeToggleProps) {
  return (
    <div
      role="radiogroup"
      aria-label="Rhyme mode"
      className="inline-flex items-center rounded-full border border-border bg-surface-muted p-0.5 font-mono text-[10px] uppercase tracking-[0.18em]"
    >
      {RHYME_MODE_OPTIONS.map((option) => {
        const active = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={active}
            title={option.description}
            onClick={() => onChange(option.value)}
            className={cn(
              "rounded-full px-3 py-1 transition-colors duration-150 ease-out",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40",
              active
                ? "bg-accent/85 font-medium text-surface"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
