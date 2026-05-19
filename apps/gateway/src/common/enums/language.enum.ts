/**
 * Supported product languages. Kept narrow and explicit: the gateway
 * validates this enum locally so unsupported values never reach FastAPI.
 */
export const SUPPORTED_LANGUAGES = ['en', 'es'] as const;
export type Language = (typeof SUPPORTED_LANGUAGES)[number];

export const DEFAULT_LANGUAGE: Language = 'en';

export type RhymeMode = 'perfect' | 'near' | 'consonant' | 'assonant';

export const SUPPORTED_RHYME_MODES: readonly RhymeMode[] = [
  'perfect',
  'near',
  'consonant',
  'assonant',
];

/**
 * The rhyme mode FastAPI applies when none is given. The gateway resolves
 * it here so the resolved value can be echoed back to the client even when
 * no rhymes are returned (e.g. the line ends in a punctuation-only token).
 */
export function defaultRhymeModeFor(language: Language): RhymeMode {
  return language === 'es' ? 'consonant' : 'perfect';
}
