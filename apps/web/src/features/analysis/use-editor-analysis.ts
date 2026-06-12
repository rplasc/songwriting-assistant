"use client";

import { useEffect, useRef, useState } from "react";
import {
  DEFAULT_LANGUAGE,
  type Language,
} from "@/features/language/language-types";
import { getSocketAdapter } from "./analysis-socket";
import { toAnalysisResult } from "./analysis-mappers";
import type { AnalysisResult, AnalysisStatus } from "./analysis-types";
import {
  DEFAULT_RHYME_MODE,
  type ClientRhymeMode,
  type RhymeMode,
} from "./rhyme-modes";

// FastAPI rejects perfect/near for Spanish — it expects consonant/assonant.
// Translate the unified client toggle into the language's supported mode.
function resolveRhymeMode(mode: ClientRhymeMode, language: Language): RhymeMode {
  if (language === "es") return mode === "perfect" ? "consonant" : "assonant";
  return mode;
}

const DEBOUNCE_MS = 150;
const MAX_LINE_LENGTH = 500;

export interface UseEditorAnalysisReturn {
  result: AnalysisResult | null;
  status: AnalysisStatus;
  error: string | null;
}

export function useEditorAnalysis(
  activeLine: string,
  activeWord: string | null,
  rhymeMode: ClientRhymeMode = DEFAULT_RHYME_MODE,
  language: Language = DEFAULT_LANGUAGE,
): UseEditorAnalysisReturn {
  const resolvedMode = resolveRhymeMode(rhymeMode, language);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [status, setStatus] = useState<AnalysisStatus>("idle");
  const [error, setError] = useState<string | null>(null);

  const latestSentRef = useRef<{
    line: string;
    targetWord: string | null;
    mode: RhymeMode;
    language: Language;
  } | null>(null);

  useEffect(() => {
    const adapter = getSocketAdapter();

    const removeAnalysis = adapter.onAnalysis((payload) => {
      const sent = latestSentRef.current;
      if (!sent || payload.line !== sent.line) return;
      // Same line text can be in flight for two caret words — the gateway
      // echoes the target it rhymed, so only the latest request's reply lands.
      if (
        sent.targetWord !== null &&
        payload.rhymes?.target_word !== sent.targetWord
      ) {
        return;
      }
      setResult(toAnalysisResult(payload));
      setStatus("ready");
      setError(null);
    });

    const removeError = adapter.onError(({ message }) => {
      setError(message ?? "Couldn't read that line.");
      setStatus("error");
    });

    const removeConnectError = adapter.onConnectError(() => {
      setError("Lost the connection.");
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
      setError("That line is too long to read.");
      return;
    }

    const sent = latestSentRef.current;
    const alreadyReady =
      sent &&
      sent.line === trimmed &&
      sent.targetWord === activeWord &&
      sent.mode === resolvedMode &&
      sent.language === language &&
      status === "ready";
    if (alreadyReady) return;

    const timer = setTimeout(() => {
      latestSentRef.current = {
        line: trimmed,
        targetWord: activeWord,
        mode: resolvedMode,
        language,
      };
      setStatus("loading");
      setError(null);
      getSocketAdapter().emit({
        line: trimmed,
        targetWord: activeWord ?? undefined,
        rhymeMode: resolvedMode,
        language,
      });
    }, DEBOUNCE_MS);

    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeLine, activeWord, resolvedMode, language]);

  return { result, status, error };
}
