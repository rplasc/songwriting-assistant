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

export interface DraftAnalysisSection {
  id: string;
  label: string;
  line_start: number;
  line_end: number;
}

export interface DraftAnalysisSummary {
  section_count: number;
  line_count: number;
}

export interface DraftAnalysisCapabilities {
  rhyme_scheme: boolean;
  cadence: boolean;
  repetition: boolean;
}

/**
 * Draft-level analysis response. Contract is provisional pending FastAPI
 * Phase 4 plan alignment — the gateway presenter forwards `insights`
 * opaquely so FastAPI can evolve insight payloads without changing this
 * envelope.
 */
export interface DraftAnalysisResponse {
  language: Language;
  summary: DraftAnalysisSummary;
  sections: DraftAnalysisSection[];
  insights: unknown[];
  capabilities: DraftAnalysisCapabilities;
}
