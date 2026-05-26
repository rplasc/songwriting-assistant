import 'reflect-metadata';
import { plainToInstance } from 'class-transformer';
import { validate } from 'class-validator';
import { AnalyzeDraftDto } from './analyze-draft.dto';

async function validateDto(payload: unknown): Promise<string[]> {
  const dto = plainToInstance(AnalyzeDraftDto, payload);
  const errors = await validate(dto);
  const collect = (nodes: typeof errors): string[] =>
    nodes.flatMap((n) =>
      Object.keys(n.constraints ?? {}).concat(collect(n.children ?? [])),
    );
  return collect(errors);
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

  it('rejects unknown analysisMode', async () => {
    const errors = await validateDto({ content: 'x', analysisMode: 'bogus' });
    expect(errors).toContain('isIn');
  });

  it('accepts revision_review analysisMode with options', async () => {
    expect(
      await validateDto({
        content: 'x',
        analysisMode: 'revision_review',
        options: { includeSemanticRepetition: true },
      }),
    ).toEqual([]);
  });

  it('rejects non-boolean nested option values', async () => {
    const errors = await validateDto({
      content: 'x',
      analysisMode: 'revision_review',
      options: { includeMotifTracking: 'yes' },
    });
    expect(errors).toContain('isBoolean');
  });
});
