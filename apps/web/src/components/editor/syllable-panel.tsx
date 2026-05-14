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
      className="rounded-md border border-border bg-surface px-4 py-3.5"
      aria-labelledby="syllable-panel-heading"
    >
      <header className="mb-3 flex items-center justify-between">
        <h2
          id="syllable-panel-heading"
          className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground"
        >
          Syllables
        </h2>
        {isLoading && (
          <span aria-live="polite" className="text-[10px] text-muted-foreground/70 italic">
            counting…
          </span>
        )}
      </header>

      {!hasResult ? (
        <p className="text-sm text-muted-foreground">
          {status === "error"
            ? "Couldn’t reach the analysis service."
            : "Start writing to see syllable counts."}
        </p>
      ) : (
        <div
          className={cn(
            "flex flex-col gap-3 transition-opacity duration-200",
            isLoading ? "opacity-40" : "opacity-100",
          )}
        >
          <div className="flex items-baseline gap-2">
            <span className="text-4xl font-bold tabular-nums leading-none tracking-tight text-foreground">
              {result.totalSyllables}
            </span>
            <span className="text-xs text-muted-foreground">
              {result.totalSyllables === 1 ? "syllable" : "syllables"}
            </span>
          </div>
          {result.tokens.length > 0 && (
            <ul
              aria-label="Syllable breakdown by word"
              className="flex flex-wrap gap-x-2.5 gap-y-1.5"
            >
              {result.tokens.map((t, i) => (
                <li
                  key={`${t.text}-${i}`}
                  className="flex items-baseline gap-1"
                >
                  <span className="text-sm text-foreground">{t.text}</span>
                  <span className="text-[10px] tabular-nums text-muted-foreground">
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
