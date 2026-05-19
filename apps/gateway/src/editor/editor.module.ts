import { Module } from '@nestjs/common';
import { FastapiModule } from '../fastapi/fastapi.module';
import { EditorController } from './editor.controller';
import { EditorGateway } from './editor.gateway';
import { EditorService } from './editor.service';
import { LanguageRequestMapper } from './mappers/language-request.mapper';
import { EditorResponsePresenter } from './presenters/editor-response.presenter';

@Module({
  imports: [FastapiModule],
  controllers: [EditorController],
  providers: [
    EditorService,
    EditorResponsePresenter,
    EditorGateway,
    LanguageRequestMapper,
  ],
})
export class EditorModule {}
