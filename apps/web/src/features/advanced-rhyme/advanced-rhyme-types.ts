import type { Language } from "@/features/language/language-types";
import type { CapabilityLevel } from "@/features/draft-analysis/draft-analysis-types";

export const ADVANCED_RHYME_MODES = [
  "perfect",
  "near",
  "consonant",
  "assonant",
  "multisyllabic",
] as const;

export type AdvancedRhymeMode = (typeof ADVANCED_RHYME_MODES)[number];

export const ADVANCED_RHYME_TARGET_TYPES = ["word", "phrase_ending"] as const;
export type AdvancedRhymeTargetType =
  (typeof ADVANCED_RHYME_TARGET_TYPES)[number];

export type RhymeFamily =
  | "perfect"
  | "multisyllabic"
  | "near"
  | "assonant"
  | "consonant";

export type RhymeConfidence = "high" | "medium" | "low";

export const EVIDENCE_TAGS = [
  "shared_stressed_ending",
  "shared_vowel_pattern",
  "shared_consonant_tail",
  "phrase_ending_match",
  "heuristic_fallback",
  "multisyllabic_key_match",
] as const;

export type EvidenceTag = (typeof EVIDENCE_TAGS)[number];

export type CapabilityReasonCode =
  | "language_unsupported"
  | "model_unavailable"
  | "insufficient_lines"
  | "option_not_requested"
  | "language_partial_support";

export interface AdvancedRhymeItem {
  id: string;
  word: string;
  syllables: number;
  rhymeType: string;
  rhymeFamily: RhymeFamily | null;
  confidence: RhymeConfidence;
  evidenceTags: EvidenceTag[];
  matchedSpan: string | null;
  matchReason: string | null;
  score: number;
}

export interface AdvancedRhymeCapabilities {
  multisyllabic: {
    status: CapabilityLevel;
    reasonCode: CapabilityReasonCode | null;
  };
}

export interface AdvancedRhymeResult {
  query: string;
  targetType: AdvancedRhymeTargetType;
  mode: AdvancedRhymeMode;
  language: Language;
  pronunciationsFound: boolean;
  items: AdvancedRhymeItem[];
  familyCounts: Record<string, number>;
  capabilities: AdvancedRhymeCapabilities;
  latencyMs: number;
}

export type AdvancedRhymeStatus =
  | "idle"
  | "loading"
  | "ready"
  | "error"
  | "unsupported";
