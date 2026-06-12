"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { Language } from "@/features/language/language-types";
import {
  AdvancedRhymeRequestError,
  exploreRhymes,
} from "./advanced-rhyme-client";
import type {
  AdvancedRhymeMode,
  AdvancedRhymeResult,
  AdvancedRhymeStatus,
  AdvancedRhymeTargetType,
} from "./advanced-rhyme-types";

const DEBOUNCE_MS = 200;
const MAX_QUERY_CHARS = 128;

export interface UseAdvancedRhymeInput {
  activeLine: string;
  /** Caret word — preferred "word" target when present. */
  activeWord?: string | null;
  language: Language;
  enabled: boolean;
  /** Initial mode; the hook owns it after mount. Defaults to "multisyllabic". */
  initialMode?: AdvancedRhymeMode;
  /** Initial target type; defaults to "word". */
  initialTargetType?: AdvancedRhymeTargetType;
}

export interface UseAdvancedRhymeReturn {
  status: AdvancedRhymeStatus;
  result: AdvancedRhymeResult | null;
  error: string | null;
  mode: AdvancedRhymeMode;
  targetType: AdvancedRhymeTargetType;
  setMode: (mode: AdvancedRhymeMode) => void;
  setTargetType: (targetType: AdvancedRhymeTargetType) => void;
  /** The string the hook would send to the server, or null when blank. */
  resolvedQuery: string | null;
}

function lastWordOf(line: string): string | null {
  const trimmed = line.trim();
  if (!trimmed) return null;
  // Strip a single trailing punctuation cluster so "hollow," still hits.
  const cleaned = trimmed.replace(/[\p{P}\p{S}]+$/u, "");
  const parts = cleaned.split(/\s+/);
  const last = parts[parts.length - 1] ?? "";
  return last.length > 0 ? last : null;
}

function resolveQuery(
  line: string,
  activeWord: string | null,
  targetType: AdvancedRhymeTargetType,
): string | null {
  if (targetType === "word") {
    // The caret word when known (matches the suggestion strip's target);
    // otherwise the line's last word.
    return activeWord ?? lastWordOf(line);
  }
  const trimmed = line.trim();
  if (!trimmed) return null;
  return trimmed.length > MAX_QUERY_CHARS
    ? trimmed.slice(-MAX_QUERY_CHARS).trim()
    : trimmed;
}

export function useAdvancedRhyme(
  input: UseAdvancedRhymeInput,
): UseAdvancedRhymeReturn {
  const { activeLine, activeWord = null, language, enabled } = input;
  const [mode, setMode] = useState<AdvancedRhymeMode>(
    input.initialMode ?? "multisyllabic",
  );
  const [targetType, setTargetType] = useState<AdvancedRhymeTargetType>(
    input.initialTargetType ?? "word",
  );
  const [status, setStatus] = useState<AdvancedRhymeStatus>("idle");
  const [result, setResult] = useState<AdvancedRhymeResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const inFlightRef = useRef<AbortController | null>(null);

  const resolvedQuery = useMemo(
    () => resolveQuery(activeLine, activeWord, targetType),
    [activeLine, activeWord, targetType],
  );

  const run = useCallback(
    async (query: string, mode_: AdvancedRhymeMode, targetType_: AdvancedRhymeTargetType, language_: Language) => {
      if (inFlightRef.current) inFlightRef.current.abort();
      const controller = new AbortController();
      inFlightRef.current = controller;
      setStatus("loading");
      setError(null);
      try {
        const next = await exploreRhymes(
          { query, mode: mode_, targetType: targetType_, language: language_ },
          { signal: controller.signal },
        );
        setResult(next);
        // Surface unsupported state explicitly when the request mode is
        // multisyllabic but the language can't deliver it.
        if (
          mode_ === "multisyllabic" &&
          next.capabilities.multisyllabic.status === "unsupported"
        ) {
          setStatus("unsupported");
        } else {
          setStatus("ready");
        }
      } catch (err) {
        if ((err as Error).name === "AbortError") return;
        const message =
          err instanceof AdvancedRhymeRequestError
            ? err.message
            : "Couldn't reach the analysis service.";
        setError(message);
        setStatus("error");
      } finally {
        if (inFlightRef.current === controller) {
          inFlightRef.current = null;
        }
      }
    },
    [],
  );

  // Debounced fire when enabled. Aborts on any input change.
  useEffect(() => {
    if (!enabled) {
      // Drop in-flight work the moment the explorer closes.
      if (inFlightRef.current) inFlightRef.current.abort();
      setStatus("idle");
      return;
    }
    if (!resolvedQuery) {
      setStatus("idle");
      setResult(null);
      return;
    }
    const timer = window.setTimeout(() => {
      void run(resolvedQuery, mode, targetType, language);
    }, DEBOUNCE_MS);
    return () => window.clearTimeout(timer);
  }, [enabled, resolvedQuery, mode, targetType, language, run]);

  // Cancel on unmount.
  useEffect(() => {
    return () => {
      if (inFlightRef.current) inFlightRef.current.abort();
    };
  }, []);

  return {
    status,
    result,
    error,
    mode,
    targetType,
    setMode,
    setTargetType,
    resolvedQuery,
  };
}
