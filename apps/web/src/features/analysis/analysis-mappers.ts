import { DEFAULT_RHYME_MODE } from "./rhyme-modes";
import type { AnalysisResult, ServerAnalysisPayload } from "./analysis-types";

export function toAnalysisResult(
  payload: ServerAnalysisPayload,
): AnalysisResult {
  return {
    line: payload.line,
    totalSyllables: payload.syllables?.total ?? 0,
    tokens: payload.syllables?.tokens ?? [],
    targetWord: payload.rhymes?.target_word ?? null,
    rhymes: payload.rhymes?.items ?? [],
    rhymeMode: payload.rhymes?.mode ?? DEFAULT_RHYME_MODE,
    latencyMs: payload.meta?.latency_ms ?? 0,
    requestId: payload.meta?.request_id,
  };
}
