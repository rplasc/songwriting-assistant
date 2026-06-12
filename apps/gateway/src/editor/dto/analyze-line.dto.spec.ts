import { plainToInstance } from 'class-transformer';
import { validate } from 'class-validator';
import { AnalyzeLineDto } from './analyze-line.dto';

async function validateDto(payload: unknown): Promise<string[]> {
  const dto = plainToInstance(AnalyzeLineDto, payload);
  const errors = await validate(dto);
  return errors.flatMap((e) => Object.keys(e.constraints ?? {}));
}

describe('AnalyzeLineDto', () => {
  it('accepts a minimal payload', async () => {
    expect(await validateDto({ line: 'hello' })).toEqual([]);
  });

  it('accepts an explicit Spanish payload with consonant mode', async () => {
    expect(
      await validateDto({
        line: 'corazón',
        language: 'es',
        rhyme_mode: 'consonant',
      }),
    ).toEqual([]);
  });

  it('rejects an unsupported language', async () => {
    const errors = await validateDto({ line: 'hi', language: 'fr' });
    expect(errors).toContain('isIn');
  });

  it('rejects an unsupported rhyme mode', async () => {
    const errors = await validateDto({ line: 'hi', rhyme_mode: 'sideways' });
    expect(errors).toContain('isIn');
  });

  it('rejects a blank line', async () => {
    const errors = await validateDto({ line: '   ' });
    expect(errors).toContain('isNotEmpty');
  });

  it('accepts an optional target_word', async () => {
    expect(
      await validateDto({ line: 'hello world', target_word: 'hello' }),
    ).toEqual([]);
  });

  it('rejects a blank target_word', async () => {
    const errors = await validateDto({ line: 'hello', target_word: '   ' });
    expect(errors).toContain('isNotEmpty');
  });

  it('rejects an overlong target_word', async () => {
    const errors = await validateDto({
      line: 'hello',
      target_word: 'x'.repeat(129),
    });
    expect(errors).toContain('maxLength');
  });
});
