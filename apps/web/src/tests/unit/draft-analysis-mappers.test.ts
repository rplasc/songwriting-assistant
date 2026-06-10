import { describe, expect, it } from "vitest";
import {
  toDraftAnalysis,
  type ServerDraftAnalysisPayload,
} from "@/features/draft-analysis/draft-analysis-mappers";

const BASE: ServerDraftAnalysisPayload = {
  draft_id: "draft-1",
  revision_hash: "abc123",
  analysis_status: "fresh",
  analyzed_at: "2026-05-20T12:00:00Z",
  analysis: {
    language: "en",
    title: "Late August",
    summary: {
      section_count: 2,
      line_count: 8,
      total_syllables: 56,
      notable_patterns: ["Chorus repeats line 1"],
    },
    sections: [
      {
        id: "s1",
        label: "Verse",
        line_start: 1,
        line_end: 4,
        line_count: 4,
        rhyme_scheme: "ABAB",
        rhyme_scheme_confidence: 0.82,
        syllable_pattern: [8, 8, 9, 8],
        syllable_variance: 0.25,
        cadence_class: "steady",
        repetition_signals: [{ kind: "phrase" }],
      },
    ],
    insights: [],
    capabilities: {
      rhyme_scheme: "full",
      cadence_patterns: "partial",
      stress_hints: "unsupported",
      repetition: "full",
      mixed_language: "partial",
    },
  },
  meta: { request_id: "req-9", latency_ms: 142 },
};

describe("toDraftAnalysis", () => {
  it("maps summary, sections, and capabilities into UI types", () => {
    const result = toDraftAnalysis(BASE);
    expect(result.draftId).toBe("draft-1");
    expect(result.serverStatus).toBe("fresh");
    expect(result.summary.sectionCount).toBe(2);
    expect(result.sections[0].rhymeScheme).toBe("ABAB");
    expect(result.sections[0].syllablePattern).toEqual([8, 8, 9, 8]);
    expect(result.capabilities.rhymeScheme).toBe("full");
    expect(result.capabilities.stressHints).toBe("unsupported");
    expect(result.latencyMs).toBe(142);
  });

  it("marks server status unsupported when the gateway says so", () => {
    const result = toDraftAnalysis({ ...BASE, analysis_status: "unsupported" });
    expect(result.serverStatus).toBe("unsupported");
  });

  it("coerces unknown capability values to unsupported instead of crashing", () => {
    const payload: ServerDraftAnalysisPayload = {
      ...BASE,
      analysis: {
        ...BASE.analysis,
        capabilities: {
          rhyme_scheme: "weird",
          cadence_patterns: "partial",
          stress_hints: "full",
          repetition: undefined as unknown as string,
          mixed_language: "unsupported",
        },
      },
    };
    const result = toDraftAnalysis(payload);
    expect(result.capabilities.rhymeScheme).toBe("unsupported");
    expect(result.capabilities.repetition).toBe("unsupported");
    expect(result.capabilities.stressHints).toBe("full");
  });

  it("maps inner-rhyme groups (and defaults to empty when absent)", () => {
    expect(toDraftAnalysis(BASE).innerRhymes).toEqual([]);

    const withInner: ServerDraftAnalysisPayload = {
      ...BASE,
      analysis: {
        ...BASE.analysis,
        inner_rhymes: [
          {
            id: "irh_x",
            rhyme_type: "near",
            confidence: "medium",
            rhyme_key: "AE_stop",
            occurrences: [
              {
                line_index: 1,
                word_index: 1,
                char_start: 4,
                char_end: 7,
                text: "cat",
                normalized: "cat",
              },
              {
                line_index: 2,
                word_index: 0,
                char_start: 0,
                char_end: 3,
                text: "cad",
                normalized: "cad",
              },
            ],
          },
        ],
      },
    };
    const result = toDraftAnalysis(withInner);
    expect(result.innerRhymes).toHaveLength(1);
    expect(result.innerRhymes[0].rhymeType).toBe("near");
    expect(result.innerRhymes[0].occurrences.map((o) => o.lineIndex)).toEqual([
      1, 2,
    ]);
  });

  it("defaults missing summary fields to zero", () => {
    const payload = {
      ...BASE,
      analysis: {
        ...BASE.analysis,
        summary: undefined as unknown as ServerDraftAnalysisPayload["analysis"]["summary"],
      },
    };
    const result = toDraftAnalysis(payload);
    expect(result.summary.sectionCount).toBe(0);
    expect(result.summary.notablePatterns).toEqual([]);
  });
});
