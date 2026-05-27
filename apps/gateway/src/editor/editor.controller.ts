import { Body, Controller, Post, Req } from '@nestjs/common';
import type { Request } from 'express';
import { AnalyzeLineDto, ExploreRhymesDto } from './dto/analyze-line.dto';
import { EditorService } from './editor.service';

@Controller('v1/editor')
export class EditorController {
  constructor(private readonly editor: EditorService) {}

  @Post('analyze')
  async analyze(@Body() dto: AnalyzeLineDto, @Req() req: Request) {
    const requestId = (req as Request & { requestId?: string }).requestId;
    return this.editor.analyze(dto.line, {
      requestId,
      rhymeMode: dto.rhyme_mode,
      language: dto.language,
    });
  }

  @Post('rhymes/explore')
  async exploreRhymes(@Body() dto: ExploreRhymesDto, @Req() req: Request) {
    const requestId = (req as Request & { requestId?: string }).requestId;
    return this.editor.exploreRhymes(dto.query, {
      requestId,
      targetType: dto.target_type,
      mode: dto.mode,
      language: dto.language,
      limit: dto.limit,
    });
  }
}
