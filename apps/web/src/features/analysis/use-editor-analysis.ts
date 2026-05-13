"use client";

import { useEffect, useRef, useState } from "react";
import { analyzeLine, AnalysisRequestError } from "./analysis-client";
import { toAnalysisResult } from "./analysis-mappers";
import type {
  AnalysisResult,
  AnalysisStatus,
} from "./analysis-types";

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

  const seqRef = useRef(0);
  const lastSentRef = useRef<string | null>(null);
  const controllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    const trimmed = activeLine.trim();

    if (!trimmed) {
      lastSentRef.current = null;
      controllerRef.current?.abort();
      seqRef.current += 1;
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

    if (trimmed === lastSentRef.current && status === "ready") {
      return;
    }

    const timer = setTimeout(async () => {
      controllerRef.current?.abort();
      const controller = new AbortController();
      controllerRef.current = controller;

      const mySeq = ++seqRef.current;
      lastSentRef.current = trimmed;
      setStatus("loading");
      setError(null);

      try {
        const payload = await analyzeLine(trimmed, { signal: controller.signal });
        if (mySeq !== seqRef.current) return;
        setResult(toAnalysisResult(payload));
        setStatus("ready");
      } catch (err) {
        if (controller.signal.aborted) return;
        if (mySeq !== seqRef.current) return;
        const message =
          err instanceof AnalysisRequestError
            ? err.message
            : "Unable to reach analysis service.";
        setError(message);
        setStatus("error");
      }
    }, DEBOUNCE_MS);

    return () => clearTimeout(timer);
    // status intentionally excluded — we don't want re-runs from status updates.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeLine]);

  useEffect(
    () => () => {
      controllerRef.current?.abort();
    },
    [],
  );

  return { result, status, error };
}
