import { Injectable } from '@nestjs/common';
import { AnalysisStatus } from '../../common/enums/analysis-status.enum';
import { Language } from '../../common/enums/language.enum';
import {
  DraftAnalysisCapabilities,
  DraftAnalysisResponse,
} from '../../fastapi/dto/fastapi-responses';

export interface DraftAnalysisSectionPayload {
  id: string;
  label: string;
  line_start: number;
  line_end: number;
}

export interface DraftAnalysisPayload {
  draft_id: string | null;
  revision_hash: string;
  analysis_status: AnalysisStatus;
  analyzed_at: string;
  analysis: {
    language: Language;
    summary: { section_count: number; line_count: number };
    sections: DraftAnalysisSectionPayload[];
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
    const anyCapabilityEnabled =
      caps.rhyme_scheme || caps.cadence || caps.repetition;
    const status: AnalysisStatus = anyCapabilityEnabled ? 'fresh' : 'unsupported';
    return {
      draft_id: input.draftId,
      revision_hash: input.revisionHash,
      analysis_status: status,
      analyzed_at: new Date().toISOString(),
      analysis: {
        language: input.upstream.language,
        summary: input.upstream.summary,
        sections: input.upstream.sections.map((s) => ({
          id: s.id,
          label: s.label,
          line_start: s.line_start,
          line_end: s.line_end,
        })),
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
