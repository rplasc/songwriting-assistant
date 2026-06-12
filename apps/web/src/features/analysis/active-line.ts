export function extractActiveLine(text: string, caret: number): string {
  if (!text) return "";
  const clamped = Math.max(0, Math.min(caret, text.length));
  const lineStart = text.lastIndexOf("\n", clamped - 1) + 1;
  const nextBreak = text.indexOf("\n", clamped);
  const lineEnd = nextBreak === -1 ? text.length : nextBreak;
  return text.slice(lineStart, lineEnd).trim();
}

const WORD_RE = /[\p{L}\p{N}'’-]+/gu;

/**
 * The word the caret is touching (inside it or at either edge), stripped of
 * punctuation. When the caret floats in whitespace, the nearest word to its
 * left wins — that's the word just typed — then the nearest to its right.
 * Null when the line has no words at all, letting the caller fall back to
 * the line's last word.
 */
export function extractWordAt(text: string, caret: number): string | null {
  if (!text) return null;
  const clamped = Math.max(0, Math.min(caret, text.length));
  let leftOf: string | null = null;
  for (const match of text.matchAll(WORD_RE)) {
    const start = match.index;
    const end = start + match[0].length;
    if (start <= clamped && clamped <= end) return match[0];
    if (end < clamped) leftOf = match[0];
    if (start > clamped) return leftOf ?? match[0];
  }
  return leftOf;
}
