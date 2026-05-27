import type { Language } from "@/features/language/language-types";
import type {
  CapabilityLevel,
  DraftInsight,
} from "@/features/draft-analysis/draft-analysis-types";

export interface CompareSummary {
  motifDeltaCount: number;
  repetitionDeltaCount: number;
  sectionDeltaCount: number;
  consistencyDeltaCount: number;
  familyCounts: Record<string, number>;
  unmatchedPreviousSectionIds: string[];
  unmatchedCurrentSectionIds: string[];
}

export interface CompareCapabilities {
  compareMotifs: CapabilityLevel;
  compareRepetition: CapabilityLevel;
  compareSections: CapabilityLevel;
  compareConsistency: CapabilityLevel;
}

export interface DraftCompareResult {
  analysisId: string;
  draftId: string | null;
  language: Language;
  title: string | null;
  baseRevisionHash: string;
  targetRevisionHash: string;
  summary: CompareSummary;
  insights: DraftInsight[];
  capabilities: CompareCapabilities;
  latencyMs: number;
}

export type DraftCompareStatus =
  | "idle"
  | "loading"
  | "ready"
  | "error"
  | "unavailable";
