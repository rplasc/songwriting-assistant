export function extractActiveLine(text: string, caret: number): string {
  if (!text) return "";
  const clamped = Math.max(0, Math.min(caret, text.length));
  const lineStart = text.lastIndexOf("\n", clamped - 1) + 1;
  const nextBreak = text.indexOf("\n", clamped);
  const lineEnd = nextBreak === -1 ? text.length : nextBreak;
  return text.slice(lineStart, lineEnd).trim();
}
