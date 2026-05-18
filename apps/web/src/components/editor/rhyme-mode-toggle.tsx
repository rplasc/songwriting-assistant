"use client";

import { cn } from "@/lib/utils";
import {
  RHYME_MODE_OPTIONS,
  type RhymeMode,
} from "@/features/analysis/rhyme-modes";

interface RhymeModeToggleProps {
  value: RhymeMode;
  onChange: (mode: RhymeMode) => void;
}

export function RhymeModeToggle({ value, onChange }: RhymeModeToggleProps) {
  return (
    <div
      role="radiogroup"
      aria-label="Rhyme mode"
      className="inline-flex items-center rounded-md border border-border bg-surface-muted p-0.5 text-[11px]"
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
              "rounded px-2.5 py-1 font-medium tracking-wide",
              "transition-colors duration-150 ease-out",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40",
              active
                ? "bg-surface text-foreground shadow-[0_1px_2px_0_rgb(0,0,0,0.05)]"
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
