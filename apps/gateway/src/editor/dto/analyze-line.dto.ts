import { Transform } from 'class-transformer';
import {
  IsIn,
  IsInt,
  IsNotEmpty,
  IsOptional,
  IsString,
  Max,
  MaxLength,
  Min,
} from 'class-validator';
import type {
  AdvancedRhymeMode,
  Language,
  RhymeMode,
  RhymeTargetType,
} from '../../common/enums/language.enum';
import {
  RHYME_TARGET_TYPES,
  SUPPORTED_ADVANCED_RHYME_MODES,
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

export class ExploreRhymesDto {
  @IsString()
  @Transform(({ value }) => (typeof value === 'string' ? value.trim() : value))
  @IsNotEmpty()
  @MaxLength(128)
  query!: string;

  @IsOptional()
  @IsIn(RHYME_TARGET_TYPES)
  target_type?: RhymeTargetType;

  @IsOptional()
  @IsIn(SUPPORTED_ADVANCED_RHYME_MODES)
  mode?: AdvancedRhymeMode;

  @IsOptional()
  @IsIn(SUPPORTED_LANGUAGES)
  language?: Language;

  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(50)
  limit?: number;
}
