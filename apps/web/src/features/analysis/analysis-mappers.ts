import { coerceLanguage } from "@/features/language/language-types";
import { DEFAULT_RHYME_MODE } from "./rhyme-modes";
import type {
  AnalysisResult,
  InnerRhymeGroup,
  ServerAnalysisPayload,
  ServerInnerRhymeGroup,
} from "./analysis-types";

/** Map the gateway's snake_case inner-rhyme groups to the client camelCase shape. */
export function toInnerRhymeGroups(
  groups: ServerInnerRhymeGroup[] | undefined,
): InnerRhymeGroup[] {
  return (groups ?? []).map((g) => ({
    id: g.id,
    rhymeType: g.rhyme_type,
    confidence: g.confidence,
    rhymeKey: g.rhyme_key,
    occurrences: g.occurrences.map((o) => ({
      lineIndex: o.line_index,
      wordIndex: o.word_index,
      charStart: o.char_start,
      charEnd: o.char_end,
      text: o.text,
      normalized: o.normalized,
    })),
  }));
}

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
    innerRhymes: toInnerRhymeGroups(payload.inner_rhymes),
    rhymeMode: payload.rhymes?.mode ?? DEFAULT_RHYME_MODE,
    lowConfidence: tokens.some((t) => t.low_confidence === true),
    latencyMs: payload.meta?.latency_ms ?? 0,
    requestId: payload.meta?.request_id,
  };
}
