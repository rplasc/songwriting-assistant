"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { Language } from "@/features/language/language-types";
import {
  analyzeDraft,
  DraftAnalysisRequestError,
} from "./draft-analysis-client";
import type {
  DraftAnalysis,
  DraftAnalysisStatus,
} from "./draft-analysis-types";

const MIN_CONTENT_CHARS = 20;
const MIN_CONTENT_LINES = 2;
const STALE_REFRESH_IDLE_MS = 4000;

export interface UseDraftAnalysisInput {
  draftId: string | null;
  content: string;
  language: Language;
}

export interface UseDraftAnalysisReturn {
  status: DraftAnalysisStatus;
  analysis: DraftAnalysis | null;
  /**
   * The exact editor text the current `analysis` was computed from. Lets
   * consumers (decorations, pattern mappers) verify line-level freshness.
   */
  analyzedContent: string | null;
  error: string | null;
  isLoading: boolean;
  /** Manually request a refresh; bypasses the min-content gate. */
  refresh: () => Promise<void>;
}

function makeRevisionKey(content: string, language: Language): string {
  return `${language}::${content}`;
}

function hasEnoughContent(content: string): boolean {
  const trimmed = content.trim();
  if (trimmed.length < MIN_CONTENT_CHARS) return false;
  const nonBlankLines = content
    .split(/\r?\n/)
    .filter((line) => line.trim().length > 0).length;
  return nonBlankLines >= MIN_CONTENT_LINES;
}

export function useDraftAnalysis(
  input: UseDraftAnalysisInput,
): UseDraftAnalysisReturn {
  const { draftId, content, language } = input;
  const [status, setStatus] = useState<DraftAnalysisStatus>("idle");
  const [analysis, setAnalysis] = useState<DraftAnalysis | null>(null);
  const [analyzedContent, setAnalyzedContent] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const inFlightRef = useRef<AbortController | null>(null);
  const autoFiredForDraftRef = useRef<string | null>(null);
  const [lastAnalyzedKey, setLastAnalyzedKey] = useState<string | null>(null);

  const currentKey = useMemo(
    () => makeRevisionKey(content, language),
    [content, language],
  );

  // Keep latest values in refs so a manual refresh always uses fresh data
  // without re-creating the callback identity on every keystroke.
  const draftIdRef = useRef(draftId);
  const contentRef = useRef(content);
  const languageRef = useRef(language);
  useEffect(() => {
    draftIdRef.current = draftId;
    contentRef.current = content;
    languageRef.current = language;
  }, [draftId, content, language]);

  const run = useCallback(async (force: boolean) => {
    const liveContent = contentRef.current;
    if (!force && !hasEnoughContent(liveContent)) {
      setStatus("idle");
      return;
    }
    if (liveContent.trim().length === 0) {
      setStatus("idle");
      return;
    }
    if (inFlightRef.current) inFlightRef.current.abort();
    const controller = new AbortController();
    inFlightRef.current = controller;
    setStatus("loading");
    setError(null);
    const keyAtRequest = makeRevisionKey(liveContent, languageRef.current);
    try {
      const result = await analyzeDraft(
        {
          draftId: draftIdRef.current,
          content: liveContent,
          language: languageRef.current,
          forceRefresh: force,
        },
        { signal: controller.signal },
      );
      setLastAnalyzedKey(keyAtRequest);
      setAnalysis(result);
      setAnalyzedContent(liveContent);
      setStatus(result.serverStatus === "unsupported" ? "unsupported" : "fresh");
    } catch (err) {
      if ((err as Error).name === "AbortError") return;
      const message =
        err instanceof DraftAnalysisRequestError
          ? err.message
          : "Couldn't reach the analysis service.";
      setError(message);
      setStatus("error");
    } finally {
      if (inFlightRef.current === controller) {
        inFlightRef.current = null;
      }
    }
  }, []);

  // Auto-fire once per draft when it opens with enough content.
  useEffect(() => {
    if (!draftId) {
      autoFiredForDraftRef.current = null;
      return;
    }
    if (autoFiredForDraftRef.current === draftId) return;
    if (!hasEnoughContent(content)) return;
    autoFiredForDraftRef.current = draftId;
    void run(false);
  }, [draftId, content, run]);

  // Cancel in-flight requests when the draft id changes or on unmount.
  useEffect(() => {
    return () => {
      if (inFlightRef.current) inFlightRef.current.abort();
    };
  }, []);

  // Derive stale state instead of toggling status from an effect. Only flip
  // a previously fresh result to stale — unsupported / error stay put until
  // the user explicitly refreshes.
  const effectiveStatus: DraftAnalysisStatus = useMemo(() => {
    if (
      status === "fresh" &&
      lastAnalyzedKey !== null &&
      lastAnalyzedKey !== currentKey
    ) {
      return "stale";
    }
    return status;
  }, [status, lastAnalyzedKey, currentKey]);

  // Gentle self-heal: when a fresh result goes stale, re-analyze after the
  // user pauses typing. The timer resets on every content change, so it only
  // fires after a true idle window; abort logic in `run` keeps one in flight.
  useEffect(() => {
    if (effectiveStatus !== "stale") return;
    if (!hasEnoughContent(content)) return;
    const t = setTimeout(() => {
      void run(false);
    }, STALE_REFRESH_IDLE_MS);
    return () => clearTimeout(t);
  }, [effectiveStatus, content, run]);

  const refresh = useCallback(async () => {
    await run(true);
  }, [run]);

  return {
    status: effectiveStatus,
    analysis,
    analyzedContent,
    error,
    isLoading: status === "loading",
    refresh,
  };
}
