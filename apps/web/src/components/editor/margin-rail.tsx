"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import type {
  AnalysisResult,
  AnalysisStatus,
} from "@/features/analysis/analysis-types";
import {
  AT_A_GLANCE_HEADING,
  COLLAPSE_LABEL,
  EMPTY_DRAFT_COPY,
  ERROR_HINT,
  EXPAND_LABEL,
  FIND_WEAK_LINE_LABEL,
  INSIGHTS_TAB_LABEL,
  LINE_NOTE_HEADING,
  LINE_TAB_LABEL,
  LOADING_COPY,
  NO_LINE_COPY,
  RAIL_TITLE,
  REFRESH_LABEL,
  STALE_HINT,
  STRUCTURE_TAB_LABEL,
  SYLLABLES_ON_LINE_LABEL,
} from "@/features/draft-analysis/draft-analysis-copy";
import type {
  DraftAnalysis,
  DraftAnalysisStatus,
  DraftInsight,
} from "@/features/draft-analysis/draft-analysis-types";
import type {
  DraftCompareResult,
  DraftCompareStatus,
} from "@/features/draft-compare/draft-compare-types";
import type { Language } from "@/features/language/language-types";
import { AnalysisFreshnessBadge } from "./analysis-freshness-badge";
import { AtAGlance } from "./at-a-glance";
import { CompareSummaryCard } from "./compare-summary-card";
import { RevisionInsightList } from "./revision-insight-list";
import { SectionAnalysisList } from "./section-analysis-list";
import { SectionInsertMenu } from "./section-insert-menu";

type RailTab = "line" | "structure" | "insights";

interface MarginRailProps {
  open: boolean;
  onToggle: () => void;
  language: Language;
  // Line tab
  lineStatus: AnalysisStatus;
  lineResult: AnalysisResult | null;
  lineNotes: string[];
  // Structure / insights tabs
  status: DraftAnalysisStatus;
  analysis: DraftAnalysis | null;
  error: string | null;
  onRefresh: () => void;
  onJump: (lineStart: number, lineEnd: number) => void;
  onInsertSection: (label: string) => void;
  // Compare (insights tab)
  compareStatus: DraftCompareStatus;
  compareResult: DraftCompareResult | null;
  compareError: string | null;
  baselineSet: boolean;
  baselineMatchesCurrent: boolean;
  onSetBaseline: () => void;
  onClearBaseline: () => void;
  onCompare: () => void;
}

function firstWeakInsight(analysis: DraftAnalysis | null): DraftInsight | null {
  if (!analysis) return null;
  return (
    analysis.insights.find(
      (i) =>
        (i.severity === "medium" || i.severity === "high") &&
        i.anchor?.lineStart != null,
    ) ?? null
  );
}

