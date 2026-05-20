import 'reflect-metadata';
import { plainToInstance } from 'class-transformer';
import { validate } from 'class-validator';
import { CreateDraftDto } from './create-draft.dto';
import { UpdateDraftDto } from './update-draft.dto';

async function validateCreate(payload: unknown): Promise<string[]> {
  const dto = plainToInstance(CreateDraftDto, payload);
  const errors = await validate(dto);
  return collectKeys(errors);
}

function collectKeys(
  errors: { constraints?: Record<string, string>; children?: unknown[] }[],
): string[] {
  return errors.flatMap((e) => [
    ...Object.keys(e.constraints ?? {}),
    ...collectKeys(
      (e.children ?? []) as {
        constraints?: Record<string, string>;
        children?: unknown[];
      }[],
    ),
  ]);
}

async function validateUpdate(payload: unknown): Promise<string[]> {
  const dto = plainToInstance(UpdateDraftDto, payload);
  const errors = await validate(dto);
  return errors.flatMap((e) => Object.keys(e.constraints ?? {}));
}

describe('CreateDraftDto', () => {
  it('accepts a payload without language (gateway defaults to en)', async () => {
    expect(await validateCreate({ content: 'lyrics' })).toEqual([]);
  });

  it('accepts Spanish language', async () => {
    expect(
      await validateCreate({ content: 'corazón', language: 'es' }),
    ).toEqual([]);
  });

  it('rejects unsupported language', async () => {
    const errors = await validateCreate({ content: 'lyrics', language: 'fr' });
    expect(errors).toContain('isIn');
  });
});

describe('CreateDraftDto sections', () => {
  it('accepts well-formed sections', async () => {
    expect(
      await validateCreate({
        content: 'a\nb',
        sections: [{ label: 'verse', lineStart: 1, lineEnd: 2 }],
      }),
    ).toEqual([]);
  });

  it('rejects sections with missing label', async () => {
    const errors = await validateCreate({
      content: 'a\nb',
      sections: [{ lineStart: 1, lineEnd: 2 }],
    });
    expect(errors.length).toBeGreaterThan(0);
  });

  it('rejects sections with non-integer line numbers', async () => {
    const errors = await validateCreate({
      content: 'a\nb',
      sections: [{ label: 'verse', lineStart: 1.5, lineEnd: 2 }],
    });
    expect(errors.length).toBeGreaterThan(0);
  });
});

describe('UpdateDraftDto', () => {
  it('accepts a language-only update', async () => {
    expect(await validateUpdate({ language: 'es' })).toEqual([]);
  });

  it('rejects unsupported language on update', async () => {
    const errors = await validateUpdate({ language: 'de' });
    expect(errors).toContain('isIn');
  });
});
