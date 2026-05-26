import {
  AnchorScope,
  CapabilityKey,
  CapabilityReasonCode,
  CapabilityStatus,
  InsightConfidence,
  InsightSeverity,
} from '../../common/enums/capability.enum';
import { Language } from '../../common/enums/language.enum';

export interface TokenAnalysis {
  text: string;
  normalized: string;
  syllables: number;
  pronunciation_found: boolean;
  source?: 'dictionary' | 'heuristic';
  low_confidence?: boolean;
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
}

export interface RhymeCandidate {
  word: string;
  syllables: number;
  rhyme_type: string;
  score: number;
  match_reason?: string | null;
}

export interface RhymeMeta {
  limit: number;
  mode: string;
  include_near: boolean;
}

export interface RhymeResponse {
  word: string;
  normalized_word: string | null;
  language: Language;
  pronunciations_found: boolean;
  rhymes: RhymeCandidate[];
  meta: RhymeMeta;
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
