import 'reflect-metadata';
import { plainToInstance } from 'class-transformer';
import { validate } from 'class-validator';
import { AnalyzeDraftDto } from './analyze-draft.dto';

async function validateDto(payload: unknown): Promise<string[]> {
  const dto = plainToInstance(AnalyzeDraftDto, payload);
  const errors = await validate(dto);
  return errors.flatMap((e) =>
    Object.keys(e.constraints ?? {}).concat(
      (e.children ?? []).flatMap((c) =>
        (c.children ?? []).flatMap((g) => Object.keys(g.constraints ?? {})),
      ),
    ),
  );
}

describe('AnalyzeDraftDto', () => {
  it('accepts a minimal request with content only', async () => {
    expect(await validateDto({ content: 'a\nb' })).toEqual([]);
  });

  it('requires content', async () => {
    const errors = await validateDto({});
    expect(errors.length).toBeGreaterThan(0);
  });

  it('rejects unsupported language', async () => {
    const errors = await validateDto({ content: 'x', language: 'fr' });
    expect(errors).toContain('isIn');
  });

  it('accepts well-formed inline sections', async () => {
    expect(
      await validateDto({
        content: 'a\nb',
        sections: [{ label: 'verse', lineStart: 1, lineEnd: 2 }],
      }),
    ).toEqual([]);
  });

  it('rejects non-UUID draftId', async () => {
    const errors = await validateDto({ content: 'x', draftId: 'not-a-uuid' });
    expect(errors).toContain('isUuid');
  });
});
