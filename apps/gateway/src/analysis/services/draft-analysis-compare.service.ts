import { BadRequestException, Injectable } from '@nestjs/common';
import { performance } from 'perf_hooks';
import { Language } from '../../common/enums/language.enum';
import { SnapshotStore } from '../../drafts/snapshot.store';
import { FastapiClient } from '../../fastapi/fastapi.client';
import { AnalyzeDraftCompareOptionsDto } from '../dto/analyze-draft-compare-options.dto';
import { DraftCompareRequestMapper } from '../mappers/draft-compare-request.mapper';
import {
  DraftComparePayload,
  DraftComparePresenter,
} from '../presenters/draft-compare.presenter';

export interface CompareDraftOptions {
  requestId?: string;
  draftId?: string;
  baseRevisionHash: string;
  targetRevisionHash: string;
  language?: Language;
  title?: string;
  options?: AnalyzeDraftCompareOptionsDto;
  /** Reserved: compare-cache toggle. Accepted by the contract; no behavior in M2/M3. */
  forceRefresh?: boolean;
}

@Injectable()
export class DraftAnalysisCompareService {
  constructor(
    private readonly fastapi: FastapiClient,
    private readonly snapshots: SnapshotStore,
    private readonly mapper: DraftCompareRequestMapper,
    private readonly presenter: DraftComparePresenter,
  ) {}

  async compareDraft(opts: CompareDraftOptions): Promise<DraftComparePayload> {
    if (!opts.draftId) {
      throw new BadRequestException({
        code: 'COMPARE_REQUIRES_DRAFT_ID',
        message:
          'analyze-draft-compare requires draftId so revision snapshots can be resolved.',
      });
    }

    const base = this.snapshots.find(opts.draftId, opts.baseRevisionHash);
    if (!base) {
      throw new BadRequestException({
        code: 'COMPARE_BASELINE_UNAVAILABLE',
        message: `No snapshot found for baseRevisionHash on draft ${opts.draftId}.`,
        missing: 'base',
      });
    }
    const target = this.snapshots.find(opts.draftId, opts.targetRevisionHash);
    if (!target) {
      throw new BadRequestException({
        code: 'COMPARE_BASELINE_UNAVAILABLE',
        message: `No snapshot found for targetRevisionHash on draft ${opts.draftId}.`,
        missing: 'target',
      });
    }

    const upstreamReq = this.mapper.resolve({
      language: opts.language,
      title: opts.title,
      base,
      target,
      options: opts.options,
    });

    const t0 = performance.now();
    const upstream = await this.fastapi.analyzeDraftCompare(upstreamReq);
    return this.presenter.toClient({
      upstream,
      draftId: opts.draftId,
      latencyMs: performance.now() - t0,
      requestId: opts.requestId,
    });
  }
}
