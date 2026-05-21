import {
  BadRequestException,
  Body,
  Controller,
  Delete,
  Get,
  Headers,
  HttpCode,
  HttpStatus,
  Param,
  ParseUUIDPipe,
  Patch,
  Post,
  Req,
} from '@nestjs/common';
import type { Request } from 'express';
import { CreateDraftDto } from './dto/create-draft.dto';
import { UpdateDraftDto } from './dto/update-draft.dto';
import { DraftsService } from './drafts.service';
import { DraftPayload, DraftPresenter } from './presenters/draft.presenter';

@Controller('v1/drafts')
export class DraftsController {
  constructor(
    private readonly drafts: DraftsService,
    private readonly presenter: DraftPresenter,
  ) {}

  @Post()
  create(
    @Body() dto: CreateDraftDto,
    @Req() req: Request,
  ): { data: DraftPayload } {
    const draft = this.drafts.create(
      {
        title: dto.title,
        content: dto.content,
        language: dto.language,
        sections: dto.sections,
      },
      { requestId: req.requestId },
    );
    return { data: this.presenter.toClient(draft) };
  }

  @Get(':id')
  findOne(@Param('id', new ParseUUIDPipe()) id: string): {
    data: DraftPayload;
  } {
    return { data: this.presenter.toClient(this.drafts.findById(id)) };
  }

  @Patch(':id')
  update(
    @Param('id', new ParseUUIDPipe()) id: string,
    @Body() dto: UpdateDraftDto,
    @Headers('if-match') ifMatch: string | undefined,
    @Req() req: Request,
  ): { data: DraftPayload } {
    if (
      dto.title === undefined &&
      dto.content === undefined &&
      dto.language === undefined &&
      dto.sections === undefined
    ) {
      throw new BadRequestException(
        'At least one of [title, content, language, sections] must be provided',
      );
    }
    const expectedVersion = parseIfMatch(ifMatch);
    const updated = this.drafts.update(
      id,
      {
        title: dto.title,
        content: dto.content,
        language: dto.language,
        sections: dto.sections,
        expectedVersion,
      },
      { requestId: req.requestId },
    );
    return { data: this.presenter.toClient(updated) };
  }

  @Delete(':id')
  @HttpCode(HttpStatus.NO_CONTENT)
  remove(
    @Param('id', new ParseUUIDPipe()) id: string,
    @Req() req: Request,
  ): void {
    this.drafts.remove(id, { requestId: req.requestId });
  }
}

function parseIfMatch(header: string | undefined): number | undefined {
  if (!header) return undefined;
  // Strip optional weak prefix and surrounding quotes per RFC 7232.
  const cleaned = header.trim().replace(/^W\//, '').replace(/^"|"$/g, '');
  const n = Number(cleaned);
  if (!Number.isInteger(n) || n < 1) {
    throw new BadRequestException({
      code: 'INVALID_IF_MATCH',
      message: `Malformed If-Match header: ${header}`,
    });
  }
  return n;
}
