import type { Language } from "@/features/language/language-types";
import type {
  DraftAnalysis,
  DraftAnalysisSectionResult,
} from "@/features/draft-analysis/draft-analysis-types";
import type { AnalysisResult } from "./analysis-types";

export interface LineNotesInput {
  /** Live WS analysis of the active line. */
  result: AnalysisResult | null;
  analysis: DraftAnalysis | null;
  /** 1-based caret line in the editor. */
  activeLineNumber: number;
  language: Language;
}

/**
 * Margin notes for the active line. Deliberately few and honest: each one
 * is a fact the data actually supports, not vibes.
 */
export function buildLineNotes(input: LineNotesInput): string[] {
  const { result, analysis, activeLineNumber, language } = input;
  if (!result) return [];
  const notes: string[] = [];

  const section = analysis
    ? findSection(analysis, activeLineNumber)
    : null;
  if (section && section.syllablePattern.length >= 2) {
    const modal = modalCount(section.syllablePattern);
    const label = sectionDisplayLabel(section, language);
    const diff = result.totalSyllables - modal;
    if (diff === 0) {
      notes.push(
        language === "es"
          ? `Sigue la cadencia de ${label} (${modal}).`
          : `Matches the ${label} cadence (${modal}).`,
      );
    } else if (Math.abs(diff) >= 2) {
      notes.push(
        language === "es"
          ? `${Math.abs(diff)} sílabas ${diff > 0 ? "más" : "menos"} que lo habitual en ${label} (${modal}).`
          : `Runs ${Math.abs(diff)} ${diff > 0 ? "over" : "under"} the usual ${label} count (${modal}).`,
      );
    }
  }

  if (result.lowConfidence) {
    notes.push(
      language === "es"
        ? "Adiviné con algunas palabras."
        : "I had to guess on a few words.",
    );
  }

  return notes;
}

function findSection(
  analysis: DraftAnalysis,
  line: number,
): DraftAnalysisSectionResult | null {
  return (
    analysis.sections.find((s) => s.lineStart <= line && line <= s.lineEnd) ??
    null
  );
}

/** Most frequent value; earliest wins ties. */
function modalCount(pattern: number[]): number {
  const freq = new Map<number, number>();
  for (const n of pattern) freq.set(n, (freq.get(n) ?? 0) + 1);
  let best = pattern[0];
  let bestCount = 0;
  for (const [value, count] of freq) {
    if (count > bestCount) {
      best = value;
      bestCount = count;
    }
  }
  return best;
}

function sectionDisplayLabel(
  section: DraftAnalysisSectionResult,
  language: Language,
): string {
  if (section.label) return capitalize(section.label);
  return language === "es" ? "la sección" : "the section";
}

function capitalize(s: string): string {
  return s.length > 0 ? s[0].toUpperCase() + s.slice(1) : s;
}
