"use client";

import { useEffect, useState } from "react";
import type { Editor } from "@tiptap/react";
import type { DraftAnalysis } from "@/features/draft-analysis/draft-analysis-types";
import { setLineSyllableCounts } from "@/features/editor/tiptap/line-metrics-extension";
import type { AnalysisResult } from "./analysis-types";
import { mapSyllablePatternToLines } from "./map-syllable-pattern";

const MAX_CACHE_ENTRIES = 600;

export interface UseLineSyllablesInput {
  editor: Editor | null;
  /** Latest full-draft analysis (per-section syllable patterns). */
  analysis: DraftAnalysis | null;
  /** The exact content `analysis` was computed from. */
  analyzedContent: string | null;
  /** Live per-line WS analysis for the active line. */
  liveResult: AnalysisResult | null;
}

/**
 * Feeds per-line syllable counts into the editor's line-metrics decorations.
 * Draft analysis backfills every line; the live WS result keeps whichever
 * line the cursor touches current between draft analyses. The cache is keyed
 * by trimmed line text (not line number), which sidesteps index drift when
 * lines move.
 */
export function useLineSyllables(input: UseLineSyllablesInput): void {
  const { editor, analysis, analyzedContent, liveResult } = input;
  const [cache] = useState(() => new Map<string, number>());

  useEffect(() => {
    if (!editor || !analysis || analyzedContent === null) return;
    const entries = mapSyllablePatternToLines(
      analysis.sections,
      analyzedContent.split("\n"),
    );
    let changed = false;
    for (const entry of entries) {
      changed = setEntry(cache, entry.text, entry.count) || changed;
    }
    if (changed) setLineSyllableCounts(editor, cache);
  }, [editor, analysis, analyzedContent, cache]);

  useEffect(() => {
    if (!editor || !liveResult) return;
    const key = liveResult.line.trim();
    if (key.length === 0) return;
    if (setEntry(cache, key, liveResult.totalSyllables)) {
      setLineSyllableCounts(editor, cache);
    }
  }, [editor, liveResult, cache]);
}

/** LRU-ish insert: re-inserting moves the key to the back; oldest entries
 * are evicted past the cap. Returns true when the map changed. */
function setEntry(cache: Map<string, number>, key: string, value: number): boolean {
  if (cache.get(key) === value) return false;
  cache.delete(key);
  cache.set(key, value);
  while (cache.size > MAX_CACHE_ENTRIES) {
    const oldest = cache.keys().next().value;
    if (oldest === undefined) break;
    cache.delete(oldest);
  }
  return true;
}
