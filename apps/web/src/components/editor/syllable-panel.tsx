import { cn } from "@/lib/utils";
import type {
  AnalysisResult,
  AnalysisStatus,
} from "@/features/analysis/analysis-types";

interface SyllablePanelProps {
  status: AnalysisStatus;
  result: AnalysisResult | null;
}

export function SyllablePanel({ status, result }: SyllablePanelProps) {
  const isLoading = status === "loading";
  const hasResult = result !== null;

  return (
    <section
      className="rounded-lg border border-border bg-surface p-4"
      aria-labelledby="syllable-panel-heading"
    >
      <header className="mb-3 flex items-baseline justify-between">
        <h2
          id="syllable-panel-heading"
          className="text-sm font-semibold tracking-wide text-foreground"
        >
          Syllables
        </h2>
        <span
          aria-live="polite"
          className={cn(
            "text-xs text-muted-foreground transition-opacity",
            isLoading ? "opacity-100" : "opacity-0",
          )}
        >
          analyzing...
        </span>
      </header>

      {!hasResult ? (
        <p className="text-sm text-muted-foreground">
          Start typing to see line feedback.
        </p>
      ) : (
        <div className="flex flex-col gap-3">
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-semibold tabular-nums">
              {result.totalSyllables}
            </span>
            <span className="text-sm text-muted-foreground">
              total in active line
            </span>
          </div>
          {result.tokens.length > 0 && (
            <ul className="flex flex-wrap gap-x-3 gap-y-1 text-sm">
              {result.tokens.map((t, i) => (
                <li
                  key={`${t.text}-${i}`}
                  className="flex items-baseline gap-1"
                >
                  <span>{t.text}</span>
                  <span className="text-xs text-muted-foreground tabular-nums">
                    {t.syllables}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </section>
  );
}
