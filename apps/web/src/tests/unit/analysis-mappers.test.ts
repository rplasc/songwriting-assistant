import { describe, expect, it } from "vitest";
import { toAnalysisResult } from "@/features/analysis/analysis-mappers";
import type { ServerAnalysisPayload } from "@/features/analysis/analysis-types";

const BASE_PAYLOAD: ServerAnalysisPayload = {
  line: "I see the fire in your eyes",
  syllables: {
    total: 8,
    tokens: [
      { text: "I", syllables: 1 },
      { text: "see", syllables: 1 },
      { text: "the", syllables: 1 },
      { text: "fire", syllables: 2 },
      { text: "in", syllables: 1 },
      { text: "your", syllables: 1 },
      { text: "eyes", syllables: 1 },
    ],
  },
  rhymes: {
    target_word: "eyes",
    items: [
      { word: "skies", syllables: 1, type: "perfect" },
      { word: "rise", syllables: 1, type: "near" },
    ],
  },
  meta: { request_id: "req-1", latency_ms: 42 },
};

describe("toAnalysisResult", () => {
  it("maps line, syllables, tokens, rhymes, and meta correctly", () => {
    const result = toAnalysisResult(BASE_PAYLOAD);
    expect(result.line).toBe("I see the fire in your eyes");
    expect(result.totalSyllables).toBe(8);
    expect(result.tokens).toHaveLength(7);
    expect(result.targetWord).toBe("eyes");
    expect(result.rhymes).toHaveLength(2);
    expect(result.rhymes[0].word).toBe("skies");
    expect(result.latencyMs).toBe(42);
    expect(result.requestId).toBe("req-1");
  });

  it("handles a null target_word by setting targetWord to null", () => {
    const payload: ServerAnalysisPayload = {
      ...BASE_PAYLOAD,
      rhymes: { target_word: null, items: [] },
    };
    const result = toAnalysisResult(payload);
    expect(result.targetWord).toBeNull();
    expect(result.rhymes).toHaveLength(0);
  });

  it("handles missing syllables fields gracefully", () => {
    // Simulate a partial payload where syllables is malformed at runtime
    const payload = {
      ...BASE_PAYLOAD,
      syllables: undefined,
    } as unknown as ServerAnalysisPayload;
    const result = toAnalysisResult(payload);
    expect(result.totalSyllables).toBe(0);
    expect(result.tokens).toHaveLength(0);
  });

  it("handles missing rhymes fields gracefully", () => {
    const payload = {
      ...BASE_PAYLOAD,
      rhymes: undefined,
    } as unknown as ServerAnalysisPayload;
    const result = toAnalysisResult(payload);
    expect(result.targetWord).toBeNull();
    expect(result.rhymes).toHaveLength(0);
  });

  it("omits requestId when not in meta", () => {
    const payload: ServerAnalysisPayload = {
      ...BASE_PAYLOAD,
      meta: { latency_ms: 10 },
    };
    const result = toAnalysisResult(payload);
    expect(result.requestId).toBeUndefined();
    expect(result.latencyMs).toBe(10);
  });
});
