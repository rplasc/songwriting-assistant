import type { StanzaRange } from "./structure-types";

/**
 * Detect stanza ranges from a pre-split array of lines (1-indexed, inclusive).
 * Each entry is one paragraph; empty strings are blank lines (stanza separators).
 * Prefer this over detectStanzas when lines already come from getEditorLines().
 */
export function detectStanzasFromLines(lines: string[]): StanzaRange[] {
  const ranges: StanzaRange[] = [];
  let runStart: number | null = null;

  for (let i = 0; i < lines.length; i += 1) {
    const isBlank = lines[i].trim().length === 0;
    if (!isBlank && runStart === null) {
      runStart = i + 1;
    } else if (isBlank && runStart !== null) {
      ranges.push({ lineStart: runStart, lineEnd: i });
      runStart = null;
    }
  }
  if (runStart !== null) {
    ranges.push({ lineStart: runStart, lineEnd: lines.length });
  }
  return ranges;
}

/**
 * Detect stanza ranges from a plain-text string (splits on \n).
 * Matches the gateway's `lineStart` / `lineEnd` 1-indexed contract.
 */
export function detectStanzas(content: string): StanzaRange[] {
  if (!content) return [];
  return detectStanzasFromLines(content.split(/\r?\n/));
}

export function stanzaKey(range: StanzaRange): string {
  return `${range.lineStart}-${range.lineEnd}`;
}
