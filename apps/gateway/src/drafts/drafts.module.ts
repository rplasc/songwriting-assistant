import { Module } from '@nestjs/common';
import { DraftsController } from './drafts.controller';
import { DraftsService } from './drafts.service';
import { DraftPresenter } from './presenters/draft.presenter';

@Module({
  controllers: [DraftsController],
  providers: [DraftsService, DraftPresenter],
})
export class DraftsModule {}
