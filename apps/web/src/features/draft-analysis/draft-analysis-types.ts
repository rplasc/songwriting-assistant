import type { Language } from "@/features/language/language-types";

export type CapabilityLevel = "full" | "partial" | "unsupported";

export type InsightSeverity = "info" | "low" | "medium" | "high";
export type InsightConfidence = "low" | "medium" | "high";
export type InsightScope = "draft" | "section";
export type AnchorScope = "draft" | "section";

export interface InsightAnchor {
  scope: AnchorScope;
  sectionId: string | null;
  lineStart: number | null;
  lineEnd: number | null;
}

/**
 * The FastAPI evidence union is broad (~19 variants). The client keeps the
 * shape open here so any `kind` renders gracefully — the evidence-reveal
 * component switches on a handful of known kinds and falls back to a key/value
 * list for the rest.
 */
export interface InsightEvidence {
  kind: string;
  [key: string]: unknown;
}

export interface DraftInsight {
  id: string;
  type: string;
  scope: InsightScope;
  target: string | null;
  severity: InsightSeverity;
  message: string;
  evidence: InsightEvidence | null;
  anchor: InsightAnchor | null;
  confidence: InsightConfidence | null;
  hookContext: boolean;
}

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
  insights: DraftInsight[];
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
