import { MiddlewareConsumer, Module, NestModule } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import appConfig from './config/app.config';
import fastapiConfig from './config/fastapi.config';
import { envValidationSchema } from './config/validation';
import { RequestIdMiddleware } from './common/middleware/request-id.middleware';
import { AnalysisModule } from './analysis/analysis.module';
import { DraftsModule } from './drafts/drafts.module';
import { EditorModule } from './editor/editor.module';
import { FastapiModule } from './fastapi/fastapi.module';
import { HealthModule } from './health/health.module';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      load: [appConfig, fastapiConfig],
      validationSchema: envValidationSchema,
    }),
    FastapiModule,
    HealthModule,
    EditorModule,
    DraftsModule,
    AnalysisModule,
  ],
})
export class AppModule implements NestModule {
  configure(consumer: MiddlewareConsumer) {
    consumer.apply(RequestIdMiddleware).forRoutes('*');
  }
}
