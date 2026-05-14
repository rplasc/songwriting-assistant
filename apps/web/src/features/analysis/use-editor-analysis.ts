"use client";

import { useEffect, useRef, useState } from "react";
import { getSocketAdapter } from "./analysis-socket";
import { toAnalysisResult } from "./analysis-mappers";
import type { AnalysisResult, AnalysisStatus } from "./analysis-types";

const DEBOUNCE_MS = 150;
const MAX_LINE_LENGTH = 500;

export interface UseEditorAnalysisReturn {
  result: AnalysisResult | null;
  status: AnalysisStatus;
  error: string | null;
}

export function useEditorAnalysis(activeLine: string): UseEditorAnalysisReturn {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [status, setStatus] = useState<AnalysisStatus>("idle");
  const [error, setError] = useState<string | null>(null);

  // Track the most recently emitted line so we can discard stale responses.
  const latestSentRef = useRef<string | null>(null);

  // Subscribe to socket events once on mount.
  useEffect(() => {
    const adapter = getSocketAdapter();

    const removeAnalysis = adapter.onAnalysis((payload) => {
      // Discard responses that don't match the line we last sent.
      if (payload.line !== latestSentRef.current) return;
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

  // Debounce and emit on activeLine changes.
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

    // Skip if this line is already reflected in the ready result.
    if (trimmed === latestSentRef.current && status === "ready") return;

    const timer = setTimeout(() => {
      latestSentRef.current = trimmed;
      setStatus("loading");
      setError(null);
      getSocketAdapter().emit(trimmed);
    }, DEBOUNCE_MS);

    return () => clearTimeout(timer);
    // status intentionally excluded from deps — re-running on every status
    // transition would restart the debounce mid-flight.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeLine]);

  return { result, status, error };
}
