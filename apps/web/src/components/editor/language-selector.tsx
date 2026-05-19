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
      className="flex items-baseline text-[12px] tracking-wide text-muted-foreground"
    >
      {LANGUAGE_OPTIONS.map((option, index) => {
        const active = option.value === value;
        return (
          <span key={option.value} className="flex items-baseline">
            {index > 0 ? (
              <span aria-hidden className="px-2 text-muted-foreground/40">
                ·
              </span>
            ) : null}
            <button
              ref={(el) => {
                refs.current[index] = el;
              }}
              type="button"
              role="radio"
              aria-checked={active}
              tabIndex={active ? 0 : -1}
              onClick={() => onChange(option.value)}
              className={cn(
                "rounded-sm px-0.5 transition-colors duration-150 ease-out",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40",
                active
                  ? "italic text-foreground"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              {option.nativeLabel}
            </button>
          </span>
        );
      })}
    </div>
  );
}
