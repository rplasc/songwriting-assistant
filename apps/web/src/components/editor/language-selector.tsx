"use client";

import { useRef, type KeyboardEvent } from "react";
import { cn } from "@/lib/utils";
import { LANGUAGE_OPTIONS } from "@/features/language/language-options";
import type { Language } from "@/features/language/language-types";

interface LanguageSelectorProps {
  value: Language;
  onChange: (lang: Language) => void;
}

export function LanguageSelector({ value, onChange }: LanguageSelectorProps) {
  const refs = useRef<Array<HTMLButtonElement | null>>([]);

  const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
    event.preventDefault();
    const currentIndex = LANGUAGE_OPTIONS.findIndex((o) => o.value === value);
    const delta = event.key === "ArrowRight" ? 1 : -1;
    const nextIndex =
      (currentIndex + delta + LANGUAGE_OPTIONS.length) %
      LANGUAGE_OPTIONS.length;
    const next = LANGUAGE_OPTIONS[nextIndex];
    onChange(next.value);
    refs.current[nextIndex]?.focus();
  };

  return (
    <div
      role="radiogroup"
      aria-label="Draft language"
      onKeyDown={handleKeyDown}
      className="inline-flex items-center rounded-full border border-border bg-surface-muted p-0.5 font-mono text-[10px] uppercase tracking-[0.18em]"
    >
      {LANGUAGE_OPTIONS.map((option, index) => {
        const active = option.value === value;
        return (
          <button
            key={option.value}
            ref={(el) => {
              refs.current[index] = el;
            }}
            type="button"
            role="radio"
            aria-checked={active}
            tabIndex={active ? 0 : -1}
            title={option.nativeLabel}
            onClick={() => onChange(option.value)}
            className={cn(
              "rounded-full px-3 py-1 transition-colors duration-150 ease-out",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40",
              active
                ? "bg-accent/85 font-medium text-surface"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            {option.value.toUpperCase()}
          </button>
        );
      })}
    </div>
  );
}
