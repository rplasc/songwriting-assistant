import { Body, Controller, Post, Req } from '@nestjs/common';
import type { Request } from 'express';
import { AnalysisService } from './analysis.service';
import { AnalyzeDraftDto } from './dto/analyze-draft.dto';
import { DraftAnalysisPayload } from './presenters/draft-analysis.presenter';

@Controller('v1/editor')
export class AnalysisController {
  constructor(private readonly analysis: AnalysisService) {}

  @Post('analyze-draft')
  async analyzeDraft(
    @Body() dto: AnalyzeDraftDto,
    @Req() req: Request,
  ): Promise<DraftAnalysisPayload> {
    const requestId = (req as Request & { requestId?: string }).requestId;
    return this.analysis.analyzeDraft({
      requestId,
      draftId: dto.draftId,
      language: dto.language,
      content: dto.content,
      inlineSections: dto.sections,
      forceRefresh: dto.forceRefresh,
    });
  }
}
