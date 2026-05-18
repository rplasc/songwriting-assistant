import {
  BadRequestException,
  Body,
  Controller,
  Get,
  Param,
  ParseUUIDPipe,
  Patch,
  Post,
} from '@nestjs/common';
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
  create(@Body() dto: CreateDraftDto): { data: DraftPayload } {
    const draft = this.drafts.create({
      title: dto.title,
      content: dto.content,
    });
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
  ): { data: DraftPayload } {
    if (dto.title === undefined && dto.content === undefined) {
      throw new BadRequestException(
        'At least one of [title, content] must be provided',
      );
    }
    const updated = this.drafts.update(id, {
      title: dto.title,
      content: dto.content,
    });
    return { data: this.presenter.toClient(updated) };
  }
}
