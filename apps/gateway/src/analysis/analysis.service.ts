import { Injectable } from '@nestjs/common';
import { performance } from 'perf_hooks';
import { AnalysisMode } from '../common/enums/analysis-mode.enum';
import { Language } from '../common/enums/language.enum';
import { DraftsService } from '../drafts/drafts.service';
import { SnapshotStore } from '../drafts/snapshot.store';
import { FastapiClient } from '../fastapi/fastapi.client';
import { AnalyzeDraftOptionsDto } from './dto/analyze-draft-options.dto';
import { DraftAnalysisRequestMapper } from './mappers/draft-analysis-request.mapper';
import {
  DraftAnalysisPayload,
  DraftAnalysisPresenter,
} from './presenters/draft-analysis.presenter';

export interface AnalyzeDraftOptions {
  requestId?: string;
  draftId?: string;
  title?: string;
  language?: Language;
  content: string;
  inlineSections?: Array<{
    label: string;
    lineStart: number;
    lineEnd: number;
  }>;
  forceRefresh?: boolean;
  analysisMode?: AnalysisMode;
  options?: AnalyzeDraftOptionsDto;
}

@Injectable()
export class AnalysisService {
  constructor(
    private readonly fastapi: FastapiClient,
    private readonly drafts: DraftsService,
    private readonly snapshots: SnapshotStore,
    private readonly mapper: DraftAnalysisRequestMapper,
    private readonly presenter: DraftAnalysisPresenter,
  ) {}

  async analyzeDraft(opts: AnalyzeDraftOptions): Promise<DraftAnalysisPayload> {
    const storedSections =
      opts.inlineSections === undefined && opts.draftId
        ? this.drafts.findById(opts.draftId).sections
        : undefined;

    const resolved = this.mapper.resolve({
      content: opts.content,
      language: opts.language,
      analysisMode: opts.analysisMode,
      options: opts.options,
      inlineSections: opts.inlineSections,
      storedSections,
    });

    const t0 = performance.now();
    const upstream = await this.fastapi.analyzeDraft({
      content: opts.content,
      language: resolved.language,
      title: opts.title,
      sections:
        resolved.upstreamSections.length > 0
          ? resolved.upstreamSections
          : undefined,
      options: resolved.upstreamOptions,
    });

    const payload = this.presenter.toClient({
      draftId: opts.draftId ?? null,
      revisionHash: resolved.revisionHash,
      upstream,
      latencyMs: performance.now() - t0,
      requestId: opts.requestId,
    });

    // Snapshot + provenance only make sense when the draft has a stable id.
    if (opts.draftId) {
      this.snapshots.put(opts.draftId, {
        revisionHash: resolved.revisionHash,
        analyzedAt: payload.analyzed_at,
        content: opts.content,
        sections: resolved.sections,
        analysisStatus: payload.analysis_status,
        capabilities: upstream.capabilities,
      });
      this.drafts.recordAnalysis(opts.draftId, {
        lastAnalyzedAt: payload.analyzed_at,
        lastAnalysisStatus: payload.analysis_status,
        latestAnalyzedRevisionHash: resolved.revisionHash,
      });
    }

    return payload;
  }
}
