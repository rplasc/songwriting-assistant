import {
  AnchorScope,
  CapabilityKey,
  CapabilityReasonCode,
  CapabilityStatus,
  InsightConfidence,
  InsightSeverity,
} from '../../common/enums/capability.enum';
import { Language, RhymeTargetType } from '../../common/enums/language.enum';

export const RHYME_FAMILIES = [
  'perfect',
  'multisyllabic',
  'near',
  'assonant',
  'consonant',
] as const;
export type RhymeFamily = (typeof RHYME_FAMILIES)[number];

export const RHYME_CONFIDENCES = ['high', 'medium', 'low'] as const;
export type RhymeConfidence = (typeof RHYME_CONFIDENCES)[number];

export const EVIDENCE_TAGS = [
  'shared_stressed_ending',
  'shared_vowel_pattern',
  'shared_consonant_tail',
  'phrase_ending_match',
  'heuristic_fallback',
  'multisyllabic_key_match',
] as const;
export type EvidenceTag = (typeof EVIDENCE_TAGS)[number];

export interface TokenAnalysis {
  text: string;
  normalized: string;
  syllables: number;
  pronunciation_found: boolean;
  source?: 'dictionary' | 'heuristic';
  low_confidence?: boolean;
}

export const INNER_RHYME_TYPES = ['perfect', 'near'] as const;
export type InnerRhymeType = (typeof INNER_RHYME_TYPES)[number];

export interface InnerRhymeOccurrence {
  line_index: number;
  word_index: number;
  char_start: number;
  char_end: number;
  text: string;
  normalized: string;
}

export interface InnerRhymeGroup {
  id: string;
  rhyme_type: InnerRhymeType;
  confidence: RhymeConfidence;
  rhyme_key: string;
  occurrences: InnerRhymeOccurrence[];
}

export interface LastWord {
  text: string;
  normalized: string;
  pronunciation_found: boolean;
  syllables?: number | null;
  source?: 'dictionary' | 'heuristic' | null;
  low_confidence?: boolean;
}

export interface LineAnalysisResponse {
  line: string;
  normalized_line: string;
  language: Language;
  total_syllables: number;
  tokens: TokenAnalysis[];
  last_word: LastWord | null;
  inner_rhymes?: InnerRhymeGroup[];
}

export interface RhymeCandidate {
  word: string;
  syllables: number;
  rhyme_type: string;
  score: number;
  match_reason?: string | null;
  // Phase 5.5 productization fields. Older callers (the default WS analyze
  // path) ignore them; the explore path forwards them to the client.
  rhyme_family?: RhymeFamily | null;
  matched_span?: string | null;
  id?: string;
  confidence?: RhymeConfidence;
  evidence_tags?: EvidenceTag[];
}

export interface RhymeMeta {
  limit: number;
  mode: string;
  include_near: boolean;
}

export interface RhymeSummary {
  family_counts: Record<string, number>;
  returned: number;
  requested_limit: number;
}

export interface UpstreamRhymeCapabilities {
  // FastAPI returns a dict keyed by capability name; multisyllabic is the
  // one Phase 5.5 cares about, others may appear later.
  multisyllabic?: UpstreamCapability;
  [key: string]: UpstreamCapability | undefined;
}

export interface RhymeResponse {
  // Legacy fields kept for the existing WS path. The explore path also
  // returns `query`, `target_type`, `summary`, and `capabilities`.
  word?: string;
  normalized_word?: string | null;
  query?: string;
  normalized_query?: string | null;
  language: Language;
  target_type?: RhymeTargetType;
  mode?: string;
  pronunciations_found: boolean;
  rhymes: RhymeCandidate[];
  meta?: RhymeMeta;
  summary?: RhymeSummary;
  capabilities?: UpstreamRhymeCapabilities;
}

export interface UpstreamCapability {
  status: CapabilityStatus;
  reason_code: CapabilityReasonCode | null;
}

export type DraftAnalysisCapabilities = Record<CapabilityKey, UpstreamCapability>;

export interface DraftAnalysisSummary {
  section_count: number;
  line_count: number;
  total_syllables: number;
  notable_patterns: string[];
  motifs?: string[];
  insight_count?: number;
  family_counts?: Record<string, number>;
}

export type UpstreamRhymeConfidence = 'full' | 'partial' | null;

export interface DraftAnalysisSection {
  id: string;
  label: string | null;
  line_start: number;
  line_end: number;
  line_count: number;
  rhyme_scheme: string | null;
  rhyme_scheme_confidence: UpstreamRhymeConfidence;
  syllable_pattern: number[];
  syllable_variance: number;
  cadence_class: string;
  repetition_signals: unknown[];
}

export interface UpstreamInsightAnchor {
  scope: AnchorScope;
  section_id: string | null;
  line_start: number | null;
  line_end: number | null;
}

/**
 * FastAPI emits a discriminated union of ~19 evidence variants (each with a
 * `kind` literal). M0/M1 keep the union structural so the gateway can pass
 * it through without locking down every variant — concrete typing lands in
 * M2 as the client starts consuming specific variants.
 */
export interface UpstreamTypedEvidence {
  kind: string;
  [key: string]: unknown;
}

export interface UpstreamInsight {
  id: string;
  type: string;
  scope: 'draft' | 'section';
  target: string | null;
  severity: InsightSeverity;
  message: string;
  evidence: UpstreamTypedEvidence | null;
  anchor: UpstreamInsightAnchor | null;
  confidence: InsightConfidence | null;
  hook_context: boolean;
}

export interface DraftDetail {
  sections: DraftAnalysisSection[];
}

export interface DraftAnalysisResponse {
  language: Language;
  title: string | null;
  capabilities: DraftAnalysisCapabilities;
  summary: DraftAnalysisSummary;
  insights: UpstreamInsight[];
  detail: DraftDetail;
  inner_rhymes?: InnerRhymeGroup[];
}

export interface DraftRevisionUpstream {
  revision_hash: string;
  analysis: DraftAnalysisResponse;
}

export interface CompareSummaryUpstream {
  motif_delta_count: number;
  repetition_delta_count: number;
  section_delta_count: number;
  consistency_delta_count: number;
  family_counts: Record<string, number>;
  unmatched_previous_section_ids: string[];
  unmatched_current_section_ids: string[];
}

export interface CompareCapabilitiesUpstream {
  compare_motifs: UpstreamCapability;
  compare_repetition: UpstreamCapability;
  compare_sections: UpstreamCapability;
  compare_consistency: UpstreamCapability;
}

export interface DraftCompareResponse {
  analysis_id: string;
  language: Language;
  title: string | null;
  previous: DraftRevisionUpstream;
  current: DraftRevisionUpstream;
  summary: CompareSummaryUpstream;
  insights: UpstreamInsight[];
  capabilities: CompareCapabilitiesUpstream;
}
