"use client";

import type { Editor } from "@tiptap/react";
import { cn } from "@/lib/utils";
import type { Language } from "@/features/language/language-types";
import type { RhymeHighlightStyle } from "@/features/settings/preferences";
import { LyricEditor } from "./lyric-editor";

interface FocusModeViewProps {
  editor: Editor | null;
  rhymeHighlightStyle: RhymeHighlightStyle;
  rhymeHighlights: boolean;
  onRhymeHighlightsChange: (on: boolean) => void;
  language: Language;
  onExit: () => void;
}

const COPY: Record<
  Language,
  {
    exit: string;
    rhymeHighlights: string;
    on: string;
    off: string;
    hint: (rhymesOn: boolean) => string;
  }
> = {
  en: {
    exit: "Exit focus",
    rhymeHighlights: "Rhyme highlights",
    on: "On",
    off: "Off",
    hint: (rhymesOn) =>
      `Focus mode · Esc to exit · rhymes ${rhymesOn ? "on" : "off"}`,
  },
  es: {
    exit: "Salir del enfoque",
    rhymeHighlights: "Resaltar rimas",
    on: "Sí",
    off: "No",
    hint: (rhymesOn) =>
      `Modo enfoque · Esc para salir · rimas ${rhymesOn ? "activadas" : "desactivadas"}`,
  },
};

function ExitIcon() {
  return (
    <svg
      aria-hidden
      viewBox="0 0 16 16"
      width="13"
      height="13"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.25"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M10 2.5h2.5a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H10" />
      <path d="M6.5 5 3.5 8l3 3M3.5 8h7" />
    </svg>
  );
}

/**
 * Distraction-free writing view: a full-screen overlay holding only the lyric
 * editor and rhyme highlighting. Cleanly covers the page chrome from page.tsx.
 * The editor is the same persistent instance as the full notebook, so the
 * analysis hooks in the shell keep rhyme highlighting live here.
 */
export function FocusModeView({
  editor,
  rhymeHighlightStyle,
  rhymeHighlights,
  onRhymeHighlightsChange,
  language,
  onExit,
}: FocusModeViewProps) {
  const copy = COPY[language];

  return (
    <div className="fixed inset-0 z-50 flex flex-col overflow-y-auto bg-surface-muted">
      <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col px-4 py-8 sm:px-6 sm:py-12">
        <div className="mb-4 flex items-center justify-end gap-3">
          <RhymeToggle
            checked={rhymeHighlights}
            onChange={onRhymeHighlightsChange}
            label={copy.rhymeHighlights}
            onText={copy.on}
            offText={copy.off}
          />
          <button
            type="button"
            onClick={onExit}
            className={cn(
              "inline-flex h-7 items-center gap-1.5 rounded-md border border-border bg-surface px-2.5 text-[11px] font-medium text-muted-foreground",
              "transition-colors duration-150 ease-out",
              "hover:border-accent/50 hover:bg-accent-muted/50 hover:text-accent",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40 focus-visible:border-accent/50",
            )}
          >
            <ExitIcon />
            {copy.exit}
          </button>
        </div>

        <LyricEditor
          editor={editor}
          rhymeHighlightStyle={rhymeHighlightStyle}
          syllableCounts={false}
        />

        <p className="mt-6 border-t border-dashed border-border/70 pt-2.5 text-center font-mono text-[9px] uppercase tracking-[0.22em] text-muted-foreground/70">
          {copy.hint(rhymeHighlights)}
        </p>
      </div>
    </div>
  );
}

interface RhymeToggleProps {
  checked: boolean;
  onChange: (next: boolean) => void;
  label: string;
  onText: string;
  offText: string;
}

function RhymeToggle({
  checked,
  onChange,
  label,
  onText,
  offText,
}: RhymeToggleProps) {
  return (
    <span className="inline-flex items-center gap-2">
      <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
        {label}
      </span>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        aria-label={`${label}: ${checked ? onText : offText}`}
        title={checked ? onText : offText}
        onClick={() => onChange(!checked)}
        className={cn(
          "relative inline-flex h-[18px] w-8 shrink-0 items-center rounded-full border transition-colors duration-150 ease-out",
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
    </span>
  );
}
