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
  /** Rhyme this word (the caret word) instead of the line's last word. */
  targetWord?: string;
  rhymeMode?: RhymeMode;
  language?: Language;
  /**
   * Skip the upstream rhymes lookup entirely (the advanced rhyme explorer is
   * already covering rhymes for this line elsewhere).
   */
  skipRhymes?: boolean;
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

    if (options.skipRhymes) {
      const lineResp = await this.fastapi.analyzeLine({ line, language });
      const targetWord =
        options.targetWord ?? lineResp.last_word?.normalized ?? null;
      return this.presenter.toClient(
        lineResp,
        null,
        performance.now() - t0,
        mode,
        language,
        options.requestId,
        targetWord,
      );
    }

    if (options.targetWord) {
      // The caret word is already known, so the rhymes request doesn't
      // depend on the line-analysis response — issue both upstream calls in
      // parallel instead of waiting on analyze-line first.
      const [lineResp, rhymes] = await Promise.all([
        this.fastapi.analyzeLine({ line, language }),
        this.fastapi.getRhymes({
          word: options.targetWord,
          mode,
          language,
        }),
      ]);
      return this.presenter.toClient(
        lineResp,
        rhymes,
        performance.now() - t0,
        mode,
        language,
        options.requestId,
        options.targetWord,
      );
    }

    const lineResp = await this.fastapi.analyzeLine({ line, language });

    // No caret word was sent, so the rhyme target depends on the line's
    // last word from the response above.
    const targetWord = lineResp.last_word?.normalized ?? null;
    const rhymes = targetWord
      ? await this.fastapi.getRhymes({
          word: targetWord,
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
      targetWord,
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
