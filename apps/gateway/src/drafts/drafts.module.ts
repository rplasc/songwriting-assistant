import { Module } from '@nestjs/common';
import { DraftsController } from './drafts.controller';
import { DraftsService } from './drafts.service';
import { DraftPresenter } from './presenters/draft.presenter';
import { SnapshotStore } from './snapshot.store';

@Module({
  controllers: [DraftsController],
  providers: [DraftsService, DraftPresenter, SnapshotStore],
  exports: [DraftsService, DraftPresenter, SnapshotStore],
})
export class DraftsModule {}
