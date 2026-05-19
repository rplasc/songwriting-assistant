import { Transform } from 'class-transformer';
import {
  IsIn,
  IsNotEmpty,
  IsOptional,
  IsString,
  MaxLength,
} from 'class-validator';
import type {
  Language,
  RhymeMode,
} from '../../common/enums/language.enum';
import {
  SUPPORTED_LANGUAGES,
  SUPPORTED_RHYME_MODES,
} from '../../common/enums/language.enum';

export type { RhymeMode } from '../../common/enums/language.enum';

export class AnalyzeLineDto {
  @IsString()
  @Transform(({ value }) => (typeof value === 'string' ? value.trim() : value))
  @IsNotEmpty()
  @MaxLength(500)
  line!: string;

  @IsOptional()
  @IsIn(SUPPORTED_RHYME_MODES)
  rhyme_mode?: RhymeMode;

  @IsOptional()
  @IsIn(SUPPORTED_LANGUAGES)
  language?: Language;
}
