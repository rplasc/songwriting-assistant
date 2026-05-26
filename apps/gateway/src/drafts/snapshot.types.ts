import { AnalysisStatus } from '../common/enums/analysis-status.enum';
import { DraftAnalysisCapabilities } from '../fastapi/dto/fastapi-responses';
import { DraftSection } from './draft.types';

export interface DraftSnapshot {
  revisionHash: string;
  analyzedAt: string;
  content: string;
  sections: DraftSection[];
  analysisStatus: AnalysisStatus;
  capabilities: DraftAnalysisCapabilities;
}
