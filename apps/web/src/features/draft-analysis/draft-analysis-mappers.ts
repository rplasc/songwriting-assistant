import { coerceLanguage } from "@/features/language/language-types";
import type {
  CapabilityLevel,
  DraftAnalysis,
  DraftAnalysisCapabilities,
  DraftAnalysisSectionResult,
  DraftAnalysisSummary,
} from "./draft-analysis-types";

interface ServerCapabilities {
  rhyme_scheme?: string;
  cadence_patterns?: string;
  stress_hints?: string;
  repetition?: string;
  mixed_language?: string;
}

interface ServerSection {
  id: string;
  label: string | null;
  line_start: number;
  line_end: number;
  line_count: number;
  rhyme_scheme: string | null;
  rhyme_scheme_confidence: number | null;
  syllable_pattern: number[];
  syllable_variance: number;
  cadence_class: string;
  repetition_signals: unknown[];
}

interface ServerSummary {
  section_count: number;
  line_count: number;
  total_syllables: number;
  notable_patterns: string[];
}

export interface ServerDraftAnalysisPayload {
  draft_id: string | null;
  revision_hash: string;
  analysis_status: string;
  analyzed_at: string;
  analysis: {
    language: string;
    title: string | null;
    summary: ServerSummary;
    sections: ServerSection[];
    insights: unknown[];
    capabilities: ServerCapabilities;
  };
  meta: {
    request_id?: string;
    latency_ms: number;
  };
}

const CAPABILITY_VALUES: ReadonlyArray<CapabilityLevel> = [
  "full",
  "partial",
  "unsupported",
];

function coerceCapability(value: unknown): CapabilityLevel {
  return typeof value === "string" &&
    (CAPABILITY_VALUES as readonly string[]).includes(value)
    ? (value as CapabilityLevel)
    : "unsupported";
}

function toCapabilities(s: ServerCapabilities): DraftAnalysisCapabilities {
  return {
    rhymeScheme: coerceCapability(s.rhyme_scheme),
    cadencePatterns: coerceCapability(s.cadence_patterns),
    stressHints: coerceCapability(s.stress_hints),
    repetition: coerceCapability(s.repetition),
    mixedLanguage: coerceCapability(s.mixed_language),
  };
}

function toSummary(s: ServerSummary | undefined): DraftAnalysisSummary {
  return {
    sectionCount: s?.section_count ?? 0,
    lineCount: s?.line_count ?? 0,
    totalSyllables: s?.total_syllables ?? 0,
    notablePatterns: s?.notable_patterns ?? [],
  };
}

function toSection(s: ServerSection): DraftAnalysisSectionResult {
  return {
    id: s.id,
    label: s.label,
    lineStart: s.line_start,
    lineEnd: s.line_end,
    lineCount: s.line_count,
    rhymeScheme: s.rhyme_scheme,
    rhymeSchemeConfidence: s.rhyme_scheme_confidence,
    syllablePattern: s.syllable_pattern ?? [],
    syllableVariance: s.syllable_variance,
    cadenceClass: s.cadence_class,
    repetitionSignals: s.repetition_signals ?? [],
  };
}

export function toDraftAnalysis(
  payload: ServerDraftAnalysisPayload,
): DraftAnalysis {
  const serverStatus =
    payload.analysis_status === "fresh" ? "fresh" : "unsupported";
  return {
    draftId: payload.draft_id,
    revisionHash: payload.revision_hash,
    language: coerceLanguage(payload.analysis?.language),
    title: payload.analysis?.title ?? null,
    summary: toSummary(payload.analysis?.summary),
    sections: (payload.analysis?.sections ?? []).map(toSection),
    capabilities: toCapabilities(payload.analysis?.capabilities ?? {}),
    analyzedAt: payload.analyzed_at,
    latencyMs: payload.meta?.latency_ms ?? 0,
    serverStatus,
  };
}
