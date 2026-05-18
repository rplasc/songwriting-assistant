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
    total_syllables: 8,
    tokens: [
      {
        text: 'fire',
        normalized: 'fire',
        syllables: 2,
        pronunciation_found: true,
      },
    ],
    last_word: { text: 'eyes', normalized: 'eyes', pronunciation_found: true },
  };

  it('shapes a full payload when rhymes are available', () => {
    const rhymes: RhymeResponse = {
      word: 'eyes',
      normalized_word: 'eyes',
      pronunciations_found: true,
      rhymes: [
        { word: 'skies', syllables: 1, rhyme_type: 'perfect', score: 0.9 },
      ],
      meta: { limit: 10, include_near: false },
    };

    const out = presenter.toClient(lineResp, rhymes, 12.7, 'perfect', 'req-1');

    expect(out).toEqual({
      line: 'I see the fire in your eyes',
      syllables: { total: 8, tokens: [{ text: 'fire', syllables: 2 }] },
      rhymes: {
        target_word: 'eyes',
        mode: 'perfect',
        items: [{ word: 'skies', syllables: 1, type: 'perfect' }],
      },
      meta: { request_id: 'req-1', latency_ms: 13 },
    });
  });

  it('returns empty items array when rhymes are null and echoes the mode', () => {
    const out = presenter.toClient(lineResp, null, 5, 'near');
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
    );
    expect(out.rhymes.target_word).toBeNull();
    expect(out.rhymes.items).toEqual([]);
  });
});
