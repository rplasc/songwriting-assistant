"use client";

import { useCallback, useEffect, useSyncExternalStore } from "react";

export type ThemePreference = "system" | "light" | "dark";

export const THEME_OPTIONS: ReadonlyArray<ThemePreference> = [
  "system",
  "light",
  "dark",
];

export type RhymeHighlightStyle = "marker" | "underline";

export const RHYME_HIGHLIGHT_STYLE_OPTIONS: ReadonlyArray<RhymeHighlightStyle> =
  ["marker", "underline"];

const THEME_KEY = "sa.theme";
const RHYME_HIGHLIGHTS_KEY = "sa.rhymeHighlights";
const RHYME_HIGHLIGHT_STYLE_KEY = "sa.rhymeHighlightStyle";

export const DEFAULT_THEME: ThemePreference = "system";
export const DEFAULT_RHYME_HIGHLIGHTS = true;
export const DEFAULT_RHYME_HIGHLIGHT_STYLE: RhymeHighlightStyle = "marker";

// One subscriber set drives both preferences. Either setter notifies it, and a
// cross-tab `storage` event folds in here too so a change in another window is
// reflected (and the theme re-applied) without a reload.
type Listener = () => void;
const listeners = new Set<Listener>();

function notify(): void {
  for (const listener of listeners) listener();
}

function subscribe(callback: Listener): () => void {
  listeners.add(callback);
  const onStorage = (event: StorageEvent) => {
    if (
      event.key === THEME_KEY ||
      event.key === RHYME_HIGHLIGHTS_KEY ||
      event.key === RHYME_HIGHLIGHT_STYLE_KEY
    ) {
      callback();
    }
  };
  if (typeof window !== "undefined") {
    window.addEventListener("storage", onStorage);
  }
  return () => {
    listeners.delete(callback);
    if (typeof window !== "undefined") {
      window.removeEventListener("storage", onStorage);
    }
  };
}

function readTheme(): ThemePreference {
  if (typeof window === "undefined") return DEFAULT_THEME;
  try {
    const raw = window.localStorage.getItem(THEME_KEY);
    return raw === "light" || raw === "dark" || raw === "system"
      ? raw
      : DEFAULT_THEME;
  } catch {
    return DEFAULT_THEME;
  }
}

function writeTheme(theme: ThemePreference): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(THEME_KEY, theme);
  } catch {
    /* ignore */
  }
  notify();
}

function readRhymeHighlights(): boolean {
  if (typeof window === "undefined") return DEFAULT_RHYME_HIGHLIGHTS;
  try {
    const raw = window.localStorage.getItem(RHYME_HIGHLIGHTS_KEY);
    return raw === null ? DEFAULT_RHYME_HIGHLIGHTS : raw === "1";
  } catch {
    return DEFAULT_RHYME_HIGHLIGHTS;
  }
}

function writeRhymeHighlights(on: boolean): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(RHYME_HIGHLIGHTS_KEY, on ? "1" : "0");
  } catch {
    /* ignore */
  }
  notify();
}

function readRhymeHighlightStyle(): RhymeHighlightStyle {
  if (typeof window === "undefined") return DEFAULT_RHYME_HIGHLIGHT_STYLE;
  try {
    const raw = window.localStorage.getItem(RHYME_HIGHLIGHT_STYLE_KEY);
    return raw === "marker" || raw === "underline"
      ? raw
      : DEFAULT_RHYME_HIGHLIGHT_STYLE;
  } catch {
    return DEFAULT_RHYME_HIGHLIGHT_STYLE;
  }
}

function writeRhymeHighlightStyle(style: RhymeHighlightStyle): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(RHYME_HIGHLIGHT_STYLE_KEY, style);
  } catch {
    /* ignore */
  }
  notify();
}

/**
 * Reflect the theme choice onto <html>. "system" clears the attribute so the
 * `color-scheme: light dark` default follows the OS; an explicit choice pins
 * `color-scheme` via the `[data-theme]` rules in globals.css. Kept in sync with
 * the inline no-flash script in layout.tsx — change both together.
 */
export function applyTheme(theme: ThemePreference): void {
  if (typeof document === "undefined") return;
  const root = document.documentElement;
  if (theme === "system") root.removeAttribute("data-theme");
  else root.setAttribute("data-theme", theme);
}

export interface UsePreferencesReturn {
  theme: ThemePreference;
  rhymeHighlights: boolean;
  rhymeHighlightStyle: RhymeHighlightStyle;
  setTheme: (theme: ThemePreference) => void;
  setRhymeHighlights: (on: boolean) => void;
  setRhymeHighlightStyle: (style: RhymeHighlightStyle) => void;
}

export function usePreferences(): UsePreferencesReturn {
  const theme = useSyncExternalStore(subscribe, readTheme, () => DEFAULT_THEME);
  const rhymeHighlights = useSyncExternalStore(
    subscribe,
    readRhymeHighlights,
    () => DEFAULT_RHYME_HIGHLIGHTS,
  );
  const rhymeHighlightStyle = useSyncExternalStore(
    subscribe,
    readRhymeHighlightStyle,
    () => DEFAULT_RHYME_HIGHLIGHT_STYLE,
  );

  // The inline script sets the attribute on first paint; this keeps it honest
  // after the user changes the choice or another tab does.
  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  const setTheme = useCallback((next: ThemePreference) => {
    if (next !== readTheme()) writeTheme(next);
  }, []);

  const setRhymeHighlights = useCallback((on: boolean) => {
    if (on !== readRhymeHighlights()) writeRhymeHighlights(on);
  }, []);

  const setRhymeHighlightStyle = useCallback((style: RhymeHighlightStyle) => {
    if (style !== readRhymeHighlightStyle()) writeRhymeHighlightStyle(style);
  }, []);

  return {
    theme,
    rhymeHighlights,
    rhymeHighlightStyle,
    setTheme,
    setRhymeHighlights,
    setRhymeHighlightStyle,
  };
}

export const THEME_STORAGE_KEY = THEME_KEY;
export const RHYME_HIGHLIGHTS_STORAGE_KEY = RHYME_HIGHLIGHTS_KEY;
export const RHYME_HIGHLIGHT_STYLE_STORAGE_KEY = RHYME_HIGHLIGHT_STYLE_KEY;
