import { isSectionLabelLine } from "@/features/structure/section-label-lines";

export const DEFAULT_TITLE = "Untitled Draft";

/**
 * First real lyric line becomes the title — section labels like `[Chorus]`
 * are structure, not words, so they're skipped.
 */
export function deriveTitle(content: string): string {
  const firstLine = content
    .split(/\r?\n/)
    .map((l) => l.trim())
    .find((l) => l.length > 0 && !isSectionLabelLine(l));
  if (!firstLine) return DEFAULT_TITLE;
  return firstLine.length > 60 ? `${firstLine.slice(0, 57)}…` : firstLine;
}
