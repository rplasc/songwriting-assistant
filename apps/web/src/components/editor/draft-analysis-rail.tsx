"use client";

import { useEffect, useRef, useState } from "react";
import {
  COLLAPSE_LABEL,
  EMPTY_DRAFT_COPY,
  ERROR_HINT,
  EXPAND_LABEL,
  LOADING_COPY,
  RAIL_TITLE,
  REFRESH_LABEL,
  STALE_HINT,
  STANZAS_HEADING,
} from "@/features/draft-analysis/draft-analysis-copy";
import type {
  DraftAnalysis,
  DraftAnalysisStatus,
} from "@/features/draft-analysis/draft-analysis-types";
import type { Language } from "@/features/language/language-types";
import type { StanzaRange } from "@/features/structure/structure-types";
import { AnalysisFreshnessBadge } from "./analysis-freshness-badge";
import { DraftAnalysisSummary } from "./draft-analysis-summary";
import { SectionAnalysisList } from "./section-analysis-list";
import { SectionLabelMenu } from "./section-label-menu";

const STORAGE_KEY = "songwriting-assistant.draft-analysis-rail.collapsed";

interface Props {
  status: DraftAnalysisStatus;
  analysis: DraftAnalysis | null;
  error: string | null;
  language: Language;
  stanzas: StanzaRange[];
  labelFor: (range: StanzaRange) => string | null;
  onAssignLabel: (range: StanzaRange, label: string) => void;
  onClearLabel: (range: StanzaRange) => void;
  onRefresh: () => void;
  onJump: (lineStart: number, lineEnd: number) => void;
}

export function DraftAnalysisRail({
  status,
  analysis,
  error,
  language,
  stanzas,
  labelFor,
  onAssignLabel,
  onClearLabel,
  onRefresh,
  onJump,
}: Props) {
  const [collapsed, setCollapsed] = useState(false);
  const isFirstRender = useRef(true);

  // Read persisted preference after mount — must run client-side only to
  // avoid a server/client hydration mismatch.
  useEffect(() => {
    try {
      if (window.localStorage.getItem(STORAGE_KEY) === "1") setCollapsed(true);
    } catch {
      // localStorage unavailable — ignore.
    }
  }, []);

  // Persist preference whenever the user changes it. The isFirstRender guard
  // prevents overwriting the stored value on mount before the read above runs.
  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }
    try {
      window.localStorage.setItem(STORAGE_KEY, collapsed ? "1" : "0");
    } catch {
      // localStorage unavailable — ignore.
    }
  }, [collapsed]);

  const isLoading = status === "loading";

  return (
    <aside
      aria-labelledby="draft-analysis-rail-heading"
      className="flex min-w-0 flex-col gap-4 xl:border-l xl:border-border/40 xl:pl-4"
    >
      <header className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <h2
            id="draft-analysis-rail-heading"
            className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground"
          >
            {RAIL_TITLE[language]}
          </h2>
          {!collapsed && (
            <AnalysisFreshnessBadge status={status} language={language} />
          )}
        </div>
        <button
          type="button"
          onClick={() => setCollapsed((v) => !v)}
          aria-label={collapsed ? EXPAND_LABEL[language] : COLLAPSE_LABEL[language]}
          title={collapsed ? EXPAND_LABEL[language] : COLLAPSE_LABEL[language]}
          className="-mr-1 px-1.5 py-0.5 text-[12px] text-muted-foreground/50 hover:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
        >
          {collapsed ? "+" : "×"}
        </button>
      </header>

      {!collapsed && (
        <>
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
              <DraftAnalysisSummary analysis={analysis} language={language} />
              <SectionAnalysisList
                sections={analysis.sections}
                language={language}
                onJump={onJump}
              />
            </>
          ) : status === "loading" ? (
            <p
              aria-live="polite"
              className="animate-pulse text-[12px] italic text-muted-foreground/60"
            >
              {LOADING_COPY[language]}
            </p>
          ) : status === "idle" ? (
            <p className="text-[12px] text-muted-foreground">
              {EMPTY_DRAFT_COPY[language]}
            </p>
          ) : null}

          {stanzas.length > 0 ? (
            <section>
              <h3 className="mb-2 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                {STANZAS_HEADING[language]} · {stanzas.length}
              </h3>
              <ul className="space-y-1.5">
                {stanzas.map((range) => (
                  <li
                    key={`${range.lineStart}-${range.lineEnd}`}
                    className="flex items-center justify-between gap-2"
                  >
                    <button
                      type="button"
                      onClick={() => onJump(range.lineStart, range.lineEnd)}
                      className="rounded-sm text-[11px] text-muted-foreground hover:text-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
                    >
                      {range.lineStart === range.lineEnd
                        ? `Line ${range.lineStart}`
                        : `Lines ${range.lineStart}–${range.lineEnd}`}
                    </button>
                    <SectionLabelMenu
                      range={range}
                      label={labelFor(range)}
                      language={language}
                      onAssign={onAssignLabel}
                      onClear={onClearLabel}
                    />
                  </li>
                ))}
              </ul>
            </section>
          ) : null}
        </>
      )}
    </aside>
  );
}
