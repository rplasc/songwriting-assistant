import type { Language } from "@/features/language/language-types";

export type CapabilityLevel = "full" | "partial" | "unsupported";

export const CAPABILITY_KEYS = [
  "rhymeScheme",
  "cadencePatterns",
  "stressHints",
  "repetition",
  "mixedLanguage",
] as const;

export type CapabilityKey = (typeof CAPABILITY_KEYS)[number];

export type DraftAnalysisCapabilities = Record<CapabilityKey, CapabilityLevel>;

export interface DraftAnalysisSummary {
  sectionCount: number;
  lineCount: number;
  totalSyllables: number;
  notablePatterns: string[];
}

export interface DraftAnalysisSectionResult {
  id: string;
  label: string | null;
  lineStart: number;
  lineEnd: number;
  lineCount: number;
  rhymeScheme: string | null;
  rhymeSchemeConfidence: number | null;
  syllablePattern: number[];
  syllableVariance: number;
  cadenceClass: string;
  repetitionSignals: unknown[];
}

export interface DraftAnalysis {
  draftId: string | null;
  revisionHash: string;
  language: Language;
  title: string | null;
  summary: DraftAnalysisSummary;
  sections: DraftAnalysisSectionResult[];
  capabilities: DraftAnalysisCapabilities;
  analyzedAt: string;
  latencyMs: number;
  serverStatus: "fresh" | "unsupported";
}

export type DraftAnalysisStatus =
  | "idle"
  | "loading"
  | "fresh"
  | "stale"
  | "error"
  | "unsupported";
