"use client";

import { useEffect, useRef, useState } from "react";
import {
  ASSIGN_SECTION_LABEL,
  CLEAR_SECTION_LABEL,
  CUSTOM_LABEL_PLACEHOLDER,
  SECTION_LABEL_PRESETS,
} from "@/features/draft-analysis/draft-analysis-copy";
import type { Language } from "@/features/language/language-types";
import type { StanzaRange } from "@/features/structure/structure-types";

interface Props {
  range: StanzaRange;
  label: string | null;
  language: Language;
  onAssign: (range: StanzaRange, label: string) => void;
  onClear: (range: StanzaRange) => void;
}

export function SectionLabelMenu({
  range,
  label,
  language,
  onAssign,
  onClear,
}: Props) {
  const [open, setOpen] = useState(false);
  const [custom, setCustom] = useState("");
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!open) return;
    function onDocClick(e: MouseEvent) {
      if (!containerRef.current?.contains(e.target as Node)) setOpen(false);
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  function pick(value: string) {
    onAssign(range, value);
    setCustom("");
    setOpen(false);
  }

  function submitCustom(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = custom.trim();
    if (trimmed) pick(trimmed);
  }

  return (
    <div ref={containerRef} className="relative inline-block">
      <button
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        title={ASSIGN_SECTION_LABEL[language]}
        className="inline-flex items-center gap-1 rounded-sm border border-border/60 bg-surface px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider text-muted-foreground transition-colors hover:border-accent/50 hover:text-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
      >
        <span aria-hidden>⌗</span>
        {label ?? ASSIGN_SECTION_LABEL[language]}
      </button>
      {open ? (
        <div
          role="menu"
          className="absolute right-0 z-20 mt-1 w-48 rounded-md border border-border bg-surface p-1 shadow-md"
        >
          <ul className="space-y-0.5">
            {SECTION_LABEL_PRESETS[language].map((preset) => (
              <li key={preset}>
                <button
                  role="menuitem"
                  type="button"
                  onClick={() => pick(preset)}
                  className="block w-full rounded-sm px-2 py-1 text-left text-[12px] text-foreground hover:bg-surface-muted focus-visible:outline-none focus-visible:bg-surface-muted"
                >
                  {preset}
                </button>
              </li>
            ))}
          </ul>
          <form onSubmit={submitCustom} className="mt-1 border-t border-border/60 pt-1">
            <input
              type="text"
              value={custom}
              onChange={(e) => setCustom(e.target.value)}
              placeholder={CUSTOM_LABEL_PLACEHOLDER[language]}
              maxLength={40}
              className="w-full rounded-sm border border-border bg-surface px-2 py-1 text-[12px] text-foreground outline-none focus:border-accent/60"
            />
          </form>
          {label ? (
            <button
              role="menuitem"
              type="button"
              onClick={() => {
                onClear(range);
                setOpen(false);
              }}
              className="mt-1 block w-full rounded-sm px-2 py-1 text-left text-[11px] text-muted-foreground hover:bg-surface-muted hover:text-foreground"
            >
              {CLEAR_SECTION_LABEL[language]}
            </button>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
