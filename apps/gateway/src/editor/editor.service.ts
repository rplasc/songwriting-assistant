import { Injectable } from '@nestjs/common';
import { performance } from 'perf_hooks';
import {
  AdvancedRhymeMode,
  DEFAULT_LANGUAGE,
  Language,
  RhymeMode,
  RhymeTargetType,
  defaultRhymeModeFor,
} from '../common/enums/language.enum';
import { FastapiClient } from '../fastapi/fastapi.client';
import { LanguageRequestMapper } from './mappers/language-request.mapper';
import {
  EditorAnalysisPayload,
  EditorResponsePresenter,
  ExploreRhymesPayload,
} from './presenters/editor-response.presenter';

export interface AnalyzeOptions {
  requestId?: string;
  rhymeMode?: RhymeMode;
  language?: Language;
}

export interface ExploreRhymesOptions {
  requestId?: string;
  targetType?: RhymeTargetType;
  mode?: AdvancedRhymeMode;
  language?: Language;
  limit?: number;
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

  async exploreRhymes(
    query: string,
    options: ExploreRhymesOptions = {},
  ): Promise<ExploreRhymesPayload> {
    const language = options.language ?? DEFAULT_LANGUAGE;
    const targetType: RhymeTargetType = options.targetType ?? 'word';
    // Default mode picks the language-appropriate "primary" rhyme mode so a
    // bare call still produces results — the client overrides this when the
    // explorer toggle is changed.
    const mode: AdvancedRhymeMode =
      options.mode ?? defaultRhymeModeFor(language);

    const t0 = performance.now();
    const upstream = await this.fastapi.getRhymes({
      word: query,
      mode,
      language,
      target_type: targetType,
      limit: options.limit,
    });

    return this.presenter.toExplorePayload(
      upstream,
      {
        query,
        targetType,
        mode,
        language,
      },
      performance.now() - t0,
      options.requestId,
    );
  }
}
