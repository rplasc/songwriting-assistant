import { Transform } from 'class-transformer';
import { IsIn, IsOptional, IsString, MaxLength } from 'class-validator';
import type { Language } from '../../common/enums/language.enum';
import { SUPPORTED_LANGUAGES } from '../../common/enums/language.enum';

export class UpdateDraftDto {
  @IsOptional()
  @IsString()
  @Transform(({ value }) => (typeof value === 'string' ? value.trim() : value))
  @MaxLength(200)
  title?: string;

  @IsOptional()
  @IsString()
  @MaxLength(10_000)
  content?: string;

  @IsOptional()
  @IsIn(SUPPORTED_LANGUAGES)
  language?: Language;
}
