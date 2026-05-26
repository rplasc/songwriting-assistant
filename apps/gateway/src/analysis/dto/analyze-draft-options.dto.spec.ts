import 'reflect-metadata';
import { plainToInstance } from 'class-transformer';
import { validate } from 'class-validator';
import { AnalyzeDraftOptionsDto } from './analyze-draft-options.dto';

async function validateDto(payload: unknown): Promise<string[]> {
  const dto = plainToInstance(AnalyzeDraftOptionsDto, payload);
  const errors = await validate(dto);
  return errors.flatMap((e) => Object.keys(e.constraints ?? {}));
}

describe('AnalyzeDraftOptionsDto', () => {
  it('accepts an empty object', async () => {
    expect(await validateDto({})).toEqual([]);
  });

  it('accepts all four boolean fields', async () => {
    expect(
      await validateDto({
        includeSemanticRepetition: true,
        includeMotifTracking: false,
        includeSectionContrast: true,
        includeConsistencyHints: false,
      }),
    ).toEqual([]);
  });

  it('rejects non-boolean values', async () => {
    expect(await validateDto({ includeMotifTracking: 'yes' })).toContain(
      'isBoolean',
    );
  });
});
