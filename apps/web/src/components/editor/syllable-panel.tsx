import { cn } from "@/lib/utils";
import type {
  AnalysisResult,
  AnalysisStatus,
} from "@/features/analysis/analysis-types";
import {
  DEFAULT_LANGUAGE,
  type Language,
} from "@/features/language/language-types";

interface SyllablePanelProps {
  status: AnalysisStatus;
  result: AnalysisResult | null;
  language?: Language;
}

const EMPTY_COPY: Record<Language, string> = {
  en: "Write a line.",
  es: "Escribe una línea.",
};

const ERROR_COPY: Record<Language, string> = {
  en: "Lost the connection.",
  es: "Se perdió la conexión.",
};

const COUNTING_COPY: Record<Language, string> = {
  en: "counting…",
  es: "contando…",
};

const SINGULAR_COPY: Record<Language, string> = {
  en: "syllable",
  es: "sílaba",
};

const PLURAL_COPY: Record<Language, string> = {
  en: "syllables",
  es: "sílabas",
};

export function SyllablePanel({
  status,
  result,
  language = DEFAULT_LANGUAGE,
}: SyllablePanelProps) {
  const isLoading = status === "loading";
  const hasResult = result !== null;
  const activeLanguage = result?.language ?? language;
  const hasLowConfidence = result?.lowConfidence === true;

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
            {COUNTING_COPY[activeLanguage]}
          </span>
        )}
      </header>

      {!hasResult ? (
        <p className="text-sm text-muted-foreground">
          {status === "error"
            ? ERROR_COPY[activeLanguage]
            : EMPTY_COPY[activeLanguage]}
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
              {result.totalSyllables === 1
                ? SINGULAR_COPY[activeLanguage]
                : PLURAL_COPY[activeLanguage]}
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
                  <span
                    className={cn(
                      "text-sm",
                      t.low_confidence
                        ? "text-muted-foreground italic"
                        : "text-foreground",
                    )}
                    title={t.low_confidence ? "Lower-confidence estimate" : undefined}
                  >
                    {t.text}
                  </span>
                  <span className="text-[10px] tabular-nums text-muted-foreground">
                    {t.syllables}
                    {t.low_confidence ? "?" : ""}
                  </span>
                </li>
              ))}
            </ul>
          )}
          {hasLowConfidence ? (
            <p className="text-[10px] italic text-muted-foreground/80">
              {activeLanguage === "es"
                ? "Adiviné con algunas."
                : "I had to guess on a few."}
            </p>
          ) : null}
        </div>
      )}
    </section>
  );
}
