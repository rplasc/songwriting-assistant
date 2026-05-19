import { Injectable } from '@nestjs/common';
import { performance } from 'perf_hooks';
import { Language, RhymeMode } from '../common/enums/language.enum';
import { FastapiClient } from '../fastapi/fastapi.client';
import { LanguageRequestMapper } from './mappers/language-request.mapper';
import {
  EditorAnalysisPayload,
  EditorResponsePresenter,
} from './presenters/editor-response.presenter';

export interface AnalyzeOptions {
  requestId?: string;
  rhymeMode?: RhymeMode;
  language?: Language;
}

@Injectable()
export class EditorService {
  constructor(
    private readonly fastapi: FastapiClient,
    private readonly presenter: EditorResponsePresenter,
    private readonly languageMapper: LanguageRequestMapper,
  ) {}

  async analyze(
    line: string,
    options: AnalyzeOptions = {},
  ): Promise<EditorAnalysisPayload> {
    const { language, mode } = this.languageMapper.resolve({
      language: options.language,
      rhyme_mode: options.rhymeMode,
    });

    const t0 = performance.now();
    const lineResp = await this.fastapi.analyzeLine({ line, language });

    const last = lineResp.last_word;
    const rhymes = last
      ? await this.fastapi.getRhymes({
          word: last.normalized,
          mode,
          language,
        })
      : null;

    return this.presenter.toClient(
      lineResp,
      rhymes,
      performance.now() - t0,
      mode,
      language,
      options.requestId,
    );
  }
}
