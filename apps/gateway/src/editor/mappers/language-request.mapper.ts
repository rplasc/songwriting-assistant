import { Injectable } from '@nestjs/common';
import {
  DEFAULT_LANGUAGE,
  Language,
  RhymeMode,
  defaultRhymeModeFor,
} from '../../common/enums/language.enum';

export interface ResolvedAnalysisRequest {
  language: Language;
  mode: RhymeMode;
}

/**
 * Resolves request-level defaults for language and rhyme mode. Kept as a
 * narrow mapper so language-aware defaulting is in one place rather than
 * scattered across the editor service, controller, and websocket gateway.
 */
@Injectable()
export class LanguageRequestMapper {
  resolve(input: {
    language?: Language;
    rhyme_mode?: RhymeMode;
  }): ResolvedAnalysisRequest {
    const language = input.language ?? DEFAULT_LANGUAGE;
    const mode = input.rhyme_mode ?? defaultRhymeModeFor(language);
    return { language, mode };
  }
}
