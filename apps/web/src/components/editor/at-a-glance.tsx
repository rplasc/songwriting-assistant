import {
  AT_A_GLANCE_CADENCE_NOTE,
  AT_A_GLANCE_HEADING,
  AT_A_GLANCE_SCHEME_NOTE,
  AT_A_GLANCE_SUMMARY,
} from "@/features/draft-analysis/draft-analysis-copy";
import type { DraftAnalysis } from "@/features/draft-analysis/draft-analysis-types";
import type { Language } from "@/features/language/language-types";

interface AtAGlanceProps {
  analysis: DraftAnalysis;
  language: Language;
}

/** Most frequent non-null rhyme scheme across sections, else none. */
function dominantScheme(analysis: DraftAnalysis): string | null {
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
  return best;
}

/** Cadence class shared by every section, when it's a clear signal. */
function sharedCadence(analysis: DraftAnalysis): "consistent" | "varied" | null {
  if (analysis.sections.length === 0) return null;
  const classes = new Set(analysis.sections.map((s) => s.cadenceClass));
  if (classes.size !== 1) return null;
  const shared = analysis.sections[0]?.cadenceClass;
  return shared === "consistent" || shared === "varied" ? shared : null;
}

export function AtAGlance({ analysis, language }: AtAGlanceProps) {
  const { sectionCount, lineCount, totalSyllables } = analysis.summary;
  const scheme = dominantScheme(analysis);
  const cadence = sharedCadence(analysis);

  return (
    <section aria-labelledby="at-a-glance-heading">
      <h3
        id="at-a-glance-heading"
        className="mb-1.5 font-mono text-[10px] font-medium uppercase tracking-[0.22em] text-muted-foreground"
      >
        {AT_A_GLANCE_HEADING[language]}
      </h3>
      <p className="text-[12px] leading-relaxed text-foreground/80">
        {AT_A_GLANCE_SUMMARY[language](sectionCount, lineCount, totalSyllables)}
        {scheme && ` ${AT_A_GLANCE_SCHEME_NOTE[language](scheme)}`}
        {cadence && ` ${AT_A_GLANCE_CADENCE_NOTE[cadence][language]}`}
      </p>
    </section>
  );
}
