"use client";

import { useCallback, useSyncExternalStore } from "react";
import {
  coerceLanguage,
  DEFAULT_LANGUAGE,
  type Language,
} from "./language-types";

const STORAGE_KEY = "sa.language";

type Listener = () => void;
const listeners = new Set<Listener>();

function readStoredLanguage(): Language {
  if (typeof window === "undefined") return DEFAULT_LANGUAGE;
  try {
    return coerceLanguage(window.localStorage.getItem(STORAGE_KEY));
  } catch {
    return DEFAULT_LANGUAGE;
  }
}

function writeStoredLanguage(lang: Language): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(STORAGE_KEY, lang);
  } catch {
    /* ignore */
  }
  for (const listener of listeners) listener();
}

function subscribeToLanguage(callback: Listener): () => void {
  listeners.add(callback);
  return () => {
    listeners.delete(callback);
  };
}

const getServerLanguage = () => DEFAULT_LANGUAGE;

export interface UseDraftLanguageReturn {
  language: Language;
  setLanguage: (lang: Language) => void;
}

export function useDraftLanguage(): UseDraftLanguageReturn {
  const language = useSyncExternalStore(
    subscribeToLanguage,
    readStoredLanguage,
    getServerLanguage,
  );

  const setLanguage = useCallback((lang: Language) => {
    if (lang !== readStoredLanguage()) writeStoredLanguage(lang);
  }, []);

  return { language, setLanguage };
}

export const LANGUAGE_STORAGE_KEY = STORAGE_KEY;
