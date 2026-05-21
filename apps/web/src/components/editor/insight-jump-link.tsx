import { JUMP_TO_LABEL } from "@/features/draft-analysis/draft-analysis-copy";
import type { Language } from "@/features/language/language-types";

interface Props {
  lineStart: number;
  lineEnd: number;
  language: Language;
  onJump: (lineStart: number, lineEnd: number) => void;
}

export function InsightJumpLink({
  lineStart,
  lineEnd,
  language,
  onJump,
}: Props) {
  const range = lineStart === lineEnd ? `${lineStart}` : `${lineStart}–${lineEnd}`;
  return (
    <button
      type="button"
      onClick={() => onJump(lineStart, lineEnd)}
      className="rounded-sm text-[11px] text-accent underline decoration-accent/30 decoration-dotted underline-offset-[3px] transition-colors duration-150 ease-out hover:decoration-accent hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
    >
      {JUMP_TO_LABEL[language]} {range}
    </button>
  );
}
