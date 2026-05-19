import { Body, Controller, Post, Req } from '@nestjs/common';
import type { Request } from 'express';
import { AnalyzeLineDto } from './dto/analyze-line.dto';
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
}
