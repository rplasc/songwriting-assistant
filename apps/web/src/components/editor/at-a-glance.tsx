import {
  AT_A_GLANCE_HEADING,
  CADENCE_LABEL,
  LINE_COUNT_LABEL,
  SCHEME_LABEL,
  SECTION_COUNT_LABEL,
  SYLLABLE_COUNT_LABEL,
  VARIANCE_LABEL,
} from "@/features/draft-analysis/draft-analysis-copy";
import type { DraftAnalysis } from "@/features/draft-analysis/draft-analysis-types";
import type { Language } from "@/features/language/language-types";

interface AtAGlanceProps {
  analysis: DraftAnalysis;
  language: Language;
}

/** Most frequent non-null rhyme scheme across sections, else em dash. */
function dominantScheme(analysis: DraftAnalysis): string {
  const freq = new Map<string, number>();
  for (const s of analysis.sections) {
    if (s.rhymeScheme) freq.set(s.rhymeScheme, (freq.get(s.rhymeScheme) ?? 0) + 1);
  }
  let best: string | null = null;
  let bestCount = 0;
  for (const [scheme, count] of freq) {
    if (count > bestCount) {
      best = scheme;
      bestCount = count;
    }
  }
  return best ?? "—";
}

function sharedCadence(analysis: DraftAnalysis): string {
  const classes = new Set(analysis.sections.map((s) => s.cadenceClass));
  if (classes.size === 1) return analysis.sections[0]?.cadenceClass ?? "—";
  return "mixed";
}

function maxVariance(analysis: DraftAnalysis): string {
  if (analysis.sections.length === 0) return "—";
  return Math.max(...analysis.sections.map((s) => s.syllableVariance)).toFixed(2);
}

export function AtAGlance({ analysis, language }: AtAGlanceProps) {
  const cells: Array<[string, string]> = [
    [capitalize(SECTION_COUNT_LABEL[language]), String(analysis.summary.sectionCount)],
    [capitalize(LINE_COUNT_LABEL[language]), String(analysis.summary.lineCount)],
    [capitalize(SYLLABLE_COUNT_LABEL[language]), String(analysis.summary.totalSyllables)],
    [SCHEME_LABEL[language], dominantScheme(analysis)],
    [CADENCE_LABEL[language], sharedCadence(analysis)],
    [VARIANCE_LABEL[language], maxVariance(analysis)],
  ];

  return (
    <section aria-labelledby="at-a-glance-heading">
      <h3
        id="at-a-glance-heading"
        className="mb-2 font-mono text-[10px] font-medium uppercase tracking-[0.22em] text-muted-foreground"
      >
        {AT_A_GLANCE_HEADING[language]}
      </h3>
      <dl className="grid grid-cols-2 gap-x-6 gap-y-1.5">
        {cells.map(([label, value]) => (
          <div
            key={label}
            className="flex items-baseline justify-between gap-2 border-b border-dotted border-border/60 pb-1"
          >
            <dt className="text-[11px] text-muted-foreground">{label}</dt>
            <dd className="font-mono text-[11px] font-medium text-foreground">
              {value}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

function capitalize(s: string): string {
  return s.length > 0 ? s[0].toUpperCase() + s.slice(1) : s;
}
