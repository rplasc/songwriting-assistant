"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { Language } from "@/features/language/language-types";
import {
  analyzeDraftCompare,
  COMPARE_BASELINE_UNAVAILABLE_CODE,
  DraftCompareRequestError,
} from "./draft-compare-client";
import type {
  DraftCompareResult,
  DraftCompareStatus,
} from "./draft-compare-types";

export interface UseDraftCompareInput {
  draftId: string | null;
  baseRevisionHash: string | null;
  targetRevisionHash: string | null;
  language: Language;
}

export interface UseDraftCompareReturn {
  status: DraftCompareStatus;
  result: DraftCompareResult | null;
  error: string | null;
  /** Trigger a compare now; resolves once the request completes. */
  run: () => Promise<void>;
  /** Clear any prior result, error, and revert status to idle. */
  reset: () => void;
}

export function useDraftCompare(
  input: UseDraftCompareInput,
): UseDraftCompareReturn {
  const { draftId, baseRevisionHash, targetRevisionHash, language } = input;
  const [status, setStatus] = useState<DraftCompareStatus>("idle");
  const [result, setResult] = useState<DraftCompareResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inFlightRef = useRef<AbortController | null>(null);

  const argsRef = useRef({
    draftId,
    baseRevisionHash,
    targetRevisionHash,
    language,
  });
  useEffect(() => {
    argsRef.current = {
      draftId,
      baseRevisionHash,
      targetRevisionHash,
      language,
    };
  }, [draftId, baseRevisionHash, targetRevisionHash, language]);

  const reset = useCallback(() => {
    if (inFlightRef.current) inFlightRef.current.abort();
    setResult(null);
    setError(null);
    setStatus("idle");
  }, []);

  const run = useCallback(async () => {
    const args = argsRef.current;
    if (!args.draftId || !args.baseRevisionHash || !args.targetRevisionHash) {
      setStatus("unavailable");
      return;
    }
    if (args.baseRevisionHash === args.targetRevisionHash) {
      // Nothing to compare against itself — surface as unavailable so the UI
      // can prompt the user to keep editing before comparing.
      setStatus("unavailable");
      return;
    }
    if (inFlightRef.current) inFlightRef.current.abort();
    const controller = new AbortController();
    inFlightRef.current = controller;
    setStatus("loading");
    setError(null);
    try {
      const next = await analyzeDraftCompare(
        {
          draftId: args.draftId,
          baseRevisionHash: args.baseRevisionHash,
          targetRevisionHash: args.targetRevisionHash,
          language: args.language,
        },
        { signal: controller.signal },
      );
      setResult(next);
      setStatus("ready");
    } catch (err) {
      if ((err as Error).name === "AbortError") return;
      // Snapshot eviction is recoverable — surface as `unavailable` so the
      // shell can prompt the user to re-set baseline rather than show a
      // generic error.
      if (
        err instanceof DraftCompareRequestError &&
        err.code === COMPARE_BASELINE_UNAVAILABLE_CODE
      ) {
        setResult(null);
        setError(null);
        setStatus("unavailable");
        return;
      }
      const message =
        err instanceof DraftCompareRequestError
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

  // Cancel any in-flight compare when the draft changes or the component
  // unmounts. We don't auto-clear the result on draft change; the shell owns
  // baseline state and decides when to call reset().
  useEffect(() => {
    return () => {
      if (inFlightRef.current) inFlightRef.current.abort();
    };
  }, []);

  return { status, result, error, run, reset };
}
