import { Injectable } from '@nestjs/common';
import { AnalysisStatus } from '../../common/enums/analysis-status.enum';
import { Language } from '../../common/enums/language.enum';
import {
  DraftAnalysisResponse,
  DraftAnalysisSection,
  DraftAnalysisSummary,
  InnerRhymeGroup,
} from '../../fastapi/dto/fastapi-responses';
import {
  CapabilitiesPayload,
  CapabilityPresenter,
} from './capability.presenter';
import { InsightPayload, InsightPresenter } from './insight.presenter';

export interface DraftAnalysisDetail {
  sections: DraftAnalysisSection[];
}

export interface DraftAnalysisPayload {
  draft_id: string | null;
  revision_hash: string;
  analysis_status: AnalysisStatus;
  analyzed_at: string;
  analysis: {
    language: Language;
    title: string | null;
    summary: DraftAnalysisSummary;
    detail: DraftAnalysisDetail;
    insights: InsightPayload[];
    capabilities: CapabilitiesPayload;
    inner_rhymes: InnerRhymeGroup[];
  };
  meta: {
    request_id?: string;
    latency_ms: number;
  };
}

@Injectable()
export class DraftAnalysisPresenter {
  constructor(
    private readonly capabilities: CapabilityPresenter,
    private readonly insights: InsightPresenter,
  ) {}

  toClient(input: {
    draftId: string | null;
    revisionHash: string;
    upstream: DraftAnalysisResponse;
    latencyMs: number;
    requestId?: string;
  }): DraftAnalysisPayload {
    const status: AnalysisStatus = this.capabilities.anyEnabled(
      input.upstream.capabilities,
    )
      ? 'fresh'
      : 'unsupported';
    return {
      draft_id: input.draftId,
      revision_hash: input.revisionHash,
      analysis_status: status,
      analyzed_at: new Date().toISOString(),
      analysis: {
        language: input.upstream.language,
        title: input.upstream.title,
        summary: input.upstream.summary,
        detail: { sections: input.upstream.detail.sections },
        insights: this.insights.toClientList(input.upstream.insights),
        capabilities: this.capabilities.toClient(input.upstream.capabilities),
        inner_rhymes: input.upstream.inner_rhymes ?? [],
      },
      meta: {
        request_id: input.requestId,
        latency_ms: Math.round(input.latencyMs),
      },
    };
  }
}
