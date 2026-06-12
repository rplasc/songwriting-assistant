import { describe, expect, it } from "vitest";
import { buildLineNotes } from "@/features/analysis/line-notes";
import type { AnalysisResult } from "@/features/analysis/analysis-types";
import type { DraftAnalysis } from "@/features/draft-analysis/draft-analysis-types";

function makeResult(overrides: Partial<AnalysisResult> = {}): AnalysisResult {
  return {
    line: "Your warmth I embrace.",
    language: "en",
    totalSyllables: 5,
    tokens: [],
    targetWord: "embrace",
    rhymes: [],
    innerRhymes: [],
    rhymeMode: "perfect",
    lowConfidence: false,
    latencyMs: 10,
    ...overrides,
  };
}

function makeAnalysis(
  sections: Array<{
    lineStart: number;
    lineEnd: number;
    syllablePattern: number[];
    label?: string | null;
  }>,
): DraftAnalysis {
  return {
    draftId: null,
    revisionHash: "h1",
    language: "en",
    title: null,
    summary: {
      sectionCount: sections.length,
      lineCount: 4,
      totalSyllables: 20,
      notablePatterns: [],
    },
    sections: sections.map((s, i) => ({
      id: `sec_${i + 1}`,
      label: s.label ?? null,
      lineStart: s.lineStart,
      lineEnd: s.lineEnd,
      lineCount: s.lineEnd - s.lineStart + 1,
      rhymeScheme: null,
      rhymeSchemeConfidence: null,
      syllablePattern: s.syllablePattern,
      syllableVariance: 0,
      cadenceClass: "consistent",
      repetitionSignals: [],
    })),
    insights: [],
    innerRhymes: [],
    capabilities: {
      rhymeScheme: "full",
      cadencePatterns: "full",
      stressHints: "partial",
      repetition: "full",
      mixedLanguage: "partial",
    },
    analyzedAt: "2026-06-10T12:00:00Z",
    latencyMs: 12,
    serverStatus: "fresh",
  };
}

describe("buildLineNotes", () => {
  it("returns nothing without a live result", () => {
    expect(
      buildLineNotes({
        result: null,
        analysis: null,
        activeLineNumber: 1,
        language: "en",
      }),
    ).toEqual([]);
  });

  it("notes a cadence match against the containing section", () => {
    const notes = buildLineNotes({
      result: makeResult({ totalSyllables: 5 }),
      analysis: makeAnalysis([
        { lineStart: 1, lineEnd: 4, syllablePattern: [5, 6, 5, 5], label: "verse" },
      ]),
      activeLineNumber: 2,
      language: "en",
    });
    expect(notes).toContain("Matches the Verse cadence (5).");
  });

  it("notes a big deviation from the section's usual count", () => {
    const notes = buildLineNotes({
      result: makeResult({ totalSyllables: 9 }),
      analysis: makeAnalysis([
        { lineStart: 1, lineEnd: 4, syllablePattern: [5, 5, 5, 5], label: "verse" },
      ]),
      activeLineNumber: 1,
      language: "en",
    });
    expect(notes).toContain("Runs 4 over the usual Verse count (5).");
  });

  it("stays quiet about a one-syllable wobble", () => {
    const notes = buildLineNotes({
      result: makeResult({ totalSyllables: 6 }),
      analysis: makeAnalysis([
        { lineStart: 1, lineEnd: 4, syllablePattern: [5, 5, 5, 5] },
      ]),
      activeLineNumber: 1,
      language: "en",
    });
    expect(notes).toEqual([]);
  });

  it("admits when counts were guessed", () => {
    const notes = buildLineNotes({
      result: makeResult({ lowConfidence: true }),
      analysis: null,
      activeLineNumber: 1,
      language: "en",
    });
    expect(notes).toContain("I had to guess on a few words.");
  });

  it("skips cadence notes for single-line sections", () => {
    const notes = buildLineNotes({
      result: makeResult({ totalSyllables: 5 }),
      analysis: makeAnalysis([{ lineStart: 1, lineEnd: 1, syllablePattern: [5] }]),
      activeLineNumber: 1,
      language: "en",
    });
    expect(notes).toEqual([]);
  });

  it("writes Spanish notes for Spanish drafts", () => {
    const notes = buildLineNotes({
      result: makeResult({ totalSyllables: 5, language: "es" }),
      analysis: makeAnalysis([
        { lineStart: 1, lineEnd: 4, syllablePattern: [5, 5, 5, 5], label: "coro" },
      ]),
      activeLineNumber: 1,
      language: "es",
    });
    expect(notes).toContain("Sigue la cadencia de Coro (5).");
  });
});
