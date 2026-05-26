import { Injectable } from '@nestjs/common';
import {
  InsightConfidence,
  InsightSeverity,
} from '../../common/enums/capability.enum';
import {
  UpstreamInsight,
  UpstreamTypedEvidence,
} from '../../fastapi/dto/fastapi-responses';
import {
  AnalysisAnchorPayload,
  AnalysisAnchorPresenter,
} from './analysis-anchor.presenter';

export interface InsightEvidencePayload {
  kind: string;
  [key: string]: unknown;
}

export interface InsightPayload {
  id: string;
  type: string;
  scope: 'draft' | 'section';
  target: string | null;
  severity: InsightSeverity;
  message: string;
  evidence: InsightEvidencePayload | null;
  anchor: AnalysisAnchorPayload | null;
  confidence: InsightConfidence | null;
  hook_context: boolean;
}

@Injectable()
export class InsightPresenter {
  constructor(private readonly anchor: AnalysisAnchorPresenter) {}

  toClient(input: UpstreamInsight): InsightPayload {
    return {
      id: input.id,
      type: input.type,
      scope: input.scope,
      target: input.target,
      severity: input.severity,
      message: input.message,
      evidence: this.normalizeEvidence(input.evidence),
      anchor: this.anchor.toClient(input.anchor),
      confidence: input.confidence,
      hook_context: input.hook_context,
    };
  }

  toClientList(input: UpstreamInsight[]): InsightPayload[] {
    return input.map((i) => this.toClient(i));
  }

  private normalizeEvidence(
    e: UpstreamTypedEvidence | null,
  ): InsightEvidencePayload | null {
    if (!e) return null;
    return { ...e };
  }
}
