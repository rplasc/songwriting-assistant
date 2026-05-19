import { plainToInstance } from 'class-transformer';
import { validate } from 'class-validator';
import { CreateDraftDto } from './create-draft.dto';
import { UpdateDraftDto } from './update-draft.dto';

async function validateCreate(payload: unknown): Promise<string[]> {
  const dto = plainToInstance(CreateDraftDto, payload);
  const errors = await validate(dto);
  return errors.flatMap((e) => Object.keys(e.constraints ?? {}));
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

describe('UpdateDraftDto', () => {
  it('accepts a language-only update', async () => {
    expect(await validateUpdate({ language: 'es' })).toEqual([]);
  });

  it('rejects unsupported language on update', async () => {
    const errors = await validateUpdate({ language: 'de' });
    expect(errors).toContain('isIn');
  });
});
