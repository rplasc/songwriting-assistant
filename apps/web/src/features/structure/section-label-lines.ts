/**
 * Typed section labels: a full line of the form `[Label]` marks the start of
 * a section. The backend section parser applies the same rule, so this module
 * is the client-side single source of truth for "is this line a label?" —
 * used by the syllable-pattern mapper and the editor decoration plugins.
 */

export const SECTION_LABEL_RE = /^\s*\[\s*([^\[\]]+?)\s*\]\s*$/u;

/** Mirrors the backend: bracketed text with no letters stays a lyric line. */
function hasLetter(s: string): boolean {
  return /\p{L}/u.test(s);
}

export function sectionLabelOf(line: string): string | null {
  const m = SECTION_LABEL_RE.exec(line);
  if (!m) return null;
  const label = m[1];
  return hasLetter(label) ? label : null;
}

export function isSectionLabelLine(line: string): boolean {
  return sectionLabelOf(line) !== null;
}

/**
 * A line that contributes to a section's `syllable_pattern`: non-blank and
 * not a section label. Mirrors the skip logic in the NLP section parser.
 */
export function isCountableLine(line: string): boolean {
  return line.trim().length > 0 && !isSectionLabelLine(line);
}
