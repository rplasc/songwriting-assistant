import { Module } from '@nestjs/common';
import { DraftsModule } from '../drafts/drafts.module';
import { FastapiModule } from '../fastapi/fastapi.module';
import { AnalysisController } from './analysis.controller';
import { AnalysisService } from './analysis.service';
import { DraftAnalysisRequestMapper } from './mappers/draft-analysis-request.mapper';
import { DraftCompareRequestMapper } from './mappers/draft-compare-request.mapper';
import { AnalysisAnchorPresenter } from './presenters/analysis-anchor.presenter';
import { CapabilityPresenter } from './presenters/capability.presenter';
import { DraftAnalysisPresenter } from './presenters/draft-analysis.presenter';
import { DraftComparePresenter } from './presenters/draft-compare.presenter';
import { InsightPresenter } from './presenters/insight.presenter';
import { DraftAnalysisCompareService } from './services/draft-analysis-compare.service';

@Module({
  imports: [FastapiModule, DraftsModule],
  controllers: [AnalysisController],
  providers: [
    AnalysisService,
    DraftAnalysisCompareService,
    DraftAnalysisRequestMapper,
    DraftCompareRequestMapper,
    DraftAnalysisPresenter,
    DraftComparePresenter,
    CapabilityPresenter,
    InsightPresenter,
    AnalysisAnchorPresenter,
  ],
})
export class AnalysisModule {}
