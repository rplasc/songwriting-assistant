"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import {
  CADENCE_LABEL,
  CONFIDENCE_LABEL,
  NO_SECTIONS_COPY,
  REPETITION_LABEL,
  RHYME_SCHEME_CONFIDENCE_LABEL,
  SECTIONS_HEADING,
  SYLLABLES_LABEL,
  VARIANCE_LABEL,
} from "@/features/draft-analysis/draft-analysis-copy";
import type { DraftAnalysisSectionResult } from "@/features/draft-analysis/draft-analysis-types";
import type { Language } from "@/features/language/language-types";
import { InsightJumpLink } from "./insight-jump-link";

interface Props {
  sections: DraftAnalysisSectionResult[];
  language: Language;
  onJump: (lineStart: number, lineEnd: number) => void;
}

export function SectionAnalysisList({ sections, language, onJump }: Props) {
  const [expandedId, setExpandedId] = useState<string | null>(
    sections[0]?.id ?? null,
  );

  return (
    <section aria-labelledby="draft-analysis-sections-heading">
      <h3
        id="draft-analysis-sections-heading"
        className="mb-2 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground"
      >
        {SECTIONS_HEADING[language]}
      </h3>
      {sections.length === 0 ? (
        <p className="text-[12px] text-muted-foreground">
          {NO_SECTIONS_COPY[language]}
        </p>
      ) : (
        <ul className="divide-y divide-border/40">
          {sections.map((s) => {
            const isOpen = expandedId === s.id;
            return (
              <li key={s.id} className="py-2 first:pt-0 last:pb-0">
                <button
                  type="button"
                  aria-expanded={isOpen}
                  onClick={() => setExpandedId(isOpen ? null : s.id)}
                  className="flex w-full items-baseline justify-between gap-2 rounded-sm py-0.5 text-left hover:bg-surface-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
                >
                  <span className="text-[12px] font-medium text-foreground">
                    {s.label ?? `${s.lineStart}–${s.lineEnd}`}
                  </span>
                  <span className="flex shrink-0 items-center gap-2 text-muted-foreground">
                    {s.rhymeScheme ? (
                      <span className="text-[10px] uppercase tracking-widest">
                        {s.rhymeScheme}
                      </span>
                    ) : null}
                    <span aria-hidden className="text-[11px]">
                      {isOpen ? "−" : "+"}
                    </span>
                  </span>
                </button>
                {isOpen ? (
                  <div className="space-y-1.5 pt-1.5 text-[11px] text-muted-foreground">
                    <Row label={CADENCE_LABEL[language]} value={s.cadenceClass} />
                    <Row
                      label={SYLLABLES_LABEL[language]}
                      value={
                        s.syllablePattern.length > 0
                          ? s.syllablePattern.join(" · ")
                          : "—"
                      }
                    />
                    <Row label={VARIANCE_LABEL[language]} value={s.syllableVariance.toFixed(2)} />
                    {s.rhymeSchemeConfidence !== null ? (
                      <Row
                        label={CONFIDENCE_LABEL[language]}
                        value={RHYME_SCHEME_CONFIDENCE_LABEL[s.rhymeSchemeConfidence][language]}
                      />
                    ) : null}
                    {s.repetitionSignals.length > 0 ? (
                      <Row
                        label={REPETITION_LABEL[language]}
                        value={String(s.repetitionSignals.length)}
                      />
                    ) : null}
                    <div className="pt-1">
                      <InsightJumpLink
                        lineStart={s.lineStart}
                        lineEnd={s.lineEnd}
                        language={language}
                        onJump={onJump}
                      />
                    </div>
                  </div>
                ) : null}
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}

interface RowProps {
  label: string;
  value: string;
}

function Row({ label, value }: RowProps) {
  return (
    <div className={cn("flex justify-between gap-3")}>
      <span className="text-[10px] uppercase tracking-wider text-muted-foreground/70">
        {label}
      </span>
      <span className="text-foreground/80">{value}</span>
    </div>
  );
}
