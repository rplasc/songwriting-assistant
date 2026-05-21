import { cn } from "@/lib/utils";
import { STATUS_COPY } from "@/features/draft-analysis/draft-analysis-copy";
import type { DraftAnalysisStatus } from "@/features/draft-analysis/draft-analysis-types";
import type { Language } from "@/features/language/language-types";

interface Props {
  status: DraftAnalysisStatus;
  language: Language;
}

export function AnalysisFreshnessBadge({ status, language }: Props) {
  return (
    <span
      aria-live="polite"
      className={cn(
        "text-[11px] italic",
        status === "stale" ? "text-accent" : "text-muted-foreground/60",
      )}
    >
      {STATUS_COPY[status][language]}
    </span>
  );
}
