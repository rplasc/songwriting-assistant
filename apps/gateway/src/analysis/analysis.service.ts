import { Injectable } from '@nestjs/common';
import { performance } from 'perf_hooks';
import { Language } from '../common/enums/language.enum';
import { DraftsService } from '../drafts/drafts.service';
import { FastapiClient } from '../fastapi/fastapi.client';
import { DraftAnalysisRequestMapper } from './mappers/draft-analysis-request.mapper';
import {
  DraftAnalysisPayload,
  DraftAnalysisPresenter,
} from './presenters/draft-analysis.presenter';

export interface AnalyzeDraftOptions {
  requestId?: string;
  draftId?: string;
  language?: Language;
  content: string;
  inlineSections?: Array<{
    label: string;
    lineStart: number;
    lineEnd: number;
  }>;
  forceRefresh?: boolean;
}

@Injectable()
export class AnalysisService {
  constructor(
    private readonly fastapi: FastapiClient,
    private readonly drafts: DraftsService,
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
      inlineSections: opts.inlineSections,
      storedSections,
    });

    const t0 = performance.now();
    const upstream = await this.fastapi.analyzeDraft({
      content: opts.content,
      language: resolved.language,
      sections: resolved.upstreamSections,
      force_refresh: opts.forceRefresh,
      revision_hash: resolved.revisionHash,
    });

    return this.presenter.toClient({
      draftId: opts.draftId ?? null,
      revisionHash: resolved.revisionHash,
      upstream,
      latencyMs: performance.now() - t0,
      requestId: opts.requestId,
    });
  }
}
