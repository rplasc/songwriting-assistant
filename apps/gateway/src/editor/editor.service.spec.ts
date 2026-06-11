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
      meta: opts.rhymeMeta ?? {
        limit: 10,
        mode: 'perfect',
        include_near: false,
      },
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

  it('rhymes the caret target word instead of the last word when provided', async () => {
    const { service, getRhymes } = setup({ pronunciationFound: true });
    const out = await service.analyze('hello world', { targetWord: 'hello' });
    expect(getRhymes).toHaveBeenCalledWith({
      word: 'hello',
      mode: 'perfect',
      language: 'en',
    });
    expect(out.rhymes.target_word).toBe('hello');
  });

  it('echoes the last word as target_word when no caret word is sent', async () => {
    const { service } = setup({ pronunciationFound: true });
    const out = await service.analyze('hello world');
    expect(out.rhymes.target_word).toBe('world');
  });

  describe('exploreRhymes', () => {
    function setupExplore(
      upstream?: Partial<{
        rhymes: Array<Record<string, unknown>>;
        capabilities: Record<string, unknown>;
        summary: Record<string, unknown>;
        mode: string;
        target_type: string;
        language: 'en' | 'es';
      }>,
    ) {
      const getRhymes = jest.fn().mockResolvedValue({
        query: 'hollow',
        normalized_query: 'hollow',
        language: upstream?.language ?? 'en',
        target_type: upstream?.target_type ?? 'word',
        mode: upstream?.mode ?? 'multisyllabic',
        pronunciations_found: true,
        summary: upstream?.summary ?? {
          family_counts: { multisyllabic: 2 },
          returned: 2,
          requested_limit: 20,
        },
        rhymes: upstream?.rhymes ?? [
          {
            word: 'shadow',
            syllables: 2,
            rhyme_type: 'multisyllabic',
            score: 0.92,
            rhyme_family: 'multisyllabic',
            id: 'r1',
            confidence: 'high',
            evidence_tags: ['multisyllabic_key_match'],
            matched_span: 'ow',
            match_reason: 'shared stressed ending',
          },
        ],
        capabilities: upstream?.capabilities ?? {
          multisyllabic: { status: 'full', reason_code: null },
        },
      });
      const fastapi = {
        analyzeLine: jest.fn(),
        getRhymes,
      } as unknown as FastapiClient;
      const service = new EditorService(
        fastapi,
        new EditorResponsePresenter(),
        new LanguageRequestMapper(),
      );
      return { service, getRhymes };
    }

    it('forwards target_type=phrase_ending and mode=multisyllabic to FastAPI', async () => {
      const { service, getRhymes } = setupExplore();
      const out = await service.exploreRhymes('let it all go hollow', {
        targetType: 'phrase_ending',
        mode: 'multisyllabic',
        language: 'en',
        limit: 10,
      });
      expect(getRhymes).toHaveBeenCalledWith({
        word: 'let it all go hollow',
        mode: 'multisyllabic',
        language: 'en',
        target_type: 'phrase_ending',
        limit: 10,
      });
      expect(out.items[0]).toMatchObject({
        word: 'shadow',
        confidence: 'high',
        rhyme_family: 'multisyllabic',
        evidence_tags: ['multisyllabic_key_match'],
        matched_span: 'ow',
      });
    });

    it('defaults to target_type=word and language-appropriate mode', async () => {
      const { service, getRhymes } = setupExplore();
      await service.exploreRhymes('hollow');
      expect(getRhymes).toHaveBeenCalledWith({
        word: 'hollow',
        mode: 'perfect',
        language: 'en',
        target_type: 'word',
        limit: undefined,
      });
    });

    it('defaults Spanish requests to mode=consonant', async () => {
      const { service, getRhymes } = setupExplore({ language: 'es' });
      await service.exploreRhymes('corazón', { language: 'es' });
      expect(getRhymes).toHaveBeenCalledWith({
        word: 'corazón',
        mode: 'consonant',
        language: 'es',
        target_type: 'word',
        limit: undefined,
      });
    });

    it('propagates multisyllabic capability through the presenter', async () => {
      const { service } = setupExplore({
        capabilities: {
          multisyllabic: {
            status: 'partial',
            reason_code: 'language_partial_support',
          },
        },
      });
      const out = await service.exploreRhymes('corazón', {
        language: 'es',
        mode: 'multisyllabic',
      });
      expect(out.capabilities.multisyllabic).toEqual({
        status: 'partial',
        reason_code: 'language_partial_support',
      });
    });

    it('echoes the upstream resolved mode (FastAPI may coerce)', async () => {
      const { service } = setupExplore({ mode: 'multisyllabic' });
      const out = await service.exploreRhymes('hollow', {
        mode: 'perfect',
        targetType: 'phrase_ending',
      });
      expect(out.mode).toBe('multisyllabic');
    });
  });
});
