import { cn } from "@/lib/utils";
import type {
  AnalysisResult,
  AnalysisStatus,
} from "@/features/analysis/analysis-types";
import {
  DEFAULT_RHYME_MODE,
  type ClientRhymeMode,
} from "@/features/analysis/rhyme-modes";
import {
  DEFAULT_LANGUAGE,
  type Language,
} from "@/features/language/language-types";

interface RhymePanelProps {
  status: AnalysisStatus;
  result: AnalysisResult | null;
  rhymeMode?: ClientRhymeMode;
  language?: Language;
  onRequestModeChange?: (mode: ClientRhymeMode) => void;
  onOpenExplorer?: () => void;
  explorerOpen?: boolean;
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

const FOR_COPY: Record<Language, string> = {
  en: "for",
  es: "para",
};

const EXPLORE_COPY: Record<Language, string> = {
  en: "Explore deeper",
  es: "Explorar más",
};

export function RhymePanel({
  status,
  result,
  rhymeMode = DEFAULT_RHYME_MODE,
  language = DEFAULT_LANGUAGE,
  onRequestModeChange,
  onOpenExplorer,
  explorerOpen = false,
}: RhymePanelProps) {
  const isLoading = status === "loading";
  const target = result?.targetWord ?? null;
  const items = result?.rhymes ?? [];
  const hasRhymes = target !== null;
  // Anchor labels and the empty-state affordance to the user's toggle, not the
  // backend's resolved mode. Otherwise "Perfect" on the toggle pairs with
  // "consonante" in the panel — same idea, different vocabulary, confusing.
  const activeMode = rhymeMode;
  const activeLanguage = result?.language ?? language;

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
        <div className="flex items-center gap-2">
          {isLoading && (
            <span aria-live="polite" className="text-[10px] text-muted-foreground/70 italic">
              {FINDING_COPY[activeLanguage]}
            </span>
          )}
          {hasRhymes && onOpenExplorer && !explorerOpen && (
            <button
              type="button"
              onClick={onOpenExplorer}
              className="rounded-sm text-[10px] uppercase tracking-widest text-accent underline decoration-accent/30 decoration-dotted underline-offset-[3px] transition-colors duration-150 ease-out hover:decoration-accent hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
            >
              {EXPLORE_COPY[activeLanguage]}
            </button>
          )}
        </div>
      </header>

      {!hasRhymes ? (
        <p className="text-sm text-muted-foreground">
          {status === "error"
            ? ERROR_COPY[activeLanguage]
            : EMPTY_COPY[activeLanguage]}
        </p>
      ) : (
        <div
          className={cn(
            "flex flex-col gap-2.5 transition-opacity duration-200",
            isLoading ? "opacity-40" : "opacity-100",
          )}
        >
          <p className="text-[11px] text-muted-foreground">
            {FOR_COPY[activeLanguage]}{" "}
            <span className="font-semibold text-accent tracking-wide">
              {target}
            </span>
            <span className="text-muted-foreground/70">
              {" · "}
              {MODE_LABEL[activeLanguage][activeMode]}
            </span>
          </p>
          {items.length === 0 ? (
            <EmptyRhymes
              mode={activeMode}
              language={activeLanguage}
              onRequestModeChange={onRequestModeChange}
            />
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

interface EmptyRhymesProps {
  mode: ClientRhymeMode;
  language: Language;
  onRequestModeChange?: (mode: ClientRhymeMode) => void;
}

const EMPTY_RHYMES_COPY: Record<
  Language,
  Record<ClientRhymeMode, { message: string; nudge: string }>
> = {
  en: {
    perfect: { message: "No perfect rhymes.", nudge: "Try Near?" },
    near: { message: "Nothing near here.", nudge: "" },
  },
  es: {
    perfect: {
      message: "Sin rimas consonantes.",
      nudge: "¿Probar asonantes?",
    },
    near: { message: "Sin rimas asonantes.", nudge: "" },
  },
};

function EmptyRhymes({ mode, language, onRequestModeChange }: EmptyRhymesProps) {
  const copy = EMPTY_RHYMES_COPY[language][mode];
  const canNudge = mode === "perfect" && Boolean(onRequestModeChange);

  return (
    <p className="text-sm text-muted-foreground">
      {copy.message}
      {canNudge ? (
        <>
          {" "}
          <button
            type="button"
            onClick={() => onRequestModeChange?.("near")}
            className="rounded-sm text-accent underline decoration-accent/30 decoration-dotted underline-offset-[3px] transition-colors duration-150 ease-out hover:decoration-accent hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
          >
            {copy.nudge}
          </button>
        </>
      ) : null}
    </p>
  );
}
