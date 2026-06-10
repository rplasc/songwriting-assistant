import { EditorResponsePresenter } from './editor-response.presenter';
import {
  LineAnalysisResponse,
  RhymeResponse,
} from '../../fastapi/dto/fastapi-responses';

describe('EditorResponsePresenter', () => {
  const presenter = new EditorResponsePresenter();

  const lineResp: LineAnalysisResponse = {
    line: 'I see the fire in your eyes',
    normalized_line: 'i see the fire in your eyes',
    language: 'en',
    total_syllables: 8,
    tokens: [
      {
        text: 'fire',
        normalized: 'fire',
        syllables: 2,
        pronunciation_found: true,
        source: 'dictionary',
        low_confidence: false,
      },
    ],
    last_word: { text: 'eyes', normalized: 'eyes', pronunciation_found: true },
  };

  it('shapes a full payload when rhymes are available', () => {
    const rhymes: RhymeResponse = {
      word: 'eyes',
      normalized_word: 'eyes',
      language: 'en',
      pronunciations_found: true,
      rhymes: [
        { word: 'skies', syllables: 1, rhyme_type: 'perfect', score: 0.9 },
      ],
      meta: { limit: 10, mode: 'perfect', include_near: false },
    };

    const out = presenter.toClient(
      lineResp,
      rhymes,
      12.7,
      'perfect',
      'en',
      'req-1',
    );

    expect(out).toEqual({
      line: 'I see the fire in your eyes',
      language: 'en',
      syllables: {
        total: 8,
        tokens: [{ text: 'fire', syllables: 2, low_confidence: false }],
      },
      rhymes: {
        target_word: 'eyes',
        mode: 'perfect',
        items: [{ word: 'skies', syllables: 1, type: 'perfect' }],
      },
      inner_rhymes: [],
      meta: { request_id: 'req-1', latency_ms: 13 },
    });
  });

  it('passes inner-rhyme groups through from the line response', () => {
    const withInner: LineAnalysisResponse = {
      ...lineResp,
      inner_rhymes: [
        {
          id: 'irh_abc123',
          rhyme_type: 'perfect',
          confidence: 'high',
          rhyme_key: 'AE1_T',
          occurrences: [
            {
              line_index: 0,
              word_index: 1,
              char_start: 4,
              char_end: 7,
              text: 'cat',
              normalized: 'cat',
            },
            {
              line_index: 0,
              word_index: 2,
              char_start: 8,
              char_end: 11,
              text: 'sat',
              normalized: 'sat',
            },
          ],
        },
      ],
    };
    const out = presenter.toClient(withInner, null, 1, 'perfect', 'en');
    expect(out.inner_rhymes).toHaveLength(1);
    expect(out.inner_rhymes[0].occurrences.map((o) => o.normalized)).toEqual([
      'cat',
      'sat',
    ]);
  });

  it('echoes the FastAPI-resolved mode when present', () => {
    const rhymes: RhymeResponse = {
      word: 'corazón',
      normalized_word: 'corazón',
      language: 'es',
      pronunciations_found: true,
      rhymes: [],
      meta: { limit: 10, mode: 'consonant', include_near: false },
    };
    const out = presenter.toClient(lineResp, rhymes, 5, 'consonant', 'es');
    expect(out.rhymes.mode).toBe('consonant');
    expect(out.language).toBe('es');
  });

  it('returns empty items array when rhymes are null and echoes the mode', () => {
    const out = presenter.toClient(lineResp, null, 5, 'near', 'en');
    expect(out.rhymes.items).toEqual([]);
    expect(out.rhymes.target_word).toBe('eyes');
    expect(out.rhymes.mode).toBe('near');
  });

  it('null target_word when last_word is missing', () => {
    const out = presenter.toClient(
      { ...lineResp, last_word: null },
      null,
      0,
      'perfect',
      'en',
    );
    expect(out.rhymes.target_word).toBeNull();
    expect(out.rhymes.items).toEqual([]);
  });
});
