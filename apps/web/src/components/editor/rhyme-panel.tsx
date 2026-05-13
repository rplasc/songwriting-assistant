import { cn } from "@/lib/utils";
import type {
  AnalysisResult,
  AnalysisStatus,
} from "@/features/analysis/analysis-types";

interface RhymePanelProps {
  status: AnalysisStatus;
  result: AnalysisResult | null;
}

export function RhymePanel({ status, result }: RhymePanelProps) {
  const isLoading = status === "loading";
  const target = result?.targetWord ?? null;
  const items = result?.rhymes ?? [];

  return (
    <section
      className="rounded-lg border border-border bg-surface p-4"
      aria-labelledby="rhyme-panel-heading"
    >
      <header className="mb-3 flex items-baseline justify-between">
        <h2
          id="rhyme-panel-heading"
          className="text-sm font-semibold tracking-wide"
        >
          Rhymes
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

      {!target ? (
        <p className="text-sm text-muted-foreground">
          Finish a word to get rhymes.
        </p>
      ) : (
        <div className="flex flex-col gap-3">
          <p className="text-sm text-muted-foreground">
            Rhyming{" "}
            <span className="font-medium text-foreground">{target}</span>
          </p>
          {items.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No rhymes found for this word.
            </p>
          ) : (
            <ul className="flex max-h-72 flex-col gap-1 overflow-y-auto pr-1">
              {items.map((r, i) => (
                <li
                  key={`${r.word}-${i}`}
                  className="flex items-baseline justify-between rounded px-2 py-1 hover:bg-surface-muted"
                >
                  <span className="text-sm">{r.word}</span>
                  <span className="text-xs text-muted-foreground">
                    {r.type} &middot; {r.syllables} syl
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
