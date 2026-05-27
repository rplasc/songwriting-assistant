"use client";

import { cn } from "@/lib/utils";
import {
  DEFAULT_LANGUAGE,
  type Language,
} from "@/features/language/language-types";
import type {
  DraftCompareResult,
  DraftCompareStatus,
} from "@/features/draft-compare/draft-compare-types";
import {
  BASELINE_EXPIRED_COPY,
  BASELINE_FRESH_NOTE,
  BASELINE_MATCHES_COPY,
  BASELINE_NOT_SET_COPY,
  BASELINE_READY_TO_COMPARE_COPY,
  BASELINE_STALE_NOTE,
  CLEAR_BASELINE_LABEL,
  COMPARE_ERROR_COPY,
  COMPARE_HEADING,
  COMPARE_LOADING_COPY,
  COMPARE_NOW_LABEL,
  DELTA_LABEL,
  NO_CHANGES_COPY,
  RECOMPARE_LABEL,
  RESET_BASELINE_LABEL,
  SET_BASELINE_LABEL,
} from "@/features/draft-compare/draft-compare-copy";

interface CompareSummaryCardProps {
  language?: Language;
  status: DraftCompareStatus;
  result: DraftCompareResult | null;
  error: string | null;
  baselineSet: boolean;
  /** True when the current draft revision matches the stored baseline. */
  baselineMatchesCurrent: boolean;
  onSetBaseline: () => void;
  onClearBaseline: () => void;
  onCompare: () => void;
}

export function CompareSummaryCard({
  language = DEFAULT_LANGUAGE,
  status,
  result,
  error,
  baselineSet,
  baselineMatchesCurrent,
  onSetBaseline,
  onClearBaseline,
  onCompare,
}: CompareSummaryCardProps) {
  const isLoading = status === "loading";

  return (
    <section aria-labelledby="compare-summary-heading">
      <header className="mb-1.5 flex flex-wrap items-baseline justify-between gap-x-3 gap-y-0.5">
        <h3
          id="compare-summary-heading"
          className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground"
        >
          {COMPARE_HEADING[language]}
          {baselineSet && (
            <span className="ml-2 normal-case font-normal tracking-normal text-muted-foreground/60">
              ·{" "}
              {baselineMatchesCurrent
                ? BASELINE_FRESH_NOTE[language]
                : BASELINE_STALE_NOTE[language]}
            </span>
          )}
        </h3>
        <div className="flex items-baseline gap-3 text-[11px]">
          {isLoading && (
            <span
              aria-live="polite"
              className="text-muted-foreground/70 italic"
            >
              {COMPARE_LOADING_COPY[language]}
            </span>
          )}
          {!baselineSet ? (
            <TextLink onClick={onSetBaseline} tone="accent">
              {SET_BASELINE_LABEL[language]}
            </TextLink>
          ) : (
            <TextLink onClick={onClearBaseline} tone="muted">
              {CLEAR_BASELINE_LABEL[language]}
            </TextLink>
          )}
        </div>
      </header>

      {!baselineSet && (
        <p className="text-[12px] leading-relaxed text-muted-foreground">
          {BASELINE_NOT_SET_COPY[language]}
        </p>
      )}

      {baselineSet && baselineMatchesCurrent && !result && (
        <p className="text-[12px] leading-relaxed text-muted-foreground">
          {BASELINE_MATCHES_COPY[language]}
        </p>
      )}

      {baselineSet &&
        !baselineMatchesCurrent &&
        !result &&
        status !== "error" &&
        status !== "unavailable" && (
          <p className="text-[12px] leading-relaxed text-muted-foreground">
            {BASELINE_READY_TO_COMPARE_COPY[language]}{" "}
            <TextLink onClick={onCompare} tone="accent" disabled={isLoading}>
              {COMPARE_NOW_LABEL[language]}
            </TextLink>
          </p>
        )}

      {status === "error" && (
        <p role="alert" className="text-[12px] text-muted-foreground">
          {error ?? COMPARE_ERROR_COPY[language]}
        </p>
      )}

      {status === "unavailable" && baselineSet && (
        <p className="text-[12px] leading-relaxed text-muted-foreground">
          {BASELINE_EXPIRED_COPY[language]}{" "}
          <TextLink onClick={onSetBaseline} tone="accent">
            {RESET_BASELINE_LABEL[language]}
          </TextLink>
        </p>
      )}

      {result && (
        <DeltaProse
          result={result}
          language={language}
          isLoading={isLoading}
          canRecompare={!baselineMatchesCurrent}
          onCompare={onCompare}
        />
      )}
    </section>
  );
}

function DeltaProse({
  result,
  language,
  isLoading,
  canRecompare,
  onCompare,
}: {
  result: DraftCompareResult;
  language: Language;
  isLoading: boolean;
  canRecompare: boolean;
  onCompare: () => void;
}) {
  const labels = DELTA_LABEL[language];
  const items: Array<{ key: keyof typeof labels; count: number }> = [
    { key: "motifs", count: result.summary.motifDeltaCount },
    { key: "repetition", count: result.summary.repetitionDeltaCount },
    { key: "sections", count: result.summary.sectionDeltaCount },
    { key: "consistency", count: result.summary.consistencyDeltaCount },
  ];

  const nonZero = items.filter((i) => i.count > 0);

  if (nonZero.length === 0) {
    return (
      <p className="text-[12px] leading-relaxed text-muted-foreground">
        {NO_CHANGES_COPY[language]}{" "}
        {canRecompare && (
          <TextLink onClick={onCompare} tone="muted" disabled={isLoading}>
            {RECOMPARE_LABEL[language]}
          </TextLink>
        )}
      </p>
    );
  }

  // Editorial prose: counts inline with middle-dot separators, accent-tinted
  // numerals so the eye lands on what changed.
  return (
    <p className="text-[12px] leading-relaxed text-foreground">
      {nonZero.map((item, idx) => (
        <span key={item.key}>
          {idx > 0 && (
            <span className="text-muted-foreground/40">{" · "}</span>
          )}
          <span className="font-semibold text-accent tabular-nums">
            {item.count}
          </span>{" "}
          <span className="text-muted-foreground">{labels[item.key]}</span>
        </span>
      ))}
      {canRecompare && (
        <>
          {" · "}
          <TextLink onClick={onCompare} tone="muted" disabled={isLoading}>
            {RECOMPARE_LABEL[language]}
          </TextLink>
        </>
      )}
    </p>
  );
}

function TextLink({
  onClick,
  tone,
  disabled,
  children,
}: {
  onClick: () => void;
  tone: "accent" | "muted";
  disabled?: boolean;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "rounded-sm underline decoration-dotted underline-offset-[3px] transition-colors duration-150 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40 disabled:opacity-50",
        tone === "accent"
          ? "text-accent decoration-accent/30 hover:decoration-accent hover:text-foreground"
          : "text-muted-foreground decoration-muted-foreground/30 hover:text-foreground",
      )}
    >
      {children}
    </button>
  );
}
