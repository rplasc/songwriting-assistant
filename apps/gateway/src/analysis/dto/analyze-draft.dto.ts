import { Transform, Type } from 'class-transformer';
import {
  IsArray,
  IsBoolean,
  IsIn,
  IsNotEmpty,
  IsOptional,
  IsString,
  IsUUID,
  MaxLength,
  ValidateNested,
} from 'class-validator';
import type { AnalysisMode } from '../../common/enums/analysis-mode.enum';
import { SUPPORTED_ANALYSIS_MODES } from '../../common/enums/analysis-mode.enum';
import type { Language } from '../../common/enums/language.enum';
import { SUPPORTED_LANGUAGES } from '../../common/enums/language.enum';
import { DraftSectionInputDto } from '../../drafts/dto/draft-section.dto';
import { AnalyzeDraftOptionsDto } from './analyze-draft-options.dto';

export class AnalyzeDraftDto {
  @IsOptional()
  @IsUUID()
  draftId?: string;

  @IsOptional()
  @IsString()
  @Transform(({ value }) => (typeof value === 'string' ? value.trim() : value))
  @MaxLength(200)
  title?: string;

  @IsString()
  @Transform(({ value }) => (typeof value === 'string' ? value.trim() : value))
  @IsNotEmpty()
  @MaxLength(10_000)
  content!: string;

  @IsOptional()
  @IsIn(SUPPORTED_LANGUAGES)
  language?: Language;

  @IsOptional()
  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => DraftSectionInputDto)
  sections?: DraftSectionInputDto[];

  @IsOptional()
  @IsBoolean()
  forceRefresh?: boolean;

  @IsOptional()
  @IsIn(SUPPORTED_ANALYSIS_MODES)
  analysisMode?: AnalysisMode;

  @IsOptional()
  @ValidateNested()
  @Type(() => AnalyzeDraftOptionsDto)
  options?: AnalyzeDraftOptionsDto;
}
