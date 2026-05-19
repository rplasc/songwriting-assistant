import { LanguageRequestMapper } from './language-request.mapper';

describe('LanguageRequestMapper', () => {
  const mapper = new LanguageRequestMapper();

  it('defaults to en/perfect when nothing is set', () => {
    expect(mapper.resolve({})).toEqual({ language: 'en', mode: 'perfect' });
  });

  it('defaults Spanish to consonant mode when mode is omitted', () => {
    expect(mapper.resolve({ language: 'es' })).toEqual({
      language: 'es',
      mode: 'consonant',
    });
  });

  it('honors an explicit mode regardless of language', () => {
    expect(mapper.resolve({ language: 'es', rhyme_mode: 'assonant' })).toEqual(
      { language: 'es', mode: 'assonant' },
    );
    expect(mapper.resolve({ rhyme_mode: 'near' })).toEqual({
      language: 'en',
      mode: 'near',
    });
  });
});
