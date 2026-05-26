import { AnalysisStatus } from '../common/enums/analysis-status.enum';
import { Language } from '../common/enums/language.enum';

export interface DraftSection {
  id: string;
  label: string;
  lineStart: number;
  lineEnd: number;
}

export interface Draft {
  id: string;
  title: string;
  content: string;
  language: Language;
  sections?: DraftSection[];
  version: number;
  createdAt: string;
  updatedAt: string;
  /**
   * Phase 5.5 snapshot provenance. Always null in M0/M1 — persistence will
   * land in M2 once compare flows need it.
   */
  lastAnalyzedAt?: string | null;
  lastAnalysisStatus?: AnalysisStatus | null;
  latestAnalyzedRevisionHash?: string | null;
}
