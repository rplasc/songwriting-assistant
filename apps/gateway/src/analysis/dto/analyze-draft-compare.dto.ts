import { Transform, Type } from 'class-transformer';
import {
  IsBoolean,
  IsIn,
  IsNotEmpty,
  IsOptional,
  IsString,
  IsUUID,
  MaxLength,
  ValidateNested,
} from 'class-validator';
import type { Language } from '../../common/enums/language.enum';
import { SUPPORTED_LANGUAGES } from '../../common/enums/language.enum';
import { AnalyzeDraftCompareOptionsDto } from './analyze-draft-compare-options.dto';

/**
 * Phase 5.5 compare request contract. Client supplies two revision hashes
 * the gateway resolves against its SnapshotStore. Compare requires draftId
 * so snapshots can be looked up.
 */
export class AnalyzeDraftCompareDto {
  @IsOptional()
  @IsUUID()
  draftId?: string;

  @IsString()
  @IsNotEmpty()
  @MaxLength(64)
  baseRevisionHash!: string;

  @IsString()
  @IsNotEmpty()
  @MaxLength(64)
  targetRevisionHash!: string;

  @IsOptional()
  @IsBoolean()
  forceRefresh?: boolean;

  @IsOptional()
  @IsIn(SUPPORTED_LANGUAGES)
  language?: Language;

  @IsOptional()
  @IsString()
  @Transform(({ value }) => (typeof value === 'string' ? value.trim() : value))
  @MaxLength(200)
  title?: string;

  @IsOptional()
  @ValidateNested()
  @Type(() => AnalyzeDraftCompareOptionsDto)
  options?: AnalyzeDraftCompareOptionsDto;
}
