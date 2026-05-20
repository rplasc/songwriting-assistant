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

/**
 * Draft-level analysis request. Contract is provisional pending FastAPI
 * Phase 4 plan alignment — field shapes match what the gateway presenter
 * expects to receive back.
 */
export interface AnalyzeDraftRequest {
  content: string;
  language?: Language;
  sections?: AnalyzeDraftSection[];
  force_refresh?: boolean;
  revision_hash?: string;
}
