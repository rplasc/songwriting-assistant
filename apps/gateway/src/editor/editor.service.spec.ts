import { EditorService } from './editor.service';
import { LanguageRequestMapper } from './mappers/language-request.mapper';
import { EditorResponsePresenter } from './presenters/editor-response.presenter';
import { FastapiClient } from '../fastapi/fastapi.client';

describe('EditorService', () => {
  const baseLineResp = {
    line: 'hello world',
    normalized_line: 'hello world',
    language: 'en' as const,
    total_syllables: 3,
    tokens: [],
    last_word: {
      text: 'world',
      normalized: 'world',
      pronunciation_found: true,
    },
  };

  function setup(opts: {
    pronunciationFound: boolean;
    rhymeMeta?: { limit: number; mode: string; include_near: boolean };
    rhymeLanguage?: 'en' | 'es';
    lineLanguage?: 'en' | 'es';
  }) {
    const analyzeLine = jest.fn().mockResolvedValue({
      ...baseLineResp,
      language: opts.lineLanguage ?? 'en',
      last_word: {
        ...baseLineResp.last_word,
        pronunciation_found: opts.pronunciationFound,
      },
    });
    const getRhymes = jest.fn().mockResolvedValue({
      word: 'world',
      normalized_word: 'world',
      language: opts.rhymeLanguage ?? 'en',
      pronunciations_found: true,
      rhymes: [],
      meta: opts.rhymeMeta ?? { limit: 10, mode: 'perfect', include_near: false },
    });
    const fastapi = { analyzeLine, getRhymes } as unknown as FastapiClient;
    const service = new EditorService(
      fastapi,
      new EditorResponsePresenter(),
      new LanguageRequestMapper(),
    );
    return { service, analyzeLine, getRhymes };
  }

  it('calls getRhymes with language=en and mode=perfect by default', async () => {
    const { service, getRhymes, analyzeLine } = setup({
      pronunciationFound: true,
    });
    const out = await service.analyze('hello world');
    expect(analyzeLine).toHaveBeenCalledWith({
      line: 'hello world',
      language: 'en',
    });
    expect(getRhymes).toHaveBeenCalledWith({
      word: 'world',
      mode: 'perfect',
      language: 'en',
    });
    expect(out.rhymes.mode).toBe('perfect');
    expect(out.language).toBe('en');
  });

  it('forwards rhymeMode=near to getRhymes', async () => {
    const { service, getRhymes } = setup({
      pronunciationFound: true,
      rhymeMeta: { limit: 10, mode: 'near', include_near: true },
    });
    const out = await service.analyze('hello world', {
      requestId: 'req-x',
      rhymeMode: 'near',
    });
    expect(getRhymes).toHaveBeenCalledWith({
      word: 'world',
      mode: 'near',
      language: 'en',
    });
    expect(out.rhymes.mode).toBe('near');
  });

  it('defaults Spanish requests to mode=consonant', async () => {
    const { service, getRhymes, analyzeLine } = setup({
      pronunciationFound: true,
      rhymeMeta: { limit: 10, mode: 'consonant', include_near: false },
      rhymeLanguage: 'es',
      lineLanguage: 'es',
    });
    const out = await service.analyze('corazón', { language: 'es' });
    expect(analyzeLine).toHaveBeenCalledWith({
      line: 'corazón',
      language: 'es',
    });
    expect(getRhymes).toHaveBeenCalledWith({
      word: 'world',
      mode: 'consonant',
      language: 'es',
    });
    expect(out.language).toBe('es');
    expect(out.rhymes.mode).toBe('consonant');
  });

  it('forwards an explicit Spanish mode (assonant)', async () => {
    const { service, getRhymes } = setup({
      pronunciationFound: true,
      rhymeMeta: { limit: 10, mode: 'assonant', include_near: false },
      rhymeLanguage: 'es',
      lineLanguage: 'es',
    });
    const out = await service.analyze('vida', {
      language: 'es',
      rhymeMode: 'assonant',
    });
    expect(getRhymes).toHaveBeenCalledWith({
      word: 'world',
      mode: 'assonant',
      language: 'es',
    });
    expect(out.rhymes.mode).toBe('assonant');
  });

  it('still calls getRhymes when pronunciation_found is false so the NLP fallback can run', async () => {
    const { service, getRhymes } = setup({ pronunciationFound: false });
    await service.analyze('hello world');
    expect(getRhymes).toHaveBeenCalledWith({
      word: 'world',
      mode: 'perfect',
      language: 'en',
    });
  });
});
