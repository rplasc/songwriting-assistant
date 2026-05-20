import { Injectable } from '@nestjs/common';
import { AnalysisStatus } from '../../common/enums/analysis-status.enum';
import { Language } from '../../common/enums/language.enum';
import {
  DraftAnalysisCapabilities,
  DraftAnalysisResponse,
  DraftAnalysisSection,
  DraftAnalysisSummary,
} from '../../fastapi/dto/fastapi-responses';

export interface DraftAnalysisPayload {
  draft_id: string | null;
  revision_hash: string;
  analysis_status: AnalysisStatus;
  analyzed_at: string;
  analysis: {
    language: Language;
    title: string | null;
    summary: DraftAnalysisSummary;
    sections: DraftAnalysisSection[];
    insights: unknown[];
    capabilities: DraftAnalysisCapabilities;
  };
  meta: {
    request_id?: string;
    latency_ms: number;
  };
}

@Injectable()
export class DraftAnalysisPresenter {
  toClient(input: {
    draftId: string | null;
    revisionHash: string;
    upstream: DraftAnalysisResponse;
    latencyMs: number;
    requestId?: string;
  }): DraftAnalysisPayload {
    const caps = input.upstream.capabilities;
    const anyCapabilityEnabled = Object.values(caps).some(
      (v) => v !== 'unsupported',
    );
    const status: AnalysisStatus = anyCapabilityEnabled ? 'fresh' : 'unsupported';
    return {
      draft_id: input.draftId,
      revision_hash: input.revisionHash,
      analysis_status: status,
      analyzed_at: new Date().toISOString(),
      analysis: {
        language: input.upstream.language,
        title: input.upstream.title,
        summary: input.upstream.summary,
        sections: input.upstream.sections,
        insights: input.upstream.insights,
        capabilities: caps,
      },
      meta: {
        request_id: input.requestId,
        latency_ms: Math.round(input.latencyMs),
      },
    };
  }
}
