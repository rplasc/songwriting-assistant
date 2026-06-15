"use client";

import { cn } from "@/lib/utils";
import type {
  AnalysisResult,
  AnalysisStatus,
} from "@/features/analysis/analysis-types";
import type { ClientRhymeMode } from "@/features/analysis/rhyme-modes";
import type { Language } from "@/features/language/language-types";

interface RhymeSuggestionStripProps {
  status: AnalysisStatus;
  result: AnalysisResult | null;
  rhymeMode: ClientRhymeMode;
  language: Language;
  onRequestModeChange: (mode: ClientRhymeMode) => void;
  onInsertWord: (word: string) => void;
  onOpenExplorer: () => void;
}

const RHYME_DEGREE: Record<string, string> = {
  perfect: "●",
  near: "◐",
  family: "○",
  consonant: "●",
  assonant: "◐",
};

const MODE_LABEL: Record<Language, Record<ClientRhymeMode, string>> = {
  en: { perfect: "perfect", near: "near" },
  es: { perfect: "consonante", near: "asonante" },
};

const HEADING: Record<Language, string> = {
  en: "Rhyme suggestions",
  es: "Sugerencias de rima",
};

const FOR_COPY: Record<Language, string> = {
  en: "for",
  es: "para",
};

const FINDING_COPY: Record<Language, string> = {
  en: "finding…",
  es: "buscando…",
};

const EMPTY_COPY: Record<Language, string> = {
  en: "Finish a word to see rhymes.",
  es: "Termina una palabra para ver rimas.",
};

const ERROR_COPY: Record<Language, string> = {
  en: "Lost the connection.",
  es: "Se perdió la conexión.",
};

const EXPLORE_COPY: Record<Language, string> = {
  en: "Explore deeper",
  es: "Explorar más",
};

const EMPTY_RHYMES_COPY: Record<
  Language,
  Record<ClientRhymeMode, { message: string; nudge: string }>
> = {
  en: {
    perfect: { message: "No perfect rhymes.", nudge: "Try Near?" },
    near: { message: "Nothing near here.", nudge: "" },
  },
  es: {
    perfect: { message: "Sin rimas consonantes.", nudge: "¿Probar asonantes?" },
    near: { message: "Sin rimas asonantes.", nudge: "" },
  },
};

export function RhymeSuggestionStrip({
  status,
  result,
  rhymeMode,
  language,
  onRequestModeChange,
  onInsertWord,
  onOpenExplorer,
}: RhymeSuggestionStripProps) {
  const isLoading = status === "loading";
  const target = result?.targetWord ?? null;
  const items = result?.rhymes ?? [];
  // Labels follow the user's toggle, not the backend's resolved mode —
  // "Perfect" on the toggle pairing with "consonante" here would confuse.
  const activeLanguage = result?.language ?? language;

  return (
    <section
      aria-labelledby="rhyme-strip-heading"
      className="border-t border-dashed border-border/70 pt-3"
    >
      <header className="mb-2 flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <p className="flex items-baseline gap-1.5">
          <span
            id="rhyme-strip-heading"
            className="font-mono text-[10px] font-medium uppercase tracking-[0.22em] text-muted-foreground"
          >
            {HEADING[activeLanguage]}
          </span>
          {target ? (
            <span className="text-[11px] text-muted-foreground">
              · {FOR_COPY[activeLanguage]}{" "}
              <span className="font-medium text-accent">{target}</span>
              <span className="text-muted-foreground/70">
                {" · "}
                {MODE_LABEL[activeLanguage][rhymeMode]}
              </span>
            </span>
          ) : null}
          {isLoading && (
            <span
              aria-live="polite"
              className="text-[10px] italic text-muted-foreground/70"
            >
              {FINDING_COPY[activeLanguage]}
            </span>
          )}
        </p>
        {target ? (
          <button
            type="button"
            onClick={onOpenExplorer}
            className="rounded-sm font-mono text-[10px] uppercase tracking-[0.18em] text-accent underline decoration-accent/30 decoration-dotted underline-offset-[3px] transition-colors duration-150 ease-out hover:text-foreground hover:decoration-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
          >
            {EXPLORE_COPY[activeLanguage]}
          </button>
        ) : null}
      </header>

      {target === null ? (
        <p className="text-[12px] text-muted-foreground">
          {status === "error" ? ERROR_COPY[activeLanguage] : EMPTY_COPY[activeLanguage]}
        </p>
      ) : items.length === 0 ? (
        <EmptyRhymes
          mode={rhymeMode}
          language={activeLanguage}
          onRequestModeChange={onRequestModeChange}
        />
      ) : (
        <ul
          aria-label={`Rhyme suggestions for ${target}`}
          className={cn(
            "flex flex-wrap gap-1.5 transition-opacity duration-200",
            isLoading ? "opacity-40" : "opacity-100",
          )}
        >
          {items.map((r, i) => (
            <li key={`${r.word}-${i}`}>
              <button
                type="button"
                onClick={() => onInsertWord(r.word)}
                title={`${r.type} · ${r.syllables} syllable${r.syllables === 1 ? "" : "s"} — click to insert`}
                className={cn(
                  "group inline-flex items-baseline gap-1.5 rounded-full border border-border bg-surface px-2.5 py-1",
                  "transition-colors duration-150 ease-out",
                  "hover:border-accent/50 hover:bg-accent-muted/50",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40",
                )}
              >
                <span className="text-[13px] font-medium text-foreground group-hover:text-accent">
                  {r.word}
                </span>
                <span className="font-mono text-[9px] tabular-nums text-muted-foreground">
                  {r.syllables}
                </span>
                <span
                  aria-label={r.type}
                  className="text-[10px] text-muted-foreground"
                >
                  {RHYME_DEGREE[r.type] ?? "·"}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

interface EmptyRhymesProps {
  mode: ClientRhymeMode;
  language: Language;
  onRequestModeChange: (mode: ClientRhymeMode) => void;
}

function EmptyRhymes({ mode, language, onRequestModeChange }: EmptyRhymesProps) {
  const copy = EMPTY_RHYMES_COPY[language][mode];
  return (
    <p className="text-[12px] text-muted-foreground">
      {copy.message}
      {mode === "perfect" ? (
        <>
          {" "}
          <button
            type="button"
            onClick={() => onRequestModeChange("near")}
            className="rounded-sm text-accent underline decoration-accent/30 decoration-dotted underline-offset-[3px] transition-colors duration-150 ease-out hover:text-foreground hover:decoration-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
          >
            {copy.nudge}
          </button>
        </>
      ) : null}
    </p>
  );
}
