import { Module } from '@nestjs/common';
import { DraftsModule } from '../drafts/drafts.module';
import { FastapiModule } from '../fastapi/fastapi.module';
import { AnalysisController } from './analysis.controller';
import { AnalysisService } from './analysis.service';
import { DraftAnalysisRequestMapper } from './mappers/draft-analysis-request.mapper';
import { DraftAnalysisPresenter } from './presenters/draft-analysis.presenter';

@Module({
  imports: [FastapiModule, DraftsModule],
  controllers: [AnalysisController],
  providers: [
    AnalysisService,
    DraftAnalysisRequestMapper,
    DraftAnalysisPresenter,
  ],
})
export class AnalysisModule {}
