import { renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { Editor } from "@tiptap/react";
import { useLineSyllables } from "@/features/analysis/use-line-syllables";
import type { AnalysisResult } from "@/features/analysis/analysis-types";
import type { DraftAnalysis } from "@/features/draft-analysis/draft-analysis-types";

const CONTENT = "[Verse]\nCounting down the days,\nTangled in my dreams,";

/** Captures the count maps the hook pushes into the editor's plugin state. */
function makeFakeEditor() {
  const dispatched: Array<ReadonlyMap<string, number>> = [];
  const tr = {
    setMeta(_key: unknown, meta: { counts: ReadonlyMap<string, number> }) {
      dispatched.push(new Map(meta.counts));
      return tr;
    },
  };
  const editor = {
    view: { dispatch: () => {} },
    state: { tr },
  } as unknown as Editor;
  return { editor, dispatched };
}

function makeAnalysis(): DraftAnalysis {
  return {
    draftId: null,
    revisionHash: "h1",
    language: "en",
    title: null,
    summary: {
      sectionCount: 1,
      lineCount: 2,
      totalSyllables: 10,
      notablePatterns: [],
    },
    sections: [
      {
        id: "sec_1",
        label: "verse",
        lineStart: 1,
        lineEnd: 3,
        lineCount: 2,
        rhymeScheme: null,
        rhymeSchemeConfidence: null,
        syllablePattern: [5, 5],
        syllableVariance: 0,
        cadenceClass: "consistent",
        repetitionSignals: [],
      },
    ],
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

function makeLiveResult(line: string, total: number): AnalysisResult {
  return {
    line,
    language: "en",
    totalSyllables: total,
    tokens: [],
    targetWord: null,
    rhymes: [],
    innerRhymes: [],
    rhymeMode: "perfect",
    lowConfidence: false,
    latencyMs: 5,
  };
}

describe("useLineSyllables", () => {
  it("pushes counts mapped from the draft analysis pattern", () => {
    const { editor, dispatched } = makeFakeEditor();
    renderHook(() =>
      useLineSyllables({
        editor,
        analysis: makeAnalysis(),
        analyzedContent: CONTENT,
        liveResult: null,
      }),
    );
    expect(dispatched).toHaveLength(1);
    const counts = dispatched[0];
    expect(counts.get("Counting down the days,")).toBe(5);
    expect(counts.get("Tangled in my dreams,")).toBe(5);
    expect(counts.has("[Verse]")).toBe(false);
  });

  it("pushes live results for the caret line without disturbing the rest", () => {
    const { editor, dispatched } = makeFakeEditor();
    const { rerender } = renderHook(
      ({ live }: { live: AnalysisResult | null }) =>
        useLineSyllables({
          editor,
          analysis: makeAnalysis(),
          analyzedContent: CONTENT,
          liveResult: live,
        }),
      { initialProps: { live: null as AnalysisResult | null } },
    );
    rerender({ live: makeLiveResult("Counting down the days, again", 7) });
    const counts = dispatched[dispatched.length - 1];
    expect(counts.get("Counting down the days, again")).toBe(7);
    expect(counts.get("Counting down the days,")).toBe(5);
  });

  it("does not re-dispatch when nothing changed", () => {
    const { editor, dispatched } = makeFakeEditor();
    const { rerender } = renderHook(
      ({ live }: { live: AnalysisResult | null }) =>
        useLineSyllables({
          editor,
          analysis: null,
          analyzedContent: null,
          liveResult: live,
        }),
      { initialProps: { live: makeLiveResult("New line here", 3) } },
    );
    expect(dispatched).toHaveLength(1);
    // Same line, same count — no dispatch.
    rerender({ live: makeLiveResult("New line here", 3) });
    expect(dispatched).toHaveLength(1);
    rerender({ live: makeLiveResult("New line here", 4) });
    expect(dispatched).toHaveLength(2);
  });

  it("stays quiet without an editor", () => {
    const { dispatched } = makeFakeEditor();
    renderHook(() =>
      useLineSyllables({
        editor: null,
        analysis: makeAnalysis(),
        analyzedContent: CONTENT,
        liveResult: makeLiveResult("a line", 2),
      }),
    );
    expect(dispatched).toHaveLength(0);
  });
});
