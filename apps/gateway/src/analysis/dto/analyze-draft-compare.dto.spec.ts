import 'reflect-metadata';
import { plainToInstance } from 'class-transformer';
import { validate } from 'class-validator';
import { AnalyzeDraftCompareDto } from './analyze-draft-compare.dto';

async function validateDto(payload: unknown): Promise<string[]> {
  const dto = plainToInstance(AnalyzeDraftCompareDto, payload);
  const errors = await validate(dto);
  const collect = (nodes: typeof errors): string[] =>
    nodes.flatMap((n) =>
      Object.keys(n.constraints ?? {}).concat(collect(n.children ?? [])),
    );
  return collect(errors);
}

describe('AnalyzeDraftCompareDto', () => {
  it('accepts a well-formed compare request', async () => {
    expect(
      await validateDto({
        baseRevisionHash: 'abc1234567890def',
        targetRevisionHash: '1234567890abcdef',
      }),
    ).toEqual([]);
  });

  it('requires base and target revision hashes', async () => {
    const errors = await validateDto({});
    expect(errors).toContain('isNotEmpty');
  });

  it('rejects non-UUID draftId', async () => {
    const errors = await validateDto({
      draftId: 'not-a-uuid',
      baseRevisionHash: 'a',
      targetRevisionHash: 'b',
    });
    expect(errors).toContain('isUuid');
  });

  it('rejects non-boolean forceRefresh', async () => {
    const errors = await validateDto({
      baseRevisionHash: 'a',
      targetRevisionHash: 'b',
      forceRefresh: 'yes',
    });
    expect(errors).toContain('isBoolean');
  });

  it('rejects unsupported language', async () => {
    const errors = await validateDto({
      baseRevisionHash: 'a',
      targetRevisionHash: 'b',
      language: 'fr',
    });
    expect(errors).toContain('isIn');
  });

  it('accepts nested compare options', async () => {
    expect(
      await validateDto({
        baseRevisionHash: 'a',
        targetRevisionHash: 'b',
        options: { compareMotifs: true, compareSections: false },
      }),
    ).toEqual([]);
  });

  it('accepts a request without nested options', async () => {
    expect(
      await validateDto({
        baseRevisionHash: 'a',
        targetRevisionHash: 'b',
      }),
    ).toEqual([]);
  });

  it('rejects baseRevisionHash longer than 64 chars', async () => {
    const errors = await validateDto({
      baseRevisionHash: 'x'.repeat(65),
      targetRevisionHash: 'b',
    });
    expect(errors).toContain('maxLength');
  });

  it('rejects non-boolean compare option values', async () => {
    const errors = await validateDto({
      baseRevisionHash: 'a',
      targetRevisionHash: 'b',
      options: { compareMotifs: 'yes' },
    });
    expect(errors).toContain('isBoolean');
  });
});