export function MarginRail(props: MarginRailProps) {
  const { open, onToggle, language } = props;
  const [tab, setTab] = useState<RailTab>("line");

  if (!open) {
    return (
      <aside
        aria-label={RAIL_TITLE[language]}
        className="hidden flex-col items-center gap-3 border-l border-border/40 pt-1 lg:flex"
      >
        <button
          type="button"
          onClick={onToggle}
          aria-label={EXPAND_LABEL[language]}
          title={EXPAND_LABEL[language]}
          className="px-1.5 py-0.5 text-[13px] text-muted-foreground/60 hover:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
        >
          ‹
        </button>
        <span
          aria-hidden
          className="font-mono text-[9px] uppercase tracking-[0.28em] text-muted-foreground/50 [writing-mode:vertical-rl]"
        >
          {RAIL_TITLE[language]}
        </span>
      </aside>
    );
  }

  const tabs: Array<[RailTab, string]> = [
    ["line", LINE_TAB_LABEL[language]],
    ["structure", STRUCTURE_TAB_LABEL[language]],
    ["insights", INSIGHTS_TAB_LABEL[language]],
  ];

  return (
    <aside
      aria-labelledby="margin-rail-heading"
      className="flex min-w-0 flex-col gap-4 lg:border-l lg:border-border/40 lg:pl-5"
    >
      <header className="flex items-center justify-between gap-2">
        <h2
          id="margin-rail-heading"
          className="font-mono text-[10px] font-medium uppercase tracking-[0.22em] text-muted-foreground"
        >
          {RAIL_TITLE[language]}
        </h2>
        <button
          type="button"
          onClick={onToggle}
          aria-label={COLLAPSE_LABEL[language]}
          title={COLLAPSE_LABEL[language]}
          className="-mr-1 px-1.5 py-0.5 text-[13px] text-muted-foreground/50 hover:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
        >
          ›
        </button>
      </header>

      <div
        role="tablist"
        aria-label={RAIL_TITLE[language]}
        className="flex items-center gap-1 border-b border-border/60"
      >
        {tabs.map(([key, label]) => {
          const active = tab === key;
          return (
            <button
              key={key}
              type="button"
              role="tab"
              id={`margin-rail-tab-${key}`}
              aria-selected={active}
              aria-controls={`margin-rail-panel-${key}`}
              onClick={() => setTab(key)}
              className={cn(
                "-mb-px border-b px-2 pb-1.5 font-mono text-[10px] uppercase tracking-[0.18em]",
                "transition-colors duration-150 ease-out",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40",
                active
                  ? "border-accent text-accent"
                  : "border-transparent text-muted-foreground hover:text-foreground",
              )}
            >
              {label}
            </button>
          );
        })}
      </div>

      <div
        role="tabpanel"
        id={`margin-rail-panel-${tab}`}
        aria-labelledby={`margin-rail-tab-${tab}`}
        className="flex min-w-0 flex-col gap-4"
      >
        {tab === "line" && <LineTab {...props} />}
        {tab === "structure" && <StructureTab {...props} />}
        {tab === "insights" && <InsightsTab {...props} />}
      </div>
    </aside>
  );
}

function LineTab({
  language,
  lineStatus,
  lineResult,
  lineNotes,
  analysis,
  onJump,
}: MarginRailProps) {
  const weak = firstWeakInsight(analysis);
  if (!lineResult) {
    return (
      <p className="text-[12px] text-muted-foreground">
        {lineStatus === "error" ? ERROR_HINT[language] : NO_LINE_COPY[language]}
      </p>
    );
  }
  return (
    <>
      <div
        className={cn(
          "transition-opacity duration-200",
          lineStatus === "loading" ? "opacity-40" : "opacity-100",
        )}
      >
        <div className="flex items-baseline gap-2.5">
          <span className="font-serif text-5xl font-semibold leading-none tracking-tight text-foreground tabular-nums">
            {lineResult.totalSyllables}
          </span>
          <span className="font-serif text-[12px] italic text-muted-foreground">
            {SYLLABLES_ON_LINE_LABEL[language]}
          </span>
        </div>
        {lineResult.tokens.length > 0 && (
          <ul
            aria-label="Syllable breakdown by word"
            className="mt-3 flex flex-wrap gap-1.5"
          >
            {lineResult.tokens.map((t, i) => (
              <li
                key={`${t.text}-${i}`}
                title={t.low_confidence ? "Lower-confidence estimate" : undefined}
                className={cn(
                  "rounded-sm border border-border bg-surface px-1.5 py-0.5 font-mono text-[10px] tracking-wide",
                  t.low_confidence
                    ? "italic text-muted-foreground"
                    : "text-foreground/85",
                )}
              >
                {t.text}·{t.syllables}
                {t.low_confidence ? "?" : ""}
              </li>
            ))}
          </ul>
        )}
      </div>

      {lineNotes.length > 0 && (
        <section aria-labelledby="line-note-heading">
          <h3
            id="line-note-heading"
            className="mb-1.5 font-mono text-[10px] font-medium uppercase tracking-[0.22em] text-muted-foreground"
          >
            {LINE_NOTE_HEADING[language]}
          </h3>
          <ul className="space-y-1">
            {lineNotes.map((note) => (
              <li key={note} className="text-[12px] leading-relaxed text-foreground/80">
                <span aria-hidden className="text-muted-foreground/60">— </span>
                {note}
              </li>
            ))}
          </ul>
        </section>
      )}

      {analysis && (
        <section aria-label={AT_A_GLANCE_HEADING[language]}>
          <AtAGlance analysis={analysis} language={language} />
        </section>
      )}

      {weak && weak.anchor?.lineStart != null && (
        <button
          type="button"
          onClick={() =>
            onJump(weak.anchor!.lineStart!, weak.anchor!.lineEnd ?? weak.anchor!.lineStart!)
          }
          className="self-start text-left text-[12px] font-medium text-accent underline-offset-2 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
        >
          {FIND_WEAK_LINE_LABEL[language]}
        </button>
      )}
    </>
  );
}

