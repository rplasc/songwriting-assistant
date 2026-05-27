"use client";

import { cn } from "@/lib/utils";
import {
  DEFAULT_LANGUAGE,
  type Language,
} from "@/features/language/language-types";
import { useAdvancedRhyme } from "@/features/advanced-rhyme/use-advanced-rhyme";
import {
  ADVANCED_RHYME_MODES,
  ADVANCED_RHYME_TARGET_TYPES,
  type AdvancedRhymeItem,
  type AdvancedRhymeMode,
  type AdvancedRhymeTargetType,
  type RhymeConfidence,
} from "@/features/advanced-rhyme/advanced-rhyme-types";
import {
  CAPABILITY_PARTIAL_COPY,
  CAPABILITY_UNSUPPORTED_COPY,
  CLOSE_LABEL,
  CONFIDENCE_LABEL,
  EMPTY_COPY,
  ERROR_COPY,
  EVIDENCE_LABEL,
  FAMILY_LABEL,
  LOADING_COPY,
  MODE_HEADER,
  MODE_LABEL,
  NO_RESULTS_COPY,
  PANEL_TITLE,
  TARGET_TYPE_HEADER,
  TARGET_TYPE_LABEL,
} from "@/features/advanced-rhyme/advanced-rhyme-copy";

interface AdvancedRhymeExplorerProps {
  activeLine: string;
  language?: Language;
  /** When false, the explorer is mounted but quiet (no fetches). */
  enabled: boolean;
  onClose?: () => void;
}

const CONFIDENCE_DOT: Record<RhymeConfidence, string> = {
  high: "●",
  medium: "◐",
  low: "○",
};

// English and Spanish each get a curated mode shortlist — the full union is
// allowed by the API but presenting all five everywhere creates UX noise.
const MODE_OPTIONS: Record<Language, AdvancedRhymeMode[]> = {
  en: ["perfect", "near", "multisyllabic"],
  es: ["consonant", "assonant", "multisyllabic"],
};

export function AdvancedRhymeExplorer({
  activeLine,
  language = DEFAULT_LANGUAGE,
  enabled,
  onClose,
}: AdvancedRhymeExplorerProps) {
  const {
    status,
    result,
    error,
    mode,
    targetType,
    setMode,
    setTargetType,
    resolvedQuery,
  } = useAdvancedRhyme({
    activeLine,
    language,
    enabled,
  });

  const isLoading = status === "loading";
  const items = result?.items ?? [];
  const capabilityStatus = result?.capabilities.multisyllabic.status;
  const showPartialNote =
    mode === "multisyllabic" && capabilityStatus === "partial";
  const showUnsupportedNote =
    mode === "multisyllabic" && capabilityStatus === "unsupported";

  return (
    <section
      className="rounded-md border border-border bg-surface px-4 py-3.5"
      aria-labelledby="advanced-rhyme-explorer-heading"
    >
      <header className="mb-3 flex flex-wrap items-center justify-between gap-x-2 gap-y-1">
        <h2
          id="advanced-rhyme-explorer-heading"
          className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground"
        >
          {PANEL_TITLE[language]}
        </h2>
        <div className="flex items-center gap-2">
          {isLoading && (
            <span
              aria-live="polite"
              className="text-[10px] text-muted-foreground/70 italic"
            >
              {LOADING_COPY[language]}
            </span>
          )}
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              className="rounded-sm text-[11px] text-muted-foreground underline decoration-muted-foreground/30 decoration-dotted underline-offset-[3px] transition-colors duration-150 ease-out hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
            >
              {CLOSE_LABEL[language]}
            </button>
          )}
        </div>
      </header>

      <div className="mb-3 flex flex-col gap-2">
        <ToggleRow
          label={TARGET_TYPE_HEADER[language]}
          value={targetType}
          options={ADVANCED_RHYME_TARGET_TYPES}
          labels={TARGET_TYPE_LABEL[language]}
          onChange={(next) => setTargetType(next)}
        />
        <ToggleRow
          label={MODE_HEADER[language]}
          value={mode}
          options={MODE_OPTIONS[language] ?? ADVANCED_RHYME_MODES}
          labels={MODE_LABEL[language]}
          onChange={(next) => setMode(next)}
        />
      </div>

      {showPartialNote && (
        <p className="mb-2 text-[11px] text-muted-foreground">
          {CAPABILITY_PARTIAL_COPY[language]}
        </p>
      )}
      {showUnsupportedNote && (
        <p className="mb-2 text-[11px] text-muted-foreground">
          {CAPABILITY_UNSUPPORTED_COPY[language]}
        </p>
      )}

      {!resolvedQuery ? (
        <p className="text-sm text-muted-foreground">{EMPTY_COPY[language]}</p>
      ) : status === "error" ? (
        <p className="text-sm text-muted-foreground">{ERROR_COPY[language]}</p>
      ) : items.length === 0 && status !== "loading" ? (
        <p className="text-sm text-muted-foreground">
          {NO_RESULTS_COPY[language]}
        </p>
      ) : (
        <ul
          aria-label={`Advanced rhyme suggestions for ${resolvedQuery}`}
          className={cn(
            "flex max-h-72 flex-col overflow-y-auto transition-opacity duration-200",
            isLoading ? "opacity-40" : "opacity-100",
          )}
        >
          {items.map((item) => (
            <ExplorerItem key={item.id} item={item} language={language} />
          ))}
        </ul>
      )}

      {error && (
        <p className="mt-2 text-[11px] text-muted-foreground/70" role="status">
          {error}
        </p>
      )}
    </section>
  );
}

