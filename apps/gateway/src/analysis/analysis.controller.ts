import { Body, Controller, Post, Req } from '@nestjs/common';
import type { Request } from 'express';
import { AnalysisService } from './analysis.service';
import { AnalyzeDraftCompareDto } from './dto/analyze-draft-compare.dto';
import { AnalyzeDraftDto } from './dto/analyze-draft.dto';
import { DraftAnalysisPayload } from './presenters/draft-analysis.presenter';
import { DraftComparePayload } from './presenters/draft-compare.presenter';
import { DraftAnalysisCompareService } from './services/draft-analysis-compare.service';

@Controller('v1/editor')
export class AnalysisController {
  constructor(
    private readonly analysis: AnalysisService,
    private readonly compare: DraftAnalysisCompareService,
  ) {}

  @Post('analyze-draft')
  async analyzeDraft(
    @Body() dto: AnalyzeDraftDto,
    @Req() req: Request,
  ): Promise<DraftAnalysisPayload> {
    const requestId = (req as Request & { requestId?: string }).requestId;
    return this.analysis.analyzeDraft({
      requestId,
      draftId: dto.draftId,
      title: dto.title,
      language: dto.language,
      content: dto.content,
      inlineSections: dto.sections,
      forceRefresh: dto.forceRefresh,
      analysisMode: dto.analysisMode,
      options: dto.options,
    });
  }

  /**
   * Phase 5.5 compare. HTTP-only by design — advanced review never flows
   * through the editor WebSocket gateway. `forceRefresh` is accepted on the
   * contract but has no behavior in M2/M3; reserved for the future cache.
   */
  @Post('analyze-draft-compare')
  async analyzeDraftCompare(
    @Body() dto: AnalyzeDraftCompareDto,
    @Req() req: Request,
  ): Promise<DraftComparePayload> {
    const requestId = (req as Request & { requestId?: string }).requestId;
    return this.compare.compareDraft({
      requestId,
      draftId: dto.draftId,
      baseRevisionHash: dto.baseRevisionHash,
      targetRevisionHash: dto.targetRevisionHash,
      language: dto.language,
      title: dto.title,
      options: dto.options,
      forceRefresh: dto.forceRefresh,
    });
  }
}
