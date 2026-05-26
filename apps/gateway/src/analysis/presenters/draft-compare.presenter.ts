import { Injectable } from '@nestjs/common';
import { Language } from '../../common/enums/language.enum';
import {
  DraftAnalysisResponse,
  DraftCompareResponse,
  DraftRevisionUpstream,
} from '../../fastapi/dto/fastapi-responses';
import {
  CapabilitiesPayload,
  CapabilityPayload,
  CapabilityPresenter,
} from './capability.presenter';
import { InsightPayload, InsightPresenter } from './insight.presenter';

export interface DraftCompareRevisionPayload {
  revision_hash: string;
  analysis: {
    language: Language;
    title: string | null;
    summary: DraftAnalysisResponse['summary'];
    detail: { sections: DraftAnalysisResponse['detail']['sections'] };
    insights: InsightPayload[];
    capabilities: CapabilitiesPayload;
  };
}

export interface CompareSummaryPayload {
  motif_delta_count: number;
  repetition_delta_count: number;
  section_delta_count: number;
  consistency_delta_count: number;
  family_counts: Record<string, number>;
  unmatched_previous_section_ids: string[];
  unmatched_current_section_ids: string[];
}

export interface CompareCapabilitiesPayload {
  compare_motifs: CapabilityPayload;
  compare_repetition: CapabilityPayload;
  compare_sections: CapabilityPayload;
  compare_consistency: CapabilityPayload;
}

export interface DraftComparePayload {
  analysis_id: string;
  draft_id: string | null;
  language: Language;
  title: string | null;
  previous: DraftCompareRevisionPayload;
  current: DraftCompareRevisionPayload;
  summary: CompareSummaryPayload;
  insights: InsightPayload[];
  capabilities: CompareCapabilitiesPayload;
  meta: {
    request_id?: string;
    latency_ms: number;
  };
}

@Injectable()
export class DraftComparePresenter {
  constructor(
    private readonly capabilities: CapabilityPresenter,
    private readonly insights: InsightPresenter,
  ) {}

  toClient(input: {
    upstream: DraftCompareResponse;
    draftId: string | null;
    latencyMs: number;
    requestId?: string;
  }): DraftComparePayload {
    const u = input.upstream;
    return {
      analysis_id: u.analysis_id,
      draft_id: input.draftId,
      language: u.language,
      title: u.title,
      previous: this.toRevisionPayload(u.previous),
      current: this.toRevisionPayload(u.current),
      summary: {
        motif_delta_count: u.summary.motif_delta_count,
        repetition_delta_count: u.summary.repetition_delta_count,
        section_delta_count: u.summary.section_delta_count,
        consistency_delta_count: u.summary.consistency_delta_count,
        family_counts: u.summary.family_counts,
        unmatched_previous_section_ids: u.summary.unmatched_previous_section_ids,
        unmatched_current_section_ids: u.summary.unmatched_current_section_ids,
      },
      insights: this.insights.toClientList(u.insights),
      capabilities: {
        compare_motifs: this.normalizeCap(u.capabilities.compare_motifs),
        compare_repetition: this.normalizeCap(u.capabilities.compare_repetition),
        compare_sections: this.normalizeCap(u.capabilities.compare_sections),
        compare_consistency: this.normalizeCap(
          u.capabilities.compare_consistency,
        ),
      },
      meta: {
        request_id: input.requestId,
        latency_ms: Math.round(input.latencyMs),
      },
    };
  }

  private toRevisionPayload(
    rev: DraftRevisionUpstream,
  ): DraftCompareRevisionPayload {
    return {
      revision_hash: rev.revision_hash,
      analysis: {
        language: rev.analysis.language,
        title: rev.analysis.title,
        summary: rev.analysis.summary,
        detail: { sections: rev.analysis.detail.sections },
        insights: this.insights.toClientList(rev.analysis.insights),
        capabilities: this.capabilities.toClient(rev.analysis.capabilities),
      },
    };
  }

  private normalizeCap(cap: {
    status: CapabilityPayload['status'];
    reason_code: CapabilityPayload['reason_code'];
  }): CapabilityPayload {
    return {
      status: cap.status,
      reason_code: cap.reason_code ?? null,
    };
  }
}
