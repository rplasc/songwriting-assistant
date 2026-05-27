"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import {
  DEFAULT_LANGUAGE,
  type Language,
} from "@/features/language/language-types";
import type {
  DraftInsight,
  InsightSeverity,
} from "@/features/draft-analysis/draft-analysis-types";
import {
  CONFIDENCE_LABEL,
  DRAFT_ANCHOR_LABEL,
  FILTER_ALL_LABEL,
  FILTER_STRONG_LABEL,
  INSIGHTS_HEADING,
  JUMP_LABEL,
  NO_INSIGHTS_COPY,
  SECTION_ANCHOR_LABEL,
  SEVERITY_LABEL,
  SHOW_LESS_LABEL,
  SHOW_MORE_LABEL,
} from "@/features/draft-analysis/insight-copy";
import { InsightEvidenceReveal } from "./insight-evidence";

interface RevisionInsightListProps {
  insights: DraftInsight[];
  language?: Language;
  /** Optional title override — useful for "current" vs "compare" lists. */
  heading?: string;
  onJump?: (lineStart: number, lineEnd: number) => void;
}

const SEVERITY_ORDER: Record<InsightSeverity, number> = {
  high: 0,
  medium: 1,
  low: 2,
  info: 3,
};

// Mirror the rhyme panel's degree glyphs so the analog/notebook vocabulary
// stays consistent across all of the analysis surfaces.
const SEVERITY_GLYPH: Record<InsightSeverity, string> = {
  high: "●",
  medium: "◐",
  low: "○",
  info: "·",
};

const SEVERITY_TONE: Record<InsightSeverity, string> = {
  high: "text-accent",
  medium: "text-accent/70",
  low: "text-muted-foreground/60",
  info: "text-muted-foreground/40",
};

type FilterMode = "all" | "strong";

const DEFAULT_VISIBLE_LIMIT = 5;

export function RevisionInsightList({
  insights,
  language = DEFAULT_LANGUAGE,
  heading,
  onJump,
}: RevisionInsightListProps) {
  const [filter, setFilter] = useState<FilterMode>("all");
  const [expanded, setExpanded] = useState(false);

  const sorted = (filter === "strong"
    ? insights.filter(
        (i) => i.severity === "high" || i.severity === "medium",
      )
    : insights
  )
    .slice()
    .sort(bySeverityThenScope);

  const visible = expanded ? sorted : sorted.slice(0, DEFAULT_VISIBLE_LIMIT);
  const hidden = sorted.length - visible.length;

  return (
    <section aria-labelledby="revision-insights-heading">
      <header className="mb-2 flex flex-wrap items-baseline justify-between gap-x-3 gap-y-0.5">
        <h3
          id="revision-insights-heading"
          className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground"
        >
          {heading ?? INSIGHTS_HEADING[language]}
          {insights.length > 0 && (
            <span className="ml-1.5 normal-case font-normal tracking-normal text-muted-foreground/60">
              · {insights.length}
            </span>
          )}
        </h3>
        {insights.length > 0 && (
          <div
            role="radiogroup"
            aria-label={INSIGHTS_HEADING[language]}
            className="flex items-baseline gap-2 text-[10px] uppercase tracking-widest"
          >
            <FilterLink
              active={filter === "all"}
              onClick={() => setFilter("all")}
            >
              {FILTER_ALL_LABEL[language]}
            </FilterLink>
            <FilterLink
              active={filter === "strong"}
              onClick={() => setFilter("strong")}
            >
              {FILTER_STRONG_LABEL[language]}
            </FilterLink>
          </div>
        )}
      </header>

      {visible.length === 0 ? (
        <p className="text-[12px] text-muted-foreground">
          {NO_INSIGHTS_COPY[language]}
        </p>
      ) : (
        <>
          <ul className="flex flex-col gap-2">
            {visible.map((insight) => (
              <InsightRow
                key={insight.id}
                insight={insight}
                language={language}
                onJump={onJump}
              />
            ))}
          </ul>
          {(hidden > 0 || expanded) && sorted.length > DEFAULT_VISIBLE_LIMIT && (
            <button
              type="button"
              onClick={() => setExpanded((v) => !v)}
              aria-expanded={expanded}
              className="mt-2 rounded-sm text-[10px] uppercase tracking-widest text-muted-foreground underline decoration-muted-foreground/30 decoration-dotted underline-offset-[3px] hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
            >
              {expanded
                ? SHOW_LESS_LABEL[language]
                : SHOW_MORE_LABEL(hidden)[language]}
            </button>
          )}
        </>
      )}
    </section>
  );
}

function bySeverityThenScope(a: DraftInsight, b: DraftInsight) {
  const sev = SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity];
  if (sev !== 0) return sev;
  // Section insights have actionable anchors; surface them above whole-draft.
  if (a.scope !== b.scope) return a.scope === "section" ? -1 : 1;
  return 0;
}

interface InsightRowProps {
  insight: DraftInsight;
  language: Language;
  onJump?: (lineStart: number, lineEnd: number) => void;
}

function InsightRow({ insight, language, onJump }: InsightRowProps) {
  const anchor = insight.anchor;
  const canJump =
    !!onJump &&
    anchor !== null &&
    anchor.lineStart !== null &&
    anchor.scope === "section";
  const anchorLabel =
    anchor === null
      ? null
      : anchor.scope === "section" && anchor.lineStart !== null
        ? anchor.lineEnd && anchor.lineEnd !== anchor.lineStart
          ? `${SECTION_ANCHOR_LABEL[language]} ${anchor.lineStart}–${anchor.lineEnd}`
          : `${SECTION_ANCHOR_LABEL[language]} ${anchor.lineStart}`
        : DRAFT_ANCHOR_LABEL[language];

  return (
    <li className="flex items-baseline gap-2.5">
      <span
        aria-hidden
        className={cn(
          "shrink-0 select-none text-[11px] leading-snug",
          SEVERITY_TONE[insight.severity],
        )}
        title={SEVERITY_LABEL[language][insight.severity]}
      >
        {SEVERITY_GLYPH[insight.severity]}
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-[12.5px] leading-snug text-foreground">
          {insight.message}
        </p>
        <p className="mt-0.5 flex flex-wrap items-baseline gap-x-2 gap-y-0.5 text-[10px] uppercase tracking-widest text-muted-foreground/70">
          {anchorLabel && <span>{anchorLabel}</span>}
          {insight.confidence && (
            <span>{CONFIDENCE_LABEL[language][insight.confidence]}</span>
          )}
          {canJump && (
            <button
              type="button"
              onClick={() =>
                onJump?.(
                  anchor!.lineStart as number,
                  (anchor!.lineEnd ?? anchor!.lineStart) as number,
                )
              }
              className="rounded-sm normal-case tracking-normal text-accent underline decoration-accent/30 decoration-dotted underline-offset-[3px] hover:decoration-accent hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
            >
              {JUMP_LABEL[language]}
            </button>
          )}
        </p>
        <InsightEvidenceReveal
          evidence={insight.evidence}
          language={language}
        />
      </div>
    </li>
  );
}

function FilterLink({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      role="radio"
      aria-checked={active}
      onClick={onClick}
      className={cn(
        "rounded-sm transition-colors duration-150 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40",
        active
          ? "text-foreground underline decoration-accent decoration-dotted underline-offset-[3px]"
          : "text-muted-foreground/70 hover:text-foreground",
      )}
    >
      {children}
    </button>
  );
}
