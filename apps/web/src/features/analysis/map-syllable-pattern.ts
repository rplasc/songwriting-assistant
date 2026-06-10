import { isCountableLine } from "@/features/structure/section-label-lines";
import type { DraftAnalysisSectionResult } from "@/features/draft-analysis/draft-analysis-types";

export interface LineSyllableEntry {
  /** 1-based line number in the analyzed content. */
  line: number;
  /** Trimmed line text — the cache key used by the editor decorations. */
  text: string;
  count: number;
}

type SectionPattern = Pick<
  DraftAnalysisSectionResult,
  "lineStart" | "lineEnd" | "syllablePattern"
>;

/**
 * A section's `syllablePattern` holds one count per countable line (non-blank,
 * non-`[Label]`) inside [lineStart..lineEnd], in order. Re-derive that walk to
 * pin counts to absolute lines. A section whose pattern length doesn't match
 * its countable lines (analysis raced an edit) is dropped entirely — wrong
 * counts are worse than none.
 */
export function mapSyllablePatternToLines(
  sections: SectionPattern[],
  sourceLines: string[],
): LineSyllableEntry[] {
  const out: LineSyllableEntry[] = [];
  for (const section of sections) {
    const entries: LineSyllableEntry[] = [];
    let i = 0;
    let mismatch = false;
    for (let line = section.lineStart; line <= section.lineEnd; line++) {
      const text = sourceLines[line - 1];
      if (text === undefined) {
        mismatch = true;
        break;
      }
      if (!isCountableLine(text)) continue;
      if (i >= section.syllablePattern.length) {
        mismatch = true;
        break;
      }
      entries.push({ line, text: text.trim(), count: section.syllablePattern[i] });
      i += 1;
    }
    if (mismatch || i !== section.syllablePattern.length) continue;
    out.push(...entries);
  }
  return out;
}
