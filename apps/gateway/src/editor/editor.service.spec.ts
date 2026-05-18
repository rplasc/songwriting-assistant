import { EditorService } from './editor.service';
import { EditorResponsePresenter } from './presenters/editor-response.presenter';
import { FastapiClient } from '../fastapi/fastapi.client';

describe('EditorService', () => {
  const baseLineResp = {
    line: 'hello world',
    normalized_line: 'hello world',
    total_syllables: 3,
    tokens: [],
    last_word: {
      text: 'world',
      normalized: 'world',
      pronunciation_found: true,
    },
  };

  function setup(opts: { pronunciationFound: boolean }) {
    const analyzeLine = jest.fn().mockResolvedValue({
      ...baseLineResp,
      last_word: {
        ...baseLineResp.last_word,
        pronunciation_found: opts.pronunciationFound,
      },
    });
    const getRhymes = jest.fn().mockResolvedValue({
      word: 'world',
      normalized_word: 'world',
      pronunciations_found: true,
      rhymes: [],
      meta: { limit: 10, include_near: false },
    });
    const fastapi = { analyzeLine, getRhymes } as unknown as FastapiClient;
    const service = new EditorService(fastapi, new EditorResponsePresenter());
    return { service, analyzeLine, getRhymes };
  }

  it('calls getRhymes when pronunciation_found is true (default perfect mode)', async () => {
    const { service, getRhymes } = setup({ pronunciationFound: true });
    const out = await service.analyze('hello world');
    expect(getRhymes).toHaveBeenCalledWith({
      word: 'world',
      rhyme_mode: 'perfect',
    });
    expect(out.rhymes.mode).toBe('perfect');
  });

  it('forwards rhyme_mode=near to getRhymes and echoes it on the response', async () => {
    const { service, getRhymes } = setup({ pronunciationFound: true });
    const out = await service.analyze('hello world', 'req-x', 'near');
    expect(getRhymes).toHaveBeenCalledWith({
      word: 'world',
      rhyme_mode: 'near',
    });
    expect(out.rhymes.mode).toBe('near');
  });

  it('still calls getRhymes when pronunciation_found is false so the NLP fallback can run', async () => {
    const { service, getRhymes } = setup({ pronunciationFound: false });
    const out = await service.analyze('hello world');
    expect(getRhymes).toHaveBeenCalledWith({
      word: 'world',
      rhyme_mode: 'perfect',
    });
    expect(out.rhymes.mode).toBe('perfect');
  });
});
