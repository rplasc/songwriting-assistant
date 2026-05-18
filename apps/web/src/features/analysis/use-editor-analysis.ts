"use client";

import { useEffect, useRef, useState } from "react";
import { getSocketAdapter } from "./analysis-socket";
import { toAnalysisResult } from "./analysis-mappers";
import type { AnalysisResult, AnalysisStatus } from "./analysis-types";
import { DEFAULT_RHYME_MODE, type RhymeMode } from "./rhyme-modes";

const DEBOUNCE_MS = 150;
const MAX_LINE_LENGTH = 500;

export interface UseEditorAnalysisReturn {
  result: AnalysisResult | null;
  status: AnalysisStatus;
  error: string | null;
}

export function useEditorAnalysis(
  activeLine: string,
  rhymeMode: RhymeMode = DEFAULT_RHYME_MODE,
): UseEditorAnalysisReturn {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [status, setStatus] = useState<AnalysisStatus>("idle");
  const [error, setError] = useState<string | null>(null);

  // Track the most recently emitted (line, mode) so we can discard stale responses.
  const latestSentRef = useRef<{ line: string; mode: RhymeMode } | null>(null);

  useEffect(() => {
    const adapter = getSocketAdapter();

    const removeAnalysis = adapter.onAnalysis((payload) => {
      const sent = latestSentRef.current;
      if (!sent || payload.line !== sent.line) return;
      setResult(toAnalysisResult(payload));
      setStatus("ready");
      setError(null);
    });

    const removeError = adapter.onError(({ message }) => {
      setError(message ?? "Unable to analyze line.");
      setStatus("error");
    });

    const removeConnectError = adapter.onConnectError(() => {
      setError("Cannot reach analysis service — check that the gateway is running.");
      setStatus("error");
    });

    return () => {
      removeAnalysis();
      removeError();
      removeConnectError();
    };
  }, []);

  useEffect(() => {
    const trimmed = activeLine.trim();

    if (!trimmed) {
      latestSentRef.current = null;
      setStatus("idle");
      setError(null);
      setResult(null);
      return;
    }

    if (trimmed.length > MAX_LINE_LENGTH) {
      setStatus("error");
      setError("Line is too long to analyze.");
      return;
    }

    const sent = latestSentRef.current;
    const alreadyReady =
      sent &&
      sent.line === trimmed &&
      sent.mode === rhymeMode &&
      status === "ready";
    if (alreadyReady) return;

    const timer = setTimeout(() => {
      latestSentRef.current = { line: trimmed, mode: rhymeMode };
      setStatus("loading");
      setError(null);
      getSocketAdapter().emit({ line: trimmed, rhymeMode });
    }, DEBOUNCE_MS);

    return () => clearTimeout(timer);
    // status intentionally excluded from deps — re-running on every status
    // transition would restart the debounce mid-flight.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeLine, rhymeMode]);

  return { result, status, error };
}
