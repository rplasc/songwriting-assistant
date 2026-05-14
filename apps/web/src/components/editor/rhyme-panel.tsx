import { cn } from "@/lib/utils";
import type {
  AnalysisResult,
  AnalysisStatus,
} from "@/features/analysis/analysis-types";

interface RhymePanelProps {
  status: AnalysisStatus;
  result: AnalysisResult | null;
}

// Degree indicator — subtle, not wordy
const RHYME_DEGREE: Record<string, string> = {
  perfect: "●",
  near: "◐",
  family: "○",
};

export function RhymePanel({ status, result }: RhymePanelProps) {
  const isLoading = status === "loading";
  const target = result?.targetWord ?? null;
  const items = result?.rhymes ?? [];
  const hasRhymes = target !== null;

  return (
    <section
      className="rounded-md border border-border bg-surface px-4 py-3.5"
      aria-labelledby="rhyme-panel-heading"
    >
      <header className="mb-3 flex items-center justify-between">
        <h2
          id="rhyme-panel-heading"
          className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground"
        >
          Rhymes
        </h2>
        {isLoading && (
          <span aria-live="polite" className="text-[10px] text-muted-foreground/70 italic">
            finding…
          </span>
        )}
      </header>

      {!hasRhymes ? (
        <p className="text-sm text-muted-foreground">
          {status === "error"
            ? "Couldn't reach the analysis service."
            : "Finish a word to see rhymes."}
        </p>
      ) : (
        <div
          className={cn(
            "flex flex-col gap-2.5 transition-opacity duration-200",
            isLoading ? "opacity-40" : "opacity-100",
          )}
        >
          <p className="text-[11px] text-muted-foreground">
            for{" "}
            <span className="font-semibold text-accent tracking-wide">
              {target}
            </span>
          </p>
          {items.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No rhymes found for this word.
            </p>
          ) : (
            <ul
              aria-label={`Rhyme suggestions for ${target}`}
              className="flex max-h-64 flex-col overflow-y-auto"
            >
              {items.map((r, i) => (
                <li
                  key={`${r.word}-${i}`}
                  className="group flex items-baseline justify-between rounded px-1.5 py-1 hover:bg-surface-muted"
                >
                  <span className="text-sm font-medium text-foreground">
                    {r.word}
                  </span>
                  <span className="flex shrink-0 items-center gap-2 text-muted-foreground">
                    <span
                      className="text-[10px] tabular-nums"
                      aria-label={`${r.syllables} syllables`}
                    >
                      {r.syllables}
                    </span>
                    <span
                      className="text-[11px]"
                      title={r.type}
                      aria-label={r.type}
                    >
                      {RHYME_DEGREE[r.type] ?? "·"}
                    </span>
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
