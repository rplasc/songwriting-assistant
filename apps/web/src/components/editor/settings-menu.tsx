"use client";

import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";
import type { Language } from "@/features/language/language-types";
import {
  RHYME_HIGHLIGHT_STYLE_OPTIONS,
  THEME_OPTIONS,
  type RhymeHighlightStyle,
  type ThemePreference,
} from "@/features/settings/preferences";

interface SettingsMenuProps {
  language: Language;
  theme: ThemePreference;
  onThemeChange: (theme: ThemePreference) => void;
  rhymeHighlights: boolean;
  onRhymeHighlightsChange: (on: boolean) => void;
  rhymeHighlightStyle: RhymeHighlightStyle;
  onRhymeHighlightStyleChange: (style: RhymeHighlightStyle) => void;
}

const COPY: Record<
  Language,
  {
    settings: string;
    appearance: string;
    theme: Record<ThemePreference, string>;
    rhymeHighlights: string;
    rhymeHighlightsHint: string;
    style: string;
    styleOptions: Record<RhymeHighlightStyle, string>;
    on: string;
    off: string;
  }
> = {
  en: {
    settings: "Settings",
    appearance: "Appearance",
    theme: { system: "System", light: "Light", dark: "Dark" },
    rhymeHighlights: "Rhyme highlights",
    rhymeHighlightsHint: "Mark rhyming words in the lyrics.",
    style: "Style",
    styleOptions: { marker: "Marker", underline: "Underline" },
    on: "On",
    off: "Off",
  },
  es: {
    settings: "Ajustes",
    appearance: "Apariencia",
    theme: { system: "Sistema", light: "Claro", dark: "Oscuro" },
    rhymeHighlights: "Resaltar rimas",
    rhymeHighlightsHint: "Marca las palabras que riman en la letra.",
    style: "Estilo",
    styleOptions: { marker: "Marcador", underline: "Subrayado" },
    on: "Sí",
    off: "No",
  },
};

function GearIcon() {
  return (
    <svg
      aria-hidden
      viewBox="0 0 16 16"
      width="15"
      height="15"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.25"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="8" cy="8" r="2.25" />
      <path d="M8 1.5v1.6M8 12.9v1.6M14.5 8h-1.6M3.1 8H1.5M12.6 3.4l-1.13 1.13M4.53 11.47 3.4 12.6M12.6 12.6l-1.13-1.13M4.53 4.53 3.4 3.4" />
    </svg>
  );
}

export function SettingsMenu({
  language,
  theme,
  onThemeChange,
  rhymeHighlights,
  onRhymeHighlightsChange,
  rhymeHighlightStyle,
  onRhymeHighlightStyleChange,
}: SettingsMenuProps) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const copy = COPY[language];

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
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-label={copy.settings}
        title={copy.settings}
        onClick={() => setOpen((v) => !v)}
        className={cn(
          "inline-flex h-7 w-7 items-center justify-center rounded-md border border-border bg-surface text-muted-foreground",
          "transition-colors duration-150 ease-out",
          "hover:border-accent/50 hover:bg-accent-muted/50 hover:text-accent",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40 focus-visible:border-accent/50",
          open && "border-accent/50 bg-accent-muted/40 text-accent",
        )}
      >
        <GearIcon />
      </button>

      {open && (
        <div
          role="dialog"
          aria-label={copy.settings}
          className={cn(
            "absolute right-0 z-20 mt-1.5 w-64 rounded-md border border-border bg-surface p-3.5",
            "shadow-[0_4px_20px_-4px_rgb(0,0,0,0.08),0_2px_6px_-2px_rgb(0,0,0,0.06)]",
            "origin-top-right motion-safe:animate-[draft-picker-in_180ms_ease-out]",
          )}
        >
          <fieldset className="mb-4">
            <legend className="mb-1.5 font-mono text-[10px] font-medium uppercase tracking-[0.22em] text-muted-foreground">
              {copy.appearance}
            </legend>
            <div
              role="radiogroup"
              aria-label={copy.appearance}
              className="inline-flex w-full items-center rounded-full border border-border bg-surface-muted p-0.5 font-mono text-[10px] uppercase tracking-[0.16em]"
            >
              {THEME_OPTIONS.map((option) => {
                const active = option === theme;
                return (
                  <button
                    key={option}
                    type="button"
                    role="radio"
                    aria-checked={active}
                    onClick={() => onThemeChange(option)}
                    className={cn(
                      "flex-1 rounded-full px-2 py-1 transition-colors duration-150 ease-out",
                      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40",
                      active
                        ? "bg-accent/85 font-medium text-surface"
                        : "text-muted-foreground hover:text-foreground",
                    )}
                  >
                    {copy.theme[option]}
                  </button>
                );
              })}
            </div>
          </fieldset>

          <div className="flex items-start justify-between gap-3">
            <span className="min-w-0">
              <span className="block text-[12px] font-medium text-foreground">
                {copy.rhymeHighlights}
              </span>
              <span className="mt-0.5 block text-[11px] leading-snug text-muted-foreground">
                {copy.rhymeHighlightsHint}
              </span>
            </span>
            <Switch
              checked={rhymeHighlights}
              onChange={onRhymeHighlightsChange}
              label={copy.rhymeHighlights}
              onText={copy.on}
              offText={copy.off}
            />
          </div>

          {/* Style only applies while highlights are on; dim it otherwise so
              the relationship is clear without hiding the choice. */}
          <div
            className={cn(
              "mt-3 flex items-center justify-between gap-3 transition-opacity duration-150",
              rhymeHighlights ? "opacity-100" : "opacity-45",
            )}
          >
            <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
              {copy.style}
            </span>
            <div
              role="radiogroup"
              aria-label={copy.style}
              className="inline-flex items-center rounded-full border border-border bg-surface-muted p-0.5 font-mono text-[10px] uppercase tracking-[0.16em]"
            >
              {RHYME_HIGHLIGHT_STYLE_OPTIONS.map((option) => {
                const active = option === rhymeHighlightStyle;
                return (
                  <button
                    key={option}
                    type="button"
                    role="radio"
                    aria-checked={active}
                    disabled={!rhymeHighlights}
                    onClick={() => onRhymeHighlightStyleChange(option)}
                    className={cn(
                      "rounded-full px-2.5 py-1 transition-colors duration-150 ease-out",
                      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40",
                      "disabled:cursor-not-allowed",
                      active
                        ? "bg-accent/85 font-medium text-surface"
                        : "text-muted-foreground enabled:hover:text-foreground",
                    )}
                  >
                    {copy.styleOptions[option]}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

interface SwitchProps {
  checked: boolean;
  onChange: (next: boolean) => void;
  label: string;
  onText: string;
  offText: string;
}

function Switch({ checked, onChange, label, onText, offText }: SwitchProps) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={`${label}: ${checked ? onText : offText}`}
      title={checked ? onText : offText}
      onClick={() => onChange(!checked)}
      className={cn(
        "relative mt-0.5 inline-flex h-[18px] w-8 shrink-0 items-center rounded-full border transition-colors duration-150 ease-out",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40",
        checked
          ? "border-accent/60 bg-accent/85"
          : "border-border bg-surface-muted",
      )}
    >
      <span
        aria-hidden
        className={cn(
          "inline-block h-3 w-3 rounded-full bg-surface shadow-sm transition-transform duration-150 ease-out",
          checked ? "translate-x-[15px]" : "translate-x-[2px]",
        )}
      />
    </button>
  );
}
