import {
  CAPABILITY_KEYS,
  type DraftAnalysis,
} from "@/features/draft-analysis/draft-analysis-types";
import {
  LINE_COUNT_LABEL,
  NO_PATTERNS_COPY,
  SECTION_COUNT_LABEL,
  SUMMARY_HEADING,
  SYLLABLE_COUNT_LABEL,
  capabilityLabel,
  capabilityLevelLabel,
} from "@/features/draft-analysis/draft-analysis-copy";
import type { Language } from "@/features/language/language-types";

interface Props {
  analysis: DraftAnalysis;
  language: Language;
}

export function DraftAnalysisSummary({ analysis, language }: Props) {
  const { summary, capabilities } = analysis;
  const limited = CAPABILITY_KEYS.filter((k) => capabilities[k] !== "full");

  return (
    <section aria-labelledby="draft-analysis-summary-heading">
      <h3
        id="draft-analysis-summary-heading"
        className="mb-2 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground"
      >
        {SUMMARY_HEADING[language]}
      </h3>
      <p className="mb-2.5 text-[12px] text-muted-foreground">
        {summary.sectionCount} {SECTION_COUNT_LABEL[language]} &middot;{" "}
        {summary.lineCount} {LINE_COUNT_LABEL[language]} &middot;{" "}
        {summary.totalSyllables} {SYLLABLE_COUNT_LABEL[language]}
      </p>
      {summary.notablePatterns.length > 0 ? (
        <ul className="mb-2.5 space-y-1">
          {summary.notablePatterns.map((pattern) => (
            <li key={pattern} className="text-[12px] text-foreground">
              {pattern}
            </li>
          ))}
        </ul>
      ) : (
        <p className="mb-2.5 text-[12px] text-muted-foreground">
          {NO_PATTERNS_COPY[language]}
        </p>
      )}
      {limited.length > 0 ? (
        <ul className="space-y-0.5 border-t border-border/40 pt-2 text-[11px] text-muted-foreground">
          {limited.map((key) => (
            <li key={key}>
              <span className="text-foreground/70">
                {capabilityLabel(key, language)}:
              </span>{" "}
              {capabilityLevelLabel(capabilities[key], language)}
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