function ExplorerItem({
  item,
  language,
}: {
  item: AdvancedRhymeItem;
  language: Language;
}) {
  const familyLabel = item.rhymeFamily
    ? FAMILY_LABEL[language][item.rhymeFamily]
    : null;
  const evidenceLabel = item.evidenceTags[0]
    ? EVIDENCE_LABEL[language][item.evidenceTags[0]]
    : null;
  const whyParts = [familyLabel, evidenceLabel].filter(
    (s): s is string => s !== null && s.length > 0,
  );
  const why = whyParts.join(" · ");
  return (
    <li
      className="group flex items-baseline justify-between gap-3 rounded px-1.5 py-1 hover:bg-surface-muted"
      title={item.matchedSpan ?? undefined}
    >
      <div className="min-w-0 flex-1">
        <span className="text-sm font-medium text-foreground">{item.word}</span>
        {why && (
          <span className="ml-2 text-[10px] text-muted-foreground/80">
            {why}
          </span>
        )}
      </div>
      <span className="flex shrink-0 items-center gap-2 text-muted-foreground">
        <span
          className="text-[10px] tabular-nums"
          aria-label={`${item.syllables} syllables`}
        >
          {item.syllables}
        </span>
        <span
          className="text-[11px]"
          title={item.matchReason ?? CONFIDENCE_LABEL[language][item.confidence]}
          aria-label={CONFIDENCE_LABEL[language][item.confidence]}
        >
          {CONFIDENCE_DOT[item.confidence]}
        </span>
      </span>
    </li>
  );
}

interface ToggleRowProps<T extends string> {
  label: string;
  value: T;
  options: readonly T[];
  labels: Record<T, string>;
  onChange: (value: T) => void;
}

function ToggleRow<T extends string>({
  label,
  value,
  options,
  labels,
  onChange,
}: ToggleRowProps<T>) {
  return (
    <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
      <span className="w-16 shrink-0 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
        {label}
      </span>
      <div
        role="radiogroup"
        aria-label={label}
        className="flex flex-wrap items-baseline gap-x-3 gap-y-0.5"
      >
        {options.map((option) => {
          const active = option === value;
          return (
            <button
              key={option}
              type="button"
              role="radio"
              aria-checked={active}
              onClick={() => onChange(option)}
              className={cn(
                "rounded-sm text-[11px] transition-colors duration-150 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40",
                active
                  ? "text-foreground underline decoration-accent decoration-dotted underline-offset-[3px]"
                  : "text-muted-foreground/70 hover:text-foreground",
              )}
            >
              {labels[option]}
            </button>
          );
        })}
      </div>
    </div>
  );
}
