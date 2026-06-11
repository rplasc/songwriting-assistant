import { isSectionLabelLine } from "@/features/structure/section-label-lines";

export const DEFAULT_TITLE = "Untitled Draft";

/**
 * The first real lyric line, untruncated — section labels like `[Chorus]`
 * are structure, not words, so they're skipped. Empty string when there's no
 * lyric line yet. Used as the editable title's source of truth.
 */
export function deriveTitleLine(content: string): string {
  return (
    content
      .split(/\r?\n/)
      .map((l) => l.trim())
      .find((l) => l.length > 0 && !isSectionLabelLine(l)) ?? ""
  );
}

/** Ellipsis-truncate a title for header display. */
export function truncateTitle(title: string): string {
  return title.length > 60 ? `${title.slice(0, 57)}…` : title;
}

/** Display title: `deriveTitleLine`, truncated and defaulted for the header. */
export function deriveTitle(content: string): string {
  const firstLine = deriveTitleLine(content);
  if (!firstLine) return DEFAULT_TITLE;
  return truncateTitle(firstLine);
}
