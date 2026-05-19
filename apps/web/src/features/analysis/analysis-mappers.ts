import { coerceLanguage } from "@/features/language/language-types";
import { DEFAULT_RHYME_MODE } from "./rhyme-modes";
import type { AnalysisResult, ServerAnalysisPayload } from "./analysis-types";

export function toAnalysisResult(
  payload: ServerAnalysisPayload,
): AnalysisResult {
  const tokens = payload.syllables?.tokens ?? [];
  return {
    line: payload.line,
    language: coerceLanguage(payload.language),
    totalSyllables: payload.syllables?.total ?? 0,
    tokens,
    targetWord: payload.rhymes?.target_word ?? null,
    rhymes: payload.rhymes?.items ?? [],
    rhymeMode: payload.rhymes?.mode ?? DEFAULT_RHYME_MODE,
    lowConfidence: tokens.some((t) => t.low_confidence === true),
    latencyMs: payload.meta?.latency_ms ?? 0,
    requestId: payload.meta?.request_id,
  };
}
