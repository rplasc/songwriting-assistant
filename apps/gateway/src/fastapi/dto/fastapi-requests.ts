import { Language, RhymeMode } from '../../common/enums/language.enum';

export interface AnalyzeLineRequest {
  line: string;
  language?: Language;
}

export interface RhymesRequest {
  word: string;
  limit?: number;
  language?: Language;
  /** Field name matches the FastAPI schema. */
  mode?: RhymeMode;
}

export interface AnalyzeDraftSection {
  id: string;
  label: string;
  line_start: number;
  line_end: number;
}

export interface AnalyzeDraftUpstreamOptions {
  include_semantic_repetition?: boolean;
  include_motif_tracking?: boolean;
  include_section_contrast?: boolean;
  include_consistency_hints?: boolean;
}

export interface AnalyzeDraftRequest {
  content: string;
  language?: Language;
  title?: string;
  sections?: AnalyzeDraftSection[];
  options?: AnalyzeDraftUpstreamOptions;
}

export interface DraftCompareUpstreamSide {
  content: string;
  sections?: AnalyzeDraftSection[];
}

export interface DraftCompareUpstreamOptions {
  compare_motifs?: boolean;
  compare_repetition?: boolean;
  compare_sections?: boolean;
  compare_consistency?: boolean;
}

export interface AnalyzeDraftCompareRequest {
  language?: Language;
  title?: string;
  previous: DraftCompareUpstreamSide;
  current: DraftCompareUpstreamSide;
  options?: DraftCompareUpstreamOptions;
}