function StructureTab({
  language,
  status,
  analysis,
  error,
  onRefresh,
  onJump,
  onInsertSection,
}: MarginRailProps) {
  const isLoading = status === "loading";
  return (
    <>
      <div className="flex items-center justify-between gap-2">
        <AnalysisFreshnessBadge status={status} language={language} />
        <SectionInsertMenu language={language} onInsert={onInsertSection} />
      </div>

      {status === "error" && error ? (
        <p role="alert" className="text-[11px] text-muted-foreground">
          {error} {ERROR_HINT[language]}
        </p>
      ) : null}

      {status === "stale" ? (
        <p className="text-[11px] text-muted-foreground">
          {STALE_HINT[language]}{" "}
          <button
            type="button"
            onClick={onRefresh}
            disabled={isLoading}
            className="text-accent underline-offset-2 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40 disabled:opacity-50"
          >
            {REFRESH_LABEL[language]}
          </button>
        </p>
      ) : null}

      {analysis ? (
        <>
          <AtAGlance analysis={analysis} language={language} />
          <SectionAnalysisList
            sections={analysis.sections}
            language={language}
            onJump={onJump}
          />
        </>
      ) : isLoading ? (
        <p
          aria-live="polite"
          className="animate-pulse text-[12px] italic text-muted-foreground/60"
        >
          {LOADING_COPY[language]}
        </p>
      ) : (
        <p className="text-[12px] text-muted-foreground">
          {EMPTY_DRAFT_COPY[language]}
        </p>
      )}
    </>
  );
}

function InsightsTab({
  language,
  status,
  analysis,
  onJump,
  compareStatus,
  compareResult,
  compareError,
  baselineSet,
  baselineMatchesCurrent,
  onSetBaseline,
  onClearBaseline,
  onCompare,
}: MarginRailProps) {
  if (!analysis) {
    return (
      <p className="text-[12px] text-muted-foreground">
        {status === "loading" ? LOADING_COPY[language] : EMPTY_DRAFT_COPY[language]}
      </p>
    );
  }
  return (
    <>
      <CompareSummaryCard
        language={language}
        status={compareStatus}
        result={compareResult}
        error={compareError}
        baselineSet={baselineSet}
        baselineMatchesCurrent={baselineMatchesCurrent}
        onSetBaseline={onSetBaseline}
        onClearBaseline={onClearBaseline}
        onCompare={onCompare}
      />
      {/* With a fresh compare result, the compare-insights list is the
          actionable surface — showing both would duplicate context. */}
      {compareResult && compareResult.insights.length > 0 ? (
        <RevisionInsightList
          insights={compareResult.insights}
          language={language}
          onJump={onJump}
        />
      ) : analysis.insights.length > 0 ? (
        <RevisionInsightList
          insights={analysis.insights}
          language={language}
          onJump={onJump}
        />
      ) : null}
    </>
  );
}
